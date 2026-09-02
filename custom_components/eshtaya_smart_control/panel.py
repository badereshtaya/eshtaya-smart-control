"""Unified sidebar panel for Eshtaya Smart Control."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PANEL_ELEMENT, PANEL_ICON, PANEL_TITLE, PANEL_URL, STATIC_URL, VERSION


async def async_register_panel(hass: HomeAssistant) -> None:
    frontend_dir = Path(__file__).parent / "frontend"
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(frontend_dir), cache_headers=True)]
        )
    except RuntimeError:
        pass

    if frontend.async_panel_exists(hass, PANEL_URL):
        frontend.async_remove_panel(hass, PANEL_URL)
    await panel_custom.async_register_panel(
        hass=hass,
        frontend_url_path=PANEL_URL,
        webcomponent_name=PANEL_ELEMENT,
        module_url=f"{STATIC_URL}/smart-control-panel-v241.js?v={VERSION}",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        require_admin=False,
        config_panel_domain=DOMAIN,
        config={},
    )


def async_remove_panel(hass: HomeAssistant) -> None:
    if frontend.async_panel_exists(hass, PANEL_URL):
        frontend.async_remove_panel(hass, PANEL_URL)
