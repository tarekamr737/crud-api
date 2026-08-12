import os

from supabase import Client, create_client
from supabase.client import ClientOptions


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
