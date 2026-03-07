"""Topic interleaver: ensures no topic appears more than N times consecutively."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


def interleave(cards: list[dict[str, Any]], max_consecutive: int = 2) -> list[dict[str, Any]]:
    """Reorder cards so no topic_id appears > max_consecutive times in a row.

    Uses a greedy consecutive-count tracker:
    - When the last topic's run reaches max_consecutive, it is excluded from
      eligible choices until a different topic is picked.
    - Among eligible topics the one with the most remaining cards is chosen
      to minimise the chance of topics running out.

    Args:
        cards: Flat list of card dicts, each with a "topic_id" key.
        max_consecutive: Maximum allowed consecutive cards from the same topic.

    Returns:
        Reordered list satisfying the consecutive constraint (best-effort).
        When it is impossible to satisfy (only one topic left), the constraint
        is relaxed gracefully.
    """
    if not cards:
        return []

    # Group cards into per-topic queues (None = "no topic" bucket)
    buckets: dict[str | None, deque[dict[str, Any]]] = defaultdict(deque)
    for card in cards:
        buckets[card.get("topic_id")].append(card)

    result: list[dict[str, Any]] = []
    last_topic: str | None = None
    consecutive_count: int = 0

    while any(buckets.values()):
        if consecutive_count >= max_consecutive:
            # Must switch: exclude the topic we've been on
            eligible = [tid for tid, dq in buckets.items() if dq and tid != last_topic]
            if not eligible:
                # Can't switch — relax constraint (best-effort)
                eligible = [tid for tid, dq in buckets.items() if dq]
        else:
            eligible = [tid for tid, dq in buckets.items() if dq]

        if not eligible:
            break

        # Greedy: pick the topic with the most remaining cards
        chosen = max(eligible, key=lambda t: len(buckets[t]))
        card = buckets[chosen].popleft()
        if not buckets[chosen]:
            del buckets[chosen]

        result.append(card)

        if chosen == last_topic:
            consecutive_count += 1
        else:
            consecutive_count = 1
        last_topic = chosen

    return result
