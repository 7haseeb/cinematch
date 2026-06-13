"""Compare movies page."""

import streamlit as st

from src.api.tmdb_api import TMDBError, movie_details, trending
from src.utils.helpers import movie_select_options, section_header, setup_page


setup_page("Compare Movies")

section_header(
    "Comparison Station",
    "Set any two titles side-by-side to compare ratings, runtime, genres, revenue, and summaries.",
)

try:
    movies = trending("week")[:12]
    options = movie_select_options(movies)
    labels = list(options.keys())

    c1, c2 = st.columns(2)
    left_label = c1.selectbox("Target Film 1", labels, index=0)
    right_label = c2.selectbox("Target Film 2", labels, index=1 if len(labels) > 1 else 0)

    left = movie_details(options[left_label])
    right = movie_details(options[right_label])

    p1, p2 = st.columns(2)
    with p1:
        st.image(f"https://image.tmdb.org/t/p/w500{left.get('poster_path')}", width="stretch")
        st.subheader(left.get("title"))
    with p2:
        st.image(f"https://image.tmdb.org/t/p/w500{right.get('poster_path')}", width="stretch")
        st.subheader(right.get("title"))

    rows = [
        ("Release Era", (left.get("release_date") or "----")[:4], (right.get("release_date") or "----")[:4]),
        ("Running Duration", f"{left.get('runtime') or '?'} min", f"{right.get('runtime') or '?'} min"),
        ("Critic Score Index", f"{left.get('vote_average', 0):.1f}", f"{right.get('vote_average', 0):.1f}"),
        ("Visual Genres", ", ".join(g["name"] for g in left.get("genres", [])), ", ".join(g["name"] for g in right.get("genres", []))),
        ("Box Revenue Yield", f"${left.get('revenue', 0):,}", f"${right.get('revenue', 0):,}"),
        ("Plot Logline Overview", left.get("overview", ""), right.get("overview", "")),
    ]
    st.dataframe(
        [{"Metric": row[0], left.get("title", "Film 1"): row[1], right.get("title", "Film 2"): row[2]} for row in rows],
        width="stretch",
        hide_index=True,
    )
except TMDBError as exc:
    st.error(str(exc))
