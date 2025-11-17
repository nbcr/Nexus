"""
Content Deduplication Service

Detects duplicate stories and links them as related content.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List
from difflib import SequenceMatcher

from app.models import ContentItem


class DeduplicationService:
    """Service for detecting and handling duplicate content"""
    
    def __init__(self):
        self.title_similarity_threshold = 0.75  # 75% similar titles
        
    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles (0.0 to 1.0)"""
        if not title1 or not title2:
            return 0.0
        
        # Normalize titles
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, t1, t2).ratio()
    
    async def find_duplicate(
        self, 
        db: AsyncSession, 
        title: str, 
        url: Optional[str] = None,
        exclude_id: Optional[int] = None
    ) -> Optional[ContentItem]:
        """
        Find existing content that matches this title/URL.
        
        Args:
            db: Database session
            title: Title to check
            url: Source URL to check (exact match)
            exclude_id: Content ID to exclude from search
            
        Returns:
            Existing ContentItem if duplicate found, None otherwise
        """
        # First check for exact URL match (fastest)
        if url:
            query = select(ContentItem).where(
                ContentItem.source_urls.contains([url]),
                ContentItem.is_published == True
            )
            if exclude_id:
                query = query.where(ContentItem.id != exclude_id)
            
            result = await db.execute(query)
            existing = result.scalar_one_or_none()
            if existing:
                print(f"✓ Found duplicate by URL: {url}")
                return existing
        
        # Check for similar titles in recent content (last 7 days)
        from datetime import datetime, timedelta
        recent_cutoff = datetime.now() - timedelta(days=7)
        
        query = select(ContentItem).where(
            ContentItem.is_published == True,
            ContentItem.title.isnot(None),
            ContentItem.created_at >= recent_cutoff
        )
        if exclude_id:
            query = query.where(ContentItem.id != exclude_id)
        
        result = await db.execute(query)
        all_items = result.scalars().all()
        
        # Check title similarity
        for item in all_items:
            if item.title:
                similarity = self.calculate_title_similarity(title, item.title)
                if similarity >= self.title_similarity_threshold:
                    print(f"✓ Found duplicate by title similarity ({similarity:.2%}): '{title}' ~= '{item.title}'")
                    return item
        
        return None
    
    async def link_as_related(
        self,
        db: AsyncSession,
        primary_content_id: int,
        related_content_id: int
    ):
        """
        Link two content items as related.
        Updates source_metadata to include related content IDs.
        """
        # Get primary content
        result = await db.execute(
            select(ContentItem).where(ContentItem.id == primary_content_id)
        )
        primary = result.scalar_one_or_none()
        
        if not primary:
            return
        
        # Initialize source_metadata if needed
        if not primary.source_metadata:
            primary.source_metadata = {}
        
        # Add to related_content_ids list
        if 'related_content_ids' not in primary.source_metadata:
            primary.source_metadata['related_content_ids'] = []
        
        if related_content_id not in primary.source_metadata['related_content_ids']:
            primary.source_metadata['related_content_ids'].append(related_content_id)
            print(f"✓ Linked content {related_content_id} as related to {primary_content_id}")
    
    async def get_related_content(
        self,
        db: AsyncSession,
        content_id: int
    ) -> List[ContentItem]:
        """
        Get all related content for a content item.
        """
        # Get the content item
        result = await db.execute(
            select(ContentItem).where(ContentItem.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content or not content.source_metadata:
            return []
        
        related_ids = content.source_metadata.get('related_content_ids', [])
        if not related_ids:
            return []
        
        # Fetch related content items
        result = await db.execute(
            select(ContentItem).where(
                ContentItem.id.in_(related_ids),
                ContentItem.is_published == True
            )
        )
        return result.scalars().all()


# Global instance
deduplication_service = DeduplicationService()
