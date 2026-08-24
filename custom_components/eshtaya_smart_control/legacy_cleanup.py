"""Best-effort cleanup of legacy HACS repositories after a verified migration."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

LEGACY_REPOSITORIES = (
    "badereshtaya/hacs-eshtaya-entity-manager",
    "badereshtaya/hacs-eshtaya-multiway-control",
    "badereshtaya/hacs-eshtaya-template-manager",
)


async def async_cleanup_legacy_hacs(hass: HomeAssistant) -> dict[str, str]:
    """Ask HACS to uninstall/unregister old repositories after verified migration."""
    results: dict[str, str] = {}
    hacs = hass.data.get("hacs")
    if hacs is None:
        return {name: "hacs_not_loaded" for name in LEGACY_REPOSITORIES}

    repositories = getattr(hacs, "repositories", None)
    getter = getattr(repositories, "get_by_full_name", None)
    if not callable(getter):
        return {name: "hacs_api_unavailable" for name in LEGACY_REPOSITORIES}

    for full_name in LEGACY_REPOSITORIES:
        repository = getter(full_name)
        if repository is None:
            results[full_name] = "not_registered"
            continue
        try:
            data = getattr(repository, "data", None)
            if getattr(data, "installed", False):
                uninstall = getattr(repository, "uninstall", None)
                if callable(uninstall):
                    await uninstall()

            repo_id = str(getattr(data, "id", ""))
            is_default = getattr(repositories, "is_default", None)
            remove = getattr(repository, "remove", None)
            if callable(remove) and (not callable(is_default) or not is_default(repo_id)):
                remove()

            hacs_data = getattr(hacs, "data", None)
            async_write = getattr(hacs_data, "async_write", None)
            if callable(async_write):
                await async_write(force=True)
            results[full_name] = "removed"
        except Exception as err:  # noqa: BLE001 - cleanup must never break HA startup
            _LOGGER.exception("Could not clean legacy HACS repository %s", full_name)
            results[full_name] = f"failed: {err}"

    return results
