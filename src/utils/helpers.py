"""Shared Streamlit UI helpers."""

from __future__ import annotations

import html

import streamlit as st
from PIL import Image

from src.api.posters import backdrop_url, image_url
from src.config import CSS_FILE, FAVICON_FILE, FAVICON_ICO_FILE
from src.database.users import render_auth_panel


def page_icon():
    for icon_file in (FAVICON_FILE, FAVICON_ICO_FILE):
        if icon_file.exists():
            return Image.open(icon_file)
    return "🎬"


def setup_page(title: str) -> None:
    st.set_page_config(
        page_title=f"{title} | CineMatch",
        page_icon=page_icon(),
        layout="wide",
        initial_sidebar_state="auto",
    )
    load_css()
    render_sidebar(title)
    process_pending_queue()


def process_pending_queue() -> None:
    pending = st.session_state.get("pending_queue_movie")
    if not pending:
        return

    from src.database.users import is_google_user, user_id
    from src.database.watchlist import add_movie

    if is_google_user():
        add_movie(pending, user_id())
        st.session_state.pop("pending_queue_movie", None)
        st.toast(f"Added {pending.get('title', 'movie')} to your Firebase queue")


def load_css() -> None:
    if CSS_FILE.exists():
        st.markdown(f"<style>{CSS_FILE.read_text()}</style>", unsafe_allow_html=True)


def render_sidebar(active_title: str = "Home") -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="cm-brand">
                <div class="cm-logo">C</div>
                <div>
                    <div class="cm-brand-title">CineMatch</div>
                    <div class="cm-brand-subtitle">Recommendation Engine</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        nav_items = [
            ("Core", "TS", "Theater Stage", "/", "Home"),
            ("Core", "DS", "Discovery", "/Discover", "Discover"),
            ("Core", "MC", "Match Console", "/Recommendations", "Recommendations"),
            ("Library", "FD", "Film Dossier", "/Movie_Details", "Movie Details"),
            ("Library", "TR", "Trending Signal", "/Trending", "Trending"),
            ("Library", "SQ", "Screening Queue", "/Watchlist", "Watchlist"),
            ("Studio", "AN", "Analytics", "/Analytics", "Analytics"),
            ("Studio", "CS", "Comparison Station", "/Compare_Movies", "Compare Movies"),
            ("Studio", "ED", "Editorial", "/About", "About"),
        ]
        nav_html = ['<nav class="cm-nav">']
        current_group = None
        for group, token, label, href, title in nav_items:
            if group != current_group:
                current_group = group
                nav_html.append(f'<div class="cm-nav-group">{html.escape(group)}</div>')
            active = " is-active" if title == active_title else ""
            nav_html.append(
                f'<a class="cm-nav-item{active}" href="{href}" target="_self">'
                f'<span class="cm-nav-token">{html.escape(token)}</span>'
                f'<span class="cm-nav-label">{html.escape(label)}</span>'
                "</a>"
            )
        nav_html.append("</nav>")
        st.markdown("".join(nav_html), unsafe_allow_html=True)
    render_auth_panel()
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-note">
                <strong>TMDB live catalog</strong><br>
                <span style="color:rgba(233,188,182,.6);font-size:.75rem;">
                Search, discover, trending, recommendations, and details are powered by TMDB.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def section_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="section-header">
            <h2>{html.escape(title)}</h2>
            <div class="section-subtitle">{html.escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(movie: dict, eyebrow: str = "Featured match") -> None:
    title = movie.get("title", "CineMatch")
    overview = movie.get("overview") or "A premium cinematic recommendation experience for discovering films worth your next screening."
    year = (movie.get("release_date") or "----")[:4]
    rating = float(movie.get("vote_average") or 0)
    bg = backdrop_url(movie.get("backdrop_path"))
    poster = image_url(movie.get("poster_path"))
    st.markdown(
        f"""
        <section class="hero hero-split" style="background-image:url('{bg}')">
            <div class="hero-content">
                <div class="eyebrow">{html.escape(eyebrow)}</div>
                <h1>{html.escape(title)}</h1>
                <p>{html.escape(overview[:320])}</p>
                <div class="tag-list">
                    <span class="tag">{html.escape(year)}</span>
                    <span class="tag">Critic Index {rating:.1f}</span>
                    <span class="tag">TMDB Live</span>
                </div>
                <div class="hero-actions">
                    <a class="cm-button" href="/Recommendations" target="_self">Start Matching</a>
                    <a class="cm-button-secondary" href="/Discover" target="_self">Browse Catalog</a>
                </div>
            </div>
            <div class="hero-poster-shell">
                <img src="{poster}" alt="{html.escape(title)}">
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def movie_card(movie: dict) -> str:
    title = movie.get("title") or movie.get("name") or "Untitled"
    year = (movie.get("release_date") or "Unknown")[:4]
    rating = float(movie.get("vote_average") or 0)
    poster = image_url(movie.get("poster_path"))
    reasons = movie.get("match_reasons") or []
    score = movie.get("similarity_score")
    match_html = ""
    if reasons or score:
        reason_text = " • ".join(reasons[:2]) if reasons else "Content similarity"
        score_text = f"{float(score) * 100:.0f}% match" if score is not None else "Matched"
        match_html = (
            '<div class="movie-match">'
            f"<strong>{html.escape(score_text)}</strong>"
            f"<span>{html.escape(reason_text)}</span>"
            "</div>"
        )
    return (
        '<div class="movie-card">'
        '<div class="poster-wrap">'
        f'<img src="{poster}" alt="{html.escape(title)}">'
        f'<div class="rating-pill">★ {rating:.1f}</div>'
        "</div>"
        '<div class="movie-body">'
        f'<div class="movie-title">{html.escape(title)}</div>'
        f'<div class="movie-meta">{html.escape(year)}</div>'
        f"{match_html}"
        "</div>"
        "</div>"
    )


def render_movie_grid(movies: list[dict], key_prefix: str, columns: int = 4) -> None:
    if not movies:
        st.markdown('<div class="empty-state">No titles found for this view.</div>', unsafe_allow_html=True)
        return

    cols = st.columns(columns)
    for index, movie in enumerate(movies):
        with cols[index % columns]:
            st.markdown(movie_card(movie), unsafe_allow_html=True)
            left, right = st.columns(2)
            with left:
                st.markdown(
                    f"""
                    <div class="movie-action-link-wrap">
                        <a class="movie-action-link" href="/Movie_Details?movie_id={movie['id']}" target="_self">Details</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with right:
                render_queue_button(movie, f"{key_prefix}_queue_{movie['id']}")


def ensure_watchlist_loaded() -> None:
    from src.database.users import is_google_user, user_id
    from src.database.watchlist import list_movies

    if is_google_user() and not st.session_state.get("watchlist_loaded_for") == user_id():
        list_movies(user_id())
        st.session_state["watchlist_loaded_for"] = user_id()


def render_queue_button(movie: dict, key: str, *, remove_label: str = "Remove") -> None:
    from src.database.users import auth_configured, is_google_user, user_id
    from src.database.watchlist import add_movie, has_movie, remove_movie

    ensure_watchlist_loaded()
    movie_id = movie.get("id") or movie.get("movie_id")
    queued = has_movie(movie_id) if movie_id else False
    label = remove_label if queued else "Queue"

    if st.button(label, key=key, width="stretch", type="secondary" if queued else "primary"):
        if not is_google_user():
            st.session_state["pending_queue_movie"] = movie
            if auth_configured():
                st.login()
            else:
                st.warning("Google login must be configured before saving movies.")
            return

        if queued:
            remove_movie(movie_id, user_id())
            st.toast(f"Removed {movie.get('title', 'movie')} from your queue")
        else:
            add_movie(movie, user_id())
            st.toast(f"Added {movie.get('title', 'movie')} to your Firebase queue")

        st.session_state["watchlist_loaded_for"] = None
        st.rerun()


def compact_movie_row(movies: list[dict], title: str, subtitle: str = "") -> None:
    section_header(title, subtitle)
    cards = []
    for movie in movies:
        movie_title = movie.get("title") or movie.get("name") or "Untitled"
        year = (movie.get("release_date") or "----")[:4]
        rating = float(movie.get("vote_average") or 0)
        cards.append(
            '<div class="mini-card">'
            f'<img src="{image_url(movie.get("poster_path"), "w342")}" alt="{html.escape(movie_title)}">'
            '<div class="mini-card-body">'
            f"<strong>{html.escape(movie_title)}</strong>"
            f"<span>{html.escape(year)} • ★ {rating:.1f}</span>"
            "</div>"
            "</div>"
        )
    st.markdown(f'<div class="poster-row">{"".join(cards)}</div>', unsafe_allow_html=True)


def cast_row(cast: list[dict]) -> None:
    if not cast:
        return

    cols = st.columns(4)
    for index, person in enumerate(cast[:8]):
        name = person.get("name", "Unknown")
        character = person.get("character", "Cast")
        with cols[index % 4]:
            st.image(image_url(person.get("profile_path"), "w185"), width="stretch")
            st.markdown(f"**{name}**")
            st.caption(character[:42])


def trailer_url(movie: dict) -> str | None:
    videos = movie.get("videos", {}).get("results", [])
    for video in videos:
        if video.get("site") == "YouTube" and video.get("type") in {"Trailer", "Teaser"}:
            return f"https://www.youtube.com/watch?v={video.get('key')}"
    return None


def metric_card(title: str, value: str, subtitle: str) -> str:
    return f"""
    <div class="metric-card">
        <span>{html.escape(title)}</span>
        <strong>{html.escape(value)}</strong>
        <small style="color:rgba(233,188,182,.45);font-weight:700;">{html.escape(subtitle)}</small>
    </div>
    """


def movie_select_options(movies: list[dict]) -> dict[str, int]:
    options = {}
    for movie in movies:
        year = (movie.get("release_date") or "----")[:4]
        options[f"{movie.get('title', 'Untitled')} ({year})"] = movie["id"]
    return options
