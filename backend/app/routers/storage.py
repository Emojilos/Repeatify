import mimetypes
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, Response

from app.core.config import settings

router = APIRouter(prefix="/api/storage", tags=["storage"])

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_RAW_SHKOLKOVO_IMAGE_ROOT = _PROJECT_ROOT / "data" / "raw" / "shkolkovo" / "images"

_ALLOWED_CONTENT_TYPES = frozenset({
    "image/svg+xml",
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
})

_CACHE_CONTROL = "public, max-age=86400"


@router.get("/raw-shkolkovo/{image_path:path}")
async def proxy_raw_shkolkovo_image(image_path: str) -> FileResponse:
    """Serve local parser image artifacts in development/import previews."""
    file_path = _resolve_raw_shkolkovo_image(image_path)
    media_type = _media_type_for_file(file_path)

    return FileResponse(
        file_path,
        media_type=media_type,
        headers={"Cache-Control": _CACHE_CONTROL},
    )


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


def _resolve_raw_shkolkovo_image(image_path: str) -> Path:
    relative_path = Path(image_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image path",
        )

    file_path = (_RAW_SHKOLKOVO_IMAGE_ROOT / relative_path).resolve()
    try:
        file_path.relative_to(_RAW_SHKOLKOVO_IMAGE_ROOT.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image path",
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return file_path


def _media_type_for_file(file_path: Path) -> str:
    media_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    if media_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File type not allowed",
        )
    return media_type
