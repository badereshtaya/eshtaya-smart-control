"""Startup-safe Multi-Way manager for slow/cloud-backed Home Assistant entities."""
from __future__ import annotations

import asyncio
from time import monotonic

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from ..const import (
    CONF_REPAIR_CONFIRMATIONS,
    CONF_REPAIR_GRACE_SECONDS,
    CONF_STARTUP_MAX_WAIT_SECONDS,
    CONF_STARTUP_SETTLE_SECONDS,
    CONF_STARTUP_WAIT_HA,
    CONF_STARTUP_WAIT_REFERENCES,
    DATA_STARTUP_STATUS,
    DOMAIN,
)
from ..runtime_options import option
from .const import HEALTH_RECOVERING, UNAVAILABLE_STATES
from .manager import MultiWayManager


_LOADING_ENTRY_STATES = {
    ConfigEntryState.NOT_LOADED,
    ConfigEntryState.SETUP_IN_PROGRESS,
    ConfigEntryState.SETUP_RETRY,
    ConfigEntryState.UNLOAD_IN_PROGRESS,
}


class StartupSafeMultiWayManager(MultiWayManager):
    """Delay readiness/repairs until Home Assistant entity providers have settled.

    The base engine historically used a fixed delay counted from the moment this
    integration loaded. On a restart, cloud integrations such as official Tuya may
    still be restoring when that timer expires. v2.4 replaces that behavior with a
    Home Assistant startup barrier plus owner-config-entry readiness and a separate
    missing-entity confirmation window.
    """

    def __init__(self, hass, store) -> None:
        super().__init__(hass, store)
        self._ha_started_unsub = None
        self._startup_barrier_task: asyncio.Task | None = None
        self._ready_since: float | None = None
        self._missing_since: dict[str, float] = {}
        self._missing_checks: dict[str, int] = {}

    async def async_start(self) -> None:
        """Start listeners immediately but keep the control/repair engine guarded."""
        if self._started:
            return
        await super().async_start()

        # The base class scheduled a fixed startup_delay. Cancel it; v2.4 readiness
        # is controlled by the HA lifecycle barrier below.
        if self._startup_unsub:
            self._startup_unsub()
            self._startup_unsub = None
        self._ready = False
        self._ready_since = None
        self._clear_transient_missing_issues()

        wait_for_ha = bool(option(self.hass, CONF_STARTUP_WAIT_HA))
        if not wait_for_ha or self.hass.is_running:
            self._schedule_startup_barrier("integration_reload" if self.hass.is_running else "startup_wait_disabled")
            return

        self._set_startup_status(
            phase="waiting_home_assistant",
            ready=False,
            pending=[],
            timed_out=False,
        )
        self._ha_started_unsub = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED, self._on_home_assistant_started
        )

    async def async_stop(self) -> None:
        """Cancel lifecycle waiters before stopping the base engine."""
        if self._ha_started_unsub:
            self._ha_started_unsub()
            self._ha_started_unsub = None
        if self._startup_barrier_task and not self._startup_barrier_task.done():
            self._startup_barrier_task.cancel()
            await asyncio.gather(self._startup_barrier_task, return_exceptions=True)
        self._startup_barrier_task = None
        self._missing_since.clear()
        self._missing_checks.clear()
        await super().async_stop()

    @callback
    def _on_home_assistant_started(self, _event) -> None:
        self._ha_started_unsub = None
        self._schedule_startup_barrier("home_assistant_started")

    def _schedule_startup_barrier(self, reason: str) -> None:
        if self._startup_barrier_task and not self._startup_barrier_task.done():
            return
        self._startup_barrier_task = self.hass.async_create_task(
            self._async_startup_barrier(reason),
            "Eshtaya Smart Control startup barrier",
        )

    def _referenced_entities(self) -> set[str]:
        entities: set[str] = set()
        for group in self._groups.values():
            output = group.get("output")
            if output:
                entities.add(str(output))
            fallback = group.get("behavior", {}).get("fallback_output")
            if fallback:
                entities.add(str(fallback))
            for controller in group.get("controllers") or []:
                entity_id = controller.get("entity_id")
                if entity_id:
                    entities.add(str(entity_id))
        return entities

    def _owner_entry(self, entity_id: str):
        registry_entry = er.async_get(self.hass).async_get(entity_id)
        if registry_entry is None or not registry_entry.config_entry_id:
            return None
        return self.hass.config_entries.async_get_entry(registry_entry.config_entry_id)

    def _owner_is_loading(self, entity_id: str) -> bool:
        """Return true while the integration that owns an entity is still restoring."""
        owner = self._owner_entry(entity_id)
        if owner is None:
            return False
        if owner.disabled_by is not None:
            # A deliberately disabled provider should not produce a startup repair.
            return True
        return owner.state in _LOADING_ENTRY_STATES

    def _pending_references(self) -> list[str]:
        """Return only referenced entities whose owning config entry is still loading."""
        if not bool(option(self.hass, CONF_STARTUP_WAIT_REFERENCES)):
            return []
        pending: list[str] = []
        for entity_id in sorted(self._referenced_entities()):
            if self.hass.states.get(entity_id) is not None:
                continue
            if self._owner_is_loading(entity_id):
                pending.append(entity_id)
        return pending

    async def _async_startup_barrier(self, reason: str) -> None:
        """Wait for referenced providers and a quiet settle window, then go ready."""
        max_wait = max(30, int(option(self.hass, CONF_STARTUP_MAX_WAIT_SECONDS)))
        settle = max(0, int(option(self.hass, CONF_STARTUP_SETTLE_SECONDS)))
        started = monotonic()
        stable_since: float | None = None
        pending: list[str] = []
        timed_out = False

        self._set_startup_status(
            phase="waiting_referenced_integrations",
            ready=False,
            pending=[],
            timed_out=False,
            reason=reason,
        )

        try:
            while self._started:
                pending = self._pending_references()
                now = monotonic()
                elapsed = now - started

                if pending:
                    stable_since = None
                else:
                    if stable_since is None:
                        stable_since = now
                    if now - stable_since >= settle:
                        break

                if elapsed >= max_wait:
                    timed_out = True
                    break

                self._set_startup_status(
                    phase="waiting_referenced_integrations" if pending else "settling",
                    ready=False,
                    pending=pending,
                    timed_out=False,
                    elapsed_seconds=round(elapsed, 1),
                    reason=reason,
                )
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            return

        if not self._started:
            return

        self._ready = True
        self._ready_since = monotonic()
        self._missing_since.clear()
        self._missing_checks.clear()
        self._set_startup_status(
            phase="ready",
            ready=True,
            pending=pending,
            timed_out=timed_out,
            elapsed_seconds=round(monotonic() - started, 1),
            reason=reason,
        )
        await self._async_initialize_groups()

    def _set_startup_status(self, *, phase: str, ready: bool, pending: list[str], timed_out: bool, **extra) -> None:
        data = self.hass.data.setdefault(DOMAIN, {})
        data[DATA_STARTUP_STATUS] = {
            "phase": phase,
            "ready": ready,
            "pending_entities": list(pending),
            "pending_count": len(pending),
            "timed_out": timed_out,
            **extra,
        }

    def _clear_transient_missing_issues(self) -> None:
        """Remove persisted false missing issues while a new startup is protected."""
        registry = ir.async_get(self.hass)
        for issue_domain, issue_id in list(registry.issues):
            if issue_domain != DOMAIN:
                continue
            if issue_id.startswith(("missing_output_", "missing_controller_")):
                registry.async_delete(DOMAIN, issue_id)

    def _forget_missing(self, entity_id: str) -> None:
        self._missing_since.pop(entity_id, None)
        self._missing_checks.pop(entity_id, None)

    def _missing_is_confirmed(self, entity_id: str) -> bool:
        """Require a real post-start grace period and repeated observations."""
        state = self.hass.states.get(entity_id)
        if state is not None:
            self._forget_missing(entity_id)
            return False
        if not self._ready or self._owner_is_loading(entity_id):
            self._forget_missing(entity_id)
            return False

        now = monotonic()
        first_seen = self._missing_since.setdefault(entity_id, now)
        grace = max(0, int(option(self.hass, CONF_REPAIR_GRACE_SECONDS)))
        if now - first_seen < grace:
            return False

        checks = self._missing_checks.get(entity_id, 0) + 1
        self._missing_checks[entity_id] = checks
        required = max(1, int(option(self.hass, CONF_REPAIR_CONFIRMATIONS)))
        return checks >= required

    def _entity_is_transient(self, entity_id: str) -> bool:
        """Return true while a missing entity is still inside startup/repair grace."""
        if self.hass.states.get(entity_id) is not None:
            self._forget_missing(entity_id)
            return False
        if not self._ready or self._owner_is_loading(entity_id):
            return True
        now = monotonic()
        first_seen = self._missing_since.setdefault(entity_id, now)
        grace = max(0, int(option(self.hass, CONF_REPAIR_GRACE_SECONDS)))
        return now - first_seen < grace

    def _refresh_repairs(self) -> None:
        if not self._ready:
            self._clear_transient_missing_issues()
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
        output_entity = str(group["output"])
        if self.hass.states.get(output_entity) is None:
            if self._missing_is_confirmed(output_entity):
                expected.add(output_issue)
                self._create_issue(
                    output_issue,
                    "missing_output",
                    {"group": group["name"], "entity": output_entity},
                    severity=ir.IssueSeverity.ERROR,
                )
            else:
                self._delete_issue(output_issue)
        else:
            self._forget_missing(output_entity)
            self._delete_issue(output_issue)

        for controller in group["controllers"]:
            controller_entity = str(controller["entity_id"])
            suffix = controller_entity.replace(".", "_")
            issue_id = f"missing_controller_{group_id}_{suffix}"[:250]
            if self.hass.states.get(controller_entity) is None:
                if self._missing_is_confirmed(controller_entity):
                    expected.add(issue_id)
                    self._create_issue(
                        issue_id,
                        "missing_controller",
                        {"group": group["name"], "entity": controller_entity},
                        severity=ir.IssueSeverity.WARNING,
                    )
                else:
                    self._delete_issue(issue_id)
            else:
                self._forget_missing(controller_entity)
                self._delete_issue(issue_id)

        threshold = int(self.store.settings()["repair_threshold"])
        runtime = self._runtime[group_id]
        unresponsive_issue = f"output_unresponsive_{group_id}"
        if runtime.consecutive_output_failures >= threshold:
            expected.add(unresponsive_issue)
            self._create_issue(
                unresponsive_issue,
                "output_unresponsive",
                {"group": group["name"], "entity": output_entity},
                severity=ir.IssueSeverity.ERROR,
            )
        else:
            self._delete_issue(unresponsive_issue)
        return expected

    def _update_health(self, group_id: str) -> None:
        group = self._groups.get(group_id)
        runtime = self._runtime.get(group_id)
        if not group or not runtime:
            return
        output_entity = str(group.get("output") or "")
        if output_entity and self.hass.states.get(output_entity) is None:
            if self._entity_is_transient(output_entity):
                runtime.health = HEALTH_RECOVERING
                return
        super()._update_health(group_id)

    async def _async_initialize_groups(self) -> None:
        await super()._async_initialize_groups()
        # Missing repairs remain subject to the separate grace/confirmation gate.
        self._refresh_repairs()
