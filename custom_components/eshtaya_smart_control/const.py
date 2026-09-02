"""Constants for Eshtaya Smart Control."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "eshtaya_smart_control"
NAME: Final = "Eshtaya Smart Control"
VERSION: Final = "2.4.1"
MANUFACTURER: Final = "Eshtaya Smart"

DATA_ENTRY: Final = "entry"
DATA_ENTITY_MANAGER: Final = "entity_manager"
DATA_TUYA_MANAGER: Final = "tuya_manager"
DATA_MIGRATION: Final = "migration"
DATA_SYSTEM: Final = "system"
DATA_ACCESS_CONTROL: Final = "access_control"
DATA_STARTUP_STATUS: Final = "startup_status"

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

# Runtime/startup safety options.
CONF_STARTUP_WAIT_HA: Final = "startup_wait_home_assistant"
CONF_STARTUP_WAIT_REFERENCES: Final = "startup_wait_referenced_integrations"
CONF_STARTUP_SETTLE_SECONDS: Final = "startup_settle_seconds"
CONF_STARTUP_MAX_WAIT_SECONDS: Final = "startup_max_wait_seconds"
CONF_REPAIR_GRACE_SECONDS: Final = "repair_grace_seconds"
CONF_REPAIR_CONFIRMATIONS: Final = "repair_missing_confirmations"

# Legacy migration controls. Native Home Assistant Group discovery/takeover is
# intentionally not a migration option and remains available independently.
CONF_LEGACY_MIGRATION_ENABLED: Final = "legacy_migration_enabled"
CONF_MIGRATE_ENTITY_MANAGER: Final = "migrate_legacy_entity_manager"
CONF_MIGRATE_MULTIWAY: Final = "migrate_legacy_multiway"
CONF_MIGRATE_TEMPLATE_MANAGER: Final = "migrate_legacy_template_manager"
CONF_LEGACY_HACS_CLEANUP: Final = "legacy_hacs_cleanup"
CONF_LEGACY_SERVICE_ALIASES: Final = "legacy_service_aliases"

DEFAULT_OPTIONS: Final = {
    # Startup safety: do not diagnose missing entities until Home Assistant and
    # the integrations that own referenced entities have settled.
    CONF_STARTUP_WAIT_HA: True,
    CONF_STARTUP_WAIT_REFERENCES: True,
    CONF_STARTUP_SETTLE_SECONDS: 15,
    CONF_STARTUP_MAX_WAIT_SECONDS: 240,
    CONF_REPAIR_GRACE_SECONDS: 90,
    CONF_REPAIR_CONFIRMATIONS: 3,
    # Legacy migrations are opt-in. Existing completed unified data remains
    # untouched; current Home Assistant discovery/import features stay available.
    CONF_LEGACY_MIGRATION_ENABLED: False,
    CONF_MIGRATE_ENTITY_MANAGER: True,
    CONF_MIGRATE_MULTIWAY: True,
    CONF_MIGRATE_TEMPLATE_MANAGER: True,
    CONF_LEGACY_HACS_CLEANUP: False,
    CONF_LEGACY_SERVICE_ALIASES: False,
}

TUYA_REGION_ENDPOINTS: Final = {
    "eu": "https://openapi.tuyaeu.com",
    "eu_west": "https://openapi-weaz.tuyaeu.com",
    "us": "https://openapi.tuyaus.com",
    "us_east": "https://openapi-ueaz.tuyaus.com",
    "cn": "https://openapi.tuyacn.com",
    "in": "https://openapi.tuyain.com",
    "sg": "https://openapi-sg.iotbing.com",
}
