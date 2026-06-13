"""Tag creation for content-based recommendations."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.preprocessing.clean_movies import build_cleaned_movies


PROCESSED_DIR = Path("data/processed")


def _join_tokens(value: list[str] | str) -> str:
    if isinstance(value, list):
        return " ".join(value)
    return str(value)


def _weighted_tokens(value: list[str] | str, weight: int) -> str:
    tokens = _join_tokens(value)
    return " ".join([tokens] * weight)


def create_tags(df: pd.DataFrame) -> pd.DataFrame:
    tagged = df.copy()
    tagged["overview_tokens"] = tagged["overview"].fillna("").str.lower()
    tagged["tags"] = (
        tagged["overview_tokens"]
        + " "
        + tagged["genres"].apply(lambda value: _weighted_tokens(value, 5)).str.lower()
        + " "
        + tagged["keywords"].apply(lambda value: _weighted_tokens(value, 4)).str.lower()
        + " "
        + tagged["cast"].apply(lambda value: _weighted_tokens(value, 2)).str.lower()
        + " "
        + tagged["director"].fillna("").apply(lambda value: " ".join([value] * 6)).str.lower()
        + " "
        + tagged["release_year"].fillna("")
    )
    tagged["tags"] = tagged["tags"].str.replace(r"[^a-zA-Z0-9\s]", " ", regex=True)
    tagged["tags"] = tagged["tags"].str.replace(r"\s+", " ", regex=True).str.strip()
    return tagged.drop(columns=["overview_tokens"])


def save_tagged_movies(df: pd.DataFrame, output_path: Path = PROCESSED_DIR / "movies_tags.csv") -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


def build_tagged_movies() -> pd.DataFrame:
    cleaned = build_cleaned_movies()
    tagged = create_tags(cleaned)
    save_tagged_movies(tagged)
    return tagged


if __name__ == "__main__":
    output = save_tagged_movies(build_tagged_movies())
    print(f"Saved {output}")
