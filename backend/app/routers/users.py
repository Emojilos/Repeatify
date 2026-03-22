from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client
from app.models.auth import UpdateProfileRequest, UserProfile, UserStats
from app.services.study_plan_service import generate_plan, get_current_plan

router = APIRouter(prefix="/api/users", tags=["users"])


def _coalesce_int(value: object, default: int) -> int:
    return default if value is None else int(value)


def _row_to_profile(
    row: dict,
    email: str | None = None,
    has_diagnostic: bool = False,
    has_study_plan: bool = False,
) -> UserProfile:
    return UserProfile(
        id=row["id"],
        email=email,
        display_name=row.get("display_name"),
        exam_date=(
            str(row["exam_date"]) if row.get("exam_date") else None
        ),
        target_score=row.get("target_score"),
        hours_per_day=row.get("hours_per_day"),
        current_xp=_coalesce_int(row.get("current_xp"), 0),
        current_level=_coalesce_int(row.get("current_level"), 1),
        current_streak=_coalesce_int(row.get("current_streak"), 0),
        longest_streak=_coalesce_int(row.get("longest_streak"), 0),
        has_diagnostic=has_diagnostic,
        has_study_plan=has_study_plan,
    )


def _check_onboarding_status(client, user_id: str) -> tuple[bool, bool]:
    """Check onboarding flags without breaking profile fetch on missing tables."""
    has_diagnostic = False
    has_study_plan = False

    try:
        diag = (
            client.table("diagnostic_results")
            .select("id")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        has_diagnostic = bool(diag.data)
    except Exception as e:
        print(f"[users] diagnostic_results lookup skipped: {type(e).__name__}: {e}")

    try:
        plan = (
            client.table("user_study_plan")
            .select("id")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        has_study_plan = bool(plan.data)
    except Exception as e:
        print(f"[users] user_study_plan lookup skipped: {type(e).__name__}: {e}")

    return has_diagnostic, has_study_plan


def _get_user_row(client, user_id: str, auto_create: bool = True) -> dict:
    result = (
        client.table("users")
        .select("*")
        .eq("id", user_id)
        .execute()
    )
    print(f"[users] select user_id={user_id}, data={result.data}")
    if not result.data:
        if auto_create:
            try:
                insert_result = client.table("users").insert({"id": user_id}).execute()
                print(f"[users] insert result: {insert_result.data}")
            except Exception as e:
                print(f"[users] insert error: {type(e).__name__}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create user profile: {e}",
                )
            return _get_user_row(client, user_id, auto_create=False)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )
    return result.data[0]


@router.get("/me", response_model=UserProfile)
async def get_me(user: dict = Depends(get_current_user)) -> UserProfile:
    """Return the current user's profile."""
    client = get_supabase_client()
    row = _get_user_row(client, user["id"])
    has_diagnostic, has_study_plan = _check_onboarding_status(client, user["id"])
    return _row_to_profile(
        row,
        email=user.get("email"),
        has_diagnostic=has_diagnostic,
        has_study_plan=has_study_plan,
    )


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

    plan_fields = {"target_score", "exam_date", "hours_per_day"}
    plan_fields_changed = bool(plan_fields & update_data.keys())

    client.table("users").update(update_data).eq("id", user["id"]).execute()

    # Auto-recalculate study plan if plan-related fields changed
    if plan_fields_changed:
        existing_plan = get_current_plan(client, user["id"])
        if existing_plan:
            row = _get_user_row(client, user["id"])
            target = row.get("target_score") or existing_plan.get("target_score", 70)
            generate_plan(
                client,
                user["id"],
                target_score=target,
            )

    row = _get_user_row(client, user["id"])
    has_diagnostic, has_study_plan = _check_onboarding_status(client, user["id"])
    return _row_to_profile(
        row,
        email=user.get("email"),
        has_diagnostic=has_diagnostic,
        has_study_plan=has_study_plan,
    )


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
        current_xp=_coalesce_int(row.get("current_xp"), 0),
        current_level=_coalesce_int(row.get("current_level"), 1),
        current_streak=_coalesce_int(row.get("current_streak"), 0),
        longest_streak=_coalesce_int(row.get("longest_streak"), 0),
        total_problems_solved=total_solved,
    )
