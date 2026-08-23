# Automatic migration from legacy Eshtaya integrations

Starting with **Eshtaya Smart Control 1.1.0**, the unified platform checks for the previous standalone integrations during its first setup.

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
11. Attempt to uninstall/unregister the old repositories through HACS itself. The integration never deletes `custom_components` folders directly.

## Migration backup

The migration backup is stored under:

`eshtaya_smart_control.migration_backup`

It contains the legacy integration data and config-entry metadata captured before cutover.

## Failure behavior

If copying, startup, or validation fails before final cleanup:

- legacy configuration is not deleted;
- entries disabled by the migration are re-enabled;
- the migration error is recorded;
- the independent backup remains available for recovery and diagnosis.

## HACS cleanup

Config-entry removal is handled by Home Assistant after validation succeeds. Package removal is requested only through HACS' repository API when it is available. This avoids leaving HACS metadata out of sync with manually deleted folders.

## System Center

The unified overview exposes migration status including phase, expected migrated counts, validation outcome and removed legacy entries.
