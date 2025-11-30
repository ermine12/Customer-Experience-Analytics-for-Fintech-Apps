"""
Configuration file for Customer Experience Analytics project.

This module centralizes all configuration settings including:
- File paths for data storage
- Bank metadata and app IDs
- Scraper settings
- Preprocessing configuration
- NLP model settings and parameters

Usage:
    Import this module to access configuration constants:
    
    from config import BANKS, SCRAPER_SETTINGS, NLP_SETTINGS
    
    # Modify settings as needed
    SCRAPER_SETTINGS["min_reviews_per_bank"] = 500
"""

from pathlib import Path
from typing import Dict, List

# ============================================================================
# Project Paths
# ============================================================================

PROJECT_ROOT: Path = Path(__file__).parent
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_PATH: Path = DATA_DIR / "raw" / "reviews_raw.csv"
APP_INFO_PATH: Path = DATA_DIR / "raw" / "app_info.csv"
PROCESSED_DATA_PATH: Path = DATA_DIR / "processed" / "reviews_clean.csv"
SENTIMENT_DATA_PATH: Path = DATA_DIR / "processed" / "reviews_with_sentiment.csv"
THEME_DATA_PATH: Path = DATA_DIR / "processed" / "reviews_with_themes.csv"
SENTIMENT_SUMMARY_PATH: Path = DATA_DIR / "processed" / "sentiment_summary.csv"
KEYWORD_SUMMARY_PATH: Path = DATA_DIR / "processed" / "keywords_per_bank.csv"
THEME_SUMMARY_PATH: Path = DATA_DIR / "processed" / "theme_summary.csv"

# ============================================================================
# Bank Configuration
# ============================================================================

BANKS: List[Dict[str, str]] = [
    {
        "bank": "Dashen Bank",
        "bank_code": "dashen",
        "app_id": "com.dashen.dashensuperapp",
    },
    {
        "bank": "Bank of Abyssinia",
        "bank_code": "abyssinia",
        "app_id": "com.boa.boaMobileBanking",
    },
    {
        "bank": "Commercial Bank of Ethiopia",
        "bank_code": "cbe",
        "app_id": "com.combanketh.mobilebanking",
    },
]
"""
List of bank configurations for scraping.

Each entry contains:
    - bank: Full bank name (display name)
    - bank_code: Short identifier for file naming
    - app_id: Google Play Store app package ID

To add a new bank, append a dictionary with these keys to this list.
"""

# ============================================================================
# Scraper Configuration
# ============================================================================

SCRAPER_SETTINGS: Dict[str, any] = {  # type: ignore
    "lang": "en",  # Language code for reviews (ISO 639-1)
    "country": "et",  # Country code for Google Play Store (ISO 3166-1 alpha-2)
    "min_reviews_per_bank": 400,  # Minimum number of reviews to collect per bank
    "batch_size": 200,  # Number of reviews to fetch per API call
    "sample_reviews": 3,  # Number of sample reviews to display after scraping
}
"""
Google Play Store scraper settings.

Parameters:
    lang (str): Language code for reviews. Default: "en" (English)
    country (str): Country code for Google Play Store. Default: "et" (Ethiopia)
    min_reviews_per_bank (int): Minimum reviews to collect per bank. 
        Target: ≥400 per bank for statistical significance.
    batch_size (int): Reviews fetched per API call. Higher = faster but more 
        memory usage. Default: 200
    sample_reviews (int): Number of sample reviews to print for verification.
        Default: 3

Usage:
    To collect more reviews, increase min_reviews_per_bank:
    SCRAPER_SETTINGS["min_reviews_per_bank"] = 500
"""

# ============================================================================
# Preprocessing Configuration
# ============================================================================

PREPROCESSING_CONFIG: Dict[str, List[str]] = {
    "required_columns": [
        "review",  # Review text content
        "rating",  # Star rating (1-5)
        "date",  # Review date (YYYY-MM-DD format)
        "bank",  # Bank name
        "source",  # Data source (e.g., "google_play")
    ],
    "optional_columns": [
        "review_year",  # Extracted year from date
        "review_month",  # Extracted month from date
        "bank_code",  # Short bank identifier
        "review_length",  # Character count of review text
        "review_id",  # Unique review identifier
        "user_name",  # Reviewer username
        "thumbs_up",  # Number of helpful votes
        "scraped_at",  # Timestamp when review was scraped
    ],
}
"""
Preprocessing configuration for data cleaning pipeline.

required_columns: Columns that MUST be present in the final clean dataset.
    Missing values in these columns will cause rows to be dropped.

optional_columns: Additional columns that may be included if available.
    These enhance analysis but are not strictly required.

The preprocessing script ensures:
    1. All required columns are present
    2. Dates are normalized to YYYY-MM-DD format
    3. Ratings are integers between 1-5
    4. Non-English reviews are filtered out
    5. Duplicates are removed
"""

# ============================================================================
# NLP Configuration
# ============================================================================

NLP_SETTINGS: Dict[str, any] = {  # type: ignore
    # Sentiment Analysis Settings
    # Model: DistilBERT fine-tuned on SST-2 (Stanford Sentiment Treebank)
    # - Fast and efficient (smaller than BERT)
    # - Good accuracy for binary sentiment classification
    # - Falls back to VADER if transformers library unavailable
    # Alternative models:
    #   - "cardiffnlp/twitter-roberta-base-sentiment-latest" (better for social media)
    #   - "nlptown/bert-base-multilingual-uncased-sentiment" (multilingual)
    "hf_model_name": "distilbert-base-uncased-finetuned-sst-2-english",
    
    # Confidence threshold for DistilBERT neutral classification.
    # If model confidence score < 0.6, review is classified as "neutral".
    # Higher values = more neutral classifications (conservative).
    # Lower values = fewer neutral classifications (more decisive).
    # Range: 0.0 to 1.0, Default: 0.6 (balanced approach)
    "neutral_threshold": 0.6,
    
    # Threshold for VADER sentiment analyzer neutral classification.
    # VADER compound score ranges from -1 (most negative) to +1 (most positive).
    # If |compound_score| <= 0.05, review is classified as "neutral".
    # Range: 0.0 to 1.0, Default: 0.05 (standard VADER recommendation)
    "vader_neutral_threshold": 0.05,
    
    # Batch size for DistilBERT sentiment processing.
    # Higher = faster processing but more memory usage.
    # Lower = slower but less memory.
    # Recommended: 16-64 depending on available RAM. Default: 32 (balanced)
    "batch_size": 32,
    
    # Theme Extraction Settings
    # Rule-based theme keywords for topic classification.
    # Each theme maps to a list of keywords. If a review contains any keyword
    # (case-insensitive), it is assigned that theme. Reviews can have multiple themes.
    # Theme Assignment Logic:
    #   1. Tokenize and lemmatize review text (spaCy)
    #   2. Check if any theme keywords appear in tokens
    #   3. Assign all matching themes
    #   4. If no themes match, assign "General Feedback"
    "theme_keywords": {
        "Access & Login": [
            "login",
            "password",
            "pin",
            "otp",
            "credential",
            "access",
        ],
        "Performance & Reliability": [
            "crash",
            "freeze",
            "slow",
            "error",
            "bug",
            "hang",
            "lag",
        ],
        "Transactions & Payments": [
            "transfer",
            "payment",
            "transaction",
            "bill",
            "send",
            "receive",
            "cash",
        ],
        "User Experience": [
            "interface",
            "design",
            "navigation",
            "ui",
            "ux",
            "layout",
        ],
        "Customer Support": [
            "support",
            "help",
            "service",
            "assist",
            "agent",
            "call",
        ],
        "Features & Functionality": [
            "feature",
            "update",
            "option",
            "statement",
            "notification",
            "limit",
        ],
    },
}
"""
NLP settings for sentiment analysis and theme extraction.

Sentiment Analysis:
    - hf_model_name: Hugging Face model for sentiment (DistilBERT by default)
    - neutral_threshold: Confidence threshold for neutral classification (0.6)
    - vader_neutral_threshold: VADER neutral threshold (0.05)
    - batch_size: Batch size for model processing (32)

Theme Extraction:
    - theme_keywords: Dictionary mapping theme names to keyword lists
      Reviews are assigned themes based on keyword matching after lemmatization.
      If no keywords match, review is assigned "General Feedback" theme.

To modify themes, add/remove keywords in the theme_keywords dictionary.
"""

# ============================================================================
# TF-IDF Keyword Extraction Settings
# ============================================================================

# Note: These settings are hardcoded in theme_analysis.py but documented here
# for reference. To modify, edit theme_analysis.py directly.

TFIDF_SETTINGS: Dict[str, any] = {  # type: ignore
    "ngram_range": (1, 2),  # Extract unigrams and bigrams (single words and 2-word phrases)
    "max_features": 500,  # Maximum number of features to extract
    "min_df": 2,  # Minimum document frequency (word must appear in ≥2 reviews)
    "top_n": 15,  # Number of top keywords to extract per bank
}
"""
TF-IDF (Term Frequency-Inverse Document Frequency) settings for keyword extraction.

These parameters control how keywords are extracted from reviews:

ngram_range (tuple): 
    - (1, 1): Only single words
    - (1, 2): Single words and 2-word phrases (default)
    - (1, 3): Up to 3-word phrases (may capture more context but slower)
    
max_features (int):
    Maximum number of unique terms to consider. Higher = more diverse keywords
    but slower processing. Default: 500
    
min_df (int):
    Minimum number of reviews a term must appear in to be considered.
    Higher = only very common terms. Lower = more diverse terms.
    Default: 2 (term must appear in at least 2 reviews)
    
top_n (int):
    Number of top-scoring keywords to return per bank.
    Default: 15

To modify these settings, edit the tfidf_keywords() function in theme_analysis.py.
"""

