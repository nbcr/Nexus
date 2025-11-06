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
    content_type: str
    content_text: str
    ai_model_used: str
    source_urls: Optional[List[str]] = []
    is_published: bool = False

class ContentItemCreate(ContentItemBase):
    topic_id: int

class ContentItemUpdate(ContentItemBase):
    content_type: Optional[str] = None
    content_text: Optional[str] = None

class ContentItem(ContentItemBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    topic_id: int
    created_at: datetime
    updated_at: datetime

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
