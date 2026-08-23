"""Observable migration coordinator for Eshtaya Smart Control.

Adds a user-facing migration timeline, sanitized before/after counters, rollback
metadata and a downloadable support report on top of the transactional migration
engine in :mod:`migration`.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, VERSION
from .entity_control.const import STORAGE_KEY as ENTITY_STORAGE_KEY
from .migration import LegacyMigrationCoordinator


MIGRATION_REPORT_SCHEMA = 1

STEP_ORDER = (
    "detect",
    "backup",
    "copy",
    "quiesce",
    "runtime_start",
    "validate",
    "remove_legacy",
    "reconcile",
    "hacs_cleanup",
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _count_entity_rules(data: Any) -> int:
    if not isinstance(data, dict):
        return 0
    rules = data.get("entity_rules")
    return len(rules) if isinstance(rules, dict) else 0


class MigrationCenterCoordinator(LegacyMigrationCoordinator):
    """Transactional migration with observable progress for System Center."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(hass)

    def _ensure_steps(self) -> dict[str, dict[str, Any]]:
        steps = self.state.setdefault("steps", {})
        for step in STEP_ORDER:
            steps.setdefault(
                step,
                {
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "message": None,
                },
            )
        return steps

    async def _save_state(self) -> None:
        await self._store.async_save(self.state)

    async def _set_step(
        self,
        step: str,
        status: str,
        *,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        steps = self._ensure_steps()
        item = steps.setdefault(step, {})
        now = _utcnow()
        if status == "running" and not item.get("started_at"):
            item["started_at"] = now
        if status in {"completed", "failed", "skipped", "rolled_back"}:
            item.setdefault("started_at", now)
            item["completed_at"] = now
        item["status"] = status
        if message is not None:
            item["message"] = message
        if details is not None:
            item["details"] = deepcopy(details)
        self.state["last_updated_at"] = now
        await self._save_state()

    async def _hydrate_completed_v11_state(self) -> None:
        """Upgrade an already-completed v1.1 migration into the v1.2 timeline."""
        self._ensure_steps()
        if not self.state.get("completed"):
            return
        if self.state.get("phase") == "no_legacy" or not self.state.get("legacy_found"):
            await self._set_step("detect", "completed", message="No legacy integrations or storage detected")
            for step in STEP_ORDER[1:]:
                item = self.state["steps"].get(step) or {}
                if item.get("status") == "pending":
                    await self._set_step(step, "skipped", message="No migration required")
            return

        expected = deepcopy(self.state.get("expected") or {})
        default_messages = {
            "detect": "Legacy Eshtaya integrations detected",
            "backup": "Independent migration backup created before cutover",
            "copy": "Legacy storage copied into the unified storage namespace where required",
            "quiesce": "Legacy config entries disabled before the new runtime started",
            "runtime_start": "Unified runtime started successfully",
            "validate": "Migration validation passed",
            "remove_legacy": "Legacy Home Assistant config entries removed after successful validation",
            "reconcile": "New Smart Group runtime reconciled hidden-member ownership",
        }
        for step, message in default_messages.items():
            item = self.state["steps"].get(step) or {}
            if item.get("status") == "pending":
                await self._set_step(step, "completed", message=message)
        cleanup = self.state.get("hacs_cleanup") or {}
        if cleanup:
            await self.async_mark_hacs_cleanup(cleanup)
        elif (self.state["steps"].get("hacs_cleanup") or {}).get("status") == "pending":
            await self._set_step(
                "hacs_cleanup",
                "skipped",
                message="HACS cleanup status was not recorded by the previous version",
            )
        self.state.setdefault(
            "counts",
            {"before": expected, "after_start": expected, "validated": expected},
        )
        self.state.setdefault(
            "rollback",
            {
                "available": True,
                "used": False,
                "backup_store": self.state.get("backup_store"),
            },
        )
        await self._save_state()

    async def async_prepare(self) -> dict[str, Any]:
        saved = await self._store.async_load()
        if isinstance(saved, dict):
            self.state = saved
            self._ensure_steps()
            if saved.get("completed"):
                await self._hydrate_completed_v11_state()
                return deepcopy(self.state)

        await self._set_step("detect", "running", message="Scanning legacy integrations and storage")
        try:
            state = await super().async_prepare()
            self.state = state
            self._ensure_steps()
        except Exception as err:
            await self._set_step("detect", "failed", message=str(err))
            raise

        if not self.state.get("legacy_found"):
            await self._set_step("detect", "completed", message="No legacy integrations or storage detected")
            for step in STEP_ORDER[1:]:
                await self._set_step(step, "skipped", message="No migration required")
            return deepcopy(self.state)

        await self._set_step(
            "detect",
            "completed",
            message="Legacy Eshtaya integrations detected",
            details={
                "entries": len(self.state.get("entries") or []),
                "expected": deepcopy(self.state.get("expected") or {}),
            },
        )
        await self._set_step(
            "backup",
            "completed",
            message="Independent migration backup created before cutover",
            details={"store": self.state.get("backup_store")},
        )
        await self._set_step(
            "copy",
            "completed",
            message="Legacy storage copied into the unified storage namespace where required",
            details=deepcopy(self.state.get("copied") or {}),
        )
        self.state["counts"] = {
            "before": deepcopy(self.state.get("expected") or {}),
            "after_start": {},
            "validated": {},
        }
        self.state["rollback"] = {
            "available": True,
            "used": False,
            "backup_store": self.state.get("backup_store"),
        }
        await self._save_state()
        return deepcopy(self.state)

    async def async_quiesce_legacy(self) -> dict[str, Any]:
        await self._set_step("quiesce", "running", message="Stopping legacy control engines safely")
        try:
            state = await super().async_quiesce_legacy()
            self.state = state
            self._ensure_steps()
            await self._set_step(
                "quiesce",
                "completed",
                message="Legacy config entries disabled before the new runtime started",
                details={"disabled_entries": len(self.state.get("disabled_by_migration") or [])},
            )
            return deepcopy(self.state)
        except Exception as err:
            await self._set_step("quiesce", "failed", message=str(err))
            raise

    async def async_mark_runtime_started(self, runtime: dict[str, Any] | None) -> None:
        """Record that the unified runtime started and expose safe after-copy counts."""
        await self._set_step("runtime_start", "running", message="Starting unified Entity and Multi-Way runtimes")
        runtime = runtime or {}
        entity_data = await Store(self.hass, 1, ENTITY_STORAGE_KEY).async_load()
        multi_store = runtime.get("store")
        smart_store = runtime.get("smart_store")
        actual = {
            "entity_rules": _count_entity_rules(entity_data),
            "multiway_groups": len(multi_store.groups()) if multi_store else 0,
            "smart_groups": len(smart_store.groups()) if smart_store else 0,
        }
        counts = self.state.setdefault("counts", {})
        counts["after_start"] = actual
        await self._set_step(
            "runtime_start",
            "completed",
            message="Unified runtime started successfully",
            details=actual,
        )

    async def async_validate(self, runtime: dict[str, Any] | None = None) -> dict[str, Any]:
        await self._set_step("validate", "running", message="Comparing migrated data before and after cutover")
        try:
            result = await super().async_validate(runtime)
            self._ensure_steps()
            counts = self.state.setdefault("counts", {})
            counts["validated"] = deepcopy(counts.get("after_start") or {})
            if result.get("ok"):
                await self._set_step(
                    "validate",
                    "completed",
                    message="Migration validation passed",
                    details={
                        "expected": deepcopy(result.get("expected") or {}),
                        "actual": deepcopy(counts.get("after_start") or {}),
                    },
                )
            else:
                await self._set_step(
                    "validate",
                    "failed",
                    message="Migration validation failed",
                    details={"errors": list(result.get("errors") or [])},
                )
            return result
        except Exception as err:
            await self._set_step("validate", "failed", message=str(err))
            raise

    async def async_finalize(self, runtime: dict[str, Any] | None = None) -> dict[str, Any]:
        await self._set_step("remove_legacy", "running", message="Removing verified legacy config entries")
        await self._set_step("reconcile", "running", message="Transferring final Smart Group visibility ownership")
        try:
            state = await super().async_finalize(runtime)
            self.state = state
            self._ensure_steps()
            await self._set_step(
                "remove_legacy",
                "completed",
                message="Legacy Home Assistant config entries removed after successful validation",
                details={"removed_entries": len(self.state.get("removed_entries") or [])},
            )
            await self._set_step(
                "reconcile",
                "completed",
                message="New Smart Group runtime reconciled hidden-member ownership",
            )
            self.state.setdefault("rollback", {})["available"] = True
            self.state["migration_duration_complete_at"] = _utcnow()
            await self._save_state()
            return deepcopy(self.state)
        except Exception as err:
            await self._set_step("remove_legacy", "failed", message=str(err))
            await self._set_step("reconcile", "failed", message="Final reconciliation did not complete")
            raise

    async def async_mark_hacs_cleanup(self, results: dict[str, str]) -> None:
        """Record HACS cleanup without turning a successful migration into a failure."""
        failures = {k: v for k, v in results.items() if str(v).startswith("failed:")}
        pending = {
            k: v
            for k, v in results.items()
            if v in {"hacs_not_loaded", "hacs_api_unavailable"}
        }
        if failures:
            status = "failed"
            message = "Migration completed, but one or more legacy HACS repositories could not be cleaned"
        elif pending:
            status = "skipped"
            message = "Migration completed; HACS cleanup can be retried later"
        else:
            status = "completed"
            message = "Legacy HACS repositories cleaned through the HACS API"
        self.state["hacs_cleanup"] = deepcopy(results)
        await self._set_step("hacs_cleanup", status, message=message, details=results)

    async def async_rollback(self, reason: str) -> dict[str, Any]:
        phase_before = self.state.get("phase")
        state = await super().async_rollback(reason)
        self.state = state
        self._ensure_steps()
        for step in ("runtime_start", "validate", "remove_legacy", "reconcile"):
            item = self.state["steps"].get(step) or {}
            if item.get("status") in {"running", "pending"}:
                await self._set_step(step, "rolled_back", message="Rolled back after migration failure")
        rollback = self.state.setdefault("rollback", {})
        rollback.update(
            {
                "available": True,
                "used": True,
                "reason": reason,
                "restored_entries": len(self.state.get("restored_entries") or []),
                "phase_before_rollback": phase_before,
            }
        )
        await self._save_state()
        return deepcopy(self.state)

    def _sanitized_steps(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        raw = data.get("steps") or {}
        return [
            {
                "id": step,
                "status": (raw.get(step) or {}).get("status", "pending"),
                "started_at": (raw.get(step) or {}).get("started_at"),
                "completed_at": (raw.get(step) or {}).get("completed_at"),
                "message": (raw.get(step) or {}).get("message"),
                "details": deepcopy((raw.get(step) or {}).get("details") or {}),
            }
            for step in STEP_ORDER
        ]

    async def async_public_status(self) -> dict[str, Any]:
        base = await super().async_public_status()
        data = self.state or await self._store.async_load() or {}
        base.update(
            {
                "steps": self._sanitized_steps(data),
                "counts": deepcopy(data.get("counts") or {}),
                "rollback": deepcopy(data.get("rollback") or {}),
                "hacs_cleanup": deepcopy(data.get("hacs_cleanup") or {}),
                "last_updated_at": data.get("last_updated_at"),
                "report_ready": bool(data),
            }
        )
        return base

    async def async_report(self) -> dict[str, Any]:
        """Return a credential-free report suitable for support/download."""
        status = await self.async_public_status()
        return {
            "schema": MIGRATION_REPORT_SCHEMA,
            "generated_at": _utcnow(),
            "integration": {
                "domain": DOMAIN,
                "version": VERSION,
            },
            "migration": status,
            "notes": [
                "This report intentionally excludes Tuya credentials and raw legacy storage contents.",
                "The backup store name is included, but its raw payload is not exposed through this report.",
            ],
        }
