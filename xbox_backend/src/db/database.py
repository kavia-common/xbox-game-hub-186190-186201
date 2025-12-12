import os
import re
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session


Base = declarative_base()

# PUBLIC_INTERFACE
def get_database_url() -> str:
    """Return the database URL for PostgreSQL.

    Order of precedence:
    1. db_connection.txt in the database container (psql postgresql://...)
    2. POSTGRES_URL env
    3. Construct from POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT with localhost
    4. Fallback to a sensible default (local container default)

    Note: We do not read the .env file here; rely on environment provided.
    """
    # Try reading db_connection.txt
    try:
        db_file_path = "/home/kavia/workspace/code-generation/xbox-game-hub-186190-186202/database/db_connection.txt"
        if os.path.exists(db_file_path):
            with open(db_file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                # Expected like: psql postgresql://user:pass@host:port/db
                match = re.search(r"(postgresql://[^\s]+)", content)
                if match:
                    return match.group(1)
    except Exception:
        # Ignore and fallback to env
        pass

    # Env var POSTGRES_URL takes precedence if present
    pg_url = os.getenv("POSTGRES_URL")
    if pg_url:
        return pg_url.strip('"').strip("'")

    # Build from discrete vars
    user = os.getenv("POSTGRES_USER", "appuser").strip('"').strip("'")
    password = os.getenv("POSTGRES_PASSWORD", "dbuser123").strip('"').strip("'")
    host = os.getenv("POSTGRES_HOST", "localhost").strip('"').strip("'")
    port = os.getenv("POSTGRES_PORT", "5000").strip('"').strip("'")
    db = os.getenv("POSTGRES_DB", "myapp").strip('"').strip("'")

    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


# Create engine and session factory
DATABASE_URL = get_database_url()

# sqlalchemy URL may not have driver; ensure psycopg2 driver if plain postgresql://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to provide a DB Session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC_INTERFACE
def init_db(seed: bool = True) -> None:
    """Initialize database tables and optionally seed minimal data for demo browsing."""
    from src.models.models import Game  # Import models to register with Base

    Base.metadata.create_all(bind=engine)

    if not seed:
        return

    # Seed minimal mock data if Game table is empty
    with SessionLocal() as session:
        games_count = session.query(Game).count()
        if games_count == 0:
            demo_games = [
                Game(
                    title="Halo Infinite",
                    genre="Shooter",
                    thumbnail="https://images.unsplash.com/photo-1605901309584-818e25960a8b?w=800&q=80",
                    description="Master Chief returns in Halo Infinite, delivering an epic campaign and robust multiplayer.",
                    screenshots=[
                        "https://images.unsplash.com/photo-1590608897129-79da98d1593d?w=1200&q=80",
                        "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1200&q=80",
                    ],
                    metadata={"platform": "Xbox Series X|S", "rating": "T"},
                ),
                Game(
                    title="Forza Horizon 5",
                    genre="Racing",
                    thumbnail="https://images.unsplash.com/photo-1549921296-3fd62d1c4f59?w=800&q=80",
                    description="A vibrant open-world racing game set in Mexico with dynamic seasons and events.",
                    screenshots=[
                        "https://images.unsplash.com/photo-1517673400267-0251440c45dc?w=1200&q=80",
                        "https://images.unsplash.com/photo-1518306727298-4c7e88b2f65a?w=1200&q=80",
                    ],
                    metadata={"platform": "Xbox Series X|S", "rating": "E"},
                ),
                Game(
                    title="Sea of Thieves",
                    genre="Adventure",
                    thumbnail="https://images.unsplash.com/photo-1544550282-9c3144b2d2de?w=800&q=80",
                    description="A pirate adventure game focused on exploration, combat, and treasure hunting.",
                    screenshots=[
                        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&q=80"
                    ],
                    metadata={"platform": "Xbox One", "rating": "T"},
                ),
            ]
            session.add_all(demo_games)
            session.commit()
