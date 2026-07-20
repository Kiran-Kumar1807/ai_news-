"""Tests for authentication (registration, login, JWT-protected routes)."""
from __future__ import annotations

from backend.services.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-password")
    assert hashed != "s3cret-password"
    assert verify_password("s3cret-password", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip():
    token = create_access_token(42)
    payload = decode_access_token(token)
    assert payload["sub"] == "42"


def test_register_and_login_flow(client):
    resp = client.post(
        "/register",
        json={"email": "alice@example.com", "password": "password123", "full_name": "Alice"},
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "alice@example.com"

    # Duplicate registration is rejected.
    dup = client.post(
        "/register",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert dup.status_code == 409

    login = client.post(
        "/login", json={"email": "alice@example.com", "password": "password123"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token

    profile = client.get("/profile", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["email"] == "alice@example.com"


def test_login_with_wrong_password(client):
    client.post(
        "/register", json={"email": "bob@example.com", "password": "password123"}
    )
    resp = client.post(
        "/login", json={"email": "bob@example.com", "password": "nope"}
    )
    assert resp.status_code == 401


def test_profile_requires_authentication(client):
    assert client.get("/profile").status_code == 401  # missing bearer
    bad = client.get("/profile", headers={"Authorization": "Bearer not-a-token"})
    assert bad.status_code == 401
