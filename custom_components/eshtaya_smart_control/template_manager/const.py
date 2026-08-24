"""Constants for the integrated Eshtaya Template Manager."""
from __future__ import annotations

from typing import Final

DATA_TEMPLATE_MANAGER: Final = "template_manager"
DATA_TEMPLATE_MIGRATION: Final = "template_manager_migration"
STORE_VERSION: Final = 1
STORE_KEY: Final = "eshtaya_smart_control.template_manager"
LEGACY_DOMAIN: Final = "eshtaya_template_manager"
LEGACY_SENSOR: Final = "sensor.eshtaya_template_manager"
SIGNAL_TEMPLATE_CHANGED: Final = "eshtaya_smart_control_template_changed"
SUPPORTED_TYPES: Final = {"light", "fan"}
STARTUP_GRACE_SECONDS: Final = 180
STARTUP_RETRY_SECONDS: Final = 5
