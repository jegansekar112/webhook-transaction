"""
Database configuration and session management.
This file sets up SQLAlchemy database connection and session handling.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env file (only if it exists)
# In Vercel/serverless, env vars come from platform, not .env file
# load_dotenv() is safe to call even if .env doesn't exist
try:
    load_dotenv()
except Exception:
    # Ignore if .env file doesn't exist (normal in serverless)
    pass

# Get DATABASE_URL from environment
# In Vercel: Set in Dashboard → Settings → Environment Variables
# In local: Set in .env file or export DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Validate DATABASE_URL is set
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        "Please set it in Vercel Dashboard → Settings → Environment Variables, "
        "or in your .env file for local development."
    )

# Configure engine with connection pooling suitable for serverless
# Reduce pool size for serverless environments (Vercel)
is_vercel = os.getenv("VERCEL") is not None
pool_size = 1 if is_vercel else 10
max_overflow = 0 if is_vercel else 20

# Add connection timeout for PostgreSQL
# Note: For Supabase IPv6 issues, use the connection pooling URL instead
# Supabase provides: postgresql://... (direct) and postgresql://...?pgbouncer=true (pooling)
# Use the pooling URL for better serverless compatibility
connect_args = {}
if "postgresql" in DATABASE_URL or "postgres" in DATABASE_URL:
    connect_args = {"connect_timeout": 10}

engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    pool_size=pool_size,  
    max_overflow=max_overflow,
    pool_recycle=3600,
    echo=False,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Track if tables have been created (lazy initialization)
_tables_created = False

def get_db():
    """
    Generator function for Flask to get database session.
    Creates tables lazily on first use (not at import time).
    """
    global _tables_created
    
    # Create tables on first database access (lazy initialization)
    if not _tables_created:
        try:
            Base.metadata.create_all(bind=engine)
            _tables_created = True
        except Exception as e:
            # Tables might already exist, or connection might fail
            # Don't crash - let the actual query handle the error
            import logging
            logging.warning(f"Table creation skipped: {str(e)}")
            _tables_created = True  # Mark as attempted to avoid repeated errors
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



