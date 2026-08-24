"""Constants for Eshtaya Smart Control."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "eshtaya_smart_control"
NAME: Final = "Eshtaya Smart Control"
VERSION: Final = "2.2.0"
MANUFACTURER: Final = "Eshtaya Smart"

DATA_ENTRY: Final = "entry"
DATA_ENTITY_MANAGER: Final = "entity_manager"
DATA_TUYA_MANAGER: Final = "tuya_manager"
DATA_MIGRATION: Final = "migration"
DATA_SYSTEM: Final = "system"
DATA_ACCESS_CONTROL: Final = "access_control"

PANEL_URL: Final = "eshtaya-smart-control"
PANEL_ELEMENT: Final = "eshtaya-smart-control-panel"
PANEL_TITLE: Final = "Eshtaya Smart Control"
PANEL_ICON: Final = "mdi:home-automation"
STATIC_URL: Final = "/eshtaya_smart_control_static"

CONF_TUYA_REGION: Final = "tuya_region"
CONF_TUYA_ENDPOINT: Final = "tuya_endpoint"
CONF_TUYA_CLIENT_ID: Final = "tuya_client_id"
CONF_TUYA_CLIENT_SECRET: Final = "tuya_client_secret"
CONF_TUYA_UID: Final = "tuya_uid"
CONF_TUYA_ACTIVATED_AT: Final = "tuya_activated_at"
CONF_TUYA_UPDATED_AT: Final = "tuya_updated_at"

TUYA_REGION_ENDPOINTS: Final = {
    "eu": "https://openapi.tuyaeu.com",
    "eu_west": "https://openapi-weaz.tuyaeu.com",
    "us": "https://openapi.tuyaus.com",
    "us_east": "https://openapi-ueaz.tuyaus.com",
    "cn": "https://openapi.tuyacn.com",
    "in": "https://openapi.tuyain.com",
    "sg": "https://openapi-sg.iotbing.com",
}
