"""High-reliability Smart Group engine for Eshtaya Multi-Way Control."""
from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from time import monotonic
from typing import Any
from uuid import uuid4

from homeassistant.core import Context, Event, HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval

from .const import (
    DOMAIN,
    MODE_EVENT,
    MODE_MIRROR,
    MODE_MOMENTARY_OFF,
    MODE_MOMENTARY_ON,
    MODE_TOGGLE,
    PERFORMANCE_SAFE,
    SIGNAL_SMART_GROUPS_UPDATED,
    SIGNAL_SMART_RUNTIME_UPDATED,
    SMART_ACTION_TYPES,
    SMART_DIRECTION_BIDIRECTIONAL,
    SMART_FAILURE_STOP,
    SMART_KIND_PHYSICAL,
    SMART_ON_OFF_TYPES,
    SMART_STATE_ALL,
    UNAVAILABLE_STATES,
    VALID_STATES,
)
from .smart_storage import SmartGroupStore


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _invert(state: str) -> str:
    return "off" if state == "on" else "on"


def _group_type(group: dict[str, Any]) -> str:
    return str(group.get("group_type") or group.get("virtual_type") or "light")


def _is_on_off_group(group: dict[str, Any]) -> bool:
    return _group_type(group) in SMART_ON_OFF_TYPES


class SmartGroupManager:
    """Control physical-controller and virtual aggregate groups safely."""

    def __init__(self, hass: HomeAssistant, store: SmartGroupStore) -> None:
        self.hass = hass
        self.store = store
        self._groups: dict[str, dict[str, Any]] = {}
        self._entity_groups: dict[str, set[str]] = defaultdict(set)
        self._runtime: dict[str, dict[str, Any]] = {}
        self._pending_contexts: dict[str, tuple[str, str, str, float]] = {}
        # Context may be lost by cloud-backed integrations. Keep a second,
        # state-aware command-echo guard keyed by Smart Group + entity.
        self._pending_expected: dict[tuple[str, str], deque[tuple[str, str, float]]] = defaultdict(deque)
        self._global_expected: dict[str, deque[tuple[str, float]]] = defaultdict(deque)
        self._unsub = None
        self._watchdog = None
        self._activity: deque[dict[str, Any]] = deque(maxlen=300)
        self._locks: dict[str, asyncio.Lock] = {}
        self._flaps: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._quarantine: dict[tuple[str, str], float] = {}
        self._scene_edges: dict[str, deque[tuple[float, str]]] = defaultdict(deque)
        self._scene_tasks: dict[str, asyncio.Task] = {}
        self._verify_tasks: dict[str, asyncio.Task] = {}
        self._edge_queues: dict[str, deque[tuple[str, Event]]] = defaultdict(deque)
        self._edge_tasks: dict[str, asyncio.Task] = {}
        self._action_last_run: dict[tuple[str, str], float] = {}
        self._source_settle_tasks: dict[str, asyncio.Task] = {}
        self._started = False

    async def async_start(self) -> None:
        if self._started:
            return
        self._started = True
        await self.async_reload()
        self._watchdog = async_track_time_interval(
            self.hass, self._async_watchdog_tick, timedelta(seconds=15)
        )

    async def async_stop(self) -> None:
        self._started = False
        if self._unsub:
            self._unsub()
            self._unsub = None
        if self._watchdog:
            self._watchdog()
            self._watchdog = None
        for task in (
            *self._scene_tasks.values(),
            *self._verify_tasks.values(),
            *self._edge_tasks.values(),
            *self._source_settle_tasks.values(),
        ):
            task.cancel()
        self._scene_tasks.clear()
        self._verify_tasks.clear()
        self._edge_tasks.clear()
        self._source_settle_tasks.clear()
        self._edge_queues.clear()
        self._pending_contexts.clear()
        self._pending_expected.clear()
        self._global_expected.clear()
        self._action_last_run.clear()

    async def async_reload(self) -> None:
        self._groups = {g["id"]: g for g in self.store.groups()}
        self._entity_groups.clear()
        valid = set(self._groups)
        for group_id, group in self._groups.items():
            self._locks.setdefault(group_id, asyncio.Lock())
            runtime = self._runtime.setdefault(group_id, self._new_runtime())
            runtime["name"] = group["name"]
            controller = group.get("controller_entity")
            if controller:
                self._entity_groups[controller].add(group_id)
            for member in group["members"]:
                self._entity_groups[member["entity_id"]].add(group_id)
            self._refresh_runtime(group_id)
        for group_id in list(self._runtime):
            if group_id not in valid:
                self._runtime.pop(group_id, None)
                self._locks.pop(group_id, None)
                self._edge_queues.pop(group_id, None)
                task = self._edge_tasks.pop(group_id, None)
                if task and not task.done():
                    task.cancel()
                settle_task = self._source_settle_tasks.pop(group_id, None)
                if settle_task and not settle_task.done():
                    settle_task.cancel()
        if self._unsub:
            self._unsub()
            self._unsub = None
        if self._entity_groups:
            self._unsub = async_track_state_change_event(
                self.hass, list(self._entity_groups), self._async_state_event
            )
        await self._async_reconcile_hidden_members()
        async_dispatcher_send(self.hass, SIGNAL_SMART_GROUPS_UPDATED)

    async def _async_reconcile_hidden_members(self) -> None:
        """Apply hide-members policy and remember only visibility owned by us."""
        desired = {
            member["entity_id"]
            for group in self._groups.values()
            if group.get("hide_members")
            for member in group.get("members", [])
        }
        owned = self.store.hidden_members_owned()
        registry = er.async_get(self.hass)
        new_owned = set(owned)

        for entity_id in desired:
            entry = registry.async_get(entity_id)
            if entry is None:
                continue
            if entry.hidden_by is None:
                registry.async_update_entity(
                    entity_id, hidden_by=er.RegistryEntryHider.INTEGRATION
                )
                new_owned.add(entity_id)
            elif entry.hidden_by == er.RegistryEntryHider.INTEGRATION:
                new_owned.add(entity_id)

        for entity_id in owned - desired:
            entry = registry.async_get(entity_id)
            if entry and entry.hidden_by == er.RegistryEntryHider.INTEGRATION:
                registry.async_update_entity(entity_id, hidden_by=None)
            new_owned.discard(entity_id)

        if new_owned != owned:
            await self.store.async_set_hidden_members_owned(new_owned)

    @staticmethod
    def _new_runtime() -> dict[str, Any]:
        return {
            "state": None,
            "desired_state": None,
            "health": "healthy",
            "last_source": None,
            "last_action": None,
            "last_changed": None,
            "last_latency_ms": None,
            "last_transaction_id": None,
            "last_error": None,
            "commands": 0,
            "failures": 0,
            "quarantined": [],
            "member_metrics": {},
            "manual_authority_until": 0.0,
            "manual_authority_source": None,
            "manual_authority_state": None,
            "verification_active": False,
            "source_generation": 0,
            "source_settle_active": False,
        }

    def list_with_runtime(self) -> list[dict[str, Any]]:
        result = []
        for group in self.store.groups():
            item = dict(group)
            item["runtime"] = self.status(group["id"])
            result.append(item)
        return result

    def status(self, group_id: str) -> dict[str, Any]:
        group = self._groups.get(group_id)
        if not group:
            return {}
        self._refresh_runtime(group_id)
        runtime = dict(self._runtime[group_id])
        runtime["members"] = [
            self._member_status(group_id, member["entity_id"]) for member in group["members"]
        ]
        controller = group.get("controller_entity")
        runtime["controller"] = self._entity_snapshot(controller) if controller else None
        runtime["quality_score"] = self._quality_score(runtime)
        latencies = [
            metric.get("avg_latency_ms")
            for metric in runtime.get("member_metrics", {}).values()
            if metric.get("avg_latency_ms") is not None
        ]
        avg = round(sum(latencies) / len(latencies)) if latencies else None
        runtime["average_member_latency_ms"] = avg
        runtime["response_class"] = (
            "cloud_or_device_limited"
            if avg and avg >= 400
            else "moderate"
            if avg and avg >= 180
            else "fast"
        )
        return runtime

    def summary(self) -> dict[str, Any]:
        groups = self.store.groups()
        statuses = [self.status(group["id"]) for group in groups]
        return {
            "groups": len(groups),
            "healthy": sum(1 for runtime in statuses if runtime.get("health") == "healthy"),
            "degraded": sum(
                1 for runtime in statuses if runtime.get("health") not in {"healthy", "maintenance"}
            ),
            "maintenance": sum(1 for group in groups if group.get("maintenance")),
            "members": sum(len(group["members"]) for group in groups),
            "physical": sum(1 for group in groups if group["kind"] == SMART_KIND_PHYSICAL),
            "virtual": sum(1 for group in groups if group["kind"] != SMART_KIND_PHYSICAL),
            "average_quality": round(
                sum(runtime.get("quality_score", 100) for runtime in statuses) / len(statuses), 1
            )
            if statuses
            else 100,
        }

    def activity(self, limit: int = 200) -> list[dict[str, Any]]:
        return list(self._activity)[-limit:][::-1]

    @callback
    def _async_state_event(self, event: Event) -> None:
        """Queue state edges per Smart Group in exact Home Assistant arrival order."""
        entity_id = event.data.get("entity_id")
        if not entity_id:
            return
        for group_id in list(self._entity_groups.get(entity_id, ())):
            self._edge_queues[group_id].append((entity_id, event))
            task = self._edge_tasks.get(group_id)
            if task is None or task.done():
                self._edge_tasks[group_id] = self.hass.async_create_task(
                    self._async_process_edge_queue(group_id)
                )

    async def _async_process_edge_queue(self, group_id: str) -> None:
        """Serialize physical/member edges so rapid opposite states cannot reorder."""
        try:
            queue = self._edge_queues[group_id]
            while queue and self._started and group_id in self._groups:
                entity_id, event = queue.popleft()
                await self._async_handle_event(group_id, entity_id, event)
        except asyncio.CancelledError:
            return
        finally:
            task = self._edge_tasks.get(group_id)
            if task is asyncio.current_task():
                self._edge_tasks.pop(group_id, None)

    async def _async_handle_event(self, group_id: str, entity_id: str, event: Event) -> None:
        group = self._groups.get(group_id)
        if not group or not group.get("enabled", True) or group.get("maintenance"):
            return
        new: State | None = event.data.get("new_state")
        old: State | None = event.data.get("old_state")
        if new is None:
            return

        # Integration-generated state reports must never become a physical
        # control edge in another Smart Group that shares this member. This
        # guard is entity-wide and state-aware, so an opposite real edge still
        # passes through immediately.
        if self._is_global_command_echo(entity_id, new.state):
            self._refresh_runtime(group_id)
            self._notify(group_id)
            return

        context_id = event.context.id if event.context else None
        pending = self._pending_contexts.pop(context_id, None) if context_id else None
        if pending and pending[0] == group_id and pending[1] == entity_id:
            self._consume_expected_echo(group_id, entity_id, new.state, pending[2])
            self._refresh_runtime(group_id)
            self._notify(group_id)
            return

        # Tuya and other cloud integrations may emit the resulting state with a
        # fresh Context. Suppress only a matching state that we recently
        # commanded; an opposite edge is always treated as a real override.
        if self._consume_expected_echo(group_id, entity_id, new.state):
            self._add_activity(
                group_id,
                "command_echo",
                entity_id,
                new.state,
                "ignored",
                None,
                self._runtime[group_id].get("last_transaction_id"),
                "echo_guard",
            )
            self._refresh_runtime(group_id)
            self._notify(group_id)
            return
        if new.state in UNAVAILABLE_STATES:
            self._refresh_runtime(group_id)
            self._notify(group_id)
            return

        old_state = old.state if old else None
        new_state = new.state
        if old_state == new_state:
            # Attribute-only updates (brightness/color/effect/etc.) must refresh
            # the virtual aggregate entity, but are not physical control edges.
            self._refresh_runtime(group_id)
            self._notify(group_id)
            return
        controller = group.get("controller_entity")
        input_capable = (
            entity_id == controller
            or group["behavior"].get("direction") == SMART_DIRECTION_BIDIRECTIONAL
        )
        # Flapping protection is for followers, not legitimate human inputs. A
        # wall controller or bidirectional member may be toggled rapidly on purpose
        # and must never be auto-quarantined for that behavior.
        if (
            _is_on_off_group(group)
            and not input_capable
            and self._record_flap(group, entity_id)
        ):
            self._refresh_runtime(group_id)
            self._notify(group_id)
            return

        if entity_id == controller:
            if _group_type(group) in SMART_ACTION_TYPES:
                if self._action_controller_fired(group, old_state, new_state):
                    await self.async_run_action_group(
                        group_id, source=entity_id, origin="physical"
                    )
            elif _is_on_off_group(group):
                target = self._controller_target(group, old_state, new_state)
                if target in VALID_STATES:
                    await self.async_set_state(
                        group_id, target, source=entity_id, origin="physical"
                    )
                    if group["behavior"].get("controller_mode", MODE_MIRROR) == MODE_MIRROR:
                        self._schedule_onoff_source_settle(group_id, entity_id, is_controller=True)
            else:
                await self._async_handle_domain_controller(
                    group_id, old_state, new_state, entity_id
                )
            return

        if (
            _is_on_off_group(group)
            and group["behavior"].get("direction") == SMART_DIRECTION_BIDIRECTIONAL
            and new_state in VALID_STATES
        ):
            runtime = self._runtime[group_id]
            if (
                group["kind"] == SMART_KIND_PHYSICAL
                and monotonic() < float(runtime.get("manual_authority_until") or 0)
                and runtime.get("manual_authority_source") == controller
                and new_state != runtime.get("manual_authority_state")
            ):
                self._add_activity(
                    group_id, "manual_priority_guard", entity_id, new_state, "ignored", None,
                    runtime.get("last_transaction_id"), "member",
                )
                return
            if self._is_scene_batch(group, entity_id):
                self._schedule_scene_settle(group_id)
                return
            await self.async_set_state(group_id, new_state, source=entity_id, origin="member")
            self._schedule_onoff_source_settle(group_id, entity_id, is_controller=False)
            return

        self._refresh_runtime(group_id)
        await self._reflect_controller_if_needed(group_id)
        self._notify(group_id)

    def _schedule_onoff_source_settle(
        self, group_id: str, source: str, *, is_controller: bool
    ) -> None:
        """Keep the latest physical/member source authoritative until it settles."""
        group = self._groups.get(group_id)
        if not group or not _is_on_off_group(group):
            return
        runtime = self._runtime[group_id]
        runtime["source_generation"] = int(runtime.get("source_generation", 0)) + 1
        generation = runtime["source_generation"]
        runtime["source_settle_active"] = True
        old = self._source_settle_tasks.get(group_id)
        if old and not old.done():
            old.cancel()
        self._source_settle_tasks[group_id] = self.hass.async_create_task(
            self._async_onoff_source_settle(group_id, source, generation, is_controller)
        )

    def _onoff_source_state(
        self, group: dict[str, Any], source: str, *, is_controller: bool
    ) -> str | None:
        state = self.hass.states.get(source)
        if state is None or state.state in UNAVAILABLE_STATES:
            return None
        if not is_controller:
            return state.state if state.state in VALID_STATES else None
        if group["behavior"].get("controller_mode", MODE_MIRROR) != MODE_MIRROR:
            return None
        mapped = state.state
        if group["behavior"].get("invert_controller") and mapped in VALID_STATES:
            mapped = _invert(mapped)
        return mapped if mapped in VALID_STATES else None

    async def _async_onoff_source_settle(
        self, group_id: str, source: str, generation: int, is_controller: bool
    ) -> None:
        """Final convergence pass using the real final state of the last source."""
        try:
            group = self._groups.get(group_id)
            if not group:
                return
            runtime = self._runtime[group_id]
            max_window = max(0.25, min(10.0, float(
                group["behavior"].get("manual_priority_ms", 2500)
            ) / 1000))
            stable_for = max(0.05, min(2.0, float(
                group["behavior"].get("source_stable_ms", 220)
            ) / 1000))
            deadline = monotonic() + max_window
            last = self._onoff_source_state(group, source, is_controller=is_controller)
            changed_at = monotonic()
            while monotonic() < deadline:
                await asyncio.sleep(0.05)
                current_group = self._groups.get(group_id)
                if not current_group or not current_group.get("enabled", True):
                    return
                runtime = self._runtime[group_id]
                if int(runtime.get("source_generation", 0)) != generation:
                    return
                current = self._onoff_source_state(
                    current_group, source, is_controller=is_controller
                )
                if current is None:
                    continue
                if current != last:
                    last = current
                    changed_at = monotonic()
                    runtime["manual_authority_until"] = monotonic() + max_window
                    runtime["manual_authority_source"] = source
                    runtime["manual_authority_state"] = current
                    continue
                if monotonic() - changed_at >= stable_for:
                    break
            runtime = self._runtime.get(group_id)
            current_group = self._groups.get(group_id)
            if not runtime or not current_group:
                return
            if int(runtime.get("source_generation", 0)) != generation:
                return
            final = self._onoff_source_state(
                current_group, source, is_controller=is_controller
            )
            if final not in VALID_STATES:
                return
            runtime["manual_authority_until"] = monotonic() + max_window
            runtime["manual_authority_source"] = source
            runtime["manual_authority_state"] = final
            self._add_activity(
                group_id, "source_settled", source, final, "success", None,
                runtime.get("last_transaction_id"), "source_settle",
            )
            await self.async_set_state(
                group_id, final, source=source, origin="source_settle"
            )
        except asyncio.CancelledError:
            return
        finally:
            runtime = self._runtime.get(group_id)
            if runtime and int(runtime.get("source_generation", 0)) == generation:
                runtime["source_settle_active"] = False
            task = self._source_settle_tasks.get(group_id)
            if task is asyncio.current_task():
                self._source_settle_tasks.pop(group_id, None)

    def _controller_target(
        self, group: dict[str, Any], old_state: str | None, new_state: str
    ) -> str | None:
        behavior = group["behavior"]
        mode = behavior.get("controller_mode", MODE_MIRROR)
        invert = behavior.get("invert_controller", False)
        mapped = _invert(new_state) if invert and new_state in VALID_STATES else new_state
        if mode == MODE_MIRROR and mapped in VALID_STATES:
            return mapped
        if mode == MODE_TOGGLE and old_state != new_state:
            return _invert(self._runtime[group["id"]].get("desired_state") or self._compute_state(group) or "off")
        if mode == MODE_MOMENTARY_ON and mapped == "on":
            return _invert(self._runtime[group["id"]].get("desired_state") or self._compute_state(group) or "off")
        if mode == MODE_MOMENTARY_OFF and mapped == "off":
            return _invert(self._runtime[group["id"]].get("desired_state") or self._compute_state(group) or "off")
        if mode == MODE_EVENT and old_state != new_state:
            return _invert(self._runtime[group["id"]].get("desired_state") or self._compute_state(group) or "off")
        return None

    def _rich_binary_state(self, group: dict[str, Any]) -> str | None:
        """Map a rich domain aggregate to a controller-friendly on/off state."""
        state = self._compute_state(group)
        group_type = _group_type(group)
        if group_type in {"cover", "valve"}:
            if state == "closed":
                return "off"
            if state in {"open", "opening", "closing"}:
                return "on"
        elif group_type == "lock":
            if state in {"locked", "locking"}:
                return "off"
            if state in {"unlocked", "unlocking", "open", "opening"}:
                return "on"
        elif group_type == "media_player":
            return "off" if state in {"off", "unavailable", "unknown"} else "on"
        return None

    def _rich_controller_target(
        self, group: dict[str, Any], old_state: str | None, new_state: str
    ) -> str | None:
        """Return the binary intent produced by a physical controller."""
        behavior = group["behavior"]
        mode = behavior.get("controller_mode", MODE_MIRROR)
        invert = behavior.get("invert_controller", False)
        mapped = _invert(new_state) if invert and new_state in VALID_STATES else new_state
        current = self._rich_binary_state(group) or "off"
        if mode == MODE_MIRROR and mapped in VALID_STATES:
            return mapped
        if mode == MODE_TOGGLE and old_state != new_state:
            return _invert(current)
        if mode == MODE_MOMENTARY_ON and mapped == "on":
            return _invert(current)
        if mode == MODE_MOMENTARY_OFF and mapped == "off":
            return _invert(current)
        if mode == MODE_EVENT and old_state != new_state:
            return _invert(current)
        return None

    def _action_controller_fired(
        self, group: dict[str, Any], old_state: str | None, new_state: str
    ) -> bool:
        """Return whether a physical controller edge should run an Action Group."""
        mode = group["behavior"].get("controller_mode", MODE_EVENT)
        if mode in {MODE_EVENT, MODE_TOGGLE, MODE_MIRROR}:
            return old_state != new_state
        if mode == MODE_MOMENTARY_ON:
            return new_state == "on" and old_state != new_state
        if mode == MODE_MOMENTARY_OFF:
            return new_state == "off" and old_state != new_state
        return False

    async def async_run_action_group(
        self, group_id: str, *, source: str = "virtual", origin: str = "service"
    ) -> bool:
        """Run all members of a scene/script/automation Action Group."""
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Smart Group not found")
        group_type = _group_type(group)
        if group_type not in SMART_ACTION_TYPES:
            raise ValueError(f"{group_type} is not an Action Group")
        if not group.get("enabled", True):
            raise ValueError("Smart Group is disabled")
        if group.get("maintenance"):
            raise ValueError("Smart Group is in maintenance mode")

        behavior = group["behavior"]
        if origin == "physical":
            key = (group_id, source)
            now = monotonic()
            cooldown = max(0.0, float(behavior.get("action_cooldown_ms", 250)) / 1000)
            previous = self._action_last_run.get(key, 0.0)
            if cooldown and now - previous < cooldown:
                self._add_activity(
                    group_id, "action_duplicate_suppressed", source, "run", "ignored",
                    None, None, origin,
                )
                return True
            self._action_last_run[key] = now

        members = [
            member["entity_id"]
            for member in group["members"]
            if member.get("enabled", True)
            and not self._is_quarantined(group_id, member["entity_id"])
        ]
        if not members:
            return False

        service = {
            "scene": "turn_on",
            "script": "turn_on",
            "automation": "trigger",
        }[group_type]
        txid = uuid4().hex[:12]
        started = monotonic()

        async def run_member(entity_id: str) -> bool:
            state = self.hass.states.get(entity_id)
            if state is None or state.state in UNAVAILABLE_STATES:
                self._metric(group_id, entity_id, False, None)
                return False
            data: dict[str, Any] = {}
            custom = behavior.get("action_data")
            if group_type == "scene":
                if isinstance(custom, dict):
                    data.update(
                        {key: value for key, value in custom.items() if key != "entity_id"}
                    )
                transition = float(behavior.get("scene_transition", 0) or 0)
                if transition > 0:
                    data["transition"] = transition
            elif group_type == "script":
                if isinstance(custom, dict) and custom:
                    data["variables"] = custom
            elif group_type == "automation":
                data["skip_condition"] = bool(
                    behavior.get("automation_skip_condition", True)
                )
            # Group membership is authoritative. Custom action data may never
            # redirect a member call to a different entity.
            data["entity_id"] = entity_id
            context = Context()
            member_started = monotonic()
            try:
                await self.hass.services.async_call(
                    group_type,
                    service,
                    data,
                    blocking=behavior.get("performance_mode") == PERFORMANCE_SAFE,
                    context=context,
                )
                self._metric(
                    group_id, entity_id, True, int((monotonic() - member_started) * 1000)
                )
                return True
            except Exception:  # noqa: BLE001
                self._metric(group_id, entity_id, False, None)
                return False

        results: list[bool] = []
        execution = behavior.get("action_execution", "parallel")
        if execution == "parallel":
            results = list(await asyncio.gather(*(run_member(entity_id) for entity_id in members)))
        else:
            delay = max(0.0, float(behavior.get("member_delay_ms", 0)) / 1000)
            for entity_id in members:
                ok = await run_member(entity_id)
                results.append(ok)
                if not ok and behavior.get("failure_policy") == SMART_FAILURE_STOP:
                    break
                if delay:
                    await asyncio.sleep(delay)

        runtime = self._runtime[group_id]
        success = all(results) if results else False
        runtime.update(
            {
                "desired_state": None,
                "last_source": source,
                "last_action": "run",
                "last_changed": _utcnow(),
                "last_transaction_id": txid,
                "last_latency_ms": int((monotonic() - started) * 1000),
                "last_error": None if success else "One or more actions failed to start",
            }
        )
        runtime["commands"] += 1
        if not success:
            runtime["failures"] += 1
        self._add_activity(
            group_id, "action_group_run", source, "run",
            "success" if success else "partial", runtime["last_latency_ms"], txid, origin,
        )
        self._refresh_runtime(group_id)
        self._notify(group_id)
        return success

    async def _async_handle_domain_controller(
        self, group_id: str, old_state: str | None, new_state: str, source: str
    ) -> None:
        """Fan a physical-controller action out using native domain services."""
        group = self._groups[group_id]
        group_type = _group_type(group)
        if group_type == "button":
            if old_state != new_state:
                await self._async_domain_action(
                    group_id, "press", source=source, origin="physical"
                )
            return
        target = self._rich_controller_target(group, old_state, new_state)
        if target not in VALID_STATES:
            self._refresh_runtime(group_id)
            self._notify(group_id)
            return
        action_map = {
            "cover": {"on": "open_cover", "off": "close_cover"},
            "valve": {"on": "open_valve", "off": "close_valve"},
            "lock": {"on": "unlock", "off": "lock"},
            "media_player": {"on": "turn_on", "off": "turn_off"},
        }
        service = action_map.get(group_type, {}).get(target)
        if service:
            await self._async_domain_action(
                group_id, service, source=source, origin="physical"
            )

    async def _async_domain_action(
        self,
        group_id: str,
        service: str,
        *,
        source: str,
        origin: str,
        service_data: dict[str, Any] | None = None,
    ) -> bool:
        """Execute a native rich-domain service on all enabled group members."""
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Smart Group not found")
        if not group.get("enabled", True):
            raise ValueError("Smart Group is disabled")
        if group.get("maintenance"):
            raise ValueError("Smart Group is in maintenance mode")
        domain = _group_type(group)
        members = [
            member["entity_id"]
            for member in group["members"]
            if member.get("enabled", True)
            and not self._is_quarantined(group_id, member["entity_id"])
        ]
        if not members:
            return False
        txid = uuid4().hex[:12]
        started = monotonic()
        results: list[bool] = []
        for entity_id in members:
            state = self.hass.states.get(entity_id)
            if state is None or state.state in UNAVAILABLE_STATES:
                self._metric(group_id, entity_id, False, None)
                results.append(False)
                continue
            context = Context()
            data = {"entity_id": entity_id}
            if service_data:
                data.update(service_data)
            start = monotonic()
            try:
                await self.hass.services.async_call(
                    domain,
                    service,
                    data,
                    blocking=group["behavior"].get("performance_mode") == PERFORMANCE_SAFE,
                    context=context,
                )
                latency = int((monotonic() - start) * 1000)
                self._metric(group_id, entity_id, True, latency)
                results.append(True)
            except Exception:  # noqa: BLE001
                self._metric(group_id, entity_id, False, None)
                results.append(False)
                if group["behavior"].get("failure_policy") == SMART_FAILURE_STOP:
                    break
        runtime = self._runtime[group_id]
        runtime.update(
            {
                "last_source": source,
                "last_action": service,
                "last_changed": _utcnow(),
                "last_transaction_id": txid,
                "last_latency_ms": int((monotonic() - started) * 1000),
                "last_error": None if all(results) else "One or more members failed",
            }
        )
        runtime["commands"] += 1
        if not all(results):
            runtime["failures"] += 1
        self._add_activity(
            group_id,
            "domain_action",
            source,
            service,
            "success" if all(results) else "partial",
            runtime["last_latency_ms"],
            txid,
            origin,
        )
        self._refresh_runtime(group_id)
        self._notify(group_id)
        return all(results)

    async def async_set_state(
        self,
        group_id: str,
        state: str,
        *,
        source: str = "virtual",
        origin: str = "service",
        service_data: dict[str, Any] | None = None,
    ) -> bool:
        if state not in VALID_STATES:
            raise ValueError("State must be on or off")
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Smart Group not found")
        if not _is_on_off_group(group):
            raise ValueError(
                f"{_group_type(group)} Smart Groups use native domain services, not ON/OFF state sync"
            )
        if not group.get("enabled", True):
            raise ValueError("Smart Group is disabled")
        if group.get("maintenance"):
            raise ValueError("Smart Group is in maintenance mode")

        async with self._locks[group_id]:
            started = monotonic()
            txid = uuid4().hex[:12]
            runtime = self._runtime[group_id]
            runtime.update(
                {
                    "desired_state": state,
                    "last_source": source,
                    "last_action": state,
                    "last_changed": _utcnow(),
                    "last_transaction_id": txid,
                    "last_error": None,
                    "verification_active": bool(group["behavior"].get("verify_members")),
                }
            )
            if origin in {"physical", "member", "test"}:
                runtime["manual_authority_until"] = monotonic() + float(
                    group["behavior"].get("manual_priority_ms", 2500)
                ) / 1000
                runtime["manual_authority_source"] = source
                runtime["manual_authority_state"] = state

            targets = [
                member["entity_id"]
                for member in group["members"]
                if member.get("enabled", True)
                and member["entity_id"] != source
                and not self._is_quarantined(group_id, member["entity_id"])
            ]
            controller = group.get("controller_entity")
            if (
                group["kind"] == SMART_KIND_PHYSICAL
                and group["behavior"].get("reflect_controller")
                and source != controller
                and controller
                and self._domain(controller) in {"switch", "light", "input_boolean"}
                and not self._is_quarantined(group_id, controller)
            ):
                targets.append(controller)

            results: list[bool] = []
            delay = float(group["behavior"].get("member_delay_ms", 0)) / 1000
            performance = group["behavior"].get("performance_mode")
            if (
                performance != PERFORMANCE_SAFE
                and not delay
                and group["behavior"].get("failure_policy") != SMART_FAILURE_STOP
            ):
                if targets:
                    results.extend(
                        await asyncio.gather(
                            *(
                                self._async_command_entity(
                                    group, entity_id, state, txid, service_data=service_data
                                )
                                for entity_id in targets
                            )
                        )
                    )
            else:
                for entity_id in targets:
                    ok = await self._async_command_entity(
                        group, entity_id, state, txid, service_data=service_data
                    )
                    results.append(ok)
                    if not ok and group["behavior"].get("failure_policy") == SMART_FAILURE_STOP:
                        break
                    if delay:
                        await asyncio.sleep(delay)

            runtime["last_latency_ms"] = int((monotonic() - started) * 1000)
            runtime["commands"] += 1
            success = all(results) if results else True
            if not success:
                runtime["failures"] += 1
                runtime["last_error"] = "One or more members failed to accept the command"
            self._add_activity(
                group_id, "set_state", source, state, "success" if success else "partial",
                runtime["last_latency_ms"], txid, origin,
            )
            self._refresh_runtime(group_id)
            self._notify(group_id)

            if group["behavior"].get("verify_members"):
                old_task = self._verify_tasks.get(group_id)
                if old_task and not old_task.done():
                    old_task.cancel()
                self._verify_tasks[group_id] = self.hass.async_create_task(
                    self._async_verify(group_id, state, txid)
                )
            return success

    async def _async_command_entity(
        self,
        group: dict[str, Any],
        entity_id: str,
        state: str,
        txid: str,
        *,
        service_data: dict[str, Any] | None = None,
    ) -> bool:
        current = self.hass.states.get(entity_id)
        if current is None or current.state in UNAVAILABLE_STATES:
            self._metric(group["id"], entity_id, False, None)
            return False
        if current.state == state and not service_data:
            self._metric(group["id"], entity_id, True, 0)
            return True
        domain = self._domain(entity_id)
        if domain not in {"switch", "light", "input_boolean", "fan"}:
            return False
        context = Context()
        echo_seconds = float(group["behavior"].get("command_echo_ms", 5000)) / 1000
        expires = monotonic() + max(0.25, echo_seconds)
        self._pending_contexts[context.id] = (group["id"], entity_id, state, expires)
        self._pending_expected[(group["id"], entity_id)].append((txid, state, expires))
        self._global_expected[entity_id].append((state, expires))
        start = monotonic()
        try:
            blocking = group["behavior"].get("performance_mode") == PERFORMANCE_SAFE
            data: dict[str, Any] = {"entity_id": entity_id}
            if domain == "light" and service_data:
                if state == "on":
                    data.update(service_data)
                elif "transition" in service_data:
                    data["transition"] = service_data["transition"]
            await self.hass.services.async_call(
                domain,
                f"turn_{state}",
                data,
                blocking=blocking,
                context=context,
            )
            latency = int((monotonic() - start) * 1000)
            self._metric(group["id"], entity_id, True, latency)
            return True
        except Exception:  # noqa: BLE001
            self._pending_contexts.pop(context.id, None)
            self._drop_expected_command(group["id"], entity_id, txid, state)
            self._drop_global_expected(entity_id, state)
            self._metric(group["id"], entity_id, False, None)
            return False

    async def _async_verify(self, group_id: str, expected: str, txid: str) -> None:
        """Wait for the whole group to converge before reporting a fault.

        Cloud-backed integrations can acknowledge a service call immediately and
        publish the resulting entity states hundreds of milliseconds (or even a
        few seconds) later.  Older builds checked after a short adaptive delay,
        retried once, and could therefore raise an Out-of-sync Repair issue in
        under a second even though the configured command timeout was 3 seconds.

        Verification now treats ``command_timeout`` as a real convergence
        window.  We poll cheaply for state convergence, perform only the
        configured bounded retries against members that are still stale, and
        create a Repair issue only when the complete window expires.
        """
        try:
            group = self._groups.get(group_id)
            if not group:
                return

            timeout = max(0.25, float(group["behavior"].get("command_timeout", 3.0)))
            started = monotonic()
            deadline = started + timeout
            poll_interval = min(0.25, max(0.10, timeout / 15))
            retry_budget = (
                max(0, int(group["behavior"].get("max_retries", 1)))
                if group["behavior"].get("auto_heal", True)
                else 0
            )
            # Give cloud devices a meaningful chance to report the first command
            # before retrying.  With the default 3s window this is ~1.35s.
            next_retry_at = started + min(1.5, max(0.6, timeout * 0.45))

            runtime = self._runtime.get(group_id)
            if not runtime or runtime.get("last_transaction_id") != txid:
                return

            mismatches = self._mismatches(group, expected)
            while mismatches and monotonic() < deadline:
                runtime = self._runtime.get(group_id)
                if not runtime or runtime.get("last_transaction_id") != txid:
                    return

                now = monotonic()
                if retry_budget > 0 and now >= next_retry_at:
                    retry_targets = [
                        entity_id
                        for entity_id in mismatches
                        if not self._is_quarantined(group_id, entity_id)
                    ]
                    if retry_targets:
                        await asyncio.gather(
                            *(
                                self._async_command_entity(
                                    group, entity_id, expected, txid
                                )
                                for entity_id in retry_targets
                            )
                        )
                    retry_budget -= 1
                    remaining = max(0.0, deadline - monotonic())
                    # Spread additional retries over the remaining convergence
                    # window rather than hammering cloud APIs back-to-back.
                    next_retry_at = monotonic() + max(0.4, remaining / (retry_budget + 1))

                remaining = deadline - monotonic()
                if remaining <= 0:
                    break
                await asyncio.sleep(min(poll_interval, remaining))
                mismatches = self._mismatches(group, expected)

            runtime = self._runtime.get(group_id)
            if not runtime or runtime.get("last_transaction_id") != txid:
                return

            # One final read at the deadline prevents a state event arriving on
            # the last poll boundary from creating a transient false warning.
            mismatches = self._mismatches(group, expected)
            if mismatches:
                runtime["last_error"] = f"Out of sync: {', '.join(mismatches[:4])}"
                self._create_issue(group, runtime["last_error"])
                if group["behavior"].get("notify_on_fault"):
                    self._notify_fault(group, runtime["last_error"])
            else:
                runtime["last_error"] = None
                self._delete_issue(f"smart_group_out_of_sync_{group_id}")

            runtime["verification_active"] = False
            self._refresh_runtime(group_id)
            self._notify(group_id)
        except asyncio.CancelledError:
            return

    async def _reflect_controller_if_needed(self, group_id: str) -> None:
        group = self._groups[group_id]
        if not _is_on_off_group(group):
            return
        if group["kind"] != SMART_KIND_PHYSICAL or not group["behavior"].get("reflect_controller"):
            return
        controller = group.get("controller_entity")
        state = self._compute_state(group)
        if (
            controller
            and state in VALID_STATES
            and self._domain(controller) in {"switch", "light", "input_boolean"}
            and not self._is_quarantined(group_id, controller)
        ):
            if group["behavior"].get("invert_controller"):
                state = _invert(state)
            await self._async_command_entity(group, controller, state, "reflect")

    async def async_action(
        self,
        group_id: str,
        action: str,
        *,
        source: str = "panel",
        service_data: dict[str, Any] | None = None,
    ) -> bool:
        """Execute a domain-aware group action from the management API."""
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Smart Group not found")
        group_type = _group_type(group)
        if group_type in SMART_ACTION_TYPES:
            if action != "run":
                raise ValueError(f"Unsupported {group_type} Action Group action: {action}")
            return await self.async_run_action_group(
                group_id, source=source, origin="panel"
            )
        if group_type in SMART_ON_OFF_TYPES:
            if action not in VALID_STATES:
                raise ValueError(f"Unsupported {group_type} group action: {action}")
            return await self.async_set_state(
                group_id,
                action,
                source=source,
                origin="panel",
                service_data=service_data,
            )
        allowed: dict[str, set[str]] = {
            "cover": {"open_cover", "close_cover", "stop_cover"},
            "valve": {"open_valve", "close_valve", "stop_valve"},
            "lock": {"lock", "unlock", "open"},
            "media_player": {"turn_on", "turn_off", "media_play", "media_pause"},
            "button": {"press"},
        }
        if action not in allowed.get(group_type, set()):
            if group_type == "notify":
                raise ValueError(
                    "Notify groups are used through the native notify entity so message data is preserved"
                )
            raise ValueError(f"{group_type} groups are read-only or do not support {action}")
        return await self._async_domain_action(
            group_id,
            action,
            source=source,
            origin="panel",
            service_data=service_data,
        )

    async def async_sync(self, group_id: str) -> bool:
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Smart Group not found")
        if not _is_on_off_group(group):
            # Native rich-domain groups continuously derive their public state from
            # members. Sync is deliberately non-destructive for them.
            self._refresh_runtime(group_id)
            self._notify(group_id)
            return True
        state: str | None
        if group["kind"] == SMART_KIND_PHYSICAL:
            controller_state = self.hass.states.get(group.get("controller_entity"))
            mode = group["behavior"].get("controller_mode", MODE_MIRROR)
            if mode == MODE_MIRROR and controller_state and controller_state.state in VALID_STATES:
                state = controller_state.state
                if group["behavior"].get("invert_controller"):
                    state = _invert(state)
            else:
                state = self._runtime[group_id].get("desired_state") or self._compute_state(group)
        else:
            state = self._runtime[group_id].get("desired_state") or self._compute_state(group)
        if state not in VALID_STATES:
            return False
        return await self.async_set_state(group_id, state, source="sync", origin="sync")

    async def async_full_test(self, group_id: str, destructive: bool = False) -> dict[str, Any]:
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Smart Group not found")
        before = self._compute_state(group)
        report = self.test_group(group_id)
        if destructive and _is_on_off_group(group) and before in VALID_STATES:
            target = _invert(before)
            started = monotonic()
            ok1 = await self.async_set_state(group_id, target, source="test_center", origin="test")
            await asyncio.sleep(0.35)
            after_toggle = self._compute_state(group)
            ok2 = await self.async_set_state(group_id, before, source="test_center", origin="test")
            await asyncio.sleep(0.35)
            restored = self._compute_state(group)
            report["destructive_test"] = {
                "toggle": ok1,
                "toggle_state": after_toggle,
                "restore": ok2,
                "restored_state": restored,
                "latency_ms": int((monotonic() - started) * 1000),
            }
            report["passed"] = report["passed"] and ok1 and ok2 and restored == before
        return report

    def test_group(self, group_id: str) -> dict[str, Any]:
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Smart Group not found")
        members = [self._member_status(group_id, member["entity_id"]) for member in group["members"]]
        controller = (
            self._entity_snapshot(group.get("controller_entity"))
            if group.get("controller_entity")
            else None
        )
        missing = [member["entity_id"] for member in members if member["state"] == "missing"]
        offline = [
            member["entity_id"] for member in members if member["state"] in UNAVAILABLE_STATES
        ]
        if controller and controller["state"] in {"missing", *UNAVAILABLE_STATES}:
            offline.append(controller["entity_id"])
        return {
            "group_id": group_id,
            "name": group["name"],
            "passed": not missing and not offline,
            "state": self._compute_state(group),
            "members": members,
            "controller": controller,
            "missing": missing,
            "offline": offline,
            "quality_score": self.status(group_id).get("quality_score"),
        }

    async def async_test_all(self) -> dict[str, Any]:
        results = [self.test_group(group_id) for group_id in self._groups]
        return {
            "total": len(results),
            "passed": sum(1 for result in results if result["passed"]),
            "failed": sum(1 for result in results if not result["passed"]),
            "results": results,
            "created_at": _utcnow(),
        }

    def diagnostics_bundle(self, group_id: str | None = None) -> dict[str, Any]:
        groups = (
            [self._groups[group_id]]
            if group_id and group_id in self._groups
            else list(self._groups.values())
        )
        return {
            "created_at": _utcnow(),
            "summary": self.summary(),
            "groups": [
                {"config": group, "runtime": self.status(group["id"])} for group in groups
            ],
            "activity": self.activity(100),
        }

    @callback
    def _async_watchdog_tick(self, _now) -> None:
        self.hass.async_create_task(self._async_watchdog())

    async def _async_watchdog(self) -> None:
        self._prune_pending_contexts()
        for group_id, group in list(self._groups.items()):
            if not group.get("enabled", True) or group.get("maintenance"):
                continue
            self._cleanup_quarantine(group_id)
            runtime = self._runtime[group_id]
            expected = runtime.get("desired_state")
            mismatches = (
                self._mismatches(group, expected)
                if _is_on_off_group(group) and expected in VALID_STATES
                else []
            )
            # Standard Smart Group semantics are command fan-out, not a forever
            # thermostat. Continuous enforcement is deliberately opt-in because
            # otherwise automations/devices can fight the watchdog and oscillate.
            if (
                group["behavior"].get("continuous_enforcement", False)
                and expected in VALID_STATES
                and mismatches
            ):
                txid = f"watchdog-{uuid4().hex[:8]}"
                await asyncio.gather(
                    *(
                        self._async_command_entity(group, entity_id, expected, txid)
                        for entity_id in mismatches
                        if not self._is_quarantined(group_id, entity_id)
                    )
                )
            elif expected in VALID_STATES and not mismatches:
                runtime["last_error"] = None
                self._delete_issue(f"smart_group_out_of_sync_{group_id}")
            self._refresh_runtime(group_id)
            self._notify(group_id)

    def _refresh_runtime(self, group_id: str) -> None:
        group = self._groups.get(group_id)
        if not group:
            return
        runtime = self._runtime.setdefault(group_id, self._new_runtime())
        state = self._compute_state(group)
        runtime["state"] = state
        if _is_on_off_group(group):
            if runtime.get("desired_state") not in VALID_STATES:
                runtime["desired_state"] = state if state in VALID_STATES else None
        else:
            runtime["desired_state"] = None
            runtime["verification_active"] = False

        tracked = [member["entity_id"] for member in group["members"]]
        controller = group.get("controller_entity") if group["kind"] == SMART_KIND_PHYSICAL else None
        if controller:
            tracked.append(controller)
        quarantined = [
            entity_id for entity_id in tracked if self._is_quarantined(group_id, entity_id)
        ]
        runtime["quarantined"] = quarantined
        if not group.get("enabled", True):
            health = "disabled"
        elif group.get("maintenance"):
            health = "maintenance"
        else:
            snapshots = [self._entity_snapshot(entity_id) for entity_id in tracked]
            if any(snapshot and snapshot["state"] == "missing" for snapshot in snapshots):
                health = "missing"
            elif any(
                snapshot and snapshot["state"] in UNAVAILABLE_STATES for snapshot in snapshots
            ):
                health = "degraded"
            elif quarantined:
                health = "quarantined"
            elif runtime.get("last_error"):
                health = "degraded"
            elif (
                _is_on_off_group(group)
                and runtime.get("desired_state") in VALID_STATES
                and (
                    runtime.get("verification_active")
                    or group["behavior"].get("continuous_enforcement", False)
                )
                and self._mismatches(group, runtime["desired_state"])
            ):
                health = "out_of_sync"
            else:
                health = "healthy"
        runtime["health"] = health

    def _compute_state(self, group: dict[str, Any]) -> str:
        group_type = _group_type(group)
        if group_type in SMART_ACTION_TYPES:
            return "available"
        states: list[str] = []
        for member in group["members"]:
            if not member.get("enabled", True) or self._is_quarantined(
                group["id"], member["entity_id"]
            ):
                continue
            state = self.hass.states.get(member["entity_id"])
            if state is not None and state.state not in UNAVAILABLE_STATES:
                states.append(state.state)
        if not states:
            return "unavailable"

        all_policy = group["behavior"].get("state_policy") == SMART_STATE_ALL
        if group_type in SMART_ON_OFF_TYPES or group_type == "binary_sensor":
            command_states = [state for state in states if state in VALID_STATES]
            if not command_states:
                return "unavailable"
            if all_policy:
                return "on" if all(state == "on" for state in command_states) else "off"
            return "on" if any(state == "on" for state in command_states) else "off"

        if group_type in {"cover", "valve"}:
            if "opening" in states:
                return "opening"
            if "closing" in states:
                return "closing"
            if all(state == "closed" for state in states):
                return "closed"
            if any(state == "open" for state in states):
                return "open"
            return states[0]

        if group_type == "lock":
            for priority in ("jammed", "unlocking", "locking", "unlocked", "open", "locked"):
                if priority in states:
                    if priority == "locked" and not all(state == "locked" for state in states):
                        continue
                    return priority
            return states[0]

        if group_type == "media_player":
            for priority in (
                "playing",
                "buffering",
                "paused",
                "on",
                "idle",
                "standby",
                "off",
            ):
                if priority in states:
                    return priority
            return states[0]

        if group_type == "sensor":
            # The domain-native SensorGroup entity performs the configured
            # calculation. Runtime diagnostics only need a representative state.
            return states[0]
        if group_type == "event":
            return max(states)
        if group_type in {"button", "notify"}:
            return "available"
        return states[0]

    def _mismatches(self, group: dict[str, Any], expected: str) -> list[str]:
        if not _is_on_off_group(group):
            return []
        result = []
        for member in group["members"]:
            entity_id = member["entity_id"]
            if (
                not member.get("enabled", True)
                or self._is_quarantined(group["id"], entity_id)
            ):
                continue
            state = self.hass.states.get(entity_id)
            if state and state.state not in UNAVAILABLE_STATES and state.state != expected:
                result.append(entity_id)
        return result

    def _member_status(self, group_id: str, entity_id: str) -> dict[str, Any]:
        snapshot = self._entity_snapshot(entity_id) or {
            "entity_id": entity_id,
            "state": "missing",
            "domain": self._domain(entity_id),
            "friendly_name": None,
        }
        metric = self._runtime[group_id].get("member_metrics", {}).get(entity_id, {})
        snapshot.update(
            {
                "quarantined": self._is_quarantined(group_id, entity_id),
                "commands": metric.get("commands", 0),
                "failures": metric.get("failures", 0),
                "avg_latency_ms": metric.get("avg_latency_ms"),
                "last_latency_ms": metric.get("last_latency_ms"),
                "quality_score": self._metric_quality(metric),
            }
        )
        return snapshot

    def _entity_snapshot(self, entity_id: str | None) -> dict[str, Any] | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        return {
            "entity_id": entity_id,
            "state": state.state if state else "missing",
            "domain": self._domain(entity_id),
            "friendly_name": state.attributes.get("friendly_name") if state else None,
        }

    def _metric(
        self, group_id: str, entity_id: str, success: bool, latency: int | None
    ) -> None:
        runtime = self._runtime[group_id]
        metrics = runtime.setdefault("member_metrics", {})
        metric = metrics.setdefault(
            entity_id,
            {"commands": 0, "failures": 0, "samples": 0, "total_latency": 0},
        )
        metric["commands"] += 1
        if not success:
            metric["failures"] += 1
        if latency is not None:
            metric["samples"] += 1
            metric["total_latency"] += latency
            metric["avg_latency_ms"] = round(metric["total_latency"] / metric["samples"])
            metric["last_latency_ms"] = latency

    @staticmethod
    def _metric_quality(metric: dict[str, Any]) -> int:
        commands = max(1, int(metric.get("commands", 0)))
        failures = int(metric.get("failures", 0))
        latency = int(metric.get("avg_latency_ms") or 0)
        score = 100 - round((failures / commands) * 60) - min(30, latency // 100)
        return max(0, min(100, score))

    def _quality_score(self, runtime: dict[str, Any]) -> int:
        metrics = list(runtime.get("member_metrics", {}).values())
        if not metrics:
            return 100
        return round(sum(self._metric_quality(metric) for metric in metrics) / len(metrics))

    def _adaptive_verify_delay(self, group: dict[str, Any], timeout: float) -> float:
        runtime = self._runtime[group["id"]]
        samples = [
            metric.get("avg_latency_ms")
            for metric in runtime.get("member_metrics", {}).values()
            if metric.get("avg_latency_ms")
        ]
        if not samples:
            return min(timeout, 0.35)
        avg = sum(samples) / len(samples) / 1000
        return min(timeout, max(0.12, min(1.2, avg * 1.35)))

    def _is_scene_batch(self, group: dict[str, Any], entity_id: str) -> bool:
        guard = float(group["behavior"].get("scene_guard_ms", 800)) / 1000
        if guard <= 0:
            return False
        now = monotonic()
        queue = self._scene_edges[group["id"]]
        queue.append((now, entity_id))
        while queue and now - queue[0][0] > guard:
            queue.popleft()
        return len({item[1] for item in queue}) >= 2

    def _schedule_scene_settle(self, group_id: str) -> None:
        old = self._scene_tasks.get(group_id)
        if old and not old.done():
            old.cancel()
        self._scene_tasks[group_id] = self.hass.async_create_task(
            self._async_scene_settle(group_id)
        )

    async def _async_scene_settle(self, group_id: str) -> None:
        try:
            group = self._groups.get(group_id)
            if not group:
                return
            await asyncio.sleep(float(group["behavior"].get("scene_guard_ms", 800)) / 1000)
            state = self._compute_state(group)
            if state in VALID_STATES:
                runtime = self._runtime[group_id]
                runtime["desired_state"] = state
                runtime["last_source"] = "scene_guard"
                runtime["last_action"] = state
                runtime["last_changed"] = _utcnow()
                self._add_activity(
                    group_id, "scene_adopted", "scene_guard", state, "success", None, None, "scene"
                )
                await self._reflect_controller_if_needed(group_id)
                self._refresh_runtime(group_id)
                self._notify(group_id)
        except asyncio.CancelledError:
            return

    def _prune_pending_contexts(self) -> None:
        now = monotonic()
        for context_id, pending in list(self._pending_contexts.items()):
            if pending[3] <= now:
                self._pending_contexts.pop(context_id, None)
        for key, queue in list(self._pending_expected.items()):
            while queue and queue[0][2] <= now:
                queue.popleft()
            if not queue:
                self._pending_expected.pop(key, None)
        for entity_id, queue in list(self._global_expected.items()):
            while queue and queue[0][1] <= now:
                queue.popleft()
            if not queue:
                self._global_expected.pop(entity_id, None)

    def _is_global_command_echo(self, entity_id: str, new_state: str) -> bool:
        """Return True for our recent command echo, independent of HA Context."""
        queue = self._global_expected.get(entity_id)
        if not queue:
            return False
        now = monotonic()
        while queue and queue[0][1] <= now:
            queue.popleft()
        if not queue:
            self._global_expected.pop(entity_id, None)
            return False
        if any(state == new_state for state, _expires in queue):
            return True
        # An opposite edge is authoritative. Drop stale expectations everywhere
        # so a later same-state physical transition is not swallowed by the old
        # command, even when the cloud integration lost the original Context.
        self._global_expected.pop(entity_id, None)

        # These maps always exist on a normally initialized manager, but keep
        # this helper defensive so isolated unit tests and recovery paths cannot
        # fail just because the manager was constructed without __init__.
        pending_expected = getattr(self, "_pending_expected", None)
        if pending_expected is not None:
            for key in [key for key in pending_expected if key[1] == entity_id]:
                pending_expected.pop(key, None)

        pending_contexts = getattr(self, "_pending_contexts", None)
        if pending_contexts is not None:
            for context_id, pending in list(pending_contexts.items()):
                if pending[1] == entity_id:
                    pending_contexts.pop(context_id, None)
        return False

    def _consume_expected_echo(
        self,
        group_id: str,
        entity_id: str,
        new_state: str,
        expected_state: str | None = None,
    ) -> bool:
        """Consume a recent matching command echo without hiding opposite edges."""
        key = (group_id, entity_id)
        queue = self._pending_expected.get(key)
        if not queue:
            return False
        now = monotonic()
        while queue and queue[0][2] <= now:
            queue.popleft()
        if not queue:
            self._pending_expected.pop(key, None)
            return False
        wanted = expected_state or new_state
        for index, (_txid, state, _expires) in enumerate(queue):
            if state == wanted and new_state == state:
                del queue[index]
                if not queue:
                    self._pending_expected.pop(key, None)
                return True
        return False

    def _drop_expected_command(
        self, group_id: str, entity_id: str, txid: str, state: str
    ) -> None:
        key = (group_id, entity_id)
        queue = self._pending_expected.get(key)
        if not queue:
            return
        kept = deque(
            item for item in queue if not (item[0] == txid and item[1] == state)
        )
        if kept:
            self._pending_expected[key] = kept
        else:
            self._pending_expected.pop(key, None)

    def _drop_global_expected(self, entity_id: str, state: str) -> None:
        queue = self._global_expected.get(entity_id)
        if not queue:
            return
        kept = deque(item for item in queue if item[0] != state)
        if kept:
            self._global_expected[entity_id] = kept
        else:
            self._global_expected.pop(entity_id, None)

    def _record_flap(self, group: dict[str, Any], entity_id: str) -> bool:
        key = (group["id"], entity_id)
        now = monotonic()
        queue = self._flaps[key]
        window = float(group["behavior"].get("flap_window_sec", 10))
        queue.append(now)
        while queue and now - queue[0] > window:
            queue.popleft()
        threshold = int(group["behavior"].get("flap_threshold", 8))
        if len(queue) >= threshold:
            until = now + float(group["behavior"].get("quarantine_sec", 60))
            self._quarantine[key] = until
            self._add_activity(
                group["id"], "member_quarantined", entity_id, None, "warning", None, None,
                "flapping",
            )
            return True
        return False

    def _is_quarantined(self, group_id: str, entity_id: str) -> bool:
        until = self._quarantine.get((group_id, entity_id), 0)
        if until and monotonic() >= until:
            self._quarantine.pop((group_id, entity_id), None)
            return False
        return bool(until)

    def _cleanup_quarantine(self, group_id: str) -> None:
        for key in list(self._quarantine):
            if key[0] == group_id:
                self._is_quarantined(*key)

    async def async_set_enabled(self, group_id: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable a Smart Group without changing any member state."""
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Smart Group not found")

        enabled = bool(enabled)
        if bool(group.get("enabled", True)) == enabled:
            self._refresh_runtime(group_id)
            self._notify(group_id)
            return self.store.get(group_id) or group

        if not enabled:
            # Stop all corrective/background work before persisting the disabled state.
            for mapping in (
                self._verify_tasks,
                self._scene_tasks,
                self._edge_tasks,
                self._source_settle_tasks,
            ):
                task = mapping.pop(group_id, None)
                if task and not task.done():
                    task.cancel()
            self._edge_queues.pop(group_id, None)
            for context_id, pending in list(self._pending_contexts.items()):
                if pending and pending[0] == group_id:
                    self._pending_contexts.pop(context_id, None)
            for key in [key for key in self._pending_expected if key[0] == group_id]:
                self._pending_expected.pop(key, None)
            runtime = self._runtime.setdefault(group_id, self._new_runtime())
            runtime["verification_active"] = False
            runtime["desired_state"] = None
            runtime["last_error"] = None
            self._delete_issue(f"smart_group_out_of_sync_{group_id}")

        updated = await self.store.async_set_enabled(group_id, enabled)
        await self.async_reload()

        # Re-enable adopts the current aggregate state; it never commands members.
        runtime = self._runtime.setdefault(group_id, self._new_runtime())
        runtime["desired_state"] = None
        self._refresh_runtime(group_id)
        self._add_activity(
            group_id,
            "group_enabled" if enabled else "group_disabled",
            "control_center",
            "enabled" if enabled else "disabled",
            "success",
            None,
            None,
            "runtime_control",
        )
        self._notify(group_id)
        return updated

    async def async_set_member_quarantine(
        self, group_id: str, entity_id: str, enabled: bool
    ) -> None:
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Smart Group not found")
        valid = {member["entity_id"] for member in group["members"]}
        if group.get("controller_entity"):
            valid.add(group["controller_entity"])
        if entity_id not in valid:
            raise ValueError("Entity does not belong to this Smart Group")
        key = (group_id, entity_id)
        if enabled:
            self._quarantine[key] = monotonic() + 86400 * 365
        else:
            self._quarantine.pop(key, None)
        self._refresh_runtime(group_id)
        self._notify(group_id)

    def _add_activity(
        self,
        group_id,
        event,
        source=None,
        action=None,
        result="success",
        latency_ms=None,
        txid=None,
        origin=None,
    ) -> None:
        self._activity.append(
            {
                "timestamp": _utcnow(),
                "group_id": group_id,
                "event": event,
                "source": source,
                "action": action,
                "result": result,
                "latency_ms": latency_ms,
                "transaction_id": txid,
                "origin": origin,
            }
        )

    def _notify(self, group_id: str) -> None:
        async_dispatcher_send(self.hass, SIGNAL_SMART_RUNTIME_UPDATED, group_id)
        self.hass.bus.async_fire(
            f"{DOMAIN}_event", {"section": "smart_group", "group_id": group_id}
        )

    def _create_issue(self, group: dict[str, Any], message: str) -> None:
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            f"smart_group_out_of_sync_{group['id']}",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="smart_group_fault",
            translation_placeholders={"group": group["name"], "error": message},
        )

    def _delete_issue(self, issue_id: str) -> None:
        ir.async_delete_issue(self.hass, DOMAIN, issue_id)

    def _notify_fault(self, group: dict[str, Any], message: str) -> None:
        try:
            from homeassistant.components import persistent_notification

            persistent_notification.async_create(
                self.hass,
                message,
                title=f"Eshtaya Smart Group: {group['name']}",
                notification_id=f"{DOMAIN}_smart_{group['id']}",
            )
        except Exception:  # noqa: BLE001
            return

    @staticmethod
    def _domain(entity_id: str) -> str:
        return entity_id.split(".", 1)[0] if isinstance(entity_id, str) and "." in entity_id else ""
