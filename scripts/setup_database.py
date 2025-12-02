"""
PostgreSQL Database Setup Script

This script:
1. Connects to PostgreSQL (using 'postgres' database)
2. Creates 'bank_reviews' database if it doesn't exist
3. Creates all required tables with proper schema
4. Verifies table creation

Usage:
    python scripts/setup_database.py

Requirements:
    - PostgreSQL server must be running
    - Set password in database_config.py or POSTGRES_PASSWORD environment variable
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("ERROR: psycopg2 not installed. Install it with:")
    print("  pip install psycopg2-binary")
    sys.exit(1)

from database_config import (
    DB_CONFIG,
    BANKS_TABLE,
    REVIEWS_TABLE,
    THEMES_TABLE,
    KEYWORDS_TABLE,
    SENTIMENT_SUMMARY_TABLE,
    THEME_SUMMARY_TABLE,
    get_psycopg2_params,
)


def check_password_set() -> bool:
    """Check if database password is configured."""
    if not DB_CONFIG["password"]:
        print("\n" + "=" * 60)
        print("ERROR: PostgreSQL password not set!")
        print("=" * 60)
        print("\nPlease set your password using ONE of these methods:")
        print("\n1. Environment variable (recommended):")
        print("   set POSTGRES_PASSWORD=your_password")
        print("\n2. Edit database_config.py:")
        print("   DB_CONFIG['password'] = 'your_postgres_password'")
        print("\n3. Set it in database_config.py:")
        print("   Uncomment and set: DB_CONFIG['password'] = 'your_password'")
        print("\n" + "=" * 60)
        return False
    return True


def create_database(conn_params: dict, db_name: str) -> bool:
    """
    Create the bank_reviews database if it doesn't exist.
    
    Args:
        conn_params: Connection parameters (without database name)
        db_name: Name of database to create
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Connect to default 'postgres' database to create new database
        print(f"\nConnecting to PostgreSQL server...")
        print(f"  Host: {conn_params['host']}")
        print(f"  Port: {conn_params['port']}")
        print(f"  User: {conn_params['user']}")
        
        admin_conn = psycopg2.connect(
            host=conn_params["host"],
            port=conn_params["port"],
            user=conn_params["user"],
            password=conn_params["password"],
            database="postgres"  # Connect to default database
        )
        admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = admin_conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()
        
        if exists:
            print(f"\n✓ Database '{db_name}' already exists")
        else:
            print(f"\nCreating database '{db_name}'...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name)
            ))
            print(f"✓ Database '{db_name}' created successfully")
        
        cursor.close()
        admin_conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n✗ ERROR: Could not connect to PostgreSQL")
        print(f"  Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is PostgreSQL service running? (Check Windows Services)")
        print("  2. Is the password correct?")
        print("  3. Are host/port correct? (default: localhost:5432)")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: Failed to create database")
        print(f"  Error: {e}")
        return False


def create_tables(conn_params: dict, db_name: str) -> bool:
    """
    Create all required tables in the database.
    
    Args:
        conn_params: Connection parameters
        db_name: Database name
    
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"\nConnecting to database '{db_name}'...")
        conn = psycopg2.connect(
            host=conn_params["host"],
            port=conn_params["port"],
            user=conn_params["user"],
            password=conn_params["password"],
            database=db_name
        )
        cursor = conn.cursor()
        
        print("\nCreating tables...")
        
        # 1. Banks table
        print(f"  Creating {BANKS_TABLE} table...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {BANKS_TABLE} (
                bank_id SERIAL PRIMARY KEY,
                bank_name VARCHAR(100) NOT NULL UNIQUE,
                app_name VARCHAR(200),
                bank_code VARCHAR(50),
                app_id VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print(f"    ✓ {BANKS_TABLE} table created")
        
        # 2. Reviews table
        print(f"  Creating {REVIEWS_TABLE} table...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {REVIEWS_TABLE} (
                review_id VARCHAR(200) PRIMARY KEY,
                bank_id INTEGER NOT NULL REFERENCES {BANKS_TABLE}(bank_id) ON DELETE CASCADE,
                review_text TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                review_date DATE NOT NULL,
                review_year INTEGER,
                review_month INTEGER,
                review_length INTEGER,
                sentiment_label VARCHAR(20),
                sentiment_score DECIMAL(5, 3),
                sentiment_source VARCHAR(50),
                source VARCHAR(50) DEFAULT 'google_play',
                user_name VARCHAR(200),
                thumbs_up INTEGER DEFAULT 0,
                scraped_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_reviews_bank_id ON {REVIEWS_TABLE}(bank_id)
        """)
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_reviews_rating ON {REVIEWS_TABLE}(rating)
        """)
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_reviews_date ON {REVIEWS_TABLE}(review_date)
        """)
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON {REVIEWS_TABLE}(sentiment_label)
        """)
        print(f"    ✓ {REVIEWS_TABLE} table created with indexes")
        
        # 3. Themes table (many-to-many relationship: reviews can have multiple themes)
        print(f"  Creating {THEMES_TABLE} table...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {THEMES_TABLE} (
                theme_id SERIAL PRIMARY KEY,
                review_id VARCHAR(200) NOT NULL REFERENCES {REVIEWS_TABLE}(review_id) ON DELETE CASCADE,
                theme_name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(review_id, theme_name)
            )
        """)
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_themes_review_id ON {THEMES_TABLE}(review_id)
        """)
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_themes_name ON {THEMES_TABLE}(theme_name)
        """)
        print(f"    ✓ {THEMES_TABLE} table created")
        
        # 4. Keywords table (stores keywords per review)
        print(f"  Creating {KEYWORDS_TABLE} table...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {KEYWORDS_TABLE} (
                keyword_id SERIAL PRIMARY KEY,
                review_id VARCHAR(200) NOT NULL REFERENCES {REVIEWS_TABLE}(review_id) ON DELETE CASCADE,
                keyword VARCHAR(200) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(review_id, keyword)
            )
        """)
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_keywords_review_id ON {KEYWORDS_TABLE}(review_id)
        """)
        print(f"    ✓ {KEYWORDS_TABLE} table created")
        
        # 5. Sentiment Summary table (aggregated statistics)
        print(f"  Creating {SENTIMENT_SUMMARY_TABLE} table...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {SENTIMENT_SUMMARY_TABLE} (
                summary_id SERIAL PRIMARY KEY,
                bank_id INTEGER NOT NULL REFERENCES {BANKS_TABLE}(bank_id) ON DELETE CASCADE,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                review_count INTEGER NOT NULL DEFAULT 0,
                positive_pct DECIMAL(5, 2),
                neutral_pct DECIMAL(5, 2),
                negative_pct DECIMAL(5, 2),
                mean_score DECIMAL(5, 3),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bank_id, rating)
            )
        """)
        print(f"    ✓ {SENTIMENT_SUMMARY_TABLE} table created")
        
        # 6. Theme Summary table
        print(f"  Creating {THEME_SUMMARY_TABLE} table...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {THEME_SUMMARY_TABLE} (
                theme_summary_id SERIAL PRIMARY KEY,
                bank_id INTEGER NOT NULL REFERENCES {BANKS_TABLE}(bank_id) ON DELETE CASCADE,
                theme_name VARCHAR(100) NOT NULL,
                review_count INTEGER NOT NULL DEFAULT 0,
                avg_rating DECIMAL(3, 2),
                sample_review TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bank_id, theme_name)
            )
        """)
        print(f"    ✓ {THEME_SUMMARY_TABLE} table created")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✓ All tables created successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to create tables")
        print(f"  Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def verify_tables(conn_params: dict, db_name: str) -> bool:
    """
    Verify that all tables were created successfully.
    
    Args:
        conn_params: Connection parameters
        db_name: Database name
    
    Returns:
        True if all tables exist, False otherwise
    """
    try:
        conn = psycopg2.connect(
            host=conn_params["host"],
            port=conn_params["port"],
            user=conn_params["user"],
            password=conn_params["password"],
            database=db_name
        )
        cursor = conn.cursor()
        
        print("\n" + "=" * 60)
        print("VERIFYING DATABASE SCHEMA")
        print("=" * 60)
        
        # Check all tables
        expected_tables = [
            BANKS_TABLE,
            REVIEWS_TABLE,
            THEMES_TABLE,
            KEYWORDS_TABLE,
            SENTIMENT_SUMMARY_TABLE,
            THEME_SUMMARY_TABLE,
        ]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print("\nTables in database:")
        all_exist = True
        for table in expected_tables:
            if table in existing_tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (MISSING)")
                all_exist = False
        
        if all_exist:
            print("\n✓ All required tables exist!")
        else:
            print("\n⚠ Some tables are missing!")
        
        cursor.close()
        conn.close()
        return all_exist
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to verify tables")
        print(f"  Error: {e}")
        return False


def main():
    """Main execution function."""
    print("=" * 60)
    print("PostgreSQL Database Setup")
    print("=" * 60)
    
    # Check password is set
    if not check_password_set():
        sys.exit(1)
    
    # Get connection parameters
    conn_params, admin_db = get_psycopg2_params(use_admin_db=True)
    conn_params_final, db_name = get_psycopg2_params(use_admin_db=False)
    
    # Step 1: Create database
    if not create_database(conn_params, db_name):
        sys.exit(1)
    
    # Step 2: Create tables
    if not create_tables(conn_params_final, db_name):
        sys.exit(1)
    
    # Step 3: Verify tables
    if not verify_tables(conn_params_final, db_name):
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ Database setup completed successfully!")
    print("=" * 60)
    print(f"\nDatabase: {db_name}")
    print(f"Host: {conn_params['host']}:{conn_params['port']}")
    print(f"User: {conn_params['user']}")
    print("\nNext step: Run 'python scripts/load_data.py' to insert data")


if __name__ == "__main__":
    main()

