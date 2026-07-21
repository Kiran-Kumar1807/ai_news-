"""Streamlit frontend for the AI News Aggregator.

A single entrypoint that renders the Login, Registration, Interest Selection,
Feed, Article Details, Profile and Dashboard Analytics views. Navigation state
is kept in ``st.session_state`` so authentication persists across views.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is importable when launched via `streamlit run`.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from frontend import api_client  # noqa: E402
from frontend.api_client import ApiError  # noqa: E402

st.set_page_config(page_title="AI News Aggregator", page_icon="📰", layout="wide")


def _init_state() -> None:
    st.session_state.setdefault("token", None)
    st.session_state.setdefault("profile", None)
    st.session_state.setdefault("view", "Login")
    st.session_state.setdefault("selected_article", None)


def _logout() -> None:
    st.session_state.token = None
    st.session_state.profile = None
    st.session_state.view = "Login"


def _refresh_profile() -> None:
    try:
        st.session_state.profile = api_client.get_profile(st.session_state.token)
    except ApiError:
        _logout()


# --------------------------------------------------------------------------- #
# Auth views
# --------------------------------------------------------------------------- #
def login_view() -> None:
    st.title("📰 AI News Aggregator")
    st.subheader("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        try:
            token = api_client.login(email, password)
            st.session_state.token = token
            _refresh_profile()
            st.session_state.view = "Feed"
            st.rerun()
        except ApiError as exc:
            st.error(f"Login failed: {exc}")
    st.info("No account yet? Choose **Register** in the sidebar.")


def register_view() -> None:
    st.title("📰 AI News Aggregator")
    st.subheader("Create an account")
    with st.form("register_form"):
        full_name = st.text_input("Full name")
        email = st.text_input("Email")
        password = st.text_input("Password (min 8 chars)", type="password")
        submitted = st.form_submit_button("Register")
    if submitted:
        try:
            api_client.register(email, password, full_name or None)
            st.success("Account created! Please log in.")
            st.session_state.view = "Login"
        except ApiError as exc:
            st.error(f"Registration failed: {exc}")


# --------------------------------------------------------------------------- #
# Authenticated views
# --------------------------------------------------------------------------- #
def interests_view() -> None:
    st.title("Select your interests")
    try:
        categories = api_client.get_categories()
    except ApiError as exc:
        st.error(f"Could not load categories: {exc}")
        return

    current = set((st.session_state.profile or {}).get("interests", []))
    with st.form("interests_form"):
        selected = [c for c in categories if st.checkbox(c, value=c in current)]
        submitted = st.form_submit_button("Save interests")
    if submitted:
        try:
            api_client.update_preferences(st.session_state.token, selected)
            _refresh_profile()
            st.success("Interests updated.")
        except ApiError as exc:
            st.error(f"Failed to update interests: {exc}")


def feed_view() -> None:
    st.title("Your personalized feed")
    try:
        articles = api_client.get_feed(st.session_state.token)
    except ApiError as exc:
        st.error(f"Could not load feed: {exc}")
        return

    if not articles:
        st.info("No articles yet. Select interests or wait for ingestion to run.")
        return

    for article in articles:
        with st.container(border=True):
            st.markdown(f"### {article['title']}")
            st.caption(f"{article['source']} · {article['category']}")
            if article.get("bulletin"):
                st.markdown(f"**{article['bulletin']}**")
            if article.get("summary"):
                st.markdown(article["summary"])
            if st.button("View details", key=f"detail_{article['id']}"):
                st.session_state.selected_article = article["id"]
                st.session_state.view = "Article"
                st.rerun()


def article_view() -> None:
    article_id = st.session_state.selected_article
    if not article_id:
        st.info("No article selected.")
        return
    try:
        article = api_client.get_article(article_id)
    except ApiError as exc:
        st.error(f"Could not load article: {exc}")
        return

    st.title(article["title"])
    st.caption(
        f"{article['source']} · {article['category']} · "
        f"{article.get('published_at', 'unknown date')}"
    )
    if article.get("bulletin"):
        st.info(article["bulletin"])
    if article.get("summary"):
        st.subheader("Summary")
        st.markdown(article["summary"])
    st.subheader("Content")
    st.write(article.get("content", ""))
    st.link_button("Read original", article["article_url"])


def profile_view() -> None:
    st.title("Profile")
    _refresh_profile()
    profile = st.session_state.profile or {}
    st.write(f"**Email:** {profile.get('email', '')}")
    st.write(f"**Name:** {profile.get('full_name') or '—'}")
    st.write(f"**Member since:** {profile.get('created_at', '')}")
    st.write("**Interests:**")
    interests = profile.get("interests", [])
    st.write(", ".join(interests) if interests else "No interests selected yet.")


def dashboard_view() -> None:
    st.title("Dashboard analytics")
    try:
        analytics = api_client.get_analytics()
    except ApiError as exc:
        st.error(f"Could not load analytics: {exc}")
        return

    st.metric("Total articles ingested", analytics.get("total_articles", 0))

    by_category = analytics.get("by_category", {})
    if by_category:
        df = pd.DataFrame(
            {"category": list(by_category.keys()), "count": list(by_category.values())}
        ).sort_values("count", ascending=False)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Articles by category")
            st.plotly_chart(
                px.bar(df, x="category", y="count"), use_container_width=True
            )
        with col2:
            st.subheader("Trending categories")
            st.plotly_chart(
                px.pie(df.head(5), names="category", values="count"),
                use_container_width=True,
            )

    by_day = analytics.get("by_day", {})
    if by_day:
        st.subheader("Daily ingestion count")
        df_day = pd.DataFrame(
            {"day": list(by_day.keys()), "count": list(by_day.values())}
        )
        st.plotly_chart(px.line(df_day, x="day", y="count"), use_container_width=True)


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
def main() -> None:
    _init_state()
    authed = bool(st.session_state.token)

    with st.sidebar:
        st.header("Navigation")
        if authed:
            profile = st.session_state.profile or {}
            st.write(f"Signed in as **{profile.get('email', '')}**")
            options = ["Feed", "Article", "Interests", "Profile", "Dashboard"]
            st.session_state.view = st.radio(
                "Go to",
                options,
                index=options.index(st.session_state.view)
                if st.session_state.view in options
                else 0,
            )
            if st.button("Log out"):
                _logout()
                st.rerun()
        else:
            options = ["Login", "Register"]
            st.session_state.view = st.radio(
                "Go to",
                options,
                index=options.index(st.session_state.view)
                if st.session_state.view in options
                else 0,
            )

    view = st.session_state.view
    if not authed and view not in ("Login", "Register"):
        view = "Login"

    views = {
        "Login": login_view,
        "Register": register_view,
        "Feed": feed_view,
        "Article": article_view,
        "Interests": interests_view,
        "Profile": profile_view,
        "Dashboard": dashboard_view,
    }
    views.get(view, login_view)()


main()
