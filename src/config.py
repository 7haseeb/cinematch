"""Application configuration."""

from pathlib import Path

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT_DIR / "assets"
CSS_FILE = ASSETS_DIR / "css" / "style.css"
FAVICON_FILE = ASSETS_DIR / "favicon.png"
FAVICON_ICO_FILE = ASSETS_DIR / "favicon.ico"

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"


def secret(name: str, default: str = "") -> str:
    """Read a Streamlit secret without failing during local setup."""
    return st.secrets.get(name, default)
