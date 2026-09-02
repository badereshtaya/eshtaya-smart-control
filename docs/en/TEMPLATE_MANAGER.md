# Template Manager

Template Manager is the permanent-entity layer inside **Eshtaya Smart Control**. It creates or manages stable Home Assistant `light` or `fan` entities in front of physical `switch` entities, commonly Tuya switches.

# Why use permanent entities?

Example:

```text
Physical source:  switch.living_main_light
Permanent entity: light.living_main_light
```

If the physical device or its source entity ID changes later, use **Relink** to point the permanent entity at a new switch while dashboards, automations and Alexa mappings can keep using the same permanent ID.

# Tabs

## Available

Shows compatible switches not already used as managed sources. Choose:

- Light or Fan;
- display name;
- final permanent Entity ID;
- Create.

Creation is refused if the requested ID is already occupied in the state machine, Entity Registry or Template Manager store.

## Managed

Shows every permanent entity managed by Template Manager, including both native Eshtaya mappings and recognized generated-package mappings.

Available operations:

- **Edit** — change display name / permanent Entity ID while staying in the same domain.
- **Source / Relink** — replace the physical source without changing the logical permanent entity.
- **Delete** — remove the permanent mapping/entity; the physical switch is not deleted.

# Generated package adoption in 2.4.2

A known Eshtaya-generated Home Assistant package is now treated as **Managed** automatically even when Legacy Migration is Off. This specifically includes:

```text
/config/packages/eshtaya_generated_lights.yaml
/config/packages/eshtaya_generated_templates.yaml
/config/eshtaya_template_manager/generated_templates.yaml
```

Depending on the Home Assistant environment, the same config root may be shown on the host as `/homeassistant`, so `/homeassistant/packages/eshtaya_generated_lights.yaml` is the same logical package location on installations that expose that path.

This is intentionally different from destructive legacy migration:

- the package file remains in place;
- Home Assistant's `template` integration remains the runtime owner of those entities;
- Eshtaya mirrors their mappings into Template Manager as Managed records;
- those mirrored records are marked deferred internally so Eshtaya does **not** create duplicate entities with the same IDs;
- the source switches are no longer shown as new Available candidates when they are already used by the generated package.

When Edit, Relink or Delete is used on a generated-package record, Eshtaya updates the **same YAML file**, creates a backup first, writes through a temporary file, and calls `template.reload`.

Backups are stored under:

```text
/config/eshtaya_smart_control_backups/generated_packages/<timestamp>/...
```

You do not need to enable Legacy Migration just to manage an existing `eshtaya_generated_lights.yaml` file.

## Missing

A mapping is Missing when its `source_entity` remains absent after the Template Manager startup protection. A temporary `unavailable` state is not by itself proof that the mapping is gone.

Replacement suggestions are heuristic conveniences. Verify the physical device before relinking.

# Runtime behavior

```text
Permanent entity state   ← source switch state
Permanent entity command → source switch service
```

The permanent entity tracks changes originating from Tuya, wall controls, Home Assistant or other automations.

# Startup protection

Template Manager has its own bounded source-startup protection and the overall Eshtaya 2.4 integration is also scheduled after official Tuya when configured.

Multi-Way's 2.4 Startup Barrier is separate from Template Manager source handling; both are designed to prevent slow provider startup from being mistaken for permanent entity loss.

# Startup and Migration settings in 2.4.2

The controls are available directly inside:

```text
Eshtaya Smart Control → System Center
→ Startup & Migration Settings
```

They also remain available through Home Assistant's integration Configure flow.

For a system where historical migrations are already complete, recommended settings are:

```text
Enable legacy Eshtaya migration: Off
Legacy HACS cleanup:             Off
Legacy service aliases:          Off
```

The individual migration selectors remain visible so you can choose old Entity Manager, Multi-Way/Smart Groups and Template Manager independently if a future migration is intentionally required.

Native Home Assistant Group discovery and **Take Over** are independent from these legacy-migration switches and continue to work with Legacy Migration Off.

# Legacy Template Manager migration

**Legacy Template Manager migration is not started automatically for normal updates.**

If you intentionally need to retire an old standalone Template Manager and move ownership into Eshtaya native entities:

1. enable **Legacy Eshtaya migration**;
2. enable **Migrate old Template Manager**;
3. take a Home Assistant backup;
4. save the settings and let the integration reload;
5. review Template Manager / Migration Center state.

The migrator can recover mappings from the old runtime/config entry and known generated sources such as:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

This explicit migration is a takeover/retirement workflow. It is not required for the normal generated-package management described above.

# Zero-duplicate migration sequence

When explicitly enabled, the migration performs a guarded cutover:

```text
Detect selected legacy evidence
→ recover mappings
→ validate readable data
→ capture Entity Registry metadata
→ create rollback backup
→ quiesce old implementation
→ release exact entity IDs
→ start unified entities
→ verify ownership and IDs
→ final cleanup when enabled
```

## `restart_required`

If retired generated entities remain resident in Home Assistant memory, the unified replacements remain deferred rather than being created as `_2` duplicates.

The next Home Assistant restart completes the exact-ID takeover after the old definitions no longer load.

A migration already at `restart_required` is allowed to finish even though new Legacy Migration runs default to Off. This prevents an earlier transaction from being stranded halfway through cutover.

# Backup and migration lock

During a real cutover phase (`prepared` or `restart_required`):

- UI mutation controls are locked;
- backend create/edit/delete/relink calls are rejected;
- deferred entities do not claim IDs still owned by the old runtime.

A stale failed or rolled-back migration status no longer keeps Template Manager permanently read-only.

# Services

Unified services:

```text
eshtaya_smart_control.template_scan
eshtaya_smart_control.template_create
eshtaya_smart_control.template_edit
eshtaya_smart_control.template_delete
eshtaya_smart_control.template_relink
```

Legacy `eshtaya_template_manager.*` aliases are an explicit compatibility option and default **Off**. Enable them only when old automations still require the retired service domain.

# Compatibility sensor

The unified integration can own:

```text
sensor.eshtaya_template_manager
```

with managed/candidate/missing counts, readiness and migration state.

# Permissions

```text
template.view
template.manage
```

`template.view` allows viewing/scanning. `template.manage` allows create/edit/delete/relink.

# Recommended state after historical migration is finished

- leave Legacy Migration Off;
- leave Legacy HACS cleanup Off unless you intentionally run a verified cleanup;
- leave Legacy Service Aliases Off unless old automations need them;
- keep generated package mappings under normal Template Manager management;
- use explicit Legacy Migration only when you intentionally want a native takeover/retirement of an old implementation.
