"""
Content Recommendation Service

Provides personalized content recommendations based on:
- User interaction history
- Trending topics
- User preferences
- Category preferences
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from collections import defaultdict

from app.models import (
    ContentItem, 
    Topic, 
    UserInteraction, 
    UserInterestProfile,
    User
)


class ContentRecommendationService:
    """Service for generating personalized content recommendations"""
    
    async def get_personalized_feed(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        session_token: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        exclude_ids: List[int] = None,
        cursor: Optional[str] = None
    ) -> Dict:
        """
        Get personalized content feed with cursor-based pagination.
        Shows newest content first and prevents duplicates.
        
        Args:
            db: Database session
            user_id: Optional user ID for personalized recommendations
            session_token: Optional session token for anonymous users
            page: Page number (1-indexed, used as fallback)
            page_size: Number of items per page
            exclude_ids: List of content IDs to exclude (already seen)
            cursor: ISO timestamp cursor for pagination
            
        Returns:
            Dict with items, next_cursor, and has_more flag
        """
        exclude_ids = exclude_ids or []
        
        # Get user preferences and interaction history (for future use)
        user_categories = await self._get_user_categories(db, user_id, session_token)
        user_interests = await self._get_user_interests(db, user_id)
        viewed_content_ids = await self._get_viewed_content(db, user_id, session_token)
        
        # Combine with exclude_ids
        all_excluded = set(exclude_ids + viewed_content_ids)
        
        # Build query - for now, show all content without filtering
        query = (
            select(ContentItem, Topic)
            .join(Topic, ContentItem.topic_id == Topic.id)
            .where(
                ContentItem.is_published == True,
                ContentItem.id.notin_(all_excluded) if all_excluded else True
            )
        )
        
        # TODO: Future filtering by user_categories can be added here
        # For now, show everything so we can learn user preferences
        
        # Apply cursor-based filtering (show items older than cursor)
        if cursor:
            try:
                cursor_time = datetime.fromisoformat(cursor)
                query = query.where(ContentItem.created_at < cursor_time)
            except (ValueError, TypeError):
                # Invalid cursor, ignore it
                pass
        
        # Order by newest first (created_at DESC), then by trend score
        query = query.order_by(
            desc(ContentItem.created_at),
            desc(Topic.trend_score)
        ).limit(page_size + 1)  # Fetch one extra to check if there's more
        
        result = await db.execute(query)
        items = result.all()
        
        # Check if there are more items
        has_more = len(items) > page_size
        if has_more:
            items = items[:page_size]  # Remove the extra item
        
        # Calculate relevance scores
        feed_items = []
        for content, topic in items:
            relevance_score = self._calculate_relevance(
                topic,
                content,
                user_categories,
                user_interests
            )
            
            feed_items.append({
                "content_id": content.id,
                "topic_id": topic.id,
                "title": topic.title,
                "description": topic.description,
                "category": topic.category,
                "content_type": content.content_type,
                "content_text": content.content_text,
                "source_urls": content.source_urls,
                "source_metadata": getattr(content, 'source_metadata', {}),
                "trend_score": topic.trend_score,
                "relevance_score": relevance_score,
                "created_at": content.created_at.isoformat(),
                "tags": topic.tags
            })
        
        # Determine next cursor (timestamp of last item)
        next_cursor = None
        if feed_items and has_more:
            next_cursor = feed_items[-1]["created_at"]
        
        return {
            "items": feed_items,
            "next_cursor": next_cursor,
            "has_more": has_more
        }
    
    async def get_trending_feed(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        exclude_ids: List[int] = None,
        cursor: Optional[str] = None
    ) -> Dict:
        """
        Get trending content feed with cursor-based pagination.
        
        Args:
            db: Database session
            page: Page number (1-indexed, used as fallback)
            page_size: Number of items per page
            category: Optional category filter
            exclude_ids: List of content IDs to exclude
            cursor: ISO timestamp cursor for pagination
            
        Returns:
            Dict with items, next_cursor, and has_more flag
        """
        exclude_ids = exclude_ids or []
        
        query = (
            select(ContentItem, Topic)
            .join(Topic, ContentItem.topic_id == Topic.id)
            .where(
                ContentItem.is_published == True,
                ContentItem.id.notin_(exclude_ids) if exclude_ids else True
            )
        )
        
        if category:
            query = query.where(Topic.category == category)
        
        # Apply cursor-based filtering
        if cursor:
            try:
                cursor_time = datetime.fromisoformat(cursor)
                query = query.where(ContentItem.created_at < cursor_time)
            except (ValueError, TypeError):
                pass
        
        query = query.order_by(
            desc(ContentItem.created_at),
            desc(Topic.trend_score)
        ).limit(page_size + 1)
        
        result = await db.execute(query)
        items = result.all()
        
        # Check if there are more items
        has_more = len(items) > page_size
        if has_more:
            items = items[:page_size]
        
        feed_items = []
        for content, topic in items:
            feed_items.append({
                "content_id": content.id,
                "topic_id": topic.id,
                "title": topic.title,
                "description": topic.description,
                "category": topic.category,
                "content_type": content.content_type,
                "content_text": content.content_text,
                "source_urls": content.source_urls,
                "source_metadata": getattr(content, 'source_metadata', {}),
                "trend_score": topic.trend_score,
                "created_at": content.created_at.isoformat(),
                "tags": topic.tags
            })
        
        # Determine next cursor
        next_cursor = None
        if feed_items and has_more:
            next_cursor = feed_items[-1]["created_at"]
        
        return {
            "items": feed_items,
            "next_cursor": next_cursor,
            "has_more": has_more
        }
    
    async def _get_user_categories(
        self,
        db: AsyncSession,
        user_id: Optional[int],
        session_token: Optional[str]
    ) -> List[str]:
        """Get user's preferred categories based on interaction history"""
        if not user_id and not session_token:
            return []
        
        # Query interactions joined with topics to get categories
        from app.models import UserSession
        
        query = (
            select(Topic.category, func.count().label('count'))
            .select_from(UserInteraction)
            .join(ContentItem, UserInteraction.content_item_id == ContentItem.id)
            .join(Topic, ContentItem.topic_id == Topic.id)
            .where(Topic.category.isnot(None))
        )
        
        if user_id:
            query = query.where(UserInteraction.user_id == user_id)
        elif session_token:
            query = query.join(UserSession, UserInteraction.session_id == UserSession.id).where(
                UserSession.session_token == session_token
            )
        
        query = query.group_by(Topic.category).order_by(desc('count')).limit(5)
        
        result = await db.execute(query)
        categories = [row[0] for row in result.all()]
        
        return categories
    
    async def _get_user_interests(
        self,
        db: AsyncSession,
        user_id: Optional[int]
    ) -> List[str]:
        """Get user's declared interests from profile"""
        if not user_id:
            return []
        
        profile = await db.get(UserInterestProfile, user_id)
        if profile and profile.interests:
            return profile.interests
        
        return []
    
    async def _get_viewed_content(
        self,
        db: AsyncSession,
        user_id: Optional[int],
        session_token: Optional[str]
    ) -> List[int]:
        """Get list of content IDs the user has already viewed"""
        from app.models import UserSession
        
        query = select(UserInteraction.content_item_id)
        
        if user_id:
            query = query.where(UserInteraction.user_id == user_id)
        elif session_token:
            query = query.join(UserSession, UserInteraction.session_id == UserSession.id).where(
                UserSession.session_token == session_token
            )
        else:
            return []
        
        query = query.distinct()
        result = await db.execute(query)
        
        return [row[0] for row in result.all()]
    
    def _calculate_relevance(
        self,
        topic: Topic,
        content: ContentItem,
        user_categories: List[str],
        user_interests: List[str]
    ) -> float:
        """
        Calculate relevance score for content based on user preferences.
        
        Returns score between 0 and 1
        """
        score = 0.5  # Base score
        
        # Category match
        if topic.category in user_categories:
            category_position = user_categories.index(topic.category)
            # Higher score for top categories
            score += 0.3 * (1 - category_position / len(user_categories))
        
        # Interest match (check if any interest keywords in title/description)
        if user_interests:
            text_to_check = f"{topic.title} {topic.description}".lower()
            matching_interests = sum(
                1 for interest in user_interests
                if interest.lower() in text_to_check
            )
            if matching_interests > 0:
                score += 0.2 * min(matching_interests / len(user_interests), 1.0)
        
        # Tag match
        if user_interests and topic.tags:
            matching_tags = sum(
                1 for tag in topic.tags
                if any(interest.lower() in tag.lower() for interest in user_interests)
            )
            if matching_tags > 0:
                score += 0.1 * min(matching_tags / len(topic.tags), 1.0)
        
        # Recency bonus
        age_hours = (datetime.utcnow() - content.created_at).total_seconds() / 3600
        if age_hours < 24:
            score += 0.1 * (1 - age_hours / 24)
        
        return min(score, 1.0)


# Global instance
recommendation_service = ContentRecommendationService()
