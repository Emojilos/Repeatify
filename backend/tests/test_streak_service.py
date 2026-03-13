"""Unit tests for the streak service."""

from datetime import date
from unittest.mock import MagicMock

from app.services.streak_service import record_activity


def _eq2_maybe(data):
    """Mock chain: .eq().eq().maybe_single().execute()."""
    m = MagicMock()
    (
        m.eq.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute.return_value
    ) = MagicMock(data=data)
    return m


def _mock_client(
    *,
    existing_activity=None,
    user_data=None,
):
    """Build a mock Supabase client."""
    client = MagicMock()
    tables: dict[str, MagicMock] = {}

    def table(name):
        if name not in tables:
            tables[name] = MagicMock()
        return tables[name]

    client.table = table

    # user_daily_activity default: today check
    tables["user_daily_activity"] = MagicMock()
    tables["user_daily_activity"].select.return_value = (
        _eq2_maybe(existing_activity)
    )
    tables["user_daily_activity"].insert.return_value \
        .execute.return_value = MagicMock(data=None)
    tables["user_daily_activity"].update.return_value \
        .eq.return_value.execute.return_value = MagicMock(
        data=None,
    )

    # users table
    udata = user_data or {
        "current_streak": 0,
        "longest_streak": 0,
    }
    tables["users"] = MagicMock()
    (
        tables["users"].select.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute.return_value
    ) = MagicMock(data=udata)
    tables["users"].update.return_value \
        .eq.return_value.execute.return_value = MagicMock(
        data=None,
    )

    return client, tables


def _setup_selects(tables, yesterday_data):
    """1st select → None (today), 2nd → yesterday_data."""
    count = [0]

    def side_effect(*_a, **_kw):
        count[0] += 1
        if count[0] == 1:
            return _eq2_maybe(None)
        return _eq2_maybe(yesterday_data)

    tables["user_daily_activity"].select.side_effect = (
        side_effect
    )


class TestRecordActivityExisting:
    """When today's activity row already exists."""

    def test_updates_existing_row(self):
        existing = {
            "id": "act1",
            "user_id": "u1",
            "activity_date": "2026-03-13",
            "problems_solved": 3,
            "sessions_completed": 1,
            "xp_earned": 30,
            "streak_maintained": True,
        }
        client, tables = _mock_client(
            existing_activity=existing,
        )

        result = record_activity(
            client, "u1",
            problems_solved=1,
            xp_earned=10,
            today=date(2026, 3, 13),
        )

        assert result == existing
        act = tables["user_daily_activity"]
        act.update.assert_called_once()
        args = act.update.call_args[0][0]
        assert args["problems_solved"] == 4
        assert args["xp_earned"] == 40

    def test_does_not_update_streak(self):
        existing = {
            "id": "act1",
            "user_id": "u1",
            "activity_date": "2026-03-13",
            "problems_solved": 1,
            "sessions_completed": 0,
            "xp_earned": 10,
            "streak_maintained": True,
        }
        client, tables = _mock_client(
            existing_activity=existing,
        )

        record_activity(
            client, "u1",
            problems_solved=1,
            today=date(2026, 3, 13),
        )

        tables["users"].update.assert_not_called()


class TestRecordActivityNew:
    """When no activity row exists for today."""

    def test_creates_new_row(self):
        client, tables = _mock_client(
            user_data={
                "current_streak": 5,
                "longest_streak": 10,
            },
        )
        _setup_selects(tables, {"id": "y1"})

        result = record_activity(
            client, "u1",
            problems_solved=1,
            xp_earned=10,
            today=date(2026, 3, 13),
        )

        assert result["problems_solved"] == 1
        assert result["xp_earned"] == 10
        assert result["streak_maintained"] is True
        act = tables["user_daily_activity"]
        act.insert.assert_called_once()

    def test_streak_continues_with_yesterday(self):
        client, tables = _mock_client(
            user_data={
                "current_streak": 5,
                "longest_streak": 10,
            },
        )
        _setup_selects(tables, {"id": "y1"})

        record_activity(
            client, "u1",
            problems_solved=1,
            today=date(2026, 3, 13),
        )

        tables["users"].update.assert_called_once()
        args = tables["users"].update.call_args[0][0]
        assert args["current_streak"] == 6

    def test_streak_resets_without_yesterday(self):
        client, tables = _mock_client(
            user_data={
                "current_streak": 5,
                "longest_streak": 10,
            },
        )
        _setup_selects(tables, None)

        record_activity(
            client, "u1",
            problems_solved=1,
            today=date(2026, 3, 13),
        )

        tables["users"].update.assert_called_once()
        args = tables["users"].update.call_args[0][0]
        assert args["current_streak"] == 1

    def test_longest_streak_updated_when_exceeded(self):
        client, tables = _mock_client(
            user_data={
                "current_streak": 10,
                "longest_streak": 10,
            },
        )
        _setup_selects(tables, {"id": "y1"})

        record_activity(
            client, "u1",
            problems_solved=1,
            today=date(2026, 3, 13),
        )

        args = tables["users"].update.call_args[0][0]
        assert args["current_streak"] == 11
        assert args["longest_streak"] == 11

    def test_longest_streak_not_updated_when_lower(self):
        client, tables = _mock_client(
            user_data={
                "current_streak": 3,
                "longest_streak": 20,
            },
        )
        _setup_selects(tables, {"id": "y1"})

        record_activity(
            client, "u1",
            problems_solved=1,
            today=date(2026, 3, 13),
        )

        args = tables["users"].update.call_args[0][0]
        assert args["current_streak"] == 4
        assert "longest_streak" not in args


class TestRecordActivitySessionTracking:
    def test_sessions_incremented(self):
        existing = {
            "id": "act1",
            "user_id": "u1",
            "activity_date": "2026-03-13",
            "problems_solved": 0,
            "sessions_completed": 2,
            "xp_earned": 0,
            "streak_maintained": True,
        }
        client, tables = _mock_client(
            existing_activity=existing,
        )

        record_activity(
            client, "u1",
            sessions_completed=1,
            today=date(2026, 3, 13),
        )

        act = tables["user_daily_activity"]
        args = act.update.call_args[0][0]
        assert args["sessions_completed"] == 3
