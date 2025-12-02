"""History tracking endpoints."""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from pydantic import BaseModel

from app.db import get_db
from app.models.user import ContentViewHistory, User
from app.models.content import ContentItem
from app.api.v1.deps import get_current_session


router = APIRouter()


class ViewHistoryItem(BaseModel):
    """Schema for view history item."""

    id: int
    content_id: int
    content_slug: str
    title: str
    view_type: str
    viewed_at: datetime
    time_spent_seconds: Optional[int]

    class Config:
        from_attributes = True


class ViewHistoryResponse(BaseModel):
    """Schema for history response with pagination."""

    items: List[ViewHistoryItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class RecordViewRequest(BaseModel):
    """Schema for recording a view."""

    content_id: int
    content_slug: str
    view_type: str  # 'seen', 'clicked', 'read'
    time_spent_seconds: Optional[int] = None


@router.post("/record", status_code=201)
async def record_view(
    view_request: RecordViewRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    session=Depends(get_current_session),
):
    """
    Record that a user has viewed content.

    - **content_id**: ID of the content item
    - **content_slug**: Unique slug of the content
    - **view_type**: Type of view ('seen', 'clicked', 'read')
    - **time_spent_seconds**: Optional engagement time
    """
    # Check if already recorded (prevent duplicates for 'seen' type)
    if view_request.view_type == "seen":
        from sqlalchemy import select, and_

        stmt = select(ContentViewHistory).where(
            and_(
                ContentViewHistory.session_token == session.session_token,
                ContentViewHistory.content_id == view_request.content_id,
                ContentViewHistory.view_type == "seen",
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return {"message": "Already recorded", "id": existing.id}

    # Create history record
    history = ContentViewHistory(
        user_id=session.user_id,
        session_token=session.session_token,
        content_id=view_request.content_id,
        content_slug=view_request.content_slug,
        view_type=view_request.view_type,
        time_spent_seconds=view_request.time_spent_seconds,
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return {"message": "View recorded", "id": history.id}


@router.get("/viewed", response_model=ViewHistoryResponse)
async def get_viewed_history(
    request: Request,
    response: Response,
    view_type: Optional[str] = Query(
        None, description="Filter by view type: 'seen', 'clicked', 'read'"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    session=Depends(get_current_session),
):
    """
    Get user's view history with optional filtering.

    - **view_type**: Optional filter ('seen', 'clicked', 'read')
    - **page**: Page number (starts at 1)
    - **page_size**: Items per page (max 100)
    """
    from sqlalchemy import select, func
    from sqlalchemy.orm import joinedload

    # Build base select
    stmt = (
        select(ContentViewHistory, ContentItem.title)
        .join(ContentItem, ContentViewHistory.content_id == ContentItem.id)
        .where(ContentViewHistory.session_token == session.session_token)
    )

    if view_type:
        stmt = stmt.where(ContentViewHistory.view_type == view_type)

    stmt = stmt.order_by(desc(ContentViewHistory.viewed_at))

    # Get total count (separate query)
    count_stmt = (
        select(func.count())
        .select_from(ContentViewHistory)
        .where(ContentViewHistory.session_token == session.session_token)
    )
    if view_type:
        count_stmt = count_stmt.where(ContentViewHistory.view_type == view_type)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for history, title in rows:
        if title is None:
            print(
                f"DEBUG: Missing title for history id={history.id}, content_id={history.content_id}, content_slug={history.content_slug}"
            )
        items.append(
            ViewHistoryItem(
                id=history.id,
                content_id=history.content_id,
                content_slug=history.content_slug,
                title=title if title is not None else "",
                view_type=history.view_type,
                viewed_at=history.viewed_at,
                time_spent_seconds=history.time_spent_seconds,
            )
        )

    has_more = (offset + page_size) < total

    return ViewHistoryResponse(
        items=items, total=total, page=page, page_size=page_size, has_more=has_more
    )


@router.get("/seen-ids")
async def get_seen_content_ids(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    session=Depends(get_current_session),
):
    """
    Get list of content IDs the user has already seen.
    Used for duplicate prevention in feed.
    """
    from sqlalchemy import select, and_

    stmt = (
        select(ContentViewHistory.content_id)
        .where(
            and_(
                ContentViewHistory.session_token == session.session_token,
                ContentViewHistory.view_type == "seen",
            )
        )
        .distinct()
    )
    result = await db.execute(stmt)
    seen_ids = result.scalars().all()
    return {"seen_ids": seen_ids}


@router.delete("/clear")
async def clear_history(
    request: Request,
    response: Response,
    view_type: Optional[str] = Query(
        None, description="Clear specific type or all if None"
    ),
    db: Session = Depends(get_db),
    session=Depends(get_current_session),
):
    """
    Clear user's view history.

    - **view_type**: Optional - clear only specific type, or all if not provided
    """
    from sqlalchemy import delete

    stmt = delete(ContentViewHistory).where(
        ContentViewHistory.session_token == session.session_token
    )
    if view_type:
        stmt = stmt.where(ContentViewHistory.view_type == view_type)
    result = await db.execute(stmt)
    await db.commit()
    deleted = result.rowcount
    return {"message": f"Cleared {deleted} history items"}
