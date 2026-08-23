<p align="center">
  <img src="custom_components/eshtaya_smart_control/brand/source_logo.png" alt="Eshtaya Smart Control" width="240">
</p>

<h1 align="center">Eshtaya Smart Control</h1>

<p align="center">
  <strong>A professional Home Assistant administration, commissioning and smart-control platform.</strong>
</p>

<p align="center">
  Entity & Alexa Control · Optional Tuya Cloud Control · Multi-Way · Smart Groups · Action Groups · Commissioning · Diagnostics · Migration · Smart Recommendations
</p>

<p align="center">
  <a href="https://github.com/badereshtaya/hacs-eshtaya-smart-control/actions"><img src="https://img.shields.io/github/actions/workflow/status/badereshtaya/hacs-eshtaya-smart-control/validate.yml?label=validation" alt="Validation"></a>
  <a href="https://github.com/badereshtaya/hacs-eshtaya-smart-control/releases"><img src="https://img.shields.io/github/v/release/badereshtaya/hacs-eshtaya-smart-control?label=release" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/HACS-Custom-41BDF5" alt="HACS Custom">
  <img src="https://img.shields.io/badge/UI-Arabic%20%7C%20English-7C3AED" alt="Arabic and English UI">
</p>

> **Current release:** `2.0.0`  
> **Integration domain:** `eshtaya_smart_control`  
> **Repository:** `badereshtaya/hacs-eshtaya-smart-control`  
> **Access:** Home Assistant administrators  
> **Tuya:** Optional; configured only inside the Tuya dashboard, never during first installation

---

## Overview

**Eshtaya Smart Control** is a modular Home Assistant integration built to act as the central installer and administration platform for Eshtaya Smart projects.

Version 2.0.0 is a major redesign. The objective is not to place unrelated tools in one menu; it is to provide one coherent operating environment with a unified language system, health model, support reports, migration engine, shared visual identity and specialized modules that can evolve independently.

The platform currently provides six major areas:

| Area | Purpose |
|---|---|
| **Dashboard** | Health, key metrics, intelligent recommendations and safe quick actions |
| **Entity & Alexa Control** | Entity naming, Alexa exposure policy, bulk administration and generated hidden files |
| **Tuya Control** | Optional Tuya OpenAPI activation, device administration, naming and bulk commissioning |
| **Multi-Way & Smart Groups** | Software Multi-Way switching, native-domain groups, Action Groups and reliability tooling |
| **Documentation Center** | Searchable Arabic/English operating documentation inside Home Assistant |
| **System Center** | Platform diagnostics, sanitized reports, file health, migration state and recovery visibility |

The architecture is intentionally expandable. Future Eshtaya Smart tools can be added as modules under the same platform rather than creating another standalone integration and another sidebar panel.

---

## What changed in 2.0.0

### Zero-friction first installation

The first Home Assistant config flow no longer asks for Tuya credentials or any optional cloud configuration.

Installation is now:

```text
Install from HACS
→ Restart Home Assistant
→ Add Eshtaya Smart Control
→ Confirm
→ Open the Dashboard
```

Tuya is activated later only when the user opens **Tuya Control**.

### Tuya on-demand activation

If Tuya is not configured, its dashboard becomes an activation wizard. It explains the required project data, tests the connection and saves the configuration only after successful validation.

After activation, the same section provides **Edit Tuya account** and **Deactivate Tuya** actions. Reinstalling the integration is not required.

### New platform identity

Version 2.0.0 uses the new Eshtaya Smart Control logo across the integration branding and dashboard shell.

### Full dashboard redesign

The unified Dashboard now includes:

- system health score;
- live module metrics;
- intelligent operational recommendations;
- module status cards;
- safe quick actions;
- direct navigation to the correct repair/management tool;
- responsive desktop, tablet and mobile layouts;
- a consistent icon system.

### Smart operational recommendations

The backend turns known system conditions into structured recommendations. Examples include:

- Alexa output files are out of sync;
- a high number of Home Assistant entities are unavailable;
- Multi-Way groups are degraded;
- Smart Groups are degraded;
- a migration needs attention;
- Tuya is inactive but optional;
- the checked system is healthy.

These are deterministic local recommendations. They do not upload home state to an external AI service.

### System reports and quick actions

System Center can now provide a sanitized support report and execute guarded actions such as:

- repair Alexa files;
- synchronize Multi-Way/Smart Groups;
- refresh Tuya devices;
- refresh the complete managed platform state.

Operations that may command physical devices require explicit confirmation in the UI.

### Complete bilingual documentation

The repository and in-app Documentation Center now provide dedicated guides for getting started, Dashboard, Entity Control, Tuya, Multi-Way, Smart Groups, commissioning, System Center, migration, architecture, security/backups and troubleshooting.

---

# Installation

## HACS custom repository

Until the repository is included in the default HACS store:

1. Open **HACS → Integrations**.
2. Open **Custom repositories**.
3. Add:

```text
https://github.com/badereshtaya/hacs-eshtaya-smart-control
```

4. Select **Integration**.
5. Install **Eshtaya Smart Control**.
6. Restart Home Assistant.

## Add the Home Assistant integration

After restart:

1. Open **Settings → Devices & services**.
2. Choose **Add Integration**.
3. Search for **Eshtaya Smart Control**.
4. Confirm the setup form.

That is the complete first setup. No Tuya Client ID, Client Secret, UID or endpoint is requested.

The integration registers one administrator-only sidebar panel named **Eshtaya Smart Control**.

---

# Dashboard

The Dashboard is the operational home of the platform.

It provides:

- current platform version;
- Home Assistant version;
- health score;
- total entity information;
- Alexa exposure information;
- Multi-Way and Smart Group counts;
- Tuya activation state;
- recommendations;
- quick repair/refresh actions;
- links into every specialized module.

The visual design is full-width and responsive and uses the official Eshtaya Smart Control identity.

Detailed guide:

- [Dashboard documentation](docs/en/DASHBOARD.md)
- [شرح لوحة التحكم بالعربية](docs/ar/DASHBOARD.md)

---

# Entity & Alexa Control

Entity & Alexa Control is designed for installations where normal one-entity-at-a-time administration becomes inefficient.

## Entity naming

The module edits the Home Assistant Entity Registry display name rather than maintaining a separate private naming database.

This provides:

- safe display-name editing;
- reset to the source/default name;
- no long-lived Home Assistant token;
- compatibility with normal Home Assistant entity administration.

Normal rename operations intentionally do not blindly change the entity ID.

## Alexa exposure model

Each entity can use:

- **Automatic** — domain/category/keyword policy decides;
- **Force Show** — explicitly keep the entity available;
- **Force Hide** — explicitly hide the entity.

Effective precedence is:

```text
Force Show
→ Force Hide
→ Domain rule
→ Automatic entity-category rule
→ Automatic keyword rule
→ Included
```

This makes broad rules practical without losing the ability to create precise exceptions.

## Domain and automatic rules

The module supports:

- whole-domain policy;
- excluded entity categories;
- excluded keywords;
- explicit entity overrides;
- orphan-rule identification;
- search/filtering by domain, area, integration/platform, availability and effective Alexa state.

## Bulk administration

Large result sets can be selected and modified together, including returning entities to Automatic behavior.

## Generated Alexa files

The authoritative rule model generates and synchronizes:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

The two managed outputs are intended to remain byte-identical. File health uses synchronization/hash information instead of merely checking that both files exist.

Detailed guide:

- [Entity & Alexa Control](docs/en/ENTITY_CONTROL.md)
- [إدارة الكيانات وAlexa](docs/ar/ENTITY_CONTROL.md)

---

# Tuya Control

Tuya Control is an **optional module**.

## Activation inside the module

Opening Tuya Control before configuration displays the activation experience. The user configures:

- Tuya data center/region;
- custom API endpoint when required;
- Client ID;
- Client Secret;
- UID.

The connection is tested before activation.

The Client Secret remains backend-only and is not returned to the dashboard after it is stored.

## Editing configuration later

After activation, the account bar offers configuration editing. Leaving the Client Secret empty while editing preserves the existing secret when supported by the backend workflow.

The module can also be deactivated without removing Eshtaya Smart Control itself.

## Device administration

The module supports:

- device list by configured UID;
- online/offline status;
- device/category/product search;
- category filtering;
- pagination;
- device details;
- UUID/Product ID/network information when Tuya returns it;
- main device rename;
- supported Shadow Property custom-name editing;
- bulk name/property editing.

Supported property naming targets are discovered from the actual device response, for example:

```text
switch_1
switch_2
socket_1
control
```

The tool does not invent unsupported Tuya DPs.

Detailed guide:

- [Tuya Control](docs/en/TUYA_CONTROL.md)
- [التحكم بتويا](docs/ar/TUYA_CONTROL.md)

---

# Multi-Way Control

The integrated Multi-Way engine provides software-defined 2-way, 3-way and N-way control around a physical output.

A group can have:

- one authoritative physical output;
- multiple physical/virtual controllers;
- a generated virtual Home Assistant entity;
- configurable behavior and reliability policy.

Controller modes include Mirror, Toggle, Momentary and Event-oriented behavior, with response profiles designed for local and cloud-backed integrations.

## Reliability tooling

The engine includes mechanisms for:

- ordered rapid physical input;
- cloud command-echo suppression;
- output confirmation;
- bounded retries;
- final source reconciliation;
- startup protection;
- health state;
- latency/quality information;
- activity history;
- missing-entity repair.

Detailed guide:

- [Multi-Way](docs/en/MULTIWAY.md)
- [التحكم متعدد النقاط](docs/ar/MULTIWAY.md)

---

# Smart Groups & Action Groups

Smart Groups add higher-level, domain-aware grouping instead of treating every device as a generic binary switch.

The integrated engine supports native concepts across supported Home Assistant domains including lights, switches, fans, covers, locks, media players, valves, sensors, binary sensors, buttons, events and notifications.

Groups may be:

- virtual aggregate groups;
- physical-controller groups;
- bidirectional when appropriate;
- read-only aggregate groups for sensor-style domains.

## Action Groups

Scenes, scripts and automations are represented as actions rather than fake persistent switches.

Action Groups support:

- parallel or sequential execution;
- failure policy;
- automation-condition behavior;
- cooldown/guard behavior;
- activity and diagnostics.

Detailed guide:

- [Smart Groups](docs/en/SMART_GROUPS.md)
- [المجموعات الذكية](docs/ar/SMART_GROUPS.md)

---

# Commissioning

Eshtaya Smart Control includes installer-oriented commissioning workflows for real projects rather than only configuration forms.

Tools include concepts such as:

- Learn Mode;
- area-aware setup;
- templates;
- cloning;
- readiness tests;
- rapid-input testing;
- member validation;
- missing-entity repair;
- health and latency review;
- configuration lock for handover.

Recommended installer workflow is documented separately:

- [Commissioning](docs/en/COMMISSIONING.md)
- [التجهيز والتسليم](docs/ar/COMMISSIONING.md)

---

# System Center

System Center is the administration/diagnostics layer above the individual engines.

It provides:

- health score;
- platform/Home Assistant versions;
- module state;
- Entity/Alexa file health;
- unavailable-entity indicators;
- Multi-Way summary;
- Smart Group summary;
- Tuya safe status;
- smart recommendations;
- quick actions;
- System Report download;
- Migration Center.

## Sanitized support report

The System Report intentionally excludes:

- Tuya Client Secret;
- Tuya access tokens;
- raw migration backup payloads;
- raw legacy storage contents.

It is intended to be safe enough for normal support workflows while still exposing operational state.

Detailed guide:

- [System Center](docs/en/SYSTEM_CENTER.md)
- [مركز النظام](docs/ar/SYSTEM_CENTER.md)

---

# Automatic legacy migration

The platform supports migration from:

- `eshtaya_entity_manager`
- `eshtaya_multiway`

The process is transactional and observable:

```text
Detect
→ Backup
→ Copy
→ Stop legacy engines
→ Start unified runtime
→ Validate counts/state
→ Remove legacy config entries
→ Reconcile ownership
→ HACS cleanup attempt
```

The independent backup store is:

```text
eshtaya_smart_control.migration_backup
```

Legacy entries are removed only after successful validation. If the cutover fails before final cleanup, entries disabled by the migration are re-enabled and the error is recorded.

Migration Center displays the timeline, expected/actual counts, rollback status and HACS cleanup state and can download a sanitized Migration Report.

Detailed guide:

- [Migration](docs/en/MIGRATION.md)
- [الهجرة التلقائية](docs/ar/MIGRATION.md)

---

# Documentation Center

Documentation is available in two layers:

1. **In-app Documentation Center** — searchable and language-aware inside the sidebar platform.
2. **Repository documentation** — detailed Markdown guides for installation, engineering and support reference.

## English documentation

- [Getting started](docs/en/GETTING_STARTED.md)
- [Dashboard](docs/en/DASHBOARD.md)
- [Entity & Alexa Control](docs/en/ENTITY_CONTROL.md)
- [Tuya Control](docs/en/TUYA_CONTROL.md)
- [Multi-Way](docs/en/MULTIWAY.md)
- [Smart Groups](docs/en/SMART_GROUPS.md)
- [Commissioning](docs/en/COMMISSIONING.md)
- [System Center](docs/en/SYSTEM_CENTER.md)
- [Migration](docs/en/MIGRATION.md)
- [Architecture](docs/en/ARCHITECTURE.md)
- [Security and backup](docs/en/SECURITY_AND_BACKUP.md)
- [Troubleshooting](docs/en/TROUBLESHOOTING.md)

## التوثيق العربي

- [البدء والاستخدام الأول](docs/ar/GETTING_STARTED.md)
- [لوحة التحكم](docs/ar/DASHBOARD.md)
- [إدارة الكيانات وAlexa](docs/ar/ENTITY_CONTROL.md)
- [التحكم بتويا](docs/ar/TUYA_CONTROL.md)
- [التحكم متعدد النقاط](docs/ar/MULTIWAY.md)
- [المجموعات الذكية](docs/ar/SMART_GROUPS.md)
- [التجهيز والتسليم](docs/ar/COMMISSIONING.md)
- [مركز النظام](docs/ar/SYSTEM_CENTER.md)
- [الهجرة التلقائية](docs/ar/MIGRATION.md)
- [البنية التقنية](docs/ar/ARCHITECTURE.md)
- [الأمان والنسخ الاحتياطية](docs/ar/SECURITY_AND_BACKUP.md)
- [استكشاف المشاكل](docs/ar/TROUBLESHOOTING.md)

---

# Language and localization

The unified interface supports Auto, Arabic and English.

When Arabic is selected:

- the shell uses RTL;
- navigation and module titles are Arabic;
- System Center and Migration Center statuses are translated;
- recommendations are translated from structured IDs rather than exposing backend English strings;
- Entity Control receives the Arabic preference;
- Tuya Control uses its Arabic dictionary;
- Multi-Way/Smart Groups use their Arabic dictionaries;
- Documentation Center loads the Arabic documentation set.

Technical identifiers such as entity IDs, service names, Tuya DP codes, JSON/YAML field names and product names remain literal where translating them would make the configuration incorrect.

---

# Security model

Eshtaya Smart Control is an administrative integration.

Key principles:

- administrator-only main panel;
- administrator-only management WebSocket commands;
- no separate public PHP administration page;
- no Home Assistant long-lived token embedded in frontend code;
- Tuya request signing in the backend;
- Tuya Client Secret not returned in normal status responses;
- access tokens not stored in browser local storage;
- migration backups never exposed raw through support reports;
- no manual deletion of old HACS component folders during migration.

Detailed guide:

- [Security and backup](docs/en/SECURITY_AND_BACKUP.md)
- [الأمان والنسخ الاحتياطية](docs/ar/SECURITY_AND_BACKUP.md)

---

# Architecture

The platform is one Home Assistant custom integration with internal module boundaries:

```text
eshtaya_smart_control
│
├── Core / System
│   ├── overview & health
│   ├── recommendations
│   ├── reports
│   ├── quick actions
│   └── migration coordination
│
├── Entity Control
│   ├── Entity Registry administration
│   ├── Alexa rules
│   └── generated file synchronization
│
├── Tuya Control
│   ├── optional activation
│   ├── signed OpenAPI client
│   ├── device/cache manager
│   └── admin WebSocket API
│
├── Multi-Way
│   ├── storage
│   ├── runtime manager
│   ├── virtual entities
│   └── reliability/health
│
├── Smart Groups
│   ├── domain-aware grouping
│   ├── Action Groups
│   ├── commissioning
│   └── repair/diagnostics
│
└── Unified frontend
    ├── Dashboard
    ├── Entity & Alexa Control
    ├── Tuya Control
    ├── Multi-Way & Smart Groups
    ├── Documentation Center
    └── System / Migration Center
```

Detailed guide:

- [Architecture](docs/en/ARCHITECTURE.md)
- [البنية التقنية](docs/ar/ARCHITECTURE.md)

---

# Validation and packaging

The repository includes CI intended to validate:

- HACS repository requirements;
- Home Assistant hassfest checks;
- Python compilation;
- JavaScript syntax;
- verified ZIP packaging after validation succeeds.

A CI pass verifies structure and static compatibility. Real-device and Home Assistant runtime testing is still important before production rollout, especially for migrations and physical-control groups.

---

# Troubleshooting

For detailed diagnosis, use:

- [English troubleshooting guide](docs/en/TROUBLESHOOTING.md)
- [دليل حل المشاكل بالعربية](docs/ar/TROUBLESHOOTING.md)

Start with System Center rather than deleting files or integrations manually.

---

# License

Licensed under the [MIT License](LICENSE).

---

# ملخص الأقسام بالعربي

## الرئيسية

تعطيك نظرة سريعة على صحة النظام، أعداد الكيانات والمجموعات، حالة Tuya، التوصيات الذكية والإجراءات السريعة. فائدتها إنك تعرف وين المشكلة أو شو يحتاج متابعة قبل ما تدخل بالتفاصيل.

## إدارة الكيانات وAlexa

لإدارة أسماء كيانات Home Assistant وقواعد ظهورها في Alexa بشكل فردي أو جماعي، مع توليد ومزامنة ملفات `hidden_entities.yaml`. فائدتها إدارة مئات الكيانات بطريقة منظمة بدل التعديل اليدوي واحدًا واحدًا.

## التحكم بتويا

قسم اختياري. لا يطلب أي معلومات وقت تثبيت الإضافة. أول مرة تفتحه فقط يعطيك شاشة تفعيل حساب/مشروع Tuya، وبعدها تستخدمه لإدارة الأجهزة، الأسماء، المخارج والتعديل الجماعي. ويمكن تعديل بيانات الحساب لاحقًا من نفس القسم.

## التحكم متعدد النقاط

لإنشاء تحكم برمجي 2-Way و3-Way وعدد أكبر من نقاط التحكم حول حمل فعلي، مع فحص الصحة والاستجابة والمزامنة والإصلاح.

## المجموعات الذكية ومجموعات الإجراءات

لجمع كيانات Home Assistant بطريقة واعية لنوع الجهاز، وإنشاء مجموعات تحكم فعلية أو افتراضية، وتشغيل Scenes/Scripts/Automations كمجموعات إجراءات مع سياسات تنفيذ وفشل واضحة.

## أدوات التجهيز والتسليم

تجمع Learn Mode والاختبارات والقوالب والإصلاح وفحص الجودة والـLatency وقفل الإعدادات، حتى تكون الأداة مناسبة للشغل الميداني وتسليم مشاريع حقيقية.

## مركز التوثيق

مكتبة شرح كاملة داخل Home Assistant بالعربي والإنجليزي. كل قسم له شرح للإعداد، الاستخدام، الحالات الخاصة، الأمان واستكشاف المشاكل.

## مركز النظام

يجمع صحة المنصة، التوصيات، ملفات Alexa، التقارير، الإجراءات السريعة، حالة الوحدات ومركز الهجرة. فائدته إنه يكون مركز التشخيص والإدارة العامة بدل فتح كل أداة لمعرفة وضعها.

## مركز الهجرة

ينقل إعدادات Eshtaya Entity Manager وEshtaya Multi-Way القديمة تلقائيًا وبطريقة آمنة: نسخة احتياطية أولًا، إيقاف القديم، تشغيل الجديد، تحقق قبل الحذف، Rollback إذا فشل، ثم تنظيف القديم بعد النجاح.

## الفكرة النهائية

الهدف أن تكون **Eshtaya Smart Control** المنصة الرئيسية لكل أدوات Eshtaya Smart داخل Home Assistant: إدارة، تجهيز، صيانة، مراقبة، تشخيص وهجرة من مكان واحد، مع بنية قابلة لإضافة وحدات جديدة مستقبلًا بدون تشتيت النظام على Integrations منفصلة.
