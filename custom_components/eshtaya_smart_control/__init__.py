"""Eshtaya Smart Control unified Home Assistant platform."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_registry as er

from . import multiway as multiway_module
from .access_control import AccessControlManager
from .const import (
    DATA_ACCESS_CONTROL,
    DATA_ENTITY_MANAGER,
    DATA_ENTRY,
    DATA_MIGRATION,
    DATA_TUYA_MANAGER,
    DOMAIN,
)
from .entity_control.manager_unified import UnifiedEntityManager
from .entity_control.websocket_access import async_register_websocket_commands as async_register_entity_ws
from .legacy_cleanup import async_cleanup_legacy_hacs
from .legacy_compat import async_register_legacy_service_aliases
from .migration_center import MigrationCenterCoordinator
from .multiway import async_remove_entry as async_remove_multiway_entry
from .multiway import async_setup as async_setup_multiway
from .multiway import async_setup_entry as async_setup_multiway_entry
from .multiway import async_unload_entry as async_unload_multiway_entry
from .multiway.const import DATA_RUNTIME
from .multiway.startup_safe_manager import StartupSafeMultiWayManager
from .multiway.websocket_access import async_register_websocket_commands as async_register_multiway_ws
from .panel import async_register_panel, async_remove_panel
from .template_manager import async_setup_services as async_setup_template_services
from .template_manager.const import (
    DATA_TEMPLATE_MANAGER,
    DATA_TEMPLATE_MIGRATION,
    LEGACY_DOMAIN as TEMPLATE_LEGACY_DOMAIN,
)
from .template_manager.manager import TemplateManager
from .template_manager.migration_v231 import LegacyTemplateMigration
from .template_manager.store import TemplateManagerStore
from .template_manager.websocket import async_register_websocket_commands as async_register_template_ws
from .tuya.manager import TuyaManager
from .tuya.websocket_access import async_register_websocket_commands as async_register_tuya_ws
from .websocket_v22 import async_register_websocket_commands as async_register_core_ws

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def _activate_v21_multiway_runtime() -> None:
    """Activate startup-safe and permission-aware Multi-Way adapters."""
    multiway_module.MultiWayManager = StartupSafeMultiWayManager
    multiway_module.async_register_websocket_commands = async_register_multiway_ws


def _schedule_legacy_hacs_cleanup(
    hass: HomeAssistant,
    entry: ConfigEntry,
    migration: MigrationCenterCoordinator,
) -> None:
    """Run HACS cleanup now or once Home Assistant has fully started."""

    async def _cleanup() -> None:
        results = await async_cleanup_legacy_hacs(hass)
        try:
            await migration.async_mark_hacs_cleanup(results)
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Could not save legacy HACS cleanup status")
        if any(value.startswith("failed:") for value in results.values()):
            _LOGGER.warning("Legacy HACS cleanup was only partially successful: %s", results)

    if hass.is_running:
        hass.async_create_task(_cleanup(), "Eshtaya Smart Control legacy HACS cleanup")
        return

    @callback
    def _on_started(_event) -> None:
        hass.async_create_task(_cleanup(), "Eshtaya Smart Control legacy HACS cleanup")

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started))


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    _activate_v21_multiway_runtime()
    await async_setup_multiway(hass, config)
    async_register_entity_ws(hass)
    async_register_tuya_ws(hass)
    async_register_template_ws(hass)
    async_register_core_ws(hass)
    await async_setup_template_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the unified platform and safely migrate all legacy Eshtaya tools."""
    data = hass.data.setdefault(DOMAIN, {})
    data[DATA_ENTRY] = entry

    access_manager = AccessControlManager(hass)
    await access_manager.async_load()
    data[DATA_ACCESS_CONTROL] = access_manager

    migration = MigrationCenterCoordinator(hass)
    data[DATA_MIGRATION] = migration
    migration_state = await migration.async_prepare()
    migration_active = bool(
        migration_state.get("legacy_found") and not migration_state.get("completed")
    )
    if migration_active:
        await migration.async_quiesce_legacy()

    template_store = TemplateManagerStore(hass)
    await template_store.async_load()
    template_migration = LegacyTemplateMigration(hass, template_store)
    data[DATA_TEMPLATE_MIGRATION] = template_migration
    template_migration_state: dict = {}

    try:
        template_migration_state = await template_migration.async_prepare()
        template_migration_active = bool(
            template_migration_state.get("legacy_found")
            and not template_migration_state.get("completed")
        )
        template_restart_required = (
            template_migration_state.get("phase") == "restart_required"
        )

        template_manager = TemplateManager(hass, template_store)
        data[DATA_TEMPLATE_MANAGER] = template_manager

        entity_manager = UnifiedEntityManager(hass)
        await entity_manager.async_initialize()
        data[DATA_ENTITY_MANAGER] = entity_manager
        data[DATA_TUYA_MANAGER] = TuyaManager(hass, entry)

        _activate_v21_multiway_runtime()
        if not await async_setup_multiway_entry(hass, entry):
            raise RuntimeError("Multi-Way module could not be initialized")

        await template_manager.async_start()

        if template_migration_active and not template_restart_required:
            template_migration_state = await template_migration.async_finalize()
            if template_migration_state.get("completed"):
                await async_setup_template_services(
                    hass,
                    register_legacy=True,
                    replace_legacy=True,
                )
        elif template_restart_required:
            _LOGGER.warning(
                "Template Manager migration is staged and requires one Home Assistant "
                "restart to release legacy entity IDs. No duplicate entities were created."
            )
        elif not hass.config_entries.async_entries(TEMPLATE_LEGACY_DOMAIN):
            await async_setup_template_services(hass, register_legacy=True)

        await async_register_panel(hass)

        if migration_active:
            runtime = data.get(DATA_RUNTIME) or {}
            await migration.async_mark_runtime_started(runtime)
            validation = await migration.async_validate(runtime)
            if not validation.get("ok"):
                raise RuntimeError(
                    "Legacy migration validation failed: "
                    + "; ".join(validation.get("errors") or ["unknown validation error"])
                )
            await migration.async_finalize(runtime)

        if not hass.config_entries.async_entries("eshtaya_multiway"):
            async_register_legacy_service_aliases(hass)

        template_cleanup_ready = bool(
            template_migration_state.get("legacy_found")
            and template_migration_state.get("completed")
        )
        if migration_active or template_cleanup_ready:
            _schedule_legacy_hacs_cleanup(hass, entry, migration)

        async def _entity_registry_changed(event) -> None:
            try:
                await entity_manager.async_handle_registry_event(dict(event.data))
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Entity Control failed after entity registry update")

        entry.async_on_unload(
            hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, _entity_registry_changed)
        )
        entry.async_on_unload(entry.add_update_listener(_entry_updated))
        return True
    except Exception as err:
        if data.get(DATA_RUNTIME):
            try:
                await async_unload_multiway_entry(hass, entry)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Could not unload unified platforms before rollback")
        try:
            await template_migration.async_rollback(str(err))
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Template Manager migration rollback failed")
        if migration_active:
            try:
                await migration.async_rollback(str(err))
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Automatic legacy migration rollback failed")
        try:
            async_remove_panel(hass)
        except Exception:  # noqa: BLE001
            pass
        _LOGGER.exception("Eshtaya Smart Control setup failed")
        raise


async def _entry_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    manager = hass.data.get(DOMAIN, {}).get(DATA_TUYA_MANAGER)
    if manager:
        manager._reload_config()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    async_remove_panel(hass)
    runtime = hass.data.get(DOMAIN, {}).get(DATA_RUNTIME)
    ok = True
    if runtime:
        ok = await async_unload_multiway_entry(hass, entry)
    if ok:
        hass.data.pop(DOMAIN, None)
    return ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_remove_multiway_entry(hass, entry)
