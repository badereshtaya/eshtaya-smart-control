"""Runtime option helpers for Eshtaya Smart Control."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_ENTRY, DEFAULT_OPTIONS, DOMAIN


def effective_options(entry: ConfigEntry | None) -> dict[str, Any]:
    """Return validated/defaulted integration options without mutating the entry."""
    result = deepcopy(DEFAULT_OPTIONS)
    if entry is not None:
        result.update(dict(entry.options))
    return result


def runtime_options(hass: HomeAssistant) -> dict[str, Any]:
    """Return effective options for the currently loaded Eshtaya config entry."""
    entry = hass.data.get(DOMAIN, {}).get(DATA_ENTRY)
    return effective_options(entry if isinstance(entry, ConfigEntry) else None)


def option(hass: HomeAssistant, key: str) -> Any:
    """Return one effective integration option."""
    return runtime_options(hass).get(key, DEFAULT_OPTIONS.get(key))
