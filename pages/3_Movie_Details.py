"""Movie details page."""

import html

import streamlit as st

from src.api.posters import backdrop_url, image_url
from src.api.tmdb_api import TMDBError, movie_details, search_movies
from src.utils.helpers import cast_row, compact_movie_row, render_movie_grid, render_queue_button, section_header, setup_page, trailer_url


setup_page("Movie Details")

section_header(
    "Film Dossier",
    "A focused detail view with cast, genres, metadata, and onward recommendations.",
)

try:
    movie_id = st.query_params.get("movie_id") or st.session_state.get("selected_movie_id")
    if not movie_id:
        query = st.text_input("Search a movie to inspect")
        results = search_movies(query)[:8] if query else []
        if results:
            labels = {f"{m['title']} ({(m.get('release_date') or '----')[:4]})": m["id"] for m in results}
            movie_id = labels[st.selectbox("Choose movie", list(labels.keys()))]

    if not movie_id:
        st.markdown('<div class="empty-state">Choose a movie from Discover or search above.</div>', unsafe_allow_html=True)
        st.stop()

    movie = movie_details(int(movie_id))
    genres = [item["name"] for item in movie.get("genres", [])]
    cast = movie.get("credits", {}).get("cast", [])[:6]
    director = next(
        (person["name"] for person in movie.get("credits", {}).get("crew", []) if person.get("job") == "Director"),
        "Unknown director",
    )

    st.markdown(
        f"""
        <div class="detail-panel detail-hero" style="background:
          linear-gradient(90deg, rgba(28,27,27,.96), rgba(28,27,27,.72)),
          url('{backdrop_url(movie.get("backdrop_path"))}'); background-size:cover; background-position:center;">
            <div class="detail-poster">
                <img src="{image_url(movie.get("poster_path"))}" alt="{html.escape(movie.get("title", "Movie"))}">
            </div>
            <div>
                <div class="eyebrow">Selected title dossier</div>
                <h1 style="font-size:clamp(2rem,5vw,4.2rem);line-height:1;font-weight:900;color:white;">
                    {html.escape(movie.get("title", "Untitled"))}
                </h1>
                <div class="tag-list">
                    <span class="tag">{html.escape((movie.get("release_date") or "----")[:4])}</span>
                    <span class="tag">{movie.get("runtime") or "?"} min</span>
                    <span class="tag">★ {float(movie.get("vote_average") or 0):.1f}</span>
                    <span class="tag">{html.escape(director)}</span>
                </div>
                <p class="section-subtitle">{html.escape(movie.get("overview") or "No overview available.")}</p>
                <div class="tag-list">
                    {"".join(f'<span class="tag">{html.escape(g)}</span>' for g in genres)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 3])
    with c1:
        render_queue_button(movie, f"details_queue_{movie['id']}", remove_label="Remove from queue")
    with c2:
        trailer = trailer_url(movie)
        if trailer:
            st.link_button("Watch trailer", trailer, width="content")

    section_header("Principal Cast", "Faces and roles attached to this title.")
    cast_row(cast)

    section_header("Related Screenings", "Recommendations attached to this title.")
    render_movie_grid(movie.get("recommendations", {}).get("results", [])[:8], "details_recs", columns=4)
    compact_movie_row(movie.get("similar", {}).get("results", [])[:12], "Similarity Corridor", "More titles with adjacent TMDB signals.")
except TMDBError as exc:
    st.error(str(exc))
