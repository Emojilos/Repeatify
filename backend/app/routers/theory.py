"""Theory content and FIRe-flow progress endpoints.

GET  /api/topics/{topic_id}/theory        — theory content by FIRe stages
POST /api/topics/{topic_id}/fire-progress — mark a FIRe stage as completed
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client
from app.models.theory import (
    FireProgress,
    FireProgressRequest,
    FireProgressResponse,
    TheoryContentItem,
    TheoryResponse,
)
from app.services.fsrs_service import create_card as create_fsrs_card
from app.services.streak_service import record_activity
from app.services.xp_service import XP_FIRE_COMPLETE, award_xp

router = APIRouter(prefix="/api/topics", tags=["theory"])

# Valid FIRe stages and their corresponding DB columns
_STAGE_COLUMNS: dict[str, str] = {
    "framework": "fire_framework_completed",
    "inquiry": "fire_inquiry_completed",
    "relationships": "fire_relationships_completed",
    "elaboration": "fire_elaboration_completed",
}


@router.get("/{topic_id}/theory", response_model=TheoryResponse)
async def get_topic_theory(
    topic_id: str,
    user: dict = Depends(get_current_user),
) -> TheoryResponse:
    """Return theory content for a topic grouped by FIRe stages."""
    client = get_supabase_client()

    # Verify topic exists and get title
    topic_result = (
        client.table("topics")
        .select("id,title")
        .eq("id", topic_id)
        .execute()
    )
    if not topic_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    # Fetch theory content
    theory_result = (
        client.table("theory_content")
        .select("*")
        .eq("topic_id", topic_id)
        .order("order_index")
        .execute()
    )

    items = [
        TheoryContentItem(
            id=row["id"],
            topic_id=row["topic_id"],
            content_type=row["content_type"],
            content_markdown=row["content_markdown"],
            visual_assets=row.get("visual_assets") or [],
            order_index=row.get("order_index", 0),
        )
        for row in (theory_result.data or [])
    ]

    # Fetch user FIRe progress
    fire_progress: FireProgress | None = None
    prog_result = (
        client.table("user_topic_progress")
        .select("*")
        .eq("user_id", user["id"])
        .eq("topic_id", topic_id)
        .execute()
    )
    if prog_result.data:
        fire_progress = FireProgress(
            fire_framework_completed=prog_result.data[0].get(
                "fire_framework_completed", False
            ),
            fire_inquiry_completed=prog_result.data[0].get(
                "fire_inquiry_completed", False
            ),
            fire_relationships_completed=prog_result.data[0].get(
                "fire_relationships_completed", False
            ),
            fire_elaboration_completed=prog_result.data[0].get(
                "fire_elaboration_completed", False
            ),
            fire_completed_at=prog_result.data[0].get("fire_completed_at"),
        )

    return TheoryResponse(
        topic_id=topic_id,
        topic_title=topic_result.data[0]["title"],
        items=items,
        fire_progress=fire_progress,
    )


@router.post("/{topic_id}/fire-progress", response_model=FireProgressResponse)
async def update_fire_progress(
    topic_id: str,
    body: FireProgressRequest,
    user: dict = Depends(get_current_user),
) -> FireProgressResponse:
    """Mark a FIRe stage as completed. Awards XP when all 4 stages are done."""
    stage = body.stage
    if stage not in _STAGE_COLUMNS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid stage '{stage}'. "
                f"Must be one of: {', '.join(_STAGE_COLUMNS)}"
            ),
        )

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

    # Upsert user_topic_progress
    existing = (
        client.table("user_topic_progress")
        .select("*")
        .eq("user_id", user["id"])
        .eq("topic_id", topic_id)
        .execute()
    )

    col = _STAGE_COLUMNS[stage]

    if existing.data:
        # Update the stage column
        client.table("user_topic_progress").update(
            {col: True}
        ).eq("id", existing.data[0]["id"]).execute()

        # Re-read to check all stages
        progress_row = dict(existing.data[0])
        progress_row[col] = True
    else:
        # Create new progress row
        row_id = str(uuid.uuid4())
        new_row = {
            "id": row_id,
            "user_id": user["id"],
            "topic_id": topic_id,
            col: True,
        }
        client.table("user_topic_progress").insert(new_row).execute()
        progress_row = new_row

    # Check if all 4 stages are now completed
    all_done = all(
        progress_row.get(c, False) for c in _STAGE_COLUMNS.values()
    )

    xp_earned = 0
    new_level_reached: int | None = None
    fire_completed_at: str | None = progress_row.get("fire_completed_at")

    if all_done and fire_completed_at is None:
        # First time completing all stages — award XP
        now_str = datetime.now(timezone.utc).isoformat()
        client.table("user_topic_progress").update(
            {"fire_completed_at": now_str}
        ).eq("user_id", user["id"]).eq("topic_id", topic_id).execute()
        fire_completed_at = now_str

        xp_earned = XP_FIRE_COMPLETE
        _, new_level_reached = award_xp(client, user["id"], xp_earned)
        record_activity(client, user["id"], xp_earned=xp_earned)

        # Auto-create SRS cards for concept-type content in this topic
        _create_concept_cards(client, user["id"], topic_id)

    return FireProgressResponse(
        stage=stage,
        completed=True,
        fire_completed_at=fire_completed_at,
        all_stages_completed=all_done,
        xp_earned=xp_earned,
        new_level_reached=new_level_reached,
    )


def _create_concept_cards(client, user_id: str, topic_id: str) -> None:
    """Auto-create FSRS cards (card_type='concept') for prototypes of the topic.

    Creates one FSRS card per prototype linked to this topic's task_number.
    Falls back to problem-based cards if no prototypes exist.
    """
    # Get topic's task_number to find prototypes
    topic_result = (
        client.table("topics")
        .select("task_number")
        .eq("id", topic_id)
        .execute()
    )
    task_number = topic_result.data[0]["task_number"] if topic_result.data else None

    if task_number:
        # Find prototypes for this task_number
        proto_result = (
            client.table("prototypes")
            .select("id")
            .eq("task_number", task_number)
            .execute()
        )
        prototype_ids = [p["id"] for p in (proto_result.data or [])]

        if prototype_ids:
            # Check which prototypes already have FSRS cards
            existing = (
                client.table("fsrs_cards")
                .select("prototype_id")
                .eq("user_id", user_id)
                .in_("prototype_id", prototype_ids)
                .execute()
            )
            existing_proto_ids = {
                c["prototype_id"] for c in (existing.data or [])
            }

            for pid in prototype_ids:
                if pid not in existing_proto_ids:
                    create_fsrs_card(
                        client,
                        user_id,
                        card_type="concept",
                        prototype_id=pid,
                    )
            return

    # Fallback: create FSRS cards for problems in this topic
    problems_result = (
        client.table("problems")
        .select("id")
        .eq("topic_id", topic_id)
        .limit(5)
        .execute()
    )
    if not problems_result.data:
        return

    problem_ids = [p["id"] for p in problems_result.data]

    existing_cards = (
        client.table("fsrs_cards")
        .select("problem_id")
        .eq("user_id", user_id)
        .in_("problem_id", problem_ids)
        .execute()
    )
    existing_problem_ids = {
        c["problem_id"] for c in (existing_cards.data or [])
    }

    for pid in problem_ids:
        if pid not in existing_problem_ids:
            create_fsrs_card(
                client,
                user_id,
                card_type="concept",
                problem_id=pid,
            )
