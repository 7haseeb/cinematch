"""Discover movies page."""

import datetime as dt

import streamlit as st

from src.api.tmdb_api import TMDBError, discover_movies, genres, search_movies
from src.utils.helpers import render_movie_grid, section_header, setup_page


setup_page("Discover")

section_header(
    "Catalog Discovery",
    "Filter the live TMDB catalog by genre, year, rating, or search phrase.",
)

try:
    genre_items = genres()
    genre_options = {"All genres": None} | {item["name"]: item["id"] for item in genre_items}

    c1, c2, c3 = st.columns([2, 1, 1])
    query = c1.text_input("Search title", placeholder="Blade Runner, Dune, Inception...")
    genre_name = c2.selectbox("Genre", list(genre_options.keys()))
    year = c3.number_input("Release year", min_value=1900, max_value=dt.date.today().year, value=2024)

    sort = st.selectbox(
        "Catalog sort",
        {
            "Most popular": "popularity.desc",
            "Highest rated": "vote_average.desc",
            "Newest releases": "primary_release_date.desc",
            "Most discussed": "vote_count.desc",
        },
    )

    if query:
        movies = search_movies(query)[:20]
    else:
        movies = discover_movies(
            genre_id=genre_options[genre_name],
            year=int(year) if year else None,
            sort_by=sort,
        )[:20]

    render_movie_grid(movies, "discover", columns=4)
except TMDBError as exc:
    st.error(str(exc))
