"""Database module for SmartNinja application.
This module provides database connection utilities and session management.
It defines the SQLAlchemy engine, session factory, and base class for models.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

# Use SQLite for development
DATABASE_URL = "sqlite:///./smartninja.db"
# Create engine with appropriate configuration
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Create declarative base for models
Base = declarative_base()


def get_db():
    """Get database session

    Yields:
        Session: Database session
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Initialize the database by creating all tables.
    Note: This function should be called after all models are imported.
    """
    # Import Base.metadata here to avoid circular imports
    Base.metadata.create_all(bind=engine)
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
