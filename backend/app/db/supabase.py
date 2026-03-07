"""Supabase service-role client for the FastAPI backend."""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.config import settings


@lru_cache(maxsize=1)
def _make_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_supabase_client() -> Client:
    """FastAPI dependency: return the shared Supabase service-role client."""
    return _make_client()
