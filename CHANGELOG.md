# Changelog

## 2.4.4 — Template Manager regression recovery & Documentation Center hardening

- Fixed the v2.4.3 Template Manager frontend regression where the full-editor extension called `insertAdjacentHTML()` on a `ShadowRoot`; browsers can throw before the initial `template/scan` WebSocket call, leaving the already-rendered counters at zero.
- Added a guarded ShadowRoot HTML-insertion compatibility layer and changed Template Manager loading so a rendering exception can never block backend scanning again.
- Added a no-op language-setter guard for Template Manager to avoid unnecessary full re-renders when the shell reassigns the same language during normal Home Assistant updates.
- Preserves the Template Manager view across shell reload/reconnect when the current user still has `template.view`, compensating for an older shell allowed-view omission.
- Added generated-package scan diagnostics for every known managed YAML path, including file existence, discovered record count and explicit parse/read errors instead of silently swallowing exceptions.
- Made generated-package synchronization non-destructive during scan errors: previously known external mappings remain available with a stale-scan marker until the YAML is readable again, rather than being purged because one scan returned zero records.
- Added `generated_scan` diagnostics and `defined_count` to the Template Manager snapshot. The Managed statistic now reflects every defined mapping, including mappings whose physical source is currently Missing.
- Rebuilt the in-app Documentation Center frontend around the authenticated `documentation/get` WebSocket endpoint for all 14 Arabic/English guides.
- Added documentation request timeout, stale-response protection, explicit loading/error/empty states and a Retry action so a backend or rendering failure can never present a blank documentation page.
- Added a resilient Markdown renderer for headings, lists, fenced code, inline code, emphasis and separators, with a raw-text fallback if rendering encounters unexpected Markdown.
- Added a cache-busted `smart-control-panel-v244.js` entrypoint so HACS updates cannot keep the broken v2.4.3 frontend bundle in the normal panel URL.
- Added CI regression gates that dynamically smoke-test ShadowRoot insertion, successful Documentation Center WebSocket rendering and visible documentation failure handling in addition to HACS, Hassfest, Python compilation, JavaScript syntax, documentation parity and package verification.
- Bumped Eshtaya Smart Control to `2.4.4`.

## 2.4.0 — Startup Barrier, false-missing suppression & opt-in legacy migration

- Fixed false `Multi-way output entity is missing` / `missing_controller` Repair issues that could appear after a Home Assistant restart when official Tuya or another entity provider had not finished restoring yet.
- Added `tuya` as a Home Assistant `after_dependencies` integration so Eshtaya Smart Control is scheduled after official Tuya when it is present.
- Replaced the old fixed Multi-Way startup-delay decision with a lifecycle-aware **Startup Barrier** that waits for Home Assistant startup completion before enabling physical reconciliation and missing-entity repairs.
- Added Entity Registry / Config Entry ownership checks so referenced outputs, controllers and fallbacks owned by integrations in setup/retry/unload states are treated as still loading instead of missing.
- Added a configurable post-provider settle window (default 15 seconds) and bounded maximum startup wait (default 240 seconds).
- Added a separate missing-entity Repair grace period (default 90 seconds) plus repeated confirmation requirement (default 3 checks) before a real missing-output/controller Repair can be created.
- Clears persisted transient missing-output/controller Repair issues at the beginning of protected startup and recreates them only after genuine post-start absence is confirmed.
- Keeps Multi-Way state events inert while `ready=false`, preventing startup entity-restoration edges from being interpreted as physical user commands.
- Reports startup protection as `starting/recovering` rather than degrading the platform Health Score while providers are still loading.
- Added startup-barrier state and effective runtime options to System Center / sanitized support reports.
- Added a full **Configure** options flow under Home Assistant Devices & Services with startup wait, referenced-integration wait, settle, maximum wait, Repair grace and confirmation controls.
- Changed retired Eshtaya integration migration to **opt-in by default**. A new installation/update no longer intentionally scans, copies, unloads, removes or cleans old Eshtaya integrations unless the migration master option is enabled.
- Added independent migration selectors for the former Entity Manager, Multi-Way/Smart Groups and Template Manager, plus separate HACS cleanup and legacy-service-alias controls.
- Preserves transaction safety by allowing a migration already in `prepared` / `restart_required` cutover before 2.4.0 to finish even if the new master migration switch is off.
- Added safe rescan behavior: a historical `no_legacy` result does not permanently block a migration that the operator explicitly enables later, while a genuinely completed migration is not repeated unnecessarily.
- Prevented unified service setup from touching a real old Template Manager service domain when legacy migration/compatibility is disabled.
- Kept **native Home Assistant Group discovery and transactional Take Over** independent from retired Eshtaya migration controls; disabling legacy migration does not disable HA Group discovery/import workflows.
- Updated Arabic/English Configure translations, Startup/Multi-Way/Migration/Getting Started/Template Manager documentation and README to match the 2.4.0 behavior.
- Added CI invariants that fail the build if official Tuya loses `after_dependencies`, legacy migration becomes enabled by default, or required Startup Barrier/Repair protection hooks disappear.
- Added JSON validation for manifest, strings and Arabic/English translations alongside HACS, Hassfest, Python compilation, JavaScript syntax, documentation parity and release archive packaging.
- Bumped Eshtaya Smart Control to `2.4.0` and the embedded Multi-Way engine marker to `3.4.0`.

## 2.3.1 — Template Manager hotfix, safer migration & documentation sync

- Fixed the frontend permission-map bug that could show Template Manager and then reject the click with `This role does not have access to that module.` even when `template.view` was present.
- Synchronized `template.view` and `template.manage` across the canonical frontend view map, permission labels, built-in roles, first-allowed-view selection, navigation filtering and click protection.
- Removed duplicate v2.3 navigation/dashboard/documentation patching so Template Manager now has one permission/navigation source of truth.
- Bumped the integration to 2.3.1 so the sidebar asset loads with `?v=2.3.1` and does not keep the cached 2.3.0 JavaScript after a normal HACS update and Home Assistant restart.
- Expanded legacy Template Manager discovery beyond config entries and the live sensor to include legacy services, the old custom component, known storage/package paths and generated YAML/JSON mappings.
- Added recovery from `/config/packages/eshtaya_generated_templates.yaml`, `/config/packages/eshtaya_generated_lights.yaml`, `/config/eshtaya_template_manager/generated_templates.yaml`, `/config/eshtaya_template_manager/templates.json` and `/config/eshtaya_template_manager/mappings.json`.
- Live legacy runtime mappings override file-discovered mappings when both exist, because the live record represents the mapping the old manager is actually using.
- Re-checks actual legacy evidence during startup, so updating over 2.3.0 can migrate an old method that the earlier migrator incorrectly recorded as `not_found`.
- Added a guarded `restart_required` migration checkpoint for YAML/non-config-entry legacy installations whose old Light/Fan entities remain resident in Home Assistant memory after their generated files are backed up and removed.
- Defers new Light/Fan entities during `restart_required`, preventing accidental `light.*_2` or `fan.*_2` entity IDs and preventing two engines from controlling the same physical source.
- Also treats an externally owned `sensor.eshtaya_template_manager` as an occupied legacy ID and defers the unified compatibility sensor, preventing `sensor.eshtaya_template_manager_2`.
- Added migration locking at both UI and Python backend layers: Create/Edit/Delete/Relink cannot modify template mappings until the legacy cutover is verified.
- Added rollback backup and file restoration support for generated legacy YAML/JSON/custom-component data.
- Uses `template.reload` when available after generated legacy definitions are removed; if runtime ownership still cannot be released safely, migration stages the exact-ID takeover for the next Home Assistant restart instead of creating duplicates.
- Kept normal HACS Update as the supported upgrade path; deleting/reinstalling the unified integration is not required for Template Manager migration.
- Reworked in-app Documentation Center to read packaged Markdown files directly rather than a separate Python documentation copy.
- Completed the GitHub documentation set to 14 Arabic and 14 English guides, including Template Manager, Access Control, commissioning, migration, security/backup and troubleshooting.
- Packaged the exact same Markdown Git blobs under the integration so GitHub documentation and the offline in-app Documentation Center are byte-identical.
- Added CI checks that fail if repository documentation and packaged in-app documentation differ or if either language is missing any of the expected 14 guides.
- Rewrote README for the current 2.3.1 architecture, safe update workflow, Template Manager migration behavior, access model and complete bilingual documentation index.

## 2.3.0 — Integrated Template Manager & zero-duplicate migration

- Integrated the former standalone **Eshtaya Template Manager** as a first-class module inside the unified Eshtaya Smart Control Control Hub.
- Added native permanent Light/Fan wrappers backed by physical Tuya switch entities, including live source-state tracking and source re-linking.
- Added Available, Managed and Missing workflows with search, create, edit, delete and ranked replacement-source suggestions.
- Added `template.view` and `template.manage` backend-enforced Eshtaya permissions.
- Added native `eshtaya_smart_control.template_*` services and preserved `eshtaya_template_manager.*` compatibility aliases after migration.
- Preserved the compatibility entity `sensor.eshtaya_template_manager`, now owned by Eshtaya Smart Control after successful migration.
- Added transactional automatic migration from the standalone `eshtaya_template_manager` method during update/reinstall.
- Migration waits for the old runtime when necessary, reads its live managed mappings, compares the readable count with the legacy reported count, and refuses destructive cleanup when the old state cannot be proven complete.
- Added rollback backups under `/config/eshtaya_smart_control_backups/template_manager_<timestamp>/`, including migration metadata, Entity Registry metadata and known legacy component/storage/package files.
- The old runtime is disabled and unloaded **before** the unified runtime claims the permanent Entity IDs, preventing duplicate control engines.
- Migration verifies every permanent Entity ID and its unified integration ownership before deleting the old config entry or files.
- Restores preserved user-facing Entity Registry metadata such as name, icon, area and labels where available.
- Cleans known standalone Template Manager files and its HACS repository only after successful verification; the rollback backup is retained.
- Added duplicate-safe rollback that removes unified registry ownership before attempting to restore the old integration.
- Added registry-aware startup grace so slow Tuya loading does not create false Missing results, while genuinely deleted sources do not unnecessarily delay startup.
- Added a complete Arabic/English Template Manager operating and migration guide inside Documentation Center.
- Bumped the integration and HACS release version to 2.3.0.

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
- Bumped the integration to 2.2.0.

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
