# Changelog

## 1.1.0 — Automatic legacy migration

- Added automatic detection of `eshtaya_entity_manager` and `eshtaya_multiway` during first setup.
- Added a rollback migration backup before any legacy config entry is removed.
- Added safe copy of Entity Control, Multi-Way and Smart Group storage into the unified integration.
- Legacy config entries are disabled before the new Multi-Way runtime starts, preventing duplicate control engines.
- Added validation of migrated rule/group counts before deleting the legacy config entries.
- Added automatic rollback that re-enables legacy config entries when migration validation fails.
- Added post-migration Smart Group hidden-member reconciliation.
- Added compatibility aliases for legacy `eshtaya_multiway.*` service calls so existing automations/scripts continue working.
- Added best-effort HACS cleanup through HACS' own repository API; legacy folders are never deleted manually.
- Added migration status to the unified overview/System Center backend.

## 1.0.0 — Unified platform

- Introduced the unified **Eshtaya Smart Control** integration and Control Hub.
- Integrated HomeAssistant Entity Control with entity renaming, Alexa rules, dual hidden YAML outputs, import/export, batch actions and maintenance tools.
- Added native **Tuya Entity Control** with per-installation account configuration, current Tuya data-center selection, signed OpenAPI backend, device search/filtering, details, main/sub-name editing and bulk operations.
- Integrated the complete **Eshtaya Multi-Way Control 3.3.1** runtime, Smart Groups, Action Groups, commissioning, diagnostics, Take Over and backup/restore tools.
- Added Arabic / English / Auto UI language modes.
- Added bilingual in-app and repository documentation.
- Added System Center with module health, Alexa-file sync state and legacy-integration detection.
- Added HACS, hassfest and syntax validation workflows.
