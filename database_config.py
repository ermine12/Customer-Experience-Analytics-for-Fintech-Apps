"""
Database configuration for PostgreSQL connection.

IMPORTANT: Set your PostgreSQL password in this file or use environment variables.

Usage:
    1. Set DB_PASSWORD below, OR
    2. Set environment variable: POSTGRES_PASSWORD=your_password
    3. Run: python scripts/setup_database.py
"""

import os
from pathlib import Path
from typing import Dict, Any

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip .env loading
    # Environment variables can still be set manually
    pass

# ============================================================================
# PostgreSQL Connection Settings
# ============================================================================

# Database connection parameters
DB_CONFIG: Dict[str, Any] = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),  # Set via environment variable or below
    "database": "bank_reviews",  # Will be created automatically
    "admin_database": "postgres",  # Default database for initial connection
}

# If password is not set via environment variable, set it here:
# DB_CONFIG["password"] = "your_postgres_password_here"

# ============================================================================
# Database Schema Settings
# ============================================================================

# Table names
BANKS_TABLE = "banks"
REVIEWS_TABLE = "reviews"
THEMES_TABLE = "themes"
KEYWORDS_TABLE = "keywords"
SENTIMENT_SUMMARY_TABLE = "sentiment_summary"
THEME_SUMMARY_TABLE = "theme_summary"

# ============================================================================
# Connection String (for SQLAlchemy)
# ============================================================================

def get_connection_string(use_admin_db: bool = False) -> str:
    """
    Generate PostgreSQL connection string.
    
    Args:
        use_admin_db: If True, connect to 'postgres' database (for creating new DB)
    
    Returns:
        PostgreSQL connection string
    """
    db_name = DB_CONFIG["admin_database"] if use_admin_db else DB_CONFIG["database"]
    return (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{db_name}"
    )


def get_psycopg2_params(use_admin_db: bool = False) -> Dict[str, Any]:
    """
    Get connection parameters for psycopg2.
    
    Args:
        use_admin_db: If True, connect to 'postgres' database
    
    Returns:
        Dictionary of connection parameters
    """
    params = DB_CONFIG.copy()
    if use_admin_db:
        params["database"] = DB_CONFIG["admin_database"]
    # Remove 'database' key and use it separately in connect()
    db_name = params.pop("database")
    admin_db = params.pop("admin_database")
    return params, db_name if not use_admin_db else admin_db

