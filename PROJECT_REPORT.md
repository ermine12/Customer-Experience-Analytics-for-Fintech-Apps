# Customer Experience Analytics for Fintech Apps - Project Report

## Executive Summary

This project focuses on building a comprehensive analytics pipeline for analyzing customer reviews of Ethiopian banking mobile applications. The system collects, processes, and analyzes user feedback from Google Play Store to provide actionable insights into customer sentiment, themes, and key issues across three major banks: Dashen Bank, Bank of Abyssinia, and Commercial Bank of Ethiopia.

---

## Business Objective

### The Business Problem

Ethiopian banking institutions face a critical challenge in understanding and responding to customer feedback about their mobile banking applications. With the rapid digitization of banking services and increasing competition in the fintech space, banks need to:

1. **Monitor Customer Satisfaction in Real-Time**: Traditional methods of collecting customer feedback (surveys, focus groups) are slow, expensive, and often suffer from low response rates. Banks need immediate insights into how customers perceive their mobile apps.

2. **Identify Pain Points Systematically**: Customer reviews on app stores contain valuable, unfiltered feedback about app performance, features, and user experience. However, manually analyzing thousands of reviews is time-consuming and impractical, leading to delayed responses to critical issues.

3. **Make Data-Driven Product Decisions**: Product managers and development teams need quantitative and qualitative insights to prioritize feature development, bug fixes, and UX improvements based on actual customer needs rather than assumptions.

4. **Competitive Intelligence**: Understanding how competitors' apps are perceived helps banks identify market gaps, benchmark performance, and develop competitive advantages.

5. **Reduce Customer Churn**: Negative reviews and unresolved issues can lead to customer dissatisfaction and churn. Early identification of problems allows banks to address issues proactively before they escalate.

### Business Value Proposition

This analytics solution addresses these challenges by:

- **Automating Review Analysis**: Transforms unstructured review data into structured, actionable insights without manual effort
- **Enabling Proactive Issue Resolution**: Identifies critical issues (performance problems, login issues, transaction failures) before they become widespread complaints
- **Supporting Strategic Decision-Making**: Provides quantitative metrics (sentiment scores, theme frequencies) to guide product roadmap and resource allocation
- **Improving Customer Satisfaction**: Helps banks understand what customers love and hate, enabling targeted improvements that enhance user experience
- **Reducing Analysis Time**: Cuts down review analysis time from weeks to hours, allowing faster response to customer concerns
- **Enabling Competitive Benchmarking**: Provides side-by-side comparison of sentiment and themes across competing banks

### Target Stakeholders

- **Product Managers**: Need insights to prioritize features and improvements
- **Customer Experience Teams**: Require understanding of customer sentiment and pain points
- **Development Teams**: Need to identify technical issues and bugs mentioned in reviews
- **Executive Leadership**: Require high-level metrics and trends for strategic decision-making
- **Marketing Teams**: Can leverage positive sentiment and themes for promotional campaigns

### Success Metrics

The success of this project will be measured by:
- **Actionability**: Ability to identify specific, addressable issues from review data
- **Timeliness**: Reduction in time-to-insight from weeks to hours
- **Coverage**: Analysis of 100% of available reviews (not just samples)
- **Accuracy**: Reliable sentiment classification and theme identification
- **Usability**: Easy-to-understand visualizations and reports for non-technical stakeholders

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

### 2.5 Parameter Choices and Configuration

#### 2.5.1 Sentiment Analysis Parameters

**Model Selection:**
- **Primary Model**: `distilbert-base-uncased-finetuned-sst-2-english` (DistilBERT)
  - **Rationale**: Fast and efficient while maintaining good accuracy
  - **Fallback**: VADER sentiment analyzer (if transformers unavailable)
  - **Alternative Models Considered**:
    - `cardiffnlp/twitter-roberta-base-sentiment-latest` (better for social media)
    - `nlptown/bert-base-multilingual-uncased-sentiment` (multilingual support)

**Neutral Classification Thresholds:**
- **DistilBERT `neutral_threshold`**: 0.6
  - **Rationale**: If model confidence < 0.6, classify as neutral
  - **Impact**: Higher values = more conservative (more neutrals), lower = more decisive
  - **Tuning**: Balanced at 0.6 to capture ambiguous reviews without over-classifying

- **VADER `vader_neutral_threshold`**: 0.05
  - **Rationale**: Standard VADER recommendation for neutral zone
  - **Logic**: If |compound_score| ≤ 0.05, classify as neutral
  - **Range**: VADER compound scores range from -1 (negative) to +1 (positive)

**Batch Processing:**
- **Batch Size**: 32 reviews per batch
  - **Rationale**: Balance between speed and memory usage
  - **Tuning**: 16-64 range recommended depending on available RAM
  - **Impact**: Higher = faster but more memory, lower = slower but less memory

#### 2.5.2 Theme Extraction Parameters

**TF-IDF Keyword Extraction:**
- **`ngram_range`**: (1, 2) - Unigrams and bigrams
  - **Rationale**: Captures meaningful phrases like "good app", "money transfer"
  - **Trade-off**: More features = better context but slower processing
  - **Alternative**: (1, 1) for only single words (faster but less context)

- **`max_features`**: 500
  - **Rationale**: Good balance for ~1000 reviews dataset
  - **Impact**: Higher = more diverse keywords but slower, lower = faster but may miss terms
  - **Scaling**: Adjust based on dataset size (500 for 1K reviews, 1000 for 10K+)

- **`min_df`**: 2 (minimum document frequency)
  - **Rationale**: Filter out typos and extremely rare terms
  - **Impact**: Higher = only very common terms, lower = more diverse but may include noise
  - **Tuning**: 2 ensures term appears in at least 2 reviews (noise reduction)

- **`top_n`**: 15 keywords per bank
  - **Rationale**: Sufficient for identifying key themes without overwhelming output
  - **Usage**: Top 15 TF-IDF scored keywords extracted per bank

**Theme Assignment:**
- **Method**: Rule-based keyword matching with spaCy lemmatization
- **Logic**: 
  1. Tokenize and lemmatize review text
  2. Check for theme keywords (case-insensitive)
  3. Assign all matching themes (reviews can have multiple themes)
  4. Default to "General Feedback" if no keywords match
- **Keyword Lists**: Defined in `config.py` under `NLP_SETTINGS["theme_keywords"]`
  - 7 themes with 6-7 keywords each
  - Keywords chosen based on domain knowledge and common review patterns

#### 2.5.3 Scraper Parameters

- **`min_reviews_per_bank`**: 400
  - **Rationale**: Target for statistical significance (≥400 per bank = ≥1,200 total)
  - **KPI Requirement**: ≥1,200 total reviews with <5% missing data
  - **Current Status**: 1,151 reviews collected (96% of target)

- **`batch_size`**: 200 reviews per API call
  - **Rationale**: Balance between API efficiency and memory usage
  - **Impact**: Higher = fewer API calls but more memory

- **`lang`**: "en" (English)
  - **Rationale**: Focus on English reviews for consistent analysis
  - **Filtering**: Non-English reviews (e.g., Amharic) filtered during preprocessing

- **`country`**: "et" (Ethiopia)
  - **Rationale**: Target Ethiopian banking apps specifically

#### 2.5.4 Preprocessing Parameters

- **Date Format**: YYYY-MM-DD (ISO 8601)
  - **Rationale**: Standardized format for temporal analysis
  - **Validation**: Invalid dates are dropped

- **Rating Range**: 1-5 (integers only)
  - **Rationale**: Google Play Store standard rating system
  - **Validation**: Ratings outside this range are dropped

- **Language Filtering**: Amharic/Ethiopic script detection
  - **Method**: Unicode regex pattern `[\u1200-\u137F]+`
  - **Rationale**: Focus on English reviews for consistent NLP processing
  - **Impact**: Non-English reviews filtered out during preprocessing

**All parameters are configurable via `config.py` for easy adaptation to different use cases.**

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

