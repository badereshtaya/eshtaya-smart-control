"""v2.3.1 hardening for legacy Template Manager migration."""
from __future__ import annotations

from typing import Any

from .const import LEGACY_SENSOR
from .migration import LegacyTemplateMigration as _BaseLegacyTemplateMigration


class LegacyTemplateMigration(_BaseLegacyTemplateMigration):
    """Extend the base migration with compatibility-sensor occupancy checks.

    Some legacy installations are YAML/custom-component based and cannot be fully
    unloaded without a Home Assistant restart. Their generated Light/Fan entities
    may release after ``template.reload`` while ``sensor.eshtaya_template_manager``
    remains alive. Treat that sensor as occupied too, otherwise the unified sensor
    could be created as ``sensor.eshtaya_template_manager_2`` and verification would
    fail after the destructive phase already started.
    """

    def _occupied_legacy_entities(self, records: list[dict[str, Any]]) -> list[str]:
        occupied = super()._occupied_legacy_entities(records)
        if self._legacy_sensor_is_external() and LEGACY_SENSOR not in occupied:
            occupied.append(LEGACY_SENSOR)
        return occupied
