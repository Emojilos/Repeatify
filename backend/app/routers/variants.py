"""Saved print variants endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/variants", tags=["variants"])


class SaveVariantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    task_number: int = Field(..., ge=1, le=19)
    problem_count: int = Field(..., ge=1, le=100)
    seed: int


class VariantResponse(BaseModel):
    id: str
    name: str
    task_number: int
    problem_count: int
    seed: int
    created_at: str


class VariantListResponse(BaseModel):
    items: list[VariantResponse]


@router.post("", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
async def save_variant(
    body: SaveVariantRequest,
    user: dict = Depends(get_current_user),
) -> VariantResponse:
    """Save a print variant to user's profile."""
    client = get_supabase_client()

    variant_id = str(uuid.uuid4())
    row = {
        "id": variant_id,
        "user_id": user["id"],
        "name": body.name,
        "task_number": body.task_number,
        "problem_count": body.problem_count,
        "seed": body.seed,
    }

    result = client.table("saved_variants").insert(row).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save variant",
        )

    saved = result.data[0]
    return VariantResponse(
        id=saved["id"],
        name=saved["name"],
        task_number=saved["task_number"],
        problem_count=saved["problem_count"],
        seed=saved["seed"],
        created_at=saved["created_at"],
    )


@router.get("", response_model=VariantListResponse)
async def list_variants(
    user: dict = Depends(get_current_user),
) -> VariantListResponse:
    """List all saved variants for the current user."""
    client = get_supabase_client()

    result = (
        client.table("saved_variants")
        .select("*")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )

    items = [
        VariantResponse(
            id=row["id"],
            name=row["name"],
            task_number=row["task_number"],
            problem_count=row["problem_count"],
            seed=row["seed"],
            created_at=row["created_at"],
        )
        for row in (result.data or [])
    ]

    return VariantListResponse(items=items)


@router.delete("/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    variant_id: str,
    user: dict = Depends(get_current_user),
) -> None:
    """Delete a saved variant."""
    client = get_supabase_client()

    result = (
        client.table("saved_variants")
        .delete()
        .eq("id", variant_id)
        .eq("user_id", user["id"])
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found",
        )
