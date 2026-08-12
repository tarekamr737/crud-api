import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from supabase_auth.errors import AuthApiError

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")

from app.auth import get_current_user


dependency_app = FastAPI()


@dependency_app.get("/protected")
def protected(user: object = Depends(get_current_user)) -> dict[str, str]:
    return {"id": str(user.id)}


client = TestClient(dependency_app)


def test_dependency_passes_explicit_bearer_token_to_supabase() -> None:
    user = SimpleNamespace(id="user-123")
    with patch(
        "app.auth.supabase.auth.get_user",
        return_value=SimpleNamespace(user=user),
    ) as get_user:
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 200
    assert response.json() == {"id": "user-123"}
    get_user.assert_called_once_with("valid-token")


def test_dependency_rejects_missing_and_malformed_authorization() -> None:
    headers = (
        {},
        {"Authorization": "Basic token"},
        {"Authorization": "Bearer"},
        {"Authorization": "Bearer token with spaces"},
    )
    with patch("app.auth.supabase.auth.get_user") as get_user:
        for request_headers in headers:
            response = client.get("/protected", headers=request_headers)
            assert response.status_code == 401
            assert response.json() == {
                "detail": "Invalid or expired authentication token"
            }
            assert response.headers["www-authenticate"] == "Bearer"

    get_user.assert_not_called()


@pytest.mark.parametrize("token", ["expired-token", "tampered-token"])
def test_dependency_rejects_invalid_or_expired_token(token: str) -> None:
    error = AuthApiError("provider JWT detail", 401, None)
    with patch("app.auth.supabase.auth.get_user", side_effect=error):
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired authentication token"}
    assert "provider" not in response.text
