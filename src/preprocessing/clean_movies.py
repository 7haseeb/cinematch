"""Raw TMDB movie dataset cleaning."""

from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd


RAW_MOVIES = Path("data/raw/tmdb_5000_movies.csv")
RAW_CREDITS = Path("data/raw/tmdb_5000_credits.csv")
PROCESSED_DIR = Path("data/processed")


def parse_list(value: str, key: str = "name", limit: int | None = None) -> list[str]:
    """Parse TMDB JSON-ish CSV cells into normalized string lists."""
    if pd.isna(value):
        return []
    try:
        items = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return []

    results = [str(item.get(key, "")).strip() for item in items if item.get(key)]
    results = [item.replace(" ", "") for item in results if item]
    return results[:limit] if limit else results


def parse_director(value: str) -> str:
    if pd.isna(value):
        return ""
    try:
        crew = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return ""

    for person in crew:
        if person.get("job") == "Director":
            return str(person.get("name", "")).replace(" ", "")
    return ""


def load_raw_movies(
    movies_path: Path = RAW_MOVIES,
    credits_path: Path = RAW_CREDITS,
) -> pd.DataFrame:
    movies = pd.read_csv(movies_path)
    credits = pd.read_csv(credits_path)
    return movies.merge(credits, left_on="id", right_on="movie_id", suffixes=("", "_credits"))


def clean_movies(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "id",
        "title",
        "overview",
        "genres",
        "keywords",
        "cast",
        "crew",
        "release_date",
        "runtime",
        "vote_average",
        "vote_count",
        "popularity",
    ]
    cleaned = df[columns].copy()
    cleaned = cleaned.dropna(subset=["overview", "title"])
    cleaned["release_year"] = cleaned["release_date"].fillna("").str[:4]
    cleaned["genres"] = cleaned["genres"].apply(parse_list)
    cleaned["keywords"] = cleaned["keywords"].apply(lambda value: parse_list(value, limit=12))
    cleaned["cast"] = cleaned["cast"].apply(lambda value: parse_list(value, limit=5))
    cleaned["director"] = cleaned["crew"].apply(parse_director)
    cleaned = cleaned.drop(columns=["crew"])
    cleaned = cleaned.drop_duplicates(subset=["id"])
    return cleaned.reset_index(drop=True)


def save_cleaned_movies(df: pd.DataFrame, output_path: Path = PROCESSED_DIR / "movies_cleaned.csv") -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


def build_cleaned_movies() -> pd.DataFrame:
    cleaned = clean_movies(load_raw_movies())
    save_cleaned_movies(cleaned)
    return cleaned


if __name__ == "__main__":
    output = save_cleaned_movies(build_cleaned_movies())
    print(f"Saved {output}")
