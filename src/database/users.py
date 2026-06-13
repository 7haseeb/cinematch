"""User/session helpers backed by Streamlit OIDC and Firestore."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib.util import find_spec

import streamlit as st

from src.database.db import firestore_client


def auth_configured() -> bool:
    auth = st.secrets.get("auth", {})
    required = ["redirect_uri", "cookie_secret", "client_id", "client_secret", "server_metadata_url"]
    return find_spec("authlib") is not None and all(auth.get(key) for key in required)


def _user_value(key: str, default: str = "") -> str:
    try:
        value = st.user.get(key, default)
    except Exception:
        value = getattr(st.user, key, default)
    return value or default


def _streamlit_user() -> dict | None:
    if not getattr(st.user, "is_logged_in", False):
        return None

    email = _user_value("email")
    name = _user_value("name", email.split("@")[0] if email else "CineMatch User")
    uid = _user_value("sub", email or "google-user")
    user = {
        "uid": f"google-{uid}",
        "name": name,
        "email": email,
        "photo_url": _user_value("picture"),
        "provider": "google",
    }
    save_user_profile(user)
    return user


def current_user() -> dict | None:
    return _streamlit_user() or st.session_state.get("user")


def is_google_user() -> bool:
    user = current_user()
    return bool(user and user.get("provider") == "google")


def user_id() -> str | None:
    user = current_user()
    return user["uid"] if user else None


def save_user_profile(user: dict) -> None:
    db = firestore_client()
    if not db:
        return
    db.collection("users").document(user["uid"]).set(
        {
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "photo_url": user.get("photo_url", ""),
            "provider": user.get("provider", "google"),
            "last_login_at": datetime.now(timezone.utc).isoformat(),
        },
        merge=True,
    )


def render_auth_panel() -> None:
    user = current_user()
    with st.sidebar:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        if user:
            avatar = user["name"][:1].upper()
            photo_url = user.get("photo_url")
            avatar_html = (
                f'<img class="auth-photo" src="{photo_url}" alt="{user["name"]}">'
                if photo_url
                else f'<div class="auth-avatar">{avatar}</div>'
            )
            st.markdown(
                f"""
                <div class="auth-user">
                    {avatar_html}
                    <div>
                        <strong>{user["name"]}</strong>
                        <span>{user["email"]}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Sign out", width="stretch"):
                if getattr(st.user, "is_logged_in", False):
                    st.logout()
                else:
                    st.session_state.pop("user", None)
                    st.rerun()
        else:
            st.markdown("**Member screening**")
            st.caption("Sign in with Google to sync your queue to Firestore.")
            if auth_configured():
                if st.button("Continue with Google", width="stretch"):
                    st.login()
            else:
                st.warning("Google OAuth client ID/secret still needed.")
        st.markdown("</div>", unsafe_allow_html=True)
