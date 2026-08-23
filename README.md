<p align="center">
  <img src="custom_components/eshtaya_smart_control/brand/logo.png" alt="Eshtaya Smart Control" width="560">
</p>

<h1 align="center">Eshtaya Smart Control</h1>

<p align="center">
  <strong>A unified professional control and commissioning platform for Home Assistant.</strong>
</p>

<p align="center">
  Entity & Alexa management · Tuya Cloud administration · Multi-Way switching · Smart Groups · Commissioning · Diagnostics
</p>

<p align="center">
  <a href="https://github.com/badereshtaya/hacs-eshtaya-smart-control/actions"><img src="https://img.shields.io/github/actions/workflow/status/badereshtaya/hacs-eshtaya-smart-control/validate.yml?label=validation" alt="Validation"></a>
  <a href="https://github.com/badereshtaya/hacs-eshtaya-smart-control/releases"><img src="https://img.shields.io/github/v/release/badereshtaya/hacs-eshtaya-smart-control?label=release" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/HACS-Custom-41BDF5" alt="HACS Custom">
  <img src="https://img.shields.io/badge/UI-Arabic%20%7C%20English-7C3AED" alt="Arabic and English UI">
</p>

> **Current unified release:** `1.0.0`  
> **Integration domain:** `eshtaya_smart_control`  
> **Repository:** `badereshtaya/hacs-eshtaya-smart-control`  
> **Interface:** Home Assistant sidebar Control Hub  
> **Access:** Home Assistant administrators only

---

## Table of contents

- [What is Eshtaya Smart Control?](#what-is-eshtaya-smart-control)
- [Control Hub](#control-hub)
- [Modules](#modules)
  - [HomeAssistant Entity Control](#1-homeassistant-entity-control)
  - [Tuya Entity Control](#2-tuya-entity-control)
  - [Multi-Way & Smart Groups](#3-multi-way--smart-groups)
  - [Documentation Center](#4-documentation-center)
  - [System Center](#5-system-center)
- [Installation with HACS](#installation-with-hacs)
- [First setup](#first-setup)
- [Tuya Cloud setup](#tuya-cloud-setup)
- [Alexa hidden entities files](#alexa-hidden-entities-files)
- [Migration from previous Eshtaya integrations](#migration-from-previous-eshtaya-integrations)
- [Architecture](#architecture)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Repository documentation](#repository-documentation)
- [Project structure](#project-structure)
- [Development and validation](#development-and-validation)
- [License](#license)
- [شرح الأقسام بالعربي](#شرح-الأقسام-بالعربي)

---

# What is Eshtaya Smart Control?

**Eshtaya Smart Control** is a modular Home Assistant integration designed to become the central administration toolbox for Eshtaya Smart installations.

Instead of installing separate management pages and separate Eshtaya integrations for each job, the platform provides one integration, one sidebar entry, one configuration entry and one expandable Control Hub.

The first unified release combines three major systems:

| Module | Main purpose |
|---|---|
| **HomeAssistant Entity Control** | Manage Home Assistant display names and Alexa exposure rules at scale |
| **Tuya Entity Control** | Manage Tuya Cloud devices, main names and supported property custom names from inside Home Assistant |
| **Multi-Way & Smart Groups** | Professional software Multi-Way switching, Smart Groups, Action Groups, commissioning and diagnostics |

The platform also includes a **Documentation Center** and **System Center** so that configuration, operating guidance, module status and migration information stay in the same interface.

## Design goals

Eshtaya Smart Control is built around a few principles:

- **One platform, many tools.** New Eshtaya Smart tools can be added as modules without creating another sidebar integration.
- **Native Home Assistant administration.** No external PHP dashboard and no Home Assistant long-lived access token are required for the included tools.
- **Professional installer workflow.** Large installations need search, bulk operations, filtering, health information and predictable migration behavior.
- **Safe configuration.** Destructive operations should be explicit, backup-aware and observable.
- **Bilingual operation.** The interface supports Arabic and English, with an Auto mode that follows Home Assistant language.
- **Modular backend.** Each tool has its own manager/API namespace so future modules do not collide with existing engines.

---

# Control Hub

Installing the integration adds a single sidebar panel:

**Eshtaya Smart Control**

The home screen is a Control Hub rather than a long configuration page. Each major tool is represented by its own card and can be opened independently.

The initial Hub contains:

1. **HomeAssistant Entity Control**
2. **Tuya Entity Control**
3. **Multi-Way & Smart Groups**
4. **Documentation Center**
5. **System Center**

A persistent navigation bar lets you move between tools without leaving the Eshtaya Smart Control panel.

## Language modes

The Control Hub supports:

- `Auto` — follows the Home Assistant language.
- `العربية` — forces Arabic / RTL presentation.
- `English` — forces English / LTR presentation.

The language selection is intended to make one installation usable by both installers and end users without maintaining separate interfaces.

---

# Modules

## 1. HomeAssistant Entity Control

HomeAssistant Entity Control is the entity administration and Alexa exposure module.

It is designed for homes where hundreds or thousands of Home Assistant entities make normal per-entity administration too slow.

### Entity naming

Entity display names can be edited directly through Home Assistant's **Entity Registry**.

This means:

- No external PHP endpoint is required.
- No Home Assistant API token is stored by the tool.
- A user-defined display name can be saved quickly.
- The custom name can be reset so Home Assistant returns to the original/friendly name.

The tool does **not** blindly rewrite entity IDs as part of the normal rename action. It focuses on safe display-name administration.

### Alexa exposure rules

Every entity can use one of three modes:

| Rule | Meaning |
|---|---|
| **Auto** | Let the domain/default rules decide |
| **Force Show** | Explicitly expose this entity even when broader rules would normally hide it |
| **Force Hide** | Explicitly exclude this entity from the generated Alexa hidden list |

Rule precedence is:

```text
Force Show
→ Force Hide
→ Domain disabled
→ Automatic entity-category exclusion
→ Automatic keyword exclusion
→ Included
```

`Force Show` has the highest priority intentionally. This allows, for example, one useful sensor or automation to remain exposed while the rest of its domain is disabled.

### Domain rules

Entire Home Assistant domains can be enabled or disabled from Alexa exposure logic.

Typical use cases:

- Keep `light`, `cover`, `climate` or selected `switch` entities available.
- Hide noisy domains such as diagnostics or helper entities.
- Use explicit Force Show exceptions without opening the complete domain.

### Automatic exclusion rules

Entity Control can automatically exclude entities using:

- `entity_category`
- entity ID/name keywords

This is useful for technical controls such as diagnostics, child locks, LED/backlight controls or other implementation entities that should not become voice-assistant devices.

### Search and filters

The entity view supports filtering by:

- Search text.
- Domain.
- Home Assistant Area.
- Source integration/platform.
- Available / unavailable state.
- Alexa effective state.
- Explicit overrides.

### Multi-select batch actions

For large installations, you can select many entities and apply a rule in one operation:

- Show selected.
- Hide selected.
- Return selected to Auto.

Keyword-based bulk editing is also available when an installation uses consistent naming conventions.

### Orphan rule detection

An explicit rule can remain after an entity is removed, renamed or temporarily no longer loaded.

Entity Control identifies those rules as **orphan rules** instead of silently deleting them.

This matters because an integration can be temporarily unavailable and its entities may return later. Cleanup is therefore an explicit maintenance action.

### Alexa rules import/export

The module supports portable `alexa_rules.json` backups containing:

- Domain enabled/disabled settings.
- Entity Force Show / Force Hide rules.
- Automatic excluded entity categories.
- Automatic excluded name keywords.

This format can be moved between Home Assistant installations or used when migrating from the former standalone Entity Manager.

Before replacing the active rule set with an imported backup, the module keeps a backup of the current rule configuration.

### Dual hidden file synchronization

The module maintains these files:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

Both are generated from the same effective rules and are kept byte-identical.

The second path is useful when another system retrieves the list through Home Assistant's `/local/` path.

On a completely fresh installation where neither file exists, valid empty YAML files are created as:

```yaml
[]
```

Using `[]` instead of a zero-byte file keeps YAML include behavior deterministic.

### File health

The module checks synchronization using file hashes rather than only checking that both paths exist.

If the copies differ, the UI can report a synchronization problem and regenerate both files from the authoritative rule store.

### Entity Control documentation

- [English documentation](docs/en/ENTITY_CONTROL.md)
- [الشرح بالعربية](docs/ar/ENTITY_CONTROL.md)

---

## 2. Tuya Entity Control

Tuya Entity Control replaces the former external PHP Tuya administration page with a native Home Assistant module.

The browser communicates only with Home Assistant. Tuya authentication, request signing and access-token handling happen in the backend.

### Portable configuration per Home Assistant

Tuya credentials are **not hard-coded in the integration**.

Each Home Assistant installation can configure its own:

- Tuya region/data center.
- API endpoint when Custom mode is used.
- Client ID.
- Client Secret.
- UID.

This makes the same HACS repository usable across different homes, customers and Tuya projects.

### Supported region presets

The integration contains presets for the major Tuya OpenAPI regions and also supports a **Custom** endpoint for installations that require a different Tuya endpoint.

Because Tuya projects must match the correct data center, choosing the region that matches the Tuya IoT project is important.

### Connection validation

When complete Tuya credentials are entered, the configuration flow validates the connection before accepting the account configuration.

The Tuya control interface also provides account/status controls so the installer can identify configuration problems without using the former PHP page.

### Device list

The module can load the devices assigned to the configured Tuya UID and expose information such as:

- Device name.
- Device ID.
- Online/offline state.
- Category.
- Product ID.
- Tuya icon when available.

The backend uses a short device-list cache to reduce unnecessary Tuya OpenAPI calls during normal navigation.

### Search, categories and filtering

The interface supports:

- Device-name search.
- Device-ID search.
- Category search/filtering.
- Product-ID search.
- Online filter.
- Offline filter.
- Pagination for larger projects.

Category codes are presented with friendlier category descriptions where known.

### Device details

For an individual Tuya device, the tool can request detailed device information from Tuya and expose available fields such as:

- UUID.
- Product ID.
- Local/WAN IP information when returned by Tuya.
- Category.
- Current Shadow Properties.

### Main Tuya device rename

The main device name can be edited directly through Tuya OpenAPI.

This is a Tuya-side change, not merely a Home Assistant display label.

### Switch / DP custom-name editor

For devices that expose supported Shadow Properties, the module identifies actual naming targets such as:

```text
switch_1
switch_2
switch_3
socket_1
control
```

The custom name can then be updated using Tuya's property `custom_name` functionality.

This is especially useful for multi-gang Tuya wall switches where every gang needs a meaningful name before or during commissioning.

### Bulk editor

Large installations often contain many multi-gang switches.

The Bulk Editor is intended to reduce repetitive work by loading compatible device properties and allowing multiple main/sub-name updates from one workflow.

Backend property loading uses bounded concurrency to avoid generating an uncontrolled burst of Tuya API requests.

### Tuya OpenAPI operations

The module currently uses the Tuya OpenAPI flows needed for:

```text
Authentication / access token
Device listing by UID
Device details
Shadow Properties
Main device rename
Property custom-name update
```

All signing is performed server-side using HMAC-SHA256.

### Credential handling

The Tuya Client Secret and access tokens are never intended to be sent back to the panel in status responses.

They are not stored in frontend JavaScript or browser local storage.

### Tuya Control documentation

- [English documentation](docs/en/TUYA_CONTROL.md)
- [الشرح بالعربية](docs/ar/TUYA_CONTROL.md)

---

## 3. Multi-Way & Smart Groups

This module integrates the mature **Eshtaya Multi-Way Control 3.3.1** runtime into the unified platform.

It is not only a UI shortcut. The Multi-Way and Smart Group engines, storage, Home Assistant platforms and reliability logic are part of Eshtaya Smart Control.

### Multi-Way engine

Multi-Way creates software-defined 2-way / 3-way / N-way control around a real output.

A typical group contains:

```text
Physical Output
└── switch.living_main

Controllers
├── switch.living_entrance
├── switch.living_sofa
└── button.living_bedside

Virtual Entity
└── light.living_room_control
```

You can then control one electrical load from multiple Home Assistant-backed wall inputs without requiring traditional electrical multi-way wiring between all controller locations.

### Controller modes

Controllers can use behavior such as:

- Mirror.
- Toggle.
- Momentary On.
- Momentary Off.
- Event.
- Follow Output.

Advanced groups can also use inversion, reflection and authority/recovery behavior.

### Rapid physical input reliability

The engine is designed for real wall-switch behavior, including rapid input.

It preserves ordered physical edges, protects against stale cloud echoes and performs final source reconciliation so a delayed integration update is less likely to leave the logical group in the wrong state.

### Performance profiles

Groups can use different reliability/performance profiles according to the installation:

| Profile | Goal |
|---|---|
| **Instant** | Lowest perceived wall-switch latency |
| **Balanced** | Fast operation with more confirmation |
| **Safe** | Stronger verification for slower or unreliable devices |

### Smart Groups

Smart Groups provide a higher-level grouping engine for Home Assistant entities.

They support physical-controller groups and virtual groups, while retaining domain-aware behavior instead of reducing every device to a generic ON/OFF switch.

Supported native group domains include categories such as:

- Light.
- Switch.
- Cover.
- Fan.
- Lock.
- Media Player.
- Valve.
- Sensor.
- Binary Sensor.
- Button.
- Event.
- Notify.

### Action Groups

Scene, Script and Automation groups are treated as stateless actions rather than fake persistent switches.

Action Groups can execute:

- Scenes.
- Scripts.
- Automations.

Execution can be parallel or sequential depending on the workflow.

### Commissioning tools

The Multi-Way module includes installer-focused tools such as:

- Learn Mode.
- Area-aware setup.
- Templates.
- Clone workflows.
- Group discovery/commissioning assistance.
- Full-system tests.
- Rapid-toggle stress testing.

### Home Assistant Group Take Over

Compatible native Home Assistant Group helpers can be migrated into Eshtaya management while preserving the intended virtual entity identity where the takeover workflow supports it.

Take Over is treated as a controlled migration rather than a blind duplicate/copy operation.

### Health and diagnostics

The engine exposes operational information such as:

- Healthy / degraded state.
- Missing output/controller/member.
- Out-of-sync state.
- Recovering state.
- Latency information.
- Quality/failure information.
- Recent activity and transactions.

### Repair and maintenance

Missing entities can be identified and remapped instead of forcing an installer to recreate the whole group.

The runtime also includes safeguards and maintenance concepts such as bounded verification/retries, command echo handling and optional quarantine/recovery behavior for unreliable members.

### Backup and configuration safety

The integrated module preserves the Multi-Way project's configuration-safety concepts, including:

- Configuration snapshots.
- Undo for supported configuration operations.
- Backup/restore.
- Configuration Lock.
- Safe handling of destructive migration operations.

### Native Home Assistant platforms

The module can create and manage Home Assistant entities across its supported platforms, allowing the resulting virtual controls and diagnostics to be used normally in:

- Dashboards.
- Automations.
- Scripts.
- Scenes.
- Voice-assistant integrations.

### Multi-Way documentation

- [English documentation](docs/en/MULTIWAY.md)
- [الشرح بالعربية](docs/ar/MULTIWAY.md)

---

## 4. Documentation Center

The Control Hub contains a Documentation Center so operating guidance is available from the same platform used for administration.

Documentation is organized by tool and includes topics such as:

- What the tool does.
- Initial configuration.
- Safe operating workflow.
- Migration.
- Security considerations.
- Architecture.

Repository documentation is also maintained in both English and Arabic under `/docs`.

---

## 5. System Center

System Center provides a platform-level view instead of forcing the installer to open each module just to determine whether the system is ready.

The first release includes information such as:

- Entity Control module availability.
- Tuya configured/not-configured state.
- Multi-Way module availability.
- Alexa hidden-file synchronization health.
- Detection of previous standalone Eshtaya Entity Manager installations.
- Detection of previous standalone Eshtaya Multi-Way installations.
- Migration guidance when a legacy integration is detected.

Tuya configuration is optional; the rest of Eshtaya Smart Control can operate without a Tuya project configured.

---

# Installation with HACS

Until Eshtaya Smart Control is available in the default HACS store, install it as a custom repository.

## Add the custom repository

1. Open **HACS**.
2. Open **Integrations**.
3. Open the menu in the upper corner.
4. Select **Custom repositories**.
5. Add:

```text
https://github.com/badereshtaya/hacs-eshtaya-smart-control
```

6. Select category/type:

```text
Integration
```

7. Install **Eshtaya Smart Control**.
8. Restart Home Assistant.

## Add the integration

After Home Assistant restarts:

1. Open **Settings**.
2. Open **Devices & services**.
3. Choose **Add Integration**.
4. Search for:

```text
Eshtaya Smart Control
```

5. Complete the setup.
6. Open **Eshtaya Smart Control** from the Home Assistant sidebar.

The integration uses a single config entry.

---

# First setup

Tuya is optional during initial installation.

You can therefore install Eshtaya Smart Control and immediately use HomeAssistant Entity Control and Multi-Way features without configuring a Tuya account.

If you enter any Tuya credential fields during setup, provide the complete required Tuya account information so the integration can validate the project.

Typical first-install workflow:

```text
Install from HACS
→ Restart Home Assistant
→ Add Eshtaya Smart Control
→ Open Control Hub
→ Review System Center
→ Configure Tuya only if required
→ Configure/import Entity Control rules
→ Migrate Multi-Way only when ready
```

---

# Tuya Cloud setup

Tuya Entity Control requires a Tuya IoT/OpenAPI project that can access the devices associated with the configured UID.

From the Eshtaya Smart Control configuration/reconfigure flow, configure:

```text
Region
Client ID
Client Secret
UID
```

For Custom region mode, configure the API endpoint as well.

## Important region note

The API region must match the Tuya cloud/data center used by the Tuya project and linked devices.

A correct Client ID/Secret with the wrong data-center endpoint can still fail connection validation or device listing.

## Changing Tuya configuration later

Use the Home Assistant integration reconfigure flow instead of editing source files.

This is one of the main differences from the former PHP dashboard: credentials are installation configuration, not constants inside the application source.

---

# Alexa hidden entities files

HomeAssistant Entity Control uses one internal rules model to produce both configured files:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

The files are intentionally synchronized.

## Why two copies?

`/config/hidden_entities.yaml` is suitable for local Home Assistant configuration/include usage.

`/config/www/hidden_entities.yaml` can be served through Home Assistant's `/local/` path when another authorized system needs to read the generated list.

## Fresh installation behavior

When neither file exists, Entity Control creates both as a valid empty list:

```yaml
[]
```

After rules are configured, both files are regenerated from the effective exclusion rules.

## Source of truth

Treat the Entity Control rules stored by Eshtaya Smart Control as the source of truth.

Manual changes to generated files may be replaced by the next regeneration or rule update.

---

# Migration from previous Eshtaya integrations

Eshtaya Smart Control uses a new integration domain:

```text
eshtaya_smart_control
```

This is intentional. It allows a controlled transition without silently taking ownership of a live older installation.

## From Eshtaya Entity Manager

The preferred migration options are:

1. Use the built-in legacy rule import when applicable.
2. Export `alexa_rules.json` from the old tool and import it into HomeAssistant Entity Control.
3. Verify the effective hidden count and generated files.
4. Remove the old tool after verification.

Existing `hidden_entities.yaml` data is handled conservatively because it may already be used by another part of the installation.

## From Eshtaya Multi-Way Control

Do **not** let two Multi-Way engines actively control the same physical group at the same time.

Recommended migration:

1. Open the existing standalone **Eshtaya Multi-Way Control**.
2. Create/export a complete backup of its configuration.
3. Install and configure **Eshtaya Smart Control**.
4. Restore/import the configuration into the integrated Multi-Way module using the supported backup workflow.
5. Verify the virtual entities and their entity IDs.
6. Verify dashboards, scenes, scripts and automations that reference those virtual entities.
7. Test real wall switches and controllers.
8. Check health/diagnostics.
9. Disable or remove the old standalone Multi-Way integration only after validation.

The platform intentionally avoids a blind automatic takeover while the old runtime may still be loaded, because duplicate virtual ownership can cause unavailable entities or conflicting control.

### Migration documentation

- [English migration guide](docs/en/MIGRATION.md)
- [دليل الهجرة بالعربية](docs/ar/MIGRATION.md)

---

# Architecture

Eshtaya Smart Control is one Home Assistant custom integration with modular internal engines.

```text
Eshtaya Smart Control
│
├── Unified Control Hub
│   ├── Home
│   ├── Documentation Center
│   └── System Center
│
├── HomeAssistant Entity Control
│   ├── Entity Registry naming
│   ├── Alexa rules engine
│   ├── Import / export
│   ├── Batch actions
│   └── hidden_entities.yaml synchronization
│
├── Tuya Entity Control
│   ├── Tuya OpenAPI client
│   ├── HMAC request signing
│   ├── access-token handling
│   ├── per-installation account configuration
│   ├── device/cache manager
│   └── admin WebSocket API
│
└── Multi-Way & Smart Groups
    ├── MultiWayManager
    ├── Multi-Way storage
    ├── SmartGroupManager
    ├── Smart Group storage
    ├── native Home Assistant platforms
    ├── Action Groups
    ├── commissioning / Learn workflows
    ├── diagnostics / health
    └── migration / Take Over tools
```

## One sidebar panel

Only the unified Eshtaya Smart Control panel is registered as the platform's main sidebar entry.

Individual tools render inside the unified shell.

## WebSocket namespaces

Management APIs are namespaced so each tool can evolve independently.

The Multi-Way API is isolated under the unified domain, for example:

```text
eshtaya_smart_control/multiway/...
```

Entity Control and Tuya Control also use their own command namespaces under the platform.

## Home Assistant platforms

The integrated Multi-Way/Smart Groups engine forwards the required native Home Assistant platforms from the unified config entry.

This keeps virtual groups and diagnostic/control entities first-class Home Assistant entities rather than UI-only objects.

### Architecture documentation

- [English architecture](docs/en/ARCHITECTURE.md)
- [البنية التقنية بالعربية](docs/ar/ARCHITECTURE.md)

---

# Security

Eshtaya Smart Control is an administrative integration. The security model is therefore intentionally different from exposing a standalone public management page.

## Home Assistant authentication

- The sidebar management panel requires a Home Assistant administrator.
- Management WebSocket commands are administrator-only.
- There is no separate query-string dashboard password.
- There is no Home Assistant long-lived access token embedded in the integration.

## Tuya credentials

- Tuya credentials are configured per Home Assistant installation.
- Client Secret is handled by the backend.
- Tuya request signing occurs in the backend.
- Tuya access tokens are not stored in browser local storage.
- Status responses should not expose the stored Client Secret.

## Generated Alexa files

Alexa rule output is written locally beneath `/config`.

Remember that `/config/www/hidden_entities.yaml` is intentionally placed under Home Assistant's web-served `www` directory. Use that copy only when your architecture requires external retrieval of the generated list.

## Public repositories

Never commit real customer Tuya Client Secrets, Home Assistant tokens or other deployment credentials to this repository.

See [SECURITY.md](SECURITY.md) for security reporting guidance.

---

# Troubleshooting

## Eshtaya Smart Control does not appear after HACS installation

Check:

1. HACS downloaded the repository as an **Integration**.
2. This directory exists:

```text
/config/custom_components/eshtaya_smart_control/
```

3. Home Assistant was restarted after installation/update.
4. Review **Settings → System → Logs** for `eshtaya_smart_control` errors.

## The sidebar still shows an older interface after updating

The frontend asset is versioned, but a browser can still retain previous application resources.

Try:

1. Restart Home Assistant after upgrading the integration.
2. Hard refresh the browser (`Ctrl+F5` on common desktop browsers).
3. Reload the Home Assistant app/webview if using a mobile/tablet client.

## Tuya account validation fails

Check:

- Correct Client ID.
- Correct Client Secret.
- Correct UID.
- Tuya project permissions/subscriptions.
- Correct Tuya data-center region.
- Device/account linkage inside the Tuya IoT project.

A region mismatch is a common cause when credentials look correct but API calls fail.

## Tuya device list is empty

Confirm that the configured UID is the one whose devices are linked to the Tuya project accessible by the configured cloud credentials.

## A Tuya gang/property is not available for rename

Tuya Entity Control only offers properties returned by the device's Shadow Properties and recognized as supported naming targets such as `switch_x`, `socket_x` or `control`.

If Tuya does not expose the property through that API path, the tool cannot safely invent it.

## Alexa files are different

Open Entity Control/System Center and repair/regenerate synchronization. The authoritative rules will be used to rewrite both generated files.

## An entity remains hidden even after its domain is enabled

Check the effective rule order:

```text
Force Show
Force Hide
Domain setting
Auto category rule
Auto keyword rule
```

An explicit Force Hide or automatic rule can still exclude it.

## Multi-Way virtual entities conflict during migration

Do not keep the old standalone engine and new integrated engine controlling the same migrated groups simultaneously.

Return to the controlled migration process and verify ownership before removing the old integration.

---

# Repository documentation

## English

- [HomeAssistant Entity Control](docs/en/ENTITY_CONTROL.md)
- [Tuya Entity Control](docs/en/TUYA_CONTROL.md)
- [Multi-Way & Smart Groups](docs/en/MULTIWAY.md)
- [Migration](docs/en/MIGRATION.md)
- [Architecture](docs/en/ARCHITECTURE.md)

## العربية

- [HomeAssistant Entity Control](docs/ar/ENTITY_CONTROL.md)
- [Tuya Entity Control](docs/ar/TUYA_CONTROL.md)
- [Multi-Way & Smart Groups](docs/ar/MULTIWAY.md)
- [الهجرة](docs/ar/MIGRATION.md)
- [البنية التقنية](docs/ar/ARCHITECTURE.md)

---

# Project structure

```text
hacs-eshtaya-smart-control/
├── .github/
│   └── workflows/
│       ├── validate.yml
│       └── release.yml
├── custom_components/
│   └── eshtaya_smart_control/
│       ├── __init__.py
│       ├── config_flow.py
│       ├── const.py
│       ├── manifest.json
│       ├── panel.py
│       ├── websocket.py
│       ├── entity_control/
│       │   ├── manager*.py
│       │   └── websocket*.py
│       ├── tuya/
│       │   ├── client.py
│       │   ├── manager.py
│       │   └── websocket.py
│       ├── multiway/
│       │   ├── manager.py
│       │   ├── smart_group_manager.py
│       │   ├── storage.py
│       │   ├── smart_storage.py
│       │   ├── native_group_migration.py
│       │   └── ...
│       ├── frontend/
│       │   ├── smart-control-panel.js
│       │   ├── tuya-control.js
│       │   ├── entity/
│       │   └── multiway/
│       ├── translations/
│       │   ├── ar.json
│       │   └── en.json
│       └── brand/
├── docs/
│   ├── ar/
│   └── en/
├── CHANGELOG.md
├── SECURITY.md
├── LICENSE
├── hacs.json
└── README.md
```

---

# Development and validation

The repository includes validation workflows intended to catch packaging and Home Assistant/HACS compatibility problems before release.

Local development should at minimum validate:

```text
Python syntax
JavaScript syntax
JSON syntax
HACS repository structure
Home Assistant / hassfest validation
```

When changing one module, keep its backend command namespace and frontend boundary isolated from the other tools unless the change belongs in the unified Core/System layer.

## Versioning

The unified platform starts at:

```text
1.0.0
```

The embedded Multi-Way runtime originated from Eshtaya Multi-Way Control `3.3.1`, but the unified platform has its own independent version lifecycle going forward.

See [CHANGELOG.md](CHANGELOG.md) for release changes.

---

# License

Eshtaya Smart Control is licensed under the [MIT License](LICENSE).

---

# شرح الأقسام بالعربي

هذا ملخص سريع للأقسام الرئيسية داخل **Eshtaya Smart Control** وما الفائدة من كل واحد:

## 1 — HomeAssistant Entity Control

هذا القسم مخصص لإدارة كيانات Home Assistant نفسها بشكل أسرع وأسهل، خصوصًا في البيوت التي تحتوي عدد كبير جدًا من الأجهزة والـEntities.

**شو بعمل؟**

- تغيير الاسم الظاهر للـEntity بسرعة.
- تحديد إذا الـEntity يظهر على Alexa أو ينحجب عنها.
- خيارات `Auto / Show / Hide` لكل Entity.
- فلترة وبحث حسب الغرفة، النوع، الـIntegration والحالة.
- تعديل مجموعة كبيرة من الـEntities مرة واحدة.
- استيراد وتصدير `alexa_rules.json`.
- كشف القواعد القديمة المرتبطة بـEntities لم تعد موجودة.
- إنشاء ومزامنة الملفين:
  - `/config/hidden_entities.yaml`
  - `/config/www/hidden_entities.yaml`

**الفائدة:** بدل ما تدور على كل Entity وتعدلها لوحدها أو تعدل ملفات يدويًا، بتدير الموضوع كامل من لوحة واحدة وبطريقة منظمة وآمنة.

## 2 — Tuya Entity Control

هذا القسم بديل احترافي لصفحة إدارة Tuya الخارجية، وموجود بالكامل داخل Home Assistant.

**شو بعمل؟**

- تربط حساب/مشروع Tuya لكل Home Assistant بشكل مستقل.
- تحدد Region وClient ID وClient Secret وUID من الإعدادات بدل ما يكونوا مكتوبين داخل الكود.
- يعرض أجهزة Tuya وحالة Online/Offline.
- بحث وتصنيف للأجهزة.
- عرض Device ID وProduct ID وUUID والتفاصيل المتاحة.
- تغيير الاسم الرئيسي للجهاز على Tuya مباشرة.
- تغيير أسماء مخارج الجهاز مثل `switch_1` و`switch_2` وغيرها إذا Tuya تسمح بذلك.
- Bulk Edit لتعديل عدد كبير من الأجهزة والمخارج بطريقة أسرع.

**الفائدة:** تجهيز أجهزة Tuya وتسميتها أثناء تركيب أي مشروع بصير من نفس Home Assistant بدون PHP منفصل وبدون تعديل أسرار داخل الملفات.

## 3 — Multi-Way & Smart Groups

هذا القسم هو محرك التحكم المتقدم للمفاتيح والجروبات، ومبني على Eshtaya Multi-Way Control.

**شو بعمل؟**

- إنشاء 2-Way و3-Way وMulti-Way برمجيًا بين المفاتيح.
- ربط أكثر من زر/مفتاح مع نفس الحمل الحقيقي.
- إنشاء Smart Groups ذكية للإنارة والستائر والمراوح وغيرها.
- إنشاء Action Groups للمشاهد والسكريبتات والأوتوميشنز.
- Learn Mode للتعرف على المفتاح الحقيقي بسهولة أثناء التركيب.
- فحص سرعة واستجابة المجموعات وحالتها.
- كشف الأجهزة أو الأعضاء غير المتوفرين أو غير المتزامنين.
- أدوات Repair وDiagnostics وTesting.
- Backup / Restore وSnapshots وحماية الإعدادات.

**الفائدة:** بتقدر تبني منطق تحكم احترافي جدًا للبيت بدون تمديدات 2-Way تقليدية، وتدير جروبات كبيرة مع أدوات فحص وصيانة مناسبة للمشاريع الحقيقية.

## 4 — Documentation Center

مركز شرح موجود داخل المنصة نفسها.

**شو بعمل؟**

- يشرح كل أداة ووظيفتها.
- يوضح طريقة الإعداد والاستخدام.
- يعطي تعليمات للهجرة من الإضافات القديمة.
- يوفر الشرح بالعربي والإنجليزي.

**الفائدة:** أي شخص يفتح النظام لاحقًا يقدر يفهم الأدوات وطريقة استخدامها بدون ما يرجع يدور على رسائل أو ملفات خارجية.

## 5 — System Center

هذا القسم يعطي نظرة عامة على صحة المنصة وكل الوحدات الموجودة فيها.

**شو بعمل؟**

- يوضح إذا Entity Control جاهز.
- يوضح إذا Tuya مهيأة أو لا.
- يوضح حالة Multi-Way.
- يفحص إذا ملفي `hidden_entities.yaml` متزامنين.
- يكتشف وجود Eshtaya Entity Manager القديم.
- يكتشف وجود Eshtaya Multi-Way Control القديم.
- يعطي تنبيه وإرشاد للهجرة بدل تشغيل نظامين متضاربين.

**الفائدة:** بدل ما تفحص كل قسم لحاله، بتشوف من مكان واحد إذا المنصة كلها سليمة وجاهزة أو في جزء يحتاج إعداد أو إصلاح.

## الفكرة العامة من Eshtaya Smart Control

الهدف النهائي من المشروع هو أن تصبح **Eshtaya Smart Control مكتبة التحكم الرئيسية لكل أدوات Eshtaya Smart داخل Home Assistant**.

يعني أي أداة جديدة مستقبلًا—إدارة أجهزة، Commissioning، صيانة، مراقبة، Alexa، Tuya، شبكات، مشاريع أو أدوات فنيين—يمكن إضافتها كقسم جديد داخل نفس المنصة بدل إنشاء Integration منفصلة كل مرة.
