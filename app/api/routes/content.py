import asyncio
import time
import logging
import secrets
import ipaddress
import httpx
import re
from typing import cast, List, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse
from io import BytesIO

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Cookie
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct, or_, and_, func
from pydantic import BaseModel

from app.db import AsyncSessionLocal
from app.api.v1.deps import get_db
from app.models import ContentItem, Topic
from app.schemas import (
    ContentItem as ContentItemSchema,
    ContentWithTopic,
    Topic as TopicSchema,
)
from app.services.content_recommendation import recommendation_service
from app.services.article_scraper import article_scraper
from app.services.deduplication import deduplication_service
from app.services.rss_discovery import rss_discovery_service
from app.core.input_validation import (
    InputValidator,
    validate_request_data,
    get_safe_user_input,
)

router = APIRouter()

# In-memory cache for thumbnail fetch attempts (content_id -> (picture_url, timestamp))
# Prevents hammering the database/scraper for items without pictures
_thumbnail_cache: dict[int, tuple[Optional[str], float]] = {}
_THUMBNAIL_CACHE_TTL = 300  # 5 minutes

# Constants
LOGGER_NAME = "uvicorn.error"
CONTENT_NOT_FOUND = "Content not found"
SNIPPET_LENGTH = 800
MIN_CONTENT_LENGTH = 100
SCRAPE_TIMEOUT = 15.0
PRIORITY_SCRAPE_TIMEOUT = 10.0
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
CACHE_CONTROL_PUBLIC = "public, max-age=86400"
IMAGE_WEBP = "image/webp"
STATUS_READY = "ready"
STATUS_LOADING = "loading"
STATUS_FAILED = "failed"
STATUS_FETCHING = "fetching"
ERROR_INVALID_EXCLUDE_IDS = "Invalid exclude_ids format"
ERROR_INVALID_URL_SCHEME = "Invalid URL scheme"
ERROR_INVALID_URL = "Invalid URL"
ERROR_INVALID_URL_FORMAT = "Invalid URL format"
ERROR_INTERNAL_ACCESS_FORBIDDEN = "Access to internal resources is forbidden"
ERROR_INVALID_CONTENT_TYPE = "Invalid content type"
ERROR_IMAGE_TOO_LARGE = "Image too large"
ERROR_IMAGE_NOT_FOUND = "Image not found"
ERROR_NO_SOURCE_URL = "No source URL available"
ERROR_UNABLE_TO_FETCH = "Unable to fetch content from source"
ERROR_UNABLE_TO_FETCH_IMAGE = "Unable to fetch image"
ERROR_FAILED_TO_SERVE_IMAGE = "Failed to serve image"
ERROR_FAILED_TO_FETCH_THUMBNAIL = "Failed to fetch thumbnail"


class CategoriesResponse(BaseModel):
    categories: List[str]


class ThumbnailResponse(BaseModel):
    picture_url: Optional[str]


class ProxyRequest(BaseModel):
    url: str


def _parse_exclude_ids(exclude_ids: Optional[str]) -> list[int]:
    """Parse comma-separated exclude_ids parameter with security validation."""
    return InputValidator.validate_exclude_ids(exclude_ids)


def _parse_categories(
    categories: Optional[str], category: Optional[str]
) -> Optional[list[str]]:
    """Parse categories parameter with multi-select support and security validation."""
    if categories:
        return InputValidator.validate_category_list(categories)
    elif category:
        # Validate single category
        validated_category = InputValidator.validate_xss_safe(category)
        validated_category = InputValidator.validate_sql_safe(validated_category)
        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", validated_category):
            raise HTTPException(status_code=400, detail="Invalid category name")
        return [validated_category]
    return None


async def _get_feed_data(
    db, page_size, excluded_ids, cursor, category_list, safe_category_list, logger
):
    """Get feed data based on category selection."""
    if category_list and "all" in [c.lower() for c in category_list]:
        logger.info("Category 'All' selected: returning all items")
        return await recommendation_service.get_all_feed(
            db=db,
            page_size=page_size,
            exclude_ids=excluded_ids,
            cursor=cursor,
        )
    elif category_list:
        logger.info("Filtering feed by categories: %s", safe_category_list)
        return await recommendation_service.get_all_feed(
            db=db,
            page_size=page_size,
            exclude_ids=excluded_ids,
            cursor=cursor,
            categories=category_list,
        )
    else:
        logger.info("No categories selected: returning all items")
        return await recommendation_service.get_all_feed(
            db=db,
            page_size=page_size,
            exclude_ids=excluded_ids,
            cursor=cursor,
        )


@router.get("/categories", response_model=CategoriesResponse)
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    """Return all unique categories from ContentItem and Topic tables."""
    logger = logging.getLogger(LOGGER_NAME)
    try:
        categories = set()
        result1 = await db.execute(
            select(distinct(ContentItem.category)).where(
                ContentItem.category.isnot(None)
            )
        )
        categories.update([row[0] for row in result1.fetchall() if row[0]])
        result2 = await db.execute(
            select(distinct(Topic.category)).where(Topic.category.isnot(None))
        )
        categories.update([row[0] for row in result2.fetchall() if row[0]])
        return CategoriesResponse(categories=sorted(categories))
    except Exception as e:
        safe_error = "".join(
            c for c in str(e)[:200] if c.isprintable() and c not in "\n\r\t"
        )
        logger.error("Error in /categories endpoint: %s", safe_error)
        raise HTTPException(status_code=500, detail="Failed to fetch categories")


def _validate_feed_params(exclude_ids, categories, category, cursor):
    """Validate and parse feed parameters."""
    excluded_ids = _parse_exclude_ids(exclude_ids)
    category_list = _parse_categories(categories, category)
    cursor = InputValidator.validate_cursor(cursor)
    return excluded_ids, category_list, cursor


def _log_feed_request(logger, page, category_list, exclude_ids, cursor):
    """Log feed request with sanitized parameters."""
    safe_category_list = InputValidator.sanitize_for_logging(category_list)
    safe_exclude_ids = InputValidator.sanitize_for_logging(exclude_ids)
    safe_cursor = InputValidator.sanitize_for_logging(cursor)

    logger.info(
        "Feed request: page=%d, categories=%s, exclude_ids=%s, cursor=%s",
        page,
        safe_category_list,
        safe_exclude_ids,
        safe_cursor,
    )


def _build_response_data(page, page_size, result, session_token):
    """Build response data structure."""
    return {
        "page": page,
        "page_size": page_size,
        "items": result["items"],
        "next_cursor": result["next_cursor"],
        "has_more": result["has_more"],
        "is_personalized": session_token is not None,
    }


def _create_cached_response(response_data):
    """Create cached JSON response for public feeds."""
    return JSONResponse(
        content=response_data,
        headers={
            "Cache-Control": "public, max-age=60",
            "Vary": "Accept-Encoding",
        },
    )


@router.get("/feed")
async def get_feed(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    category: Optional[str] = Query(None),
    categories: Optional[str] = Query(None),
    exclude_ids: Optional[str] = Query(None),
    cursor: Optional[str] = Query(None),
    nexus_session: Optional[str] = Cookie(default=None),
):
    """Get personalized content feed with cursor-based pagination."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.info("[FEED] Endpoint called")

    excluded_ids, category_list, cursor = _validate_feed_params(
        exclude_ids, categories, category, cursor
    )
    session_token = nexus_session or request.cookies.get("nexus_session")

    _log_feed_request(logger, page, category_list, exclude_ids, cursor)

    result = await _get_feed_data(
        db,
        page_size,
        excluded_ids,
        cursor,
        category_list,
        InputValidator.sanitize_for_logging(category_list),
        logger,
    )

    _trigger_background_scraping(result)

    response_data = _build_response_data(page, page_size, result, session_token)

    return (
        _create_cached_response(response_data)
        if session_token is None
        else response_data
    )


def _find_articles_to_scrape(items: list) -> list:
    """Find articles that need content scraping."""
    return [
        item
        for item in items
        if (not item.get("facts") or not item.get("facts").strip())
        and item.get("source_urls")
    ]


async def _scrape_single_article(item: dict, bg_db: AsyncSession, logger) -> None:
    """Scrape a single article with error handling."""
    try:
        content = await bg_db.get(ContentItem, item["content_id"])
        if content and (not content.facts or not content.facts.strip()):
            source_url = content.source_urls[0] if content.source_urls else None
            if source_url:
                await asyncio.wait_for(
                    _scrape_and_store_article(content, source_url, bg_db),
                    timeout=SCRAPE_TIMEOUT,
                )
    except asyncio.TimeoutError:
        logger.debug("Background scrape timed out for %s", item["content_id"])
    except Exception as e:
        safe_error = "".join(
            c for c in str(e)[:200] if c.isprintable() and c not in "\n\r\t"
        )
        logger.debug(
            "Background scrape error for %s: %s", item["content_id"], safe_error
        )


async def _background_scrape_articles(result):
    """Background scraping task - runs in separate worker"""
    logger = logging.getLogger(LOGGER_NAME)
    try:
        articles_to_scrape = _find_articles_to_scrape(result["items"])
        if articles_to_scrape:
            async with AsyncSessionLocal() as bg_db:
                for item in articles_to_scrape[:1]:
                    await _scrape_single_article(item, bg_db, logger)
    except Exception as e:
        safe_error = "".join(
            c for c in str(e)[:200] if c.isprintable() and c not in "\n\r\t"
        )
        logger.debug("Background scraping task failed: %s", safe_error)


def _trigger_background_scraping(result):
    """Trigger background scraping for articles without content."""
    task = asyncio.create_task(_background_scrape_articles(result))
    task.add_done_callback(lambda t: None)


@router.get("/trending-feed")
async def get_trending_feed_endpoint():
    """Deprecated: Trending disabled."""
    raise HTTPException(status_code=404, detail="Trending disabled")


@router.get("/", response_model=List[ContentWithTopic])
async def get_content_items(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """Get all content items with their topics"""
    result = await db.execute(
        select(ContentItem, Topic)
        .join(Topic, ContentItem.topic_id == Topic.id)
        .where(ContentItem.title.isnot(None))  # Skip records with NULL titles
        .offset(skip)
        .limit(limit)
    )

    content_items = []
    for content_item, topic in result.all():
        content_dict = ContentItemSchema.model_validate(content_item).model_dump()
        content_dict["topic"] = TopicSchema.model_validate(topic).model_dump()
        content_items.append(content_dict)

    return content_items


@router.get("/{content_id}", response_model=ContentWithTopic)
async def get_content_item(content_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific content item with its topic"""
    result = await db.execute(
        select(ContentItem, Topic)
        .join(Topic, ContentItem.topic_id == Topic.id)
        .where(ContentItem.id == content_id)
    )

    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Content item not found")

    content_item, topic = row
    content_dict = ContentItemSchema.model_validate(content_item).model_dump()
    content_dict["topic"] = TopicSchema.model_validate(topic).model_dump()

    return content_dict


def _get_cached_content(content: ContentItem) -> Optional[dict]:
    """Return cached content if available and valid."""
    if (
        content.content_text
        and len(content.content_text) > MIN_CONTENT_LENGTH
        and not content.content_text.startswith("Trending topic")
    ):
        snippet = (
            content.content_text[:SNIPPET_LENGTH]
            if len(content.content_text) > SNIPPET_LENGTH
            else content.content_text
        )
        return {"snippet": snippet, "full_content_available": True}
    return None


def _get_source_url(content: ContentItem) -> Optional[str]:
    """Extract and validate source URL from content."""
    if not content.source_urls or len(content.source_urls) == 0:
        return None
    return content.source_urls[0]


async def _scrape_and_store_article(
    content: ContentItem, source_url: str, db: AsyncSession
) -> Optional[str]:
    """Scrape article and persist to database. Returns snippet or None."""
    # Validate URL before scraping to prevent SSRF
    _validate_scraping_url(source_url)

    article_data = await asyncio.to_thread(article_scraper.fetch_article, source_url)

    # Always mark scraping as attempted
    _update_scraping_metadata(content)

    if not article_data or not article_data.get("content"):
        await db.commit()
        return None

    # Store content
    full_content = article_data["content"]
    content.content_text = full_content
    content.facts = full_content

    # Update metadata from article
    _update_article_metadata(content, article_data)

    # Download image
    await _download_article_image(content, article_data)

    await db.commit()

    # Generate snippet
    return _generate_snippet(content)


def _update_scraping_metadata(content: ContentItem) -> None:
    """Mark scraping as attempted."""
    if not content.source_metadata:
        content.source_metadata = {}
    content.source_metadata["scraped_at"] = datetime.now(timezone.utc).isoformat()


def _update_article_metadata(content: ContentItem, article_data: dict) -> None:
    """Update content metadata from scraped article."""
    if article_data.get("title"):
        content.title = article_data["title"]
    if article_data.get("author"):
        content.source_metadata["author"] = article_data["author"]
    if article_data.get("published_date"):
        content.source_metadata["published_date"] = article_data["published_date"]


async def _download_article_image(content: ContentItem, article_data: dict) -> None:
    """Download and optimize image for content."""
    image_url = article_data.get("image_url")
    if not image_url:
        print(f"⚠️ No image URL for content {content.id}")
        return

    print(f"🖼️  Attempting to download image from: {image_url[:80]}...")
    try:
        image_data = await asyncio.to_thread(
            article_scraper.download_and_optimize_image,
            image_url,
        )
        if image_data:
            content.image_data = image_data
            print(
                f"✅ Stored optimized image for content {content.id} ({len(image_data)} bytes)"
            )
        else:
            print(f"⚠️ Image download returned None for content {content.id}")
    except (OSError, ValueError, TypeError) as e:
        print(f"⚠️ Failed to optimize image: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error optimizing image: {e}")


def _generate_snippet(content: ContentItem) -> Optional[str]:
    """Generate snippet from content facts."""
    if content.facts is not None:
        facts_str = cast(str, content.facts)
        if len(facts_str) > SNIPPET_LENGTH:
            return facts_str[:SNIPPET_LENGTH]
        return facts_str
    return content.facts


def _get_content_for_snippet(content_id: int, db: AsyncSession):
    """Get content item for snippet endpoints."""
    return db.execute(select(ContentItem).where(ContentItem.id == content_id))


def _check_existing_snippet(content: ContentItem) -> Optional[dict]:
    """Check if content already has a snippet and return response if so."""
    if content.facts and content.facts.strip():
        snippet = (
            content.facts[:SNIPPET_LENGTH]
            if len(content.facts) > SNIPPET_LENGTH
            else content.facts
        )
        return {
            "snippet": snippet,
            "full_content_available": True,
            "rate_limited": False,
        }
    return None


def _is_rate_limit_error(error: Exception) -> bool:
    """Check if error is rate-limit related."""
    error_msg = str(error).lower()
    return any(keyword in error_msg for keyword in ["rate", "limit", "429", "too many"])


def _get_rate_limit_response() -> dict:
    """Return dad joke rate limit response."""
    dad_jokes = [
        "Whoa there, speed racer! Even my dad jokes need a breather. Try again in a moment!",
        "Easy there, tiger! You're clicking faster than my dad can tell a punchline. Slow down!",
        "Hold your horses! You're moving faster than a dad running to turn off the thermostat!",
        "Pump the brakes! Even the internet needs a coffee break. Try again soon!",
        "Woah! You're scrolling faster than dad jokes spread at a BBQ. Give it a sec!",
        "Cool your jets! You're browsing faster than dad running when mom says 'dinner's ready'!",
    ]
    return {
        "snippet": None,
        "rate_limited": True,
        "message": secrets.choice(dad_jokes),
    }


@router.get("/snippet/{content_id}")
async def get_content_snippet(content_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fetch article snippet/content on demand.
    Returns immediately with description, triggers background scraping for full content.
    """
    # Get content from database
    result = await _get_content_for_snippet(content_id, db)
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail=CONTENT_NOT_FOUND)

    # Check if already scraped
    existing_snippet = _check_existing_snippet(content)
    if existing_snippet:
        return existing_snippet

    # Validate source URL
    source_url = _get_source_url(content)
    if not source_url:
        return {"snippet": content.description or None, "rate_limited": False}

    # Return description immediately and trigger background scraping
    # This way the UI shows the description immediately and gets the full content later
    async def background_scrape():
        """Background task to scrape article without blocking response"""
        try:
            async with AsyncSessionLocal() as bg_db:
                bg_result = await bg_db.execute(
                    select(ContentItem).where(ContentItem.id == content_id)
                )
                bg_content = bg_result.scalar_one_or_none()
                if bg_content and (
                    not bg_content.facts or not bg_content.facts.strip()
                ):
                    await _scrape_and_store_article(bg_content, source_url, bg_db)
        except Exception as e:
            logger = logging.getLogger(LOGGER_NAME)
            logger.error(f"Background scrape failed for content {content_id}: {e}")

    # Fire and forget - don't await
    task = asyncio.create_task(background_scrape())
    task.add_done_callback(lambda t: None)  # Prevent garbage collection

    # Return description immediately while scraping happens in background
    return {
        "snippet": content.description or None,
        "rate_limited": False,
        "status": STATUS_FETCHING,
    }


@router.get("/snippet/{content_id}/priority")
async def get_content_snippet_priority(
    content_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch article snippet on-demand with user waiting (e.g., card expansion).
    Attempts to scrape immediately and returns within timeout.
    Shows loading state if scraping takes longer than timeout.
    """
    # Get content from database
    result = await _get_content_for_snippet(content_id, db)
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail=CONTENT_NOT_FOUND)

    # Check if already scraped
    existing_snippet = _check_existing_snippet(content)
    if existing_snippet:
        existing_snippet["status"] = STATUS_READY
        return existing_snippet

    # Validate source URL
    source_url = _get_source_url(content)
    if not source_url:
        return {
            "snippet": content.description or None,
            "rate_limited": False,
            "status": STATUS_READY,
        }

    # Try to scrape immediately with timeout
    try:
        # Use asyncio.timeout context manager to enforce timeout
        async with asyncio.timeout(PRIORITY_SCRAPE_TIMEOUT):
            snippet = await _scrape_and_store_article(content, source_url, db)

        if snippet:
            return {
                "snippet": snippet,
                "full_content_available": True,
                "rate_limited": False,
                "status": "ready",
            }
    except asyncio.TimeoutError:
        # Scraping took too long - return loading state
        return {
            "snippet": None,
            "rate_limited": False,
            "status": STATUS_LOADING,
        }
    except Exception as e:
        if _is_rate_limit_error(e):
            return _get_rate_limit_response()
        logger = logging.getLogger(LOGGER_NAME)
        safe_error = "".join(
            c for c in str(e)[:200] if c.isprintable() and c not in "\n\r\t"
        )
        logger.debug("Priority scrape error for %s: %s", content_id, safe_error)
        # Return failed status when scraping fails
        return {
            "snippet": None,
            "rate_limited": False,
            "status": STATUS_FAILED,
        }

    # Fallback to description
    return {
        "snippet": content.description or None,
        "rate_limited": False,
        "status": STATUS_READY,
    }


@router.get("/related/{content_id}")
async def get_related_content(content_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get related content items for a given content ID.
    Returns stories from different sources about the same topic.
    """
    related_items = await deduplication_service.get_related_content(db, content_id)

    return {
        "related_items": [
            {
                "content_id": item.id,
                "title": item.title,
                "description": item.description,
                "category": item.category,
                "source_urls": item.source_urls,
                "source": (
                    item.source_metadata.get("source", "Unknown")
                    if item.source_metadata
                    else "Unknown"
                ),
                "picture_url": (
                    item.source_metadata.get("picture_url")
                    if item.source_metadata
                    else None
                ),
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in related_items
        ]
    }


def _is_search_url(url: str) -> bool:
    """Check if URL is a search engine query."""
    return (
        "duckduckgo.com" in url
        or "google.com/search" in url
        or "bing.com/search" in url
    )


async def _fetch_article_by_type(source_url: str) -> dict | None:
    """Fetch article content based on URL type (search vs regular article)."""
    # Validate URL before scraping to prevent SSRF
    _validate_scraping_url(source_url)

    if _is_search_url(source_url):
        return await asyncio.to_thread(article_scraper.fetch_search_context, source_url)
    else:
        return await asyncio.to_thread(article_scraper.fetch_article, source_url)


async def _save_scraped_content(
    content: ContentItem, article_data: dict, content_id: int, db: AsyncSession
) -> None:
    """Save scraped content back to database for future use."""
    try:
        content.content_text = article_data.get("content", "")

        # Update title if better one was scraped
        if article_data.get("title") and len(article_data["title"]) > len(
            content.title or ""
        ):
            content.title = article_data["title"][:500]

        # Save image URL if found
        if article_data.get("image_url"):
            if not content.source_metadata:
                content.source_metadata = {}
            content.source_metadata["picture_url"] = article_data["image_url"]
            content.source_metadata["scraped_at"] = datetime.now(
                timezone.utc
            ).isoformat()

        await db.commit()
        print(f"✅ Saved scraped content for item {content_id}")
    except Exception as e:
        print(f"⚠️ Error saving scraped content: {e}")
        await db.rollback()


def _format_related_items(related_items: List[ContentItem]) -> List[dict]:
    """Format related content items for API response."""
    return [
        {
            "content_id": item.id,
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "tags": item.tags,
            "source_urls": item.source_urls,
            "source": (
                item.source_metadata.get("source", "Unknown")
                if item.source_metadata
                else "Unknown"
            ),
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in related_items
    ]


@router.get("/article/{content_id}")
async def get_article_content(content_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch and return the full article content for a content item."""
    content = await _get_content_or_404(content_id, db)

    if _has_scraped_content(content):
        article_data = _build_article_from_cache(content)
    else:
        article_data = await _scrape_article_content(content, content_id, db)

    # Find related content
    related_items = await _get_related_items_safely(db, content)
    article_data["related_items"] = _format_related_items(related_items)

    return article_data


async def _get_content_or_404(content_id: int, db: AsyncSession) -> ContentItem:
    """Get content item or raise 404."""
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail=CONTENT_NOT_FOUND)
    return content


def _has_scraped_content(content: ContentItem) -> bool:
    """Check if content has valid scraped content."""
    return bool(
        content.content_text
        and len(content.content_text) > MIN_CONTENT_LENGTH
        and not content.content_text.startswith("Trending topic")
        and content.source_metadata
        and content.source_metadata.get("scraped_at")
    )


def _get_safe_domain(url: str) -> Optional[str]:
    """Safely extract domain from URL without exposing user-controlled data."""
    try:
        parsed = urlparse(url)
        if parsed.netloc:
            # Only return domain, sanitized and length-limited
            domain = parsed.netloc.lower()[:100]
            # Remove any suspicious characters
            safe_domain = "".join(c for c in domain if c.isalnum() or c in ".-")
            return safe_domain if safe_domain else None
    except Exception:
        pass
    return None


def _build_article_from_cache(content: ContentItem) -> dict:
    """Build article data from cached content."""
    return {
        "title": content.title,
        "content": content.content_text,
        "author": (
            content.source_metadata.get("author") if content.source_metadata else None
        ),
        "published_date": (
            content.source_metadata.get("published_date")
            if content.source_metadata
            else None
        ),
        "image_url": (
            content.source_metadata.get("picture_url")
            if content.source_metadata
            else None
        ),
        "domain": (
            _get_safe_domain(content.source_urls[0]) if content.source_urls else None
        ),
    }


async def _scrape_article_content(
    content: ContentItem, content_id: int, db: AsyncSession
) -> dict:
    """Scrape article content and save it."""
    source_url = _get_source_url(content)
    if not source_url:
        raise HTTPException(status_code=404, detail=ERROR_NO_SOURCE_URL)

    article_data = await _fetch_article_by_type(source_url)
    if not article_data:
        raise HTTPException(status_code=404, detail=ERROR_UNABLE_TO_FETCH)

    await _save_scraped_content(content, article_data, content_id, db)
    return article_data


async def _get_related_items_safely(db: AsyncSession, content: ContentItem) -> list:
    """Get related items, handling errors."""
    try:
        return await find_related_content(db, content)
    except Exception as e:
        print(f"❌ Error finding related content: {e}")
        return []


@router.get("/thumbnail/{content_id}", response_model=ThumbnailResponse)
async def get_thumbnail(content_id: int, db: AsyncSession = Depends(get_db)):
    """Ensure a thumbnail is available for a content item and return it.
    If missing, scrape the article to fetch image_url and persist to source_metadata.picture_url.
    Uses in-memory caching to prevent hammering database on repeated failed attempts.
    """
    logger = logging.getLogger(LOGGER_NAME)

    try:
        current_time = time.time()
        cached_result = _check_thumbnail_cache(content_id, current_time)
        if cached_result is not None:
            return ThumbnailResponse(picture_url=cached_result)

        content = await _get_content_for_thumbnail(content_id, db, current_time)
        if content is None:
            return ThumbnailResponse(picture_url=None)

        pic = _get_existing_picture_url(content)
        if pic:
            _thumbnail_cache[content_id] = (pic, current_time)
            return ThumbnailResponse(picture_url=pic)

        # Try to scrape
        pic = await _scrape_thumbnail(content, db, current_time, logger)
        return ThumbnailResponse(picture_url=pic)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Thumbnail endpoint failed", extra={"content_id": content_id})
        raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_FETCH_THUMBNAIL)


def _check_thumbnail_cache(content_id: int, current_time: float) -> Optional[str]:
    """Check if thumbnail is cached."""
    if content_id in _thumbnail_cache:
        cached_url, timestamp = _thumbnail_cache[content_id]
        if current_time - timestamp < _THUMBNAIL_CACHE_TTL:
            return cached_url
        else:
            del _thumbnail_cache[content_id]
    return None


async def _get_content_for_thumbnail(
    content_id: int, db: AsyncSession, current_time: float
) -> Optional[ContentItem]:
    """Get content item for thumbnail, caching negative results."""
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        _thumbnail_cache[content_id] = (None, current_time)
        raise HTTPException(status_code=404, detail=CONTENT_NOT_FOUND)
    return content


def _get_existing_picture_url(content: ContentItem) -> Optional[str]:
    """Get existing picture URL from metadata."""
    if content.source_metadata:
        return content.source_metadata.get("picture_url")
    return None


async def _scrape_thumbnail(
    content: ContentItem, db: AsyncSession, current_time: float, logger
) -> Optional[str]:
    """Scrape article to get thumbnail URL."""
    if not content.source_urls or len(content.source_urls) == 0:
        _thumbnail_cache[content.id] = (None, current_time)
        return None

    source_url = content.source_urls[0]
    is_search_url = (
        "duckduckgo.com" in source_url
        or "google.com/search" in source_url
        or "bing.com/search" in source_url
    )
    try:
        # Validate URL before scraping to prevent SSRF
        _validate_scraping_url(source_url)

        if is_search_url:
            data = await asyncio.to_thread(
                article_scraper.fetch_search_context, source_url
            )
        else:
            data = await asyncio.to_thread(article_scraper.fetch_article, source_url)
        if data and data.get("image_url"):
            if not content.source_metadata:
                content.source_metadata = {}
            content.source_metadata["picture_url"] = data["image_url"]
            content.source_metadata["scraped_at"] = datetime.now(
                timezone.utc
            ).isoformat()
            await db.commit()
            _thumbnail_cache[content.id] = (data["image_url"], current_time)
            return data["image_url"]
    except Exception:
        await db.rollback()
        # Safely extract domain for logging to prevent taint vulnerability
        safe_domain = _get_safe_domain(source_url) or "unknown"
        logger.exception(
            "Thumbnail scrape failed",
            extra={"content_id": content.id, "domain": safe_domain},
        )
    _thumbnail_cache[content.id] = (None, current_time)
    return None


@router.get("/{content_id}/image")
async def get_content_image(
    content_id: int,
    size: int = Query(800, ge=400, le=1600),
    db: AsyncSession = Depends(get_db),
):
    """
    Serve stored WebP image for content, with optional resizing.
    Images are stored at 600px and upscaled on-demand.

    Args:
        content_id: ID of the content item
        size: Desired width in pixels (400-1600, default 800)

    Returns:
        WebP image data with appropriate size
    """
    try:
        result = await db.execute(
            select(ContentItem).where(ContentItem.id == content_id)
        )
        content = result.scalar_one_or_none()

        if not content or not content.image_data:
            raise HTTPException(status_code=404, detail=ERROR_IMAGE_NOT_FOUND)

        # If size matches or is smaller than original, return as-is
        if size <= 600:
            return StreamingResponse(
                iter([content.image_data]),
                media_type=IMAGE_WEBP,
                headers={"Cache-Control": CACHE_CONTROL_PUBLIC},
            )

        # Upscale image using high-quality resampling
        from PIL import Image

        img = Image.open(BytesIO(content.image_data))

        # Calculate aspect ratio and new height
        aspect_ratio = img.height / img.width
        new_height = int(size * aspect_ratio)

        # Upscale with LANCZOS resampling (best for enlargement)
        img = img.resize((size, new_height), Image.Resampling.LANCZOS)

        # Save as WebP
        output = BytesIO()
        img.save(output, "WEBP", quality=75, method=6)
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="image/webp",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to serve image for content {content_id}: {e}")
        raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_SERVE_IMAGE)


@router.get("/proxy/image")
async def image_proxy(
    url: str, w: int = Query(None, ge=1, le=1200), h: int = Query(None, ge=1, le=1200)
):
    """Proxy and optionally resize remote images to avoid mixed-content/CORS issues."""
    logger = logging.getLogger("uvicorn.error")

    # Validate URL parameter to prevent SSRF (don't use aggressive XSS sanitization on URLs)
    _validate_image_url(url)

    try:
        image_data, content_type = await _fetch_image_data(url, logger)
        image_data, content_type = _resize_image_if_needed(
            image_data, content_type, w, h, logger
        )

        return StreamingResponse(
            iter([image_data]),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=2592000",  # 30 days
                "ETag": f'"{hash(url)}"',
            },
        )
    except HTTPException:
        raise
    except Exception:
        # Only log domain to prevent sensitive data exposure
        try:
            parsed_url = urlparse(url)
            safe_domain = parsed_url.netloc[:100] if parsed_url.netloc else "unknown"
            logger.warning("Image proxy failed for domain: %s", safe_domain)
        except Exception:
            logger.warning("Image proxy failed for invalid URL")
        raise HTTPException(status_code=404, detail=ERROR_UNABLE_TO_FETCH_IMAGE)


def _validate_scraping_url(url: str) -> None:
    """Validate URL for scraping to prevent SSRF attacks."""
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise HTTPException(status_code=400, detail="Invalid URL scheme")

        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(status_code=400, detail="Invalid URL")

        # Check for IP addresses and validate they're not private/internal
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
                raise HTTPException(
                    status_code=403, detail=ERROR_INTERNAL_ACCESS_FORBIDDEN
                )
        except ValueError:
            # Not an IP address, check hostname patterns
            hostname_lower = hostname.lower()

            # Block localhost variants and internal domains
            blocked_patterns = [
                "localhost",
                "127.",
                "0.0.0.0",
                "::1",
                "::ffff:127.0.0.1",
                ".local",
                ".internal",
                ".corp",
                ".lan",
                "metadata.google.internal",
                "169.254.",
                "metadata",
                "consul",
                "vault",
            ]

            if any(pattern in hostname_lower for pattern in blocked_patterns):
                raise HTTPException(
                    status_code=403, detail=ERROR_INTERNAL_ACCESS_FORBIDDEN
                )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail=ERROR_INVALID_URL_FORMAT)


def _validate_image_url(url: str) -> None:
    """Validate URL for security against SSRF attacks and path traversal."""
    try:
        # First validate with InputValidator to prevent path traversal
        url = InputValidator.validate_path_safe(url)

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise HTTPException(status_code=400, detail=ERROR_INVALID_URL_SCHEME)

        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(status_code=400, detail=ERROR_INVALID_URL)

        # Validate path component for traversal attacks
        if parsed.path and ("../" in parsed.path or "..\\" in parsed.path):
            raise HTTPException(status_code=400, detail="Path traversal detected")

        # Check for IP addresses and validate they're not private/internal
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
                raise HTTPException(
                    status_code=403, detail=ERROR_INTERNAL_ACCESS_FORBIDDEN
                )
        except ValueError:
            # Not an IP address, check hostname patterns
            hostname_lower = hostname.lower()

            # Block localhost variants and internal domains
            blocked_patterns = [
                "localhost",
                "127.",
                "0.0.0.0",
                "::1",
                "::ffff:127.0.0.1",
                ".local",
                ".internal",
                ".corp",
                ".lan",
                "metadata.google.internal",
                "169.254.",
                "metadata",
                "consul",
                "vault",
            ]

            if any(pattern in hostname_lower for pattern in blocked_patterns):
                raise HTTPException(
                    status_code=403, detail=ERROR_INTERNAL_ACCESS_FORBIDDEN
                )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail=ERROR_INVALID_URL_FORMAT)


async def _fetch_image_data(url: str, logger) -> tuple[bytes, str]:
    """Fetch image data from URL with size limits."""
    async with httpx.AsyncClient(follow_redirects=False, timeout=5.0) as client:
        # Validate and sanitize URL for logging to prevent malicious content
        if len(url) > 2000:  # Reject extremely long URLs
            raise HTTPException(status_code=400, detail="URL too long")

        # Only log domain part to prevent sensitive data exposure
        try:
            parsed_url = urlparse(url)
            safe_domain = parsed_url.netloc[:100] if parsed_url.netloc else "unknown"
            logger.info("Image proxy fetch from domain: %s", safe_domain)
        except Exception:
            logger.info("Image proxy fetch from invalid URL")
        resp = await client.get(url)
        resp.raise_for_status()

        # Limit response size to prevent DoS
        if int(resp.headers.get("content-length", 0)) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=413, detail=ERROR_IMAGE_TOO_LARGE)

        content_type = resp.headers.get("content-type", "image/jpeg")
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=ERROR_INVALID_CONTENT_TYPE)

        return resp.content, content_type


def _resize_image_if_needed(
    image_data: bytes, content_type: str, w: Optional[int], h: Optional[int], logger
) -> tuple[bytes, str]:
    """Resize image if dimensions specified."""
    if (w or h) and content_type.startswith("image/"):
        try:
            from PIL import Image  # type: ignore

            img = Image.open(BytesIO(image_data))

            target_w = w or img.width
            target_h = h or img.height

            img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)

            output = BytesIO()
            save_kwargs = {"quality": 75, "method": 6}
            img.save(output, format="WEBP", **save_kwargs)
            return output.getvalue(), IMAGE_WEBP
        except Exception as e:
            safe_error = "".join(
                c for c in str(e)[:200] if c.isprintable() and c not in "\n\r\t"
            )
            logger.warning("Image resize failed: %s, returning original", safe_error)

    return image_data, content_type


def _extract_keywords(title: str) -> tuple[List[str], List[str]]:
    """Extract proper nouns and other significant keywords from title."""
    original_words = title.split()
    proper_nouns = [
        word.strip(".,!?:;\"'-()[]{}").lower()
        for word in original_words
        if word and word[0].isupper()
    ]

    other_keywords = [
        word.strip(".,!?:;\"'-()[]{}").lower()
        for word in original_words
        if len(word) > 2 and not word[0].isupper()
    ]

    return proper_nouns, other_keywords


def _filter_stop_words(proper_nouns: List[str], other_keywords: List[str]) -> List[str]:
    """Filter stop words and return priority keywords."""
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "are",
        "was",
        "were",
        "been",
        "have",
        "has",
        "had",
        "their",
        "called",
        "begging",
    }
    all_keywords = [w for w in (proper_nouns + other_keywords) if w not in stop_words]
    return proper_nouns[:8] if proper_nouns else all_keywords[:8]


def _build_search_conditions(
    priority_keywords: List[str], content: ContentItem
) -> List:
    """Build SQLAlchemy search conditions for keywords."""
    conditions = []
    for keyword in priority_keywords:
        conditions.append(func.lower(ContentItem.title).contains(keyword))
        if content.description:
            conditions.append(func.lower(ContentItem.description).contains(keyword))
    return conditions


def _calculate_match_score(
    item: ContentItem,
    proper_nouns: List[str],
    other_keywords: List[str],
    content: ContentItem,
) -> int:
    """Calculate relevance score for a candidate match."""
    score = 0
    item_title_lower = item.title.lower() if item.title else ""
    item_desc_lower = item.description.lower() if item.description else ""

    # Score based on keyword matches
    for keyword in proper_nouns:
        if keyword in item_title_lower:
            score += 2
        if keyword in item_desc_lower:
            score += 1

    for keyword in other_keywords:
        if keyword in item_title_lower or keyword in item_desc_lower:
            score += 1

    # Bonus for different source
    if content.source_metadata and item.source_metadata:
        content_source = content.source_metadata.get("source", "")
        item_source = item.source_metadata.get("source", "")
        if content_source != item_source:
            score += 3

    return score


async def find_related_content(
    db: AsyncSession, content: ContentItem, limit: int = 5
) -> List[ContentItem]:
    """Find related content items based on title similarity and keywords."""
    # Extract and filter keywords
    proper_nouns, other_keywords = _extract_keywords(content.title)
    priority_keywords = _filter_stop_words(proper_nouns, other_keywords)

    if not priority_keywords:
        return []

    safe_title = "".join(
        c for c in str(content.title)[:200] if c.isprintable() and c not in "\n\r\t"
    )
    safe_keywords = "".join(
        c for c in str(priority_keywords)[:200] if c.isprintable() and c not in "\n\r\t"
    )
    print(
        "🔍 Finding related content for '%s' using keywords: %s",
        safe_title,
        safe_keywords,
    )

    # Build and execute query
    conditions = _build_search_conditions(priority_keywords, content)
    result = await db.execute(
        select(ContentItem)
        .where(
            and_(
                ContentItem.id != content.id,
                ContentItem.is_published == True,
                or_(*conditions),
            )
        )
        .limit(limit * 2)
    )

    candidates = result.scalars().all()

    # Score and sort matches
    scored_matches = []
    for item in candidates:
        score = _calculate_match_score(item, proper_nouns, other_keywords, content)
        if score > 0:
            scored_matches.append((score, item))

    scored_matches.sort(key=lambda x: x[0], reverse=True)
    related = [item for score, item in scored_matches[:limit]]

    print(f"✅ Found {len(related)} related items")
    return related


@router.get("/topic/{topic_id}")
async def get_content_by_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Get all content for a specific topic"""
    result = await db.execute(
        select(ContentItem).where(ContentItem.topic_id == topic_id)
    )
    content_items = result.scalars().all()
    return content_items


@router.get("/preferences/analyze")
async def analyze_user_preferences(
    request: Request,
    db: AsyncSession = Depends(get_db),
    nexus_session: Optional[str] = Cookie(default=None),
):
    """
    Analyze user's reading preferences based on their interaction history.
    Returns categories, keywords, and reading patterns.
    """
    user_id = getattr(request.state, "user_id", None)
    session_token = nexus_session

    try:
        preferences = await rss_discovery_service.analyze_user_preferences(
            db, user_id, session_token
        )
        return preferences
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze preferences: {str(e)}"
        )


@router.get("/rss/discover")
async def discover_rss_feeds(
    request: Request,
    db: AsyncSession = Depends(get_db),
    nexus_session: Optional[str] = Cookie(default=None),
):
    """
    Discover RSS feeds tailored to user's preferences.
    Returns a list of recommended RSS feeds with relevance scores.
    """
    user_id = getattr(request.state, "user_id", None)
    session_token = nexus_session

    try:
        feeds = await rss_discovery_service.discover_feeds_for_user(
            db, user_id, session_token
        )
        return {"feeds": feeds, "count": len(feeds)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to discover feeds: {str(e)}"
        )


@router.get("/rss/content")
async def get_rss_content(
    request: Request,
    db: AsyncSession = Depends(get_db),
    nexus_session: Optional[str] = Cookie(default=None),
    max_items: int = Query(20, ge=1, le=100),
):
    """
    Get personalized content from RSS feeds based on user's preferences.
    Returns aggregated content from multiple relevant RSS feeds.
    """
    user_id = getattr(request.state, "user_id", None)
    session_token = nexus_session

    try:
        items = await rss_discovery_service.get_personalized_rss_content(
            db, user_id, session_token, max_items_per_feed=max_items // 4
        )
        return {"items": items[:max_items], "count": len(items[:max_items])}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch RSS content: {str(e)}"
        )


@router.get("/suggestions/topics")
async def suggest_topics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    nexus_session: Optional[str] = Cookie(default=None),
):
    """
    Suggest topic keywords for content discovery based on user's reading history.
    Useful for search and exploration features.
    """
    user_id = getattr(request.state, "user_id", None)
    session_token = nexus_session

    try:
        suggestions = await rss_discovery_service.suggest_topics_from_preferences(
            db, user_id, session_token
        )
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate suggestions: {str(e)}"
        )


@router.get("/rss/search")
async def search_rss_feeds(
    keyword: str = Query(..., description="Keyword to search for RSS feeds"),
    max_results: int = Query(5, ge=1, le=20),
):
    """
    Search for RSS feeds by keyword using multiple discovery strategies.
    Returns validated feeds with quality scores.
    """
    try:
        feeds = await rss_discovery_service.search_feeds_by_keyword(
            keyword, max_results=max_results
        )
        return {"keyword": keyword, "feeds": feeds, "count": len(feeds)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search for feeds: {str(e)}"
        )


@router.get("/rss/auto-discover")
async def auto_discover_feeds(
    request: Request,
    db: AsyncSession = Depends(get_db),
    nexus_session: Optional[str] = Cookie(default=None),
    max_feeds: int = Query(10, ge=1, le=20),
):
    """
    Automatically discover new RSS feeds based on user's reading preferences.
    Searches for feeds matching user's top keywords and categories.
    Returns newly discovered feeds not in the curated list.
    """
    user_id = getattr(request.state, "user_id", None)
    session_token = nexus_session

    try:
        discovered_feeds = await rss_discovery_service.auto_discover_feeds_for_user(
            db, user_id, session_token, max_feeds=max_feeds
        )
        return {
            "discovered_feeds": discovered_feeds,
            "count": len(discovered_feeds),
            "message": f"Discovered {len(discovered_feeds)} new feeds based on your preferences",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to auto-discover feeds: {str(e)}"
        )
