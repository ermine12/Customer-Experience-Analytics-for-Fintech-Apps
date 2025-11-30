from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "reviews_raw.csv"
APP_INFO_PATH = DATA_DIR / "raw" / "app_info.csv"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "reviews_clean.csv"
SENTIMENT_DATA_PATH = DATA_DIR / "processed" / "reviews_with_sentiment.csv"
THEME_DATA_PATH = DATA_DIR / "processed" / "reviews_with_themes.csv"
SENTIMENT_SUMMARY_PATH = DATA_DIR / "processed" / "sentiment_summary.csv"
KEYWORD_SUMMARY_PATH = DATA_DIR / "processed" / "keywords_per_bank.csv"
THEME_SUMMARY_PATH = DATA_DIR / "processed" / "theme_summary.csv"

BANKS = [
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

SCRAPER_SETTINGS = {
    "lang": "en",
    "country": "et",
    "min_reviews_per_bank": 400,
    "batch_size": 200,
    "sample_reviews": 3,
}

PREPROCESSING_CONFIG = {
    "required_columns": ["review", "rating", "date", "bank", "source"],
    "optional_columns": [
        "review_year",
        "review_month",
        "bank_code",
        "review_length",
        "review_id",
        "user_name",
        "thumbs_up",
        "scraped_at",
    ],
}

NLP_SETTINGS = {
    "hf_model_name": "distilbert-base-uncased-finetuned-sst-2-english",
    "neutral_threshold": 0.6,
    "vader_neutral_threshold": 0.05,
    "batch_size": 32,
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

