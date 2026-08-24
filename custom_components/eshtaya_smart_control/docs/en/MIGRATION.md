# Automatic Legacy Migration

Eshtaya Smart Control is designed to replace several standalone tools with one unified platform without running two control engines against the same hardware and without requiring you to delete/reinstall the unified integration for normal updates.

## What can be migrated?

There are two major migration paths.

### Existing unified legacy migration

This covers tools such as:

```text
eshtaya_entity_manager
eshtaya_multiway
```

and moves Entity/Alexa rules, Multi-Way configuration, and Smart Group data into the unified stores.

### Legacy Template Manager

Starting with 2.3.x, Template Manager is a first-class module inside Eshtaya Smart Control. Version 2.3.1 expands legacy discovery to include:

- an old config entry when present;
- an externally owned `sensor.eshtaya_template_manager`;
- old-domain services;
- the old custom-component directory;
- known storage/package files;
- generated YAML/JSON used by the previous permanent-entity workflow.

# Core transaction rule

Migration is not “copy and delete.” The safe order is:

```text
Detect
→ Capture
→ Backup
→ Quiesce / stop legacy
→ Import or stage new state
→ Verify
→ Final cleanup
```

If the migrator cannot prove that required data was recovered, it must not assume success or continue destructive cleanup.

# Migration Center states

Important states include:

```text
not_found
prepared
restart_required
completed
rolled_back
error
```

## `not_found`

No legacy evidence requiring migration was found in that run.

Version 2.3.1 does not treat a previous 2.3.0 `not_found` result as permanent proof that no legacy Template Manager exists. It re-evaluates real legacy evidence during startup, allowing a normal update over 2.3.0 to discover generated files missed by the earlier migrator.

## `prepared`

Legacy state has been captured/backed up and the unified runtime is prepared to take ownership.

## `restart_required`

This is a safety checkpoint, not a failure.

For Template Manager it normally means:

- old mappings were recovered;
- a rollback backup was created;
- generated legacy definitions were removed from disk;
- old Light/Fan entities or the compatibility sensor are still resident in Home Assistant memory;
- unified replacements are marked deferred and are not created yet.

The purpose is to prevent:

```text
light.example_2
fan.example_2
sensor.eshtaya_template_manager_2
```

The correct next step is one Home Assistant restart.

## `completed`

Required entities/rules/groups were verified and the unified platform is now the effective owner.

## `rolled_back`

A cutover started but validation failed before final cleanup. The migration attempted to restore the old config/files rather than continuing with an unsafe cleanup.

# Backups

## Entity/Multi-Way migration

Migration Center stores an internal rollback snapshot with enough configuration/entry state to re-enable old components when validation fails.

## Template Manager migration

A physical backup is created under:

```text
/config/eshtaya_smart_control_backups/template_manager_<timestamp>/
```

It can include:

- mappings;
- Entity Registry metadata;
- config-entry metadata;
- generated YAML/JSON;
- known package/storage files;
- the old custom component when present.

The migration does not automatically delete this backup after success.

# Entity & Alexa migration

The general flow is:

1. Detect legacy storage.
2. Create backup state.
3. Copy rules into UnifiedEntityManager when the destination is suitable.
4. Compare expected/actual counts.
5. Validate hidden-entity files.
6. Retire the old implementation after successful verification.

The managed files remain:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

# Multi-Way and Smart Groups migration

The general flow is:

1. Read legacy config/storage.
2. Backup.
3. Prevent old/new runtime overlap.
4. Start the unified runtime.
5. Compare expected and actual group counts.
6. Reconcile hidden-member ownership.
7. Remove the old config entry after verification.

Compatibility aliases preserve common `eshtaya_multiway.*` services after migration so existing automations have a transition path.

# Template Manager migration in 2.3.1

## Mapping sources

The migrator can read live runtime data and files such as:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

When the same permanent entity is found both in files and a live runtime record, the live runtime record wins because it reflects the mapping the old manager is actually using at that moment.

## Data captured before cleanup

The migration preserves, where available:

- permanent `entity_id`;
- `source_entity`;
- Light/Fan type;
- display name;
- Entity Registry metadata such as Area, Icon, and Labels.

After the unified entities start, the migration verifies that the expected IDs exist and are owned by `eshtaya_smart_control`.

## Legacy installations without a config entry

Some older installations are YAML/custom-component based and cannot be cleanly unloaded at runtime.

Version 2.3.1 handles this by backing up/removing known generated definitions and calling `template.reload` when available. If any permanent entity or the old compatibility sensor remains resident in memory, the migration switches to `restart_required` instead of creating duplicates.

# HACS cleanup

Removing legacy HACS repositories is a post-verification cleanup step, not the proof that migration succeeded.

If the HACS API is temporarily unavailable, the data cutover can still be valid while HACS cleanup is reported separately.

# Should I remove and reinstall Eshtaya Smart Control?

No. For a normal update:

```text
HACS Update
→ Restart Home Assistant
→ review Migration Center / Template Manager
```

Deleting the unified config entry can remove state the migrator needs to determine what has already been moved.

# Post-migration validation

Confirm:

- no unexpected `_2` entity IDs;
- old automations still work;
- Alexa files are synchronized;
- Multi-Way and Smart Groups are healthy;
- Template Manager Managed/Missing state is correct;
- no legacy engine is still actively controlling the same hardware.

A full Home Assistant backup remains the strongest disaster-recovery layer before significant upgrades or migrations.
