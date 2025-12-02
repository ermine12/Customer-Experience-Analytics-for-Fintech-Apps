-- SQL Verification Queries for bank_reviews Database
-- 
-- This file contains SQL queries to verify data integrity and generate reports.
-- Run these queries in PostgreSQL to check:
--   - Review counts per bank
--   - Average ratings
--   - Data completeness
--   - Sentiment distribution
--   - Date ranges
--
-- Usage:
--   psql -U postgres -d bank_reviews -f scripts/verify_data.sql
--   OR
--   Connect via pgAdmin or psql and run queries individually

-- ============================================================================
-- 1. BASIC STATISTICS
-- ============================================================================

-- Total number of reviews
SELECT COUNT(*) as total_reviews FROM reviews;

-- Total number of banks
SELECT COUNT(*) as total_banks FROM banks;

-- ============================================================================
-- 2. REVIEWS PER BANK
-- ============================================================================

-- Count reviews per bank
SELECT 
    b.bank_name,
    COUNT(r.review_id) as review_count,
    ROUND(COUNT(r.review_id) * 100.0 / (SELECT COUNT(*) FROM reviews), 2) as percentage
FROM banks b
LEFT JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_id, b.bank_name
ORDER BY review_count DESC;

-- ============================================================================
-- 3. AVERAGE RATING PER BANK
-- ============================================================================

-- Average rating per bank
SELECT 
    b.bank_name,
    COUNT(r.review_id) as review_count,
    ROUND(AVG(r.rating), 2) as avg_rating,
    MIN(r.rating) as min_rating,
    MAX(r.rating) as max_rating
FROM banks b
LEFT JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_id, b.bank_name
ORDER BY avg_rating DESC;

-- ============================================================================
-- 4. RATING DISTRIBUTION
-- ============================================================================

-- Rating distribution (all reviews)
SELECT 
    rating,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reviews), 2) as percentage
FROM reviews
GROUP BY rating
ORDER BY rating DESC;

-- Rating distribution per bank
SELECT 
    b.bank_name,
    r.rating,
    COUNT(*) as count
FROM banks b
JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_name, r.rating
ORDER BY b.bank_name, r.rating DESC;

-- ============================================================================
-- 5. SENTIMENT ANALYSIS
-- ============================================================================

-- Sentiment distribution (all reviews)
SELECT 
    sentiment_label,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reviews WHERE sentiment_label IS NOT NULL), 2) as percentage
FROM reviews
WHERE sentiment_label IS NOT NULL
GROUP BY sentiment_label
ORDER BY 
    CASE sentiment_label
        WHEN 'positive' THEN 1
        WHEN 'neutral' THEN 2
        WHEN 'negative' THEN 3
    END;

-- Sentiment distribution per bank
SELECT 
    b.bank_name,
    r.sentiment_label,
    COUNT(*) as count,
    ROUND(AVG(r.sentiment_score), 3) as avg_sentiment_score
FROM banks b
JOIN reviews r ON b.bank_id = r.bank_id
WHERE r.sentiment_label IS NOT NULL
GROUP BY b.bank_name, r.sentiment_label
ORDER BY b.bank_name, 
    CASE r.sentiment_label
        WHEN 'positive' THEN 1
        WHEN 'neutral' THEN 2
        WHEN 'negative' THEN 3
    END;

-- ============================================================================
-- 6. TEMPORAL ANALYSIS
-- ============================================================================

-- Date range of reviews
SELECT 
    MIN(review_date) as earliest_review,
    MAX(review_date) as latest_review,
    COUNT(DISTINCT review_date) as unique_dates
FROM reviews
WHERE review_date IS NOT NULL;

-- Reviews per year
SELECT 
    review_year,
    COUNT(*) as review_count
FROM reviews
WHERE review_year IS NOT NULL
GROUP BY review_year
ORDER BY review_year DESC;

-- Reviews per month (across all years)
SELECT 
    review_month,
    COUNT(*) as review_count
FROM reviews
WHERE review_month IS NOT NULL
GROUP BY review_month
ORDER BY review_month;

-- Reviews per bank per year
SELECT 
    b.bank_name,
    r.review_year,
    COUNT(*) as review_count
FROM banks b
JOIN reviews r ON b.bank_id = r.bank_id
WHERE r.review_year IS NOT NULL
GROUP BY b.bank_name, r.review_year
ORDER BY b.bank_name, r.review_year DESC;

-- ============================================================================
-- 7. DATA QUALITY CHECKS
-- ============================================================================

-- Check for missing critical data
SELECT 
    'Missing review_text' as issue,
    COUNT(*) as count
FROM reviews
WHERE review_text IS NULL OR review_text = ''
UNION ALL
SELECT 
    'Missing rating' as issue,
    COUNT(*) as count
FROM reviews
WHERE rating IS NULL
UNION ALL
SELECT 
    'Missing review_date' as issue,
    COUNT(*) as count
FROM reviews
WHERE review_date IS NULL
UNION ALL
SELECT 
    'Invalid rating (< 1 or > 5)' as issue,
    COUNT(*) as count
FROM reviews
WHERE rating < 1 OR rating > 5;

-- Check for reviews without sentiment
SELECT 
    COUNT(*) as reviews_without_sentiment,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reviews), 2) as percentage
FROM reviews
WHERE sentiment_label IS NULL;

-- ============================================================================
-- 8. TOP REVIEWS
-- ============================================================================

-- Top 10 most helpful reviews (by thumbs_up)
SELECT 
    b.bank_name,
    r.rating,
    r.review_text,
    r.thumbs_up,
    r.review_date
FROM reviews r
JOIN banks b ON r.bank_id = b.bank_id
WHERE r.thumbs_up > 0
ORDER BY r.thumbs_up DESC
LIMIT 10;

-- Top 10 longest reviews
SELECT 
    b.bank_name,
    r.rating,
    LEFT(r.review_text, 200) as review_preview,
    r.review_length,
    r.review_date
FROM reviews r
JOIN banks b ON r.bank_id = b.bank_id
WHERE r.review_length IS NOT NULL
ORDER BY r.review_length DESC
LIMIT 10;

-- ============================================================================
-- 9. BANK COMPARISON SUMMARY
-- ============================================================================

-- Comprehensive bank comparison
SELECT 
    b.bank_name,
    COUNT(r.review_id) as total_reviews,
    ROUND(AVG(r.rating), 2) as avg_rating,
    COUNT(CASE WHEN r.sentiment_label = 'positive' THEN 1 END) as positive_reviews,
    COUNT(CASE WHEN r.sentiment_label = 'negative' THEN 1 END) as negative_reviews,
    ROUND(AVG(r.sentiment_score), 3) as avg_sentiment_score,
    MIN(r.review_date) as first_review,
    MAX(r.review_date) as last_review
FROM banks b
LEFT JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_id, b.bank_name
ORDER BY avg_rating DESC;

-- ============================================================================
-- 10. FOREIGN KEY INTEGRITY CHECK
-- ============================================================================

-- Check for orphaned reviews (reviews without valid bank_id)
SELECT 
    COUNT(*) as orphaned_reviews
FROM reviews r
LEFT JOIN banks b ON r.bank_id = b.bank_id
WHERE b.bank_id IS NULL;

-- Check for banks without reviews
SELECT 
    b.bank_name,
    COUNT(r.review_id) as review_count
FROM banks b
LEFT JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_id, b.bank_name
HAVING COUNT(r.review_id) = 0;

