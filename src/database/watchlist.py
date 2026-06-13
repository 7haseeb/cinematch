"""Watchlist persistence helpers."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from src.database.db import firestore_client


SESSION_KEY = "watchlist"


def _local_watchlist() -> dict[str, dict]:
    st.session_state.setdefault(SESSION_KEY, {})
    return st.session_state[SESSION_KEY]


def add_movie(movie: dict, user_id: str | None = None) -> None:
    movie_id = str(movie["id"])
    payload = {
        "movie_id": movie["id"],
        "title": movie.get("title") or movie.get("name", "Untitled"),
        "poster_path": movie.get("poster_path"),
        "backdrop_path": movie.get("backdrop_path"),
        "release_date": movie.get("release_date", ""),
        "vote_average": movie.get("vote_average", 0),
        "overview": movie.get("overview", ""),
        "added_at": datetime.now(timezone.utc).isoformat(),
        "watched": movie.get("watched", False),
        "notes": movie.get("notes", ""),
    }
    _local_watchlist()[movie_id] = payload

    db = firestore_client()
    if db and user_id:
        db.collection("users").document(user_id).collection("watchlist").document(movie_id).set(payload)


def remove_movie(movie_id: int | str, user_id: str | None = None) -> None:
    movie_id = str(movie_id)
    _local_watchlist().pop(movie_id, None)

    db = firestore_client()
    if db and user_id:
        db.collection("users").document(user_id).collection("watchlist").document(movie_id).delete()


def list_movies(user_id: str | None = None) -> list[dict]:
    db = firestore_client()
    if db and user_id:
        docs = db.collection("users").document(user_id).collection("watchlist").stream()
        movies = [doc.to_dict() for doc in docs]
        st.session_state[SESSION_KEY] = {str(movie["movie_id"]): movie for movie in movies}
    return list(_local_watchlist().values())


def has_movie(movie_id: int | str) -> bool:
    return str(movie_id) in _local_watchlist()


def update_movie(movie_id: int | str, user_id: str | None = None, **updates: object) -> None:
    movie_id = str(movie_id)
    watchlist = _local_watchlist()
    if movie_id in watchlist:
        watchlist[movie_id].update(updates)

    db = firestore_client()
    if db and user_id:
        db.collection("users").document(user_id).collection("watchlist").document(movie_id).set(
            updates,
            merge=True,
        )
