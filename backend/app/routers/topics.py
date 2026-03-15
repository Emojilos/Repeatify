from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client
from app.models.topics import (
    TopicDetail,
    TopicListItem,
    TopicProgress,
    TopicRelationship,
)

router = APIRouter(prefix="/api/topics", tags=["topics"])

_optional_bearer = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
) -> dict | None:
    """Return the current user if a valid token is provided, else None."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def _build_progress(row: dict) -> TopicProgress:
    return TopicProgress(
        strength_score=row.get("strength_score", 0.0),
        fire_completed=row.get("fire_completed_at") is not None,
        fire_completed_at=row.get("fire_completed_at"),
        total_attempts=row.get("total_attempts", 0),
        correct_attempts=row.get("correct_attempts", 0),
        last_practiced_at=row.get("last_practiced_at"),
    )


def _row_to_topic(row: dict, progress: TopicProgress | None = None) -> TopicListItem:
    return TopicListItem(
        id=row["id"],
        task_number=row["task_number"],
        title=row["title"],
        description=row.get("description"),
        difficulty_level=row["difficulty_level"],
        max_points=row["max_points"],
        estimated_study_hours=row.get("estimated_study_hours"),
        order_index=row.get("order_index", 0),
        user_progress=progress,
    )


def _row_to_detail(row: dict, progress: TopicProgress | None = None) -> TopicDetail:
    return TopicDetail(
        id=row["id"],
        task_number=row["task_number"],
        title=row["title"],
        description=row.get("description"),
        difficulty_level=row["difficulty_level"],
        max_points=row["max_points"],
        estimated_study_hours=row.get("estimated_study_hours"),
        order_index=row.get("order_index", 0),
        parent_topic_id=row.get("parent_topic_id"),
        user_progress=progress,
    )


@router.get("", response_model=list[TopicListItem])
async def list_topics(
    user: dict | None = Depends(get_optional_user),
) -> list[TopicListItem]:
    """Return all topics sorted by task_number, with user progress if authenticated."""
    client = get_supabase_client()

    result = (
        client.table("topics")
        .select("*")
        .order("task_number")
        .execute()
    )
    topics = result.data or []

    # Load user progress if authenticated
    progress_map: dict[str, TopicProgress] = {}
    if user is not None:
        prog_result = (
            client.table("user_topic_progress")
            .select("*")
            .eq("user_id", user["id"])
            .execute()
        )
        for p in prog_result.data or []:
            progress_map[p["topic_id"]] = _build_progress(p)

    return [
        _row_to_topic(t, progress_map.get(t["id"]))
        for t in topics
    ]


@router.get("/{topic_id}", response_model=TopicDetail)
async def get_topic(
    topic_id: str,
    user: dict | None = Depends(get_optional_user),
) -> TopicDetail:
    """Return details for a single topic, with user progress if authenticated."""
    client = get_supabase_client()

    result = (
        client.table("topics")
        .select("*")
        .eq("id", topic_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    progress: TopicProgress | None = None
    if user is not None:
        prog_result = (
            client.table("user_topic_progress")
            .select("*")
            .eq("user_id", user["id"])
            .eq("topic_id", topic_id)
            .execute()
        )
        if prog_result.data:
            progress = _build_progress(prog_result.data[0])

    return _row_to_detail(result.data[0], progress)


@router.get("/{topic_id}/relationships", response_model=list[TopicRelationship])
async def get_topic_relationships(
    topic_id: str,
) -> list[TopicRelationship]:
    """Return relationships for a topic (both as source and target)."""
    client = get_supabase_client()

    # Verify topic exists
    topic_result = (
        client.table("topics")
        .select("id")
        .eq("id", topic_id)
        .execute()
    )
    if not topic_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    # Get relationships where this topic is the source
    result = (
        client.table("topic_relationships")
        .select("*")
        .eq("source_topic_id", topic_id)
        .execute()
    )
    relationships = result.data or []

    # Enrich with related topic info
    related_topic_ids = [r["target_topic_id"] for r in relationships]
    related_topics: dict[str, dict] = {}
    if related_topic_ids:
        topics_result = (
            client.table("topics")
            .select("*")
            .in_("id", related_topic_ids)
            .execute()
        )
        for t in topics_result.data or []:
            related_topics[t["id"]] = t

    output: list[TopicRelationship] = []
    for r in relationships:
        related = related_topics.get(r["target_topic_id"])
        output.append(
            TopicRelationship(
                id=r["id"],
                source_topic_id=r["source_topic_id"],
                target_topic_id=r["target_topic_id"],
                relationship_type=r["relationship_type"],
                description=r.get("description"),
                related_topic=_row_to_topic(related) if related else None,
            )
        )

    return output
