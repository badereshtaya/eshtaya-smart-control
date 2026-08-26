# Template Manager

Template Manager is the permanent-entity layer inside **Eshtaya Smart Control**. It creates a stable Home Assistant `light` or `fan` entity in front of a physical `switch`, commonly a Tuya switch.

## Why use a permanent entity?

Instead of building dashboards, automations, and Alexa mappings around the physical source entity ID, you can keep a stable logical entity.

Example:

```text
Physical source: switch.living_main_light
Permanent entity: light.living_main_light
```

If the Tuya device is replaced or its source entity ID changes, you can **Relink** the physical source while keeping:

```text
light.living_main_light
```

unchanged.

# Tabs

## Available

Shows compatible `switch` entities that are not already used as the source of a managed permanent entity.

For each item you can choose:

- **Type** — Light or Fan.
- **Name** — display name.
- **Entity ID** — final permanent entity ID.
- **Create** — store the mapping and create the managed entity.

A default suggestion converts, for example:

```text
switch.office_light
```

into:

```text
light.office_light
```

Selecting Fan changes the domain to `fan`.

Creation is blocked when the requested entity ID is already present in the Home Assistant state machine, Entity Registry, or Template Manager store.

## Managed

Lists every permanent entity currently owned by Template Manager.

Each row exposes:

- name;
- permanent entity ID;
- `source_entity`;
- source state;
- source platform;
- Light/Fan type.

### Edit

Edit can change the display name and permanent entity ID. The entity must remain in its original domain; a Light is not converted into a Fan simply by renaming the entity ID.

When possible, entity-ID changes are performed through Home Assistant’s Entity Registry so the same managed entity is renamed rather than replaced by an unrelated duplicate.

### Source / Relink

Changes the physical source behind the existing permanent entity.

Example:

```text
Old source: switch.living_light_old
New source: switch.living_light_new
Permanent:  light.living_light
```

Only the source changes. Automations and dashboards can continue using `light.living_light`.

### Delete

Deletes the permanent Template Manager entity and its mapping. It does **not** delete the physical Tuya switch.

## Missing

A managed item is placed in Missing when its configured `source_entity` no longer exists after startup protection.

A temporary `unavailable` state does not automatically mean the mapping should be deleted.

Template Manager can rank replacement suggestions based on similarity to the previous source entity ID. A suggestion is a convenience, not proof that the device is correct—verify the physical device before relinking.

# Live state tracking

Permanent entities mirror the physical switch state and send control commands to the source:

```text
Permanent entity state ← physical switch state
Permanent entity command → switch service call
```

A change originating from Tuya, a wall button, Home Assistant, or another automation is reflected by the permanent entity.

# Startup protection

Cloud-backed integrations can take time to populate states during Home Assistant startup.

Template Manager waits within a bounded grace period when a source is still present in Entity Registry but has not appeared in the state machine. This avoids incorrectly marking every mapping Missing because Tuya loaded slowly.

# Legacy migration in 2.3.1

Version 2.3.1 supports multiple shapes of the old Template Manager implementation.

## Legacy evidence

The migrator can detect:

- old `eshtaya_template_manager` config entries;
- an externally owned `sensor.eshtaya_template_manager`;
- old-domain services;
- the old custom-component directory;
- known storage/package files;
- generated YAML/JSON definitions used by the previous permanent-entity workflow.

Known generated sources include:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

## Why file-based recovery matters

Some older installations were YAML/generated-file based rather than a clean config-entry integration. Relying only on a runtime sensor could miss those mappings when startup order changed.

Version 2.3.1 can recover mappings directly from generated files and merge them with live runtime mappings when available. Live runtime mappings take precedence because they reflect the mapping the old manager was actually using at that moment.

# Safe migration sequence

The high-level sequence is:

```text
Detect legacy evidence
→ wait for old runtime when useful
→ read runtime + generated mappings
→ validate readable data
→ capture Entity Registry metadata
→ create rollback backup
→ disable/unload old config entry when present
→ remove old services
→ remove legacy generated files after backup
→ call template.reload when available
→ wait for old entity IDs to be released
```

Then one of two paths is used.

## Path A — old IDs are released

```text
Import mappings
→ start unified Light/Fan entities
→ verify exact IDs and platform ownership
→ restore name/icon/area/labels
→ remove old config entry
→ mark completed
```

## Path B — old runtime is still holding IDs

If an old entity such as:

```text
light.room_1
```

is still resident in Home Assistant memory after its generated file was removed, the unified entity is **not** forced into existence.

Instead, the migration:

- marks records as deferred;
- does not create the new Light/Fan entities;
- does not create the compatibility sensor on a conflicting ID;
- locks Create/Edit/Delete/Relink;
- reports `restart_required`.

After the next Home Assistant restart, the removed legacy files no longer recreate the old entities and the unified runtime can claim the **same entity IDs**.

This is specifically designed to prevent:

```text
light.room_1_2
fan.room_1_2
sensor.eshtaya_template_manager_2
```

and to prevent two control engines from operating the same source.

# Backup

Before removing legacy definitions, the migrator creates a rollback backup under:

```text
/config/eshtaya_smart_control_backups/template_manager_<timestamp>/
```

The backup can include:

- recovered mappings;
- Entity Registry metadata;
- old config-entry metadata;
- generated YAML/JSON/storage files;
- the old custom component when present.

Keep the backup until migration is verified complete.

# Migration lock

While a legacy migration is active and incomplete, version 2.3.1 locks mutations at two levels:

1. the UI disables mutation controls;
2. the Python backend rejects create/edit/delete/relink even if a WebSocket or service call is sent manually.

This prevents configuration from changing in the middle of the cutover.

# Services

Native services include:

```text
eshtaya_smart_control.template_scan
eshtaya_smart_control.template_create
eshtaya_smart_control.template_edit
eshtaya_smart_control.template_delete
eshtaya_smart_control.template_relink
```

After migration is completed, compatibility aliases can be registered under the old `eshtaya_template_manager` service domain when no old implementation remains.

# Compatibility sensor

After successful takeover, the unified integration provides:

```text
sensor.eshtaya_template_manager
```

with attributes such as:

- `managed`;
- `candidates`;
- `missing`;
- counts;
- readiness;
- migration state;
- update time.

# Permissions

```text
template.view
```

allows viewing and scanning.

```text
template.manage
```

allows creating, editing, deleting, and relinking permanent entities.

Version 2.3.1 also fixes the old frontend navigation guard so it recognizes `template.view` exactly like the backend.

# What to do after updating to 2.3.1

For an installation that uses the old method:

```text
HACS Update
→ Restart Home Assistant
→ open Template Manager
```

If the page reports **Migration completed**, the cutover is finished.

If it reports **Restart Required**:

```text
Restart Home Assistant once
→ reopen Template Manager
→ verify Managed entities retain their original IDs without *_2
```

Do not remove and reinstall Eshtaya Smart Control just to complete this migration.
