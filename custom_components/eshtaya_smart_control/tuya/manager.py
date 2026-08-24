"""Tuya Entity Control business logic and safe config management."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from ..const import (
    CONF_TUYA_ACTIVATED_AT,
    CONF_TUYA_CLIENT_ID,
    CONF_TUYA_CLIENT_SECRET,
    CONF_TUYA_ENDPOINT,
    CONF_TUYA_REGION,
    CONF_TUYA_UID,
    CONF_TUYA_UPDATED_AT,
    TUYA_REGION_ENDPOINTS,
)
from .client import TuyaOpenApiClient


class TuyaManager:
    """Tuya cloud manager with bounded concurrency and stale-cache recovery."""

    CACHE_TTL = 20.0

    def __init__(self, hass, entry) -> None:
        self.hass = hass
        self.entry = entry
        self._devices: list[dict[str, Any]] = []
        self._devices_at = 0.0
        self._devices_lock = asyncio.Lock()
        self._sem = asyncio.Semaphore(5)
        self._last_success_at: str | None = None
        self._last_error: str | None = None
        self._last_error_at: str | None = None
        self._reload_config()

    @staticmethod
    def _utcnow() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _config(self) -> dict[str, Any]:
        return {**self.entry.data, **self.entry.options}

    def _reload_config(self) -> None:
        cfg = self._config()
        region = str(cfg.get(CONF_TUYA_REGION, "eu"))
        endpoint = str(cfg.get(CONF_TUYA_ENDPOINT, "")).strip().rstrip("/")
        if region != "custom":
            endpoint = TUYA_REGION_ENDPOINTS.get(region, endpoint)
        self.region = region
        self.endpoint = endpoint
        self.client_id = str(cfg.get(CONF_TUYA_CLIENT_ID, "")).strip()
        self.client_secret = str(cfg.get(CONF_TUYA_CLIENT_SECRET, "")).strip()
        self.uid = str(cfg.get(CONF_TUYA_UID, "")).strip()
        self.client = TuyaOpenApiClient(
            self.hass,
            endpoint=self.endpoint,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        self._devices_at = 0.0

    @property
    def configured(self) -> bool:
        return bool(self.client.configured and self.uid)

    def public_status(self) -> dict[str, Any]:
        masked = ""
        if self.client_id:
            masked = (
                self.client_id[:4] + "…" + self.client_id[-3:]
                if len(self.client_id) > 8
                else "configured"
            )
        cfg = self._config()
        cache_age = (
            max(0.0, time.monotonic() - self._devices_at)
            if self._devices_at
            else None
        )
        return {
            "configured": self.configured,
            "activated": self.configured,
            "region": self.region,
            "endpoint": self.endpoint,
            "client_id_masked": masked,
            "uid_configured": bool(self.uid),
            "cached_devices": len(self._devices),
            "cache_age_seconds": round(cache_age, 1) if cache_age is not None else None,
            "last_success_at": self._last_success_at,
            "last_error": self._last_error,
            "last_error_at": self._last_error_at,
            "activated_at": cfg.get(CONF_TUYA_ACTIVATED_AT),
            "updated_at": cfg.get(CONF_TUYA_UPDATED_AT),
        }

    async def async_test_config(
        self, config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        cfg = self._effective_candidate(config or {})
        client = TuyaOpenApiClient(
            self.hass,
            endpoint=cfg[CONF_TUYA_ENDPOINT],
            client_id=cfg[CONF_TUYA_CLIENT_ID],
            client_secret=cfg[CONF_TUYA_CLIENT_SECRET],
        )
        await client.async_test()
        path = f"/v1.0/users/{cfg[CONF_TUYA_UID]}/devices"
        result = await client.async_request("GET", path)
        devices = result.get("result") or []
        return {
            "ok": True,
            "devices": len(devices),
            "endpoint": cfg[CONF_TUYA_ENDPOINT],
        }

    def _effective_candidate(self, raw: dict[str, Any]) -> dict[str, str]:
        current = self._config()
        region = str(
            raw.get(CONF_TUYA_REGION, current.get(CONF_TUYA_REGION, "eu"))
        )
        endpoint = str(
            raw.get(
                CONF_TUYA_ENDPOINT, current.get(CONF_TUYA_ENDPOINT, "")
            )
        ).strip().rstrip("/")
        if region != "custom":
            endpoint = TUYA_REGION_ENDPOINTS.get(region, endpoint)
        secret = str(raw.get(CONF_TUYA_CLIENT_SECRET, "")).strip() or str(
            current.get(CONF_TUYA_CLIENT_SECRET, "")
        ).strip()
        client_id = str(raw.get(CONF_TUYA_CLIENT_ID, "")).strip() or str(
            current.get(CONF_TUYA_CLIENT_ID, "")
        ).strip()
        uid = str(raw.get(CONF_TUYA_UID, "")).strip() or str(
            current.get(CONF_TUYA_UID, "")
        ).strip()
        cfg = {
            CONF_TUYA_REGION: region,
            CONF_TUYA_ENDPOINT: endpoint,
            CONF_TUYA_CLIENT_ID: client_id,
            CONF_TUYA_CLIENT_SECRET: secret,
            CONF_TUYA_UID: uid,
        }
        if not all(
            (
                cfg[CONF_TUYA_ENDPOINT],
                cfg[CONF_TUYA_CLIENT_ID],
                cfg[CONF_TUYA_CLIENT_SECRET],
                cfg[CONF_TUYA_UID],
            )
        ):
            raise ValueError("Endpoint, Client ID, Client Secret and UID are required")
        return cfg

    async def async_save_config(
        self, raw: dict[str, Any], *, test_first: bool = True
    ) -> dict[str, Any]:
        """Validate and activate/update Tuya without replacing unrelated entry data."""
        cfg = self._effective_candidate(raw)
        test = await self.async_test_config(cfg) if test_first else {"ok": True}
        now = self._utcnow()
        current = dict(self.entry.data)
        first_activation = not self.configured
        current.update(cfg)
        if first_activation and not current.get(CONF_TUYA_ACTIVATED_AT):
            current[CONF_TUYA_ACTIVATED_AT] = now
        current[CONF_TUYA_UPDATED_AT] = now
        self.hass.config_entries.async_update_entry(self.entry, data=current)
        self._reload_config()
        self._last_error = None
        self._last_error_at = None
        return {
            **test,
            "first_activation": first_activation,
            "status": self.public_status(),
        }

    async def async_clear_config(self) -> dict[str, Any]:
        """Deactivate only the optional Tuya module and preserve unified entry."""
        data = dict(self.entry.data)
        for key in (
            CONF_TUYA_REGION,
            CONF_TUYA_ENDPOINT,
            CONF_TUYA_CLIENT_ID,
            CONF_TUYA_CLIENT_SECRET,
            CONF_TUYA_UID,
            CONF_TUYA_ACTIVATED_AT,
            CONF_TUYA_UPDATED_AT,
        ):
            data.pop(key, None)
        self.hass.config_entries.async_update_entry(self.entry, data=data)
        self._reload_config()
        self._devices = []
        self._devices_at = 0.0
        self._last_error = None
        self._last_error_at = None
        return self.public_status()

    async def async_list_devices(self, *, force: bool = False) -> list[dict[str, Any]]:
        """List devices without allowing concurrent refresh storms.

        A normal page load may use the last successful cache if Tuya Cloud has a
        temporary failure. An explicit force refresh still reports the cloud
        error so the operator knows the refresh did not succeed.
        """
        if not self.configured:
            raise ValueError("Tuya Cloud account is not configured")
        if (
            not force
            and self._devices
            and (time.monotonic() - self._devices_at) < self.CACHE_TTL
        ):
            return list(self._devices)

        async with self._devices_lock:
            if (
                not force
                and self._devices
                and (time.monotonic() - self._devices_at) < self.CACHE_TTL
            ):
                return list(self._devices)
            try:
                result = await self.client.async_request(
                    "GET", f"/v1.0/users/{self.uid}/devices"
                )
                raw = result.get("result") or []
                self._devices = [
                    {
                        "device_id": str(d.get("id") or ""),
                        "name": str(d.get("name") or ""),
                        "online": bool(d.get("online")),
                        "category": str(d.get("category") or ""),
                        "product_id": str(d.get("product_id") or ""),
                        "icon_url": str(d.get("icon") or ""),
                    }
                    for d in raw
                    if isinstance(d, dict)
                ]
                self._devices_at = time.monotonic()
                self._last_success_at = self._utcnow()
                self._last_error = None
                self._last_error_at = None
                return list(self._devices)
            except Exception as err:
                self._last_error = str(err)
                self._last_error_at = self._utcnow()
                if self._devices and not force:
                    return list(self._devices)
                raise

    async def async_device_details(self, device_id: str) -> dict[str, Any]:
        result = await self.client.async_request("GET", f"/v1.0/devices/{device_id}")
        return result.get("result") or {}

    async def async_shadow_props(self, device_id: str) -> list[dict[str, Any]]:
        result = await self.client.async_request(
            "GET", f"/v2.0/cloud/thing/{device_id}/shadow/properties"
        )
        payload = result.get("result") or {}
        return list(payload.get("properties") or [])

    async def async_update_device_name(self, device_id: str, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValueError("Device name cannot be empty")
        await self.client.async_request(
            "PUT", f"/v1.0/devices/{device_id}", {"name": name}
        )
        self._devices_at = 0.0

    async def async_update_prop_name(
        self, device_id: str, code: str, custom_name: str
    ) -> None:
        code, custom_name = code.strip(), custom_name.strip()
        if not code or not custom_name:
            raise ValueError("Property code and custom name are required")
        await self.client.async_request(
            "POST",
            f"/v2.0/cloud/thing/{device_id}/shadow/properties",
            {"properties": [{"code": code, "custom_name": custom_name}]},
        )

    async def async_bulk_details(self, device_ids: list[str]) -> list[dict[str, Any]]:
        async def one(device_id: str) -> dict[str, Any]:
            async with self._sem:
                try:
                    props = await self.async_shadow_props(device_id)
                    switches = [
                        p
                        for p in props
                        if isinstance(p, dict)
                        and (
                            str(p.get("code", "")).startswith("switch_")
                            or str(p.get("code", "")).startswith("socket_")
                            or str(p.get("code", "")) == "control"
                        )
                    ]
                    return {
                        "device_id": device_id,
                        "properties": switches,
                        "ok": True,
                    }
                except Exception as err:
                    return {
                        "device_id": device_id,
                        "properties": [],
                        "ok": False,
                        "error": str(err),
                    }

        return await asyncio.gather(*(one(device_id) for device_id in device_ids))

    async def async_bulk_save(self, changes: list[dict[str, Any]]) -> dict[str, int]:
        ok = failed = 0
        for change in changes:
            try:
                device_id = str(change.get("device_id") or "")
                if "name" in change and str(change.get("name") or "").strip():
                    await self.async_update_device_name(
                        device_id, str(change["name"])
                    )
                for prop in change.get("properties") or []:
                    if str(prop.get("custom_name") or "").strip():
                        await self.async_update_prop_name(
                            device_id,
                            str(prop.get("code") or ""),
                            str(prop.get("custom_name") or ""),
                        )
                ok += 1
            except Exception:
                failed += 1
        return {"ok": ok, "failed": failed}
