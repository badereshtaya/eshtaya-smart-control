# Template Manager

Template Manager is the permanent-entity layer inside **Eshtaya Smart Control**. It creates stable Home Assistant `light` or `fan` entities in front of physical `switch` entities, commonly Tuya switches.

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

Shows every permanent entity currently owned by the unified Template Manager, including its source and source state.

Available operations:

- **Edit** — change display name / permanent Entity ID while staying in the same domain.
- **Source / Relink** — replace the physical source without changing the logical permanent entity.
- **Delete** — remove the permanent mapping/entity; the physical switch is not deleted.

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

Multi-Way's new 2.4 Startup Barrier is separate from Template Manager source handling; both are designed to prevent slow provider startup from being mistaken for permanent entity loss.

# Legacy Template Manager migration in 2.4.0

**Legacy Template Manager migration is no longer started automatically for every normal update.**

Open:

```text
Settings → Devices & services
→ Eshtaya Smart Control
→ Configure
```

For a system where migration is already complete, recommended settings are:

```text
Enable legacy Eshtaya migration: Off
Legacy HACS cleanup:             Off
Legacy service aliases:          Off
```

Existing unified Template Manager mappings continue to load normally with Legacy Migration Off.

If you intentionally need to migrate a retired Template Manager later:

1. enable **Legacy Eshtaya migration**;
2. keep **Migrate old Template Manager** enabled;
3. take a Home Assistant backup;
4. save Configure and let the integration reload;
5. review Template Manager / Migration Center state.

The migrator can recover mappings from the old runtime/config entry and known generated sources such as:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

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

A migration already at `restart_required` before upgrading to 2.4.0 is allowed to finish even though new Legacy Migration runs default to Off. This prevents an earlier transaction from being stranded halfway through cutover.

# Backup and migration lock

Before removing legacy definitions, the migration keeps a rollback backup under:

```text
/config/eshtaya_smart_control_backups/template_manager_<timestamp>/
```

While a migration is active and incomplete:

- UI mutation controls are locked;
- backend create/edit/delete/relink calls are rejected;
- deferred entities do not claim IDs still owned by the old runtime.

# Services

Unified services:

```text
eshtaya_smart_control.template_scan
eshtaya_smart_control.template_create
eshtaya_smart_control.template_edit
eshtaya_smart_control.template_delete
eshtaya_smart_control.template_relink
```

Legacy `eshtaya_template_manager.*` aliases are now an explicit compatibility option and default **Off**. Enable them only when old automations still require the retired service domain.

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

If all old Template Manager data is already inside Eshtaya Smart Control:

- leave Legacy Migration Off;
- leave Legacy HACS cleanup Off unless you intentionally run a verified cleanup;
- leave Legacy Service Aliases Off unless old automations need them;
- use the normal unified Template Manager for future mappings and source relinks.
