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
        exclude_ids: List[int] = None
    ) -> List[Dict]:
        """
        Get personalized content feed with infinite scroll support.
        
        Args:
            db: Database session
            user_id: Optional user ID for personalized recommendations
            session_token: Optional session token for anonymous users
            page: Page number (1-indexed)
            page_size: Number of items per page
            exclude_ids: List of content IDs to exclude (already seen)
            
        Returns:
            List of content items with topics and relevance scores
        """
        exclude_ids = exclude_ids or []
        offset = (page - 1) * page_size
        
        # Get user preferences and interaction history
        user_categories = await self._get_user_categories(db, user_id, session_token)
        user_interests = await self._get_user_interests(db, user_id)
        viewed_content_ids = await self._get_viewed_content(db, user_id, session_token)
        
        # Combine with exclude_ids
        all_excluded = set(exclude_ids + viewed_content_ids)
        
        # Build query with scoring
        query = (
            select(ContentItem, Topic)
            .join(Topic, ContentItem.topic_id == Topic.id)
            .where(
                ContentItem.is_published == True,
                ContentItem.id.notin_(all_excluded) if all_excluded else True
            )
        )
        
        # Apply category filtering with some randomness for diversity
        if user_categories:
            # 70% from preferred categories, 30% from all categories
            if page % 3 == 0:  # Every 3rd page shows diverse content
                pass  # No category filter
            else:
                query = query.where(Topic.category.in_(user_categories))
        
        # Order by trend score and recency
        query = query.order_by(
            desc(Topic.trend_score),
            desc(ContentItem.created_at)
        ).offset(offset).limit(page_size)
        
        result = await db.execute(query)
        items = result.all()
        
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
        
        # Sort by combined score (trend + relevance)
        feed_items.sort(
            key=lambda x: (x["relevance_score"] * 0.4 + x["trend_score"] * 0.6),
            reverse=True
        )
        
        return feed_items
    
    async def get_trending_feed(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        exclude_ids: List[int] = None
    ) -> List[Dict]:
        """
        Get trending content feed (non-personalized).
        
        Args:
            db: Database session
            page: Page number (1-indexed)
            page_size: Number of items per page
            category: Optional category filter
            exclude_ids: List of content IDs to exclude
            
        Returns:
            List of trending content items
        """
        exclude_ids = exclude_ids or []
        offset = (page - 1) * page_size
        
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
        
        query = query.order_by(
            desc(Topic.trend_score),
            desc(ContentItem.created_at)
        ).offset(offset).limit(page_size)
        
        result = await db.execute(query)
        items = result.all()
        
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
        
        return feed_items
    
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
