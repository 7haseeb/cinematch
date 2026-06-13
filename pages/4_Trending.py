"""Trending movies page."""

import streamlit as st

from src.api.tmdb_api import TMDBError, trending
from src.utils.helpers import render_movie_grid, section_header, setup_page


setup_page("Trending")

section_header(
    "Trending Signal",
    "Daily and weekly TMDB momentum translated into a premium poster grid.",
)

try:
    day, week = st.tabs(["Today", "This Week"])
    with day:
        render_movie_grid(trending("day")[:20], "trending_day", columns=4)
    with week:
        render_movie_grid(trending("week")[:20], "trending_week", columns=4)
except TMDBError as exc:
    st.error(str(exc))
