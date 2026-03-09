from supabase import Client, create_client

from app.core.config import settings

_client: Client | None = None


def get_supabase_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return _client


async def verify_connection() -> bool:
    """Verify Supabase connection by querying the topics table."""
    try:
        client = get_supabase_client()
        client.table("topics").select("id").limit(1).execute()
        return True
    except Exception:
        return False
