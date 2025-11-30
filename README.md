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
1. **Scrape reviews**
   ```powershell
   python scripts/scrape_reviews.py
   ```
   - Fetches lightweight metadata for each configured app (title, rating, installs) and stores it under `data/raw/app_info.csv`.
   - Scrapes ≥400 reviews per bank (content, rating, dates, thumbs up, etc.) into `data/raw/reviews_raw.csv`.
   - Prints sample reviews per bank so you can quickly verify quality before moving on.

2. **Preprocess**
   ```powershell
   python scripts/preprocess_reviews.py
   ```
   - Removes duplicates, missing critical values, invalid dates, non-English content, and ratings outside 1–5.
   - Adds helper fields (`review_year`, `review_month`, `review_length`) while ensuring the deliverable columns `review`, `rating`, `date`, `bank`, `source` stay intact.
   - Outputs a KPI-focused summary (rows kept, % missing, distribution per bank) and saves the clean CSV at `data/processed/reviews_clean.csv`.

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

## KPIs
- ≥1,200 reviews total with <5% missing records post-cleaning.
- Clean CSV with normalized dates (YYYY-MM-DD), metadata columns, and English-only text.
- Sentiment labels + scores for ≥90% of reviews, with summaries per bank/rating.
- ≥3 recurring themes per bank captured via keyword-driven grouping.

