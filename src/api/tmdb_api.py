"""TMDB API client helpers."""

from __future__ import annotations

import requests
import streamlit as st
from requests import RequestException

from src.config import TMDB_BASE_URL, secret


class TMDBError(RuntimeError):
    """Raised when TMDB returns an unusable response."""


def _params(**extra: object) -> dict[str, object]:
    api_key = secret("TMDB_API_KEY")
    if not api_key:
        raise TMDBError("TMDB_API_KEY is missing from .streamlit/secrets.toml")
    return {"api_key": api_key, "language": "en-US", **extra}


@st.cache_data(ttl=60 * 30, show_spinner=False)
def tmdb_get(endpoint: str, **params: object) -> dict:
    try:
        response = requests.get(
            f"{TMDB_BASE_URL}{endpoint}",
            params=_params(**params),
            timeout=12,
        )
    except RequestException as exc:
        raise TMDBError("Unable to reach TMDB. Check your internet connection and try again.") from exc

    if response.status_code != 200:
        raise TMDBError(f"TMDB request failed: {response.status_code}")
    return response.json()


def trending(time_window: str = "week", page: int = 1) -> list[dict]:
    return tmdb_get(f"/trending/movie/{time_window}", page=page).get("results", [])


def search_movies(query: str, page: int = 1) -> list[dict]:
    if not query.strip():
        return []
    return tmdb_get(
        "/search/movie",
        query=query.strip(),
        page=page,
        include_adult=False,
    ).get("results", [])


def discover_movies(
    *,
    genre_id: str | int | None = None,
    year: int | None = None,
    sort_by: str = "popularity.desc",
    page: int = 1,
) -> list[dict]:
    params: dict[str, object] = {
        "sort_by": sort_by,
        "include_adult": False,
        "include_video": False,
        "page": page,
        "vote_count.gte": 80,
    }
    if genre_id:
        params["with_genres"] = genre_id
    if year:
        params["primary_release_year"] = year
    return tmdb_get("/discover/movie", **params).get("results", [])


def movie_details(movie_id: int) -> dict:
    return tmdb_get(
        f"/movie/{movie_id}",
        append_to_response="credits,recommendations,similar,videos",
    )


def genres() -> list[dict]:
    return tmdb_get("/genre/movie/list").get("genres", [])
