# Troubleshooting

Start with the visible symptom and work down to the underlying module. Do not remove the integration or delete migration files as the first troubleshooting step; most issues can be diagnosed without losing state.

# 1. A tab is visible but clicking it is denied

If the UI shows:

```text
This role does not have access to that module.
```

check **Access Control → Effective Permissions**.

Version 2.3.0 had a specific frontend bug for Template Manager: `template.view` existed in the backend but an older click guard did not know the `template` view. Version 2.3.1 synchronizes the view map and permission labels with the backend.

After updating:

```text
HACS Update
→ Restart Home Assistant
→ reopen the panel
```

Version 2.3.1 also changes the frontend version query so the corrected JavaScript is requested instead of the cached 2.3.0 module.

# 2. The old Template Manager is still present

Version 2.3.1 checks more than an old config entry. It can detect generated definitions and legacy files such as:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

It also checks the old sensor, services, custom-component directory, and known storage/package paths.

If legacy files are removed but old entities remain resident in Home Assistant memory, migration reports:

```text
restart_required
```

This is intentional. Perform one Home Assistant restart. The unified entities are deferred specifically to prevent duplicates.

# 3. An entity became `light.xxx_2` or `fan.xxx_2`

Do not immediately rename the replacement.

The original entity ID is probably still owned by an old entity in the state machine or Entity Registry.

Check:

- Template Manager migration state;
- entity owner/platform in Entity Registry;
- whether a manual entity was created during migration;
- whether the old method is still loaded in memory.

Version 2.3.1 defers both permanent Light/Fan entities and the compatibility sensor while the old IDs are occupied.

# 4. Template Manager shows Missing

Missing means the configured `source_entity` no longer exists after startup protection.

A temporary `unavailable` source is not automatically treated as a permanently missing mapping.

Procedure:

1. Let Tuya/the source integration finish loading.
2. Refresh Template Manager.
3. Find the new physical source entity ID.
4. Use a suggested replacement or manual Source/Relink.
5. Keep the permanent Light/Fan entity ID unchanged unless you intentionally want to rename it.

# 5. Tuya is slow or does not load

The current Tuya frontend/backend includes:

- bounded frontend WebSocket requests;
- safe retry for read operations;
- backend refresh locking;
- last-success cache for normal reads;
- forced refresh that exposes the real cloud error.

Check:

- internet connectivity;
- Tuya region/endpoint;
- Client ID / Secret / UID;
- cloud project permissions;
- Home Assistant logs.

# 6. Groups or entity pages sometimes remain loading

The unified shell loads modules independently. A temporary Tuya failure should not block Entity Control or Multi-Way from mounting.

Multi-Way uses settled independent reads and debounced engine-event refresh to prevent one failed request or event storm from cancelling the entire page load.

If one module still fails:

- inspect the browser console;
- identify the first error, not only follow-on errors;
- capture the WebSocket error message;
- inspect Home Assistant logs for the corresponding backend module.

# 7. Alexa files are out of sync

The two managed files are:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

Use **System Center → Repair Alexa Files** or the regeneration tools in Entity Control.

# 8. Multi-Way repeats commands or oscillates

Review:

- controller mode;
- debounce;
- cloud echo guard;
- physical priority;
- settle/source-stable settings;
- confirmation/retry behavior;
- Activity history to identify which path emitted each command.

Do not add arbitrary delays before identifying the duplicate command source.

# 9. Eshtaya permission is present but an operation is still denied

Some operations also rely on Home Assistant’s native entity/account permissions.

For example, a user can have an Eshtaya module permission while Home Assistant itself denies an edit/control action on the target entity.

Check both:

- Eshtaya Effective Permissions;
- the user’s actual Home Assistant role/native permissions.

# 10. The frontend still looks like the old version after HACS Update

The panel asset includes the integration version:

```text
smart-control-panel-v23.js?v=<VERSION>
```

For 2.3.1 verify:

- HACS actually installed version 2.3.1;
- Home Assistant was restarted;
- the browser was refreshed;
- the loaded asset uses `?v=2.3.1` if you inspect the Network tab.

# What to include in a bug report

Provide:

1. Home Assistant version.
2. Eshtaya Smart Control version.
3. Affected module/tab.
4. Exact error text.
5. Browser console for UI issues.
6. Home Assistant traceback for backend issues.
7. Migration state when relevant.
8. Whether this was an update over an existing installation or a new install.

Never include Tuya Client Secret or access tokens.
