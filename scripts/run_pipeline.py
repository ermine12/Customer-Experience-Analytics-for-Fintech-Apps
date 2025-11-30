"""
End-to-end pipeline execution script for Customer Experience Analytics.

This script orchestrates the complete data processing pipeline:
1. Scrape reviews from Google Play Store
2. Preprocess and clean the data
3. Perform sentiment analysis
4. Extract themes and keywords
5. Generate summary reports

Usage:
    python scripts/run_pipeline.py [--skip-scrape] [--skip-preprocess] [--skip-sentiment] [--skip-themes]

Options:
    --skip-scrape      Skip the scraping step (use existing raw data)
    --skip-preprocess  Skip preprocessing (use existing clean data)
    --skip-sentiment   Skip sentiment analysis (use existing sentiment data)
    --skip-themes      Skip theme analysis (use existing theme data)
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

from config import (
    PROCESSED_DATA_PATH,
    RAW_DATA_PATH,
    SENTIMENT_DATA_PATH,
    THEME_DATA_PATH,
)


def run_scraping() -> bool:
    """Execute review scraping from Google Play Store.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("=" * 60)
        logger.info("STEP 1: Scraping Reviews from Google Play Store")
        logger.info("=" * 60)
        
        from scripts.scrape_reviews import main as scrape_main
        scrape_main()
        
        # Verify output
        if not RAW_DATA_PATH.exists():
            logger.error(f"Scraping failed: {RAW_DATA_PATH} not found")
            return False
        
        import pandas as pd
        df = pd.read_csv(RAW_DATA_PATH)
        logger.info(f"✓ Successfully scraped {len(df):,} reviews")
        logger.info(f"  Saved to: {RAW_DATA_PATH}")
        
        # Check per-bank counts
        bank_counts = df['bank'].value_counts()
        logger.info("  Reviews per bank:")
        for bank, count in bank_counts.items():
            logger.info(f"    {bank}: {count:,}")
        
        return True
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        return False


def run_preprocessing() -> bool:
    """Execute data preprocessing and cleaning.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("=" * 60)
        logger.info("STEP 2: Preprocessing and Cleaning Data")
        logger.info("=" * 60)
        
        from scripts.preprocess_reviews import ReviewPreprocessor
        processor = ReviewPreprocessor()
        processor.process()
        
        # Verify output and data quality
        if not PROCESSED_DATA_PATH.exists():
            logger.error(f"Preprocessing failed: {PROCESSED_DATA_PATH} not found")
            return False
        
        import pandas as pd
        df = pd.read_csv(PROCESSED_DATA_PATH)
        
        # Verify required columns
        required_cols = ['review', 'rating', 'date', 'bank', 'source']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            return False
        
        # Data quality metrics
        missing_pct = (df.isna().sum() / len(df) * 100).to_dict()
        logger.info(f"✓ Successfully preprocessed {len(df):,} reviews")
        logger.info(f"  Saved to: {PROCESSED_DATA_PATH}")
        logger.info("  Data quality metrics:")
        for col, pct in missing_pct.items():
            logger.info(f"    {col}: {pct:.2f}% missing")
        
        # Verify date format
        sample_date = df['date'].iloc[0] if len(df) > 0 else None
        logger.info(f"  Date format: {sample_date} (YYYY-MM-DD)")
        
        # Per-bank counts
        bank_counts = df['bank'].value_counts()
        logger.info("  Reviews per bank:")
        for bank, count in bank_counts.items():
            logger.info(f"    {bank}: {count:,}")
        
        return True
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        return False


def run_sentiment_analysis() -> bool:
    """Execute sentiment analysis on cleaned reviews.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("=" * 60)
        logger.info("STEP 3: Performing Sentiment Analysis")
        logger.info("=" * 60)
        
        from scripts.sentiment_analysis import main as sentiment_main
        sentiment_main()
        
        # Verify output
        if not SENTIMENT_DATA_PATH.exists():
            logger.error(f"Sentiment analysis failed: {SENTIMENT_DATA_PATH} not found")
            return False
        
        import pandas as pd
        df = pd.read_csv(SENTIMENT_DATA_PATH)
        
        # Coverage metrics
        total = len(df)
        with_sentiment = df['sentiment_label'].notna().sum()
        coverage = (with_sentiment / total * 100) if total > 0 else 0
        
        logger.info(f"✓ Successfully analyzed sentiment for {with_sentiment:,}/{total:,} reviews ({coverage:.1f}% coverage)")
        logger.info(f"  Saved to: {SENTIMENT_DATA_PATH}")
        
        # Sentiment distribution
        if 'sentiment_label' in df.columns:
            sentiment_dist = df['sentiment_label'].value_counts()
            logger.info("  Sentiment distribution:")
            for label, count in sentiment_dist.items():
                pct = (count / total * 100) if total > 0 else 0
                logger.info(f"    {label}: {count:,} ({pct:.1f}%)")
        
        return True
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
        return False


def run_theme_analysis() -> bool:
    """Execute theme and keyword extraction.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("=" * 60)
        logger.info("STEP 4: Extracting Themes and Keywords")
        logger.info("=" * 60)
        
        from scripts.theme_analysis import main as theme_main
        theme_main()
        
        # Verify output
        if not THEME_DATA_PATH.exists():
            logger.error(f"Theme analysis failed: {THEME_DATA_PATH} not found")
            return False
        
        import pandas as pd
        df = pd.read_csv(THEME_DATA_PATH)
        
        # Coverage metrics
        total = len(df)
        with_themes = df['themes'].notna().sum()
        coverage = (with_themes / total * 100) if total > 0 else 0
        
        logger.info(f"✓ Successfully extracted themes for {with_themes:,}/{total:,} reviews ({coverage:.1f}% coverage)")
        logger.info(f"  Saved to: {THEME_DATA_PATH}")
        
        # Theme distribution
        if 'themes' in df.columns:
            all_themes = []
            for themes_str in df['themes'].dropna():
                all_themes.extend(str(themes_str).split('|'))
            from collections import Counter
            theme_counts = Counter(all_themes)
            logger.info("  Top themes:")
            for theme, count in theme_counts.most_common(5):
                pct = (count / total * 100) if total > 0 else 0
                logger.info(f"    {theme}: {count:,} ({pct:.1f}%)")
        
        return True
    except Exception as e:
        logger.error(f"Theme analysis failed: {e}", exc_info=True)
        return False


def main(
    skip_scrape: bool = False,
    skip_preprocess: bool = False,
    skip_sentiment: bool = False,
    skip_themes: bool = False,
) -> int:
    """Execute the complete data processing pipeline.
    
    Args:
        skip_scrape: If True, skip the scraping step
        skip_preprocess: If True, skip the preprocessing step
        skip_sentiment: If True, skip the sentiment analysis step
        skip_themes: If True, skip the theme analysis step
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("=" * 60)
    logger.info("Customer Experience Analytics - Pipeline Execution")
    logger.info("=" * 60)
    logger.info("")
    
    steps_completed = 0
    steps_failed = 0
    
    # Step 1: Scraping
    if not skip_scrape:
        if run_scraping():
            steps_completed += 1
        else:
            steps_failed += 1
            logger.error("Pipeline stopped due to scraping failure")
            return 1
    else:
        logger.info("Skipping scraping step (--skip-scrape)")
        if RAW_DATA_PATH.exists():
            logger.info(f"  Using existing data: {RAW_DATA_PATH}")
        else:
            logger.warning(f"  Warning: {RAW_DATA_PATH} not found")
    
    # Step 2: Preprocessing
    if not skip_preprocess:
        if run_preprocessing():
            steps_completed += 1
        else:
            steps_failed += 1
            logger.error("Pipeline stopped due to preprocessing failure")
            return 1
    else:
        logger.info("Skipping preprocessing step (--skip-preprocess)")
        if PROCESSED_DATA_PATH.exists():
            logger.info(f"  Using existing data: {PROCESSED_DATA_PATH}")
        else:
            logger.warning(f"  Warning: {PROCESSED_DATA_PATH} not found")
    
    # Step 3: Sentiment Analysis
    if not skip_sentiment:
        if run_sentiment_analysis():
            steps_completed += 1
        else:
            steps_failed += 1
            logger.error("Pipeline stopped due to sentiment analysis failure")
            return 1
    else:
        logger.info("Skipping sentiment analysis step (--skip-sentiment)")
        if SENTIMENT_DATA_PATH.exists():
            logger.info(f"  Using existing data: {SENTIMENT_DATA_PATH}")
        else:
            logger.warning(f"  Warning: {SENTIMENT_DATA_PATH} not found")
    
    # Step 4: Theme Analysis
    if not skip_themes:
        if run_theme_analysis():
            steps_completed += 1
        else:
            steps_failed += 1
            logger.error("Pipeline stopped due to theme analysis failure")
            return 1
    else:
        logger.info("Skipping theme analysis step (--skip-themes)")
        if THEME_DATA_PATH.exists():
            logger.info(f"  Using existing data: {THEME_DATA_PATH}")
        else:
            logger.warning(f"  Warning: {THEME_DATA_PATH} not found")
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Pipeline Execution Summary")
    logger.info("=" * 60)
    logger.info(f"Steps completed: {steps_completed}")
    logger.info(f"Steps failed: {steps_failed}")
    
    if steps_failed == 0:
        logger.info("✓ Pipeline completed successfully!")
        return 0
    else:
        logger.error("✗ Pipeline completed with errors")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the complete Customer Experience Analytics pipeline"
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip the scraping step (use existing raw data)"
    )
    parser.add_argument(
        "--skip-preprocess",
        action="store_true",
        help="Skip preprocessing (use existing clean data)"
    )
    parser.add_argument(
        "--skip-sentiment",
        action="store_true",
        help="Skip sentiment analysis (use existing sentiment data)"
    )
    parser.add_argument(
        "--skip-themes",
        action="store_true",
        help="Skip theme analysis (use existing theme data)"
    )
    
    args = parser.parse_args()
    
    exit_code = main(
        skip_scrape=args.skip_scrape,
        skip_preprocess=args.skip_preprocess,
        skip_sentiment=args.skip_sentiment,
        skip_themes=args.skip_themes,
    )
    
    sys.exit(exit_code)

