"""HTTP client for the backend API used by the Streamlit frontend."""
from __future__ import annotations

import os
from typing import Any

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 30


class ApiError(Exception):
    """Raised when the backend returns an error response."""


def _headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _handle(response: requests.Response) -> Any:
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise ApiError(str(detail))
    if response.content:
        return response.json()
    return None


def register(email: str, password: str, full_name: str | None) -> dict:
    resp = requests.post(
        f"{API_BASE_URL}/register",
        json={"email": email, "password": password, "full_name": full_name},
        timeout=TIMEOUT,
    )
    return _handle(resp)


def login(email: str, password: str) -> str:
    resp = requests.post(
        f"{API_BASE_URL}/login",
        json={"email": email, "password": password},
        timeout=TIMEOUT,
    )
    return _handle(resp)["access_token"]


def get_profile(token: str) -> dict:
    resp = requests.get(f"{API_BASE_URL}/profile", headers=_headers(token), timeout=TIMEOUT)
    return _handle(resp)


def get_categories() -> list[str]:
    resp = requests.get(f"{API_BASE_URL}/categories", timeout=TIMEOUT)
    return _handle(resp)["categories"]


def update_preferences(token: str, interests: list[str]) -> list[str]:
    resp = requests.post(
        f"{API_BASE_URL}/preferences",
        json={"interests": interests},
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(resp)["interests"]


def get_feed(token: str, limit: int = 50) -> list[dict]:
    resp = requests.get(
        f"{API_BASE_URL}/feed",
        params={"limit": limit},
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(resp)


def get_article(article_id: int) -> dict:
    resp = requests.get(f"{API_BASE_URL}/articles/{article_id}", timeout=TIMEOUT)
    return _handle(resp)


def get_analytics() -> dict:
    resp = requests.get(f"{API_BASE_URL}/articles/analytics", timeout=TIMEOUT)
    return _handle(resp)


def get_health() -> dict:
    resp = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
    return _handle(resp)
