# Customer Experience Analytics for Fintech Apps

Task 1 focuses on building a reproducible pipeline that gathers and cleans Google Play Store reviews for Ethiopian banking apps.

## Project Structure
- `scripts/scrape_reviews.py` – collects reviews from Google Play.
- `scripts/preprocess_reviews.py` – cleans data, filters languages, exports analysis-ready CSV.
- `scripts/sentiment_analysis.py` – scores sentiment for all reviews (Task 2).
- `scripts/theme_analysis.py` – extracts keywords and assigns themes (Task 2).
- `notebooks/preprocessing_eda.ipynb` – EDA for preprocessed reviews (Task 2).
- `notebooks/sentiment_eda.ipynb` – EDA for sentiment analysis results (Task 2).
- `notebooks/theme_eda.ipynb` – EDA for theme and keyword analysis (Task 2).
- `data/raw/` – intermediate scraped data (ignored by git).
- `data/processed/` – cleaned outputs (ignored by git).
- `config.py` – central configuration for file paths and bank metadata.

## Setup
```powershell
cd "Customer Experience Analytics for Fintech Apps"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Git workflow
```powershell
git init
git remote add origin <your_repo_url>
git checkout -b task-1
```
Commit after every logical milestone (e.g., scraper finished, preprocessing finished, README updated) with descriptive messages. Push the `task-1` branch for review.

## Usage

### Quick Start: End-to-End Pipeline

Run the complete pipeline in one command:

```powershell
python scripts/run_pipeline.py
```

This executes all steps sequentially:
1. Scrape reviews from Google Play Store
2. Preprocess and clean data
3. Perform sentiment analysis
4. Extract themes and keywords

**Skip specific steps** (if you already have intermediate data):

```powershell
# Skip scraping, use existing raw data
python scripts/run_pipeline.py --skip-scrape

# Skip preprocessing, use existing clean data
python scripts/run_pipeline.py --skip-preprocess

# Skip sentiment analysis
python scripts/run_pipeline.py --skip-sentiment

# Skip theme analysis
python scripts/run_pipeline.py --skip-themes

# Combine flags
python scripts/run_pipeline.py --skip-scrape --skip-preprocess
```

**Logs**: Pipeline execution logs are saved to `pipeline.log` in the project root.

---

### Individual Script Usage

#### 1. **Scrape Reviews** (`scripts/scrape_reviews.py`)

Scrapes reviews from Google Play Store for all configured banks.

```powershell
python scripts/scrape_reviews.py
```

**What it does:**
- Fetches app metadata (title, rating, installs) for each bank
- Scrapes ≥400 reviews per bank (configurable in `config.py`)
- Collects: review content, ratings, dates, user info, thumbs-up counts
- Saves to `data/raw/reviews_raw.csv` and `data/raw/app_info.csv`
- Displays sample reviews per bank for verification

**Configuration:**
Edit `config.py` to modify:
- `SCRAPER_SETTINGS["min_reviews_per_bank"]`: Target reviews per bank (default: 400)
- `SCRAPER_SETTINGS["batch_size"]`: Reviews per API call (default: 200)
- `BANKS`: Add/modify bank configurations

**Example Output:**
```
[1/3] Fetching app metadata...
- Dashen Bank Super App: rating=4.2 (1250 ratings, 850 reviews)
[2/3] Scraping Google Play reviews...
Fetching Dashen Bank: 100%|████████| 400/400 [00:45<00:00]
Review counts per bank:
  Dashen Bank: 400
  Bank of Abyssinia: 384
  Commercial Bank of Ethiopia: 382
Total reviews: 1,166
```

---

#### 2. **Preprocess Data** (`scripts/preprocess_reviews.py`)

Cleans and normalizes scraped review data.

```powershell
python scripts/preprocess_reviews.py
```

**What it does:**
- Removes duplicate reviews
- Filters out missing critical values (review, rating, date, bank)
- Normalizes dates to YYYY-MM-DD format
- Removes non-English reviews (Amharic/Ethiopic script detection)
- Validates ratings (1-5 range only)
- Adds helper fields: `review_year`, `review_month`, `review_length`
- Saves clean CSV to `data/processed/reviews_clean.csv`

**Required Output Columns:**
- `review`: Review text content
- `rating`: Star rating (1-5)
- `date`: Review date (YYYY-MM-DD)
- `bank`: Bank name
- `source`: Data source (e.g., "google_play")

**Example Output:**
```
Loaded 1,166 reviews
Removed 5 duplicate rows
Dropped 8 rows with missing critical fields
Removed 2 rows with invalid dates
Removed 0 non-English (e.g., Amharic) reviews
Preprocessing summary
---------------------
Original rows: 1,166
After duplicates: 1,161
After missing filters: 1,153
Removed non-English: 0
Final rows: 1,151
Missing percentages after cleaning:
  review: 0.00%
  rating: 0.00%
  date: 0.00%
  bank: 0.00%
Per-bank counts:
  Dashen Bank: 385
  Bank of Abyssinia: 384
  Commercial Bank of Ethiopia: 382
```

---

#### 3. **Sentiment Analysis** (`scripts/sentiment_analysis.py`)

Performs sentiment scoring on cleaned reviews.

```powershell
python scripts/sentiment_analysis.py
```

**What it does:**
- Loads cleaned reviews from `data/processed/reviews_clean.csv`
- Scores sentiment using DistilBERT (falls back to VADER if unavailable)
- Classifies as: positive, neutral, or negative
- Generates sentiment scores (0.0 to 1.0)
- Aggregates statistics by bank and rating
- Saves to:
  - `data/processed/reviews_with_sentiment.csv` (enriched reviews)
  - `data/processed/sentiment_summary.csv` (aggregated stats)

**Configuration:**
Edit `config.py` → `NLP_SETTINGS`:
- `neutral_threshold`: 0.6 (confidence threshold for neutral classification)
- `vader_neutral_threshold`: 0.05 (VADER neutral zone)
- `batch_size`: 32 (reviews per batch)

**Example Output:**
```
Loading cleaned reviews...
Loaded 1,151 reviews for sentiment scoring.
Scoring sentiment (vader): 100%|████████| 2/2 [00:05<00:00]
Sentiment coverage: 100.00%
Preview of aggregated sentiment (top 5 rows):
                       bank  rating  reviews  positive_pct  neutral_pct  negative_pct  mean_score
          Bank of Abyssinia       1      125     21.600000    28.000000     50.400000    0.376460
          Bank of Abyssinia       2       14     42.857143    42.857143     14.285714    0.262793
...
```

---

#### 4. **Theme Analysis** (`scripts/theme_analysis.py`)

Extracts keywords and assigns themes to reviews.

```powershell
python scripts/theme_analysis.py
```

**What it does:**
- Loads sentiment-enriched reviews
- Preprocesses text with spaCy (tokenization, lemmatization)
- Extracts top keywords per bank using TF-IDF
- Assigns themes based on keyword matching
- Generates summaries with sample reviews
- Saves to:
  - `data/processed/reviews_with_themes.csv` (themed reviews)
  - `data/processed/keywords_per_bank.csv` (TF-IDF keywords)
  - `data/processed/theme_summary.csv` (theme statistics)

**Configuration:**
- **TF-IDF Parameters** (in `scripts/theme_analysis.py`):
  - `ngram_range=(1, 2)`: Extract unigrams and bigrams
  - `max_features=500`: Maximum vocabulary size
  - `min_df=2`: Minimum document frequency
  - `top_n=15`: Top keywords per bank
- **Theme Keywords**: Defined in `config.py` → `NLP_SETTINGS["theme_keywords"]`

**Example Output:**
```
Loading sentiment-enriched reviews...
Top themes preview:
                       bank                    theme  review_count  avg_rating
          Bank of Abyssinia        General Feedback           303        3.75
          Bank of Abyssinia  Performance & Reliability            31        1.32
...
```

---

### Configuration via `config.py`

All settings are centralized in `config.py` for easy customization:

**Add a new bank:**
```python
BANKS.append({
    "bank": "New Bank Name",
    "bank_code": "newbank",
    "app_id": "com.newbank.app",
})
```

**Modify scraper settings:**
```python
SCRAPER_SETTINGS["min_reviews_per_bank"] = 500  # Collect more reviews
SCRAPER_SETTINGS["batch_size"] = 300  # Larger batches
```

**Adjust sentiment thresholds:**
```python
NLP_SETTINGS["neutral_threshold"] = 0.7  # More conservative
NLP_SETTINGS["vader_neutral_threshold"] = 0.1  # Wider neutral zone
```

**Add/modify themes:**
```python
NLP_SETTINGS["theme_keywords"]["New Theme"] = ["keyword1", "keyword2", ...]
```

See `config.py` for detailed parameter documentation and explanations.

## Task 2: Sentiment & Themes

Install the additional NLP dependencies (plus the spaCy English model once):
```powershell
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

1. **Sentiment scoring**
   ```powershell
   python scripts/sentiment_analysis.py
   ```
   - Uses `distilbert-base-uncased-finetuned-sst-2-english` for positive/negative scoring (automatic VADER fallback if transformers/torch are unavailable).
   - Derives a neutral class for low-confidence predictions and aggregates sentiment by bank + rating.
   - Saves enriched reviews to `data/processed/reviews_with_sentiment.csv` and summary stats to `data/processed/sentiment_summary.csv`.

2. **Keyword & thematic analysis**
   ```powershell
   python scripts/theme_analysis.py
   ```
   - Cleans text with spaCy, extracts high-weight keywords per bank via TF-IDF, and assigns rule-based themes (Access/Login, Reliability, Transactions, UX, Support, Features, plus a General fallback).
   - Exports:
     - `data/processed/reviews_with_themes.csv` (keywords + themes per review),
     - `data/processed/keywords_per_bank.csv` (top TF-IDF terms),
     - `data/processed/theme_summary.csv` (theme counts, average ratings, exemplar review per bank).

3. **Exploratory Data Analysis (EDA)**
   
   Three separate EDA notebooks for focused analysis:
   
   **Preprocessing EDA:**
   ```powershell
   jupyter notebook notebooks/preprocessing_eda.ipynb
   ```
   - Dataset overview and quality metrics
   - Reviews distribution by bank
   - Rating distribution analysis
   - Temporal trends (if available)
   
   **Sentiment EDA:**
   ```powershell
   jupyter notebook notebooks/sentiment_eda.ipynb
   ```
   - Overall sentiment distribution
   - Sentiment by bank and rating
   - Sentiment score distributions
   - Correlation between ratings and sentiment
   
   **Theme EDA:**
   ```powershell
   jupyter notebook notebooks/theme_eda.ipynb
   ```
   - Theme frequency and distribution
   - Keywords per bank (TF-IDF scores)
   - Theme-sentiment correlations
   - Sample reviews by theme
   
   All notebooks include visualizations (bar charts, heatmaps, time series) and summary statistics.

## Banks Covered
- Dashen Bank – `com.dashen.dashensuperapp`
- Bank of Abyssinia – `com.boa.boaMobileBanking`
- Commercial Bank of Ethiopia – `com.combanketh.mobilebanking`

## Task 3: PostgreSQL Database

### Database Setup

**Choose your setup method:**

#### Option A: Docker (Recommended - No Installation Needed!) 🐳

**Best for:** Quick setup, no system installation, easy cleanup

1. **Install Docker Desktop:**
   - Download from: https://www.docker.com/products/docker-desktop/
   - Install and start Docker Desktop

2. **Start PostgreSQL:**
   ```powershell
   docker-compose up -d
   ```
   PostgreSQL is now running in a container!

3. **Set password in `.env` file:**
   - Edit `.env` and set `POSTGRES_PASSWORD=postgres` (or match docker-compose.yml)

4. **See `DOCKER_SETUP.md` for detailed Docker instructions.**

#### Option B: Local PostgreSQL Installation

1. **Install PostgreSQL** (if not already installed)
   - Download from: https://www.postgresql.org/download/
   - Windows: Use the installer and remember your postgres user password

2. **Set Database Password**
   ```powershell
   # Option 1: Environment variable (recommended)
   set POSTGRES_PASSWORD=your_password
   
   # Option 2: Edit database_config.py
   # Uncomment and set: DB_CONFIG['password'] = 'your_password'
   ```

3. **Create Database and Tables**
   ```powershell
   python scripts/setup_database.py
   ```
   This will:
   - Create the `bank_reviews` database
   - Create all required tables with proper schema
   - Set up indexes and foreign key relationships
   - Verify table creation

4. **Load Data into Database**
   ```powershell
   python scripts/load_data.py
   ```
   This will:
   - Insert bank information from config
   - Load reviews from processed CSV files
   - Insert reviews with proper foreign key relationships
   - Handle duplicates automatically
   - Verify data integrity with SQL queries
   - Display loading statistics

### Database Schema

The `bank_reviews` database contains the following tables:

#### 1. `banks` Table
Stores information about the banks being analyzed.

| Column | Type | Description |
|--------|------|-------------|
| `bank_id` | SERIAL PRIMARY KEY | Auto-incrementing unique identifier |
| `bank_name` | VARCHAR(100) NOT NULL UNIQUE | Full bank name (e.g., "Dashen Bank") |
| `app_name` | VARCHAR(200) | Name of the mobile banking app |
| `bank_code` | VARCHAR(50) | Short identifier (e.g., "dashen") |
| `app_id` | VARCHAR(200) | Google Play Store app package ID |
| `created_at` | TIMESTAMP | Timestamp when record was created |

#### 2. `reviews` Table
Stores the scraped and processed review data.

| Column | Type | Description |
|--------|------|-------------|
| `review_id` | VARCHAR(200) PRIMARY KEY | Unique identifier from source |
| `bank_id` | INTEGER NOT NULL | Foreign key to `banks.bank_id` |
| `review_text` | TEXT NOT NULL | Full text content of the review |
| `rating` | INTEGER NOT NULL | Star rating (1-5, CHECK constraint) |
| `review_date` | DATE NOT NULL | Date when review was posted |
| `review_year` | INTEGER | Extracted year from `review_date` |
| `review_month` | INTEGER | Extracted month from `review_date` |
| `review_length` | INTEGER | Character count of review text |
| `sentiment_label` | VARCHAR(20) | Sentiment: "positive", "neutral", or "negative" |
| `sentiment_score` | DECIMAL(5, 3) | Sentiment score (0.0 to 1.0) |
| `sentiment_source` | VARCHAR(50) | Source of sentiment (e.g., "distilbert", "vader") |
| `source` | VARCHAR(50) | Data source (default: "google_play") |
| `user_name` | VARCHAR(200) | Name of the reviewer |
| `thumbs_up` | INTEGER | Number of helpful votes (default: 0) |
| `scraped_at` | TIMESTAMP | When review was scraped |
| `created_at` | TIMESTAMP | When record was created |
| `updated_at` | TIMESTAMP | When record was last updated |

**Foreign Key:** `bank_id` → `banks.bank_id` (ON DELETE CASCADE)

**Indexes:**
- `idx_reviews_bank_id` on `bank_id`
- `idx_reviews_rating` on `rating`
- `idx_reviews_date` on `review_date`
- `idx_reviews_sentiment` on `sentiment_label`
- `idx_reviews_year` on `review_year`
- `idx_reviews_month` on `review_month`

#### 3. `themes` Table
Stores theme assignments for reviews (many-to-many relationship).

| Column | Type | Description |
|--------|------|-------------|
| `theme_id` | SERIAL PRIMARY KEY | Auto-incrementing unique identifier |
| `review_id` | VARCHAR(200) NOT NULL | Foreign key to `reviews.review_id` |
| `theme_name` | VARCHAR(100) NOT NULL | Theme name (e.g., "Performance & Reliability") |
| `created_at` | TIMESTAMP | When record was created |

**Foreign Key:** `review_id` → `reviews.review_id` (ON DELETE CASCADE)

**Unique Constraint:** (`review_id`, `theme_name`) - prevents duplicate theme assignments

#### 4. `keywords` Table
Stores keywords extracted from reviews via TF-IDF.

| Column | Type | Description |
|--------|------|-------------|
| `keyword_id` | SERIAL PRIMARY KEY | Auto-incrementing unique identifier |
| `review_id` | VARCHAR(200) NOT NULL | Foreign key to `reviews.review_id` |
| `keyword` | VARCHAR(200) NOT NULL | Extracted keyword or phrase |
| `created_at` | TIMESTAMP | When record was created |

**Foreign Key:** `review_id` → `reviews.review_id` (ON DELETE CASCADE)

**Unique Constraint:** (`review_id`, `keyword`) - prevents duplicate keywords

#### 5. `sentiment_summary` Table
Stores aggregated sentiment statistics by bank and rating.

| Column | Type | Description |
|--------|------|-------------|
| `summary_id` | SERIAL PRIMARY KEY | Auto-incrementing unique identifier |
| `bank_id` | INTEGER NOT NULL | Foreign key to `banks.bank_id` |
| `rating` | INTEGER NOT NULL | Star rating (1-5, CHECK constraint) |
| `review_count` | INTEGER NOT NULL | Number of reviews in this category |
| `positive_pct` | DECIMAL(5, 2) | Percentage of positive reviews |
| `neutral_pct` | DECIMAL(5, 2) | Percentage of neutral reviews |
| `negative_pct` | DECIMAL(5, 2) | Percentage of negative reviews |
| `mean_score` | DECIMAL(5, 3) | Average sentiment score |
| `created_at` | TIMESTAMP | When record was created |
| `updated_at` | TIMESTAMP | When record was last updated |

**Foreign Key:** `bank_id` → `banks.bank_id` (ON DELETE CASCADE)

**Unique Constraint:** (`bank_id`, `rating`) - one summary per bank-rating combination

#### 6. `theme_summary` Table
Stores aggregated theme statistics by bank.

| Column | Type | Description |
|--------|------|-------------|
| `theme_summary_id` | SERIAL PRIMARY KEY | Auto-incrementing unique identifier |
| `bank_id` | INTEGER NOT NULL | Foreign key to `banks.bank_id` |
| `theme_name` | VARCHAR(100) NOT NULL | Name of the theme |
| `review_count` | INTEGER NOT NULL | Number of reviews with this theme |
| `avg_rating` | DECIMAL(3, 2) | Average rating for reviews with this theme |
| `sample_review` | TEXT | Example review text for this theme |
| `created_at` | TIMESTAMP | When record was created |
| `updated_at` | TIMESTAMP | When record was last updated |

**Foreign Key:** `bank_id` → `banks.bank_id` (ON DELETE CASCADE)

**Unique Constraint:** (`bank_id`, `theme_name`) - one summary per bank-theme combination

### SQL Verification Queries

Run verification queries to check data integrity:

```powershell
# Using psql command line
psql -U postgres -d bank_reviews -f scripts/verify_data.sql

# Or connect via pgAdmin and run queries from scripts/verify_data.sql
```

The verification script includes queries for:
- Total review counts
- Reviews per bank
- Average ratings per bank
- Rating distribution
- Sentiment distribution
- Temporal analysis (reviews by year/month)
- Data quality checks
- Foreign key integrity

### Schema Files

- **`database_schema.sql`**: Complete SQL schema definition (can be used to recreate database)
- **`scripts/verify_data.sql`**: SQL queries for data verification and reporting

### Database Connection

Connection settings are configured in `database_config.py`:
- **Host**: localhost (default)
- **Port**: 5432 (default)
- **Database**: bank_reviews
- **User**: postgres (default)
- **Password**: Set via environment variable or in config file

## KPIs
- ≥1,200 reviews total with <5% missing records post-cleaning.
- Clean CSV with normalized dates (YYYY-MM-DD), metadata columns, and English-only text.
- Sentiment labels + scores for ≥90% of reviews, with summaries per bank/rating.
- ≥3 recurring themes per bank captured via keyword-driven grouping.
- **PostgreSQL database with >1,000 review entries** (Task 3 KPI).
- **Working database connection + insert script** (Task 3 KPI).
- **SQL dump/schema file committed to repository** (Task 3 KPI).

