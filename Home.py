"""CineMatch Streamlit home page."""

import streamlit as st

from src.api.tmdb_api import TMDBError, discover_movies, trending
from src.utils.helpers import compact_movie_row, hero, render_movie_grid, section_header, setup_page


setup_page("Home")

try:
    movies = trending("week")[:12]
    new_releases = discover_movies(sort_by="primary_release_date.desc")[:12]
    top_rated = discover_movies(sort_by="vote_average.desc")[:12]
    featured = movies[0] if movies else {}
except TMDBError as exc:
    st.error(str(exc))
    movies = []
    new_releases = []
    top_rated = []
    featured = {}

if featured:
    hero(featured, "This week's featured signal")
else:
    st.title("CineMatch")
    st.write("A cinematic movie recommendation system.")

section_header(
    "Now Entering The Theater",
    "Live TMDB titles shaped into the same premium, dark cinematic style as the reference UI.",
)
render_movie_grid(movies[:8], "home_trending", columns=4)

compact_movie_row(new_releases, "Fresh Releases", "Recently surfaced titles from the live catalog.")
compact_movie_row(top_rated, "Critic Dense Signals", "High-rating titles with enough audience volume to matter.")
