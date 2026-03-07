"""FIRe propagator: credit/penalty propagation through the knowledge graph.

Credit propagation (rating >= 3):
  When a user answers a card from topic B correctly:
  1. For each prerequisite A of B (edge B→A with weight w):
     a. transferred = credit * w
     b. If transferred < THRESHOLD: stop branch.
     c. Add `transferred` to user_topic_mastery.implicit_credit for A.
     d. While implicit_credit >= 1.0:
        - Extend due_dates of A's review-state cards (interval boost).
        - implicit_credit -= 1.0
     e. Recurse upstream: propagate_credit(A, transferred)

Penalty propagation (rating == 1):
  When a user fails on a card from topic A:
  1. For each dependent B of A (edge A→B with weight w):
     a. transferred = penalty * w
     b. If transferred < THRESHOLD: stop branch.
     c. Accelerate due_dates of B's cards (pull forward in time).
     d. Recurse downstream: propagate_penalty_up(B, transferred)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from supabase import Client

from app.core.fire.graph import KnowledgeGraph

# Minimum credit amount to continue recursion along a branch.
_PROPAGATION_THRESHOLD = 0.3

# Interval boost factor: extend due_date by 10% of current interval (min 1 day).
_BOOST_FACTOR = 0.10
_BOOST_MIN_DAYS = 1

# Penalty pull-forward factor: move due_date earlier by 20% of current interval (min 1 day).
_PENALTY_FACTOR = 0.20
_PENALTY_MIN_DAYS = 1


def propagate_credit(
    sb: Client,
    user_id: str,
    topic_id: str,
    credit: float,
    graph: KnowledgeGraph,
    *,
    _visited: set[str] | None = None,
) -> None:
    """Propagate implicit review credit upstream through prerequisite topics.

    Args:
        sb: Supabase service-role client.
        user_id: The user who answered correctly.
        topic_id: Topic of the reviewed card (starting point of propagation).
        credit: Credit amount to distribute (1.0 for a single correct answer).
        graph: Knowledge graph for traversal.
        _visited: Internal cycle guard; do not pass from call sites.
    """
    if _visited is None:
        _visited = set()

    for edge in graph.get_prerequisites(topic_id):
        prereq_id = edge.topic_id

        # Prevent cycles (the graph should be a DAG, but defensive check)
        if prereq_id in _visited:
            continue

        transferred = credit * edge.weight
        if transferred < _PROPAGATION_THRESHOLD:
            # Attenuated to below threshold — stop this branch
            continue

        _visited.add(prereq_id)

        # Accumulate implicit credit in user_topic_mastery
        new_credit = _add_implicit_credit(sb, user_id, prereq_id, transferred)

        # Consume full credit units: each unit = one interval boost
        if new_credit >= 1.0:
            consumed = int(new_credit)  # number of full units
            for _ in range(consumed):
                _boost_topic_intervals(sb, user_id, prereq_id)
            remainder = new_credit - consumed
            _set_implicit_credit(sb, user_id, prereq_id, remainder)

        # Recurse further upstream with the attenuated credit
        propagate_credit(sb, user_id, prereq_id, transferred, graph, _visited=_visited)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _add_implicit_credit(sb: Client, user_id: str, topic_id: str, amount: float) -> float:
    """Add `amount` to implicit_credit in user_topic_mastery; return new total."""
    resp = (
        sb.table("user_topic_mastery")
        .select("id, implicit_credit")
        .eq("user_id", user_id)
        .eq("topic_id", topic_id)
        .maybe_single()
        .execute()
    )
    existing: dict[str, Any] = resp.data or {}
    current = float(existing.get("implicit_credit") or 0.0)
    new_total = current + amount

    if existing.get("id"):
        sb.table("user_topic_mastery").update({"implicit_credit": new_total}).eq(
            "id", existing["id"]
        ).execute()
    else:
        sb.table("user_topic_mastery").insert(
            {
                "user_id": user_id,
                "topic_id": topic_id,
                "implicit_credit": new_total,
            }
        ).execute()

    return new_total


def _set_implicit_credit(sb: Client, user_id: str, topic_id: str, value: float) -> None:
    """Overwrite implicit_credit to `value` (used after consuming whole units)."""
    sb.table("user_topic_mastery").update({"implicit_credit": value}).match(
        {"user_id": user_id, "topic_id": topic_id}
    ).execute()


def _boost_topic_intervals(sb: Client, user_id: str, topic_id: str) -> None:
    """Extend due_dates for all review-state cards in a topic for a user.

    Only cards that are not yet overdue are boosted (no point pushing already
    overdue cards further into the future — they should be reviewed first).
    """
    now = datetime.now(timezone.utc)

    # Fetch card IDs belonging to this topic
    cards_resp = sb.table("cards").select("id").eq("topic_id", topic_id).execute()
    card_ids = [row["id"] for row in (cards_resp.data or [])]
    if not card_ids:
        return

    # Fetch user progress rows for these cards that are in 'review' state
    prog_resp = (
        sb.table("user_card_progress")
        .select("id, due_date, interval_days")
        .eq("user_id", user_id)
        .eq("fsrs_state", "review")
        .in_("card_id", card_ids)
        .execute()
    )

    for row in prog_resp.data or []:
        due = row.get("due_date")
        if due is None:
            continue

        if isinstance(due, str):
            due = datetime.fromisoformat(due)
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)

        # Skip cards that are already overdue — reviewing them takes priority
        if due < now:
            continue

        interval = float(row.get("interval_days") or 1)
        boost_days = max(_BOOST_MIN_DAYS, round(interval * _BOOST_FACTOR))
        new_due = due + timedelta(days=boost_days)
        new_interval = interval + boost_days

        sb.table("user_card_progress").update(
            {
                "due_date": new_due.isoformat(),
                "interval_days": new_interval,
            }
        ).eq("id", row["id"]).execute()


# ---------------------------------------------------------------------------
# Penalty propagation (downstream: prerequisite → dependents)
# ---------------------------------------------------------------------------


def propagate_penalty_up(
    sb: Client,
    user_id: str,
    topic_id: str,
    penalty: float,
    graph: KnowledgeGraph,
    *,
    _visited: set[str] | None = None,
) -> None:
    """Propagate review penalty downstream to dependent topics after a wrong answer.

    When a user answers a card from topic A with rating=1 (Again), it signals a
    gap in foundational knowledge.  Topics that depend on A (its dependents) are
    likely to be reviewed sooner than scheduled, so we pull their due_dates
    forward in time proportionally to the edge weight.

    Args:
        sb: Supabase service-role client.
        user_id: The user who answered incorrectly.
        topic_id: Topic of the failed card (starting point of penalty propagation).
        penalty: Penalty strength (1.0 for a single wrong answer).
        graph: Knowledge graph for traversal.
        _visited: Internal cycle guard; do not pass from call sites.
    """
    if _visited is None:
        _visited = set()

    for edge in graph.get_dependents(topic_id):
        dep_id = edge.topic_id

        if dep_id in _visited:
            continue

        transferred = penalty * edge.weight
        if transferred < _PROPAGATION_THRESHOLD:
            continue

        _visited.add(dep_id)

        # Pull due_dates of dependent topic's cards forward
        _accelerate_topic_cards(sb, user_id, dep_id)

        # Recurse further downstream with attenuated penalty
        propagate_penalty_up(sb, user_id, dep_id, transferred, graph, _visited=_visited)


def _accelerate_topic_cards(sb: Client, user_id: str, topic_id: str) -> None:
    """Pull due_dates earlier for learning/review-state cards in a topic.

    Only cards that are not yet overdue are accelerated (already-overdue cards
    will naturally appear in the next session anyway).
    """
    now = datetime.now(timezone.utc)

    cards_resp = sb.table("cards").select("id").eq("topic_id", topic_id).execute()
    card_ids = [row["id"] for row in (cards_resp.data or [])]
    if not card_ids:
        return

    prog_resp = (
        sb.table("user_card_progress")
        .select("id, due_date, interval_days, fsrs_state")
        .eq("user_id", user_id)
        .in_("card_id", card_ids)
        .execute()
    )

    for row in prog_resp.data or []:
        state = row.get("fsrs_state") or ""
        if state not in ("learning", "review"):
            continue

        due = row.get("due_date")
        if due is None:
            continue
        if isinstance(due, str):
            due = datetime.fromisoformat(due)
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)

        # Only accelerate cards that are not yet overdue
        if due <= now:
            continue

        interval = float(row.get("interval_days") or 1)
        pull_days = max(_PENALTY_MIN_DAYS, round(interval * _PENALTY_FACTOR))
        new_due = due - timedelta(days=pull_days)
        # Never pull before now (card would be immediately overdue — that's fine,
        # but don't push into the past beyond what's meaningful)
        new_due = max(new_due, now)

        sb.table("user_card_progress").update(
            {"due_date": new_due.isoformat()}
        ).eq("id", row["id"]).execute()
