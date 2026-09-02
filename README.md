<p align="center">
  <img src="custom_components/eshtaya_smart_control/brand/source_logo.png" alt="Eshtaya Smart Control" width="240">
</p>

<h1 align="center">Eshtaya Smart Control</h1>

<p align="center"><strong>Unified Home Assistant administration, commissioning and smart-control platform.</strong></p>

<p align="center">
  Entity & Alexa · Tuya · Multi-Way · Smart Groups · Template Manager · System Center · Access Control · Bilingual Documentation
</p>

<p align="center">
  <a href="https://github.com/badereshtaya/hacs-eshtaya-smart-control/actions"><img src="https://img.shields.io/github/actions/workflow/status/badereshtaya/hacs-eshtaya-smart-control/validate.yml?label=validation" alt="Validation"></a>
  <a href="https://github.com/badereshtaya/hacs-eshtaya-smart-control/releases"><img src="https://img.shields.io/github/v/release/badereshtaya/hacs-eshtaya-smart-control?label=release" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
</p>

> **Current development release:** `2.4.0`  
> **Integration domain:** `eshtaya_smart_control`  
> **Repository:** `badereshtaya/hacs-eshtaya-smart-control`  
> **Tuya:** optional; official Home Assistant Tuya is treated as an after-dependency for startup ordering

---

# What is Eshtaya Smart Control?

Eshtaya Smart Control combines the Eshtaya Home Assistant tools into one HACS integration, one sidebar application, one lifecycle, one permission model and one diagnostic surface.

| Module | Purpose |
|---|---|
| Dashboard | Health, metrics, recommendations and navigation |
| Entity & Alexa Control | Entity administration and Alexa exposure policy |
| Tuya Control | Optional Tuya OpenAPI administration |
| Multi-Way | Reliable software-defined 2-way/3-way/N-way control |
| Smart Groups / Action Groups | Domain-aware groups and action orchestration |
| Template Manager | Permanent Light/Fan wrappers over physical switches |
| System Center | Startup state, diagnostics, reports and migration history |
| Access Control | Eshtaya module RBAC and supported HA account controls |
| Documentation Center | Offline Arabic/English copies of the GitHub Markdown guides |

---

# Version 2.4.0 — Startup Barrier & Migration Controls

## Fix: false `Multi-way output entity is missing` after restart

Earlier releases used a fixed Multi-Way `startup_delay` counted from the moment Eshtaya loaded. A cloud integration such as official Tuya could still be restoring when that timer expired. If a referenced output such as:

```text
light.updown
```

had not entered Home Assistant's state machine yet, Eshtaya could temporarily classify it as missing and create a Repair issue even though Tuya created it moments later.

Version **2.4.0** removes that fixed-delay decision from the unified runtime and introduces a layered startup barrier.

### Layer 1 — Home Assistant dependency ordering

`manifest.json` contains:

```json
"after_dependencies": ["tuya"]
```

When official Tuya is configured, Home Assistant schedules Eshtaya after that integration.

### Layer 2 — Home Assistant startup-complete barrier

Multi-Way listeners may be prepared during setup, but the engine remains protected until Home Assistant reaches its startup-complete lifecycle event.

During this phase:

```text
ready = false
health = recovering / starting
missing-output repairs = suppressed
physical startup reconciliation = deferred
```

### Layer 3 — referenced integration readiness

For every configured Multi-Way output/controller/fallback, Eshtaya checks the Entity Registry. If a missing state belongs to a Config Entry that is still setting up, retrying or unloading, the entity is treated as **still loading**, not missing.

### Layer 4 — settle window

After referenced providers stop loading, Eshtaya waits a configurable quiet settle period before becoming ready. Default:

```text
15 seconds
```

### Layer 5 — Repair grace + repeated confirmation

Even after startup protection finishes, one absent observation cannot create a Repair issue.

Defaults:

```text
repair grace:          90 seconds
required confirmations: 3
```

Only an entity that stays absent after the startup barrier, remains absent through the grace period, and fails repeated checks can generate `missing_output` / `missing_controller`.

Persisted false missing Repair issues are cleared when a new protected startup begins and are recreated later only if the absence is genuinely confirmed.

---

# Configure — Startup & Migration Settings

Open:

```text
Settings
→ Devices & services
→ Eshtaya Smart Control
→ Configure
```

The options flow reloads the integration automatically after saving.

## Startup safety

| Setting | Default | Meaning |
|---|---:|---|
| Wait for Home Assistant startup | On | Do not activate Multi-Way repair/reconciliation before HA startup completes |
| Wait for referenced integrations | On | Wait while the Config Entries owning referenced entities are still restoring |
| Startup settle seconds | 15 | Quiet period after providers become ready |
| Startup maximum wait | 240 | Bounded maximum; a broken provider cannot block forever |
| Repair grace seconds | 90 | Extra post-start absence time before a missing entity can mature |
| Repair confirmations | 3 | Repeated missing checks required before creating a Repair issue |

## Legacy migration

Legacy migration is **OFF by default in 2.4.0**.

| Setting | Default |
|---|---:|
| Enable legacy Eshtaya migration | Off |
| Migrate old Entity Manager | On when master migration is enabled |
| Migrate old Multi-Way / Smart Groups | On when master migration is enabled |
| Migrate old Template Manager | On when master migration is enabled |
| Legacy HACS cleanup | Off |
| Legacy service aliases | Off |

When the master migration setting is off, Eshtaya does not intentionally scan/copy/unload/remove retired Eshtaya integrations as part of a new migration.

**Safety exception:** a migration already in a transactional `prepared` / `restart_required` cutover before upgrading to 2.4.0 is allowed to finish. This prevents leaving an old engine disabled halfway through a previously started migration.

### Native Home Assistant Groups are not legacy migration

The following stays available independently of the legacy migration master switch:

```text
Home Assistant Group discovery
→ inspect native/UI Group helper
→ transactional Take Over when supported
→ preserve exact entity ID and metadata
```

Disabling legacy Eshtaya migration does **not** remove native HA Group discovery or Take Over.

---

# Installation

1. Open **HACS → Integrations → Custom repositories**.
2. Add:

```text
https://github.com/badereshtaya/hacs-eshtaya-smart-control
```

3. Select **Integration** and install Eshtaya Smart Control.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration**.
6. Add **Eshtaya Smart Control**.

Tuya OpenAPI credentials are not required during initial installation.

---

# Updating

Use the normal HACS update path:

```text
HACS
→ Eshtaya Smart Control
→ Update
→ Restart Home Assistant
```

Do **not** delete the unified Config Entry just to update.

For an installation that already completed all old migrations, leave **Enable legacy Eshtaya migration = Off**.

---

# Multi-Way

The Multi-Way engine provides:

- Mirror / Toggle / Momentary / Event / Follow modes;
- physical-output authority;
- cloud echo protection;
- rapid input handling;
- confirmation and bounded retry;
- fallback output support;
- startup barrier and Repair grace;
- health/latency/activity diagnostics;
- test, remap, backup and restore tooling.

Guides:
- [English Multi-Way](docs/en/MULTIWAY.md)
- [Multi-Way بالعربية](docs/ar/MULTIWAY.md)

---

# Native Smart Groups and HA Group Take Over

Smart Groups remain independent from legacy migration. Eshtaya can inspect Home Assistant Group helpers and, where strict compatibility permits, transactionally take over a UI-created helper while preserving its entity ID and user-facing registry metadata.

Guides:
- [English Smart Groups](docs/en/SMART_GROUPS.md)
- [المجموعات الذكية](docs/ar/SMART_GROUPS.md)

---

# Template Manager

Template Manager creates permanent Light/Fan entities backed by physical switch entities and supports source relinking while keeping the permanent entity ID stable.

Legacy Template Manager migration is now controlled by the global/individual migration options. Existing unified Template Manager mappings continue to load normally even when legacy migration is disabled.

Guides:
- [English Template Manager](docs/en/TEMPLATE_MANAGER.md)
- [إدارة الكيانات الدائمة](docs/ar/TEMPLATE_MANAGER.md)

---

# System Center

System Center includes:

- health score;
- startup-barrier phase and pending reference count;
- Multi-Way/Smart Group health;
- migration history/status;
- current non-secret startup/migration options;
- Alexa file health;
- repair actions;
- sanitized System Report and Migration Report.

Tuya secrets/tokens are never included in those reports.

---

# Documentation

The repository and in-app Documentation Center use the same 14 Markdown guides in both languages. CI performs a byte-for-byte comparison between:

```text
docs/ar                               ↔ custom_components/eshtaya_smart_control/docs/ar
docs/en                               ↔ custom_components/eshtaya_smart_control/docs/en
```

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

# Validation

Every release must pass:

- HACS validation;
- Hassfest;
- Python compilation;
- JSON/translation parsing;
- JavaScript syntax checks;
- startup/migration safety invariants;
- GitHub ↔ in-app documentation byte comparison;
- verified release packaging.

See [CHANGELOG.md](CHANGELOG.md) for release history.

# Security

Never publish Tuya Client Secret/access tokens, Home Assistant tokens or raw migration backups. See [SECURITY.md](SECURITY.md).

# License

MIT — see [LICENSE](LICENSE).
