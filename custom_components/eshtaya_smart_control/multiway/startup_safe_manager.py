"""Startup-safe Multi-Way manager for slow/cloud-backed Home Assistant entities."""
from __future__ import annotations

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from .manager import MultiWayManager


class StartupSafeMultiWayManager(MultiWayManager):
    """Avoid false missing-entity repairs while integrations restore after restart."""

    def _entity_known(self, entity_id: str) -> bool:
        if self.hass.states.get(entity_id) is not None:
            return True
        return er.async_get(self.hass).async_get(entity_id) is not None

    def _refresh_repairs(self) -> None:
        # MultiWayManager.async_reload() runs before startup protection completes.
        # Tuya and similar integrations may not have published states yet.
        if not self._ready:
            return
        super()._refresh_repairs()

    def _refresh_repairs_for_group(self, group_id: str) -> set[str]:
        expected: set[str] = set()
        group = self._groups.get(group_id)
        if not group:
            return expected
        if not self._ready:
            return expected

        output_issue = f"missing_output_{group_id}"
        if not self._entity_known(group["output"]):
            expected.add(output_issue)
            self._create_issue(
                output_issue,
                "missing_output",
                {"group": group["name"], "entity": group["output"]},
                severity=ir.IssueSeverity.ERROR,
            )
        else:
            self._delete_issue(output_issue)

        for controller in group["controllers"]:
            suffix = controller["entity_id"].replace(".", "_")
            issue_id = f"missing_controller_{group_id}_{suffix}"[:250]
            if not self._entity_known(controller["entity_id"]):
                expected.add(issue_id)
                self._create_issue(
                    issue_id,
                    "missing_controller",
                    {"group": group["name"], "entity": controller["entity_id"]},
                    severity=ir.IssueSeverity.WARNING,
                )
            else:
                self._delete_issue(issue_id)

        threshold = int(self.store.settings()["repair_threshold"])
        runtime = self._runtime[group_id]
        unresponsive_issue = f"output_unresponsive_{group_id}"
        if runtime.consecutive_output_failures >= threshold:
            expected.add(unresponsive_issue)
            self._create_issue(
                unresponsive_issue,
                "output_unresponsive",
                {"group": group["name"], "entity": group["output"]},
                severity=ir.IssueSeverity.ERROR,
            )
        else:
            self._delete_issue(unresponsive_issue)
        return expected

    async def _async_initialize_groups(self) -> None:
        await super()._async_initialize_groups()
        # Re-evaluate repairs only after startup protection and reconciliation.
        self._refresh_repairs()
