"""
Content Recommendation Service

Provides personalized content recommendations based on:
- User interaction history
- Trending topics
- User preferences
- Category preferences
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, cast, String
from collections import defaultdict
import re

from app.models import ContentItem, Topic, UserInteraction, UserInterestProfile, User


class ContentRecommendationService:
    @staticmethod
    def _strip_images_from_html(html_text: Optional[str]) -> str:
        """Remove img tags and their content from HTML, return plain text."""
        if not html_text:
            return ""
        # Remove img tags
        text = re.sub(r"<img[^>]*/?>", "", html_text)
        # Remove picture tags
        text = re.sub(r"<picture[^>]*>.*?</picture>", "", text, flags=re.DOTALL)
        # Remove figure tags with content
        text = re.sub(r"<figure[^>]*>.*?</figure>", "", text, flags=re.DOTALL)
        # Remove video and audio tags
        text = re.sub(r"<video[^>]*>.*?</video>", "", text, flags=re.DOTALL)
        text = re.sub(r"<audio[^>]*>.*?</audio>", "", text, flags=re.DOTALL)
        # Remove iframes (often contain embeds/images)
        text = re.sub(r"<iframe[^>]*>.*?</iframe>", "", text, flags=re.DOTALL)
        # Remove style tags that might define background images
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        # Remove inline styles that reference images/background images
        text = re.sub(
            r'style="[^"]*(?:background|image)[^"]*"', "", text, flags=re.IGNORECASE
        )
        return text.strip()

    async def _get_related_content(
        self,
        db: AsyncSession,
        base_content: ContentItem,
        base_topic: Topic,
        limit: int = 3,
    ) -> List[Dict]:
        """Find related content items by category and overlapping tags."""
        candidates = await self._fetch_related_candidates(db, base_content, base_topic)
        scored = self._score_and_sort_candidates(candidates, base_content, base_topic)
        return self._format_related_items(scored, limit)

    async def _fetch_related_candidates(
        self, db: AsyncSession, base_content: ContentItem, base_topic: Topic
    ) -> List[tuple]:
        """Fetch candidate related content items"""
        filters = [
            ContentItem.id != base_content.id,
            ContentItem.is_published == True,
            Topic.category == base_topic.category,
        ]

        query = (
            select(ContentItem, Topic)
            .join(Topic, ContentItem.topic_id == Topic.id)
            .where(*filters)
            .order_by(desc(ContentItem.created_at))
            .limit(20)
        )

        result = await db.execute(query)
        return result.all()

    def _score_and_sort_candidates(
        self, candidates: List[tuple], base_content: ContentItem, base_topic: Topic
    ) -> List[tuple]:
        """Score candidates by tag overlap and title similarity"""

        def score(c: ContentItem, t: Topic) -> float:
            tag_score = self._calculate_tag_overlap_score(
                base_content, base_topic, c, t
            )
            title_score = self._calculate_title_overlap_score(
                base_content, base_topic, c, t
            )
            return tag_score + title_score

        return sorted(candidates, key=lambda ct: score(ct[0], ct[1]), reverse=True)

    def _calculate_tag_overlap_score(
        self,
        base_content: ContentItem,
        base_topic: Topic,
        cand_content: ContentItem,
        cand_topic: Topic,
    ) -> float:
        """Calculate score based on tag overlap"""
        base_tags = self._extract_tags(base_content, base_topic)
        cand_tags = self._extract_tags(cand_content, cand_topic)
        overlap = base_tags.intersection(cand_tags)

        if not overlap:
            return 0.0

        return 0.6 * min(len(overlap) / max(len(base_tags) or 1, 1), 1.0)

    def _calculate_title_overlap_score(
        self,
        base_content: ContentItem,
        base_topic: Topic,
        cand_content: ContentItem,
        cand_topic: Topic,
    ) -> float:
        """Calculate score based on title keyword overlap"""
        base_words = set((base_content.title or base_topic.title or "").lower().split())
        cand_words = set((cand_content.title or cand_topic.title or "").lower().split())
        word_overlap = base_words.intersection(cand_words)

        if not word_overlap:
            return 0.0

        return 0.4 * min(len(word_overlap) / max(len(base_words) or 1, 1), 1.0)

    def _extract_tags(self, content: ContentItem, topic: Topic) -> set:
        """Extract all tags from content and topic"""
        tags = set(topic.tags or [])
        if content.source_metadata:
            tags.update(content.source_metadata.get("tags", []))
        return tags

    def _format_related_items(self, scored: List[tuple], limit: int) -> List[Dict]:
        """Format scored candidates into related item dictionaries"""
        related = []
        for content, topic in scored[:limit]:
            related.append(
                {
                    "content_id": content.id,
                    "title": content.title or topic.title,
                    "source_urls": content.source_urls,
                    "category": content.category or topic.category,
                    "created_at": content.created_at.isoformat(),
                }
            )

            return related
        """Service for generating personalized content recommendations"""

    async def get_personalized_feed(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        session_token: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        exclude_ids: List[int] = None,
        cursor: Optional[str] = None,
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

        # Build query - Show items with meaningful content
        query = (
            select(ContentItem, Topic)
            .join(Topic, ContentItem.topic_id == Topic.id)
            .where(
                ContentItem.is_published == True,
                Topic.category != "Reference",
                ContentItem.id.notin_(all_excluded) if all_excluded else True,
            )
        )

        # FIXME: Future filtering by user_categories can be added here
        # For now, show everything so we can learn user preferences

        # Apply cursor-based filtering (show items older than cursor)
        if cursor:
            try:
                cursor_time = datetime.fromisoformat(cursor)
                query = query.where(ContentItem.created_at < cursor_time)
            except (ValueError, TypeError):
                # Invalid cursor, ignore it
                pass

        # Order by:
        # 1. Most recently CREATED (not updated) - shows truly new content first
        # 2. Trend score as tiebreaker
        # This ensures newest content always appears first regardless of type
        query = query.order_by(
            desc(ContentItem.created_at),  # Show newest content first
        ).limit(
            page_size + 1
        )  # Fetch one extra to check if there's more

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
                topic, content, user_categories, user_interests
            )

            related_items = await self._get_related_content(db, content, topic, limit=3)

            feed_items.append(
                {
                    "content_id": content.id,
                    "slug": content.slug,  # Add unique slug for history tracking and direct linking
                    "topic_id": topic.id,
                    "title": (
                        content.title if content.title else topic.title
                    ),  # Use content title if available
                    "description": self._strip_images_from_html(
                        content.description
                        if content.description
                        else topic.description
                    ),  # Use content description if available, cleaned of images
                    "category": (
                        content.category if content.category else topic.category
                    ),  # Use content category if available
                    "content_type": content.content_type,
                    "content_text": self._strip_images_from_html(
                        content.content_text
                    ),  # Clean images from content text
                    "source_urls": content.source_urls,
                    "source_metadata": getattr(content, "source_metadata", {}),
                    "trend_score": topic.trend_score,
                    "relevance_score": relevance_score,
                    "created_at": content.created_at.isoformat(),
                    "updated_at": content.updated_at.isoformat(),
                    "tags": topic.tags,
                    "related_items": related_items,
                }
            )

        # Determine next cursor (timestamp of last item's created_at for pagination)
        next_cursor = None
        if feed_items and has_more:
            next_cursor = feed_items[-1]["created_at"]

        return {"items": feed_items, "next_cursor": next_cursor, "has_more": has_more}

    async def get_trending_feed(
        self,
        db: AsyncSession,
        page_size: int = 20,
        category: Optional[str] = None,
        exclude_ids: List[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict:
        """Deprecated: Use get_all_feed instead."""
        return await self.get_all_feed(
            db=db,
            page_size=page_size,
            exclude_ids=exclude_ids or [],
            cursor=cursor,
            category=category,
        )

    async def get_all_feed(
        self,
        db: AsyncSession,
        page_size: int = 20,
        exclude_ids: List[int] = None,
        cursor: Optional[str] = None,
        category: Optional[str] = None,
        categories: Optional[List[str]] = None,
    ) -> Dict:
        """Return all published content with cursor pagination; optional category filter(s)."""
        exclude_ids = exclude_ids or []

        query = self._build_base_feed_query(exclude_ids)
        query = self._apply_category_filters(query, category, categories)
        query = self._apply_cursor_filter(query, cursor)
        query = query.order_by(desc(ContentItem.created_at)).limit(page_size + 1)

        result = await db.execute(query)
        rows = result.all()

        has_more = len(rows) > page_size
        if has_more:
            rows = rows[:page_size]

        items = await self._build_feed_items(db, rows)

        next_cursor = None
        if items and has_more:
            next_cursor = items[-1]["created_at"]

        return {"items": items, "next_cursor": next_cursor, "has_more": has_more}

    def _build_base_feed_query(self, exclude_ids: List[int]):
        """Build base query for feed with exclusions"""
        where_clauses = [
            ContentItem.is_published == True,
            Topic.category != "Reference",
        ]
        if exclude_ids:
            where_clauses.append(ContentItem.id.notin_(exclude_ids))

        return (
            select(ContentItem, Topic)
            .join(Topic, ContentItem.topic_id == Topic.id)
            .where(*where_clauses)
        )

    def _apply_category_filters(
        self, query, category: Optional[str], categories: Optional[List[str]]
    ):
        """Apply category filters to feed query"""
        if categories:
            filtered_categories = [c for c in categories if c != "Reference"]
            if filtered_categories:
                query = query.where(Topic.category.in_(filtered_categories))
        elif category:
            if category == "Reference":
                return None  # Signal empty result
            query = query.where(Topic.category == category)
        return query

    def _apply_cursor_filter(self, query, cursor: Optional[str]):
        """Apply cursor-based pagination filter"""
        if not cursor:
            return query

        try:
            cursor_time = datetime.fromisoformat(cursor)
            query = query.where(ContentItem.created_at < cursor_time)
        except (ValueError, TypeError):
            pass

        return query

    async def _build_feed_items(
        self, db: AsyncSession, rows: List[tuple]
    ) -> List[Dict]:
        """Build feed item dictionaries from query results"""
        items = []
        for content, topic in rows:
            related_items = await self._get_related_content(db, content, topic, limit=3)
            items.append(
                {
                    "content_id": content.id,
                    "slug": content.slug,
                    "topic_id": topic.id,
                    "title": content.title or topic.title,
                    "description": self._strip_images_from_html(
                        content.description or topic.description
                    ),
                    "category": content.category or topic.category,
                    "content_type": content.content_type,
                    "content_text": self._strip_images_from_html(content.content_text),
                    "source_urls": content.source_urls,
                    "source_metadata": getattr(content, "source_metadata", {}),
                    "thumbnail_url": (
                        getattr(content, "source_metadata", {}) or {}
                    ).get("picture_url"),
                    "trend_score": topic.trend_score,
                    "created_at": content.created_at.isoformat(),
                    "updated_at": content.updated_at.isoformat(),
                    "tags": topic.tags,
                    "related_items": related_items,
                }
            )
        return items

    async def _get_user_categories(
        self, db: AsyncSession, user_id: Optional[int], session_token: Optional[str]
    ) -> List[str]:
        """Get user's preferred categories based on interaction history"""
        if not user_id and not session_token:
            return []

        # Query interactions joined with topics to get categories
        from app.models import UserSession

        query = (
            select(Topic.category, func.count().label("count"))
            .select_from(UserInteraction)
            .join(ContentItem, UserInteraction.content_item_id == ContentItem.id)
            .join(Topic, ContentItem.topic_id == Topic.id)
            .where(Topic.category.isnot(None))
        )

        if user_id:
            query = query.where(UserInteraction.user_id == user_id)
        else:
            # Use session_token (already checked to be not None in parent condition)
            query = query.join(
                UserSession, UserInteraction.session_id == UserSession.id
            ).where(UserSession.session_token == session_token)

        query = query.group_by(Topic.category).order_by(desc("count")).limit(5)

        result = await db.execute(query)
        categories = [row[0] for row in result.all()]

        return categories

    async def _get_user_interests(
        self, db: AsyncSession, user_id: Optional[int]
    ) -> List[str]:
        """Get user's declared interests from profile"""
        if not user_id:
            return []

        profile = await db.get(UserInterestProfile, user_id)
        if profile and profile.interests:
            return profile.interests

        return []

    async def _get_viewed_content(
        self, db: AsyncSession, user_id: Optional[int], session_token: Optional[str]
    ) -> List[int]:
        """Get list of content IDs the user has already viewed (from view history)"""
        from app.models.user import ContentViewHistory

        query = select(ContentViewHistory.content_id).where(
            ContentViewHistory.view_type
            == "seen"  # Only exclude content marked as 'seen'
        )

        if session_token:
            # Always use session_token for tracking (works for both auth and anon)
            query = query.where(ContentViewHistory.session_token == session_token)
        elif user_id:
            # Fallback to user_id if no session token
            query = query.where(ContentViewHistory.user_id == user_id)
        else:
            return []

        query = query.distinct()
        result = await db.execute(query)

        return [row[0] for row in result.all()]

    async def _get_related_queries(
        self, db: AsyncSession, parent_keyword: str
    ) -> List[Dict]:
        """
        Get related search queries for a given keyword.

        Args:
            db: Database session
            parent_keyword: The base trend title to find related queries for

        Returns:
            List of related query dictionaries with title and url
        """
        # Fetch all Search Query category topics
        query = (
            select(Topic)
            .where(Topic.category == "Search Query")
            .order_by(desc(Topic.created_at), desc(Topic.trend_score))
            .limit(200)  # Get recent queries
        )

        result = await db.execute(query)
        all_queries = result.scalars().all()

        # Filter for queries related to this specific keyword
        related = []
        parent_normalized = parent_keyword.lower().strip()

        # Extract key terms from the parent title for better matching
        # Remove common words and special characters
        key_terms = [term for term in parent_normalized.split() if len(term) > 3]

        for topic in all_queries:
            # Check if any tag matches key terms from the parent keyword
            if topic.tags:
                for tag in topic.tags:
                    tag_lower = str(tag).lower()
                    # Match if any key term is in the tag
                    if (
                        any(term in tag_lower for term in key_terms)
                        or parent_normalized in tag_lower
                    ):
                        related.append(
                            {
                                "title": topic.title,
                                "url": f"https://trends.google.com/trends/explore?geo=CA&q={topic.title}",
                                "trend_score": topic.trend_score,
                            }
                        )
                        break  # Don't add the same topic multiple times

                # Limit to top 5 related queries
                if len(related) >= 5:
                    break

        return related

    def _calculate_relevance(
        self,
        topic: Topic,
        content: ContentItem,
        user_categories: List[str],
        user_interests: List[str],
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
                1 for interest in user_interests if interest.lower() in text_to_check
            )
            if matching_interests > 0:
                score += 0.2 * min(matching_interests / len(user_interests), 1.0)

        # Tag match
        if user_interests and topic.tags:
            matching_tags = sum(
                1
                for tag in topic.tags
                if any(interest.lower() in tag.lower() for interest in user_interests)
            )
            if matching_tags > 0:
                score += 0.1 * min(matching_tags / len(topic.tags), 1.0)

        # Recency bonus
        age_hours = (
            datetime.now(timezone.utc) - content.created_at
        ).total_seconds() / 3600
        if age_hours < 24:
            score += 0.1 * (1 - age_hours / 24)

        return min(score, 1.0)


# Global instance
recommendation_service = ContentRecommendationService()
