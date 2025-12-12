from __future__ import annotations

import os
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.db.database import get_db, init_db
from src.models.models import Account, Game
from src.schemas.schemas import (
    APIError,
    AuthResponse,
    GameDetail,
    GameListItem,
    GamesResponse,
    LoginRequest,
    RegisterRequest,
    AccountResponse,
    ProfileResponse,
)

APP_TITLE = "Xbox Game Hub API"
APP_DESCRIPTION = (
    "Backend API for browsing games, viewing details, and basic account management."
)
APP_VERSION = "0.1.0"

openapi_tags = [
    {"name": "Health", "description": "Service health and status endpoints."},
    {"name": "Games", "description": "Browse and view game information."},
    {"name": "Accounts", "description": "Register and login to accounts (demo)."},
    {"name": "Profile", "description": "User profile endpoints (demo)."},
]

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    openapi_tags=openapi_tags,
)

# CORS (keep as-is behavior)
default_origins = [
    "http://localhost:3000",
    os.getenv("FRONTEND_URL", "").strip('"').strip("'"),
]
allowed_from_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_from_env:
    default_origins.extend([o.strip() for o in allowed_from_env.split(",") if o.strip()])

# Remove empties and deduplicate
allow_origins = sorted({o for o in default_origins if o})

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize tables and seed demo data on startup."""
    init_db(seed=True)


# PUBLIC_INTERFACE
@app.get("/", tags=["Health"], summary="Health Check")
def health_check() -> dict:
    """Health check endpoint to validate service is running."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get(
    "/api/games",
    response_model=GamesResponse,
    responses={404: {"model": APIError}},
    tags=["Games"],
    summary="List games",
    description="Returns a paginated list of games with optional title search.",
)
def list_games(
    q: Optional[str] = Query(default=None, description="Search by title (case-insensitive)"),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=12, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
) -> GamesResponse:
    """List games with pagination and optional search by title."""
    query = db.query(Game)
    if q:
        query = query.filter(func.lower(Game.title).like(f"%{q.lower()}%"))

    total = query.count()
    if total == 0:
        return GamesResponse(total=0, page=page, page_size=page_size, items=[])

    items = (
        query.order_by(Game.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    out_items: List[GameListItem] = [
        GameListItem(id=g.id, title=g.title, genre=g.genre, thumbnail=g.thumbnail)
        for g in items
    ]
    return GamesResponse(total=total, page=page, page_size=page_size, items=out_items)


# PUBLIC_INTERFACE
@app.get(
    "/api/games/{game_id}",
    response_model=GameDetail,
    responses={404: {"model": APIError}},
    tags=["Games"],
    summary="Get game details",
    description="Returns detailed information for a specific game.",
)
def get_game_details(game_id: int, db: Session = Depends(get_db)) -> GameDetail:
    """Retrieve details for a specific game by ID."""
    game: Optional[Game] = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return GameDetail(
        id=game.id,
        title=game.title,
        genre=game.genre,
        thumbnail=game.thumbnail,
        description=game.description,
        screenshots=game.screenshots or [],
        metadata=game.metadata or {},
    )


def _hash_password(pw: str) -> str:
    # Demo-only: not secure. Replace with passlib/bcrypt in real use.
    # Simple reversible placeholder: do NOT use in production.
    return f"demo$sha1${pw[::-1]}"


def _fake_token(account_id: int) -> str:
    return f"demo-token-{account_id}"


# PUBLIC_INTERFACE
@app.post(
    "/api/accounts/register",
    response_model=AuthResponse,
    responses={
        400: {"model": APIError},
        409: {"model": APIError},
    },
    tags=["Accounts"],
    summary="Register account",
    description="Creates a simple demo account record. Returns a placeholder token.",
)
def register_account(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Register a demo account."""
    existing_email = db.query(Account).filter(Account.email == payload.email).first()
    if existing_email:
        raise HTTPException(status_code=409, detail="Email already registered")

    existing_username = db.query(Account).filter(Account.username == payload.username).first()
    if existing_username:
        raise HTTPException(status_code=409, detail="Username already taken")

    account = Account(
        email=payload.email,
        username=payload.username,
        password_hash=_hash_password(payload.password),
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    acc = AccountResponse(
        id=account.id, email=account.email, username=account.username, created_at=account.created_at
    )
    return AuthResponse(success=True, message="Registered", account=acc, token=_fake_token(account.id))


# PUBLIC_INTERFACE
@app.post(
    "/api/accounts/login",
    response_model=AuthResponse,
    responses={401: {"model": APIError}},
    tags=["Accounts"],
    summary="Login",
    description="Validates credentials against stored demo hash. Returns a placeholder token.",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Login to a demo account with email or username."""
    if not payload.email and not payload.username:
        raise HTTPException(status_code=401, detail="Email or username is required")

    query = db.query(Account)
    if payload.email:
        query = query.filter(Account.email == payload.email)
    else:
        query = query.filter(Account.username == payload.username)

    account = query.first()
    if not account or account.password_hash != _hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    acc = AccountResponse(
        id=account.id, email=account.email, username=account.username, created_at=account.created_at
    )
    return AuthResponse(success=True, message="Logged in", account=acc, token=_fake_token(account.id))


# PUBLIC_INTERFACE
@app.get(
    "/api/account/profile",
    response_model=ProfileResponse,
    tags=["Profile"],
    summary="Get current user profile (demo)",
    description="Returns a static demo profile for the current user. No authentication is required in this demo.",
)
def get_profile() -> ProfileResponse:
    """Return a static demo profile object.

    For the purpose of this demo, this endpoint does not authenticate the user
    and always returns the same mock profile.
    """
    return ProfileResponse(
        id=1,
        gamertag="DemoSpartan117",
        avatar="https://images.unsplash.com/photo-1547425260-76bcadfb4f2c?w=256&q=80",
        bio="Xbox enthusiast. Loves shooters and racing games.",
        preferences={
            "theme": "light",
            "language": "en-US",
            "mature_content": False,
        },
    )
