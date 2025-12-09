import asyncio
import time
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Cookie  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore
from sqlalchemy import select  # pyright: ignore[reportMissingImports]
from typing import List, Optional
from datetime import datetime, timezone

from app.db import AsyncSessionLocal
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

from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

# In-memory cache for thumbnail fetch attempts (content_id -> (picture_url, timestamp))
# Prevents hammering the database/scraper for items without pictures
_thumbnail_cache: dict[int, tuple[Optional[str], float]] = {}
_THUMBNAIL_CACHE_TTL = 300  # 5 minutes

# Constants
LOGGER_NAME = "uvicorn.error"
CONTENT_NOT_FOUND = "Content not found"


class CategoriesResponse(BaseModel):
    categories: List[str]


class ThumbnailResponse(BaseModel):
    picture_url: Optional[str]


class ProxyRequest(BaseModel):
    url: str


async def get_db():
    async with AsyncSessionLocal() as session:
        return session


@router.get("/categories", response_model=CategoriesResponse)
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    """Return all unique categories from ContentItem and Topic tables."""
    import logging

    logger = logging.getLogger(LOGGER_NAME)
    try:
        from sqlalchemy import select, distinct

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
        logger.error(f"Error in /categories endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch categories")


@router.get("/feed")
async def get_personalized_feed(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    category: Optional[str] = Query(None),
    categories: Optional[str] = Query(None),  # New: comma-separated list
    exclude_ids: Optional[str] = Query(None),
    cursor: Optional[str] = Query(None),
    nexus_session: Optional[str] = Cookie(default=None),
):
    """
    Get personalized content feed with cursor-based pagination.
    Shows newest content first and prevents duplicates.
    Supports multi-category filtering via 'categories' param (comma-separated).
    """
    # Parse exclude_ids
    excluded_ids = []
    if exclude_ids:
        try:
            excluded_ids = [
                int(id.strip()) for id in exclude_ids.split(",") if id.strip()
            ]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid exclude_ids format")

    # Parse categories (multi-select support)
    category_list = None
    if categories:
        category_list = [cat.strip() for cat in categories.split(",") if cat.strip()]
    elif category:
        category_list = [category]

    # Get session token for anonymous users
    session_token = nexus_session or request.cookies.get("nexus_session")

    import logging

    logger = logging.getLogger(LOGGER_NAME)

    # Sanitize user input for logging to prevent log injection
    safe_category_list = (
        str(category_list).replace("\n", "").replace("\r", "")
        if category_list
        else None
    )
    safe_exclude_ids = str(exclude_ids).replace("\n", "").replace("\r", "")
    safe_cursor = str(cursor).replace("\n", "").replace("\r", "") if cursor else None

    logger.info(
        f"Feed request: page={page}, categories={safe_category_list}, exclude_ids={safe_exclude_ids}, cursor={safe_cursor}"
    )
    # Feed selection - when no categories specified, show all feed (not personalized)
    if category_list and "all" in [c.lower() for c in category_list]:
        logger.info("Category 'All' selected: returning all items")
        result = await recommendation_service.get_all_feed(
            db=db,
            page_size=page_size,
            exclude_ids=excluded_ids,
            cursor=cursor,
        )
    elif category_list:
        # Filter by multiple categories
        logger.info(f"Filtering feed by categories: {safe_category_list}")
        result = await recommendation_service.get_all_feed(
            db=db,
            page_size=page_size,
            exclude_ids=excluded_ids,
            cursor=cursor,
            categories=category_list,
        )
    else:
        # No category filter = show all content
        logger.info("No categories selected: returning all items")
        result = await recommendation_service.get_all_feed(
            db=db,
            page_size=page_size,
            exclude_ids=excluded_ids,
            cursor=cursor,
        )

    # Trigger background scraping for articles without content
    # This happens in parallel without blocking the response
    async def background_scrape_articles():
        """Background scraping task - runs in separate worker"""
        try:
            articles_to_scrape = [
                item
                for item in result["items"]
                if (not item.get("facts") or not item.get("facts").strip())
                and item.get("source_urls")
            ]

            if articles_to_scrape:
                async with AsyncSessionLocal() as bg_db:
                    for item in articles_to_scrape[:5]:  # Limit to 5 per request
                        try:
                            content = await bg_db.get(ContentItem, item["content_id"])
                            if content and (
                                not content.facts or not content.facts.strip()
                            ):
                                source_url = (
                                    content.source_urls[0]
                                    if content.source_urls
                                    else None
                                )
                                if source_url:
                                    await _scrape_and_store_article(
                                        content, source_url, bg_db
                                    )
                        except Exception as e:
                            logger.debug(
                                f"Background scrape error for {item['content_id']}: {e}"
                            )
        except Exception as e:
            logger.debug(f"Background scraping task failed: {e}")

    # Fire and forget - don't await
    asyncio.create_task(background_scrape_articles())

    return {
        "page": page,
        "page_size": page_size,
        "items": result["items"],
        "next_cursor": result["next_cursor"],
        "has_more": result["has_more"],
        "is_personalized": session_token is not None,
    }


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
        and len(content.content_text) > 100
        and not content.content_text.startswith("Trending topic")
    ):
        snippet = (
            content.content_text[:800]
            if len(content.content_text) > 800
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
    from datetime import timezone

    article_data = await asyncio.to_thread(article_scraper.fetch_article, source_url)

    # Always mark scraping as attempted
    if not content.source_metadata:
        content.source_metadata = {}
    content.source_metadata["scraped_at"] = datetime.now(timezone.utc).isoformat()

    if not article_data or not article_data.get("content"):
        await db.commit()
        return None

    # Store full content in content_text and extracted facts in facts field
    full_content = article_data["content"]
    content.content_text = full_content
    content.facts = full_content  # Facts are the same as content (already extracted by _limit_to_excerpt)

    if article_data.get("title"):
        content.title = article_data["title"]
    if article_data.get("author"):
        content.source_metadata["author"] = article_data["author"]
    if article_data.get("published_date"):
        content.source_metadata["published_date"] = article_data["published_date"]

    # Download and optimize image during scraping
    if article_data.get("image_url"):
        try:
            local_image_path = await asyncio.to_thread(
                article_scraper.download_and_optimize_image,
                article_data["image_url"],
                content.id,
            )
            if local_image_path:
                content.local_image_path = local_image_path
                print(
                    f"✅ Stored optimized image for content {content.id}: {local_image_path}"
                )
        except Exception as e:
            print(f"⚠️ Failed to optimize image: {e}")

    await db.commit()

    # Generate snippet from facts
    snippet = content.facts[:800] if len(content.facts) > 800 else content.facts
    return snippet


def _is_rate_limit_error(error: Exception) -> bool:
    """Check if error is rate-limit related."""
    error_msg = str(error).lower()
    return any(keyword in error_msg for keyword in ["rate", "limit", "429", "too many"])


def _get_rate_limit_response() -> dict:
    """Return dad joke rate limit response."""
    import secrets

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
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail=CONTENT_NOT_FOUND)

    # Check if already scraped
    if content.facts and content.facts.strip():
        snippet = content.facts[:800] if len(content.facts) > 800 else content.facts
        return {
            "snippet": snippet,
            "full_content_available": True,
            "rate_limited": False,
        }

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
            import logging

            logger = logging.getLogger(LOGGER_NAME)
            logger.error(f"Background scrape failed for content {content_id}: {e}")

    # Fire and forget - don't await
    asyncio.create_task(background_scrape())

    # Return description immediately while scraping happens in background
    return {
        "snippet": content.description or None,
        "rate_limited": False,
        "status": "fetching",
    }


@router.get("/snippet/{content_id}/priority")
async def get_content_snippet_priority(
    content_id: int,
    db: AsyncSession = Depends(get_db),
    timeout: int = Query(5, ge=1, le=30),
):
    """
    Fetch article snippet on-demand with user waiting (e.g., card expansion).
    Attempts to scrape immediately and returns within timeout.
    Shows loading state if scraping takes longer than timeout.
    """
    # Get content from database
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail=CONTENT_NOT_FOUND)

    # Check if already scraped
    if content.facts and content.facts.strip():
        snippet = content.facts[:800] if len(content.facts) > 800 else content.facts
        return {
            "snippet": snippet,
            "full_content_available": True,
            "rate_limited": False,
            "status": "ready",
        }

    # Validate source URL
    source_url = _get_source_url(content)
    if not source_url:
        return {
            "snippet": content.description or None,
            "rate_limited": False,
            "status": "ready",
        }

    # Try to scrape immediately with timeout
    try:
        # Use asyncio.wait_for to enforce timeout
        snippet = await asyncio.wait_for(
            _scrape_and_store_article(content, source_url, db),
            timeout=float(timeout),
        )

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
            "status": "loading",
        }
    except Exception as e:
        if _is_rate_limit_error(e):
            return _get_rate_limit_response()
        import logging

        logger = logging.getLogger(LOGGER_NAME)
        logger.debug(f"Priority scrape error for {content_id}: {e}")
        # Return failed status when scraping fails
        return {
            "snippet": None,
            "rate_limited": False,
            "status": "failed",
        }

    # Fallback to description
    return {
        "snippet": content.description or None,
        "rate_limited": False,
        "status": "ready",
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


async def _fetch_article_by_type(source_url: str) -> dict:
    """Fetch article content based on URL type (search vs regular article)."""
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
    # Get content item from database
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail=CONTENT_NOT_FOUND)

    # Check if we have valid cached content (must have been scraped, not just RSS description)
    has_scraped_content = (
        content.content_text
        and len(content.content_text) > 100
        and not content.content_text.startswith("Trending topic")
        and content.source_metadata
        and content.source_metadata.get("scraped_at")
    )

    if has_scraped_content:
        # Use cached content - construct response from database
        article_data = {
            "title": content.title,
            "content": content.content_text,
            "author": (
                content.source_metadata.get("author")
                if content.source_metadata
                else None
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
                content.source_urls[0].split("/")[2] if content.source_urls else None
            ),
        }
    else:
        # Need to scrape - validate source URL
        source_url = _get_source_url(content)
        if not source_url:
            raise HTTPException(status_code=404, detail="No source URL available")

        # Scrape appropriate content based on URL type
        article_data = await _fetch_article_by_type(source_url)
        if not article_data:
            raise HTTPException(
                status_code=404, detail="Unable to fetch content from source"
            )

        # Save scraped content
        await _save_scraped_content(content, article_data, content_id, db)

    # Find related content items
    try:
        related_items = await find_related_content(db, content)
    except Exception as e:
        print(f"❌ Error finding related content: {e}")
        related_items = []

    # Add related items to response
    article_data["related_items"] = _format_related_items(related_items)

    return article_data


@router.get("/thumbnail/{content_id}", response_model=ThumbnailResponse)
async def get_thumbnail(content_id: int, db: AsyncSession = Depends(get_db)):
    """Ensure a thumbnail is available for a content item and return it.
    If missing, scrape the article to fetch image_url and persist to source_metadata.picture_url.
    Uses in-memory caching to prevent hammering database on repeated failed attempts.
    """
    import logging

    logger = logging.getLogger(LOGGER_NAME)

    try:
        # Check cache first
        current_time = time.time()
        if content_id in _thumbnail_cache:
            cached_url, timestamp = _thumbnail_cache[content_id]
            if current_time - timestamp < _THUMBNAIL_CACHE_TTL:
                return ThumbnailResponse(picture_url=cached_url)
            else:
                # Cache expired
                del _thumbnail_cache[content_id]

        result = await db.execute(
            select(ContentItem).where(ContentItem.id == content_id)
        )
        content = result.scalar_one_or_none()
        if not content:
            # Cache negative result for 5 min to avoid repeated 404 queries
            _thumbnail_cache[content_id] = (None, current_time)
            raise HTTPException(status_code=404, detail=CONTENT_NOT_FOUND)

        # If already have a picture_url, cache and return it
        pic = (
            (content.source_metadata or {}).get("picture_url")
            if content.source_metadata
            else None
        )
        if pic:
            _thumbnail_cache[content_id] = (pic, current_time)
            return ThumbnailResponse(picture_url=pic)

        # Try to scrape the article to get image_url
        if not content.source_urls or len(content.source_urls) == 0:
            _thumbnail_cache[content_id] = (None, current_time)
            return ThumbnailResponse(picture_url=None)

        source_url = content.source_urls[0]
        is_search_url = (
            "duckduckgo.com" in source_url
            or "google.com/search" in source_url
            or "bing.com/search" in source_url
        )
        try:
            if is_search_url:
                data = await asyncio.to_thread(
                    article_scraper.fetch_search_context, source_url
                )
            else:
                data = await asyncio.to_thread(
                    article_scraper.fetch_article, source_url
                )
            if data and data.get("image_url"):
                if not content.source_metadata:
                    content.source_metadata = {}
                content.source_metadata["picture_url"] = data["image_url"]
                content.source_metadata["scraped_at"] = datetime.now(
                    timezone.utc
                ).isoformat()
                await db.commit()
                _thumbnail_cache[content_id] = (data["image_url"], current_time)
                return ThumbnailResponse(picture_url=data["image_url"])
        except Exception:
            await db.rollback()
            # Still cache the failed attempt to avoid retrying immediately
            _thumbnail_cache[content_id] = (None, current_time)
            logger.exception(
                "Thumbnail scrape failed",
                extra={"content_id": content_id, "source_url": source_url},
            )
            return ThumbnailResponse(picture_url=None)

        return ThumbnailResponse(picture_url=None)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Thumbnail endpoint failed", extra={"content_id": content_id})
        raise HTTPException(status_code=500, detail="Failed to fetch thumbnail")


@router.get("/proxy/image")
async def image_proxy(
    url: str, w: int = Query(None, ge=1, le=1200), h: int = Query(None, ge=1, le=1200)
):
    """Proxy and optionally resize remote images to avoid mixed-content/CORS issues."""
    import httpx  # pyright: ignore[reportMissingImports]
    import logging
    from urllib.parse import urlparse
    from io import BytesIO

    logger = logging.getLogger("uvicorn.error")

    # Validate URL to prevent SSRF attacks
    try:
        parsed = urlparse(url)

        # Only allow http and https schemes
        if parsed.scheme not in ("http", "https"):
            raise HTTPException(status_code=400, detail="Invalid URL scheme")

        # Block private/internal IP ranges
        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(status_code=400, detail="Invalid URL")

        # Block localhost and private IP ranges
        blocked_hosts = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "10.",
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.20.",
            "172.21.",
            "172.22.",
            "172.23.",
            "172.24.",
            "172.25.",
            "172.26.",
            "172.27.",
            "172.28.",
            "172.29.",
            "172.30.",
            "172.31.",
            "192.168.",
            "169.254.",
        ]

        hostname_lower = hostname.lower()
        if any(
            hostname_lower == blocked or hostname_lower.startswith(blocked)
            for blocked in blocked_hosts
        ):
            raise HTTPException(
                status_code=403, detail="Access to internal resources is forbidden"
            )

        # Additional check for IPv6 localhost
        if hostname_lower in ("::1", "::ffff:127.0.0.1"):
            raise HTTPException(
                status_code=403, detail="Access to internal resources is forbidden"
            )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid URL format")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=5.0) as client:
            safe_url = url.replace("\n", "").replace("\r", "")
            logger.info(f"Image proxy fetch: {safe_url}")
            resp = await client.get(url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "image/jpeg")
            image_data = resp.content

            # Resize image if dimensions specified
            if (w or h) and content_type.startswith("image/"):
                try:
                    from PIL import Image

                    img = Image.open(BytesIO(image_data))

                    # Default dimensions for feed display
                    target_w = w or img.width
                    target_h = h or img.height

                    # Maintain aspect ratio
                    img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)

                    # Save optimized image as WebP for better compression
                    output = BytesIO()
                    save_kwargs = {"quality": 80, "method": 6}
                    img.save(output, format="WEBP", **save_kwargs)
                    image_data = output.getvalue()
                    content_type = "image/webp"
                except Exception as e:
                    logger.warning(f"Image resize failed: {e}, returning original")
                    # Return original if resize fails
                    pass

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
        safe_url = url.replace("\n", "").replace("\r", "")
        logger.warning(f"Image proxy failed for URL: {safe_url}")
        raise HTTPException(status_code=404, detail="Unable to fetch image")


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
    from sqlalchemy import func

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
    from sqlalchemy import or_, and_

    # Extract and filter keywords
    proper_nouns, other_keywords = _extract_keywords(content.title)
    priority_keywords = _filter_stop_words(proper_nouns, other_keywords)

    if not priority_keywords:
        return []

    print(
        f"🔍 Finding related content for '{content.title}' using keywords: {priority_keywords}"
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
