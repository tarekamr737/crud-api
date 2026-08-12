import os
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://unused")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")

import app.repository as repository


original_init_db = repository.init_db
repository.init_db = lambda: None
from app.main import app

repository.init_db = original_init_db

from fastapi.testclient import TestClient
from supabase_auth.errors import AuthApiError


client = TestClient(app)


def test_public_info_requires_no_authentication() -> None:
    response = client.get("/public/info")

    assert response.status_code == 200
    assert response.json() == {"message": "Welcome stranger! This info is public."}


def test_profile_returns_safe_verified_user_data() -> None:
    user = SimpleNamespace(
        id="user-123",
        email="person@example.com",
        created_at="2026-08-12T10:00:00Z",
    )
    with patch(
        "app.auth.supabase.auth.get_user",
        return_value=SimpleNamespace(user=user),
    ):
        response = client.get(
            "/protected/profile",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "id": "user-123",
        "email": "person@example.com",
        "created_at": "2026-08-12T10:00:00Z",
    }


def test_profile_rejects_missing_token() -> None:
    response = client.get("/protected/profile")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired authentication token"}


def test_dashboard_reuses_the_same_auth_dependency() -> None:
    user = SimpleNamespace(id="user-123")
    with patch(
        "app.auth.supabase.auth.get_user",
        return_value=SimpleNamespace(user=user),
    ) as get_user:
        response = client.get(
            "/protected/dashboard",
            headers={"Authorization": "Bearer same-valid-token"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "message": "This dashboard is protected.",
        "user_id": "user-123",
    }
    get_user.assert_called_once_with("same-valid-token")


def test_signup_returns_only_safe_user_data() -> None:
    user = SimpleNamespace(
        id="user-123",
        email="person@example.com",
        created_at="2026-08-12T10:00:00Z",
    )
    with patch("app.main.supabase.auth.sign_up", return_value=SimpleNamespace(user=user)):
        response = client.post(
            "/auth/signup",
            json={"email": " person@example.com ", "password": "strong-password"},
        )

    assert response.status_code == 201
    assert response.json() == {
        "id": "user-123",
        "email": "person@example.com",
        "created_at": "2026-08-12T10:00:00Z",
    }


def test_signup_rejects_missing_or_empty_fields() -> None:
    for body in ({}, {"email": "", "password": "secret"}, {"email": "a@b.com", "password": "   "}):
        response = client.post("/auth/signup", json=body)
        assert response.status_code == 400
        assert response.json() == {"error": "Invalid request"}


def test_signup_normalizes_supabase_errors() -> None:
    error = AuthApiError("internal provider detail", 400, None)
    with patch("app.main.supabase.auth.sign_up", side_effect=error):
        response = client.post(
            "/auth/signup",
            json={"email": "person@example.com", "password": "strong-password"},
        )

    assert response.status_code == 400
    assert response.json() == {"error": "Unable to create account"}
    assert "provider" not in response.text


def test_login_returns_access_and_refresh_tokens() -> None:
    session = SimpleNamespace(
        access_token="access-token",
        refresh_token="refresh-token",
    )
    with patch(
        "app.main.supabase.auth.sign_in_with_password",
        return_value=SimpleNamespace(session=session),
    ):
        response = client.post(
            "/auth/login",
            json={"email": "person@example.com", "password": "strong-password"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
    }


def test_login_rejects_missing_or_empty_fields() -> None:
    for body in ({}, {"email": "", "password": "secret"}, {"email": "a@b.com", "password": ""}):
        response = client.post("/auth/login", json=body)
        assert response.status_code == 400
        assert response.json() == {"error": "Invalid request"}


def test_login_normalizes_invalid_credentials() -> None:
    error = AuthApiError("provider rejected credentials", 400, None)
    with patch("app.main.supabase.auth.sign_in_with_password", side_effect=error):
        response = client.post(
            "/auth/login",
            json={"email": "person@example.com", "password": "wrong-password"},
        )

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid email or password"}
    assert "provider" not in response.text
