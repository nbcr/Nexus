import asyncio
import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.database import engine, Base, AsyncSessionLocal
from app.models import (
    User,
    UserSession,
    Topic,
    ContentItem,
    UserInteraction,
    UserInterestProfile,
)


async def init_database():
    """Initialize database tables"""
    print("Creating database tables...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created successfully!")


async def create_sample_data():
    """Create sample data for testing"""
    from datetime import datetime

    async with AsyncSessionLocal() as session:
        try:
            # Create sample topic
            topic = Topic(
                title="Artificial Intelligence",
                normalized_title="artificial_intelligence",
                description="The simulation of human intelligence by machines",
                trend_score=0.85,
                category="Technology",
                tags=["AI", "Machine Learning", "Technology"],
            )
            session.add(topic)
            await session.commit()  # Use commit instead of flush for simplicity

            # Create sample content
            content = ContentItem(
                topic_id=topic.id,
                content_type="summary",
                content_text="Artificial Intelligence (AI) refers to the simulation of human intelligence in machines...",
                ai_model_used="gpt-3.5-turbo",
                source_urls=["https://example.com/ai"],
                is_published=True,
            )
            session.add(content)
            await session.commit()

            print("Sample data created!")

        except Exception as e:
            print(f"Error creating sample data: {e}")
            await session.rollback()


async def main():
    """Main async function to run both tasks"""
    print("Initializing Nexus Database...")
    await init_database()
    await create_sample_data()
    print("Done!")


if __name__ == "__main__":
    # Use asyncio.run() only once at the top level
    asyncio.run(main())
