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
        pct = (self.df.isna().sum() / len(self.df)) * 100
        self.stats.missing_pct = pct.to_dict()
        print("Missing percentages after cleaning:")
        for col, val in pct.items():
            print(f"  {col}: {val:.2f}%")
        self.stats.bank_counts = self.df["bank"].value_counts().to_dict()
        if "rating" in self.df.columns:
            self.stats.rating_distribution = (
                self.df["rating"].value_counts().sort_index().to_dict()
            )

    def generate_report(self) -> None:
        """Print a concise preprocessing summary for the console log."""
        print("\nPreprocessing summary")
        print("---------------------")
        print(f"Original rows: {self.stats.original_count}")
        print(f"After duplicates: {self.stats.after_drop_duplicates}")
        print(f"After missing filters: {self.stats.after_missing}")
        print(f"Removed non-English: {self.stats.removed_non_english}")
        print(f"Final rows: {self.stats.final_count}")

        missing_pct = self.stats.missing_pct
        if missing_pct:
            worst_col = max(missing_pct.items(), key=lambda item: item[1])
            print(
                f"Worst missing column: {worst_col[0]} ({worst_col[1]:.2f}%)"
            )
        if self.stats.bank_counts:
            print("Per-bank counts:")
            for bank, count in self.stats.bank_counts.items():
                print(f"  {bank}: {count}")
        if self.stats.rating_distribution:
            print("Rating distribution:")
            for rating, count in sorted(self.stats.rating_distribution.items()):
                print(f"  {rating}★: {count}")

    def save(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(self.output_path, index=False)
        print(f"Saved clean dataset to {self.output_path}")

    def process(self) -> None:
        self.load()
        self.remove_duplicates()
        self.handle_missing()
        self.normalize_dates()
        self.remove_non_english()
        self.validate_ratings()
        self.add_text_features()
        self.finalize_columns()
        self.compute_missing_stats()
        self.save()
        self.generate_report()


def main():
    processor = ReviewPreprocessor()
    processor.process()


if __name__ == "__main__":
    main()

