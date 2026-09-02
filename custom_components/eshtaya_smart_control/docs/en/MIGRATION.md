# Migration

Version 2.4.0 changes legacy Eshtaya migration from an automatic background behavior into an **explicit, configurable operation**.

This guide distinguishes three different concepts that should not be mixed together:

1. migration from retired Eshtaya integrations;
2. the already-integrated Template Manager data that belongs to Eshtaya Smart Control itself;
3. discovery/takeover of native Home Assistant Group helpers.

# Default behavior in 2.4.0

For a normal installation that already completed its old migrations:

```text
Enable legacy Eshtaya migration = Off
Legacy HACS cleanup = Off
Legacy service aliases = Off
```

With the master migration switch off, a new migration run does not intentionally:

- scan old Entity Manager / Multi-Way / Template Manager data for takeover;
- disable an old config entry;
- copy old storage;
- remove an old config entry;
- remove legacy HACS repositories;
- register retired service-domain aliases.

Existing **unified** Entity Control, Multi-Way, Smart Groups and Template Manager data loads normally.

# Configure migration

Open:

```text
Settings → Devices & services → Eshtaya Smart Control → Configure
```

Migration controls:

| Option | Default | Purpose |
|---|---:|---|
| Enable legacy Eshtaya migration | Off | Master switch for new retired-tool migration |
| Migrate old Entity Manager | On | Included only when master migration is enabled |
| Migrate old Multi-Way / Smart Groups | On | Included only when master migration is enabled |
| Migrate old Template Manager | On | Included only when master migration is enabled |
| Legacy HACS cleanup | Off | Remove verified retired HACS repositories after successful migration |
| Legacy service aliases | Off | Keep compatibility service names for old automations |

The component switches are independent. If old Entity Manager is disabled in the migration options, the coordinator does not intentionally copy, unload or remove that old domain while migrating another selected tool.

# Safety exception: an in-progress cutover may finish

Disabling future migration must never strand a transactional migration that had already reached a destructive preparation stage before the 2.4 upgrade.

Therefore, a previously started migration in an in-flight state such as:

```text
prepared
legacy_disabled
validated
cleanup_partial
restart_required
```

may be resumed automatically even when the new master switch defaults to Off.

This behavior is strictly for completing an already-started safe cutover. It is not a new background scan of retired tools.

# Old Entity Manager / Multi-Way migration

When explicitly enabled, the coordinator:

1. detects only the selected old domains;
2. loads only the selected old storage;
3. creates a migration backup;
4. copies data only into an empty/compatible unified target;
5. disables the selected old config entry before unified runtime ownership;
6. validates migrated counts;
7. removes selected old config entries only after validation;
8. rolls back disabled entries if validation fails.

Unselected legacy domains are outside that transaction.

# Old Template Manager migration

Template Manager has its own zero-duplicate migration path because it owns permanent `light.*` and `fan.*` entity IDs.

When explicitly enabled, it may recover mappings from:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

and/or the old runtime sensor/services/config entry.

It creates a rollback backup before legacy cleanup.

## `restart_required`

If old permanent entities remain resident in Home Assistant memory after their generated definitions are removed, the unified entities remain deferred. No `_2` duplicate is intentionally created.

The next Home Assistant restart completes the exact-ID takeover after the retired definitions no longer load.

A migration already waiting at `restart_required` is considered an in-progress cutover and is allowed to resume in 2.4 even when new legacy migrations are disabled by default.

# Legacy HACS cleanup

Cleanup is now a separate explicit option and defaults Off.

Turning on the migration master does not automatically imply that HACS repositories should be removed. Cleanup is scheduled only when:

- migration/verification is complete enough for cleanup; and
- `legacy_hacs_cleanup` is enabled.

# Legacy service aliases

Compatibility aliases are also independent and default Off.

Enable them only if existing automations still use retired domains such as:

```text
eshtaya_multiway.*
eshtaya_template_manager.*
```

New automations should use the unified `eshtaya_smart_control` services.

# Native Home Assistant Groups are NOT legacy migration

Discovery of Home Assistant Group helpers and transactional Take Over remain available regardless of the legacy migration master setting.

Typical flow:

```text
Home Assistant Group helper
→ Eshtaya discovers it
→ operator chooses Take Over
→ Eshtaya validates compatibility
→ exact entity ID / metadata are preserved where supported
```

This is an operator-requested transformation of current Home Assistant configuration, not an automatic migration from a retired Eshtaya custom integration.

# Recommended configuration after a successful historical migration

For systems where all old Eshtaya tools are already migrated:

```text
legacy_migration_enabled = false
legacy_hacs_cleanup = false
legacy_service_aliases = false
```

Keep the individual migration component checkboxes at their defaults; they do nothing while the master migration switch is Off.

Native Group discovery/takeover continues to work.

# Diagnostics

System Report includes only non-secret startup/migration settings plus the sanitized historical migration state. Raw backup data and Tuya credentials are excluded.

If a migration is intentionally enabled, take a Home Assistant backup first and keep the Eshtaya migration backup until the cutover is fully verified.
