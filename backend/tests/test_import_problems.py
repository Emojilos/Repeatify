"""Tests for scripts/import_problems.py."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.import_problems import (
    _get_existing_problem_keys,
    _get_existing_texts,
    _get_topic_map,
    _validate,
    import_problems,
)

# --- Validation tests ---


class TestValidation:
    def test_valid_part1_problem(self):
        item = {
            "task_number": 1,
            "problem_text": "Find x",
            "correct_answer": "5",
        }
        assert _validate(item, 0) == []

    def test_valid_part2_problem_no_answer(self):
        item = {
            "task_number": 13,
            "problem_text": "Prove that...",
        }
        assert _validate(item, 0) == []

    def test_missing_task_number(self):
        item = {"problem_text": "Find x"}
        errors = _validate(item, 0)
        assert any("task_number" in e for e in errors)

    def test_missing_problem_text(self):
        item = {"task_number": 1, "correct_answer": "5"}
        errors = _validate(item, 0)
        assert any("problem_text" in e for e in errors)

    def test_task_number_out_of_range(self):
        item = {"task_number": 20, "problem_text": "X"}
        errors = _validate(item, 0)
        assert any("вне диапазона" in e for e in errors)

    def test_part1_missing_correct_answer(self):
        item = {"task_number": 5, "problem_text": "Find x"}
        errors = _validate(item, 0)
        assert any("correct_answer" in e for e in errors)

    def test_invalid_difficulty(self):
        item = {
            "task_number": 1,
            "problem_text": "X",
            "correct_answer": "1",
            "difficulty": "impossible",
        }
        errors = _validate(item, 0)
        assert any("difficulty" in e for e in errors)

    def test_valid_difficulties(self):
        for diff in ("basic", "medium", "hard", "olympiad"):
            item = {
                "task_number": 1,
                "problem_text": "X",
                "correct_answer": "1",
                "difficulty": diff,
            }
            assert _validate(item, 0) == []


# --- Helper function tests ---


class TestGetTopicMap:
    def test_returns_mapping(self):
        client = MagicMock()
        chain = client.table.return_value.select.return_value
        chain.execute.return_value.data = [
            {"id": "uuid-1", "task_number": 1},
            {"id": "uuid-2", "task_number": 2},
        ]
        result = _get_topic_map(client)
        assert result == {1: "uuid-1", 2: "uuid-2"}
        client.table.assert_called_with("topics")


class TestGetExistingTexts:
    def test_returns_texts(self):
        client = MagicMock()
        chain = client.table.return_value.select.return_value
        chain = chain.in_.return_value
        chain.execute.return_value.data = [
            {"problem_text": "Text A"},
            {"problem_text": " Text B "},
        ]
        result = _get_existing_texts(client, {"uuid-1"})
        assert "Text A" in result
        assert "Text B" in result

    def test_empty_topic_ids(self):
        client = MagicMock()
        result = _get_existing_texts(client, set())
        assert result == set()
        client.table.assert_not_called()


class TestGetExistingProblemKeys:
    def test_returns_texts_and_hashes(self):
        client = MagicMock()
        chain = client.table.return_value.select.return_value.in_.return_value
        chain.execute.return_value.data = [
            {"problem_text": "Text A", "content_hash": "hash-a"},
            {"problem_text": " Text B ", "content_hash": None},
        ]

        texts, hashes = _get_existing_problem_keys(client, {"uuid-1"})

        assert texts == {"Text A", "Text B"}
        assert hashes == {"hash-a"}


# --- Import integration tests ---


def _make_client(
    topics: list[dict],
    existing_texts: list[dict] | None = None,
) -> MagicMock:
    """Build a mock Supabase client with topic map and existing texts."""
    client = MagicMock()
    sel = client.table.return_value.select.return_value
    sel.execute.return_value.data = topics
    in_chain = sel.in_.return_value
    in_chain.execute.return_value.data = existing_texts or []
    return client


def _write_json(items: list) -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    )
    json.dump(items, f)
    f.close()
    return f.name


class TestImportProblems:
    def test_add_new_problems(self):
        client = _make_client(
            [{"id": "topic-1", "task_number": 1}],
        )
        insert = client.table.return_value.insert
        insert.return_value.execute.return_value = MagicMock()

        path = _write_json([
            {
                "task_number": 1,
                "problem_text": "New problem",
                "correct_answer": "42",
            },
        ])
        import_problems(path, client=client)

        insert.assert_called_once()
        inserted = insert.call_args[0][0]
        assert inserted["problem_text"] == "New problem"
        assert inserted["topic_id"] == "topic-1"
        Path(path).unlink()

    def test_add_parser_fields(self):
        client = _make_client(
            [{"id": "topic-1", "task_number": 1}],
        )
        insert = client.table.return_value.insert
        insert.return_value.execute.return_value = MagicMock()

        path = _write_json([
            {
                "task_number": 1,
                "category": "№1. Планиметрия",
                "subcategory": "Авторские задачи №1",
                "problem_text": "Find x [image: graph]",
                "correct_answer": "42",
                "problem_images": ["data/raw/shkolkovo/images/task_1/a.svg"],
                "solution_images": [],
                "source_image_urls": ["https://example.test/a.svg"],
                "source": "shkolkovo",
                "source_id": "100",
                "source_url": "https://example.test/problem/100",
                "content_hash": "hash-100",
                "parse_status": "ok",
                "parse_errors": [],
            },
        ])

        import_problems(path, client=client)

        inserted = insert.call_args[0][0]
        assert inserted["category"] == "№1. Планиметрия"
        assert inserted["subcategory"] == "Авторские задачи №1"
        assert inserted["problem_images"] == [
            "data/raw/shkolkovo/images/task_1/a.svg",
        ]
        assert inserted["source_image_urls"] == ["https://example.test/a.svg"]
        assert inserted["source"] == "shkolkovo"
        assert inserted["source_id"] == "100"
        assert inserted["source_url"] == "https://example.test/problem/100"
        assert inserted["content_hash"] == "hash-100"
        assert inserted["parse_status"] == "ok"
        assert inserted["parse_errors"] == []
        Path(path).unlink()

    def test_skip_duplicates(self, capsys):
        client = _make_client(
            [{"id": "topic-1", "task_number": 1}],
            [{"problem_text": "Existing problem"}],
        )

        path = _write_json([
            {
                "task_number": 1,
                "problem_text": "Existing problem",
                "correct_answer": "1",
            },
        ])
        import_problems(path, client=client)

        client.table.return_value.insert.assert_not_called()
        output = capsys.readouterr().out
        assert "Пропущено (дубликаты): 1" in output
        Path(path).unlink()

    def test_skip_duplicates_by_content_hash(self, capsys):
        client = _make_client(
            [{"id": "topic-1", "task_number": 1}],
            [{"problem_text": "Different text", "content_hash": "same-hash"}],
        )

        path = _write_json([
            {
                "task_number": 1,
                "problem_text": "New text",
                "correct_answer": "1",
                "content_hash": "same-hash",
            },
        ])

        import_problems(path, client=client)

        client.table.return_value.insert.assert_not_called()
        output = capsys.readouterr().out
        assert "Пропущено (дубликаты): 1" in output
        Path(path).unlink()

    def test_validation_errors_exit(self, capsys):
        path = _write_json([
            {"problem_text": "No task number"},
        ])
        with pytest.raises(SystemExit):
            import_problems(path, client=MagicMock())
        output = capsys.readouterr().out
        assert "Ошибки валидации" in output
        Path(path).unlink()

    def test_missing_topic_exits(self):
        client = _make_client([])  # no topics

        path = _write_json([
            {
                "task_number": 1,
                "problem_text": "X",
                "correct_answer": "1",
            },
        ])
        with pytest.raises(SystemExit):
            import_problems(path, client=client)
        Path(path).unlink()

    def test_insert_error_counted(self, capsys):
        client = _make_client(
            [{"id": "topic-1", "task_number": 1}],
        )
        insert = client.table.return_value.insert
        insert.return_value.execute.side_effect = Exception(
            "DB error"
        )

        path = _write_json([
            {
                "task_number": 1,
                "problem_text": "Will fail",
                "correct_answer": "1",
            },
        ])
        import_problems(path, client=client)

        output = capsys.readouterr().out
        assert "Ошибки: 1" in output
        Path(path).unlink()

    def test_empty_file(self, capsys):
        path = _write_json([])
        import_problems(path, client=MagicMock())
        output = capsys.readouterr().out
        assert "нечего импортировать" in output
        Path(path).unlink()

    def test_parser_partial_part1_without_answer_is_skipped(self, capsys):
        client = _make_client(
            [{"id": "topic-1", "task_number": 1}],
        )

        path = _write_json([
            {
                "task_number": 1,
                "problem_text": "Displayable but no answer",
                "parse_status": "partial",
                "parse_errors": ["missing_correct_answer"],
            },
        ])

        import_problems(path, client=client)

        client.table.return_value.insert.assert_not_called()
        output = capsys.readouterr().out
        assert "Пропущено (неполные): 1" in output
        Path(path).unlink()

    def test_import_directory_reads_task_json_files(self, tmp_path):
        client = _make_client(
            [
                {"id": "topic-1", "task_number": 1},
                {"id": "topic-2", "task_number": 2},
            ],
        )
        insert = client.table.return_value.insert
        insert.return_value.execute.return_value = MagicMock()

        (tmp_path / "task_1.json").write_text(
            json.dumps([
                {
                    "task_number": 1,
                    "problem_text": "Task 1",
                    "correct_answer": "1",
                },
            ]),
            encoding="utf-8",
        )
        (tmp_path / "task_2.json").write_text(
            json.dumps([
                {
                    "task_number": 2,
                    "problem_text": "Task 2",
                    "correct_answer": "2",
                },
            ]),
            encoding="utf-8",
        )
        (tmp_path / "task_2_errors.json").write_text("[]", encoding="utf-8")

        import_problems(str(tmp_path), client=client)

        assert insert.call_count == 2

    def test_repeat_import_no_duplicates(self, capsys):
        """Run import twice: second run should skip all."""
        client = _make_client(
            [{"id": "topic-1", "task_number": 1}],
        )
        insert = client.table.return_value.insert
        insert.return_value.execute.return_value = MagicMock()

        items = [
            {
                "task_number": 1,
                "problem_text": "Unique problem",
                "correct_answer": "7",
            },
        ]
        path = _write_json(items)

        # First import
        import_problems(path, client=client)
        out1 = capsys.readouterr().out
        assert "Добавлено: 1" in out1

        # Now set existing texts to include it
        sel = client.table.return_value.select.return_value
        sel.in_.return_value.execute.return_value.data = [
            {"problem_text": "Unique problem"},
        ]

        # Second import
        import_problems(path, client=client)
        out2 = capsys.readouterr().out
        assert "Пропущено (дубликаты): 1" in out2
        Path(path).unlink()
