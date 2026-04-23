"""Parse HTML strings into nested JSON-serializable dictionaries."""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, Comment, Doctype, NavigableString, Tag


def html_string_to_dict(html: str, *, parser: str = 'html.parser') -> dict[str, Any]:
    """Parse an HTML string into a nested dictionary tree.

    **Shape**

    - Each element is ``{"tag": str, "attrs": dict, "children": list}``.
    - ``attrs`` maps attribute names to ``str`` or ``list[str]`` (e.g. ``class``).
    - Text nodes appear as plain ``str`` entries inside ``children`` (never as dicts).

    **Whitespace**

    - Leading/trailing whitespace on text nodes is stripped.
    - Text nodes that are empty after stripping are omitted.

    **Comments and doctype**

    - HTML comments are omitted.
    - ``<!DOCTYPE ...>`` is omitted.

    **Root**

    - If the document has a single top-level element tag, that element's dict is
      returned (e.g. a full document yields the ``html`` node).
    - If there are multiple top-level nodes, or only non-tag top-level content,
      the return value is
      ``{"tag": "_fragment_", "attrs": {}, "children": [...]}`` where ``children``
      holds each top-level element dict and/or text strings in order.

    Args:
        html: HTML source as a string (decode bytes before calling).
        parser: BeautifulSoup parser name (default ``html.parser``).

    Returns:
        A dictionary representing the document (or a synthetic fragment root).

    """
    soup = BeautifulSoup(html, parser)
    top_level: list[dict[str, Any] | str] = []
    for element in soup.contents:
        if isinstance(element, (Doctype, Comment)):
            continue
        if isinstance(element, Tag):
            top_level.append(_tag_to_dict(element))
        elif isinstance(element, NavigableString):
            text = _text_from_navigable_string(element)
            if text is not None:
                top_level.append(text)

    if len(top_level) == 1 and isinstance(top_level[0], dict):
        return top_level[0]
    return {'tag': '_fragment_', 'attrs': {}, 'children': top_level}


def _text_from_navigable_string(node: NavigableString) -> str | None:
    stripped = str(node).strip()
    return stripped if stripped else None


def _normalize_attrs(tag: Tag) -> dict[str, Any]:
    attrs: dict[str, Any] = {}
    for key, value in tag.attrs.items():
        if isinstance(value, list):
            attrs[key] = value
        else:
            attrs[key] = str(value)
    return attrs


def _tag_to_dict(tag: Tag) -> dict[str, Any]:
    children: list[dict[str, Any] | str] = []
    for child in tag.children:
        if isinstance(child, Tag):
            children.append(_tag_to_dict(child))
        elif isinstance(child, NavigableString):
            if isinstance(child, Comment):
                continue
            text = _text_from_navigable_string(child)
            if text is not None:
                children.append(text)
    return {'tag': tag.name, 'attrs': _normalize_attrs(tag), 'children': children}
