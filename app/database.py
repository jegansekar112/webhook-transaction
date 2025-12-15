"""
Database configuration and session management.
This file sets up SQLAlchemy database connection and session handling.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./webhook_db.sqlite")

engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    pool_size=10,  
    max_overflow=20,
    pool_recycle=3600,
    echo=False  
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Generator function for Flask to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



