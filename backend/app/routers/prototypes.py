from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client
from app.models.problems import ProblemListItem, ProblemListResponse
from app.models.prototype import (
    PrototypeListItem,
    PrototypeListResponse,
    PrototypeResponse,
)
from app.models.video import VideoResourceResponse

router = APIRouter(prefix="/api/prototypes", tags=["prototypes"])


def _row_to_list_item(row: dict) -> PrototypeListItem:
    return PrototypeListItem(
        id=row["id"],
        task_number=row["task_number"],
        prototype_code=row["prototype_code"],
        title=row["title"],
        description=row.get("description"),
        difficulty_within_task=row["difficulty_within_task"],
        estimated_study_minutes=row.get("estimated_study_minutes"),
        order_index=row.get("order_index"),
    )


def _row_to_detail(row: dict) -> PrototypeResponse:
    return PrototypeResponse(
        id=row["id"],
        task_number=row["task_number"],
        prototype_code=row["prototype_code"],
        title=row["title"],
        description=row.get("description"),
        difficulty_within_task=row["difficulty_within_task"],
        estimated_study_minutes=row.get("estimated_study_minutes"),
        theory_markdown=row.get("theory_markdown"),
        key_formulas=row.get("key_formulas"),
        solution_algorithm=row.get("solution_algorithm"),
        common_mistakes=row.get("common_mistakes"),
        related_prototypes=row.get("related_prototypes"),
        order_index=row.get("order_index"),
    )


def _row_to_problem(row: dict, max_points: int | None = None) -> ProblemListItem:
    return ProblemListItem(
        id=row["id"],
        topic_id=row["topic_id"],
        task_number=row["task_number"],
        difficulty=row["difficulty"],
        problem_text=row["problem_text"],
        problem_images=row.get("problem_images"),
        hints=row.get("hints"),
        source=row.get("source"),
        max_points=max_points,
        prototype_id=row.get("prototype_id"),
        source_url=row.get("source_url"),
        content_hash=row.get("content_hash"),
    )


@router.get("", response_model=PrototypeListResponse)
async def list_prototypes(
    task_number: int | None = Query(None, ge=1, le=19),
    _user: dict = Depends(get_current_user),
) -> PrototypeListResponse:
    """List all prototypes, optionally filtered by task_number."""
    client = get_supabase_client()

    query = client.table("prototypes").select("*", count="exact")

    if task_number is not None:
        query = query.eq("task_number", task_number)

    query = query.order("task_number").order("order_index")
    result = query.execute()

    items = [_row_to_list_item(r) for r in (result.data or [])]
    total = result.count if result.count is not None else len(items)

    return PrototypeListResponse(items=items, total=total)


@router.get("/{prototype_id}", response_model=PrototypeResponse)
async def get_prototype(
    prototype_id: str,
    _user: dict = Depends(get_current_user),
) -> PrototypeResponse:
    """Return full details for a single prototype."""
    client = get_supabase_client()

    result = (
        client.table("prototypes")
        .select("*")
        .eq("id", prototype_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prototype not found",
        )

    return _row_to_detail(result.data[0])


@router.get(
    "/{prototype_id}/videos",
    response_model=list[VideoResourceResponse],
)
async def get_prototype_videos(
    prototype_id: str,
    _user: dict = Depends(get_current_user),
) -> list[VideoResourceResponse]:
    """Return video resources linked to a prototype."""
    client = get_supabase_client()

    # Verify prototype exists
    proto_result = (
        client.table("prototypes")
        .select("id")
        .eq("id", prototype_id)
        .execute()
    )
    if not proto_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prototype not found",
        )

    result = (
        client.table("video_resources")
        .select("*")
        .eq("prototype_id", prototype_id)
        .order("order_index")
        .execute()
    )

    return [
        VideoResourceResponse(
            id=r["id"],
            prototype_id=r["prototype_id"],
            youtube_video_id=r["youtube_video_id"],
            title=r["title"],
            channel_name=r.get("channel_name"),
            duration_seconds=r.get("duration_seconds"),
            timestamps=r.get("timestamps"),
            order_index=r.get("order_index"),
        )
        for r in (result.data or [])
    ]


@router.get(
    "/{prototype_id}/problems",
    response_model=ProblemListResponse,
)
async def get_prototype_problems(
    prototype_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _user: dict = Depends(get_current_user),
) -> ProblemListResponse:
    """Return problems linked to a prototype with pagination."""
    client = get_supabase_client()

    # Verify prototype exists
    proto_result = (
        client.table("prototypes")
        .select("id,task_number")
        .eq("id", prototype_id)
        .execute()
    )
    if not proto_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prototype not found",
        )

    offset = (page - 1) * page_size
    result = (
        client.table("problems")
        .select("*", count="exact")
        .eq("prototype_id", prototype_id)
        .order("task_number")
        .range(offset, offset + page_size - 1)
        .execute()
    )

    problems = result.data or []
    total = result.count if result.count is not None else len(problems)

    # Enrich with max_points from topics
    topic_ids = list({p["topic_id"] for p in problems})
    points_map: dict[str, int] = {}
    if topic_ids:
        topics_result = (
            client.table("topics")
            .select("id,max_points")
            .in_("id", topic_ids)
            .execute()
        )
        for t in topics_result.data or []:
            points_map[t["id"]] = t["max_points"]

    items = [
        _row_to_problem(p, points_map.get(p["topic_id"]))
        for p in problems
    ]

    return ProblemListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
