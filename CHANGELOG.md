# Changelog

## 2.2.0 — Runtime resilience, Home Assistant system access & full operating manual

- Fixed intermittent first-load failures that could leave Entity/Alexa, Tuya or Multi-Way/Smart Groups mounted without data after a transient WebSocket disconnect or startup race.
- Added bounded request timeouts, exponential retry/backoff, stale-request protection, browser online/focus recovery and independent module recovery instead of single-shot loading.
- Reworked Multi-Way frontend bootstrap so a temporary Catalog or Native Group request failure does not cancel successfully loaded runtime/group data.
- Added visible recovery diagnostics for Tuya and Multi-Way while automatic retry is active.
- Added a new versioned v2.2 frontend entrypoint to prevent older cached frontend modules from surviving an upgrade.
- Added **real Home Assistant system-wide user access management** using Home Assistant's native auth manager and built-in Administrator, User and Read Only groups.
- Added real account Active/Inactive and Local Only controls, while protecting the Home Assistant Owner, the current administrator from self-lockout, and system-generated users.
- Kept Eshtaya granular roles and Allow/Deny/expiration rules as a separate backend-enforced layer instead of pretending they are unsupported Home Assistant Core RBAC rules.
- Explicitly documents current Home Assistant Core limitations: HACS integrations cannot safely create supported custom Core RBAC roles, explicit Core deny policies or per-service ACLs.
- Replaced the short in-app help with a detailed Arabic-first operating manual covering installation, Dashboard, Entity/Alexa, Tuya, Multi-Way, Smart Groups, Commissioning, System Center, Access Control, Migration, architecture, security/backups and troubleshooting.
- Expanded troubleshooting documentation with the intermittent loading root cause, automatic recovery behavior, Tuya timeout diagnosis, Multi-Way startup recovery, permissions troubleshooting and cache recovery.
- Bumped the integration and HACS release version to 2.2.0.

## 2.1.0 — Access Control, startup safety & in-app documentation

- Added a backend-enforced **Access Control Center** built on existing Home Assistant users.
- Added built-in roles: No Access, Viewer, Operator, Technician and Platform Manager, plus custom roles.
- Added granular permissions for Dashboard, Entity Control, Tuya view/control/configuration, Multi-Way view/control/manage, Documentation, System actions/reports and Access administration.
- Added per-user Allow/Deny overrides, optional temporary expiration and a persistent audit log.
- Home Assistant administrators always retain full Eshtaya Smart Control access and cannot be restricted by local role rules.
- Replaced admin-only module WebSocket registration with permission-aware backend enforcement for Entity Control, Tuya and Multi-Way.
- Added permission-aware dashboard/module filtering so restricted users do not receive hidden module metrics in the overview payload.
- Added a permission-aware Control Hub frontend and Access Control UI for assigning users, roles, overrides and expiry.
- Fixed Documentation Center 404 behavior by serving packaged bilingual documentation through authenticated WebSocket APIs instead of relying on a static `/docs` path.
- Added the Access Control guide to the packaged Arabic and English documentation set.
- Added a startup-safe Multi-Way manager that checks both the Home Assistant state machine and Entity Registry before declaring entities missing.
- Suppressed false `missing_output` / `missing_controller` Repair issues during Multi-Way startup protection and re-evaluated repairs after startup reconciliation.
- Preserved the mature Multi-Way engine and storage format while activating the v2.1 startup-safety adapter.
- Added a versioned v2.1 frontend entrypoint so browser cache does not keep the v2.0 Control Hub after upgrade.

## 2.0.0 — Intelligent Control Platform redesign

- Rebuilt the first-install experience so the integration installs with zero optional cloud credentials.
- Moved all Tuya onboarding into the Tuya dashboard with test-before-activate, edit and deactivate workflows.
- Added a credential-safe Tuya activation state and timestamps without exposing the Client Secret to the frontend.
- Rebuilt the unified Dashboard with the new Eshtaya Smart Control visual identity, health score, metrics, module cards and responsive layouts.
- Adopted the new user-provided Eshtaya Smart Control logo across dashboard and integration brand assets.
- Added structured local smart recommendations for migration, Alexa file health, unavailable entities, Multi-Way health, Smart Group health and optional Tuya activation.
- Added safe System Center quick actions for Alexa repair, group synchronization, Tuya refresh and full managed refresh.
- Added a sanitized downloadable System Report that excludes Tuya secrets, access tokens and raw storage/backup data.
- Expanded System Center into the platform-level diagnostics and operational administration console.
- Preserved and integrated the v1.2 Migration Center with the redesigned v2 shell and reports.
- Added a comprehensive searchable in-app Documentation Center in Arabic and English.
- Expanded repository documentation with dedicated Getting Started, Dashboard, Entity Control, Tuya, Multi-Way, Smart Groups, Commissioning, System Center, Migration, Architecture, Security/Backup and Troubleshooting guides in both languages.
- Expanded Arabic localization throughout the unified shell and embedded Entity, Tuya and Multi-Way/Smart Group interfaces.
- Switched the panel loader to the new versioned `smart-control-panel.js` v2 frontend.
- Preserved config-entry compatibility with existing 1.x installations while changing the product release version to 2.0.0.

## 1.2.0 — Migration Center & operational visibility

- Added a full **Migration Center** inside System Center with a visual nine-step migration timeline.
- Added Before/After counters for Entity/Alexa rules, Multi-Way groups and Smart Groups.
- Added persistent migration-step state, timestamps, messages and sanitized details for support diagnostics.
- Added rollback readiness/status and migration-backup visibility without exposing raw backup contents.
- Added HACS cleanup status reporting for both legacy repositories.
- Added a credential-free `migration_report` WebSocket endpoint and one-click JSON report download from the UI.
- Migration reports intentionally exclude Tuya credentials, Client Secret values and raw legacy storage payloads.
- Added compatibility hydration so systems that already completed the v1.1 migration receive a correct completed v1.2 timeline instead of pending steps.
- Rebuilt the unified Control Hub with a more responsive, high-density professional UI and migration banner.
- Updated bilingual in-app migration documentation.

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
