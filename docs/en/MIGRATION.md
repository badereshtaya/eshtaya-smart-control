# Automatic migration from legacy Eshtaya integrations

Starting with **Eshtaya Smart Control 1.1.0**, the unified platform checks for previous standalone integrations during first setup. Starting with **1.2.0**, the complete cutover is visible inside the new **Migration Center**.

Supported legacy integrations:

- `Eshtaya Entity Manager` — domain: `eshtaya_entity_manager`
- `Eshtaya Multi-Way Control` — domain: `eshtaya_multiway`

## Automatic sequence

1. Detect legacy config entries and storage.
2. Create an independent migration backup before deleting anything.
3. Copy Entity Control, Multi-Way and Smart Group data only when the new destination is empty.
4. Temporarily disable legacy config entries so two control engines cannot run over the same devices.
5. Start the unified Entity Control, Multi-Way and Smart Group modules.
6. Validate migrated rule/group counts against the legacy data.
7. If validation fails, re-enable the legacy config entries automatically and keep the backup.
8. If validation succeeds, remove the legacy config entries through Home Assistant.
9. Reconcile Smart Group hidden-member ownership after the old Multi-Way entry is removed.
10. Replace old `eshtaya_multiway.*` service handlers with compatibility aliases that forward to the new engine, preserving existing automations and scripts.
11. Attempt to uninstall/unregister old repositories through HACS itself. The integration never deletes `custom_components` folders directly.

## Migration Center

**System Center → Migration Center** presents the transition as a visual workflow:

`Detect → Backup → Copy → Stop Legacy → Start New Runtime → Validate → Remove Legacy → Reconcile → HACS Cleanup`

Each stage exposes a safe status, timestamps when available, a short explanation and sanitized operational details.

Supported states are Pending, Running, Completed, Failed, Rolled Back and Skipped.

## Before / after validation

Migration Center compares:

- Entity / Alexa rule count;
- Multi-Way group count;
- Smart Group count.

The migration is not finalized until the transferred configuration passes validation.

## Migration backup

The independent backup is stored under:

`eshtaya_smart_control.migration_backup`

It contains the legacy integration data and config-entry metadata captured before cutover. Raw backup contents are never exposed through the UI or migration report.

## Failure behavior

If copying, startup or validation fails before final cleanup:

- legacy configuration is not deleted;
- entries disabled by the migration are re-enabled;
- the failure is recorded in Migration Center;
- affected steps are marked Failed or Rolled Back;
- the independent backup remains available for recovery and diagnosis.

## Migration Report

Migration Center can download a JSON support report containing:

- Eshtaya Smart Control version;
- migration phase and timeline;
- before/after counts;
- validation result;
- rollback state;
- HACS cleanup result;
- recorded errors.

For security, the report intentionally excludes:

- Tuya Client Secret;
- Tuya credentials;
- raw legacy storage payloads;
- raw migration-backup contents.

## Compatibility with v1.1 migration records

If migration already completed on **v1.1.0** before upgrading to v1.2.0, Migration Center hydrates the previous record into a completed timeline rather than incorrectly showing pending steps.

## HACS cleanup

Config-entry removal is handled by Home Assistant after validation succeeds. Package removal is requested only through the HACS repository API when available. This avoids leaving HACS metadata out of sync with manually deleted folders.
