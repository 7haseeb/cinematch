"""Feature engineering for recommendation inputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.preprocessing.create_tags import build_tagged_movies


PROCESSED_DIR = Path("data/processed")


def create_final_movies(df: pd.DataFrame) -> pd.DataFrame:
    final = df[
        [
            "id",
            "title",
            "overview",
            "genres",
            "keywords",
            "cast",
            "director",
            "release_date",
            "release_year",
            "runtime",
            "vote_average",
            "vote_count",
            "popularity",
            "tags",
        ]
    ].copy()
    final = final.sort_values(["popularity", "vote_count"], ascending=False).reset_index(drop=True)
    return final


def save_final_movies(df: pd.DataFrame, output_path: Path = PROCESSED_DIR / "movies_final.csv") -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


def build_final_movies() -> pd.DataFrame:
    tagged = build_tagged_movies()
    final = create_final_movies(tagged)
    save_final_movies(final)
    return final


if __name__ == "__main__":
    output = save_final_movies(build_final_movies())
    print(f"Saved {output}")
