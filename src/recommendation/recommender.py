"""Recommendation engine orchestration."""

from __future__ import annotations

import pickle
import re
from difflib import get_close_matches
from math import log10
from pathlib import Path

import pandas as pd

from src.preprocessing.feature_engineering import build_final_movies
from src.recommendation.similarity import build_similarity


MODELS_DIR = Path("models")
PROCESSED_DIR = Path("data/processed")
MOVIES_PKL = MODELS_DIR / "movies.pkl"
SIMILARITY_PKL = MODELS_DIR / "similarity.pkl"
VECTORIZER_PKL = MODELS_DIR / "vectorizer.pkl"
MOVIES_FINAL_CSV = PROCESSED_DIR / "movies_final.csv"


def _read_pickle(path: Path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def _write_pickle(value, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(value, handle, protocol=pickle.HIGHEST_PROTOCOL)


def build_recommendation_artifacts() -> pd.DataFrame:
    movies = build_final_movies()
    vectorizer, similarity = build_similarity(movies["tags"].fillna("").tolist())

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    _write_pickle(movies, MOVIES_PKL)
    _write_pickle(similarity, SIMILARITY_PKL)
    _write_pickle(vectorizer, VECTORIZER_PKL)
    movies.to_csv(MOVIES_FINAL_CSV, index=False)
    return movies


def artifacts_available() -> bool:
    return MOVIES_PKL.exists() and SIMILARITY_PKL.exists() and VECTORIZER_PKL.exists()


def _as_set(value) -> set[str]:
    if isinstance(value, list):
        return {str(item).lower() for item in value if item}
    if pd.isna(value):
        return set()
    text = str(value)
    if text.startswith("[") and text.endswith("]"):
        try:
            import ast

            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                return {str(item).lower() for item in parsed if item}
        except (ValueError, SyntaxError):
            pass
    return {item.lower() for item in text.split() if item}


def _overlap(left, right) -> float:
    left_set = _as_set(left)
    right_set = _as_set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def _humanize_token(token: str) -> str:
    replacements = {
        "sciencefiction": "Science Fiction",
        "dccomics": "DC Comics",
        "spacecolony": "Space Colony",
        "spacetravel": "Space Travel",
        "crimefighter": "Crime Fighter",
        "fathersonrelationship": "Father Son Relationship",
        "artificialintelligence": "Artificial Intelligence",
        "organizedcrime": "Organized Crime",
    }
    if token.lower() in replacements:
        return replacements[token.lower()]
    token = re.sub(r"[^A-Za-z0-9]+", " ", token)
    token = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", token)
    return token.strip().title()


def _match_reasons(seed: pd.Series, candidate: pd.Series) -> list[str]:
    reasons = []
    shared_genres = sorted(_as_set(seed.get("genres")) & _as_set(candidate.get("genres")))
    shared_keywords = sorted(_as_set(seed.get("keywords")) & _as_set(candidate.get("keywords")))
    shared_cast = sorted(_as_set(seed.get("cast")) & _as_set(candidate.get("cast")))

    if shared_genres:
        reasons.append("Genres: " + ", ".join(_humanize_token(item) for item in shared_genres[:3]))
    if seed.get("director") and seed.get("director") == candidate.get("director"):
        reasons.append(f"Director: {_humanize_token(str(seed.get('director')))}")
    if shared_keywords:
        reasons.append("Themes: " + ", ".join(_humanize_token(item) for item in shared_keywords[:3]))
    if shared_cast:
        reasons.append("Cast: " + ", ".join(_humanize_token(item) for item in shared_cast[:2]))
    return reasons[:3]


def _quality_confidence(movie: pd.Series) -> float:
    rating = float(movie.get("vote_average", 0) or 0) / 10
    votes = float(movie.get("vote_count", 0) or 0)
    vote_confidence = min(log10(votes + 1) / 5, 1)
    return rating * vote_confidence


def _movie_to_card(movie: pd.Series, score: float | None = None, reasons: list[str] | None = None) -> dict:
    card = {
        "id": int(movie["id"]),
        "title": movie["title"],
        "overview": movie.get("overview", ""),
        "release_date": movie.get("release_date", ""),
        "vote_average": float(movie.get("vote_average", 0) or 0),
        "poster_path": None,
        "backdrop_path": None,
        "similarity_score": score,
        "match_reasons": reasons or [],
    }
    return card


class MovieRecommender:
    def __init__(
        self,
        movies_path: Path = MOVIES_PKL,
        similarity_path: Path = SIMILARITY_PKL,
    ) -> None:
        if not artifacts_available():
            build_recommendation_artifacts()
        self.movies: pd.DataFrame = _read_pickle(movies_path)
        self.similarity = _read_pickle(similarity_path)
        self.title_to_index = {title.lower(): index for index, title in enumerate(self.movies["title"])}
        self.id_to_index = {int(movie_id): index for index, movie_id in enumerate(self.movies["id"])}

    def search(self, query: str, limit: int = 10) -> list[dict]:
        query = query.strip().lower()
        if not query:
            rows = self.movies.head(limit)
            return [_movie_to_card(row) for _, row in rows.iterrows()]

        mask = self.movies["title"].str.lower().str.contains(query, regex=False, na=False)
        rows = self.movies[mask].head(limit)
        if rows.empty:
            matches = get_close_matches(query, list(self.title_to_index.keys()), n=limit, cutoff=0.45)
            rows = self.movies.iloc[[self.title_to_index[match] for match in matches]]
        return [_movie_to_card(row) for _, row in rows.iterrows()]

    def get_by_id(self, movie_id: int) -> dict | None:
        index = self.id_to_index.get(int(movie_id))
        if index is None:
            return None
        return _movie_to_card(self.movies.iloc[index])

    def recommend_by_id(self, movie_id: int, limit: int = 12) -> list[dict]:
        index = self.id_to_index.get(int(movie_id))
        if index is None:
            return []

        seed = self.movies.iloc[index]
        cosine_scores = list(enumerate(self.similarity[index]))
        cosine_scores = sorted(cosine_scores, key=lambda item: item[1], reverse=True)[1:120]

        ranked = []
        for candidate_index, cosine_score in cosine_scores:
            candidate = self.movies.iloc[candidate_index]
            genre_score = _overlap(seed.get("genres"), candidate.get("genres"))
            keyword_score = _overlap(seed.get("keywords"), candidate.get("keywords"))
            cast_score = _overlap(seed.get("cast"), candidate.get("cast"))
            same_director = seed.get("director") and seed.get("director") == candidate.get("director")
            director_score = 1.0 if same_director and (genre_score >= 0.25 or keyword_score > 0) else 0.35 if same_director else 0.0
            quality_score = _quality_confidence(candidate)

            final_score = (
                (0.66 * float(cosine_score))
                + (0.10 * genre_score)
                + (0.15 * keyword_score)
                + (0.12 * director_score)
                + (0.06 * cast_score)
                + (0.03 * quality_score)
            )
            if genre_score > 0 and keyword_score == 0 and director_score == 0 and cast_score == 0:
                final_score *= 0.82
            ranked.append((candidate_index, final_score))

        scores = sorted(ranked, key=lambda item: item[1], reverse=True)
        recs = []
        for candidate_index, score in scores[:limit]:
            candidate = self.movies.iloc[candidate_index]
            recs.append(_movie_to_card(candidate, float(score), _match_reasons(seed, candidate)))
        return recs

    def recommend_by_title(self, title: str, limit: int = 12) -> list[dict]:
        index = self.title_to_index.get(title.lower())
        if index is None:
            matches = get_close_matches(title.lower(), list(self.title_to_index.keys()), n=1, cutoff=0.45)
            if not matches:
                return []
            index = self.title_to_index[matches[0]]
        movie_id = int(self.movies.iloc[index]["id"])
        return self.recommend_by_id(movie_id, limit=limit)


def get_recommender() -> MovieRecommender:
    return MovieRecommender()


if __name__ == "__main__":
    movies = build_recommendation_artifacts()
    print(f"Built recommendation artifacts for {len(movies)} movies")
