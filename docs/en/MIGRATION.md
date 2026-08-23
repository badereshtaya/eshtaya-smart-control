# Automatic Legacy Migration

## Supported legacy integrations
- Eshtaya Entity Manager (`eshtaya_entity_manager`).
- Eshtaya Multi-Way Control (`eshtaya_multiway`).

## Transaction model
Migration is designed as a guarded cutover, not a blind copy. It detects legacy config entries/storage, creates an independent backup, copies only into empty unified destinations, disables legacy engines before starting the new runtime, validates migrated counts and removes legacy config entries only after validation succeeds.

## Migration phases
1. Detect legacy entries/storage.
2. Backup legacy configuration and entry metadata.
3. Copy Entity rules, Multi-Way and Smart Group data where needed.
4. Disable legacy entries to prevent two control engines acting on the same hardware.
5. Start the unified runtime.
6. Compare expected and actual rule/group counts.
7. Remove verified legacy config entries.
8. Reconcile Smart Group hidden-member ownership.
9. Attempt HACS cleanup through HACS APIs when available.

## Backup location
The internal migration backup uses `eshtaya_smart_control.migration_backup`. The report exposes the backup store name but not its raw payload.

## Rollback
If startup or validation fails before final cleanup, entries disabled by the migration are re-enabled. Migration state records the reason and restored-entry count. A Home Assistant full backup remains the strongest disaster-recovery fallback and is still recommended.

## Compatibility aliases
After legacy Multi-Way is retired, compatibility service aliases preserve common `eshtaya_multiway.*` calls by forwarding them to the new engine so existing scripts/automations have a transition path.

## Existing v1.x unified installations
Updating Eshtaya Smart Control does not rerun a completed migration destructively. Existing unified storage and config entry are reused.

## Do not manually race the migration
Avoid deleting old config entries or folders while the migration is running. Wait for Migration Center to complete or roll back, then resolve any recorded error.
