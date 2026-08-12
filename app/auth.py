import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client
from supabase.client import ClientOptions
from supabase_auth.errors import AuthError
from supabase_auth.types import User


def required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


supabase: Client = create_client(
    required_setting("SUPABASE_URL"),
    required_setting("SUPABASE_KEY"),
    options=ClientOptions(auto_refresh_token=False, persist_session=False),
)

bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials
        or any(character.isspace() for character in credentials.credentials)
    ):
        raise unauthorized()

    try:
        response = supabase.auth.get_user(credentials.credentials)
    except AuthError:
        raise unauthorized() from None

    if response.user is None:
        raise unauthorized()
    return response.user
