"""Firebase Admin setup helpers."""

from __future__ import annotations

from pathlib import Path

import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore


@st.cache_resource(show_spinner=False)
def firestore_client():
    path = st.secrets.get("FIREBASE_SERVICE_ACCOUNT_PATH", "")
    if not path or not Path(path).exists():
        return None

    if not firebase_admin._apps:
        cred = credentials.Certificate(path)
        firebase_admin.initialize_app(cred)
    return firestore.client()
