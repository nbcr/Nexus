import asyncio
from app.database import engine, Base
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
        # Drop all tables (use with caution!)
        # await conn.run_sync(Base.metadata.drop_all)

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created successfully!")


async def create_sample_data():
    """Create sample data for testing"""
    from app.database import AsyncSessionLocal
    from datetime import datetime

    async with AsyncSessionLocal() as session:
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
        await session.flush()

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


if __name__ == "__main__":
    print("Initializing Nexus Database...")
    asyncio.run(init_database())
    asyncio.run(create_sample_data())
    print("Done!")
