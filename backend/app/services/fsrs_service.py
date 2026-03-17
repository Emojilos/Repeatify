"""FSRS spaced repetition service wrapping the py-fsrs library.

Provides card lifecycle management (create, review, session building)
with Supabase persistence and exam-aware desired_retention tuning.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fsrs import Card as FSRSCard
from fsrs import Rating, Scheduler, State


def _map_state_to_db(state: State) -> str:
    """Map py-fsrs State enum to DB string."""
    return {
        State.Learning: "learning",
        State.Review: "review",
        State.Relearning: "relearning",
    }[state]


def _map_db_to_state(state_str: str) -> State:
    """Map DB string to py-fsrs State enum."""
    return {
        "new": State.Learning,
        "learning": State.Learning,
        "review": State.Review,
        "relearning": State.Relearning,
    }[state_str]


def _map_rating(rating: int) -> Rating:
    """Map integer rating (1-4) to py-fsrs Rating enum."""
    return {
        1: Rating.Again,
        2: Rating.Hard,
        3: Rating.Good,
        4: Rating.Easy,
    }[rating]


def adjust_desired_retention(exam_date: date | None) -> float:
    """Return desired_retention based on days until exam.

    >90 days  → 0.90 (standard)
    30-90 days → 0.85
    14-30 days → 0.80
    <14 days  → 0.75 (frequent reviews)
    No exam   → 0.90 (default)
    """
    if exam_date is None:
        return 0.90
    days_remaining = (exam_date - date.today()).days
    if days_remaining > 90:
        return 0.90
    if days_remaining >= 30:
        return 0.85
    if days_remaining >= 14:
        return 0.80
    return 0.75


def _build_scheduler(exam_date: date | None = None) -> Scheduler:
    """Build a Scheduler with desired_retention tuned to exam proximity."""
    retention = adjust_desired_retention(exam_date)
    return Scheduler(desired_retention=retention)


def _db_row_to_fsrs_card(row: dict) -> FSRSCard:
    """Reconstruct a py-fsrs Card from a DB row."""
    card = FSRSCard()
    card.card_id = hash(row.get("id", ""))
    card.state = _map_db_to_state(row.get("state", "new"))
    card.stability = row.get("stability")
    card.difficulty = row.get("difficulty")
    if row.get("last_review"):
        lr = row["last_review"]
        if isinstance(lr, str):
            lr = datetime.fromisoformat(lr)
        card.last_review = lr.replace(tzinfo=timezone.utc) if lr.tzinfo is None else lr
    else:
        card.last_review = None
    if row.get("due"):
        due = row["due"]
        if isinstance(due, str):
            due = datetime.fromisoformat(due)
        card.due = due.replace(tzinfo=timezone.utc) if due.tzinfo is None else due
    return card


def create_card(
    client,
    user_id: str,
    card_type: str = "problem",
    problem_id: str | None = None,
    prototype_id: str | None = None,
) -> dict:
    """Create a new FSRS card in the database.

    Returns the inserted row as a dict.
    """
    now = datetime.now(timezone.utc)
    card_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "card_type": card_type,
        "difficulty": 0,
        "stability": 0,
        "due": now.isoformat(),
        "last_review": None,
        "reps": 0,
        "lapses": 0,
        "state": "new",
        "scheduled_days": 0,
        "elapsed_days": 0,
    }
    if problem_id:
        card_data["problem_id"] = problem_id
    if prototype_id:
        card_data["prototype_id"] = prototype_id

    result = client.table("fsrs_cards").insert(card_data).execute()
    return result.data[0] if result.data else card_data


def review_card(
    client,
    card_id: str,
    rating: int,
    user_id: str,
    exam_date: date | None = None,
) -> dict:
    """Review a card with the given rating (1-4).

    Uses py-fsrs Scheduler to compute the next state, then persists
    the updated card to the database.

    Returns the updated DB row.
    """
    row_result = (
        client.table("fsrs_cards")
        .select("*")
        .eq("id", card_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not row_result.data:
        msg = f"Card {card_id} not found for user {user_id}"
        raise ValueError(msg)

    row = row_result.data[0]

    # If card is brand-new (never reviewed), start with a fresh Card
    is_new = (
        row.get("state") == "new"
        or (not row.get("stability") and not row.get("last_review"))
    )
    if is_new:
        fsrs_card = FSRSCard()
    else:
        fsrs_card = _db_row_to_fsrs_card(row)
    scheduler = _build_scheduler(exam_date)
    fsrs_rating = _map_rating(rating)

    updated_card, _log = scheduler.review_card(fsrs_card, fsrs_rating)

    now = datetime.now(timezone.utc)
    old_reps = row.get("reps", 0) or 0
    old_lapses = row.get("lapses", 0) or 0

    update_data = {
        "difficulty": (
            round(updated_card.difficulty, 4)
            if updated_card.difficulty
            else 0
        ),
        "stability": (
            round(updated_card.stability, 4)
            if updated_card.stability
            else 0
        ),
        "due": updated_card.due.isoformat(),
        "last_review": now.isoformat(),
        "state": _map_state_to_db(updated_card.state),
        "reps": old_reps + 1,
        "lapses": old_lapses + (1 if fsrs_rating == Rating.Again else 0),
    }

    if updated_card.last_review and row.get("last_review"):
        old_lr = row["last_review"]
        if isinstance(old_lr, str):
            old_lr = datetime.fromisoformat(old_lr)
        if old_lr.tzinfo is None:
            old_lr = old_lr.replace(tzinfo=timezone.utc)
        update_data["elapsed_days"] = (now - old_lr).days
    else:
        update_data["elapsed_days"] = 0

    if updated_card.due and now:
        update_data["scheduled_days"] = max(0, (updated_card.due - now).days)

    client.table("fsrs_cards").update(update_data).eq("id", card_id).execute()

    row.update(update_data)
    return row


def get_retrievability(
    row: dict,
    exam_date: date | None = None,
) -> float:
    """Compute current retrievability for a card DB row."""
    state_str = row.get("state", "new")
    if state_str == "new":
        return 0.0
    fsrs_card = _db_row_to_fsrs_card(row)
    if fsrs_card.stability is None:
        return 0.0
    scheduler = _build_scheduler(exam_date)
    return scheduler.get_card_retrievability(fsrs_card)


def get_session(
    client,
    user_id: str,
    max_cards: int = 20,
    exam_date: date | None = None,
) -> list[dict]:
    """Get a study session: due cards sorted by retrievability (low→high).

    Applies interleaving so no more than 2 consecutive cards share the
    same task_number.
    """
    now = datetime.now(timezone.utc).isoformat()

    result = (
        client.table("fsrs_cards")
        .select("*")
        .eq("user_id", user_id)
        .lte("due", now)
        .neq("state", "new")
        .order("due")
        .execute()
    )
    cards = result.data or []

    for card in cards:
        card["retrievability"] = get_retrievability(card, exam_date)

    cards.sort(key=lambda c: c["retrievability"])

    cards = _enrich_cards(client, cards)

    cards = _interleave(cards)

    return cards[:max_cards]


def _enrich_cards(client, cards: list[dict]) -> list[dict]:
    """Enrich cards with problem text, topic title, task_number."""
    problem_ids = [c["problem_id"] for c in cards if c.get("problem_id")]
    prototype_ids = [c["prototype_id"] for c in cards if c.get("prototype_id")]

    problems_map: dict[str, dict] = {}
    if problem_ids:
        p_result = (
            client.table("problems")
            .select("id,problem_text,problem_images,hints,topic_id,task_number,difficulty")
            .in_("id", problem_ids)
            .execute()
        )
        for p in p_result.data or []:
            problems_map[p["id"]] = p

    prototypes_map: dict[str, dict] = {}
    if prototype_ids:
        pr_result = (
            client.table("prototypes")
            .select("id,title,task_number,prototype_code")
            .in_("id", prototype_ids)
            .execute()
        )
        for pr in pr_result.data or []:
            prototypes_map[pr["id"]] = pr

    topic_ids = {p.get("topic_id") for p in problems_map.values() if p.get("topic_id")}
    topics_map: dict[str, str] = {}
    if topic_ids:
        t_result = (
            client.table("topics")
            .select("id,title")
            .in_("id", list(topic_ids))
            .execute()
        )
        for t in t_result.data or []:
            topics_map[t["id"]] = t["title"]

    for card in cards:
        prob = problems_map.get(card.get("problem_id", ""), {})
        proto = prototypes_map.get(card.get("prototype_id", ""), {})
        card["problem_text"] = prob.get("problem_text")
        card["problem_images"] = prob.get("problem_images")
        card["hints"] = prob.get("hints")
        card["task_number"] = prob.get("task_number") or proto.get("task_number")
        card["topic_title"] = topics_map.get(prob.get("topic_id", ""))
        card["difficulty_label"] = prob.get("difficulty")
        card["prototype_code"] = proto.get("prototype_code")
        card["prototype_title"] = proto.get("title")

    return cards


def _interleave(cards: list[dict]) -> list[dict]:
    """Reorder cards so no more than 2 consecutive share a task_number."""
    if len(cards) <= 2:
        return cards

    result: list[dict] = []
    remaining = list(cards)

    while remaining:
        placed = False
        for i, card in enumerate(remaining):
            tn = card.get("task_number")
            if len(result) < 2 or not (
                result[-1].get("task_number") == tn
                and result[-2].get("task_number") == tn
            ):
                result.append(remaining.pop(i))
                placed = True
                break
        if not placed:
            result.append(remaining.pop(0))

    return result
