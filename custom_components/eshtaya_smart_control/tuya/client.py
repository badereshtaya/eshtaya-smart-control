"""Minimal Tuya OpenAPI client used by Eshtaya Smart Control."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from typing import Any

from homeassistant.helpers.aiohttp_client import async_get_clientsession


class TuyaApiError(RuntimeError):
    pass


class TuyaOpenApiClient:
    def __init__(self, hass, *, endpoint: str, client_id: str, client_secret: str) -> None:
        self.hass = hass
        self.endpoint = endpoint.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = ""
        self._expire_at = 0.0
        self._token_lock = asyncio.Lock()

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.client_id and self.client_secret)

    async def async_test(self) -> dict[str, Any]:
        token = await self._get_token(force=True)
        return {"ok": bool(token), "endpoint": self.endpoint}

    async def async_request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.configured:
            raise TuyaApiError("Tuya Cloud account is not configured")
        token = await self._get_token()
        result = await self._raw_request(method, path, body, token)
        if int(result.get("code", 0) or 0) == 1010:
            token = await self._get_token(force=True)
            result = await self._raw_request(method, path, body, token)
        if result.get("success") is False:
            raise TuyaApiError(str(result.get("msg") or result.get("error") or result))
        return result

    async def _get_token(self, force: bool = False) -> str:
        if not force and self._access_token and self._expire_at > time.time() + 60:
            return self._access_token
        async with self._token_lock:
            if not force and self._access_token and self._expire_at > time.time() + 60:
                return self._access_token
            path = "/v1.0/token?grant_type=1"
            result = await self._raw_request("GET", path, None, "")
            if not result.get("success"):
                raise TuyaApiError(f"Token failed: {result.get('msg') or result}")
            payload = result.get("result") or {}
            token = str(payload.get("access_token") or "")
            expire = int(payload.get("expire_time") or 0)
            if not token or expire <= 0:
                raise TuyaApiError("Tuya returned an invalid access token")
            self._access_token = token
            self._expire_at = time.time() + expire
            return token

    async def _raw_request(self, method: str, path: str, body: dict[str, Any] | None, access_token: str) -> dict[str, Any]:
        body_text = "" if body is None else json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        timestamp = str(round(time.time() * 1000))
        body_hash = hashlib.sha256(body_text.encode()).hexdigest()
        string_to_sign = f"{method.upper()}\n{body_hash}\n\n{path}"
        sign_source = f"{self.client_id}{access_token}{timestamp}{string_to_sign}"
        signature = hmac.new(
            self.client_secret.encode(), sign_source.encode(), hashlib.sha256
        ).hexdigest().upper()
        headers = {
            "client_id": self.client_id,
            "sign_method": "HMAC-SHA256",
            "t": timestamp,
            "sign": signature,
            "Content-Type": "application/json",
        }
        if access_token:
            headers["access_token"] = access_token
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(30):
                async with session.request(
                    method.upper(), self.endpoint + path, headers=headers,
                    data=body_text if body_text else None,
                ) as response:
                    text = await response.text()
        except TimeoutError as err:
            raise TuyaApiError("Tuya request timed out") from err
        except Exception as err:
            raise TuyaApiError(f"Tuya connection failed: {err}") from err
        try:
            data = json.loads(text)
        except json.JSONDecodeError as err:
            raise TuyaApiError(f"Tuya returned invalid JSON (HTTP {response.status})") from err
        return data
