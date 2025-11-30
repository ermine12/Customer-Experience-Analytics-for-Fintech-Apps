"""
Theme and keyword extraction pipeline for Task 2.

- Loads sentiment-enriched reviews.
- Cleans text with spaCy, extracts keywords via TF-IDF + token frequency.
- Applies rule-based theme tagging (3–5 per bank) and persists results.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    KEYWORD_SUMMARY_PATH,
    NLP_SETTINGS,
    SENTIMENT_DATA_PATH,
    THEME_DATA_PATH,
    THEME_SUMMARY_PATH,
)

try:
    import spacy
except ImportError as exc:  # pragma: no cover - optional dependency
    raise SystemExit(
        "spaCy is required for theme analysis. Please install it via pip."
    ) from exc


def load_model() -> "spacy.language.Language":
    try:
        return spacy.load("en_core_web_sm", exclude=["ner"])
    except OSError:
        print(
            "Warning: spaCy model 'en_core_web_sm' not found. "
            "Using a blank English pipeline (run `python -m spacy download en_core_web_sm` for better accuracy)."
        )
        return spacy.blank("en")


def preprocess_reviews(df: pd.DataFrame, nlp: "spacy.language.Language") -> pd.DataFrame:
    texts = df["review"].fillna("").astype(str).tolist()
    processed_tokens: List[List[str]] = []
    processed_strings: List[str] = []

    for text in texts:
        if not text or not text.strip():
            processed_tokens.append([])
            processed_strings.append("")
            continue
        
        doc = nlp(text)
        tokens = [
            token.lemma_.lower()
            for token in doc
            if token.is_alpha and not token.is_stop and not token.is_punct
        ]
        processed_tokens.append(tokens)
        processed_strings.append(" ".join(tokens))

    df = df.copy()
    df["tokens"] = processed_tokens
    df["clean_text"] = processed_strings
    return df


def tfidf_keywords(texts: Sequence[str], bank: str, top_n: int = 15) -> List[Tuple[str, float]]:
    # Filter out empty strings and ensure we have valid text
    texts = [text.strip() for text in texts if text and isinstance(text, str) and text.strip()]
    if not texts or not any(texts):
        return []
    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=500,
            min_df=2,
        )
        matrix = vectorizer.fit_transform(texts)
        if matrix.shape[1] == 0:  # No features extracted
            return []
        scores = matrix.sum(axis=0).A1
        feature_names = vectorizer.get_feature_names_out()
        top_indices = scores.argsort()[::-1][:top_n]
        return [(feature_names[idx], float(scores[idx])) for idx in top_indices]
    except ValueError as e:
        # Handle cases where vectorizer can't process the text
        print(f"Warning: Could not extract keywords for {bank}: {e}")
        return []


def per_review_keywords(tokens: Sequence[str], top_n: int = 5) -> List[str]:
    if not tokens:
        return []
    counts = Counter(tokens)
    return [token for token, _ in counts.most_common(top_n)]


def load_theme_rules() -> Dict[str, List[str]]:
    rules = NLP_SETTINGS["theme_keywords"]
    return {theme: [kw.lower() for kw in keywords] for theme, keywords in rules.items()}


def assign_themes(tokens: Sequence[str], theme_rules: Dict[str, List[str]]) -> List[str]:
    token_set = set(tokens)
    joined_text = " ".join(tokens)
    matched = []
    for theme, keywords in theme_rules.items():
        for keyword in keywords:
            if " " in keyword and keyword in joined_text:
                matched.append(theme)
                break
            if keyword in token_set:
                matched.append(theme)
                break
    if not matched:
        matched.append("General Feedback")
    return matched


def summarize_keywords(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for bank, group in df.groupby("bank"):
        keywords = tfidf_keywords(group["clean_text"].tolist(), bank)
        for keyword, score in keywords:
            rows.append({"bank": bank, "keyword": keyword, "tfidf_score": score})
    summary = pd.DataFrame(rows)
    if summary.empty:
        return pd.DataFrame(columns=["bank", "keyword", "tfidf_score"])
    return summary.sort_values(["bank", "tfidf_score"], ascending=[True, False])


def summarize_themes(df: pd.DataFrame) -> pd.DataFrame:
    exploded = df.explode("themes")
    summary = (
        exploded.groupby(["bank", "themes"])
        .agg(
            review_count=("review_id", "count"),
            avg_rating=("rating", "mean"),
            sample_review=("review", lambda x: x.iloc[0][:200] + "..."),
        )
        .reset_index()
        .rename(columns={"themes": "theme"})
        .sort_values(["bank", "review_count"], ascending=[True, False])
    )
    return summary


def save_outputs(df: pd.DataFrame, keyword_summary: pd.DataFrame, theme_summary: pd.DataFrame) -> None:
    THEME_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(THEME_DATA_PATH, index=False)
    keyword_summary.to_csv(KEYWORD_SUMMARY_PATH, index=False)
    theme_summary.to_csv(THEME_SUMMARY_PATH, index=False)
    print(f"Saved themed reviews to {THEME_DATA_PATH}")
    print(f"Saved keyword summary to {KEYWORD_SUMMARY_PATH}")
    print(f"Saved theme summary to {THEME_SUMMARY_PATH}")


def main() -> None:
    print("Loading sentiment-enriched reviews...")
    df = pd.read_csv(SENTIMENT_DATA_PATH)
    if "review_id" not in df.columns:
        df["review_id"] = df.index.astype(str)
    df["review"] = df["review"].fillna("")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["rating"] = df["rating"].fillna(df["rating"].median()).astype(float)
    if "tokens" in df.columns:
        df = df.drop(columns=["tokens"])

    nlp = load_model()
    df = preprocess_reviews(df, nlp)

    theme_rules = load_theme_rules()
    df["keywords"] = df["tokens"].apply(per_review_keywords)
    df["themes"] = df["tokens"].apply(lambda toks: assign_themes(toks, theme_rules))

    df["keywords"] = df["keywords"].apply(lambda kws: "|".join(kws))
    df["themes"] = df["themes"].apply(lambda themes: "|".join(sorted(set(themes))))

    keyword_summary = summarize_keywords(df)
    theme_summary = summarize_themes(
        df.assign(themes=df["themes"].str.split("|"))
    )

    save_outputs(df, keyword_summary, theme_summary)

    print("Top themes preview:")
    # Use to_string() with proper encoding to handle Unicode characters
    try:
        print(theme_summary.head().to_string())
    except UnicodeEncodeError:
        # Fallback: print without problematic columns
        preview = theme_summary.head().copy()
        if 'sample_review' in preview.columns:
            preview['sample_review'] = preview['sample_review'].str.encode('ascii', 'ignore').str.decode('ascii')
        print(preview.to_string())


if __name__ == "__main__":
    main()

