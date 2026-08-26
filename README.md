<p align="center">
  <img src="custom_components/eshtaya_smart_control/brand/source_logo.png" alt="Eshtaya Smart Control" width="240">
</p>

<h1 align="center">Eshtaya Smart Control</h1>

<p align="center">
  <strong>Unified Home Assistant administration, commissioning, access-control and smart-control platform.</strong>
</p>

<p align="center">
  Entity & Alexa · Tuya Cloud · Multi-Way · Smart Groups · Template Manager · System Center · Access Control · Bilingual Documentation
</p>

<p align="center">
  <a href="https://github.com/badereshtaya/hacs-eshtaya-smart-control/actions"><img src="https://img.shields.io/github/actions/workflow/status/badereshtaya/hacs-eshtaya-smart-control/validate.yml?label=validation" alt="Validation"></a>
  <a href="https://github.com/badereshtaya/hacs-eshtaya-smart-control/releases"><img src="https://img.shields.io/github/v/release/badereshtaya/hacs-eshtaya-smart-control?label=release" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/HACS-Custom-41BDF5" alt="HACS Custom">
  <img src="https://img.shields.io/badge/UI-Arabic%20%7C%20English-7C3AED" alt="Arabic and English UI">
</p>

> **Current release:** `2.3.1`  
> **Integration domain:** `eshtaya_smart_control`  
> **Repository:** `badereshtaya/hacs-eshtaya-smart-control`  
> **Home Assistant:** `2026.3.0+`  
> **Tuya:** optional; configured only from the Tuya module

---

## What is Eshtaya Smart Control?

**Eshtaya Smart Control** combines the main Eshtaya Home Assistant administration tools into one HACS integration, one sidebar panel, one lifecycle, one permission model and one diagnostic surface.

The current platform includes:

| Module | Purpose |
|---|---|
| **Dashboard** | Health score, metrics, recommendations and module navigation |
| **Entity & Alexa Control** | Entity naming, Alexa exposure rules, bulk tools and generated hidden files |
| **Tuya Control** | Optional Tuya OpenAPI activation, device administration and cloud naming |
| **Multi-Way** | Software-defined 2-way/3-way/N-way control with reliability tooling |
| **Smart Groups / Action Groups** | Domain-aware aggregate control and stateless action orchestration |
| **Template Manager** | Permanent `light`/`fan` entities backed by physical switches with safe legacy migration |
| **System Center** | Diagnostics, repair actions, reports and Migration Center |
| **Access Control** | Eshtaya module RBAC plus supported Home Assistant Core account-role controls |
| **Documentation Center** | The same Arabic/English Markdown guides packaged offline inside Home Assistant |

---

# Version 2.3.1 highlights

## Template Manager navigation/access fix

Version 2.3.0 introduced Template Manager and the backend permissions:

```text
template.view
template.manage
```

but an older frontend navigation guard still used a view map from before the Template Manager existed. This could make the tab visible and then reject the click with:

```text
This role does not have access to that module.
```

Version **2.3.1** synchronizes the canonical frontend view-permission map, role labels, first-allowed-view logic and click guard with the backend permissions.

## Safe migration from the old Template Manager method

2.3.1 supports normal **HACS Update over an existing installation**. You do not need to delete Eshtaya Smart Control and install it again.

The migration can recover old permanent-entity mappings from:

- old `eshtaya_template_manager` config entries;
- `sensor.eshtaya_template_manager`;
- legacy service registration;
- old custom-component files;
- generated YAML/JSON and known package/storage paths.

Recognized generated sources include:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

The safe cutover sequence is:

```text
Detect legacy evidence
→ Recover mappings
→ Capture Entity Registry metadata
→ Create rollback backup
→ Stop/neutralize legacy definitions
→ Release old entity IDs
→ Start unified permanent entities
→ Verify exact IDs and ownership
→ Final cleanup
```

### `restart_required` is a safety checkpoint

Some YAML/custom-component legacy installations cannot release every old entity from Home Assistant memory immediately.

If an old `light.*`, `fan.*` or `sensor.eshtaya_template_manager` ID is still occupied, 2.3.1 **does not create a duplicate**. The new entities remain deferred and Migration Center reports:

```text
restart_required
```

Perform one Home Assistant restart. The next startup completes the exact-ID takeover after the removed legacy definitions are no longer loaded.

This is designed to prevent:

```text
light.example_2
fan.example_2
sensor.eshtaya_template_manager_2
```

## Migration lock

While a legacy Template Manager migration is incomplete:

- the UI disables Create/Edit/Delete/Relink;
- the Python backend rejects the same mutations even if called directly through WebSocket/services.

## Documentation now has one source of truth

The human-edited documentation lives under:

```text
docs/ar
docs/en
```

The **same Git blobs** are packaged under:

```text
custom_components/eshtaya_smart_control/docs/ar
custom_components/eshtaya_smart_control/docs/en
```

The in-app Documentation Center reads those packaged Markdown files directly. CI performs byte-for-byte `diff` checks, so a release fails if repository documentation and in-app documentation diverge.

## Frontend cache busting

The sidebar asset is versioned with the integration release:

```text
smart-control-panel-v23.js?v=2.3.1
```

After the HACS update and Home Assistant restart, the corrected frontend is requested instead of the cached 2.3.0 module.

---

# Installation

## HACS custom repository

1. Open **HACS → Integrations**.
2. Open **Custom repositories**.
3. Add:

```text
https://github.com/badereshtaya/hacs-eshtaya-smart-control
```

4. Select **Integration**.
5. Install **Eshtaya Smart Control**.
6. Restart Home Assistant.
7. Open **Settings → Devices & services → Add Integration**.
8. Search for **Eshtaya Smart Control** and add it.

Tuya credentials are not required during initial setup.

---

# Updating an existing installation

Use the normal update path:

```text
HACS
→ Eshtaya Smart Control
→ Update
→ Restart Home Assistant
→ Open Eshtaya Smart Control
```

**Do not remove the unified config entry simply to update.** Migration state and old integration evidence are intentionally inspected during startup.

If Template Manager reports **Restart Required**, perform one additional Home Assistant restart. Do not remove/reinstall the integration to force the migration.

---

# Entity & Alexa Control

The module provides:

- Home Assistant Entity Registry display-name editing;
- Alexa Automatic / Force Show / Force Hide rules;
- domain, device-class/category and keyword policies;
- search/filtering and bulk administration;
- orphan-rule cleanup;
- import/export and repair workflows;
- synchronized generated files:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

Detailed guides:

- [English: Entity & Alexa Control](docs/en/ENTITY_CONTROL.md)
- [العربية: إدارة الكيانات وAlexa](docs/ar/ENTITY_CONTROL.md)

---

# Tuya Control

Tuya is optional and activated from its module only.

The backend supports:

- region/data-center selection;
- test-before-activate;
- credential-safe storage;
- device search/filtering and pagination;
- device details;
- main-device naming;
- supported Shadow Property custom names;
- bounded bulk operations;
- backend request timeout/cache/refresh locking.

Detailed guides:

- [English: Tuya Control](docs/en/TUYA_CONTROL.md)
- [العربية: إدارة تويا](docs/ar/TUYA_CONTROL.md)

---

# Multi-Way

Multi-Way provides software-defined multi-point control around one authoritative physical output.

The engine includes:

- Mirror / Toggle / Momentary / Event / Follow-oriented modes;
- rapid physical-input handling;
- cloud echo protection;
- source/output confirmation;
- bounded retries;
- startup protection;
- health and latency data;
- activity history;
- test and repair tooling.

Detailed guides:

- [English: Multi-Way](docs/en/MULTIWAY.md)
- [العربية: Multi-Way](docs/ar/MULTIWAY.md)

---

# Smart Groups and Action Groups

Smart Groups provide domain-aware grouping for supported Home Assistant entity types instead of flattening every device into a generic switch.

Action Groups represent stateless operations such as scenes, scripts, automations and buttons with parallel/sequential execution and failure-policy controls.

Detailed guides:

- [English: Smart Groups](docs/en/SMART_GROUPS.md)
- [العربية: المجموعات الذكية](docs/ar/SMART_GROUPS.md)

---

# Template Manager

Template Manager creates stable permanent Home Assistant entities backed by physical switches:

```text
switch.living_main_light
        ↓
light.living_main_light
```

The permanent entity can keep the same ID while the physical source is later replaced/relinked.

The module provides:

- **Available** — create new Light/Fan wrappers;
- **Managed** — inspect/edit mappings;
- **Missing** — recover a source that disappeared;
- source replacement/relink;
- live source-state tracking;
- startup-safe source detection;
- automatic legacy migration and rollback backup;
- compatibility services/sensor after successful cutover.

Detailed guides:

- [English: Template Manager](docs/en/TEMPLATE_MANAGER.md)
- [العربية: إدارة الكيانات الدائمة](docs/ar/TEMPLATE_MANAGER.md)

---

# Access Control

There are two distinct layers.

## Eshtaya module permissions

Current module permissions include:

```text
dashboard.view
entity.view / entity.manage
tuya.view / tuya.control / tuya.configure
multi.view / multi.control / multi.manage
template.view / template.manage
docs.view
system.view / system.actions / system.reports
access.manage
```

Built-in roles include No Access, Viewer, Operator, Technician and Platform Manager, with custom roles and per-user Allow/Deny overrides.

## Home Assistant Core account access

Where Home Assistant exposes supported account controls, Access Control can manage native account-level concepts such as Administrator, User and Read Only.

Eshtaya module RBAC is **not** presented as a replacement for Home Assistant Core authorization.

Detailed guides:

- [English: Access Control](docs/en/ACCESS_CONTROL.md)
- [العربية: الصلاحيات](docs/ar/ACCESS_CONTROL.md)

---

# System Center

System Center contains:

- health score;
- sanitized platform status;
- repair actions;
- Alexa file health;
- migration timeline/state;
- recommendations;
- System Report;
- Migration Report / rollback visibility.

Detailed guides:

- [English: System Center](docs/en/SYSTEM_CENTER.md)
- [العربية: مركز النظام](docs/ar/SYSTEM_CENTER.md)

---

# Documentation

The repository and in-app Documentation Center contain the same 14 guides in both languages.

## English

1. [Getting Started](docs/en/GETTING_STARTED.md)
2. [Dashboard](docs/en/DASHBOARD.md)
3. [Entity & Alexa Control](docs/en/ENTITY_CONTROL.md)
4. [Tuya Control](docs/en/TUYA_CONTROL.md)
5. [Multi-Way](docs/en/MULTIWAY.md)
6. [Smart Groups](docs/en/SMART_GROUPS.md)
7. [Commissioning](docs/en/COMMISSIONING.md)
8. [System Center](docs/en/SYSTEM_CENTER.md)
9. [Access Control](docs/en/ACCESS_CONTROL.md)
10. [Migration](docs/en/MIGRATION.md)
11. [Architecture](docs/en/ARCHITECTURE.md)
12. [Security and Backup](docs/en/SECURITY_AND_BACKUP.md)
13. [Troubleshooting](docs/en/TROUBLESHOOTING.md)
14. [Template Manager](docs/en/TEMPLATE_MANAGER.md)

## العربية

1. [البدء والتثبيت](docs/ar/GETTING_STARTED.md)
2. [لوحة التحكم](docs/ar/DASHBOARD.md)
3. [إدارة الكيانات وAlexa](docs/ar/ENTITY_CONTROL.md)
4. [إدارة تويا](docs/ar/TUYA_CONTROL.md)
5. [Multi-Way](docs/ar/MULTIWAY.md)
6. [المجموعات الذكية](docs/ar/SMART_GROUPS.md)
7. [التجهيز والتسليم](docs/ar/COMMISSIONING.md)
8. [مركز النظام](docs/ar/SYSTEM_CENTER.md)
9. [الصلاحيات](docs/ar/ACCESS_CONTROL.md)
10. [الهجرة](docs/ar/MIGRATION.md)
11. [البنية التقنية](docs/ar/ARCHITECTURE.md)
12. [الأمان والنسخ الاحتياطية](docs/ar/SECURITY_AND_BACKUP.md)
13. [استكشاف المشاكل](docs/ar/TROUBLESHOOTING.md)
14. [إدارة الكيانات الدائمة](docs/ar/TEMPLATE_MANAGER.md)

---

# Validation and release quality

Every pull request/release validates:

- HACS integration structure;
- Home Assistant Hassfest;
- Python compilation;
- JavaScript syntax;
- byte-identical repository/in-app documentation;
- complete 14-guide Arabic/English documentation sets;
- verified release archive packaging.

Release history is documented in [CHANGELOG.md](CHANGELOG.md).

---

# Security

Do not publish:

- Tuya Client Secret;
- Tuya access/access tokens;
- private Home Assistant tokens;
- raw private migration backups.

See:

- [Security and Backup](docs/en/SECURITY_AND_BACKUP.md)
- [الأمان والنسخ الاحتياطية](docs/ar/SECURITY_AND_BACKUP.md)
- [SECURITY.md](SECURITY.md)

---

# License

MIT — see [LICENSE](LICENSE).
