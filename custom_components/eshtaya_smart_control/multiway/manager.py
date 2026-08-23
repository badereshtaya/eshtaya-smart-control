"""Synchronization engine for Eshtaya Multi-Way Control."""
from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
import logging
from time import monotonic
from typing import Any
from uuid import uuid4

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import Context, Event, HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)

from .const import (
    COMMANDABLE_DOMAINS,
    DOMAIN,
    EVENT_TYPE,
    HEALTH_DEGRADED,
    HEALTH_DISABLED,
    HEALTH_HEALTHY,
    HEALTH_MISSING_OUTPUT,
    HEALTH_OUT_OF_SYNC,
    HEALTH_OUTPUT_OFFLINE,
    HEALTH_RECOVERING,
    MODE_EVENT,
    MODE_FOLLOW,
    MODE_MIRROR,
    MODE_MOMENTARY_OFF,
    MODE_MOMENTARY_ON,
    MODE_TOGGLE,
    PERFORMANCE_BALANCED,
    PERFORMANCE_INSTANT,
    PERFORMANCE_SAFE,
    PRESSABLE_DOMAINS,
    SIGNAL_GROUPS_UPDATED,
    SIGNAL_RUNTIME_UPDATED,
    UNAVAILABLE_STATES,
    VALID_STATES,
)
from .models import GroupRuntime, PendingCommand
from .storage import MultiWayStore

_LOGGER = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _invert_state(state: str) -> str:
    return "off" if state == "on" else "on"


class MultiWayManager:
    """Coordinate multi-way groups safely and without feedback loops."""

    def __init__(self, hass: HomeAssistant, store: MultiWayStore) -> None:
        self.hass = hass
        self.store = store
        self._groups: dict[str, dict[str, Any]] = {}
        self._entity_to_group: dict[str, str] = {}
        self._runtime: dict[str, GroupRuntime] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._activity: deque[dict[str, Any]] = deque(maxlen=100)
        self._state_unsub = None
        self._watchdog_unsub = None
        self._startup_unsub = None
        self._started = False
        self._ready = False
        self._verification_tasks: set[asyncio.Task] = set()
        self._event_queues: dict[str, asyncio.Queue[tuple[Event, float]]] = {}
        self._event_workers: dict[str, asyncio.Task] = {}
        self._source_reconcile_tasks: dict[str, asyncio.Task] = {}
        self._learn_sessions: dict[str, dict[str, Any]] = {}

    async def async_start(self) -> None:
        """Start listeners and delayed startup reconciliation."""
        if self._started:
            return
        self._started = True
        await self.async_reload(reconcile=False)
        settings = self.store.settings()
        self._startup_unsub = async_call_later(
            self.hass,
            float(settings["startup_delay"]),
            self._async_startup_ready,
        )
        self._restart_watchdog()
        self._add_activity(
            event="engine_started",
            result="pending",
            message=f"Startup protection active for {settings['startup_delay']} seconds",
        )

    async def async_stop(self) -> None:
        """Stop all listeners and flush state."""
        self._started = False
        self._ready = False
        for unsub in (self._state_unsub, self._watchdog_unsub, self._startup_unsub):
            if unsub:
                unsub()
        self._state_unsub = None
        self._watchdog_unsub = None
        self._startup_unsub = None
        for session_id in list(self._learn_sessions):
            self.cancel_learn(session_id)
        tasks = [
            *self._verification_tasks,
            *self._event_workers.values(),
            *self._source_reconcile_tasks.values(),
        ]
        self._verification_tasks.clear()
        self._event_workers.clear()
        self._source_reconcile_tasks.clear()
        self._event_queues.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await self.store.async_close()

    @callback
    def _async_startup_ready(self, _now) -> None:
        self._startup_unsub = None
        self._ready = True
        self.hass.async_create_task(self._async_initialize_groups())

    async def _async_initialize_groups(self) -> None:
        """Choose a safe authority for each group after startup settles."""
        for group_id, group in self._groups.items():
            if not group.get("enabled", True):
                self._update_health(group_id)
                continue
            runtime = self._runtime[group_id]
            output = self.hass.states.get(group["output"])
            if output and output.state in VALID_STATES:
                runtime.desired_state = output.state
            elif group.get("last_state") in VALID_STATES:
                runtime.desired_state = group["last_state"]
            else:
                runtime.desired_state = self._first_valid_controller_state(group)

            if runtime.desired_state in VALID_STATES:
                self.store.set_last_state(group_id, runtime.desired_state)
                # Never force a missing/offline output at startup. If output is online,
                # it is the authority and we only reconcile controllers to it.
                if output and output.state in VALID_STATES:
                    await self._async_sync_controllers(
                        group,
                        runtime.desired_state,
                        transaction_id="startup",
                        wait=False,
                    )
            self._update_health(group_id)

        self._add_activity(
            event="engine_ready",
            result="success",
            message="Startup protection ended; groups reconciled",
        )
        self._notify_all()

    async def async_reload(self, *, reconcile: bool = True) -> None:
        """Reload groups/settings after configuration changes."""
        groups = self.store.groups()
        self._groups = {group["id"]: group for group in groups}
        self._entity_to_group.clear()
        for group in groups:
            self._entity_to_group[group["output"]] = group["id"]
            fallback = group.get("behavior", {}).get("fallback_output")
            if fallback:
                self._entity_to_group[fallback] = group["id"]
            for controller in group["controllers"]:
                self._entity_to_group[controller["entity_id"]] = group["id"]
            self._runtime.setdefault(group["id"], GroupRuntime())
            self._locks.setdefault(group["id"], asyncio.Lock())

        valid_ids = set(self._groups)
        self._runtime = {
            group_id: runtime
            for group_id, runtime in self._runtime.items()
            if group_id in valid_ids
        }
        self._locks = {
            group_id: lock for group_id, lock in self._locks.items() if group_id in valid_ids
        }
        # Keep one FIFO edge queue per group. This guarantees that rapid ON -> OFF
        # transitions are handled in arrival order instead of racing independent tasks.
        for group_id in valid_ids:
            self._event_queues.setdefault(group_id, asyncio.Queue())
        for group_id in list(self._event_queues):
            if group_id not in valid_ids:
                self._event_queues.pop(group_id, None)
                worker = self._event_workers.pop(group_id, None)
                if worker:
                    worker.cancel()
                reconcile = self._source_reconcile_tasks.pop(group_id, None)
                if reconcile:
                    reconcile.cancel()

        settings = self.store.settings()
        old_activity = list(self._activity)[-int(settings["history_size"]) :]
        self._activity = deque(old_activity, maxlen=int(settings["history_size"]))
        self._resubscribe_states()
        self._restart_watchdog()
        self._refresh_repairs()
        async_dispatcher_send(self.hass, SIGNAL_GROUPS_UPDATED)

        if reconcile and self._ready:
            for group_id in self._groups:
                await self.async_sync_group(group_id)
        self._notify_all()

    def _active_output(self, group: dict[str, Any]) -> str:
        """Return primary output, or configured fallback when primary is unavailable."""
        primary = group["output"]
        state = self.hass.states.get(primary)
        if state is not None and state.state not in UNAVAILABLE_STATES:
            return primary
        fallback = group.get("behavior", {}).get("fallback_output")
        if fallback:
            fallback_state = self.hass.states.get(fallback)
            if fallback_state is not None and fallback_state.state not in UNAVAILABLE_STATES:
                return fallback
        return primary

    def _resubscribe_states(self) -> None:
        if self._state_unsub:
            self._state_unsub()
            self._state_unsub = None
        entity_ids = list(self._entity_to_group)
        if entity_ids:
            self._state_unsub = async_track_state_change_event(
                self.hass, entity_ids, self._async_state_event
            )

    def _restart_watchdog(self) -> None:
        if self._watchdog_unsub:
            self._watchdog_unsub()
            self._watchdog_unsub = None
        if not self._started:
            return
        from datetime import timedelta

        interval = max(10.0, float(self.store.settings()["watchdog_interval"]))
        self._watchdog_unsub = async_track_time_interval(
            self.hass, self._async_watchdog_tick, timedelta(seconds=interval)
        )

    @callback
    def _async_state_event(self, event: Event) -> None:
        """Queue physical edges in exact arrival order for their group."""
        entity_id = event.data.get("entity_id")
        group_id = self._entity_to_group.get(entity_id)
        if not group_id or group_id not in self._groups:
            return
        queue = self._event_queues.setdefault(group_id, asyncio.Queue())
        queue.put_nowait((event, monotonic()))
        worker = self._event_workers.get(group_id)
        if worker is None or worker.done():
            worker = self.hass.async_create_task(self._async_drain_group_events(group_id))
            self._event_workers[group_id] = worker

    async def _async_drain_group_events(self, group_id: str) -> None:
        """Drain one group's edge queue serially; never reorder rapid presses."""
        queue = self._event_queues.get(group_id)
        if queue is None:
            return
        try:
            while True:
                try:
                    event, received_at = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return
                try:
                    await self._async_handle_state_event(event, received_at)
                finally:
                    queue.task_done()
        finally:
            current = self._event_workers.get(group_id)
            if current is asyncio.current_task():
                self._event_workers.pop(group_id, None)
            if queue and not queue.empty() and group_id in self._groups:
                worker = self.hass.async_create_task(self._async_drain_group_events(group_id))
                self._event_workers[group_id] = worker

    async def _async_handle_state_event(self, event: Event, received_at: float) -> None:
        if not self._ready:
            return
        entity_id: str = event.data["entity_id"]
        group_id = self._entity_to_group.get(entity_id)
        if not group_id or group_id not in self._groups:
            return
        group = self._groups[group_id]
        if not group.get("enabled", True):
            return

        old: State | None = event.data.get("old_state")
        new: State | None = event.data.get("new_state")
        if new is None:
            self._update_health(group_id)
            self._notify(group_id)
            return

        runtime = self._runtime[group_id]
        self._cleanup_pending(runtime)
        event_context_id = event.context.id if event.context else None
        own_command = runtime.command_contexts.pop(event_context_id, None) if event_context_id else None
        if own_command:
            pending = runtime.pending.get(entity_id)
            if pending and pending.context_id == event_context_id:
                runtime.pending.pop(entity_id, None)
            # Context proves this state change came from our own service call. Ignore
            # even stale echoes from older transactions so they can never become input.
            self._update_health(group_id)
            self._notify(group_id)
            return
        pending = runtime.pending.get(entity_id)
        if pending:
            if new.state == pending.expected_state and pending.transaction_id == runtime.last_transaction_id:
                # Fallback for integrations that do not propagate HA Context.
                runtime.pending.pop(entity_id, None)
                self._update_health(group_id)
                self._notify(group_id)
                return
            if new.state != pending.expected_state:
                # Opposite edge always wins, even inside the suppression/debounce window.
                runtime.pending.pop(entity_id, None)
                runtime.rapid_edges_seen += 1

        old_state = old.state if old else None
        new_state = new.state
        if old_state == new_state and self._controller_mode(group, entity_id) != MODE_EVENT:
            return

        if new_state in UNAVAILABLE_STATES:
            self._add_activity(
                group_id=group_id, source=entity_id, event="entity_offline",
                result="warning", message=f"{entity_id} became {new_state}",
            )
            self._update_health(group_id)
            self._refresh_repairs_for_group(group_id)
            self._notify(group_id)
            return

        recovered = old is None or old_state in UNAVAILABLE_STATES
        if recovered:
            await self._async_handle_recovery(group, entity_id, new_state)
            return

        runtime.input_sequence += 1
        input_sequence = runtime.input_sequence
        engine_delay_ms = int((monotonic() - received_at) * 1000)
        runtime.last_engine_latency_ms = engine_delay_ms

        if entity_id in {group["output"], group.get("behavior", {}).get("fallback_output")} :
            if new_state not in VALID_STATES:
                return
            if (
                group.get("behavior", {}).get("source_policy", "latest_physical") == "latest_physical"
                and runtime.authority_source
                and runtime.authority_source != entity_id
                and runtime.authority_state in VALID_STATES
                and monotonic() < runtime.authority_until
            ):
                if new_state == runtime.authority_state:
                    self._add_activity(
                        group_id=group_id, source=entity_id, event="authority_confirmed",
                        action=new_state, result="success",
                        message=f"Output confirmed latest source {runtime.authority_source}",
                    )
                    self._update_health(group_id)
                    self._notify(group_id)
                    return
                # A mismatching Main edge inside the source-authority window is
                # treated as a stale command echo. Reassert only the newest source
                # state; never adopt the older edge as group truth.
                self._add_activity(
                    group_id=group_id, source=entity_id, event="stale_output_edge",
                    action=new_state, result="warning",
                    message=f"Ignored during authority lease of {runtime.authority_source}",
                )
                runtime.input_sequence += 1
                self.hass.async_create_task(
                    self.async_request_state(
                        group_id, runtime.authority_state, source=runtime.authority_source,
                        origin="physical_controller", input_sequence=runtime.input_sequence,
                        engine_delay_ms=engine_delay_ms,
                    )
                )
                return
            if group.get("behavior", {}).get("source_policy", "latest_physical") == "latest_physical":
                generation = self._claim_source_authority(group, runtime, entity_id, new_state)
            else:
                generation = None
                runtime.authority_source = None
                runtime.authority_state = None
                runtime.authority_until = 0.0
            async with self._locks[group_id]:
                await self._async_accept_output_change(group, new_state, entity_id)
            if generation is not None:
                self._schedule_source_reconcile(group_id, entity_id, generation)
            return

        controller = self._controller(group, entity_id)
        if controller is None:
            return

        mode = controller["mode"]
        mapped_state = self._controller_to_group_state(controller, new_state)
        target: str | None = None
        if mode == MODE_MIRROR and mapped_state in VALID_STATES:
            target = mapped_state
        elif mode == MODE_TOGGLE and old_state != new_state:
            target = self._toggle_target(group_id)
        elif mode == MODE_MOMENTARY_ON and mapped_state == "on":
            target = self._toggle_target(group_id)
        elif mode == MODE_MOMENTARY_OFF and mapped_state == "off":
            target = self._toggle_target(group_id)
        elif mode == MODE_EVENT and old_state != new_state:
            target = self._toggle_target(group_id)
        elif mode == MODE_FOLLOW:
            return

        if target not in VALID_STATES:
            return
        if self._debounced(group, runtime, entity_id, target):
            return

        generation = None
        if (
            mode == MODE_MIRROR
            and group.get("behavior", {}).get("source_policy", "latest_physical") == "latest_physical"
        ):
            generation = self._claim_source_authority(
                group, runtime, entity_id, target
            )
        elif runtime.authority_source and runtime.authority_source != entity_id:
            runtime.authority_source = None
            runtime.authority_state = None
            runtime.authority_until = 0.0

        await self.async_request_state(
            group_id,
            target,
            source=entity_id,
            origin="physical_controller",
            input_sequence=input_sequence,
            engine_delay_ms=engine_delay_ms,
        )
        if generation is not None:
            self._schedule_source_reconcile(group_id, entity_id, generation)

    async def _async_handle_recovery(
        self, group: dict[str, Any], entity_id: str, new_state: str
    ) -> None:
        group_id = group["id"]
        runtime = self._runtime[group_id]
        runtime.recovering = True
        self._notify(group_id)

        if entity_id == group["output"] and new_state in VALID_STATES:
            if runtime.pending_offline_state in VALID_STATES:
                pending_state = runtime.pending_offline_state
                applied = await self.async_request_state(
                    group_id, pending_state, source=entity_id, origin="output_recovery"
                )
                if applied:
                    runtime.pending_offline_state = None
            else:
                policy = group["behavior"].get("output_restore_policy", "adopt")
                if policy == "adopt" or runtime.desired_state not in VALID_STATES:
                    runtime.desired_state = new_state
                    self.store.set_last_state(group_id, new_state)
                    await self._async_sync_controllers(
                        group, new_state, transaction_id="recovery", wait=False
                    )
                else:
                    await self.async_request_state(
                        group_id, runtime.desired_state, source=entity_id, origin="output_recovery"
                    )
        elif runtime.desired_state in VALID_STATES:
            controller = self._controller(group, entity_id)
            if controller and controller.get("reflect_state"):
                await self._async_command_controller(
                    group,
                    controller,
                    runtime.desired_state,
                    transaction_id="recovery",
                    wait=False,
                )

        runtime.recovering = False
        self._add_activity(
            group_id=group_id,
            source=entity_id,
            event="entity_recovered",
            result="success",
            message=f"{entity_id} recovered without being treated as a user press",
        )
        self._update_health(group_id)
        self._refresh_repairs_for_group(group_id)
        self._notify(group_id)

    async def _async_accept_output_change(
        self, group: dict[str, Any], state: str, source: str
    ) -> None:
        group_id = group["id"]
        runtime = self._runtime[group_id]
        runtime.desired_state = state
        runtime.last_source = source
        runtime.last_action = state
        runtime.last_changed = _utcnow()
        runtime.last_error = None
        self.store.set_last_state(group_id, state)
        txid = self._txid()
        runtime.last_transaction_id = txid
        started = monotonic()
        performance = self._performance_mode(group)
        results = await self._async_sync_controllers(
            group,
            state,
            transaction_id=txid,
            wait=performance == PERFORMANCE_SAFE,
            blocking=performance == PERFORMANCE_SAFE,
        )
        runtime.last_latency_ms = int((monotonic() - started) * 1000)
        self._add_activity(
            group_id=group_id,
            transaction_id=txid,
            source=source,
            event="output_changed",
            action=state,
            result="success" if all(results) else "partial",
            latency_ms=runtime.last_latency_ms,
        )
        self._update_health(group_id)
        self._notify(group_id)

    async def async_request_state(
        self,
        group_id: str,
        state: str,
        *,
        source: str = "virtual",
        origin: str = "service",
        input_sequence: int | None = None,
        engine_delay_ms: int | None = None,
    ) -> bool:
        """Request a state transaction using the configured performance profile."""
        if state not in VALID_STATES:
            raise ValueError("State must be on or off")
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Group not found")
        if not group.get("enabled", True):
            raise ValueError("Group is disabled")

        async with self._locks[group_id]:
            runtime = self._runtime[group_id]
            if input_sequence is not None and input_sequence < runtime.input_sequence:
                runtime.stale_transactions_discarded += 1
                return True
            txid = self._txid()
            started = monotonic()
            performance = self._performance_mode(group)
            confirm = self._confirm_output(group)

            runtime.last_transaction_id = txid
            runtime.last_source = source
            runtime.last_action = state
            runtime.last_changed = _utcnow()
            runtime.last_error = None
            if engine_delay_ms is not None:
                runtime.last_engine_latency_ms = engine_delay_ms

            # Instant mode is optimistic by design: publish the desired state and
            # dispatch the physical output immediately. A version-aware background
            # verifier confirms/retries it without holding the group lock.
            if performance == PERFORMANCE_INSTANT:
                runtime.desired_state = state
                self.store.set_last_state(group_id, state)
                self._notify(group_id)

                output_ok = await self._async_command_output(
                    group,
                    state,
                    transaction_id=txid,
                    wait_override=False,
                    blocking=False,
                )
                if not output_ok:
                    return self._record_immediate_output_failure(
                        group, runtime, txid, state, source, origin, started
                    )

                controller_results = await self._async_sync_controllers(
                    group,
                    state,
                    transaction_id=txid,
                    wait=False,
                    blocking=False,
                    skip_entity_id=source if origin in {"physical_controller", "test_center", "source_settle"} else None,
                )
                runtime.last_latency_ms = int((monotonic() - started) * 1000)
                self._add_activity(
                    group_id=group_id,
                    transaction_id=txid,
                    source=source,
                    event="transaction_dispatched",
                    action=state,
                    result="success" if all(controller_results) else "partial",
                    latency_ms=runtime.last_latency_ms,
                    origin=origin,
                    message="Instant dispatch; output verification continues in background"
                    if confirm
                    else "Instant dispatch without output confirmation",
                )
                self._update_health(group_id)
                self._notify(group_id)
                if confirm:
                    self._schedule_fast_verification(group_id, state, txid, source, origin)
                # Physical-source settle is scheduled from the state-event handler,
                # where the authoritative generation is known.
                return all(controller_results)

            # Balanced: dispatch output without blocking the service handler, but
            # confirm the physical state before updating followers. Safe: preserve
            # the fully blocking/confirmed behavior for maximum determinism.
            self._notify(group_id)
            safe = performance == PERFORMANCE_SAFE
            output_ok = await self._async_command_output(
                group,
                state,
                transaction_id=txid,
                wait_override=confirm,
                blocking=safe,
            )
            if not output_ok:
                return self._record_immediate_output_failure(
                    group, runtime, txid, state, source, origin, started
                )

            runtime.consecutive_output_failures = 0
            runtime.desired_state = state
            self.store.set_last_state(group_id, state)
            self._delete_issue(f"output_unresponsive_{group_id}")
            controller_results = await self._async_sync_controllers(
                group,
                state,
                transaction_id=txid,
                wait=safe,
                blocking=safe,
                skip_entity_id=source if origin in {"physical_controller", "test_center", "source_settle"} else None,
            )
            runtime.last_latency_ms = int((monotonic() - started) * 1000)
            success = all(controller_results)
            if not success:
                runtime.last_error = "One or more controllers could not be synchronized"

            self._add_activity(
                group_id=group_id,
                transaction_id=txid,
                source=source,
                event="transaction",
                action=state,
                result="success" if success else "partial",
                latency_ms=runtime.last_latency_ms,
                origin=origin,
            )
            self._update_health(group_id)
            self._refresh_repairs_for_group(group_id)
            self._notify(group_id)
            # Physical-source settle is scheduled from the state-event handler.
            return success

    def _record_immediate_output_failure(
        self,
        group: dict[str, Any],
        runtime: GroupRuntime,
        txid: str,
        state: str,
        source: str,
        origin: str,
        started: float,
    ) -> bool:
        group_id = group["id"]
        runtime.consecutive_output_failures += 1
        active_output = self._active_output(group)
        runtime.last_error = f"Output {active_output} could not accept {state}"
        output_state = self.hass.states.get(active_output)
        if output_state and output_state.state in VALID_STATES:
            runtime.desired_state = output_state.state
            self.store.set_last_state(group_id, output_state.state)
        elif origin in {"physical_controller", "test_center"}:
            # Preserve only the newest requested physical state while the Main is offline.
            # Recovery will apply this one state, never replay a queue of stale commands.
            runtime.desired_state = state
            runtime.pending_offline_state = state
            self.store.set_last_state(group_id, state)
        runtime.last_latency_ms = int((monotonic() - started) * 1000)
        self._add_activity(
            group_id=group_id,
            transaction_id=txid,
            source=source,
            event="transaction",
            action=state,
            result="failed",
            latency_ms=runtime.last_latency_ms,
            message=runtime.last_error,
            origin=origin,
        )
        self._update_health(group_id)
        self._refresh_repairs_for_group(group_id)
        self._notify(group_id)
        return False

    def _schedule_fast_verification(
        self, group_id: str, state: str, txid: str, source: str, origin: str
    ) -> None:
        task = self.hass.async_create_task(
            self._async_verify_fast_transaction(group_id, state, txid, source, origin)
        )
        self._verification_tasks.add(task)
        task.add_done_callback(self._verification_tasks.discard)

    async def _async_verify_fast_transaction(
        self, group_id: str, state: str, txid: str, source: str, origin: str
    ) -> None:
        group = self._groups.get(group_id)
        runtime = self._runtime.get(group_id)
        if not group or not runtime:
            return
        timeout = self._group_timeout(group)
        active_output = self._active_output(group)
        confirmed = await self._async_wait_for_state(active_output, state, timeout)
        if runtime.last_transaction_id != txid or runtime.desired_state != state:
            return
        if not confirmed:
            confirmed = await self._async_command_entity(
                active_output,
                state,
                transaction_id=txid,
                wait=True,
                timeout=timeout,
                retries=self._group_retries(group),
                blocking=False,
            )
        if runtime.last_transaction_id != txid or runtime.desired_state != state:
            return
        if confirmed:
            runtime.consecutive_output_failures = 0
            runtime.last_error = None
            self._delete_issue(f"output_unresponsive_{group_id}")
            self._add_activity(
                group_id=group_id,
                transaction_id=txid,
                source=source,
                event="output_confirmed",
                action=state,
                result="success",
                origin=origin,
            )
        else:
            runtime.consecutive_output_failures += 1
            runtime.last_error = f"Output {active_output} did not confirm {state}"
            actual = self.hass.states.get(active_output)
            if actual and actual.state in VALID_STATES:
                runtime.desired_state = actual.state
                self.store.set_last_state(group_id, actual.state)
                await self._async_sync_controllers(
                    group,
                    actual.state,
                    transaction_id=f"rollback_{txid}",
                    wait=False,
                    blocking=False,
                )
            self._add_activity(
                group_id=group_id,
                transaction_id=txid,
                source=source,
                event="output_confirmation_failed",
                action=state,
                result="failed",
                message=runtime.last_error,
                origin=origin,
            )
        self._update_health(group_id)
        self._refresh_repairs_for_group(group_id)
        self._notify(group_id)

    async def _async_command_output(
        self,
        group: dict[str, Any],
        state: str,
        *,
        transaction_id: str,
        wait_override: bool | None = None,
        blocking: bool = False,
    ) -> bool:
        output = self._active_output(group)
        current = self.hass.states.get(output)
        if current and current.state == state:
            return True
        if current is None or current.state in UNAVAILABLE_STATES:
            return False

        if output != group["output"]:
            self._add_activity(
                group_id=group["id"], source=output, event="fallback_output_used",
                action=state, result="warning", message=f"Primary output {group['output']} unavailable",
            )
        confirm = self._confirm_output(group) if wait_override is None else wait_override
        return await self._async_command_entity(
            output,
            state,
            transaction_id=transaction_id,
            wait=bool(confirm),
            timeout=self._group_timeout(group),
            retries=self._group_retries(group),
            blocking=blocking,
        )

    async def _async_sync_controllers(
        self,
        group: dict[str, Any],
        state: str,
        *,
        transaction_id: str,
        wait: bool,
        blocking: bool = False,
        skip_entity_id: str | None = None,
    ) -> list[bool]:
        tasks = []
        for controller in group["controllers"]:
            if controller["entity_id"] == skip_entity_id:
                continue
            if not controller.get("reflect_state"):
                continue
            tasks.append(
                self._async_command_controller(
                    group,
                    controller,
                    state,
                    transaction_id=transaction_id,
                    wait=wait,
                    blocking=blocking,
                )
            )
        if not tasks:
            return [True]
        return list(await asyncio.gather(*tasks, return_exceptions=False))

    async def _async_command_controller(
        self,
        group: dict[str, Any],
        controller: dict[str, Any],
        state: str,
        *,
        transaction_id: str,
        wait: bool,
        blocking: bool = False,
    ) -> bool:
        entity_id = controller["entity_id"]
        target = self._group_to_controller_state(controller, state)
        return await self._async_command_entity(
            entity_id,
            target,
            transaction_id=transaction_id,
            wait=wait,
            timeout=self._group_timeout(group),
            retries=self._group_retries(group),
            blocking=blocking,
        )

    async def _async_command_entity(
        self,
        entity_id: str,
        state: str,
        *,
        transaction_id: str,
        wait: bool,
        timeout: float,
        retries: int,
        blocking: bool = False,
    ) -> bool:
        current = self.hass.states.get(entity_id)
        if current is None or current.state in UNAVAILABLE_STATES:
            return False
        if current.state == state:
            return True

        domain = entity_id.split(".", 1)[0]
        if domain not in COMMANDABLE_DOMAINS:
            return False
        service = "turn_on" if state == "on" else "turn_off"

        group_id = self._entity_to_group.get(entity_id)
        runtime = self._runtime.get(group_id) if group_id else None
        command_started = monotonic()
        if runtime:
            metric = runtime.entity_metrics.setdefault(
                entity_id, {"commands": 0, "failures": 0, "last_latency_ms": None, "last_action": None, "last_result": None, "last_timestamp": None}
            )
            metric["commands"] += 1
            metric["last_action"] = state
        for attempt in range(retries + 1):
            command_context = Context()
            if runtime:
                command = PendingCommand(
                    expected_state=state,
                    transaction_id=transaction_id,
                    expires=monotonic() + timeout + 2,
                    context_id=command_context.id,
                    source_entity=runtime.last_source,
                )
                runtime.pending[entity_id] = command
                runtime.command_contexts[command_context.id] = command
            try:
                await self.hass.services.async_call(
                    domain,
                    service,
                    {ATTR_ENTITY_ID: entity_id},
                    blocking=blocking,
                    context=command_context,
                )
                if not wait:
                    if runtime:
                        self._record_entity_metric(runtime, entity_id, True, command_started)
                    return True
                if await self._async_wait_for_state(entity_id, state, timeout):
                    if runtime:
                        self._record_entity_metric(runtime, entity_id, True, command_started)
                    return True
            except Exception as err:  # noqa: BLE001 - isolate third-party entity failures
                _LOGGER.warning(
                    "Command %s.%s failed for %s (attempt %s/%s): %s",
                    domain,
                    service,
                    entity_id,
                    attempt + 1,
                    retries + 1,
                    err,
                )
            if attempt < retries:
                await asyncio.sleep(min(0.5 * (attempt + 1), 1.5))

        if runtime:
            runtime.pending.pop(entity_id, None)
            self._record_entity_metric(runtime, entity_id, False, command_started)
        return False

    async def _async_wait_for_state(
        self, entity_id: str, target: str, timeout: float
    ) -> bool:
        current = self.hass.states.get(entity_id)
        if current and current.state == target:
            return True
        future: asyncio.Future[bool] = self.hass.loop.create_future()

        @callback
        def state_listener(event: Event) -> None:
            new_state: State | None = event.data.get("new_state")
            if new_state and new_state.state == target and not future.done():
                future.set_result(True)

        unsub = async_track_state_change_event(self.hass, [entity_id], state_listener)
        try:
            await asyncio.wait_for(future, timeout=timeout)
            return True
        except TimeoutError:
            return False
        finally:
            unsub()

    async def async_sync_group(self, group_id: str) -> bool:
        """Synchronize a group using the physical output as authority when available."""
        runtime = self._runtime.get(group_id)
        if runtime:
            runtime.test_mode_until = 0.0
            runtime.suppressed_until.clear()
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Group not found")
        if not group.get("enabled", True):
            return False
        active_output = self._active_output(group)
        output = self.hass.states.get(active_output)
        if output and output.state in VALID_STATES:
            state = output.state
            runtime = self._runtime[group_id]
            runtime.desired_state = state
            self.store.set_last_state(group_id, state)
            results = await self._async_sync_controllers(
                group, state, transaction_id="manual_sync", wait=True
            )
            self._update_health(group_id)
            self._notify(group_id)
            return all(results)
        desired = self._runtime[group_id].desired_state
        if desired in VALID_STATES:
            return await self.async_request_state(
                group_id, desired, source="manual_sync", origin="manual_sync"
            )
        return False

    async def async_sync_all(self) -> dict[str, bool]:
        """Synchronize all groups."""
        result: dict[str, bool] = {}
        for group_id in self._groups:
            try:
                result[group_id] = await self.async_sync_group(group_id)
            except Exception:  # noqa: BLE001
                result[group_id] = False
        return result

    async def async_set_enabled(self, group_id: str, enabled: bool) -> dict[str, Any]:
        """Enable/disable a group and reload listeners/entities."""
        group = await self.store.async_set_enabled(group_id, enabled)
        await self.async_reload(reconcile=enabled)
        self._add_activity(
            group_id=group_id,
            event="group_enabled" if enabled else "group_disabled",
            result="success",
        )
        return group

    def test_group(self, group_id: str) -> dict[str, Any]:
        """Run a non-destructive readiness snapshot for a group."""
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Group not found")
        status = self.status(group_id)
        metrics = status.get("entity_metrics", {})
        entities = []
        test_members = [("output", group["output"])]
        fallback = group.get("behavior", {}).get("fallback_output")
        if fallback:
            test_members.append(("fallback_output", fallback))
        test_members.extend(("controller", c["entity_id"]) for c in group["controllers"])
        for role, entity_id in test_members:
            state = self.hass.states.get(entity_id)
            domain = entity_id.split(".", 1)[0]
            action = None
            if domain in COMMANDABLE_DOMAINS and state and state.state in VALID_STATES:
                action = "toggle"
            elif domain in PRESSABLE_DOMAINS:
                action = "press"
            entities.append(
                {
                    "entity_id": entity_id, "role": role, "domain": domain,
                    "exists": state is not None, "state": state.state if state else "missing",
                    "commandable": action is not None, "test_action": action,
                    "metrics": metrics.get(entity_id, {}),
                }
            )
        recent = [item for item in self.activity(100) if item.get("group_id") == group_id][:10]
        return {
            "group_id": group_id, "name": group["name"], "health": status["health"],
            "runtime": status, "entities": entities, "activity": recent,
        }

    async def async_test_entity_action(
        self, group_id: str, entity_id: str
    ) -> dict[str, Any]:
        """Exercise one member through the real multi-way path (end-to-end test)."""
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Group not found")
        members = {group["output"], *(c["entity_id"] for c in group["controllers"])}
        if entity_id not in members:
            raise ValueError("Entity does not belong to this group")
        current = self.hass.states.get(entity_id)
        if current is None or current.state in UNAVAILABLE_STATES:
            raise ValueError("Entity is missing or unavailable")

        domain = entity_id.split(".", 1)[0]
        runtime = self._runtime[group_id]
        timeout = min(max(self._group_timeout(group), 1.0), 6.0)
        started = monotonic()
        txid = f"e2e_test_{self._txid()}"
        before_group = runtime.desired_state
        target: str | None = None
        expected_group: str | None = None
        action: str

        if domain in COMMANDABLE_DOMAINS:
            if current.state not in VALID_STATES:
                raise ValueError("Entity does not expose an ON/OFF state")
            target = _invert_state(current.state)
            action = "toggle"
            if entity_id == group["output"]:
                expected_group = target
            else:
                controller = self._controller(group, entity_id)
                if controller and controller["mode"] == MODE_MIRROR:
                    expected_group = self._controller_to_group_state(controller, target)
                elif controller and controller["mode"] != MODE_FOLLOW:
                    expected_group = _invert_state(
                        before_group if before_group in VALID_STATES else "off"
                    )
            service = "turn_on" if target == "on" else "turn_off"
            await self.hass.services.async_call(
                domain, service, {ATTR_ENTITY_ID: entity_id}, blocking=False, context=Context()
            )
            source_ok = await self._async_wait_for_state(entity_id, target, timeout)
        elif domain in PRESSABLE_DOMAINS:
            action = "press"
            if before_group in VALID_STATES:
                expected_group = _invert_state(before_group)
            await self.hass.services.async_call(
                domain, "press", {ATTR_ENTITY_ID: entity_id}, blocking=False, context=Context()
            )
            source_ok = True
        else:
            raise ValueError("This entity is read-only and cannot be exercised")

        output_ok = True
        if expected_group in VALID_STATES:
            output_ok = await self._async_wait_for_state(self._active_output(group), expected_group, timeout)
        await asyncio.sleep(0.05)
        latency_ms = int((monotonic() - started) * 1000)
        ok = bool(source_ok and output_ok)
        self._add_activity(
            group_id=group_id, transaction_id=txid, source=entity_id,
            event="end_to_end_test", action=target or action,
            result="success" if ok else "failed", latency_ms=latency_ms,
            origin="test_center",
            message="Real group test: source action propagated through normal multi-way logic",
        )
        self._update_health(group_id)
        self._notify(group_id)
        return {
            "ok": ok, "entity_id": entity_id, "action": action, "target": target,
            "expected_group_state": expected_group, "latency_ms": latency_ms,
            "engine_latency_ms": runtime.last_engine_latency_ms,
            "group": self.test_group(group_id),
        }

    async def async_rapid_toggle_test(
        self, group_id: str, entity_id: str, count: int = 4, interval_ms: int = 120
    ) -> dict[str, Any]:
        """Rapidly toggle one real member and verify final group state."""
        group = self._groups.get(group_id)
        if not group:
            raise ValueError("Group not found")
        members = {group["output"], *(c["entity_id"] for c in group["controllers"])}
        if entity_id not in members:
            raise ValueError("Entity does not belong to this group")
        state = self.hass.states.get(entity_id)
        domain = entity_id.split(".", 1)[0]
        if not state or state.state not in VALID_STATES or domain not in COMMANDABLE_DOMAINS:
            raise ValueError("Rapid test requires a commandable ON/OFF entity")
        count = max(2, min(int(count), 10))
        interval = max(50, min(int(interval_ms), 1000)) / 1000
        started = monotonic()
        target = state.state
        for _ in range(count):
            target = _invert_state(target)
            await self.hass.services.async_call(
                domain, "turn_on" if target == "on" else "turn_off",
                {ATTR_ENTITY_ID: entity_id}, blocking=False, context=Context()
            )
            await asyncio.sleep(interval)
        source_ok = await self._async_wait_for_state(entity_id, target, min(self._group_timeout(group), 6.0))
        controller = self._controller(group, entity_id)
        if entity_id == group["output"]:
            expected_group = target
        elif controller and controller["mode"] == MODE_MIRROR:
            expected_group = self._controller_to_group_state(controller, target)
        else:
            expected_group = self._runtime[group_id].desired_state
        output_ok = expected_group in VALID_STATES and await self._async_wait_for_state(
            self._active_output(group), expected_group, min(self._group_timeout(group), 6.0)
        )
        latency_ms = int((monotonic() - started) * 1000)
        ok = bool(source_ok and output_ok)
        self._add_activity(
            group_id=group_id, source=entity_id, event="rapid_toggle_test",
            action=target, result="success" if ok else "failed", latency_ms=latency_ms,
            origin="test_center", message=f"{count} edges at {int(interval*1000)} ms interval",
        )
        return {
            "ok": ok, "entity_id": entity_id, "count": count,
            "interval_ms": int(interval * 1000), "final_source_state": target,
            "expected_group_state": expected_group,
            "actual_output_state": self.hass.states.get(self._active_output(group)).state if self.hass.states.get(self._active_output(group)) else "missing",
            "latency_ms": latency_ms, "group": self.test_group(group_id),
        }

    @callback
    def _async_watchdog_tick(self, _now) -> None:
        if self._ready:
            self.hass.async_create_task(self._async_watchdog())

    async def _async_watchdog(self) -> None:
        """Safety watchdog: heal missed updates without becoming primary control logic."""
        for group_id, group in self._groups.items():
            if not group.get("enabled", True):
                self._update_health(group_id)
                continue
            runtime = self._runtime[group_id]
            self._cleanup_pending(runtime)
            self._cleanup_suppressed(runtime)
            self._update_health(group_id)
            if not group["behavior"].get("auto_heal", True):
                continue
            if runtime.desired_state not in VALID_STATES:
                continue
            active_output = self._active_output(group)
            output = self.hass.states.get(active_output)
            if (
                group.get("behavior", {}).get("source_policy", "latest_physical") == "output_authority"
                and output and output.state in VALID_STATES and output.state != runtime.desired_state
            ):
                runtime.desired_state = output.state
                self.store.set_last_state(group_id, output.state)
            if output and output.state in VALID_STATES:
                await self._async_sync_controllers(
                    group,
                    runtime.desired_state,
                    transaction_id="watchdog",
                    wait=False,
                )
            self._update_health(group_id)
            self._refresh_repairs_for_group(group_id)
            self._notify(group_id)

    def status(self, group_id: str) -> dict[str, Any]:
        """Return runtime status plus physical entity states."""
        group = self._groups.get(group_id)
        if not group:
            return {"health": "missing_group"}
        runtime = self._runtime[group_id]
        self._update_health(group_id)
        members = []
        output_state = self.hass.states.get(group["output"])
        members.append(
            {
                "entity_id": group["output"],
                "role": "output",
                "state": output_state.state if output_state else "missing",
                "metrics": runtime.entity_metrics.get(group["output"], {}),
            }
        )
        fallback = group.get("behavior", {}).get("fallback_output")
        if fallback:
            fallback_state = self.hass.states.get(fallback)
            members.append({
                "entity_id": fallback, "role": "fallback_output",
                "state": fallback_state.state if fallback_state else "missing",
                "metrics": runtime.entity_metrics.get(fallback, {}),
            })
        for controller in group["controllers"]:
            state = self.hass.states.get(controller["entity_id"])
            members.append(
                {
                    "entity_id": controller["entity_id"],
                    "role": "controller",
                    "mode": controller["mode"],
                    "reflect_state": controller["reflect_state"],
                    "invert": controller["invert"],
                    "state": state.state if state else "missing",
                    "metrics": runtime.entity_metrics.get(controller["entity_id"], {}),
                }
            )
        return {**runtime.as_dict(), "members": members}

    def summary(self) -> dict[str, Any]:
        """Return integration-wide health metrics."""
        statuses = [self.status(group_id) for group_id in self._groups]
        return {
            "groups": len(statuses),
            "enabled": sum(
                1 for group in self._groups.values() if group.get("enabled", True)
            ),
            "healthy": sum(1 for status in statuses if status["health"] == HEALTH_HEALTHY),
            "degraded": sum(
                1
                for status in statuses
                if status["health"] not in {HEALTH_HEALTHY, HEALTH_DISABLED}
            ),
            "controllers": sum(len(g["controllers"]) for g in self._groups.values()),
            "ready": self._ready,
        }

    def activity(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return newest activity entries first."""
        limit = max(1, min(limit, 1000))
        return list(reversed(list(self._activity)[-limit:]))

    def _update_health(self, group_id: str) -> None:
        group = self._groups.get(group_id)
        runtime = self._runtime.get(group_id)
        if not group or not runtime:
            return
        if not group.get("enabled", True):
            runtime.health = HEALTH_DISABLED
            return
        if runtime.recovering:
            runtime.health = HEALTH_RECOVERING
            return

        output = self.hass.states.get(group["output"])
        fallback_id = group.get("behavior", {}).get("fallback_output")
        fallback = self.hass.states.get(fallback_id) if fallback_id else None
        primary_ok = output is not None and output.state not in UNAVAILABLE_STATES
        fallback_ok = fallback is not None and fallback.state not in UNAVAILABLE_STATES
        if output is None and not fallback_ok:
            runtime.health = HEALTH_MISSING_OUTPUT
            return
        if not primary_ok and not fallback_ok:
            runtime.health = HEALTH_OUTPUT_OFFLINE
            return

        degraded = False
        mismatch = False
        for controller in group["controllers"]:
            state = self.hass.states.get(controller["entity_id"])
            if state is None or state.state in UNAVAILABLE_STATES:
                degraded = True
                continue
            if (
                controller.get("reflect_state")
                and runtime.desired_state in VALID_STATES
                and state.state in VALID_STATES
                and self._controller_to_group_state(controller, state.state)
                != runtime.desired_state
            ):
                mismatch = True
        if mismatch:
            runtime.health = HEALTH_OUT_OF_SYNC
        elif degraded:
            runtime.health = HEALTH_DEGRADED
        else:
            runtime.health = HEALTH_HEALTHY

    def _refresh_repairs(self) -> None:
        expected: set[str] = set()
        for group_id in self._groups:
            expected.update(self._refresh_repairs_for_group(group_id))

        registry = ir.async_get(self.hass)
        managed_prefixes = ("missing_output_", "missing_controller_", "output_unresponsive_")
        stale = [
            issue_id
            for (issue_domain, issue_id) in registry.issues
            if issue_domain == DOMAIN
            and issue_id.startswith(managed_prefixes)
            and issue_id not in expected
        ]
        for issue_id in stale:
            registry.async_delete(DOMAIN, issue_id)

    def _refresh_repairs_for_group(self, group_id: str) -> set[str]:
        expected: set[str] = set()
        group = self._groups.get(group_id)
        if not group:
            return expected
        output_issue = f"missing_output_{group_id}"
        output = self.hass.states.get(group["output"])
        if output is None:
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
            if self.hass.states.get(controller["entity_id"]) is None:
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

    def _create_issue(
        self,
        issue_id: str,
        translation_key: str,
        placeholders: dict[str, str],
        *,
        severity: ir.IssueSeverity,
    ) -> None:
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            issue_domain=DOMAIN,
            severity=severity,
            translation_key=translation_key,
            translation_placeholders=placeholders,
        )

    def _delete_issue(self, issue_id: str) -> None:
        ir.async_delete_issue(self.hass, DOMAIN, issue_id)

    def _first_valid_controller_state(self, group: dict[str, Any]) -> str | None:
        for controller in group["controllers"]:
            if controller["mode"] not in {MODE_MIRROR, MODE_FOLLOW}:
                continue
            state = self.hass.states.get(controller["entity_id"])
            if state and state.state in VALID_STATES:
                return self._controller_to_group_state(controller, state.state)
        return None

    def _toggle_target(self, group_id: str) -> str:
        current = self._runtime[group_id].desired_state
        if current not in VALID_STATES:
            group = self._groups[group_id]
            output = self.hass.states.get(self._active_output(group))
            current = output.state if output and output.state in VALID_STATES else "off"
        return _invert_state(current)

    @staticmethod
    def _controller(group: dict[str, Any], entity_id: str) -> dict[str, Any] | None:
        for controller in group["controllers"]:
            if controller["entity_id"] == entity_id:
                return controller
        return None

    def _controller_mode(self, group: dict[str, Any], entity_id: str) -> str | None:
        controller = self._controller(group, entity_id)
        return controller["mode"] if controller else None

    @staticmethod
    def _controller_to_group_state(controller: dict[str, Any], state: str) -> str:
        if state not in VALID_STATES:
            return state
        return _invert_state(state) if controller.get("invert") else state

    @staticmethod
    def _group_to_controller_state(controller: dict[str, Any], state: str) -> str:
        return _invert_state(state) if controller.get("invert") else state

    @staticmethod
    def _cleanup_pending(runtime: GroupRuntime) -> None:
        expired = [entity_id for entity_id, cmd in runtime.pending.items() if cmd.expired]
        for entity_id in expired:
            runtime.pending.pop(entity_id, None)
        expired_contexts = [context_id for context_id, cmd in runtime.command_contexts.items() if cmd.expired]
        for context_id in expired_contexts:
            runtime.command_contexts.pop(context_id, None)

    @staticmethod
    def _cleanup_suppressed(runtime: GroupRuntime) -> None:
        now = monotonic()
        expired = [entity_id for entity_id, until in runtime.suppressed_until.items() if until <= now]
        for entity_id in expired:
            runtime.suppressed_until.pop(entity_id, None)

    @staticmethod
    def _txid() -> str:
        return uuid4().hex[:10]

    def _performance_mode(self, group: dict[str, Any]) -> str:
        value = group.get("behavior", {}).get("performance_mode", PERFORMANCE_INSTANT)
        if value not in {PERFORMANCE_INSTANT, PERFORMANCE_BALANCED, PERFORMANCE_SAFE}:
            return PERFORMANCE_INSTANT
        return value

    def _confirm_output(self, group: dict[str, Any]) -> bool:
        behavior = group["behavior"]
        value = behavior.get("confirm_output")
        if value is None:
            value = self.store.settings()["confirm_output"]
        return bool(value)

    def _group_timeout(self, group: dict[str, Any]) -> float:
        value = group["behavior"].get("command_timeout")
        if value is None:
            value = self.store.settings()["command_timeout"]
        return max(0.5, float(value))

    def _group_retries(self, group: dict[str, Any]) -> int:
        value = group["behavior"].get("max_retries")
        if value is None:
            value = self.store.settings()["max_retries"]
        return max(0, min(int(value), 5))

    @staticmethod
    def _debounced(
        group: dict[str, Any], runtime: GroupRuntime, entity_id: str, semantic_state: str
    ) -> bool:
        """Suppress only duplicate semantic edges; opposite edges are never dropped."""
        debounce = max(0, int(group["behavior"].get("debounce_ms", 120))) / 1000
        now = monotonic()
        previous_time = runtime.last_input_time.get(entity_id, 0.0)
        previous_state = runtime.last_input_state.get(entity_id)
        runtime.last_input_time[entity_id] = now
        runtime.last_input_state[entity_id] = semantic_state
        if previous_state != semantic_state:
            if previous_time and now - previous_time < max(0.01, float(group["behavior"].get("rapid_settle_ms", 2600)) / 1000):
                runtime.rapid_edges_seen += 1
            return False
        return debounce > 0 and now - previous_time < debounce

    @staticmethod
    def _record_entity_metric(
        runtime: GroupRuntime, entity_id: str, success: bool, started: float
    ) -> None:
        metric = runtime.entity_metrics.setdefault(
            entity_id, {"commands": 0, "failures": 0, "last_latency_ms": None, "last_action": None, "last_result": None, "last_timestamp": None}
        )
        if not success:
            metric["failures"] += 1
        metric["last_latency_ms"] = int((monotonic() - started) * 1000)
        metric["last_result"] = "success" if success else "failed"
        metric["last_timestamp"] = _utcnow()

    def _claim_source_authority(
        self, group: dict[str, Any], runtime: GroupRuntime, source: str, state: str
    ) -> int:
        """Make the latest physical mirror/output source authoritative for settling."""
        settle_ms = max(250, min(int(group["behavior"].get("rapid_settle_ms", 2600)), 10000))
        runtime.authority_generation += 1
        runtime.authority_source = source
        runtime.authority_state = state
        runtime.authority_until = monotonic() + settle_ms / 1000
        return runtime.authority_generation

    def _schedule_source_reconcile(
        self, group_id: str, source: str, generation: int
    ) -> None:
        """Settle rapid physical input and converge the group to the source's final state."""
        previous = self._source_reconcile_tasks.pop(group_id, None)
        if previous and not previous.done():
            previous.cancel()
        task = self.hass.async_create_task(
            self._async_reconcile_source(group_id, source, generation)
        )
        self._source_reconcile_tasks[group_id] = task
        task.add_done_callback(
            lambda done, gid=group_id: self._source_reconcile_tasks.pop(gid, None)
            if self._source_reconcile_tasks.get(gid) is done else None
        )

    def _authoritative_source_state(
        self, group: dict[str, Any], source: str
    ) -> str | None:
        state = self.hass.states.get(source)
        if not state or state.state not in VALID_STATES:
            return None
        if source in {group.get("output"), group.get("behavior", {}).get("fallback_output")}:
            return state.state
        controller = self._controller(group, source)
        if not controller or controller.get("mode") != MODE_MIRROR:
            return None
        mapped = self._controller_to_group_state(controller, state.state)
        return mapped if mapped in VALID_STATES else None

    async def _async_reconcile_source(
        self, group_id: str, source: str, generation: int
    ) -> None:
        """Wait for the source to settle, then make every other member match it.

        This is intentionally independent of an individual transaction ID. Cloud
        integrations can publish rapid physical edges late; the authority generation
        follows the physical source, while older transaction verifiers are already
        version-aware and therefore cannot override the final state.
        """
        try:
            group = self._groups.get(group_id)
            runtime = self._runtime.get(group_id)
            if not group or not runtime:
                return
            settle_window = max(0.25, min(float(group["behavior"].get("rapid_settle_ms", 2600)) / 1000, 10.0))
            stable_for = max(0.05, min(float(group["behavior"].get("source_stable_ms", 220)) / 1000, 2.0))
            deadline = monotonic() + settle_window
            last_state = self._authoritative_source_state(group, source)
            if last_state not in VALID_STATES:
                return
            last_change = monotonic()

            while monotonic() < deadline:
                await asyncio.sleep(0.05)
                group = self._groups.get(group_id)
                runtime = self._runtime.get(group_id)
                if not group or not runtime or not group.get("enabled", True):
                    return
                if runtime.authority_generation != generation or runtime.authority_source != source:
                    return
                current = self._authoritative_source_state(group, source)
                if current not in VALID_STATES:
                    return
                if current != last_state:
                    last_state = current
                    last_change = monotonic()
                    runtime.authority_state = current
                    runtime.authority_until = monotonic() + settle_window
                    runtime.rapid_edges_seen += 1
                    continue
                if monotonic() - last_change >= stable_for:
                    break

            group = self._groups.get(group_id)
            runtime = self._runtime.get(group_id)
            if not group or not runtime:
                return
            if runtime.authority_generation != generation or runtime.authority_source != source:
                return
            final_state = self._authoritative_source_state(group, source)
            if final_state not in VALID_STATES:
                return
            runtime.authority_state = final_state
            runtime.input_sequence += 1
            await self.async_request_state(
                group_id,
                final_state,
                source=source,
                origin="source_settle",
                input_sequence=runtime.input_sequence,
                engine_delay_ms=0,
            )
            self._add_activity(
                group_id=group_id,
                source=source,
                event="source_settled",
                action=final_state,
                result="success",
                message="Final convergence matched the latest physical source state",
            )
            runtime.authority_until = monotonic() + stable_for
        except asyncio.CancelledError:
            return

    def start_learn(
        self,
        role: str,
        timeout: float = 12.0,
        allowed_domains: list[str] | None = None,
    ) -> dict[str, Any]:
        """Start a temporary entity-learning session."""
        if role not in {"output", "controller"}:
            raise ValueError("Invalid learn role")
        default_allowed = {"switch", "light", "input_boolean", "fan"} if role == "output" else {
            "switch", "light", "input_boolean", "binary_sensor", "button", "input_button", "event"
        }
        allowed = set(allowed_domains or default_allowed)
        allowed.discard("")
        if not allowed:
            raise ValueError("At least one learn domain is required")
        registry = er.async_get(self.hass)
        entity_ids = []
        for state in self.hass.states.async_all():
            entity_id = state.entity_id
            if entity_id.split(".", 1)[0] not in allowed:
                continue
            entry = registry.async_get(entity_id)
            if entry and entry.platform == DOMAIN:
                continue
            entity_ids.append(entity_id)
        session_id = uuid4().hex[:12]
        session: dict[str, Any] = {
            "id": session_id, "role": role, "status": "waiting", "created": monotonic(),
            "expires": monotonic() + max(5.0, min(float(timeout), 30.0)),
            "candidates": {}, "unsub": None, "finish_unsub": None, "timeout_unsub": None,
        }

        @callback
        def on_change(event: Event) -> None:
            old = event.data.get("old_state")
            new = event.data.get("new_state")
            if new is None or new.state in UNAVAILABLE_STATES:
                return
            if old and old.state == new.state and new.entity_id.split(".", 1)[0] != "event":
                return
            domain = new.entity_id.split(".", 1)[0]
            score = 100 if domain in {"switch", "light", "input_boolean"} else 92
            if domain in {"button", "input_button", "event"}:
                score = 96
            if domain == "fan":
                score = 82
            recommended_mode = MODE_EVENT if domain in {"button", "input_button", "event"} else MODE_MIRROR
            session["candidates"][new.entity_id] = {
                "entity_id": new.entity_id, "domain": domain, "score": score,
                "old_state": old.state if old else None, "new_state": new.state,
                "recommended_mode": recommended_mode,
            }
            if session["status"] == "waiting":
                session["status"] = "capturing"
                session["finish_unsub"] = async_call_later(
                    self.hass, 0.8, lambda _now: self._finish_learn(session_id, "detected")
                )

        if entity_ids:
            session["unsub"] = async_track_state_change_event(self.hass, entity_ids, on_change)
        session["timeout_unsub"] = async_call_later(
            self.hass, max(5.0, min(float(timeout), 30.0)),
            lambda _now: self._finish_learn(session_id, "timeout"),
        )
        self._learn_sessions[session_id] = session
        return {"session_id": session_id, "status": "waiting", "timeout": timeout}

    @callback
    def _finish_learn(self, session_id: str, status: str) -> None:
        session = self._learn_sessions.get(session_id)
        if not session or session.get("status") in {"detected", "timeout", "cancelled"}:
            return
        session["status"] = status if session.get("candidates") else "timeout"
        for key in ("unsub", "finish_unsub", "timeout_unsub"):
            unsub = session.get(key)
            if unsub:
                unsub()
                session[key] = None

    def learn_status(self, session_id: str) -> dict[str, Any]:
        """Return learn session status and ranked candidates."""
        session = self._learn_sessions.get(session_id)
        if not session:
            raise ValueError("Learn session not found")
        if monotonic() >= session["expires"] and session["status"] not in {"detected", "timeout", "cancelled"}:
            self._finish_learn(session_id, "timeout")
        candidates = sorted(
            session["candidates"].values(), key=lambda item: (-item["score"], item["entity_id"])
        )
        return {
            "session_id": session_id, "role": session["role"], "status": session["status"],
            "candidates": candidates[:8],
        }

    def cancel_learn(self, session_id: str) -> bool:
        session = self._learn_sessions.get(session_id)
        if not session:
            return False
        for key in ("unsub", "finish_unsub", "timeout_unsub"):
            unsub = session.get(key)
            if unsub:
                unsub()
        session["status"] = "cancelled"
        self._learn_sessions.pop(session_id, None)
        return True

    def _add_activity(self, **entry: Any) -> None:
        item = {
            "timestamp": _utcnow(),
            "group_id": None,
            "transaction_id": None,
            "source": None,
            "event": "event",
            "action": None,
            "result": "info",
            "latency_ms": None,
            "message": None,
            "origin": None,
            **entry,
        }
        self._activity.append(item)
        self.hass.bus.async_fire(EVENT_TYPE, item)

    def _notify(self, group_id: str) -> None:
        async_dispatcher_send(self.hass, SIGNAL_RUNTIME_UPDATED, group_id)
        self.hass.bus.async_fire(
            EVENT_TYPE,
            {
                "timestamp": _utcnow(),
                "event": "runtime_updated",
                "group_id": group_id,
                "status": self.status(group_id),
            },
        )

    def _notify_all(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_GROUPS_UPDATED)
        for group_id in self._groups:
            async_dispatcher_send(self.hass, SIGNAL_RUNTIME_UPDATED, group_id)
