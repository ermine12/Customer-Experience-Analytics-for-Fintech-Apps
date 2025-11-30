# Customer Experience Analytics for Fintech Apps - Project Report

## Executive Summary

This project focuses on building a comprehensive analytics pipeline for analyzing customer reviews of Ethiopian banking mobile applications. The system collects, processes, and analyzes user feedback from Google Play Store to provide actionable insights into customer sentiment, themes, and key issues across three major banks: Dashen Bank, Bank of Abyssinia, and Commercial Bank of Ethiopia.

---

## 1. Project Overview

### 1.1 Objective
Develop a reproducible data pipeline that:
- Collects customer reviews from Google Play Store
- Cleans and preprocesses review data
- Performs sentiment analysis on customer feedback
- Extracts themes and keywords from reviews
- Provides comprehensive analytics and visualizations for stakeholders

### 1.2 Banks Analyzed
- **Dashen Bank** (`com.dashen.dashensuperapp`)
- **Bank of Abyssinia** (`com.boa.boaMobileBanking`)
- **Commercial Bank of Ethiopia** (`com.combanketh.mobilebanking`)

---

## 2. Completed Work

### 2.1 Data Collection Pipeline

#### 2.1.1 Review Scraping (`scripts/scrape_reviews.py`)
- **Status**: ✅ Completed
- **Functionality**:
  - Fetches app metadata (title, rating, installs) for each bank
  - Scrapes ≥400 reviews per bank from Google Play Store
  - Collects comprehensive review data including:
    - Review content and ratings
    - Review dates and user information
    - Thumbs-up counts and app versions
  - Normalizes data into a consistent schema
  - Saves raw data to `data/raw/reviews_raw.csv`

- **Results**:
  - Successfully collected reviews from all three banks
  - Generated app metadata file (`data/raw/app_info.csv`)

#### 2.1.2 Data Preprocessing (`scripts/preprocess_reviews.py`)
- **Status**: ✅ Completed
- **Functionality**:
  - Removes duplicate reviews
  - Filters out missing critical data (review, rating, date, bank)
  - Normalizes dates to YYYY-MM-DD format
  - Removes non-English reviews (filters Amharic text using Unicode regex)
  - Validates ratings (ensures 1-5 star range)
  - Adds helper fields:
    - `review_year` and `review_month` for temporal analysis
    - `review_length` for text analysis
  - Generates preprocessing statistics and quality metrics

- **Results**:
  - **Final dataset**: 1,151 clean reviews
  - **Data quality**: <5% missing records (meets KPI requirement)
  - **Distribution**: Balanced across banks (~33% each)
  - **Output**: `data/processed/reviews_clean.csv`

### 2.2 Natural Language Processing & Analysis

#### 2.2.1 Sentiment Analysis (`scripts/sentiment_analysis.py`)
- **Status**: ✅ Completed
- **Functionality**:
  - Uses DistilBERT model (`distilbert-base-uncased-finetuned-sst-2-english`) for sentiment scoring
  - Falls back to VADER sentiment analyzer if transformers unavailable
  - Classifies reviews into three categories:
    - **Positive**: High confidence positive sentiment
    - **Neutral**: Low confidence or ambiguous sentiment
    - **Negative**: High confidence negative sentiment
  - Generates sentiment scores (0.0 to 1.0) for each review
  - Aggregates sentiment statistics by bank and rating

- **Results**:
  - **Coverage**: 100% of reviews have sentiment scores
  - **Overall Distribution**:
    - Positive: 59.6% (686 reviews)
    - Neutral: 26.7% (307 reviews)
    - Negative: 13.7% (158 reviews)
  - **Bank Comparison**:
    - Dashen Bank: 66.5% positive (highest)
    - Commercial Bank of Ethiopia: 61.3% positive
    - Bank of Abyssinia: 51.0% positive (highest negative at 19.8%)
  - **Rating Correlation**: Strong correlation between ratings and sentiment
    - 5-star reviews: 73.8% positive
    - 1-star reviews: 46.2% negative
  - **Outputs**:
    - `data/processed/reviews_with_sentiment.csv` (enriched reviews)
    - `data/processed/sentiment_summary.csv` (aggregated statistics)

#### 2.2.2 Theme & Keyword Analysis (`scripts/theme_analysis.py`)
- **Status**: ✅ Completed
- **Functionality**:
  - Text preprocessing using spaCy NLP library
  - Tokenization, lemmatization, and stopword removal
  - TF-IDF keyword extraction per bank (top keywords by importance)
  - Rule-based theme assignment using keyword matching
  - Identifies 7 major themes:
    1. **General Feedback** (78.1% of reviews)
    2. **Features & Functionality** (8.3%)
    3. **Transactions & Payments** (7.0%)
    4. **Performance & Reliability** (5.1%)
    5. **Customer Support** (4.1%)
    6. **Access & Login** (3.9%)
    7. **User Experience** (2.7%)

- **Results**:
  - **Coverage**: 100% of reviews have theme assignments
  - **Top Keywords by Bank**:
    - Common keywords: "good", "app", "nice", "bank"
    - Bank-specific: "boa", "cbe", "dashen", "wow", "super"
  - **Theme Distribution**:
    - Varies by bank (e.g., Performance & Reliability issues more common in Bank of Abyssinia)
    - General Feedback dominates across all banks
  - **Outputs**:
    - `data/processed/reviews_with_themes.csv` (themed reviews)
    - `data/processed/keywords_per_bank.csv` (TF-IDF keyword scores)
    - `data/processed/theme_summary.csv` (theme statistics with sample reviews)

### 2.3 Exploratory Data Analysis

#### 2.3.1 Preprocessing EDA (`notebooks/preprocessing_eda.ipynb`)
- **Status**: ✅ Completed
- **Analysis Includes**:
  - Dataset overview and quality metrics
  - Reviews distribution by bank (balanced ~33% each)
  - Rating distribution analysis:
    - 5-star: 61.6% (709 reviews)
    - 1-star: 21.6% (249 reviews)
    - 4-star: 7.5% (86 reviews)
    - 3-star: 5.6% (65 reviews)
    - 2-star: 3.6% (42 reviews)
  - Temporal trends (reviews from 2024-2025)
  - Sample reviews by rating category

#### 2.3.2 Sentiment EDA (`notebooks/sentiment_eda.ipynb`)
- **Status**: ✅ Completed
- **Analysis Includes**:
  - Overall sentiment distribution (positive/neutral/negative)
  - Sentiment by bank comparison
  - Sentiment by rating correlation
  - Sentiment score distributions and statistics
  - Heatmaps showing sentiment percentages by bank and rating
  - Coverage analysis (100% coverage achieved)

#### 2.3.3 Theme EDA (`notebooks/theme_eda.ipynb`)
- **Status**: ✅ Completed
- **Analysis Includes**:
  - Theme frequency and distribution across all reviews
  - Theme distribution by bank
  - Top keywords per bank (TF-IDF scores)
  - Theme-sentiment correlations
  - Sample reviews by theme category
  - Theme summary with average ratings and exemplar reviews

### 2.4 Data Outputs

All processed data is stored in `data/processed/`:

1. **`reviews_clean.csv`**: Preprocessed reviews (1,151 records)
2. **`reviews_with_sentiment.csv`**: Reviews with sentiment labels and scores
3. **`reviews_with_themes.csv`**: Reviews with theme assignments and keywords
4. **`sentiment_summary.csv`**: Aggregated sentiment statistics by bank and rating
5. **`theme_summary.csv`**: Theme statistics with review counts and sample reviews
6. **`keywords_per_bank.csv`**: Top TF-IDF keywords for each bank

---

## 3. Key Findings

### 3.1 Sentiment Insights
- **Overall Positive Sentiment**: 59.6% of reviews are positive
- **Bank Performance**:
  - Dashen Bank leads with 66.5% positive sentiment
  - Bank of Abyssinia has the highest negative sentiment (19.8%)
- **Rating-Sentiment Correlation**: Strong positive correlation (higher ratings = more positive sentiment)

### 3.2 Theme Insights
- **Most Common Issues**: General Feedback dominates (78.1%)
- **Technical Issues**: Performance & Reliability and Access & Login are significant concerns
- **Feature Requests**: Features & Functionality theme indicates areas for improvement
- **Bank-Specific Patterns**: Each bank shows unique theme distributions

### 3.3 Data Quality
- **Coverage**: 100% of reviews processed for both sentiment and themes
- **Data Completeness**: <5% missing data (exceeds KPI requirement)
- **Balance**: Even distribution across three banks (~33% each)

---

## 4. Planned Work

### 4.1 Database Integration

#### 4.1.1 PostgreSQL Database Setup
- **Objective**: Load all processed CSV data into a PostgreSQL database for efficient querying and data management
- **Planned Tasks**:
  1. **Database Schema Design**:
     - Create tables for:
       - `reviews` (main review data with sentiment and themes)
       - `sentiment_summary` (aggregated sentiment statistics)
       - `theme_summary` (theme statistics)
       - `keywords_summary` (TF-IDF keywords per bank)
     - Design appropriate indexes for performance
     - Set up foreign key relationships

  2. **Data Loading Script**:
     - Create `scripts/load_to_postgres.py` script
     - Read all processed CSV files
     - Transform data to match database schema
     - Insert data into PostgreSQL tables
     - Handle duplicates and data validation
     - Generate loading statistics

  3. **Database Configuration**:
     - Set up connection configuration in `config.py`
     - Support for local and remote PostgreSQL instances
     - Environment variable support for credentials

  4. **Data Validation**:
     - Verify data integrity after loading
     - Compare record counts between CSV and database
     - Validate data types and constraints

#### 4.1.2 Expected Benefits
- Centralized data storage for easier access
- Efficient querying capabilities
- Support for future data updates and incremental loading
- Foundation for API development
- Better data governance and versioning

### 4.2 Client Visualization Dashboard

#### 4.2.1 Dashboard Development
- **Objective**: Create an interactive web-based dashboard for client visualization
- **Technology Stack Options**:
  - **Option 1**: Streamlit (Python-based, quick development)
  - **Option 2**: Dash (Plotly-based, more customization)
  - **Option 3**: Flask/FastAPI + React (full-stack solution)

#### 4.2.2 Planned Visualizations

1. **Executive Summary Dashboard**:
   - Overall sentiment distribution (pie/bar charts)
   - Total reviews count and trends
   - Key performance indicators (KPIs)
   - Bank comparison overview

2. **Sentiment Analysis Dashboard**:
   - Sentiment distribution by bank (stacked bar charts)
   - Sentiment over time (line charts)
   - Sentiment by rating (heatmaps)
   - Sentiment score distributions (histograms)
   - Top positive/negative reviews

3. **Theme Analysis Dashboard**:
   - Theme frequency by bank (bar charts)
   - Theme-sentiment correlation (heatmaps)
   - Top keywords per bank (word clouds or bar charts)
   - Theme distribution over time
   - Sample reviews by theme

4. **Bank Comparison Dashboard**:
   - Side-by-side bank comparisons
   - Performance metrics comparison
   - Issue identification by bank
   - Competitive analysis

5. **Interactive Features**:
   - Date range filtering
   - Bank selection filters
   - Rating filters
   - Theme filters
   - Search functionality for reviews
   - Export capabilities (PDF, CSV)

#### 4.2.3 Dashboard Features
- **Real-time Data**: Connect directly to PostgreSQL database
- **Responsive Design**: Works on desktop, tablet, and mobile
- **User Authentication**: Optional login system for client access
- **Export Functionality**: Download reports and charts
- **Customizable Views**: Save favorite dashboard configurations

#### 4.2.4 Implementation Plan
1. **Phase 1**: Basic dashboard with core visualizations
   - Set up web framework
   - Connect to PostgreSQL
   - Create basic charts and tables
   - Implement filtering

2. **Phase 2**: Enhanced interactivity
   - Add advanced filtering options
   - Implement drill-down capabilities
   - Add search functionality
   - Create export features

3. **Phase 3**: Polish and deployment
   - Improve UI/UX design
   - Add user authentication
   - Optimize performance
   - Deploy to production (cloud hosting)

---

## 5. Technical Architecture

### 5.1 Current Architecture
```
Data Sources (Google Play Store)
    ↓
Scraping Script (scrape_reviews.py)
    ↓
Raw Data (CSV)
    ↓
Preprocessing (preprocess_reviews.py)
    ↓
Clean Data (CSV)
    ↓
┌─────────────────────┬─────────────────────┐
│ Sentiment Analysis  │ Theme Analysis      │
│ (sentiment_analysis)│ (theme_analysis)    │
└─────────────────────┴─────────────────────┘
    ↓
Processed Data (CSV)
    ↓
EDA Notebooks (Jupyter)
```

### 5.2 Planned Architecture
```
Data Sources (Google Play Store)
    ↓
Scraping Script
    ↓
Raw Data (CSV)
    ↓
Preprocessing
    ↓
Clean Data (CSV)
    ↓
┌─────────────────────┬─────────────────────┐
│ Sentiment Analysis  │ Theme Analysis      │
└─────────────────────┴─────────────────────┘
    ↓
Processed Data (CSV)
    ↓
PostgreSQL Database ←──┐
    ↓                  │
Dashboard (Web App) ───┘
    ↓
Client Visualization
```

---

## 6. Project Statistics

### 6.1 Data Collection
- **Total Reviews Collected**: 1,151 reviews
- **Banks Covered**: 3 banks
- **Date Range**: September 2024 - November 2025
- **Data Sources**: Google Play Store

### 6.2 Processing Coverage
- **Preprocessing**: 100% coverage
- **Sentiment Analysis**: 100% coverage (1,151 reviews)
- **Theme Analysis**: 100% coverage (1,151 reviews)

### 6.3 Analysis Results
- **Sentiment Labels**: 3 categories (positive, neutral, negative)
- **Themes Identified**: 7 major themes
- **Keywords Extracted**: Top 15 per bank via TF-IDF
- **Summary Reports**: 3 summary CSV files generated

---

## 7. Dependencies & Tools

### 7.1 Core Libraries
- **Data Processing**: pandas, numpy
- **Web Scraping**: google-play-scraper
- **NLP**: transformers, spacy, vaderSentiment, scikit-learn
- **Visualization**: matplotlib, seaborn
- **Notebooks**: jupyter

### 7.2 Planned Additions
- **Database**: psycopg2 (PostgreSQL adapter)
- **Web Framework**: streamlit or dash (for dashboard)
- **Deployment**: docker (optional, for containerization)

---

## 8. Next Steps & Timeline

### 8.1 Immediate Next Steps
1. **Week 1-2**: PostgreSQL Database Setup
   - Design database schema
   - Create database and tables
   - Develop data loading script
   - Test data integrity

2. **Week 3-4**: Dashboard Development (Phase 1)
   - Choose web framework
   - Set up basic dashboard structure
   - Connect to PostgreSQL
   - Create core visualizations

3. **Week 5-6**: Dashboard Enhancement (Phase 2)
   - Add interactivity and filters
   - Implement advanced features
   - User testing and feedback

4. **Week 7**: Deployment & Documentation
   - Deploy dashboard
   - Create user documentation
   - Final testing and bug fixes

### 8.2 Future Enhancements
- Automated data refresh pipeline
- Email alerts for negative sentiment spikes
- Machine learning models for sentiment prediction
- Integration with other data sources
- Mobile app version of dashboard
- API development for programmatic access

---

## 9. Conclusion

The project has successfully completed the data collection, preprocessing, and analysis phases. We have:
- ✅ Collected 1,151 reviews from 3 Ethiopian banks
- ✅ Cleaned and preprocessed all data with high quality
- ✅ Performed comprehensive sentiment analysis (100% coverage)
- ✅ Extracted themes and keywords from all reviews
- ✅ Created detailed EDA notebooks with visualizations

**Next Phase**: Database integration and client visualization dashboard development will transform this analytical pipeline into a production-ready system that provides actionable insights to stakeholders in an accessible, interactive format.

---

## Appendix: File Structure

```
Customer Experience Analytics for Fintech Apps/
├── config.py                          # Configuration file
├── requirements.txt                   # Python dependencies
├── README.md                          # Project documentation
├── PROJECT_REPORT.md                  # This report
│
├── scripts/
│   ├── scrape_reviews.py              # Google Play scraper
│   ├── preprocess_reviews.py          # Data cleaning
│   ├── sentiment_analysis.py          # Sentiment scoring
│   └── theme_analysis.py              # Theme extraction
│
├── notebooks/
│   ├── preprocessing_eda.ipynb        # Preprocessing EDA
│   ├── sentiment_eda.ipynb            # Sentiment EDA
│   └── theme_eda.ipynb                # Theme EDA
│
└── data/
    ├── raw/
    │   ├── reviews_raw.csv            # Raw scraped data
    │   └── app_info.csv               # App metadata
    │
    └── processed/
        ├── reviews_clean.csv          # Cleaned reviews
        ├── reviews_with_sentiment.csv # Sentiment-enriched
        ├── reviews_with_themes.csv    # Theme-enriched
        ├── sentiment_summary.csv      # Sentiment stats
        ├── theme_summary.csv          # Theme stats
        └── keywords_per_bank.csv      # TF-IDF keywords
```

---

**Report Generated**: December 2024  
**Project Status**: Phase 1 & 2 Complete | Phase 3 (Database & Dashboard) - In Planning

