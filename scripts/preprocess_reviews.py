"""
Preprocess scraped Google Play reviews:
- remove duplicates and missing data
- normalize dates
- filter out Amharic/non-English reviews
- output clean CSV with required columns.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import PREPROCESSING_CONFIG, PROCESSED_DATA_PATH, RAW_DATA_PATH

ETHIOPIC_REGEX = re.compile(r"[\u1200-\u137F]+")


@dataclass
class PreprocessStats:
    original_count: int = 0
    after_drop_duplicates: int = 0
    after_missing: int = 0
    removed_non_english: int = 0
    final_count: int = 0
    missing_pct: Dict[str, float] = field(default_factory=dict)
    bank_counts: Dict[str, int] = field(default_factory=dict)
    rating_distribution: Dict[int, int] = field(default_factory=dict)


class ReviewPreprocessor:
    REQUIRED_COLUMNS: List[str] = PREPROCESSING_CONFIG["required_columns"]
    OPTIONAL_COLUMNS: List[str] = PREPROCESSING_CONFIG["optional_columns"]

    def __init__(self, input_path=RAW_DATA_PATH, output_path=PROCESSED_DATA_PATH):
        self.input_path = input_path
        self.output_path = output_path
        self.df: pd.DataFrame | None = None
        self.stats = PreprocessStats()

    def load(self) -> None:
        self.df = pd.read_csv(self.input_path)
        self.stats.original_count = len(self.df)
        print(f"Loaded {self.stats.original_count} reviews")

    def remove_duplicates(self) -> None:
        before = len(self.df)
        subset = ["review_id", "review", "bank"]
        subset = [col for col in subset if col in self.df.columns]
        self.df = self.df.drop_duplicates(subset=subset)
        self.stats.after_drop_duplicates = len(self.df)
        removed = before - self.stats.after_drop_duplicates
        if removed:
            print(f"Removed {removed} duplicate rows")

    def handle_missing(self) -> None:
        before = len(self.df)
        self.df = self.df.dropna(subset=["review", "rating", "bank", "date"])
        self.df["rating"] = pd.to_numeric(self.df["rating"], errors="coerce")
        self.df = self.df.dropna(subset=["rating"])
        self.df["rating"] = self.df["rating"].astype(int)
        self.stats.after_missing = len(self.df)
        removed = before - self.stats.after_missing
        if removed:
            print(f"Dropped {removed} rows with missing critical fields")

    def normalize_dates(self) -> None:
        self.df["date"] = pd.to_datetime(self.df["date"], errors="coerce")
        before = len(self.df)
        self.df = self.df.dropna(subset=["date"])
        removed = before - len(self.df)
        if removed:
            print(f"Removed {removed} rows with invalid dates")
        self.df["review_year"] = self.df["date"].dt.year
        self.df["review_month"] = self.df["date"].dt.month
        self.df["date"] = self.df["date"].dt.date.astype(str)

    def remove_non_english(self) -> None:
        def is_non_english(text: str) -> bool:
            if not isinstance(text, str):
                return True
            return bool(ETHIOPIC_REGEX.search(text))

        before = len(self.df)
        self.df = self.df[~self.df["review"].apply(is_non_english)]
        self.stats.removed_non_english = before - len(self.df)
        if self.stats.removed_non_english:
            print(f"Removed {self.stats.removed_non_english} non-English (e.g., Amharic) reviews")

    def validate_ratings(self) -> None:
        before = len(self.df)
        self.df = self.df[(self.df["rating"] >= 1) & (self.df["rating"] <= 5)]
        removed = before - len(self.df)
        if removed:
            print(f"Removed {removed} rows with invalid ratings")

    def add_text_features(self) -> None:
        """Add review length metadata for downstream analysis."""
        self.df["review"] = self.df["review"].astype(str).str.strip()
        before = len(self.df)
        self.df = self.df[self.df["review"].str.len() > 0]
        removed = before - len(self.df)
        if removed:
            print(f"Removed {removed} blank reviews after trimming whitespace")
        self.df["review_length"] = self.df["review"].str.len()

    def finalize_columns(self) -> None:
        column_order = self.REQUIRED_COLUMNS + [
            col for col in self.OPTIONAL_COLUMNS if col in self.df.columns
        ]
        available = [col for col in column_order if col in self.df.columns]
        missing = set(self.REQUIRED_COLUMNS) - set(available)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
        self.df = self.df[available]
        self.stats.final_count = len(self.df)

    def compute_missing_stats(self) -> None:
        """Compute and log detailed missing data statistics."""
        total_rows = len(self.df)
        if total_rows == 0:
            print("WARNING: No rows remaining after preprocessing!")
            return
        
        # Calculate missing percentages for all columns
        missing_counts = self.df.isna().sum()
        pct = (missing_counts / total_rows) * 100
        self.stats.missing_pct = pct.to_dict()
        
        print("\n" + "=" * 60)
        print("MISSING DATA ANALYSIS")
        print("=" * 60)
        print(f"Total rows analyzed: {total_rows:,}")
        print("\nMissing data percentages by column:")
        for col in sorted(self.df.columns):
            missing_count = missing_counts[col]
            missing_pct = pct[col]
            status = "✓" if missing_pct < 5.0 else "⚠" if missing_pct < 10.0 else "✗"
            print(f"  {status} {col:20s}: {missing_count:5d} ({missing_pct:5.2f}%)")
        
        # Check KPI requirement (<5% missing)
        worst_col = max(pct.items(), key=lambda item: item[1])
        if worst_col[1] < 5.0:
            print(f"\n✓ KPI MET: Worst missing column '{worst_col[0]}' has {worst_col[1]:.2f}% missing (<5% required)")
        else:
            print(f"\n⚠ KPI WARNING: Worst missing column '{worst_col[0]}' has {worst_col[1]:.2f}% missing (≥5% threshold)")
        
        self.stats.bank_counts = self.df["bank"].value_counts().to_dict()
        if "rating" in self.df.columns:
            self.stats.rating_distribution = (
                self.df["rating"].value_counts().sort_index().to_dict()
            )

    def generate_report(self) -> None:
        """Print a comprehensive preprocessing summary."""
        print("\n" + "=" * 60)
        print("PREPROCESSING SUMMARY")
        print("=" * 60)
        print(f"Original rows:                    {self.stats.original_count:,}")
        print(f"After removing duplicates:        {self.stats.after_drop_duplicates:,}")
        print(f"After removing missing data:      {self.stats.after_missing:,}")
        print(f"After removing non-English:       {self.stats.removed_non_english:,}")
        print(f"Final rows (clean dataset):       {self.stats.final_count:,}")
        
        # Calculate retention rate
        if self.stats.original_count > 0:
            retention = (self.stats.final_count / self.stats.original_count) * 100
            print(f"Data retention rate:              {retention:.1f}%")
        
        # Check total review count KPI
        if self.stats.final_count >= 1200:
            print(f"\n✓ KPI MET: Total reviews: {self.stats.final_count:,} (≥1,200 required)")
        else:
            print(f"\n⚠ KPI WARNING: Total reviews: {self.stats.final_count:,} (<1,200 required)")
        
        if self.stats.bank_counts:
            print("\nPer-bank review counts:")
            for bank, count in sorted(self.stats.bank_counts.items()):
                status = "✓" if count >= 400 else "⚠"
                print(f"  {status} {bank:30s}: {count:,} reviews")
        
        if self.stats.rating_distribution:
            print("\nRating distribution:")
            for rating, count in sorted(self.stats.rating_distribution.items()):
                stars = "★" * rating
                pct = (count / self.stats.final_count * 100) if self.stats.final_count > 0 else 0
                print(f"  {stars:5s} ({rating}): {count:4d} reviews ({pct:5.1f}%)")

    def verify_final_csv(self) -> None:
        """Verify the final CSV has all required columns and proper format."""
        print("\n" + "=" * 60)
        print("FINAL CSV VERIFICATION")
        print("=" * 60)
        
        # Check required columns
        missing_required = set(self.REQUIRED_COLUMNS) - set(self.df.columns)
        if missing_required:
            raise ValueError(
                f"CRITICAL: Missing required columns in final dataset: {', '.join(missing_required)}"
            )
        
        print("✓ Required columns present:")
        for col in self.REQUIRED_COLUMNS:
            if col in self.df.columns:
                non_null = self.df[col].notna().sum()
                print(f"  - {col:20s}: {non_null:,} non-null values")
        
        # Verify date format
        if "date" in self.df.columns:
            sample_dates = self.df["date"].dropna().head(5)
            if len(sample_dates) > 0:
                print(f"\n✓ Date format verification (sample):")
                for date_val in sample_dates:
                    print(f"  - {date_val}")
                # Check if dates match YYYY-MM-DD format
                date_pattern = r'^\d{4}-\d{2}-\d{2}$'
                valid_dates = self.df["date"].astype(str).str.match(date_pattern).sum()
                total_dates = self.df["date"].notna().sum()
                if valid_dates == total_dates:
                    print(f"  ✓ All {valid_dates:,} dates are in YYYY-MM-DD format")
                else:
                    print(f"  ⚠ Only {valid_dates:,}/{total_dates:,} dates match YYYY-MM-DD format")
        
        # Verify rating range
        if "rating" in self.df.columns:
            valid_ratings = self.df["rating"].between(1, 5).sum()
            total_ratings = self.df["rating"].notna().sum()
            print(f"\n✓ Rating validation:")
            print(f"  - Valid ratings (1-5): {valid_ratings:,}/{total_ratings:,}")
            if valid_ratings == total_ratings:
                print(f"  ✓ All ratings are in valid range (1-5)")
            else:
                invalid = total_ratings - valid_ratings
                print(f"  ⚠ {invalid:,} ratings outside valid range")
        
        # Verify bank distribution
        if "bank" in self.df.columns:
            bank_counts = self.df["bank"].value_counts()
            print(f"\n✓ Bank distribution:")
            for bank, count in bank_counts.items():
                print(f"  - {bank:30s}: {count:,} reviews")
            min_bank_count = bank_counts.min()
            if min_bank_count >= 400:
                print(f"\n✓ KPI MET: Minimum reviews per bank: {min_bank_count:,} (≥400 required)")
            else:
                print(f"\n⚠ KPI WARNING: Minimum reviews per bank: {min_bank_count:,} (<400 required)")
        
        # Verify source column
        if "source" in self.df.columns:
            sources = self.df["source"].value_counts()
            print(f"\n✓ Data sources:")
            for source, count in sources.items():
                print(f"  - {source:20s}: {count:,} reviews")
        
        print("\n" + "=" * 60)
    
    def save(self) -> None:
        """Save the cleaned dataset and verify output."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Verify before saving
        self.verify_final_csv()
        
        # Save to CSV
        self.df.to_csv(self.output_path, index=False)
        print(f"\n✓ Saved clean dataset to: {self.output_path}")
        print(f"  - Total rows: {len(self.df):,}")
        print(f"  - Total columns: {len(self.df.columns)}")
        print(f"  - File size: {self.output_path.stat().st_size / 1024:.1f} KB")

    def process(self) -> None:
        """Execute the complete preprocessing pipeline."""
        self.load()
        self.remove_duplicates()
        self.handle_missing()
        self.normalize_dates()
        self.remove_non_english()
        self.validate_ratings()
        self.add_text_features()
        self.finalize_columns()
        self.compute_missing_stats()
        self.save()  # This now includes verify_final_csv()
        self.generate_report()


def main():
    processor = ReviewPreprocessor()
    processor.process()


if __name__ == "__main__":
    main()

