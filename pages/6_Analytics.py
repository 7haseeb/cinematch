"""Movie analytics page."""

from collections import Counter

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.api.posters import backdrop_url, image_url
from src.api.tmdb_api import TMDBError, movie_details, search_movies, trending
from src.database.users import is_google_user, user_id
from src.database.watchlist import has_movie, list_movies
from src.utils.helpers import render_queue_button, setup_page


setup_page("Analytics")

PLOT_LAYOUT = {
    "template": "plotly_dark",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#f7f3f2", "family": "Inter"},
    "margin": {"l": 10, "r": 10, "t": 42, "b": 20},
}


def analytics_metric(label: str, value: str, detail: str, accent: str = "red") -> str:
    return f"""
    <div class="analytics-metric analytics-metric-{accent}">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
    """


def chart_heading(title: str, eyebrow: str) -> None:
    st.markdown(
        f"""
        <div class="analytics-chart-head">
          <span>{eyebrow}</span>
          <h3>{title}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def money(value: int | float | None) -> str:
    if not value:
        return "Undisclosed"
    return f"${value:,.0f}"


def choose_movie() -> int | None:
    query = st.text_input("Select a movie for analytics", placeholder="Search a title or use current trending signals")
    candidates = search_movies(query)[:10] if query else trending("week")[:10]
    if not candidates:
        st.info("Search for a movie to analyze.")
        return None

    labels = {
        f"{movie.get('title', 'Untitled')} ({(movie.get('release_date') or '----')[:4]})": movie["id"]
        for movie in candidates
    }
    return labels[st.selectbox("Analysis target", list(labels.keys()))]


try:
    movie_id = choose_movie()
    if not movie_id:
        st.stop()

    movie = movie_details(movie_id)
    recommendations = movie.get("recommendations", {}).get("results", [])[:12]
    similar = movie.get("similar", {}).get("results", [])[:12]
    cast = movie.get("credits", {}).get("cast", [])[:12]
    crew = movie.get("credits", {}).get("crew", [])
    genres = [genre["name"] for genre in movie.get("genres", [])]
    director = next((person["name"] for person in crew if person.get("job") == "Director"), "Unknown")
    release_year = (movie.get("release_date") or "----")[:4]
    runtime = movie.get("runtime") or 0
    rating = float(movie.get("vote_average") or 0)
    votes = int(movie.get("vote_count") or 0)
    budget = movie.get("budget") or 0
    revenue = movie.get("revenue") or 0
    profit = revenue - budget if revenue and budget else 0

    if is_google_user():
        list_movies(user_id())
    queued = has_movie(movie["id"])

    st.markdown(
        f"""
        <section class="analytics-hero" style="background:
          linear-gradient(105deg, rgba(14,14,14,.96), rgba(14,14,14,.78), rgba(14,14,14,.46)),
          url('{backdrop_url(movie.get("backdrop_path"))}'); background-size:cover; background-position:center;">
          <div>
            <div class="eyebrow">Movie intelligence dossier</div>
            <h1>{movie.get("title", "Untitled")}</h1>
            <p>{movie.get("overview") or "No overview available."}</p>
            <div class="tag-list">
              <span class="tag">{release_year}</span>
              <span class="tag">{runtime or "?"} min</span>
              <span class="tag">{director}</span>
              <span class="tag">{"Queued" if queued else "Not queued"}</span>
            </div>
          </div>
          <div class="analytics-hero-poster">
            <img src="{image_url(movie.get("poster_path"))}" alt="{movie.get("title", "Movie")}">
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    action_col, note_col = st.columns([1, 3])
    with action_col:
        render_queue_button(movie, f"analytics_queue_{movie['id']}", remove_label="Remove")
    with note_col:
        st.caption("Analytics update when you choose another movie above. Queue state syncs with Firebase for signed-in users.")

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(analytics_metric("Critic Index", f"{rating:.1f}", f"{votes:,} TMDB votes"), unsafe_allow_html=True)
    m2.markdown(analytics_metric("Runtime", f"{runtime or 0}", "minutes", "blush"), unsafe_allow_html=True)
    m3.markdown(analytics_metric("Budget", money(budget), "production scale"), unsafe_allow_html=True)
    m4.markdown(analytics_metric("Revenue", money(revenue), f"profit {money(profit)}" if profit else "yield undisclosed", "blush"), unsafe_allow_html=True)

    tab_profile, tab_market, tab_match = st.tabs(["Profile", "Market & Score", "Recommendation Signals"])

    with tab_profile:
        c1, c2 = st.columns([0.9, 1.1])
        with c1:
            chart_heading("Genre Fingerprint", "Narrative buckets")
            genre_values = [1 for _ in genres] or [1]
            genre_labels = genres or ["Unclassified"]
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=genre_labels,
                        values=genre_values,
                        hole=0.58,
                        marker={"colors": ["#e50914", "#ffb4aa", "#e9bcb6", "#6f4e4b", "#3d3837"]},
                        textinfo="label",
                    )
                ]
            )
            fig.update_layout(**PLOT_LAYOUT, height=360, showlegend=False)
            st.plotly_chart(fig, width="stretch")

        with c2:
            chart_heading("Principal Cast Weight", "Top-billed actors")
            cast_names = [person.get("name", "Unknown") for person in cast[:8]]
            cast_order = list(range(len(cast_names), 0, -1))
            fig = px.bar(
                x=cast_order,
                y=cast_names,
                orientation="h",
                color=cast_order,
                color_continuous_scale=["#3a1719", "#e50914", "#ffb4aa"],
            )
            fig.update_layout(**PLOT_LAYOUT, height=360, coloraxis_showscale=False)
            fig.update_xaxes(showgrid=False, title="")
            fig.update_yaxes(showgrid=False, title="", autorange="reversed")
            st.plotly_chart(fig, width="stretch")

    with tab_market:
        c3, c4 = st.columns([1, 1])
        with c3:
            chart_heading("Commercial Yield", "Budget vs revenue")
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=["Budget", "Revenue", "Profit"],
                        y=[budget, revenue, max(profit, 0)],
                        marker={"color": ["#e9bcb6", "#e50914", "#ffb4aa"]},
                    )
                ]
            )
            fig.update_layout(**PLOT_LAYOUT, height=350)
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)", title="")
            st.plotly_chart(fig, width="stretch")

        with c4:
            chart_heading("Score Positioning", "Rating, vote volume, runtime")
            fig = go.Figure()
            fig.add_trace(
                go.Scatterpolar(
                    r=[rating * 10, min(votes / 1000, 100), min(runtime / 2, 100)],
                    theta=["Rating", "Vote Volume", "Runtime"],
                    fill="toself",
                    line={"color": "#e50914"},
                    fillcolor="rgba(229,9,20,0.28)",
                )
            )
            fig.update_layout(**PLOT_LAYOUT, height=350, polar={"radialaxis": {"visible": True, "range": [0, 100]}})
            st.plotly_chart(fig, width="stretch")

    with tab_match:
        rec_ratings = [item.get("vote_average", 0) for item in recommendations]
        sim_ratings = [item.get("vote_average", 0) for item in similar]
        c5, c6 = st.columns([1, 1])
        with c5:
            chart_heading("Recommendation Rating Spread", "TMDB recommendation set")
            fig = px.histogram(x=rec_ratings, nbins=6, color_discrete_sequence=["#e50914"])
            fig.update_layout(**PLOT_LAYOUT, height=330)
            fig.update_xaxes(title="Rating", gridcolor="rgba(255,255,255,0.06)")
            fig.update_yaxes(title="Titles", gridcolor="rgba(255,255,255,0.06)")
            st.plotly_chart(fig, width="stretch")

        with c6:
            chart_heading("Similar Title Spread", "Adjacency set")
            fig = px.histogram(x=sim_ratings, nbins=6, color_discrete_sequence=["#ffb4aa"])
            fig.update_layout(**PLOT_LAYOUT, height=330)
            fig.update_xaxes(title="Rating", gridcolor="rgba(255,255,255,0.06)")
            fig.update_yaxes(title="Titles", gridcolor="rgba(255,255,255,0.06)")
            st.plotly_chart(fig, width="stretch")

        st.markdown(
            f"""
            <div class="analytics-feature-strip">
              <div><span>Recommendation count</span><strong>{len(recommendations)}</strong></div>
              <div><span>Similar count</span><strong>{len(similar)}</strong></div>
              <div><span>Top cast signal</span><strong>{cast[0].get("name", "Unknown") if cast else "Unknown"}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

except TMDBError as exc:
    st.error(str(exc))
