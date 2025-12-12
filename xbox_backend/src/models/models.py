from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import ARRAY

from src.db.database import Base


class Game(Base):
    """SQLAlchemy model representing a game available in the hub."""

    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    genre = Column(String(100), nullable=True, index=True)
    thumbnail = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    # Postgres friendly types: use ARRAY(Text) for screenshots, JSONB for extra metadata
    screenshots = Column(ARRAY(Text), nullable=True, default=[])
    # "metadata" is a reserved attribute name in SQLAlchemy's Declarative API.
    # Use a different attribute name while still mapping the column name to "metadata" in the DB.
    extra_metadata = Column("metadata", JSONB, nullable=True, default={})


class Account(Base):
    """SQLAlchemy model for a simple account record."""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
