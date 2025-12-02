"""
Content Router

This module handles content-related endpoints including:
- Personalized infinite scroll feed
- List all content items (with pagination)
- Get specific content item details
- List content items by topic
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Annotated, Optional

from app.db import AsyncSessionLocal
from app.models import ContentItem, Topic, User
from app.schemas import (
    ContentItem as ContentItemSchema,
    ContentWithTopic,
    Topic as TopicSchema,
)
from app.services.content_recommendation import recommendation_service
from app.services.article_scraper import article_scraper
from app.api.v1.deps import get_db, get_current_user

# Router Configuration
router = APIRouter()


@router.get(
    "/feed",
    responses={
        200: {"description": "Personalized content feed"},
        400: {"description": "Invalid pagination parameters"},
    },
)
async def get_personalized_feed(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    category: Optional[str] = Query(None, description="Filter by category"),
    exclude_ids: Optional[str] = Query(
        None, description="Comma-separated list of content IDs to exclude"
    ),
    current_user: Optional[User] = Depends(get_current_user),
    nexus_session: Optional[str] = Cookie(default=None),
):
    """
    Get personalized content feed with infinite scroll support.

    This endpoint provides:
    - Personalized recommendations based on user history
    - Trending content from Google Trends
    - Category filtering
    - Infinite scroll pagination
    - Exclusion of already-viewed content

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 50)
        category: Optional category filter
        exclude_ids: Comma-separated list of content IDs already displayed
        current_user: Authenticated user (optional)
        nexus_session: Anonymous session cookie (optional)
        db: Database session

    Returns:
        List of content items with relevance scores
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

    # Get session token for anonymous users
    session_token = nexus_session or request.cookies.get("nexus_session")
    user_id = current_user.id if current_user else None

    # Get personalized feed
    if category:
        # If filtering by category, use trending feed
        feed_items = await recommendation_service.get_trending_feed(
            db=db,
            page=page,
            page_size=page_size,
            category=category,
            exclude_ids=excluded_ids,
        )
    else:
        # Use personalized feed
        feed_items = await recommendation_service.get_personalized_feed(
            db=db,
            user_id=user_id,
            session_token=session_token,
            page=page,
            page_size=page_size,
            exclude_ids=excluded_ids,
        )

    return {
        "page": page,
        "page_size": page_size,
        "items": feed_items,
        "has_more": len(feed_items) == page_size,
        "is_personalized": user_id is not None or session_token is not None,
    }


@router.get(
    "/trending-feed",
    responses={
        200: {"description": "Trending content feed"},
        400: {"description": "Invalid pagination parameters"},
    },
)
async def get_trending_feed_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    category: Optional[str] = Query(None, description="Filter by category"),
    exclude_ids: Optional[str] = Query(
        None, description="Comma-separated list of content IDs to exclude"
    ),
):
    """
    Get trending content feed (non-personalized).

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 50)
        category: Optional category filter
        exclude_ids: Comma-separated list of content IDs already displayed
        db: Database session

    Returns:
        List of trending content items
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

    feed_items = await recommendation_service.get_trending_feed(
        db=db,
        page=page,
        page_size=page_size,
        category=category,
        exclude_ids=excluded_ids,
    )

    return {
        "page": page,
        "page_size": page_size,
        "items": feed_items,
        "has_more": len(feed_items) == page_size,
    }


@router.get(
    "/",
    response_model=List[ContentWithTopic],
    responses={
        200: {"description": "List of content items with their topics"},
        400: {"description": "Invalid pagination parameters"},
    },
)
async def get_content_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> List[dict]:
    """
    Get a paginated list of content items with their associated topics.

    Args:
        skip: Number of items to skip (pagination offset)
        limit: Maximum number of items to return
        db: Database session dependency

    Returns:
        List of content items with their topics
    """
    result = await db.execute(
        select(ContentItem, Topic)
        .join(Topic, ContentItem.topic_id == Topic.id)
        .offset(skip)
        .limit(limit)
    )

    content_items = []
    for content_item, topic in result.all():
        content_dict = ContentItemSchema.model_validate(content_item).model_dump()
        content_dict["topic"] = TopicSchema.model_validate(topic).model_dump()
        content_items.append(content_dict)

    return content_items


@router.get(
    "/{content_id}",
    response_model=ContentWithTopic,
    responses={
        200: {"description": "Content item details"},
        404: {"description": "Content item not found"},
    },
)
async def get_content_item(
    content_id: Annotated[int, Path(ge=1)], db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """
    Get a specific content item by its ID.

    Args:
        content_id: ID of the content item to retrieve
        db: Database session dependency

    Returns:
        Content item with its topic

    Raises:
        HTTPException: If content item is not found
    """
    result = await db.execute(
        select(ContentItem, Topic)
        .join(Topic, ContentItem.topic_id == Topic.id)
        .where(ContentItem.id == content_id)
    )

    row = result.first()
    if not row:
        raise HTTPException(
            status_code=404, detail=f"Content item with id {content_id} not found"
        )

    content_item, topic = row
    content_dict = ContentItemSchema.model_validate(content_item).model_dump()
    content_dict["topic"] = TopicSchema.model_validate(topic).model_dump()

    return content_dict


@router.get(
    "/topic/{topic_id}",
    response_model=List[ContentItemSchema],
    responses={
        200: {"description": "List of content items for the topic"},
        404: {"description": "Topic not found"},
    },
)
async def get_content_by_topic(
    topic_id: Annotated[int, Path(ge=1)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> List[ContentItem]:
    """
    Get all content items for a specific topic.

    Args:
        topic_id: ID of the topic to get content for
        skip: Number of items to skip (pagination offset)
        limit: Maximum number of items to return
        db: Database session dependency

    Returns:
        List of content items for the topic

    Raises:
        HTTPException: If topic is not found
    """
    # First check if topic exists
    topic = await db.execute(select(Topic).where(Topic.id == topic_id))
    if not topic.scalar_one_or_none():
        raise HTTPException(
            status_code=404, detail=f"Topic with id {topic_id} not found"
        )

    result = await db.execute(
        select(ContentItem)
        .where(ContentItem.topic_id == topic_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/article/{content_id}",
    responses={
        200: {"description": "Article content retrieved with related items"},
        404: {"description": "Content not found or article unavailable"},
    },
)
async def get_article_content(
    content_id: int = Path(..., ge=1, description="Content ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch and return the full article content for a content item.

    Scrapes the article from the source URL and returns readable content,
    along with related content items (e.g., trending searches related to news stories).

    Args:
        content_id: ID of the content item
        db: Database session

    Returns:
        Dict with article data and related_items list

    Raises:
        HTTPException: If content not found or scraping fails
    """
    # Get content item from database
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_id))
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Get the source URL
    if not content.source_urls or len(content.source_urls) == 0:
        raise HTTPException(status_code=404, detail="No source URL available")

    source_url = content.source_urls[0]

    # Scrape the article
    article_data = await article_scraper.fetch_article(source_url)

    if not article_data:
        raise HTTPException(
            status_code=404, detail="Unable to fetch article content from source"
        )

    # Find related content items (after scraping succeeds)
    try:
        related_items = await find_related_content(db, content)
    except Exception as e:
        print(f"❌ Error finding related content: {e}")
        related_items = []

    # Add related items to response
    article_data["related_items"] = [
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

    return article_data


async def find_related_content(
    db: AsyncSession, content: ContentItem, limit: int = 5
) -> List[ContentItem]:
    """
    Find related content items based on title similarity, tags, and keywords.

    For news articles: find related trending searches
    For trending searches: find related news articles
    """
    from sqlalchemy import or_, and_, func as sql_func

    related = []
    title_lower = content.title.lower()

    # Extract key terms from title (simple approach - split by spaces and filter common words)
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "up",
        "down",
        "out",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "s",
        "t",
        "just",
        "don",
        "now",
        "their",
        "called",
        "begging",
    }

    title_words = [w.strip(".,!?:;\"'-()[]{}") for w in title_lower.split()]
    keywords = [
        w for w in title_words if len(w) > 2 and w not in stop_words
    ]  # Lowered from 3 to 2 chars, get all keywords

    # Prioritize proper nouns and important terms (capitalized in original title)
    original_words = content.title.split()
    proper_nouns = []
    for word in original_words:
        clean = word.strip(".,!?:;\"'-()[]{}")
        if clean and clean[0].isupper() and clean.lower() not in stop_words:
            proper_nouns.append(clean.lower())

    # Use proper nouns first, then other keywords
    priority_keywords = list(set(proper_nouns))[:8]  # Get up to 8 proper nouns
    if len(priority_keywords) < 3:
        # Add more keywords if we don't have enough proper nouns
        priority_keywords.extend(
            [k for k in keywords if k not in priority_keywords][
                : 8 - len(priority_keywords)
            ]
        )

    if not priority_keywords:
        return []

    print(
        f"🔍 Finding related content for '{content.title}' using keywords: {priority_keywords}"
    )

    # Build query to find related content
    # Look for items that share keywords in title
    conditions = []
    for keyword in priority_keywords:
        conditions.append(sql_func.lower(ContentItem.title).contains(keyword))

    # Find related items (exclude self)
    result = await db.execute(
        select(ContentItem)
        .where(
            and_(
                ContentItem.id != content.id,
                ContentItem.is_published == True,
                or_(*conditions),
            )
        )
        .limit(limit * 2)  # Get more results to filter
    )

    all_matches = result.scalars().all()

    # Score and sort by relevance
    scored_matches = []
    for item in all_matches:
        score = 0
        item_title_lower = item.title.lower()

        # Count keyword matches
        for keyword in priority_keywords:
            if keyword in item_title_lower:
                score += 2 if keyword in proper_nouns else 1

        # Prefer different sources (news vs search queries)
        source = item.source_metadata.get("source", "") if item.source_metadata else ""
        content_source = (
            content.source_metadata.get("source", "") if content.source_metadata else ""
        )
        if source != content_source:
            score += 3

        # Prefer items with pytrends tag if current item is news, and vice versa
        has_pytrends = "pytrends" in (item.tags or [])
        content_has_pytrends = "pytrends" in (content.tags or [])
        if has_pytrends != content_has_pytrends:
            score += 5

        scored_matches.append((score, item))

    # Sort by score descending and take top results
    scored_matches.sort(key=lambda x: x[0], reverse=True)
    related = [item for score, item in scored_matches[:limit] if score > 0]

    print(f"✅ Found {len(related)} related items")

    return related
