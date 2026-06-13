"""Movie recommendations page."""

import streamlit as st

from src.api.posters import image_url
from src.api.tmdb_api import TMDBError, movie_details
from src.recommendation.recommender import artifacts_available, get_recommender
from src.utils.helpers import movie_select_options, render_movie_grid, section_header, setup_page


setup_page("Recommendations")


@st.cache_resource(show_spinner=False)
def load_recommender():
    return get_recommender()


@st.cache_data(ttl=60 * 60, show_spinner=False)
def enrich_movie(movie: dict) -> dict:
    try:
        details = movie_details(int(movie["id"]))
    except TMDBError:
        return movie

    enriched = movie.copy()
    enriched.update(
        {
            "title": details.get("title") or movie.get("title"),
            "overview": details.get("overview") or movie.get("overview"),
            "release_date": details.get("release_date") or movie.get("release_date"),
            "vote_average": details.get("vote_average") or movie.get("vote_average"),
            "poster_path": details.get("poster_path"),
            "backdrop_path": details.get("backdrop_path"),
        }
    )
    return enriched

section_header(
    "Recommendation Console",
    "Select a seed film and CineMatch will generate local content-based matches from the TMDB 5000 dataset.",
)

try:
    if not artifacts_available():
        st.warning("Recommendation models are missing. Run `.venv/bin/python -m src.recommendation.recommender` first.")
        st.stop()

    recommender = load_recommender()
    query = st.text_input("Find a seed movie", placeholder="Search Avatar, The Dark Knight, Interstellar...")
    seed_movies = recommender.search(query, limit=12)
    options = movie_select_options(seed_movies)

    if not options:
        st.info("No local dataset matches found. Try another title.")
    else:
        selected = st.selectbox("Seed title", list(options.keys()))
        selected_id = options[selected]
        local_seed = recommender.get_by_id(selected_id)
        local_recs = [enrich_movie(movie) for movie in recommender.recommend_by_id(selected_id, limit=12)]

        try:
            details = movie_details(selected_id)
        except TMDBError:
            details = local_seed or {}

        st.session_state["selected_movie_id"] = selected_id
        c1, c2 = st.columns([1, 3])
        with c1:
            st.image(image_url(details.get("poster_path")), width="stretch")
        with c2:
            st.subheader(details.get("title") or local_seed.get("title", "Selected movie"))
            st.write(details.get("overview") or local_seed.get("overview", ""))
            st.caption(
                f"Rating {float(details.get('vote_average') or local_seed.get('vote_average') or 0):.1f} • "
                f"{(details.get('release_date') or local_seed.get('release_date') or '----')[:4]} • "
                f"{details.get('runtime') or local_seed.get('runtime') or 'Runtime unknown'} min"
            )
            st.markdown(
                """
                <div class="tag-list">
                    <span class="tag">Local TF-IDF</span>
                    <span class="tag">Content Similarity</span>
                    <span class="tag">TMDB 5000</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        tmdb_recs = details.get("recommendations", {}).get("results", []) if isinstance(details, dict) else []
        tmdb_similar = details.get("similar", {}).get("results", []) if isinstance(details, dict) else []

        tab1, tab2, tab3 = st.tabs(["CineMatch Engine", "TMDB Recommended", "TMDB Similar"])
        with tab1:
            render_movie_grid(local_recs, "local_recommendations", columns=4)
        with tab2:
            render_movie_grid(tmdb_recs[:12], "tmdb_recommendations", columns=4)
        with tab3:
            render_movie_grid(tmdb_similar[:12], "tmdb_similar", columns=4)
except TMDBError as exc:
    st.error(str(exc))
