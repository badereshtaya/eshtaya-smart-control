<p align="center">
  <img src="custom_components/eshtaya_smart_control/brand/logo.png" alt="Eshtaya Smart Control" width="560">
</p>

<h1 align="center">Eshtaya Smart Control</h1>

<p align="center">
  <strong>A unified professional control, commissioning and administration platform for Home Assistant.</strong>
</p>

<p align="center">
  Entity & Alexa management · Tuya Cloud administration · Multi-Way switching · Smart Groups · Commissioning · Diagnostics · Automatic Migration
</p>

<p align="center">
  <a href="https://github.com/badereshtaya/hacs-eshtaya-smart-control/actions"><img src="https://img.shields.io/github/actions/workflow/status/badereshtaya/hacs-eshtaya-smart-control/validate.yml?label=validation" alt="Validation"></a>
  <a href="https://github.com/badereshtaya/hacs-eshtaya-smart-control/releases"><img src="https://img.shields.io/github/v/release/badereshtaya/hacs-eshtaya-smart-control?label=release" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/HACS-Custom-41BDF5" alt="HACS Custom">
  <img src="https://img.shields.io/badge/UI-Arabic%20%7C%20English-7C3AED" alt="Arabic and English UI">
</p>

> **Current unified release:** `1.2.0`  
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
  - [Migration Center](#6-migration-center)
- [Installation with HACS](#installation-with-hacs)
- [First setup](#first-setup)
- [Automatic migration](#automatic-migration)
- [Tuya Cloud setup](#tuya-cloud-setup)
- [Alexa hidden entities files](#alexa-hidden-entities-files)
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

**Eshtaya Smart Control** is a modular Home Assistant integration intended to become the central administration toolbox for Eshtaya Smart installations.

Instead of installing a separate custom integration or external PHP dashboard for every installation task, Eshtaya Smart Control provides:

- one HACS repository;
- one Home Assistant config entry;
- one sidebar Control Hub;
- one expandable backend domain;
- isolated internal modules for different installer workflows;
- Arabic / English / Auto interface language;
- built-in documentation and migration visibility.

The platform currently combines three major control systems plus administration and migration tooling:

| Module | Main purpose |
|---|---|
| **HomeAssistant Entity Control** | Manage Home Assistant display names and Alexa exposure rules at scale |
| **Tuya Entity Control** | Manage Tuya Cloud devices, main names and supported property custom names from inside Home Assistant |
| **Multi-Way & Smart Groups** | Professional software Multi-Way switching, Smart Groups, Action Groups, commissioning and diagnostics |
| **Documentation Center** | Bilingual in-app operating guidance |
| **System Center** | Platform health, module state, Alexa-file health and migration state |
| **Migration Center** | Safe automatic migration from the previous standalone Eshtaya integrations |

## Design goals

The project is built around the following principles:

- **One platform, many tools.** New Eshtaya Smart tools can be added as modules without creating another sidebar integration.
- **Native Home Assistant administration.** No external PHP dashboard is required for the included management workflows.
- **Professional installer workflow.** Search, batch actions, health information, backups and migration visibility are first-class features.
- **Safe configuration.** Destructive operations are backup-aware and validated before cleanup.
- **Bilingual operation.** Arabic, English and Auto modes are available from the unified shell.
- **Modular backend.** Entity Control, Tuya, Multi-Way and migration logic remain isolated internally.
- **Migration without duplicated engines.** Legacy Multi-Way is stopped before the unified runtime takes control.
- **Credential isolation.** Tuya Client Secret and access tokens stay in the backend.

---

# Control Hub

Installing Eshtaya Smart Control adds one Home Assistant sidebar panel:

**Eshtaya Smart Control**

The sidebar opens a Control Hub instead of a long configuration form. The home page presents the available tools as separate operational cards.

The v1.2 Control Hub includes:

1. **HomeAssistant Entity Control**
2. **Tuya Entity Control**
3. **Multi-Way & Smart Groups**
4. **Documentation Center**
5. **System Center**
6. **Migration Center** inside System Center

The header includes:

- current Eshtaya Smart Control version;
- Arabic / English / Auto language selector;
- refresh action;
- unified navigation.

The home dashboard also shows compact metrics for Home Assistant entities, Alexa-hidden entities, Multi-Way groups and Smart Groups.

When an automatic legacy migration has been performed, a migration banner links directly to the Migration Center.

## Language modes

The unified shell supports:

- `Auto` — follows Home Assistant language;
- `العربية` — Arabic / RTL;
- `English` — English / LTR.

The selected mode is also passed to the embedded Eshtaya tools where supported.

---

# Modules

## 1. HomeAssistant Entity Control

HomeAssistant Entity Control is the entity administration and Alexa exposure module.

It is designed for installations where manually editing hundreds of Home Assistant entities becomes impractical.

### Entity naming

Display names can be changed through Home Assistant's Entity Registry.

The normal rename workflow focuses on safe display-name administration rather than blindly changing entity IDs.

### Alexa exposure modes

Each entity can use:

| Rule | Meaning |
|---|---|
| **Auto** | Let domain/default logic decide |
| **Force Show** | Explicitly expose the entity |
| **Force Hide** | Explicitly exclude the entity |

Effective precedence is:

```text
Force Show
→ Force Hide
→ Domain disabled
→ Automatic entity-category exclusion
→ Automatic keyword exclusion
→ Included
```

### Search and filters

Entity Control supports filtering by:

- text search;
- entity domain;
- Home Assistant Area;
- source integration/platform;
- available/unavailable state;
- Alexa effective state;
- explicit overrides.

### Multi-select batch actions

Large installations can select many entities and apply a rule in one operation:

- Show selected;
- Hide selected;
- Return selected to Auto.

### Orphan rules

Explicit rules whose entities are currently missing are shown as orphan rules instead of being silently removed. This prevents temporary integration outages from destroying configuration.

### Import / export

Portable `alexa_rules.json` backups can contain:

- domain rules;
- per-entity rules;
- excluded entity categories;
- excluded keywords.

The module also keeps a backup before replacing the active rule set during import.

### Dual Alexa hidden files

Entity Control maintains:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

Both are generated from the same rule source and are expected to remain byte-identical.

On a completely fresh installation, the valid empty representation is:

```yaml
[]
```

### Documentation

- [English Entity Control documentation](docs/en/ENTITY_CONTROL.md)
- [الشرح بالعربية](docs/ar/ENTITY_CONTROL.md)

---

## 2. Tuya Entity Control

Tuya Entity Control replaces the former external PHP administration page with a native Home Assistant workflow.

The browser talks only to Home Assistant. Tuya authentication, signing and access-token handling happen in the backend.

### Per-installation configuration

Each Home Assistant installation can configure its own:

- Tuya region/data center;
- custom API endpoint when needed;
- Client ID;
- Client Secret;
- UID.

This makes one HACS repository usable across multiple customers and Tuya projects.

### Connection validation

When complete Tuya credentials are supplied, the setup/reconfigure flow can validate the account before accepting the configuration.

### Device administration

The module can expose information including:

- device name;
- Device ID;
- online/offline state;
- category;
- Product ID;
- UUID and additional device details when available;
- Shadow Properties.

### Search and filters

Supported workflows include:

- device-name search;
- Device-ID search;
- category/product search;
- Online / Offline filtering;
- pagination for larger projects.

### Main device rename

The primary device name can be changed through Tuya OpenAPI. This is a Tuya-side rename rather than only a Home Assistant display label.

### Property / gang custom names

Supported Shadow Properties can expose naming targets such as:

```text
switch_1
switch_2
switch_3
socket_1
control
```

Where Tuya supports `custom_name`, the tool can edit those sub-names directly.

### Bulk editor

The bulk workflow reduces repetitive commissioning work when a project contains many multi-gang Tuya devices.

Backend property loading uses bounded concurrency to avoid uncontrolled API bursts.

### Credential handling

Tuya Client Secret and access tokens are not intended to be returned to the frontend status API or stored in browser local storage.

### Documentation

- [English Tuya documentation](docs/en/TUYA_CONTROL.md)
- [الشرح بالعربية](docs/ar/TUYA_CONTROL.md)

---

## 3. Multi-Way & Smart Groups

This module integrates the mature **Eshtaya Multi-Way Control 3.3.1** runtime into the unified platform.

It is not only a shortcut to the previous UI. The runtime, storage, Home Assistant platforms and reliability logic are embedded into Eshtaya Smart Control.

### Multi-Way engine

Multi-Way creates software-defined 2-way / 3-way / N-way control around a real output.

Example:

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

### Controller behavior

Supported control concepts include:

- Mirror;
- Toggle;
- Momentary On;
- Momentary Off;
- Event;
- Follow Output;
- inversion/reflection;
- source authority and recovery behavior.

### Rapid physical input reliability

The engine preserves ordered physical edges, protects against stale cloud command echoes and performs final reconciliation after rapid changes.

### Performance profiles

| Profile | Goal |
|---|---|
| **Instant** | Lowest perceived wall-switch latency |
| **Balanced** | Fast operation with additional confirmation |
| **Safe** | Stronger verification for slower or unreliable devices |

### Smart Groups

Smart Groups support physical-controller and virtual aggregate groups while retaining domain-aware behavior.

Supported group domains include lights, switches, covers, fans, locks, media players, valves, sensors, binary sensors, buttons, events and notify entities.

### Action Groups

Scenes, Scripts and Automations are supported as stateless Action Groups with parallel/sequential execution behavior.

### Commissioning and maintenance

Installer-focused tools include:

- Learn Mode;
- Area-aware setup;
- templates;
- clone workflows;
- discovery/commissioning assistance;
- health and diagnostics;
- rapid-toggle testing;
- missing-entity repair/remapping;
- backup/restore;
- snapshots and Undo where safe;
- Configuration Lock;
- Home Assistant Group Take Over workflows.

### Native Home Assistant entities

The integrated runtime forwards supported Home Assistant platforms so resulting virtual groups and diagnostic controls remain first-class Home Assistant entities usable from dashboards, scripts, automations and voice systems.

### Documentation

- [English Multi-Way documentation](docs/en/MULTIWAY.md)
- [الشرح بالعربية](docs/ar/MULTIWAY.md)

---

## 4. Documentation Center

Documentation Center keeps installer guidance inside the same platform used for administration.

It covers:

- tool purpose;
- initial setup;
- safe operating workflow;
- automatic migration;
- security;
- architecture.

Repository documentation is maintained in English and Arabic under `/docs`.

---

## 5. System Center

System Center provides a platform-level operational view.

It includes:

- Entity Control availability;
- Tuya configured/not-configured state;
- Multi-Way availability;
- Alexa hidden-file synchronization state;
- automatic migration state;
- Migration Center;
- HACS legacy-cleanup result when available.

Tuya is optional. Entity Control and Multi-Way can operate without a configured Tuya project.

---

## 6. Migration Center

**Migration Center** was added in v1.2.0 to make automatic cutover observable instead of opaque.

The visual timeline contains nine stages:

```text
Detect legacy
→ Create backup
→ Copy configuration
→ Stop legacy engines
→ Start new runtime
→ Validate
→ Remove legacy config entries
→ Reconcile state/ownership
→ Clean legacy HACS repositories
```

Each stage can report:

- Pending;
- Running;
- Completed;
- Failed;
- Rolled Back;
- Skipped.

### Before / after comparison

Migration Center shows safe before/after counters for:

- Entity / Alexa rules;
- Multi-Way groups;
- Smart Groups.

### Rollback visibility

The UI shows:

- migration backup store name;
- whether rollback protection is available;
- whether rollback was used;
- how many legacy config entries were removed after validation.

### HACS cleanup status

The platform records the result of attempting to uninstall/unregister the two legacy repositories through HACS itself.

No raw `custom_components` folder deletion is performed by the migration engine.

### Downloadable Migration Report

Administrators can download a JSON migration report directly from Migration Center.

The report includes:

- Eshtaya Smart Control version;
- migration phase;
- timeline states;
- before/after counters;
- validation result;
- rollback state;
- HACS cleanup result;
- recorded migration errors.

For security, the report intentionally excludes:

- Tuya Client Secret;
- Tuya credentials;
- raw legacy storage payloads;
- raw migration backup contents.

---

# Installation with HACS

Until Eshtaya Smart Control is included in the default HACS store, install it as a custom repository.

1. Open **HACS → Integrations**.
2. Open the menu and select **Custom repositories**.
3. Add:

```text
https://github.com/badereshtaya/hacs-eshtaya-smart-control
```

4. Select type:

```text
Integration
```

5. Install **Eshtaya Smart Control**.
6. Restart Home Assistant.
7. Open **Settings → Devices & services → Add Integration**.
8. Search for **Eshtaya Smart Control**.
9. Complete setup.
10. Open the new sidebar panel.

The integration uses a single config entry.

---

# First setup

Tuya configuration is optional.

On first setup, Eshtaya Smart Control automatically checks whether the previous standalone Eshtaya integrations are present.

Recommended workflow:

```text
Create a full Home Assistant backup
→ Install Eshtaya Smart Control from HACS
→ Restart Home Assistant
→ Add Eshtaya Smart Control
→ Automatic legacy detection/migration runs when required
→ Open System Center / Migration Center
→ Verify migration result and before/after counts
→ Configure Tuya only when required
```

Do **not** manually remove the previous Eshtaya integrations before first setup if you want the automatic migration engine to import their active storage/config-entry state.

A full Home Assistant backup remains recommended even though the integration also creates its own migration backup.

---

# Automatic migration

Eshtaya Smart Control can migrate from:

```text
eshtaya_entity_manager
eshtaya_multiway
```

The migration engine is transactional:

1. Detect legacy config entries and storage.
2. Create an independent backup under:

```text
eshtaya_smart_control.migration_backup
```

3. Copy legacy storage only when the unified destination is not already populated.
4. Disable legacy config entries before the unified Multi-Way runtime starts.
5. Start the new Entity Control / Multi-Way / Smart Group runtime.
6. Validate transferred rule/group counts.
7. If validation fails, automatically re-enable entries disabled by the migration and record the rollback.
8. If validation succeeds, remove the old config entries through Home Assistant.
9. Reconcile Smart Group hidden-member ownership.
10. Register compatibility aliases for old `eshtaya_multiway.*` services where applicable.
11. Attempt HACS cleanup through HACS' repository API.

### Compatibility with migration performed on v1.1

If a system already completed the automatic migration using v1.1.0, upgrading to v1.2.0 hydrates that saved migration record into a completed Migration Center timeline instead of showing false Pending stages.

### Migration documentation

- [English migration guide](docs/en/MIGRATION.md)
- [دليل الهجرة بالعربية](docs/ar/MIGRATION.md)

---

# Tuya Cloud setup

Tuya Entity Control requires a Tuya IoT/OpenAPI project that can access the devices associated with the configured UID.

Configure:

```text
Region
Client ID
Client Secret
UID
```

For Custom region mode, also configure the API endpoint.

## Region note

The OpenAPI region must match the Tuya data center used by the project and linked devices. Correct credentials against the wrong data center can still fail connection validation.

## Changing Tuya configuration later

Use Home Assistant's integration reconfigure flow rather than editing source files.

---

# Alexa hidden entities files

Entity Control uses one internal rule model to generate:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

Both files are intentionally synchronized.

`/config/hidden_entities.yaml` is suitable for local Home Assistant configuration/include usage.

`/config/www/hidden_entities.yaml` can be served through Home Assistant's `/local/` path when another authorized system needs the generated list.

Fresh installations create valid empty YAML as:

```yaml
[]
```

Treat Entity Control storage as the source of truth. Manual edits to generated files can be replaced during regeneration.

---

# Architecture

Eshtaya Smart Control is one Home Assistant custom integration with isolated internal modules.

```text
Eshtaya Smart Control
│
├── Unified Control Hub
│   ├── Home dashboard
│   ├── Documentation Center
│   ├── System Center
│   └── Migration Center
│
├── HomeAssistant Entity Control
│   ├── Entity Registry naming
│   ├── Alexa rules engine
│   ├── import / export
│   ├── batch actions
│   └── hidden_entities.yaml synchronization
│
├── Tuya Entity Control
│   ├── Tuya OpenAPI client
│   ├── HMAC request signing
│   ├── access-token handling
│   ├── per-installation credentials
│   ├── device/cache manager
│   └── admin WebSocket API
│
├── Multi-Way & Smart Groups
│   ├── MultiWayManager
│   ├── Multi-Way storage
│   ├── SmartGroupManager
│   ├── Smart Group storage
│   ├── native Home Assistant platforms
│   ├── Action Groups
│   ├── commissioning / Learn workflows
│   └── diagnostics / health
│
└── Migration subsystem
    ├── transactional legacy migration
    ├── migration backup
    ├── validation / rollback
    ├── legacy service compatibility
    ├── HACS cleanup
    └── Migration Center report API
```

## WebSocket namespaces

Management APIs are namespaced beneath the unified domain.

Examples:

```text
eshtaya_smart_control/overview
eshtaya_smart_control/migration_report
eshtaya_smart_control/entity/...
eshtaya_smart_control/multiway/...
```

### Architecture documentation

- [English architecture](docs/en/ARCHITECTURE.md)
- [البنية التقنية بالعربية](docs/ar/ARCHITECTURE.md)

---

# Security

Eshtaya Smart Control is an administrative integration.

## Home Assistant authentication

- Sidebar management requires a Home Assistant administrator.
- Management WebSocket commands are administrator-only.
- No separate public dashboard password is used.
- No Home Assistant long-lived access token is embedded in the integration.

## Tuya credentials

- Tuya credentials are configured per Home Assistant installation.
- Client Secret remains backend-side.
- Tuya request signing occurs in the backend.
- Access tokens are not stored in browser local storage.

## Migration report security

Downloaded migration reports are intentionally sanitized and do not expose Tuya credentials or raw legacy/backup storage.

## Generated Alexa files

`/config/www/hidden_entities.yaml` lives under Home Assistant's web-served `www` directory. Use that copy only when your architecture intentionally requires external retrieval.

Never commit customer Tuya Client Secrets, Home Assistant tokens or deployment credentials to the repository.

See [SECURITY.md](SECURITY.md).

---

# Troubleshooting

## Eshtaya Smart Control does not appear after HACS installation

Verify:

1. HACS installed the repository as an **Integration**.
2. This directory exists:

```text
/config/custom_components/eshtaya_smart_control/
```

3. Home Assistant was restarted.
4. Review **Settings → System → Logs** for `eshtaya_smart_control` errors.

## Old interface appears after an update

1. Restart Home Assistant.
2. Hard refresh the browser (`Ctrl+F5`).
3. Reload the Home Assistant mobile/tablet webview when applicable.

v1.2 uses a versioned Control Hub frontend module to reduce stale-cache problems.

## Automatic migration fails

Open **System Center → Migration Center**.

Check:

- failed timeline stage;
- recorded error;
- before/after counts;
- rollback state;
- whether legacy config entries were restored.

If cutover failed before final cleanup, the migration engine attempts to re-enable the legacy entries it disabled.

The independent migration backup is kept under:

```text
eshtaya_smart_control.migration_backup
```

## HACS cleanup is skipped

The functional Home Assistant migration can complete even when HACS is not ready during cleanup.

Migration Center may show states such as:

```text
hacs_not_loaded
hacs_api_unavailable
not_registered
removed
```

The integration never compensates by blindly deleting legacy custom-component folders.

## Tuya validation fails

Check:

- Client ID;
- Client Secret;
- UID;
- Tuya project permissions/subscriptions;
- data-center region;
- device/account linkage.

## Tuya device list is empty

Confirm that the configured UID belongs to the account whose devices are linked to the configured Tuya IoT project.

## A Tuya property cannot be renamed

The tool can only edit naming targets actually exposed by Tuya through the relevant Shadow Property/OpenAPI flow.

## Alexa files differ

Open Entity Control/System Center and regenerate synchronization. The stored Entity Control rules remain the source of truth.

## An entity remains hidden after enabling its domain

Check effective precedence:

```text
Force Show
Force Hide
Domain setting
Auto category rule
Auto keyword rule
```

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
│       ├── migration.py
│       ├── migration_center.py
│       ├── legacy_cleanup.py
│       ├── legacy_compat.py
│       ├── entity_control/
│       ├── tuya/
│       ├── multiway/
│       ├── frontend/
│       │   ├── smart-control-panel-v12.js
│       │   ├── tuya-control.js
│       │   ├── entity/
│       │   └── multiway/
│       ├── translations/
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

The repository includes validation workflows covering:

```text
Python syntax
JavaScript syntax
HACS repository structure
Home Assistant / hassfest validation
```

The v1.2.0 Migration Center implementation was verified using the repository's GitHub validation workflow with HACS, hassfest, Python compilation and JavaScript syntax checks.

## Versioning

The unified project was introduced at `1.0.0` and now follows its own version lifecycle independently from the embedded Multi-Way runtime version.

Current release:

```text
1.2.0
```

See [CHANGELOG.md](CHANGELOG.md).

---

# License

Eshtaya Smart Control is licensed under the [MIT License](LICENSE).

---

# شرح الأقسام بالعربي

هذا ملخص سريع للأقسام الرئيسية داخل **Eshtaya Smart Control** وفائدة كل قسم:

## 1 — HomeAssistant Entity Control

**شو بعمل؟**

- تغيير الاسم الظاهر للـEntity من Entity Registry.
- تحديد `Auto / Show / Hide` بالنسبة لـAlexa.
- بحث وفلترة حسب الغرفة والنوع والـIntegration والحالة.
- تعديل عدد كبير من الـEntities مرة واحدة.
- استيراد وتصدير `alexa_rules.json`.
- كشف Orphan Rules.
- إنشاء ومزامنة:
  - `/config/hidden_entities.yaml`
  - `/config/www/hidden_entities.yaml`

**الفائدة:** إدارة مئات أو آلاف الـEntities من مكان واحد بدل التعديل اليدوي Entity وراء Entity.

## 2 — Tuya Entity Control

**شو بعمل؟**

- إعداد حساب/مشروع Tuya لكل Home Assistant بشكل مستقل.
- Region + Client ID + Client Secret + UID من Config Entry.
- Test Connection.
- عرض Online / Offline والأجهزة والتفاصيل.
- تعديل الاسم الرئيسي للجهاز على Tuya.
- تعديل أسماء `switch_1` و`switch_2` و`socket_x` وغيرها عندما تدعمها Tuya.
- Bulk Edit للمشاريع الكبيرة.

**الفائدة:** تجهيز وتسميات Tuya تصير من داخل Home Assistant بدون صفحة PHP خارجية وبدون أسرار مكتوبة داخل الكود.

## 3 — Multi-Way & Smart Groups

**شو بعمل؟**

- 2-Way / 3-Way / N-Way برمجيًا.
- ربط أكثر من Controller بنفس الحمل.
- Smart Groups وAction Groups.
- Learn Mode وCommissioning.
- Health وDiagnostics وTesting.
- Missing Entity Repair.
- Backup / Restore / Snapshots.
- Configuration Lock وTake Over workflows.

**الفائدة:** بناء منطق تحكم احترافي للمشاريع بدون الاعتماد على تمديدات Multi-Way التقليدية، مع أدوات فحص وصيانة مناسبة للتركيب الحقيقي.

## 4 — Documentation Center

**شو بعمل؟**

- شرح الأدوات بالعربي والإنجليزي.
- تعليمات الإعداد والاستخدام والهجرة والأمان.

**الفائدة:** الفني أو المسؤول يقدر يفهم النظام من نفس المنصة بدل الرجوع لصفحات وأدوات خارجية.

## 5 — System Center

**شو بعمل؟**

- يعرض حالة الوحدات.
- حالة إعداد Tuya.
- صحة ملفي Alexa YAML.
- حالة الهجرة التلقائية.
- HACS cleanup status.

**الفائدة:** تشوف صحة المنصة كاملة من مكان واحد.

## 6 — Migration Center

**شو بعمل؟**

- يكتشف `Eshtaya Entity Manager` و`Eshtaya Multi-Way Control` القديمات تلقائيًا.
- يعمل Backup مستقل قبل Cutover.
- ينقل Entity Rules وMulti-Way Groups وSmart Groups.
- يوقف المحركات القديمة قبل تشغيل الجديدة.
- يقارن الأعداد قبل وبعد.
- لا يحذف Config Entries القديمة إلا بعد Validation ناجح.
- إذا فشل الانتقال يعمل Rollback ويعيد تفعيل القديم عندما يكون ذلك ممكنًا.
- يعرض Timeline لكل خطوة.
- يعرض Rollback readiness وHACS cleanup.
- يسمح بتنزيل Migration Report JSON آمن للدعم.

**الفائدة:** تقدر تنزل Eshtaya Smart Control على Home Assistant فيه الإضافات القديمة وتخلي عملية الانتقال تتم بطريقة منظمة ومراقبة بدل النقل اليدوي والخوف من ضياع الجروبات أو تضارب المحركات.

## الفكرة العامة

الهدف هو أن تصبح **Eshtaya Smart Control مكتبة التحكم الرئيسية لكل أدوات Eshtaya Smart داخل Home Assistant**.

أي أدوات مستقبلية مثل Commissioning، صيانة، شبكات، مراقبة، إدارة مشاريع أو أدوات فنيين يمكن إضافتها كأقسام جديدة داخل نفس المنصة بدل إنشاء Integration منفصلة لكل وظيفة.
