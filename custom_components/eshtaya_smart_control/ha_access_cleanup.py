"""Safe cleanup for Eshtaya-managed Home Assistant auth groups."""
from __future__ import annotations

import logging

from homeassistant.auth.const import GROUP_ID_USER

from .access_control import AccessControlManager
from .ha_access import HomeAssistantAccessManager, MANAGED_GROUP_PREFIX

_LOGGER = logging.getLogger(__name__)


async def async_restore_managed_access_on_remove(hass) -> None:
    """Restore original HA groups before the integration is permanently removed.

    This is intentionally not used on normal unload/restart. Native access must
    survive restarts, but it should not strand users in an Eshtaya-only custom
    auth group after the config entry itself is deleted.
    """
    metadata = AccessControlManager(hass)
    await metadata.async_load()
    manager = HomeAssistantAccessManager(hass, metadata)
    store = manager._auth_store()
    if store is None:
        _LOGGER.warning(
            "Could not restore managed Home Assistant access during removal: AuthStore compatibility check failed"
        )
        return

    users = await hass.auth.async_get_users()
    for user in users:
        if getattr(user, "is_owner", False) or getattr(user, "system_generated", False):
            continue
        record = metadata.ha_access_record(user.id)
        if not record.get("managed"):
            continue
        original = record.get("original_group_ids")
        valid = [
            group_id
            for group_id in (original or [])
            if group_id in store._groups
            and not str(group_id).startswith(MANAGED_GROUP_PREFIX)
        ]
        if not valid:
            valid = [GROUP_ID_USER]
        try:
            await hass.auth.async_update_user(user, group_ids=valid)
            user.invalidate_cache()
        except Exception:  # noqa: BLE001 - removal cleanup must continue for others
            _LOGGER.exception(
                "Could not restore original Home Assistant groups for user %s during Eshtaya removal",
                user.id,
            )

    # Remove only Eshtaya-owned groups that are no longer referenced.
    referenced = {
        group.id
        for user in await hass.auth.async_get_users()
        for group in getattr(user, "groups", [])
    }
    removed = False
    for group_id in list(store._groups):
        if str(group_id).startswith(MANAGED_GROUP_PREFIX) and group_id not in referenced:
            store._groups.pop(group_id, None)
            removed = True
    if removed:
        store._async_schedule_save()
