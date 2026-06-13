"""Trending movie API helpers."""

from src.api.tmdb_api import trending


def trending_today() -> list[dict]:
    return trending("day")


def trending_this_week() -> list[dict]:
    return trending("week")
