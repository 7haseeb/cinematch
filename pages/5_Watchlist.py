"""User watchlist page."""

import streamlit as st

from src.api.posters import image_url
from src.database.users import auth_configured, is_google_user, user_id
from src.database.watchlist import list_movies, remove_movie, update_movie
from src.utils.helpers import movie_card, section_header, setup_page


setup_page("Watchlist")

section_header(
    "Private Screening Queue",
    "Your saved movies are synced to Firestore and restored whenever you sign in with Google.",
)

if not is_google_user():
    st.markdown(
        """
        <div class="empty-state">
          <strong>Google sign-in required</strong><br>
          Sign in with Google to create and restore your private Firebase watchlist.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if auth_configured() and st.button("Continue with Google", width="content"):
        st.login()
    st.stop()

movies = list_movies(user_id())

if not movies:
    st.markdown(
        '<div class="empty-state"><strong>Screening Queue is Empty</strong><br>Browse Discover or Trending and queue a film.</div>',
        unsafe_allow_html=True,
    )
else:
    c1, c2, c3 = st.columns([1, 1, 2])
    view_mode = c1.segmented_control("View", ["Grid", "List"], default="Grid")
    status_filter = c2.segmented_control("Status", ["All", "Unwatched", "Watched"], default="All")
    sort_by = c3.selectbox("Sort queue", ["Recently added", "Highest rated", "Release year", "Title"])

    if status_filter == "Watched":
        movies = [movie for movie in movies if movie.get("watched")]
    elif status_filter == "Unwatched":
        movies = [movie for movie in movies if not movie.get("watched")]

    if sort_by == "Highest rated":
        movies = sorted(movies, key=lambda item: item.get("vote_average") or 0, reverse=True)
    elif sort_by == "Release year":
        movies = sorted(movies, key=lambda item: item.get("release_date") or "", reverse=True)
    elif sort_by == "Title":
        movies = sorted(movies, key=lambda item: item.get("title") or "")
    else:
        movies = sorted(movies, key=lambda item: item.get("added_at") or "", reverse=True)

    watched_count = sum(1 for movie in list_movies(user_id()) if movie.get("watched"))
    st.caption(f"{len(movies)} visible title(s) • {watched_count} watched")

    if view_mode == "Grid":
        cols = st.columns(4)
        for index, movie in enumerate(movies):
            movie_id = movie["movie_id"]
            with cols[index % 4]:
                st.markdown(movie_card(movie), unsafe_allow_html=True)
                watched = st.checkbox(
                    "Watched",
                    value=bool(movie.get("watched")),
                    key=f"watched_grid_{movie_id}",
                )
                if watched != bool(movie.get("watched")):
                    update_movie(movie_id, user_id(), watched=watched)
                    st.rerun()
                if st.button("Remove queue", key=f"remove_{movie_id}", width="stretch"):
                    remove_movie(movie_id, user_id())
                    st.rerun()
    else:
        for movie in movies:
            movie_id = movie["movie_id"]
            st.markdown(
                f"""
                <div class="queue-list-item">
                    <img src="{image_url(movie.get("poster_path"))}" alt="{movie.get("title", "Movie")}">
                    <div>
                        <h3>{movie.get("title", "Untitled")}</h3>
                        <p>{(movie.get("release_date") or "----")[:4]} • ★ {float(movie.get("vote_average") or 0):.1f}</p>
                        <p>{movie.get("overview", "")[:220]}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            left, right = st.columns([1, 1])
            watched = left.checkbox(
                "Watched",
                value=bool(movie.get("watched")),
                key=f"watched_list_{movie_id}",
            )
            if watched != bool(movie.get("watched")):
                update_movie(movie_id, user_id(), watched=watched)
                st.rerun()
            if right.button("Remove queue", key=f"remove_list_{movie_id}", width="stretch"):
                remove_movie(movie_id, user_id())
                st.rerun()
