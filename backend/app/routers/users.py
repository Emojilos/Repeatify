from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client
from app.models.auth import UserProfile

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
async def get_me(user: dict = Depends(get_current_user)) -> UserProfile:
    """Return the current user's profile."""
    client = get_supabase_client()
    result = (
        client.table("users")
        .select("*")
        .eq("id", user["id"])
        .maybe_single()
        .execute()
    )

    if result.data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    row = result.data
    return UserProfile(
        id=row["id"],
        email=user.get("email"),
        display_name=row.get("display_name"),
        exam_date=(
            str(row["exam_date"]) if row.get("exam_date") else None
        ),
        target_score=row.get("target_score"),
        current_xp=row.get("current_xp", 0),
        current_level=row.get("current_level", 1),
        current_streak=row.get("current_streak", 0),
        longest_streak=row.get("longest_streak", 0),
    )
