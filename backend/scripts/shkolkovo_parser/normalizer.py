"""Text and LaTeX normalization for Shkolkovo problem pages."""

from __future__ import annotations

import re
from collections.abc import Iterable

from bs4 import BeautifulSoup, NavigableString, Tag

SERVICE_SELECTORS = (
    "button",
    "nav",
    "script",
    "style",
    "noscript",
    "mjx-container",
    ".MathJax",
    ".mathjax",
    ".ui-panel",
    ".show-answer",
    ".answer",
    ".correct-answer",
    "[aria-hidden='true']",
)

INLINE_MATH_CLASSES = {"math-inline", "tex-inline", "latex-inline"}
DISPLAY_MATH_CLASSES = {"math-display", "tex-display", "latex-display"}

HTML_PATTERN = re.compile(r"<[a-zA-Z][^>]*>")
DISPLAY_MATH_PATTERN = re.compile(r"\$\$\s*(.*?)\s*\$\$", re.DOTALL)
INLINE_MATH_PATTERN = re.compile(r"(?<!\$)\$\s*([^$]+?)\s*\$(?!\$)", re.DOTALL)


def normalize_problem_html(html: str) -> str:
    """Normalize the first problem text block found in a full HTML document."""
    soup = BeautifulSoup(html, "lxml")
    problem_node = soup.select_one(".problem-text")
    if isinstance(problem_node, Tag):
        return normalize_problem_text(problem_node)
    return normalize_problem_text(soup)


def normalize_problem_text(value: str | Tag) -> str:
    """Return readable Markdown/LaTeX text from HTML or already-normalized text."""
    if isinstance(value, Tag):
        return _normalize_tag(value)
    if not HTML_PATTERN.search(value):
        return _normalize_text(value)

    soup = BeautifulSoup(value, "lxml")
    problem_node = soup.select_one(".problem-text")
    if isinstance(problem_node, Tag):
        return _normalize_tag(problem_node)
    return _normalize_tag(soup)


def normalize_plain_text(value: str | Tag) -> str:
    """Normalize non-problem text without interpreting math-specific markup."""
    if isinstance(value, Tag):
        text = value.get_text(" ", strip=True)
    else:
        text = BeautifulSoup(value, "lxml").get_text(" ", strip=True)
    return _normalize_text(text)


def _normalize_tag(value: Tag) -> str:
    soup = BeautifulSoup(str(value), "lxml")
    root = soup.select_one(".problem-text") or soup

    _replace_math_nodes(root)
    _remove_service_nodes(root)
    return _normalize_text(root.get_text(" ", strip=True))


def _replace_math_nodes(root: Tag) -> None:
    for node in tuple(root.find_all(_is_math_node)):
        if not isinstance(node, Tag):
            continue

        tex = _tex_from_node(node)
        if not tex:
            continue

        node.replace_with(NavigableString(_format_latex(tex, _is_display_math(node))))


def _remove_service_nodes(root: Tag) -> None:
    for node in root.select(",".join(SERVICE_SELECTORS)):
        node.decompose()


def _is_math_node(node: Tag) -> bool:
    if not isinstance(node, Tag):
        return False
    if _tex_from_node(node):
        return True
    return node.name == "script" and _script_math_type(node) is not None


def _tex_from_node(node: Tag) -> str | None:
    data_tex = node.get("data-tex")
    if isinstance(data_tex, str) and data_tex.strip():
        return data_tex.strip()

    script_math_type = _script_math_type(node)
    if script_math_type is not None:
        return node.get_text(" ", strip=True)

    annotation = node.select_one("annotation[encoding='application/x-tex']")
    if isinstance(annotation, Tag):
        annotation_text = annotation.get_text(" ", strip=True)
        if annotation_text:
            return annotation_text

    return None


def _script_math_type(node: Tag) -> str | None:
    if node.name != "script":
        return None
    script_type = node.get("type")
    if not isinstance(script_type, str):
        return None
    script_type = script_type.strip().lower()
    if script_type.startswith("math/tex"):
        return script_type
    return None


def _is_display_math(node: Tag) -> bool:
    class_names = _class_names(node)
    if class_names & DISPLAY_MATH_CLASSES:
        return True
    if class_names & INLINE_MATH_CLASSES:
        return False

    script_math_type = _script_math_type(node)
    return script_math_type is not None and "mode=display" in script_math_type


def _class_names(node: Tag) -> set[str]:
    classes = node.get("class")
    if not isinstance(classes, Iterable) or isinstance(classes, str):
        return set()
    return {class_name for class_name in classes if isinstance(class_name, str)}


def _format_latex(tex: str, display: bool) -> str:
    tex = _normalize_latex_source(tex)
    if display:
        return f" $$ {tex} $$ "
    return f" ${tex}$ "


def _normalize_latex_source(tex: str) -> str:
    tex = tex.strip()
    if tex.startswith("$$") and tex.endswith("$$"):
        tex = tex[2:-2]
    elif tex.startswith("$") and tex.endswith("$"):
        tex = tex[1:-1]
    return " ".join(tex.strip().split())


def _normalize_text(text: str) -> str:
    text = DISPLAY_MATH_PATTERN.sub(lambda match: f"$${match.group(1).strip()}$$", text)
    text = INLINE_MATH_PATTERN.sub(lambda match: f"${match.group(1).strip()}$", text)
    text = " ".join(text.split())
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([(])\s+", r"\1", text)
    text = re.sub(r"\s+([)])", r"\1", text)
    return text.strip()
