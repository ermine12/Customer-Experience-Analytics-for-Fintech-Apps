"""
Google Play review scraper for Ethiopian banking apps.
Collects >= min_reviews_per_bank reviews (content, rating, date, metadata)
for each configured bank and stores them as a single CSV.
"""

from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
from google_play_scraper import Sort, app, reviews
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    APP_INFO_PATH,
    BANKS,
    RAW_DATA_PATH,
    SCRAPER_SETTINGS,
)


@dataclass
class BankConfig:
    bank: str
    bank_code: str
    app_id: str


@dataclass
class AppInfo:
    bank: str
    bank_code: str
    app_id: str
    title: str
    score: float
    ratings: int
    reviews: int
    installs: str


def fetch_reviews_for_bank(
    bank: BankConfig,
    lang: str,
    country: str,
    min_reviews: int,
    batch_size: int,
) -> List[Dict]:
    """
    Fetch reviews for a single bank until min_reviews is reached or tokens exhaust.
    
    Args:
        bank: Bank configuration
        lang: Language code (e.g., "en")
        country: Country code (e.g., "et")
        min_reviews: Minimum number of reviews to collect (target: 400)
        batch_size: Number of reviews per API call
    
    Returns:
        List of review dictionaries. May be less than min_reviews if API limits reached.
    """
    all_reviews: List[Dict] = []
    continuation_token: Optional[Tuple] = None
    attempts = 0
    max_attempts = 50  # Prevent infinite loops

    with tqdm(
        total=min_reviews,
        desc=f"Fetching {bank.bank}",
        unit="reviews",
        leave=False,
    ) as progress:
        while len(all_reviews) < min_reviews and attempts < max_attempts:
            try:
                batch, continuation_token = reviews(
                    bank.app_id,
                    lang=lang,
                    country=country,
                    sort=Sort.NEWEST,
                    count=batch_size,
                    continuation_token=continuation_token,
                )

                if not batch:
                    break

                all_reviews.extend(batch)
                progress.update(len(batch))
                attempts += 1

                if continuation_token is None:
                    break
            except Exception as e:
                print(f"\nWarning: Error fetching reviews for {bank.bank}: {e}")
                break

    # Final status
    if len(all_reviews) >= min_reviews:
        progress.n = min_reviews
        progress.refresh()
    else:
        # Update progress bar to show actual count
        progress.n = len(all_reviews)
        progress.refresh()

    return all_reviews


def normalize_record(raw_record: Dict, bank: BankConfig) -> Dict:
    """Normalize google-play-scraper record into our schema."""
    review_dt: Optional[datetime] = raw_record.get("at")
    normalized = {
        "review_id": raw_record.get("reviewId"),
        "review": raw_record.get("content", "").strip(),
        "rating": raw_record.get("score"),
        "date": review_dt.date().isoformat() if isinstance(review_dt, datetime) else None,
        "bank": bank.bank,
        "bank_code": bank.bank_code,
        "source": "google_play",
        "user_name": raw_record.get("userName"),
        "thumbs_up": raw_record.get("thumbsUpCount", 0),
        "app_version": raw_record.get("appVersion"),
        "scraped_at": datetime.utcnow().isoformat(),
    }
    return normalized


def fetch_app_info(bank: BankConfig, lang: str, country: str) -> AppInfo | None:
    """Fetch summary metadata for a bank's app."""
    try:
        metadata = app(bank.app_id, lang=lang, country=country)
    except Exception as exc:  # pragma: no cover - network failures
        print(f"Warning: failed to fetch app info for {bank.bank} ({exc})")
        return None

    return AppInfo(
        bank=bank.bank,
        bank_code=bank.bank_code,
        app_id=bank.app_id,
        title=metadata.get("title", bank.bank),
        score=metadata.get("score", 0.0),
        ratings=metadata.get("ratings", 0),
        reviews=metadata.get("reviews", 0),
        installs=metadata.get("installs", ""),
    )


def load_bank_configs() -> List[BankConfig]:
    """Convert BANKS dicts into BankConfig dataclasses."""
    return [BankConfig(**bank) for bank in BANKS]


def collect_app_metadata(bank_configs: List[BankConfig], settings: Dict) -> List[AppInfo]:
    """Collect summary metadata for all banks before scraping."""
    print("\n[1/3] Fetching app metadata...")
    records: List[AppInfo] = []
    for bank in bank_configs:
        info = fetch_app_info(bank, settings["lang"], settings["country"])
        if info:
            records.append(info)
            print(
                f"- {info.title}: rating={info.score} ({info.ratings} ratings, {info.reviews} reviews)"
            )
    return records


def scrape_all_banks(
    bank_configs: List[BankConfig], settings: Dict
) -> pd.DataFrame:
    """
    Scrape all configured banks and return combined DataFrame.
    
    Ensures at least min_reviews_per_bank (default: 400) reviews per bank.
    Logs detailed statistics and KPI compliance.
    """
    normalized_records: List[Dict] = []
    stats = []
    min_target = settings["min_reviews_per_bank"]

    print("\n[2/3] Scraping Google Play reviews...")
    print(f"Target: ≥{min_target} reviews per bank")
    print("-" * 60)
    
    for bank in bank_configs:
        raw_reviews = fetch_reviews_for_bank(
            bank=bank,
            lang=settings["lang"],
            country=settings["country"],
            min_reviews=min_target,
            batch_size=settings["batch_size"],
        )
        bank_records = [normalize_record(rec, bank) for rec in raw_reviews]
        normalized_records.extend(bank_records)
        count = len(bank_records)
        stats.append((bank.bank, count))
        
        # Detailed logging per bank
        if count >= min_target:
            print(f"✓ {bank.bank:30s}: {count:,} reviews (target met)")
        else:
            print(f"⚠ {bank.bank:30s}: {count:,} reviews (target: {min_target}, shortfall: {min_target - count})")

    df = pd.DataFrame(normalized_records)
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("SCRAPING SUMMARY")
    print("=" * 60)
    print(f"Total reviews collected: {len(df):,}")
    print("\nReview counts per bank:")
    all_met_target = True
    for bank_name, count in stats:
        status = "✓" if count >= min_target else "⚠"
        print(f"  {status} {bank_name:30s}: {count:,} reviews")
        if count < min_target:
            all_met_target = False
    
    # KPI verification
    print("\n" + "-" * 60)
    if all_met_target:
        print(f"✓ KPI MET: All banks have ≥{min_target} reviews")
    else:
        print(f"⚠ KPI WARNING: Some banks have <{min_target} reviews")
    
    total_reviews = len(df)
    if total_reviews >= 1200:
        print(f"✓ KPI MET: Total reviews: {total_reviews:,} (≥1,200 required)")
    else:
        print(f"⚠ KPI WARNING: Total reviews: {total_reviews:,} (<1,200 required)")
    
    print("=" * 60 + "\n")
    return df


def save_raw_reviews(df: pd.DataFrame) -> None:
    """Persist DataFrame to CSV at RAW_DATA_PATH."""
    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_DATA_PATH, index=False)
    print(f"Saved raw reviews to {RAW_DATA_PATH}")


def save_app_info(records: List[AppInfo]) -> None:
    """Persist collected app metadata."""
    if not records:
        return
    APP_INFO_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([asdict(record) for record in records])
    df.to_csv(APP_INFO_PATH, index=False)
    print(f"Saved app metadata to {APP_INFO_PATH}")


def display_sample_reviews(df: pd.DataFrame, n: int) -> None:
    """Print sample reviews per bank for quick sanity checks."""
    if df.empty:
        return
    print("\n[3/3] Sample reviews")
    for bank_name, bank_df in df.groupby("bank"):
        print(f"\n{bank_name}")
        print("-" * len(bank_name))
        samples = bank_df.head(n)
        for _, row in samples.iterrows():
            stars = "★" * int(row.get("rating", 0))
            print(f"{stars} {row.get('date')} – {row.get('review')[:140].strip()}")


def main():
    settings = SCRAPER_SETTINGS
    bank_configs = load_bank_configs()

    app_info_records = collect_app_metadata(bank_configs, settings)
    save_app_info(app_info_records)

    df = scrape_all_banks(bank_configs, settings)
    if df.empty:
        raise RuntimeError("No reviews were fetched. Please check scraper settings.")
    save_raw_reviews(df)
    display_sample_reviews(df, settings.get("sample_reviews", 3))


if __name__ == "__main__":
    main()

