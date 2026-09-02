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

# Installation through HACS

1. Open **HACS → Integrations**.
2. Add the custom repository:

```text
https://github.com/badereshtaya/hacs-eshtaya-smart-control
```

3. Install **Eshtaya Smart Control**.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration**.
6. Search for **Eshtaya Smart Control** and complete setup.

Tuya OpenAPI credentials are not required during initial installation. Tuya Control is optional.

# Updating an existing installation

Use the normal update path:

```text
HACS → Eshtaya Smart Control → Update
→ Restart Home Assistant
→ Open Eshtaya Smart Control
```

Do **not** delete the unified Config Entry just to update.

# What is different in 2.4.0?

Version 2.4.0 introduces a startup barrier designed for slow/cloud-backed Home Assistant integrations such as official Tuya.

The old Multi-Way runtime used a fixed delay measured from Eshtaya load time. That could expire before Tuya restored a referenced entity and produce a false Repair such as:

```text
Multi-way output entity is missing
```

2.4.0 now layers:

1. official Tuya `after_dependencies` ordering;
2. Home Assistant startup-complete waiting;
3. referenced Config Entry readiness checks;
4. a configurable settle period;
5. a post-start Repair grace period plus repeated missing confirmations.

During protected startup, Multi-Way reports `starting/recovering`, not a fault, and missing-output/controller Repairs are suppressed.

Recommended defaults:

```text
Wait for Home Assistant startup:       On
Wait for referenced integrations:      On
Startup settle:                         15 seconds
Startup maximum wait:                  240 seconds
Missing Repair grace:                  90 seconds
Missing confirmations:                 3
```

# Configure startup and migration controls

Open:

```text
Settings → Devices & services
→ Eshtaya Smart Control
→ Configure
```

Saving the options reloads the Eshtaya config entry automatically.

## Legacy migration defaults

For systems that already completed migration from the retired Eshtaya tools, use:

```text
Enable legacy Eshtaya migration: Off
Legacy HACS cleanup:             Off
Legacy service aliases:          Off
```

The individual old Entity Manager / Multi-Way / Template Manager selectors can remain enabled; they are inactive while the master Legacy Migration switch is Off.

An already-started transactional cutover may still be allowed to finish after an upgrade so the system cannot be stranded halfway through a previous migration.

## Native Home Assistant Groups remain available

Native/UI-created Home Assistant Group discovery and transactional Take Over are **not** legacy Eshtaya migration. They remain available when Legacy Migration is Off.

# If an old Template Manager cutover is still in progress

If a previous migration is already at:

```text
restart_required
```

perform the required Home Assistant restart. The unified Template Manager keeps the replacement entities deferred until the retired runtime releases the exact entity IDs, preventing `*_2` duplicates.

For a system where this migration has already completed, leave Legacy Migration Off.

# Recommended first tour

Review the platform in this order:

1. **Dashboard** — health score and startup/module status.
2. **Entity & Alexa Control** — entity rules and hidden-entity files.
3. **Tuya Control** — activate only if direct cloud management is needed.
4. **Multi-Way** — verify groups and the startup state.
5. **Template Manager** — verify Managed / Available / Missing.
6. **System Center** — startup barrier, diagnostics, migration history, reports and repairs.
7. **Access Control** — verify end-user permissions before handover.

# Access layers

There are two different access layers:

- **Eshtaya permissions** control access to modules and actions inside Eshtaya Smart Control.
- **Home Assistant Core access** controls supported system-wide account roles such as Administrator, User, and Read Only.

Granting `template.manage`, for example, does not make a user a Home Assistant Administrator.

# Before handover

A production installation should have:

- startup barrier reaches `ready` after restart;
- no false missing-output Repairs during provider restore;
- no unexplained migration error;
- no unintended Missing Template source;
- healthy Multi-Way/Smart Group behavior after startup settles;
- synchronized Alexa hidden-entity files;
- permissions tested with a real non-admin account;
- a current Home Assistant backup.

Use the specialized guides under `docs/en` or the in-app Documentation Center for deeper configuration details.
