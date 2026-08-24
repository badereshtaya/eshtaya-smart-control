# Getting Started with Eshtaya Smart Control

This guide covers installation, updates, first startup, and the checks that matter before using the platform in a real Home Assistant project.

## What is Eshtaya Smart Control?

**Eshtaya Smart Control** is a unified Home Assistant platform that combines:

- Entity and Alexa exposure management.
- Optional Tuya Cloud management.
- Multi-Way control, Smart Groups, and Action Groups.
- Template Manager for permanent Light/Fan entities backed by physical switches.
- System diagnostics and reports.
- Eshtaya module permissions and supported Home Assistant account-role controls.
- Arabic/English in-app documentation.

## New installation through HACS

1. Open **HACS → Integrations**.
2. Add the custom repository:

```text
https://github.com/badereshtaya/hacs-eshtaya-smart-control
```

3. Install **Eshtaya Smart Control**.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration**.
6. Search for **Eshtaya Smart Control** and complete setup.

Tuya credentials are not required during the initial installation. Tuya is optional and can be activated later from Tuya Control.

## Updating an existing installation

The normal update path is supported and preferred:

```text
HACS → Eshtaya Smart Control → Update
→ Restart Home Assistant
→ Open Eshtaya Smart Control
```

**Do not remove the integration just to update it.** Removing the config entry may discard state that could otherwise be migrated automatically.

Version 2.3.1 also changes the frontend version string so Home Assistant and the browser request fresh JavaScript after restart instead of continuing to use the 2.3.0 asset from cache.

## If you use the old Template Manager method

Version 2.3.1 can migrate legacy generated YAML/JSON installations, not only old config-entry installations.

The migrator recognizes sources such as:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

Before destructive cleanup it writes a rollback backup under:

```text
/config/eshtaya_smart_control_backups/
```

If the old generated entities remain resident in Home Assistant memory, the new entities are intentionally deferred and the migration reports **Restart Required**. This prevents `*_2` entity IDs and prevents two engines from controlling the same physical source. One additional Home Assistant restart completes the exact-ID takeover.

## Recommended first tour

Review the platform in this order:

1. **Dashboard** — health score and module status.
2. **Entity & Alexa Control** — entity rules and hidden-entity files.
3. **Tuya Control** — activate only if direct cloud management is needed.
4. **Multi-Way** — verify groups and health.
5. **Template Manager** — verify Managed / Available / Missing and migration state.
6. **System Center** — diagnostics, migration, reports, and repairs.
7. **Access Control** — verify end-user permissions before handover.

## Access layers

There are two different access layers:

- **Eshtaya permissions** control access to modules and actions inside Eshtaya Smart Control.
- **Home Assistant Core access** controls supported system-wide account roles such as Administrator, User, and Read Only.

Granting `template.manage`, for example, does not make a user a Home Assistant Administrator.

## Before handover

A production installation should have:

- no unexplained migration error;
- no unintended Missing template source;
- healthy Multi-Way/Smart Group behavior;
- synchronized Alexa hidden-entity files;
- permissions tested with a real non-admin account;
- a current Home Assistant backup.

Use the specialized guides under `docs/en` or the in-app Documentation Center for deeper configuration details.
