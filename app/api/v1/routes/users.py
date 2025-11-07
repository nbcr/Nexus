"""
Users Router

This module handles user management endpoints:
- User CRUD operations
- User preferences
- User profile management
- User content interactions
"""
from fastapi import APIRouter, HTTPException, status, Path, Query, Body, Depends
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.api.v1.deps import get_db, get_current_user, get_current_active_user
from app.models import User, UserInteraction, UserInterestProfile
from app.schemas import (
    UserResponse,
    UserUpdate,
    UserInteractionResponse,
    UserPreferences,
    UserProfile,
    UserStats
)
from app.services.user_service import (
    update_user_profile,
    get_user_stats,
    get_user_preferences
)

# Router Configuration
router = APIRouter()

@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        200: {"description": "Current user profile"},
        401: {"description": "Not authenticated"}
    }
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get the current user's profile.
    
    Args:
        current_user: The authenticated user (from dependency)
        
    Returns:
        User profile data
    """
    return current_user

@router.patch(
    "/me",
    response_model=UserResponse,
    responses={
        200: {"description": "Profile updated successfully"},
        401: {"description": "Not authenticated"},
        400: {"description": "Invalid update data"}
    }
)
async def update_current_user(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update the current user's profile.
    
    Args:
        update_data: User data to update
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Updated user profile
        
    Raises:
        HTTPException: If update fails or data is invalid
    """
    try:
        # Check if email is being changed and is unique
        if update_data.email and update_data.email != current_user.email:
            existing = await db.execute(
                select(User).where(User.email == update_data.email)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Update user
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(**update_data.model_dump(exclude_unset=True))
        )
        await db.commit()
        
        # Refresh user data
        await db.refresh(current_user)
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )

@router.get(
    "/me/interactions",
    response_model=List[UserInteractionResponse],
    responses={
        200: {"description": "User's content interactions"},
        401: {"description": "Not authenticated"}
    }
)
async def get_user_interactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    interaction_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[UserInteractionResponse]:
    """
    Get the current user's content interactions.
    
    Args:
        current_user: The authenticated user
        skip: Number of items to skip
        limit: Maximum number of items to return
        interaction_type: Optional filter by interaction type
        db: Database session
        
    Returns:
        List of user interactions
    """
    query = select(UserInteraction).where(UserInteraction.user_id == current_user.id)
    
    if interaction_type:
        query = query.where(UserInteraction.interaction_type == interaction_type)
        
    query = query.order_by(UserInteraction.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get(
    "/me/preferences",
    response_model=UserPreferences,
    responses={
        200: {"description": "User's preferences"},
        401: {"description": "Not authenticated"}
    }
)
async def get_user_preferences_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserPreferences:
    """
    Get the current user's preferences.
    
    Args:
        current_user: The authenticated user
        db: Database session
        
    Returns:
        User preferences data
    """
    return await get_user_preferences(db, current_user.id)

@router.put(
    "/me/preferences",
    response_model=UserPreferences,
    responses={
        200: {"description": "Preferences updated successfully"},
        401: {"description": "Not authenticated"},
        400: {"description": "Invalid preferences data"}
    }
)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserPreferences:
    """
    Update the current user's preferences.
    
    Args:
        preferences: New preferences data
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Updated preferences
        
    Raises:
        HTTPException: If update fails
    """
    try:
        profile = await db.get(UserInterestProfile, current_user.id)
        if not profile:
            profile = UserInterestProfile(user_id=current_user.id)
            db.add(profile)
        
        profile.interests = preferences.interests
        profile.preferred_categories = preferences.preferred_categories
        profile.reading_preferences = preferences.reading_preferences
        
        await db.commit()
        await db.refresh(profile)
        
        return preferences
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )

@router.get(
    "/me/stats",
    response_model=UserStats,
    responses={
        200: {"description": "User's activity statistics"},
        401: {"description": "Not authenticated"}
    }
)
async def get_user_statistics(
    timeframe: str = Query("30d", pattern="^(24h|7d|30d|all)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserStats:
    """
    Get the current user's activity statistics.
    
    Args:
        current_user: The authenticated user
        timeframe: Time period for stats
        db: Database session
        
    Returns:
        User activity statistics
    """
    return await get_user_stats(db, current_user.id, timeframe)

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Account deleted successfully"},
        401: {"description": "Not authenticated"}
    }
)
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete the current user's account.
    
    Args:
        current_user: The authenticated user
        db: Database session
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        await db.delete(current_user)
        await db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )