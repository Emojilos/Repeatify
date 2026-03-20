"""Tests for the normalizer — HTML cleanup, LaTeX normalization, dedup, upload."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add tools directory to path so we can import the normalizer
_tools_dir = Path(__file__).resolve().parent.parent.parent / "tools" / "parsers"
sys.path.insert(0, str(_tools_dir))

from normalizer import (  # noqa: E402
    NormalizedProblem,
    NormalizerStats,
    clean_html_artifacts,
    clean_problem_text,
    compute_content_hash,
    link_prototypes,
    load_problems_from_json,
    normalize_latex,
    normalize_problems,
    upload_problems,
)

# ---------------------------------------------------------------------------
# clean_html_artifacts
# ---------------------------------------------------------------------------


class TestCleanHtmlArtifacts:
    def test_removes_html_entities(self) -> None:
        text = "2&nbsp;&gt;&nbsp;1 &amp; 3&lt;4"
        result = clean_html_artifacts(text)
        assert result == "2 > 1 & 3<4"

    def test_removes_stray_tags(self) -> None:
        text = "Найдите <b>значение</b> выражения <span class='x'>x+1</span>"
        result = clean_html_artifacts(text)
        assert result == "Найдите значение выражения x+1"

    def test_removes_br_tags(self) -> None:
        text = "Строка 1<br/>Строка 2<br>Строка 3"
        result = clean_html_artifacts(text)
        assert result == "Строка 1Строка 2Строка 3"

    def test_preserves_latex_angle_brackets(self) -> None:
        text = r"Если $\langle a, b \rangle > 0$, то"
        result = clean_html_artifacts(text)
        assert r"\langle" in result
        assert r"\rangle" in result

    def test_empty_string(self) -> None:
        assert clean_html_artifacts("") == ""

    def test_none_passthrough(self) -> None:
        # None should be returned as-is (falsy)
        assert clean_html_artifacts(None) is None  # type: ignore[arg-type]

    def test_numeric_entities(self) -> None:
        text = "символ &#8212; тире"
        result = clean_html_artifacts(text)
        assert "&#" not in result

    def test_cyrillic_entities(self) -> None:
        text = "Текст &laquo;в кавычках&raquo;"
        result = clean_html_artifacts(text)
        assert result == "Текст «в кавычках»"


# ---------------------------------------------------------------------------
# normalize_latex
# ---------------------------------------------------------------------------


class TestNormalizeLatex:
    def test_inline_math_conversion(self) -> None:
        text = r"Выражение \( x^2 + 1 \) равно"
        result = normalize_latex(text)
        assert result == "Выражение $x^2 + 1$ равно"

    def test_display_math_conversion(self) -> None:
        text = r"Формула: \[ \frac{a}{b} \]"
        result = normalize_latex(text)
        assert result == "Формула: $$\\frac{a}{b}$$"

    def test_already_standard_delimiters(self) -> None:
        text = "Inline $x$ and display $$y$$"
        result = normalize_latex(text)
        assert result == "Inline $x$ and display $$y$$"

    def test_collapses_spaces(self) -> None:
        text = "Много   пробелов   здесь"
        result = normalize_latex(text)
        assert result == "Много пробелов здесь"

    def test_collapses_blank_lines(self) -> None:
        text = "Абзац 1\n\n\n\nАбзац 2"
        result = normalize_latex(text)
        assert result == "Абзац 1\n\nАбзац 2"

    def test_empty_string(self) -> None:
        assert normalize_latex("") == ""

    def test_mixed_delimiters(self) -> None:
        text = r"Inline \( a \) and display \[ b \] and standard $c$"
        result = normalize_latex(text)
        assert result == "Inline $a$ and display $$b$$ and standard $c$"


# ---------------------------------------------------------------------------
# clean_problem_text (combined pipeline)
# ---------------------------------------------------------------------------


class TestCleanProblemText:
    def test_full_pipeline(self) -> None:
        text = r"<b>Задача</b>: Найдите &nbsp;\( \frac{1}{2} \)&nbsp;от числа"
        result = clean_problem_text(text)
        assert "<b>" not in result
        assert "&nbsp;" not in result
        assert "$\\frac{1}{2}$" in result

    def test_real_world_example(self) -> None:
        text = (
            '<p>Найдите значение выражения \\( \\frac{2x+1}{x-3} \\) '
            "при <em>x</em>&nbsp;=&nbsp;5.</p>"
        )
        result = clean_problem_text(text)
        assert "<p>" not in result
        assert "<em>" not in result
        assert "&nbsp;" not in result
        assert "$" in result


# ---------------------------------------------------------------------------
# compute_content_hash
# ---------------------------------------------------------------------------


class TestComputeContentHash:
    def test_deterministic(self) -> None:
        h1 = compute_content_hash("Найдите x")
        h2 = compute_content_hash("Найдите x")
        assert h1 == h2

    def test_whitespace_normalization(self) -> None:
        h1 = compute_content_hash("Найдите   x")
        h2 = compute_content_hash("Найдите x")
        assert h1 == h2

    def test_case_insensitive(self) -> None:
        h1 = compute_content_hash("Abc")
        h2 = compute_content_hash("abc")
        assert h1 == h2

    def test_sha256_length(self) -> None:
        h = compute_content_hash("test")
        assert len(h) == 64

    def test_different_text_different_hash(self) -> None:
        h1 = compute_content_hash("Задача 1")
        h2 = compute_content_hash("Задача 2")
        assert h1 != h2


# ---------------------------------------------------------------------------
# load_problems_from_json
# ---------------------------------------------------------------------------


class TestLoadProblemsFromJson:
    def test_load_single_file(self, tmp_path: Path) -> None:
        data = [{"task_number": 6, "problem_text": "test"}]
        f = tmp_path / "problems.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        result = load_problems_from_json([str(f)])
        assert len(result) == 1
        assert result[0]["task_number"] == 6

    def test_load_multiple_files(self, tmp_path: Path) -> None:
        for i, name in enumerate(["a.json", "b.json"]):
            f = tmp_path / name
            data = [{"task_number": i + 1, "problem_text": f"problem {i}"}]
            f.write_text(json.dumps(data), encoding="utf-8")
        result = load_problems_from_json([
            str(tmp_path / "a.json"), str(tmp_path / "b.json"),
        ])
        assert len(result) == 2

    def test_missing_file_skipped(self, tmp_path: Path) -> None:
        result = load_problems_from_json([str(tmp_path / "nonexistent.json")])
        assert result == []

    def test_single_dict_input(self, tmp_path: Path) -> None:
        f = tmp_path / "single.json"
        data = {"task_number": 1, "problem_text": "t"}
        f.write_text(json.dumps(data), encoding="utf-8")
        result = load_problems_from_json([str(f)])
        assert len(result) == 1


# ---------------------------------------------------------------------------
# normalize_problems
# ---------------------------------------------------------------------------


class TestNormalizeProblems:
    def test_basic_normalization(self) -> None:
        raw = [
            {
                "task_number": 6,
                "problem_text": "<b>Find</b> \\( x \\)",
                "correct_answer": "5",
                "source": "shkolkovo",
                "source_url": "https://example.com/1",
                "content_hash": "",
                "difficulty": "medium",
            }
        ]
        problems, stats = normalize_problems(raw, recompute_hashes=True)
        assert len(problems) == 1
        assert "<b>" not in problems[0].problem_text
        assert problems[0].content_hash  # non-empty
        assert stats.cleaned == 1

    def test_deduplication_within_batch(self) -> None:
        raw = [
            {"task_number": 6, "problem_text": "Same text", "content_hash": ""},
            {"task_number": 6, "problem_text": "Same text", "content_hash": ""},
        ]
        problems, stats = normalize_problems(raw, recompute_hashes=True)
        assert len(problems) == 1
        assert stats.duplicates_in_file == 1

    def test_skips_empty_text(self) -> None:
        raw = [
            {"task_number": 6, "problem_text": ""},
            {"task_number": None, "problem_text": "Valid text"},
        ]
        problems, stats = normalize_problems(raw)
        assert len(problems) == 0
        assert stats.failed == 2

    def test_preserves_existing_hash(self) -> None:
        raw = [
            {
                "task_number": 1,
                "problem_text": "test",
                "content_hash": "abc123",
            }
        ]
        problems, stats = normalize_problems(raw, recompute_hashes=False)
        assert problems[0].content_hash == "abc123"

    def test_recompute_hashes_flag(self) -> None:
        raw = [
            {
                "task_number": 1,
                "problem_text": "test",
                "content_hash": "abc123",
            }
        ]
        problems, stats = normalize_problems(raw, recompute_hashes=True)
        assert problems[0].content_hash != "abc123"
        assert len(problems[0].content_hash) == 64

    def test_answer_cleanup(self) -> None:
        raw = [
            {"task_number": 1, "problem_text": "task", "correct_answer": "  5.5  "},
        ]
        problems, _ = normalize_problems(raw, recompute_hashes=True)
        assert problems[0].correct_answer == "5.5"

    def test_empty_answer_becomes_none(self) -> None:
        raw = [
            {"task_number": 1, "problem_text": "task", "correct_answer": "  "},
        ]
        problems, _ = normalize_problems(raw, recompute_hashes=True)
        assert problems[0].correct_answer is None

    def test_invalid_images_reset(self) -> None:
        raw = [
            {"task_number": 1, "problem_text": "task", "problem_images": "not a list"},
        ]
        problems, _ = normalize_problems(raw, recompute_hashes=True)
        assert problems[0].problem_images == []


# ---------------------------------------------------------------------------
# link_prototypes
# ---------------------------------------------------------------------------


class TestLinkPrototypes:
    def test_single_prototype_assigned(self) -> None:
        problems = [NormalizedProblem(task_number=6, problem_text="test")]
        proto_map = {6: [{"id": "uuid-1", "prototype_code": "6.1", "order_index": 0}]}
        result = link_prototypes(problems, proto_map)
        assert result[0]._prototype_id == "uuid-1"  # type: ignore[attr-defined]

    def test_multiple_prototypes_picks_first(self) -> None:
        problems = [NormalizedProblem(task_number=6, problem_text="test")]
        proto_map = {
            6: [
                {"id": "uuid-1", "prototype_code": "6.1", "order_index": 0},
                {"id": "uuid-2", "prototype_code": "6.2", "order_index": 1},
            ]
        }
        result = link_prototypes(problems, proto_map)
        assert result[0]._prototype_id == "uuid-1"  # type: ignore[attr-defined]

    def test_no_prototype_sets_none(self) -> None:
        problems = [NormalizedProblem(task_number=99, problem_text="test")]
        result = link_prototypes(problems, {})
        assert result[0]._prototype_id is None  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# NormalizerStats
# ---------------------------------------------------------------------------


class TestNormalizerStats:
    def test_summary_format(self) -> None:
        stats = NormalizerStats(
            total_input=20,
            cleaned=18,
            duplicates_in_file=2,
            duplicates_in_db=3,
            no_topic=1,
            inserted=12,
            failed=0,
        )
        summary = stats.summary()
        assert "Added: 12" in summary
        assert "Skipped (duplicates): 5" in summary
        assert "Total input: 20" in summary


# ---------------------------------------------------------------------------
# upload_problems (mocked Supabase)
# ---------------------------------------------------------------------------


class TestUploadProblems:
    @patch.dict(
        "os.environ",
        {"SUPABASE_URL": "http://test", "SUPABASE_SERVICE_KEY": "key"},
    )
    @patch("supabase.create_client")
    def test_inserts_new_problem(self, mock_create: MagicMock) -> None:
        client = MagicMock()
        mock_create.return_value = client

        # Topic map
        topics_select = MagicMock()
        topic_data = [{"id": "topic-1", "task_number": 6}]
        topics_select.execute.return_value = MagicMock(data=topic_data)

        # Prototype map
        proto_select = MagicMock()
        proto_order = MagicMock()
        proto_data = [
            {
                "id": "proto-1",
                "task_number": 6,
                "prototype_code": "6.1",
                "order_index": 0,
            },
        ]
        proto_order.execute.return_value = MagicMock(data=proto_data)
        proto_select.order.return_value = proto_order

        def table_side_effect(name: str) -> MagicMock:
            mock = MagicMock()
            if name == "problems":
                # For fetch_existing_hashes: .select().not_.is_().execute()
                hash_chain = MagicMock()
                hash_chain.execute.return_value = MagicMock(data=[])
                not_mock = MagicMock()
                not_mock.is_.return_value = hash_chain
                select_mock = MagicMock()
                select_mock.not_ = not_mock
                mock.select.return_value = select_mock
                # For insert
                mock.insert.return_value.execute.return_value = MagicMock(data=[{}])
            elif name == "topics":
                mock.select.return_value = topics_select
            elif name == "prototypes":
                mock.select.return_value = proto_select
            return mock

        client.table.side_effect = table_side_effect

        problem = NormalizedProblem(
            task_number=6,
            problem_text="Find x",
            content_hash="unique_hash_123",
            source="shkolkovo",
        )
        stats = NormalizerStats(total_input=1, cleaned=1)
        result = upload_problems([problem], stats)
        assert result.inserted == 1

    @patch.dict(
        "os.environ",
        {"SUPABASE_URL": "http://test", "SUPABASE_SERVICE_KEY": "key"},
    )
    @patch("supabase.create_client")
    def test_skips_existing_hash(self, mock_create: MagicMock) -> None:
        client = MagicMock()
        mock_create.return_value = client

        def table_side_effect(name: str) -> MagicMock:
            mock = MagicMock()
            if name == "problems":
                hash_chain = MagicMock()
                existing = [{"content_hash": "existing_hash"}]
                hash_chain.execute.return_value = MagicMock(
                    data=existing,
                )
                not_mock = MagicMock()
                not_mock.is_.return_value = hash_chain
                select_mock = MagicMock()
                select_mock.not_ = not_mock
                mock.select.return_value = select_mock
            elif name == "topics":
                data = [{"id": "t1", "task_number": 6}]
                mock.select.return_value.execute.return_value = (
                    MagicMock(data=data)
                )
            elif name == "prototypes":
                chain = mock.select.return_value.order.return_value
                chain.execute.return_value = MagicMock(data=[])
            return mock

        client.table.side_effect = table_side_effect

        problem = NormalizedProblem(
            task_number=6,
            problem_text="test",
            content_hash="existing_hash",
            source="shkolkovo",
        )
        stats = NormalizerStats(total_input=1, cleaned=1)
        result = upload_problems([problem], stats)
        assert result.duplicates_in_db == 1
        assert result.inserted == 0

    def test_upload_without_env_vars(self) -> None:
        """Upload should return early if env vars are missing."""
        with patch.dict("os.environ", {}, clear=True):
            stats = NormalizerStats()
            result = upload_problems([], stats)
            assert result.inserted == 0


# ---------------------------------------------------------------------------
# Integration: load -> normalize -> stats
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_full_pipeline(self, tmp_path: Path) -> None:
        data = [
            {
                "task_number": 6,
                "problem_text": "<b>Найдите</b> значение \\( x^2 \\) при &nbsp;x=3",
                "correct_answer": "9",
                "problem_images": ["https://img.example.com/1.png"],
                "source": "shkolkovo",
                "source_url": "https://example.com/task/1",
                "content_hash": "",
                "difficulty": "medium",
            },
            {
                "task_number": 6,
                "problem_text": "<b>Найдите</b> значение \\( x^2 \\) при &nbsp;x=3",
                "correct_answer": "9",
                "problem_images": [],
                "source": "shkolkovo",
                "source_url": "https://example.com/task/2",
                "content_hash": "",
                "difficulty": "medium",
            },
            {
                "task_number": 7,
                "problem_text": "Другая задача \\[ \\frac{a}{b} \\]",
                "correct_answer": "2",
                "problem_images": [],
                "source": "math100",
                "source_url": "https://math100.ru/task/5",
                "content_hash": "",
                "difficulty": "medium",
            },
        ]
        f = tmp_path / "input.json"
        f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        raw = load_problems_from_json([str(f)])
        assert len(raw) == 3

        problems, stats = normalize_problems(raw, recompute_hashes=True)
        assert len(problems) == 2  # one deduped
        assert stats.duplicates_in_file == 1
        assert stats.cleaned == 3

        # Check cleaning was applied
        for p in problems:
            assert "<b>" not in p.problem_text
            assert "&nbsp;" not in p.problem_text
            assert "\\(" not in p.problem_text  # converted to $
            assert p.content_hash
            assert len(p.content_hash) == 64
