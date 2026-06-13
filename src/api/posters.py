"""Poster fetching helpers."""

from src.config import TMDB_IMAGE_BASE_URL


def image_url(path: str | None, size: str = "w500") -> str:
    if not path:
        return "https://placehold.co/500x750/1c1b1b/e9bcb6?text=CineMatch"
    return f"{TMDB_IMAGE_BASE_URL}/{size}{path}"


def backdrop_url(path: str | None, size: str = "w1280") -> str:
    if not path:
        return "https://placehold.co/1280x720/0e0e0e/e50914?text=CineMatch"
    return f"{TMDB_IMAGE_BASE_URL}/{size}{path}"
