"""Offline documentation loader for Eshtaya Smart Control.

The canonical human-edited Markdown lives under ``docs/ar`` and ``docs/en`` at
repository root. The exact same blobs are packaged under this integration's
``docs`` directory so HACS installations render the same text offline.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

_DOCS_ROOT: Final = Path(__file__).with_name("docs")
_FILENAME_TO_SLUG: Final = {
    "SECURITY_AND_BACKUP": "SECURITY_BACKUP",
}


def _load_documentation() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {"ar": {}, "en": {}}
    for language in ("ar", "en"):
        language_dir = _DOCS_ROOT / language
        if not language_dir.is_dir():
            raise RuntimeError(f"Packaged documentation directory is missing: {language_dir}")
        for path in sorted(language_dir.glob("*.md")):
            content = path.read_text(encoding="utf-8")
            if not content.strip():
                continue
            raw_slug = path.stem.strip().upper()
            slug = _FILENAME_TO_SLUG.get(raw_slug, raw_slug)
            result[language][slug] = content
    return result


DOCUMENTATION: Final = _load_documentation()
