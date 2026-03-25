import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.core.config import settings

router = APIRouter(prefix="/api/storage", tags=["storage"])

_ALLOWED_CONTENT_TYPES = frozenset({
    "image/svg+xml",
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
})

_CACHE_CONTROL = "public, max-age=86400"


@router.get("/{path:path}")
async def proxy_storage(path: str) -> Response:
    """Proxy public Supabase Storage objects to avoid third-party blocking."""
    url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{path}"

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            upstream = await client.get(url)
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch from storage",
            )

    if upstream.status_code != 200:
        raise HTTPException(
            status_code=upstream.status_code,
            detail="Storage object not found",
        )

    content_type = upstream.headers.get("content-type", "application/octet-stream")
    media_type = content_type.split(";")[0].strip()

    if media_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File type not allowed",
        )

    return Response(
        content=upstream.content,
        media_type=content_type,
        headers={"Cache-Control": _CACHE_CONTROL},
    )
