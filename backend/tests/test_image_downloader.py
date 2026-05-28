"""Tests for deterministic Shkolkovo problem image downloads."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import httpx

from scripts.shkolkovo_parser.exporter import (
    build_dataset_record,
    export_task_files,
)
from scripts.shkolkovo_parser.image_downloader import (
    download_problem_images,
    image_download_failed_error,
    image_filename_for_url,
)
from scripts.shkolkovo_parser.validator import (
    IMAGE_DOWNLOAD_FAILED,
    ParseStatus,
    ValidatedProblemRecord,
)


def _validated_record(
    source_image_urls: tuple[str, ...] = (
        "https://3.shkolkovo.online/media/problems/100601/triangle.png",
    ),
) -> ValidatedProblemRecord:
    return ValidatedProblemRecord(
        task_number=6,
        problem_text="В треугольнике ABC найдите AB.",
        correct_answer="10",
        source_url="https://3.shkolkovo.online/problem/100601?SubjectId=1",
        source_id="100601",
        category="Планиметрия",
        subcategory="Треугольники",
        parse_status=cast(ParseStatus, "ok"),
        parse_errors=(),
        source_image_urls=source_image_urls,
    )


def test_image_downloader_saves_problem_image_with_deterministic_name(
    tmp_path: Path,
) -> None:
    image_url = "https://3.shkolkovo.online/media/problems/100601/triangle.png"
    image_bytes = b"\x89PNG\r\nfixture"
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                content=image_bytes,
                headers={"content-type": "image/png"},
                request=request,
            ),
        ),
    )

    result = download_problem_images(
        _validated_record((image_url,)),
        client=client,
        data_dir=tmp_path / "data" / "raw" / "shkolkovo",
        repository_root_path=tmp_path,
    )

    expected_filename = image_filename_for_url(image_url, source_id="100601")
    expected_relative_path = (
        f"data/raw/shkolkovo/images/task_6/{expected_filename}"
    )

    assert result.record.problem_images == (expected_relative_path,)
    assert result.downloads[0].source_url == image_url
    assert result.downloads[0].repository_relative_path == expected_relative_path
    assert result.downloads[0].local_path.read_bytes() == image_bytes
    assert result.downloads[0].bytes_written == len(image_bytes)

    dataset_record = build_dataset_record(result.record)
    assert dataset_record["problem_images"] == [expected_relative_path]
    assert dataset_record["source_image_urls"] == [image_url]
    assert dataset_record["solution_images"] == []


def test_image_downloader_repeat_run_reuses_same_path_without_extra_file(
    tmp_path: Path,
) -> None:
    image_url = "https://static.shkolkovo.online/problems/100601/angle.webp"
    image_bytes = b"RIFFfixtureWEBP"
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                content=image_bytes,
                headers={"content-type": "image/webp"},
                request=request,
            ),
        ),
    )
    record = _validated_record((image_url, image_url))
    data_dir = tmp_path / "data" / "raw" / "shkolkovo"

    first = download_problem_images(
        record,
        client=client,
        data_dir=data_dir,
        repository_root_path=tmp_path,
    )
    second = download_problem_images(
        record,
        client=client,
        data_dir=data_dir,
        repository_root_path=tmp_path,
    )

    files = sorted((data_dir / "images" / "task_6").iterdir())
    assert first.record.problem_images == second.record.problem_images
    assert len(first.downloads) == 1
    assert len(second.downloads) == 1
    assert len(files) == 1
    assert files[0].read_bytes() == image_bytes


def test_export_task_files_writes_downloaded_problem_image_paths(
    tmp_path: Path,
) -> None:
    image_url = "https://3.shkolkovo.online/media/problems/100601/triangle.png"
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                content=b"png",
                headers={"content-type": "image/png"},
                request=request,
            ),
        ),
    )
    downloaded = download_problem_images(
        _validated_record((image_url,)),
        client=client,
        data_dir=tmp_path / "data" / "raw" / "shkolkovo",
        repository_root_path=tmp_path,
    )

    export = export_task_files(
        task_number=6,
        records=(downloaded.record,),
        output_dir=tmp_path / "data" / "raw" / "shkolkovo",
    )

    records = json.loads(export.output_file.read_text(encoding="utf-8"))
    assert records[0]["problem_images"] == list(downloaded.record.problem_images)
    assert records[0]["source_image_urls"] == [image_url]


def test_image_downloader_keeps_record_partial_when_one_image_fails(
    tmp_path: Path,
) -> None:
    ok_url = "https://3.shkolkovo.online/media/problems/100601/triangle.png"
    failed_url = "https://3.shkolkovo.online/media/problems/100601/missing.png"

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == ok_url:
            return httpx.Response(
                200,
                content=b"png",
                headers={"content-type": "image/png"},
                request=request,
            )
        return httpx.Response(404, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    result = download_problem_images(
        _validated_record((ok_url, failed_url)),
        client=client,
        data_dir=tmp_path / "data" / "raw" / "shkolkovo",
        repository_root_path=tmp_path,
    )

    expected_error = image_download_failed_error(failed_url)

    assert len(result.downloads) == 1
    assert result.downloads[0].source_url == ok_url
    assert len(result.failures) == 1
    assert result.failures[0].source_url == failed_url
    assert result.failures[0].parse_error == expected_error
    assert result.record.parse_status == "partial"
    assert result.record.parse_errors == (expected_error,)
    assert result.record.source_image_urls == (ok_url, failed_url)
    assert result.record.problem_images == (
        result.downloads[0].repository_relative_path,
    )
    assert expected_error.startswith(IMAGE_DOWNLOAD_FAILED)
    assert failed_url in expected_error


def test_partial_image_download_record_stays_in_dataset_export(
    tmp_path: Path,
) -> None:
    ok_url = "https://3.shkolkovo.online/media/problems/100601/triangle.png"
    failed_url = "https://3.shkolkovo.online/media/problems/100601/missing.png"
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                404 if str(request.url) == failed_url else 200,
                content=b"png",
                headers={"content-type": "image/png"},
                request=request,
            ),
        ),
    )
    downloaded = download_problem_images(
        _validated_record((ok_url, failed_url)),
        client=client,
        data_dir=tmp_path / "data" / "raw" / "shkolkovo",
        repository_root_path=tmp_path,
    )

    export = export_task_files(
        task_number=6,
        records=(downloaded.record,),
        errors=(),
        output_dir=tmp_path / "data" / "raw" / "shkolkovo",
    )

    records = json.loads(export.output_file.read_text(encoding="utf-8"))
    errors = json.loads(export.errors_file.read_text(encoding="utf-8"))
    assert export.records_written == 1
    assert export.errors_written == 0
    assert records[0]["parse_status"] == "partial"
    assert records[0]["source_image_urls"] == [ok_url, failed_url]
    assert records[0]["parse_errors"] == [
        image_download_failed_error(failed_url),
    ]
    assert errors == []


def test_image_downloader_rejects_non_http_urls_without_request(
    tmp_path: Path,
) -> None:
    requests_seen = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal requests_seen
        requests_seen += 1
        return httpx.Response(200, content=b"png")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    file_url = "file:///tmp/problem.png"
    javascript_url = "javascript:alert(1)"

    result = download_problem_images(
        _validated_record((file_url, javascript_url)),
        client=client,
        data_dir=tmp_path / "data" / "raw" / "shkolkovo",
        repository_root_path=tmp_path,
    )

    assert requests_seen == 0
    assert result.downloads == ()
    assert [failure.source_url for failure in result.failures] == [
        file_url,
        javascript_url,
    ]
    assert result.record.parse_status == "partial"
    assert result.record.problem_images == ()
    assert result.record.parse_errors == (
        image_download_failed_error(file_url),
        image_download_failed_error(javascript_url),
    )


def test_image_downloader_sanitizes_traversal_like_source_id(
    tmp_path: Path,
) -> None:
    image_url = "https://3.shkolkovo.online/media/problems/100601/triangle.png"
    record = _validated_record((image_url,))
    record = replace(record, source_id="../100601")
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                content=b"png",
                headers={"content-type": "image/png"},
                request=request,
            ),
        ),
    )
    data_dir = tmp_path / "data" / "raw" / "shkolkovo"

    result = download_problem_images(
        record,
        client=client,
        data_dir=data_dir,
        repository_root_path=tmp_path,
    )

    assert len(result.downloads) == 1
    assert result.downloads[0].local_path.parent == data_dir / "images" / "task_6"
    assert ".." not in result.downloads[0].local_path.name
    assert "/" not in result.downloads[0].local_path.name
    assert not (data_dir / "images" / "100601").exists()
