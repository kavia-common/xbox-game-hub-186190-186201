from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, EmailStr


class APIError(BaseModel):
    """Standardized error response."""
    detail: str = Field(..., description="Error description")


class GameBase(BaseModel):
    """Shared fields for game models."""
    title: str = Field(..., description="Game title")
    genre: Optional[str] = Field(None, description="Game genre")
    thumbnail: Optional[str] = Field(None, description="Thumbnail image URL")


class GameListItem(GameBase):
    """Game item returned in listings."""
    id: int = Field(..., description="Unique game ID")


class GameDetail(GameBase):
    """Detailed game information."""
    id: int = Field(..., description="Unique game ID")
    description: Optional[str] = Field(None, description="Detailed description")
    screenshots: Optional[List[str]] = Field(default=None, description="Screenshot URLs")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class GamesResponse(BaseModel):
    """Paginated games response."""
    total: int = Field(..., description="Total number of matching games")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Page size")
    items: List[GameListItem] = Field(..., description="Games list for the page")


class RegisterRequest(BaseModel):
    """Request schema for account registration."""
    email: EmailStr = Field(..., description="Email address")
    username: str = Field(..., description="Desired username")
    password: str = Field(..., description="Password (plain, demo only)")


class LoginRequest(BaseModel):
    """Request schema for account login."""
    email: Optional[EmailStr] = Field(None, description="Email address")
    username: Optional[str] = Field(None, description="Username")
    password: str = Field(..., description="Password (plain, demo only)")


class AccountResponse(BaseModel):
    """Account information to return to clients."""
    id: int = Field(..., description="Account ID")
    email: EmailStr = Field(..., description="Email")
    username: str = Field(..., description="Username")
    created_at: datetime = Field(..., description="Creation timestamp")


class AuthResponse(BaseModel):
    """Authentication response for demo flow."""
    success: bool = Field(..., description="If the operation was successful")
    message: str = Field(..., description="Result message")
    account: Optional[AccountResponse] = Field(None, description="Account details when applicable")
    token: Optional[str] = Field(None, description="Fake token for demo")
