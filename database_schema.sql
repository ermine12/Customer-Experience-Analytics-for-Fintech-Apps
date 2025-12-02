-- PostgreSQL Database Schema for bank_reviews
-- 
-- This file contains the complete database schema definition.
-- It can be used to recreate the database structure from scratch.
--
-- Database: bank_reviews
-- Created: 2024
--
-- Usage:
--   1. Create database: CREATE DATABASE bank_reviews;
--   2. Run this file: psql -U postgres -d bank_reviews -f database_schema.sql
--   OR
--   Use the setup_database.py script which creates everything automatically
--
-- ============================================================================
-- DATABASE CREATION
-- ============================================================================

-- Note: Database creation must be done separately (requires superuser privileges)
-- CREATE DATABASE bank_reviews;

-- ============================================================================
-- TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Banks Table
-- ----------------------------------------------------------------------------
-- Stores information about the banks being analyzed

CREATE TABLE IF NOT EXISTS banks (
    bank_id SERIAL PRIMARY KEY,
    bank_name VARCHAR(100) NOT NULL UNIQUE,
    app_name VARCHAR(200),
    bank_code VARCHAR(50),
    app_id VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE banks IS 'Stores information about banks and their mobile apps';
COMMENT ON COLUMN banks.bank_id IS 'Primary key, auto-incrementing integer';
COMMENT ON COLUMN banks.bank_name IS 'Full name of the bank (e.g., "Dashen Bank")';
COMMENT ON COLUMN banks.app_name IS 'Name of the mobile banking app';
COMMENT ON COLUMN banks.bank_code IS 'Short identifier for the bank (e.g., "dashen")';
COMMENT ON COLUMN banks.app_id IS 'Google Play Store app package ID';
COMMENT ON COLUMN banks.created_at IS 'Timestamp when bank record was created';

-- ----------------------------------------------------------------------------
-- 2. Reviews Table
-- ----------------------------------------------------------------------------
-- Stores the scraped and processed review data

CREATE TABLE IF NOT EXISTS reviews (
    review_id VARCHAR(200) PRIMARY KEY,
    bank_id INTEGER NOT NULL REFERENCES banks(bank_id) ON DELETE CASCADE,
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
);

COMMENT ON TABLE reviews IS 'Stores individual customer reviews with sentiment and metadata';
COMMENT ON COLUMN reviews.review_id IS 'Unique identifier for the review (from source)';
COMMENT ON COLUMN reviews.bank_id IS 'Foreign key to banks table';
COMMENT ON COLUMN reviews.review_text IS 'Full text content of the review';
COMMENT ON COLUMN reviews.rating IS 'Star rating (1-5)';
COMMENT ON COLUMN reviews.review_date IS 'Date when review was posted';
COMMENT ON COLUMN reviews.review_year IS 'Extracted year from review_date';
COMMENT ON COLUMN reviews.review_month IS 'Extracted month from review_date';
COMMENT ON COLUMN reviews.review_length IS 'Character count of review_text';
COMMENT ON COLUMN reviews.sentiment_label IS 'Sentiment classification: positive, neutral, or negative';
COMMENT ON COLUMN reviews.sentiment_score IS 'Sentiment score (0.0 to 1.0)';
COMMENT ON COLUMN reviews.sentiment_source IS 'Source of sentiment analysis (e.g., "distilbert", "vader")';
COMMENT ON COLUMN reviews.source IS 'Data source (e.g., "google_play")';
COMMENT ON COLUMN reviews.user_name IS 'Name of the reviewer';
COMMENT ON COLUMN reviews.thumbs_up IS 'Number of helpful votes';

-- ----------------------------------------------------------------------------
-- 3. Themes Table
-- ----------------------------------------------------------------------------
-- Stores theme assignments for reviews (many-to-many relationship)

CREATE TABLE IF NOT EXISTS themes (
    theme_id SERIAL PRIMARY KEY,
    review_id VARCHAR(200) NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    theme_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(review_id, theme_name)
);

COMMENT ON TABLE themes IS 'Stores theme assignments for reviews (reviews can have multiple themes)';
COMMENT ON COLUMN themes.theme_id IS 'Primary key, auto-incrementing integer';
COMMENT ON COLUMN themes.review_id IS 'Foreign key to reviews table';
COMMENT ON COLUMN themes.theme_name IS 'Name of the theme (e.g., "Performance & Reliability")';

-- ----------------------------------------------------------------------------
-- 4. Keywords Table
-- ----------------------------------------------------------------------------
-- Stores keywords extracted from reviews

CREATE TABLE IF NOT EXISTS keywords (
    keyword_id SERIAL PRIMARY KEY,
    review_id VARCHAR(200) NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    keyword VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(review_id, keyword)
);

COMMENT ON TABLE keywords IS 'Stores keywords extracted from reviews via TF-IDF';
COMMENT ON COLUMN keywords.keyword_id IS 'Primary key, auto-incrementing integer';
COMMENT ON COLUMN keywords.review_id IS 'Foreign key to reviews table';
COMMENT ON COLUMN keywords.keyword IS 'Extracted keyword or phrase';

-- ----------------------------------------------------------------------------
-- 5. Sentiment Summary Table
-- ----------------------------------------------------------------------------
-- Stores aggregated sentiment statistics

CREATE TABLE IF NOT EXISTS sentiment_summary (
    summary_id SERIAL PRIMARY KEY,
    bank_id INTEGER NOT NULL REFERENCES banks(bank_id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_count INTEGER NOT NULL DEFAULT 0,
    positive_pct DECIMAL(5, 2),
    neutral_pct DECIMAL(5, 2),
    negative_pct DECIMAL(5, 2),
    mean_score DECIMAL(5, 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bank_id, rating)
);

COMMENT ON TABLE sentiment_summary IS 'Aggregated sentiment statistics by bank and rating';
COMMENT ON COLUMN sentiment_summary.bank_id IS 'Foreign key to banks table';
COMMENT ON COLUMN sentiment_summary.rating IS 'Star rating (1-5)';
COMMENT ON COLUMN sentiment_summary.review_count IS 'Number of reviews in this category';
COMMENT ON COLUMN sentiment_summary.positive_pct IS 'Percentage of positive reviews';
COMMENT ON COLUMN sentiment_summary.neutral_pct IS 'Percentage of neutral reviews';
COMMENT ON COLUMN sentiment_summary.negative_pct IS 'Percentage of negative reviews';
COMMENT ON COLUMN sentiment_summary.mean_score IS 'Average sentiment score';

-- ----------------------------------------------------------------------------
-- 6. Theme Summary Table
-- ----------------------------------------------------------------------------
-- Stores aggregated theme statistics

CREATE TABLE IF NOT EXISTS theme_summary (
    theme_summary_id SERIAL PRIMARY KEY,
    bank_id INTEGER NOT NULL REFERENCES banks(bank_id) ON DELETE CASCADE,
    theme_name VARCHAR(100) NOT NULL,
    review_count INTEGER NOT NULL DEFAULT 0,
    avg_rating DECIMAL(3, 2),
    sample_review TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bank_id, theme_name)
);

COMMENT ON TABLE theme_summary IS 'Aggregated theme statistics by bank';
COMMENT ON COLUMN theme_summary.bank_id IS 'Foreign key to banks table';
COMMENT ON COLUMN theme_summary.theme_name IS 'Name of the theme';
COMMENT ON COLUMN theme_summary.review_count IS 'Number of reviews with this theme';
COMMENT ON COLUMN theme_summary.avg_rating IS 'Average rating for reviews with this theme';
COMMENT ON COLUMN theme_summary.sample_review IS 'Example review text for this theme';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Indexes for better query performance

-- Reviews table indexes
CREATE INDEX IF NOT EXISTS idx_reviews_bank_id ON reviews(bank_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(review_date);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_reviews_year ON reviews(review_year);
CREATE INDEX IF NOT EXISTS idx_reviews_month ON reviews(review_month);

-- Themes table indexes
CREATE INDEX IF NOT EXISTS idx_themes_review_id ON themes(review_id);
CREATE INDEX IF NOT EXISTS idx_themes_name ON themes(theme_name);

-- Keywords table indexes
CREATE INDEX IF NOT EXISTS idx_keywords_review_id ON keywords(review_id);

-- ============================================================================
-- SAMPLE DATA QUERIES
-- ============================================================================

-- Example: Insert a bank
-- INSERT INTO banks (bank_name, bank_code, app_id) 
-- VALUES ('Dashen Bank', 'dashen', 'com.dashen.dashensuperapp');

-- Example: Insert a review
-- INSERT INTO reviews (review_id, bank_id, review_text, rating, review_date)
-- VALUES ('review_123', 1, 'Great app!', 5, '2024-01-15');

-- ============================================================================
-- NOTES
-- ============================================================================

-- Foreign Key Relationships:
--   reviews.bank_id -> banks.bank_id
--   themes.review_id -> reviews.review_id
--   keywords.review_id -> reviews.review_id
--   sentiment_summary.bank_id -> banks.bank_id
--   theme_summary.bank_id -> banks.bank_id

-- Constraints:
--   - reviews.rating must be between 1 and 5
--   - sentiment_summary.rating must be between 1 and 5
--   - banks.bank_name must be unique
--   - reviews.review_id is the primary key
--   - themes and keywords have unique constraints on (review_id, theme_name/keyword)

-- Data Types:
--   - SERIAL: Auto-incrementing integer (for primary keys)
--   - VARCHAR(n): Variable-length string with max length n
--   - TEXT: Unlimited length string
--   - INTEGER: 32-bit integer
--   - DECIMAL(p, s): Fixed-point number with p digits and s decimal places
--   - DATE: Date value (YYYY-MM-DD)
--   - TIMESTAMP: Date and time value

