"""v2.4.4 generated-package scanner with explicit diagnostics."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

import yaml

from .generated_package_v243 import GeneratedPackageManager as _V243GeneratedPackageManager


class GeneratedPackageManager(_V243GeneratedPackageManager):
    """Keep generated YAML discovery observable instead of failing silently."""

    def __init__(self, hass) -> None:
        super().__init__(hass)
        self._scan_diagnostics: dict[str, Any] = {
            "files": [],
            "records": 0,
            "errors": 0,
        }

    @property
    def scan_diagnostics(self) -> dict[str, Any]:
        return deepcopy(self._scan_diagnostics)

    def _scan_sync(self) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        files: list[dict[str, Any]] = []
        error_count = 0

        for path in self.paths():
            item: dict[str, Any] = {
                "file": str(path.relative_to(self.config_root)),
                "exists": path.is_file(),
                "records": 0,
                "ok": True,
                "error": None,
            }
            if not path.is_file():
                files.append(item)
                continue

            try:
                text = path.read_text(encoding="utf-8")
                value = yaml.safe_load(text)
                records = self._records_from(value, path)
                item["records"] = len(records)
                for record in records:
                    merged[str(record["entity_id"])] = record
            except Exception as err:  # noqa: BLE001
                item["ok"] = False
                item["error"] = f"{type(err).__name__}: {err}"
                error_count += 1
            files.append(item)

        self._scan_diagnostics = {
            "files": files,
            "records": len(merged),
            "errors": error_count,
        }
        return list(merged.values())
