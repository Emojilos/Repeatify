from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client
from app.models.auth import UpdateProfileRequest, UserProfile, UserStats

router = APIRouter(prefix="/api/users", tags=["users"])


def _row_to_profile(row: dict, email: str | None = None) -> UserProfile:
    return UserProfile(
        id=row["id"],
        email=email,
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


def _get_user_row(client, user_id: str) -> dict:
    result = (
        client.table("users")
        .select("*")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    if result.data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )
    return result.data


@router.get("/me", response_model=UserProfile)
async def get_me(user: dict = Depends(get_current_user)) -> UserProfile:
    """Return the current user's profile."""
    client = get_supabase_client()
    row = _get_user_row(client, user["id"])
    return _row_to_profile(row, email=user.get("email"))


@router.patch("/me", response_model=UserProfile)
async def update_me(
    body: UpdateProfileRequest,
    user: dict = Depends(get_current_user),
) -> UserProfile:
    """Update the current user's profile (display_name, exam_date, target_score)."""
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    # Convert date to ISO string for Supabase
    if "exam_date" in update_data and update_data["exam_date"] is not None:
        update_data["exam_date"] = update_data["exam_date"].isoformat()

    client = get_supabase_client()
    # Ensure user exists
    _get_user_row(client, user["id"])

    client.table("users").update(update_data).eq("id", user["id"]).execute()

    row = _get_user_row(client, user["id"])
    return _row_to_profile(row, email=user.get("email"))


@router.get("/me/stats", response_model=UserStats)
async def get_stats(user: dict = Depends(get_current_user)) -> UserStats:
    """Return aggregated stats for the current user."""
    client = get_supabase_client()
    row = _get_user_row(client, user["id"])

    # Count total distinct problems solved correctly
    attempts_result = (
        client.table("user_problem_attempts")
        .select("problem_id", count="exact")
        .eq("user_id", user["id"])
        .eq("is_correct", True)
        .execute()
    )
    total_solved = attempts_result.count if attempts_result.count is not None else 0

    return UserStats(
        current_xp=row.get("current_xp", 0),
        current_level=row.get("current_level", 1),
        current_streak=row.get("current_streak", 0),
        longest_streak=row.get("longest_streak", 0),
        total_problems_solved=total_solved,
    )
