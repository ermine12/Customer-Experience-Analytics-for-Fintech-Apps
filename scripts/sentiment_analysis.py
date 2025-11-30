"""
Sentiment analysis pipeline for Task 2.

- Loads the cleaned reviews dataset.
- Scores every review using DistilBERT sentiment (falls back to VADER if HF
  dependencies are unavailable) and derives positive/negative/neutral labels.
- Aggregates sentiment by bank and star rating.
- Persists enriched review data and summary CSVs for downstream analysis.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import pandas as pd
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    NLP_SETTINGS,
    PROCESSED_DATA_PATH,
    SENTIMENT_DATA_PATH,
    SENTIMENT_SUMMARY_PATH,
)

try:
    from transformers import pipeline as hf_pipeline
except Exception:  # pragma: no cover - missing optional dep handled in runtime
    hf_pipeline = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except Exception:  # pragma: no cover - missing optional dep handled in runtime
    SentimentIntensityAnalyzer = None


@dataclass
class SentimentResult:
    label: str
    score: float
    engine: str


class SentimentEngine:
    """Wrapper that prefers Hugging Face transformers and falls back to VADER."""

    def __init__(self, settings: dict):
        self.model_name = settings["hf_model_name"]
        self.neutral_threshold = settings["neutral_threshold"]
        self.vader_neutral_threshold = settings["vader_neutral_threshold"]
        self.batch_size = settings["batch_size"]

        self._hf = None
        self._vader = None
        self.engine_name = ""
        self._build()

    def _build(self) -> None:
        if hf_pipeline is not None:
            try:
                self._hf = hf_pipeline(
                    "sentiment-analysis",
                    model=self.model_name,
                    truncation=True,
                )
                self.engine_name = f"hf:{self.model_name}"
                return
            except Exception as exc:  # pragma: no cover - network failures
                print(
                    f"Warning: could not load Hugging Face pipeline ({exc}). "
                    "Falling back to VADER."
                )
                self._hf = None

        if SentimentIntensityAnalyzer is None:
            raise RuntimeError(
                "No sentiment engine available. Please install transformers or vaderSentiment."
            )

        self._vader = SentimentIntensityAnalyzer()
        self.engine_name = "vader"

    def analyze(self, texts: Sequence[str]) -> List[SentimentResult]:
        if not texts:
            return []
        if self._hf:
            return self._analyze_with_hf(texts)
        return self._analyze_with_vader(texts)

    def _analyze_with_hf(self, texts: Sequence[str]) -> List[SentimentResult]:
        results: List[SentimentResult] = []
        total = len(texts)
        for start in range(0, total, self.batch_size):
            batch = list(texts[start : start + self.batch_size])
            predictions = self._hf(batch)
            for label_info in predictions:
                label = label_info["label"].upper()
                score = float(label_info.get("score", 0.0))
                normalized_label = self._normalize_label(label, score)
                results.append(
                    SentimentResult(
                        label=normalized_label,
                        score=score,
                        engine=self.engine_name,
                    )
                )
        return results

    def _normalize_label(self, label: str, score: float) -> str:
        if score < self.neutral_threshold:
            return "neutral"
        return "positive" if label == "POSITIVE" else "negative"

    def _analyze_with_vader(self, texts: Sequence[str]) -> List[SentimentResult]:
        results: List[SentimentResult] = []
        for text in texts:
            text = text or ""
            polarity = self._vader.polarity_scores(text)
            compound = float(polarity["compound"])
            label = self._normalize_vader(compound)
            score = abs(compound)
            results.append(
                SentimentResult(label=label, score=score, engine=self.engine_name)
            )
        return results

    def _normalize_vader(self, compound: float) -> str:
        if compound >= self.vader_neutral_threshold:
            return "positive"
        if compound <= -self.vader_neutral_threshold:
            return "negative"
        return "neutral"


def load_reviews() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DATA_PATH)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").astype(int)
    df["review"] = df["review"].fillna("")
    if "review_id" not in df.columns:
        df["review_id"] = df.index.astype(str)
    return df


def attach_sentiment(df: pd.DataFrame, engine: SentimentEngine) -> pd.DataFrame:
    texts = df["review"].tolist()
    results = []
    chunk_size = 1000
    for start in tqdm(
        range(0, len(texts), chunk_size),
        desc=f"Scoring sentiment ({engine.engine_name})",
        unit="reviews",
    ):
        chunk = texts[start : start + chunk_size]
        results.extend(engine.analyze(chunk))

    if len(results) != len(df):
        raise RuntimeError("Sentiment result count does not match input rows.")

    df = df.copy()
    df["sentiment_label"] = [res.label for res in results]
    df["sentiment_score"] = [res.score for res in results]
    df["sentiment_source"] = engine.engine_name
    return df


def aggregate_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["bank", "rating"])
        .agg(
            reviews=("review_id", "count"),
            positive_pct=("sentiment_label", lambda x: (x == "positive").mean() * 100),
            neutral_pct=("sentiment_label", lambda x: (x == "neutral").mean() * 100),
            negative_pct=("sentiment_label", lambda x: (x == "negative").mean() * 100),
            mean_score=("sentiment_score", "mean"),
        )
        .reset_index()
        .sort_values(["bank", "rating"])
    )
    return summary


def save_outputs(df: pd.DataFrame, summary: pd.DataFrame) -> None:
    SENTIMENT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SENTIMENT_DATA_PATH, index=False)
    summary.to_csv(SENTIMENT_SUMMARY_PATH, index=False)
    print(f"Saved enriched reviews to {SENTIMENT_DATA_PATH}")
    print(f"Saved sentiment summary to {SENTIMENT_SUMMARY_PATH}")


def main() -> None:
    print("Loading cleaned reviews...")
    df = load_reviews()
    print(f"Loaded {len(df):,} reviews for sentiment scoring.")

    engine = SentimentEngine(NLP_SETTINGS)
    enriched = attach_sentiment(df, engine)

    coverage = len(enriched[enriched["sentiment_label"].notna()]) / len(enriched)
    print(f"Sentiment coverage: {coverage * 100:.2f}%")

    summary = aggregate_sentiment(enriched)
    print("Preview of aggregated sentiment (top 5 rows):")
    print(summary.head())

    save_outputs(enriched, summary)


if __name__ == "__main__":
    main()

