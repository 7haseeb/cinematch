"""About CineMatch page."""

import streamlit as st

from src.utils.helpers import setup_page


setup_page("About")

st.markdown(
    """
    <section class="editorial-hero">
      <div class="editorial-copy">
        <div class="eyebrow">Editorial statement</div>
        <h1>CineMatch</h1>
        <p>
          A dark cinematic recommendation studio built for browsing, comparing,
          analyzing, and saving films with the taste of a cinephile and the speed
          of a modern data app.
        </p>
        <div class="editorial-credit">
          <span>Developed by</span>
          <strong>Muhammad Haseeb Shah</strong>
        </div>
      </div>
      <div class="editorial-mark">
        <div class="film-slate">
          <span></span><span></span><span></span>
        </div>
        <div class="play-orbit">▶</div>
        <div class="check-mark">✓</div>
      </div>
    </section>

    <section class="editorial-grid">
      <div class="editorial-card">
        <span>01</span>
        <h3>Recommendation Engine</h3>
        <p>Weighted content similarity using genres, director, cast, keywords, overview, and reranked match signals.</p>
      </div>
      <div class="editorial-card">
        <span>02</span>
        <h3>Personal Queue</h3>
        <p>Google login with Firebase-backed watchlists, so saved films follow the user across sessions.</p>
      </div>
      <div class="editorial-card">
        <span>03</span>
        <h3>Movie Intelligence</h3>
        <p>Dynamic analytics for selected titles, including market yield, genre fingerprint, cast weight, and match spread.</p>
      </div>
    </section>

    <section class="editorial-band">
      <div>
        <span>Stack</span>
        <strong>Streamlit · TMDB · Firebase · Scikit-learn · Plotly</strong>
      </div>
      <div>
        <span>Dataset</span>
        <strong>TMDB 5000 Movie Metadata</strong>
      </div>
      <div>
        <span>Experience</span>
        <strong>Cinematic, responsive, user-aware</strong>
      </div>
    </section>

    <section class="signature-panel">
      <div class="signature-line"></div>
      <p>
        CineMatch was designed as more than a demo: it is a full movie discovery
        workspace, combining recommendation logic, authenticated persistence,
        live TMDB data, and a premium cinema-inspired interface.
      </p>
      <strong>Muhammad Haseeb Shah</strong>
    </section>
    """,
    unsafe_allow_html=True,
)
