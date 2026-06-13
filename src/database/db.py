"""Firebase Admin setup helpers."""

from __future__ import annotations

import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore


@st.cache_resource(show_spinner=False)
def firestore_client():
    path = st.secrets.get("FIREBASE_SERVICE_ACCOUNT_PATH", "")
    service_account = st.secrets.get("firebase_service_account", None)
    if not path and not service_account:
        return None

    if not firebase_admin._apps:
        cred = credentials.Certificate(dict(service_account) if service_account else path)
        firebase_admin.initialize_app(cred)
    return firestore.client()
