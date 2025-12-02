"""
PostgreSQL Data Loading Script

This script loads cleaned and processed review data into PostgreSQL database.

It performs:
1. Loads bank information from config and inserts into banks table
2. Loads reviews from processed CSV files
3. Inserts reviews into reviews table with proper foreign key relationships
4. Handles duplicates (uses ON CONFLICT DO NOTHING)
5. Verifies data integrity with SQL queries
6. Generates loading statistics

Usage:
    python scripts/load_data.py

Requirements:
    - PostgreSQL database must be set up (run setup_database.py first)
    - Processed CSV files must exist in data/processed/
    - Set password in database_config.py or POSTGRES_PASSWORD environment variable
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import pandas as pd
    import psycopg2
    from psycopg2.extras import execute_batch
    from psycopg2 import sql
except ImportError as e:
    print(f"ERROR: Required package not installed: {e}")
    print("Install with: pip install pandas psycopg2-binary")
    sys.exit(1)

from database_config import (
    DB_CONFIG,
    BANKS_TABLE,
    REVIEWS_TABLE,
    THEMES_TABLE,
    get_psycopg2_params,
)
from config import BANKS, SENTIMENT_DATA_PATH, THEME_DATA_PATH, PROCESSED_DATA_PATH


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
        print("\n" + "=" * 60)
        return False
    return True


def get_bank_id_mapping(cursor) -> Dict[str, int]:
    """
    Get mapping of bank_name to bank_id from database.
    
    Returns:
        Dictionary mapping bank_name -> bank_id
    """
    cursor.execute(f"SELECT bank_id, bank_name FROM {BANKS_TABLE}")
    return {row[1]: row[0] for row in cursor.fetchall()}


def insert_banks(cursor, conn) -> Dict[str, int]:
    """
    Insert bank information into banks table.
    
    Returns:
        Dictionary mapping bank_name -> bank_id
    """
    print("\n" + "=" * 60)
    print("INSERTING BANKS")
    print("=" * 60)
    
    bank_mapping = {}
    
    for bank_info in BANKS:
        bank_name = bank_info["bank"]
        bank_code = bank_info["bank_code"]
        app_id = bank_info["app_id"]
        
        # Check if bank already exists
        cursor.execute(
            f"SELECT bank_id FROM {BANKS_TABLE} WHERE bank_name = %s",
            (bank_name,)
        )
        existing = cursor.fetchone()
        
        if existing:
            bank_id = existing[0]
            print(f"  ✓ {bank_name} already exists (ID: {bank_id})")
        else:
            # Insert new bank
            cursor.execute(
                f"""
                INSERT INTO {BANKS_TABLE} (bank_name, bank_code, app_id)
                VALUES (%s, %s, %s)
                RETURNING bank_id
                """,
                (bank_name, bank_code, app_id)
            )
            bank_id = cursor.fetchone()[0]
            conn.commit()
            print(f"  ✓ Inserted {bank_name} (ID: {bank_id})")
        
        bank_mapping[bank_name] = bank_id
    
    return bank_mapping


def load_reviews_data(file_path: Path) -> pd.DataFrame:
    """
    Load reviews data from CSV file.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        DataFrame with review data
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Review data file not found: {file_path}")
    
    print(f"\nLoading reviews from: {file_path}")
    df = pd.read_csv(file_path)
    print(f"  Loaded {len(df):,} reviews")
    
    return df


def prepare_review_row(row: pd.Series, bank_id: int) -> tuple:
    """
    Prepare a single review row for database insertion.
    
    Args:
        row: Pandas Series with review data
        bank_id: Foreign key to banks table
        
    Returns:
        Tuple of values in correct order for INSERT
    """
    # Map CSV columns to database columns
    review_id = str(row.get('review_id', ''))
    review_text = str(row.get('review', row.get('review_text', '')))
    rating = int(row.get('rating', 0))
    
    # Handle date - convert to date object
    date_str = row.get('date', row.get('review_date', ''))
    if pd.isna(date_str) or date_str == '':
        review_date = None
    else:
        try:
            review_date = pd.to_datetime(date_str).date()
        except:
            review_date = None
    
    # Extract year and month if date is valid
    review_year = None
    review_month = None
    if review_date:
        review_year = review_date.year
        review_month = review_date.month
    
    # Optional fields
    review_length = int(row.get('review_length', row.get('text_length', 0))) if pd.notna(row.get('review_length', row.get('text_length', 0))) else None
    sentiment_label = str(row.get('sentiment_label', '')) if pd.notna(row.get('sentiment_label', '')) else None
    sentiment_score = float(row.get('sentiment_score', 0)) if pd.notna(row.get('sentiment_score', 0)) else None
    sentiment_source = str(row.get('sentiment_source', '')) if pd.notna(row.get('sentiment_source', '')) else None
    source = str(row.get('source', 'google_play'))
    user_name = str(row.get('user_name', '')) if pd.notna(row.get('user_name', '')) else None
    thumbs_up = int(row.get('thumbs_up', 0)) if pd.notna(row.get('thumbs_up', 0)) else 0
    
    return (
        review_id,
        bank_id,
        review_text,
        rating,
        review_date,
        review_year,
        review_month,
        review_length,
        sentiment_label,
        sentiment_score,
        sentiment_source,
        source,
        user_name,
        thumbs_up,
    )


def insert_reviews(cursor, conn, df: pd.DataFrame, bank_mapping: Dict[str, int]) -> Dict[str, int]:
    """
    Insert reviews into reviews table.
    
    Args:
        cursor: Database cursor
        conn: Database connection
        df: DataFrame with review data
        bank_mapping: Dictionary mapping bank_name -> bank_id
        
    Returns:
        Dictionary with insertion statistics
    """
    print("\n" + "=" * 60)
    print("INSERTING REVIEWS")
    print("=" * 60)
    
    stats = {
        'total_rows': len(df),
        'inserted': 0,
        'skipped': 0,
        'errors': 0,
    }
    
    # Prepare data for batch insertion
    insert_query = f"""
        INSERT INTO {REVIEWS_TABLE} (
            review_id, bank_id, review_text, rating, review_date,
            review_year, review_month, review_length,
            sentiment_label, sentiment_score, sentiment_source,
            source, user_name, thumbs_up
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (review_id) DO NOTHING
    """
    
    batch_data = []
    errors = []
    
    for idx, row in df.iterrows():
        try:
            bank_name = str(row.get('bank', ''))
            if bank_name not in bank_mapping:
                errors.append(f"Row {idx}: Bank '{bank_name}' not found in database")
                stats['errors'] += 1
                continue
            
            bank_id = bank_mapping[bank_name]
            review_row = prepare_review_row(row, bank_id)
            
            # Validate required fields
            if not review_row[0] or not review_row[2] or not review_row[3] or not review_row[4]:
                errors.append(f"Row {idx}: Missing required fields (review_id, review_text, rating, or date)")
                stats['errors'] += 1
                continue
            
            batch_data.append(review_row)
            
        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")
            stats['errors'] += 1
    
    # Batch insert
    if batch_data:
        print(f"\nInserting {len(batch_data):,} reviews in batches...")
        try:
            execute_batch(cursor, insert_query, batch_data, page_size=100)
            conn.commit()
            stats['inserted'] = len(batch_data)
            print(f"  ✓ Inserted {stats['inserted']:,} reviews")
        except Exception as e:
            conn.rollback()
            print(f"  ✗ Error during batch insert: {e}")
            stats['errors'] += len(batch_data)
    
    if errors:
        print(f"\n  ⚠ {len(errors)} errors encountered (first 5 shown):")
        for error in errors[:5]:
            print(f"    - {error}")
    
    return stats


def verify_data_integrity(cursor) -> Dict[str, any]:
    """
    Run SQL queries to verify data integrity.
    
    Returns:
        Dictionary with verification results
    """
    print("\n" + "=" * 60)
    print("VERIFYING DATA INTEGRITY")
    print("=" * 60)
    
    results = {}
    
    # 1. Count reviews per bank
    print("\n1. Reviews per bank:")
    cursor.execute(f"""
        SELECT b.bank_name, COUNT(r.review_id) as review_count
        FROM {BANKS_TABLE} b
        LEFT JOIN {REVIEWS_TABLE} r ON b.bank_id = r.bank_id
        GROUP BY b.bank_id, b.bank_name
        ORDER BY review_count DESC
    """)
    bank_counts = cursor.fetchall()
    results['reviews_per_bank'] = {}
    for bank_name, count in bank_counts:
        print(f"   {bank_name}: {count:,} reviews")
        results['reviews_per_bank'][bank_name] = count
    
    # 2. Average rating per bank
    print("\n2. Average rating per bank:")
    cursor.execute(f"""
        SELECT b.bank_name, 
               ROUND(AVG(r.rating), 2) as avg_rating,
               COUNT(r.review_id) as review_count
        FROM {BANKS_TABLE} b
        LEFT JOIN {REVIEWS_TABLE} r ON b.bank_id = r.bank_id
        GROUP BY b.bank_id, b.bank_name
        ORDER BY avg_rating DESC
    """)
    avg_ratings = cursor.fetchall()
    results['avg_rating_per_bank'] = {}
    for bank_name, avg_rating, count in avg_ratings:
        if count > 0:
            print(f"   {bank_name}: {avg_rating:.2f} stars ({count:,} reviews)")
            results['avg_rating_per_bank'][bank_name] = avg_rating
    
    # 3. Total review count
    cursor.execute(f"SELECT COUNT(*) FROM {REVIEWS_TABLE}")
    total_reviews = cursor.fetchone()[0]
    results['total_reviews'] = total_reviews
    print(f"\n3. Total reviews in database: {total_reviews:,}")
    
    # 4. Reviews with sentiment
    cursor.execute(f"""
        SELECT 
            COUNT(*) as total,
            COUNT(sentiment_label) as with_sentiment,
            COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positive,
            COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END) as neutral,
            COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negative
        FROM {REVIEWS_TABLE}
    """)
    sentiment_stats = cursor.fetchone()
    results['sentiment_stats'] = {
        'total': sentiment_stats[0],
        'with_sentiment': sentiment_stats[1],
        'positive': sentiment_stats[2],
        'neutral': sentiment_stats[3],
        'negative': sentiment_stats[4],
    }
    print(f"\n4. Sentiment distribution:")
    print(f"   Total reviews: {sentiment_stats[0]:,}")
    print(f"   With sentiment: {sentiment_stats[1]:,} ({sentiment_stats[1]/sentiment_stats[0]*100:.1f}%)")
    if sentiment_stats[1] > 0:
        print(f"   Positive: {sentiment_stats[2]:,}")
        print(f"   Neutral: {sentiment_stats[3]:,}")
        print(f"   Negative: {sentiment_stats[4]:,}")
    
    # 5. Date range
    cursor.execute(f"""
        SELECT MIN(review_date), MAX(review_date)
        FROM {REVIEWS_TABLE}
        WHERE review_date IS NOT NULL
    """)
    date_range = cursor.fetchone()
    if date_range[0] and date_range[1]:
        results['date_range'] = (str(date_range[0]), str(date_range[1]))
        print(f"\n5. Date range: {date_range[0]} to {date_range[1]}")
    
    # 6. Rating distribution
    print(f"\n6. Rating distribution:")
    cursor.execute(f"""
        SELECT rating, COUNT(*) as count
        FROM {REVIEWS_TABLE}
        GROUP BY rating
        ORDER BY rating DESC
    """)
    rating_dist = cursor.fetchall()
    results['rating_distribution'] = {}
    for rating, count in rating_dist:
        pct = (count / total_reviews * 100) if total_reviews > 0 else 0
        print(f"   {rating} stars: {count:,} ({pct:.1f}%)")
        results['rating_distribution'][rating] = count
    
    return results


def main():
    """Main execution function."""
    print("=" * 60)
    print("POSTGRESQL DATA LOADING")
    print("=" * 60)
    
    # Check password is set
    if not check_password_set():
        sys.exit(1)
    
    # Get connection parameters
    conn_params, db_name = get_psycopg2_params(use_admin_db=False)
    
    try:
        # Connect to database
        print(f"\nConnecting to database '{db_name}'...")
        conn = psycopg2.connect(
            host=conn_params["host"],
            port=conn_params["port"],
            user=conn_params["user"],
            password=conn_params["password"],
            database=db_name
        )
        cursor = conn.cursor()
        print("✓ Connected successfully")
        
        # Step 1: Insert banks
        bank_mapping = insert_banks(cursor, conn)
        
        # Step 2: Load review data
        # Try to load from reviews_with_sentiment.csv first (has sentiment data)
        # Fall back to reviews_clean.csv if not available
        review_file = SENTIMENT_DATA_PATH if SENTIMENT_DATA_PATH.exists() else PROCESSED_DATA_PATH
        
        if not review_file or not review_file.exists():
            print(f"\n✗ ERROR: Review data file not found!")
            print(f"   Expected: {SENTIMENT_DATA_PATH} or {PROCESSED_DATA_PATH}")
            sys.exit(1)
        
        df_reviews = load_reviews_data(review_file)
        
        # Step 3: Insert reviews
        stats = insert_reviews(cursor, conn, df_reviews, bank_mapping)
        
        # Step 4: Verify data integrity
        verification_results = verify_data_integrity(cursor)
        
        # Summary
        print("\n" + "=" * 60)
        print("LOADING SUMMARY")
        print("=" * 60)
        print(f"Total rows processed: {stats['total_rows']:,}")
        print(f"Successfully inserted: {stats['inserted']:,}")
        print(f"Errors: {stats['errors']:,}")
        print(f"\nTotal reviews in database: {verification_results['total_reviews']:,}")
        
        if verification_results['total_reviews'] >= 400:
            print("✓ SUCCESS: Database contains ≥400 reviews (meets minimum requirement)")
        else:
            print(f"⚠ WARNING: Database contains {verification_results['total_reviews']:,} reviews (<400 minimum)")
        
        if verification_results['total_reviews'] >= 1000:
            print("✓ SUCCESS: Database contains ≥1,000 reviews (meets KPI requirement)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✓ Data loading completed successfully!")
        print("=" * 60)
        
    except psycopg2.OperationalError as e:
        print(f"\n✗ ERROR: Could not connect to PostgreSQL")
        print(f"  Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is PostgreSQL service running?")
        print("  2. Is the database 'bank_reviews' created? (run setup_database.py first)")
        print("  3. Are connection settings correct?")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

