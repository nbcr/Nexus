from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# Topic Schemas
class TopicBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    trend_score: Optional[float] = 0.0
    tags: Optional[List[str]] = []

class TopicCreate(TopicBase):
    pass

class TopicUpdate(TopicBase):
    title: Optional[str] = None

class Topic(TopicBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    normalized_title: str
    created_at: datetime
    updated_at: datetime

# Content Item Schemas
class ContentItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    content_type: str
    content_text: str
    ai_model_used: str
    source_urls: Optional[List[str]] = []
    source_metadata: Optional[Dict[str, Any]] = {}
    is_published: bool = False

class ContentItemCreate(ContentItemBase):
    topic_id: int

class ContentItemUpdate(ContentItemBase):
    title: Optional[str] = None
    content_type: Optional[str] = None
    content_text: Optional[str] = None

class ContentItem(ContentItemBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    topic_id: int
    created_at: datetime
    updated_at: datetime

# User Preference Schemas
class UserPreferences(BaseModel):
    interests: List[str] = []
    preferred_categories: List[str] = []
    reading_preferences: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)

class UserProfile(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    social_links: Dict[str, str] = {}
    expertise: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class UserStats(BaseModel):
    total_interactions: int = 0
    content_views: int = 0
    topic_follows: int = 0
    average_engagement: float = 0.0
    favorite_categories: List[str] = []
    activity_by_day: Dict[str, int] = {}

    model_config = ConfigDict(from_attributes=True)

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[str] = None

class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

# Response Schemas
class TopicWithContent(Topic):
    content_items: List[ContentItem] = []

class ContentWithTopic(ContentItem):
    topic: Topic

# User Profile Schemas
class UserProfile(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    social_links: Dict[str, str] = {}
    expertise: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class UserPreferences(BaseModel):
    interests: List[str] = []
    preferred_categories: List[str] = []
    reading_preferences: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)

class UserStats(BaseModel):
    total_interactions: int
    content_views: int
    topic_follows: int
    average_engagement: float
    favorite_categories: Dict[str, int]
    activity_by_day: Dict[str, int]

    model_config = ConfigDict(from_attributes=True)

# User Interaction Schemas
class UserInteractionResponse(BaseModel):
    id: int
    user_id: int
    content_id: int
    interaction_type: str
    created_at: datetime
    content: Optional[ContentWithTopic] = None

    model_config = ConfigDict(from_attributes=True)

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)

# Session Schemas
class SessionResponse(BaseModel):
    session_token: str
    user_id: Optional[int] = None
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HistoryResponse(BaseModel):
    interaction_type: str
    content: ContentWithTopic
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# Trending Schemas
class TrendingResponse(BaseModel):
    topic: Topic
    score: float
    rank: int
    content_count: int
    recent_views: int
    trend_direction: str  # "up", "down", or "stable"

    model_config = ConfigDict(from_attributes=True)

class EnhancedTrendResponse(TrendingResponse):
    interaction_rate: float
    velocity: float  # rate of score change
    engagement_score: float
    top_content: Optional[List[ContentWithTopic]] = []
    related_topics: Optional[List[Topic]] = []

    model_config = ConfigDict(from_attributes=True)
