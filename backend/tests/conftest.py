import pytest


@pytest.fixture(autouse=True)
def _show_problems_by_default(monkeypatch):
    monkeypatch.setenv("SHOW_PROBLEMS", "true")
