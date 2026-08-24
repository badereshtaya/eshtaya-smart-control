"""Documentation loader for Eshtaya Smart Control.

The canonical human-edited documentation lives under ``docs/ar`` and ``docs/en``
in the GitHub repository. ``docs_bundle.json`` is a packaged mirror of those
Markdown files so HACS installations can render the exact same documentation
offline inside Home Assistant.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Final

_BUNDLE_PATH: Final = Path(__file__).with_name("docs_bundle.json")


def _load_documentation() -> dict[str, dict[str, str]]:
    try:
        raw = json.loads(_BUNDLE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise RuntimeError(f"Could not load packaged documentation: {err}") from err

    result: dict[str, dict[str, str]] = {"ar": {}, "en": {}}
    for language in ("ar", "en"):
        pages = raw.get(language)
        if not isinstance(pages, dict):
            raise RuntimeError(f"Documentation bundle is missing language: {language}")
        for slug, content in pages.items():
            if isinstance(slug, str) and isinstance(content, str) and content.strip():
                result[language][slug.strip().upper()] = content
    return result


DOCUMENTATION: Final = _load_documentation()
