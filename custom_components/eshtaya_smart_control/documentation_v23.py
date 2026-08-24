"""v2.3 documentation additions."""
from __future__ import annotations

from copy import deepcopy

from .documentation_v22 import DOCUMENTATION as V22_DOCUMENTATION

DOCUMENTATION = deepcopy(V22_DOCUMENTATION)

DOCUMENTATION.setdefault("en", {})["TEMPLATE_MANAGER"] = r"""
# Template Manager

## Purpose

Template Manager is the permanent-entity layer inside Eshtaya Smart Control. It replaces the old standalone `eshtaya_template_manager` integration and the earlier `switch_as_x` workflow.

Its job is to keep a stable Home Assistant Light or Fan entity in front of a physical Tuya switch. Automations, dashboards, Alexa mappings and scripts can continue to use the permanent entity even when the physical Tuya source is renamed or replaced.

Example:

```text
Physical source: switch.living_main_light
Permanent entity: light.living_main_light
```

The permanent entity sends ON/OFF to the physical source and mirrors its live state.

## Available tab

The **Available** tab shows Tuya switch entities that are not already used by a managed template.

For every row you can choose:

- **Type**: Light or Fan.
- **Name**: the Home Assistant display name of the permanent entity.
- **Entity ID**: the exact permanent entity ID that will be created.
- **Create**: stores the mapping and creates the native entity through the Eshtaya Smart Control config entry.

The default type is Light. The suggested Entity ID changes `switch.example` into `light.example`. If Fan is selected the domain becomes `fan`.

An Entity ID cannot be created when that ID is already used by another Home Assistant entity or registry entry.

## Managed tab

The **Managed** tab lists every permanent entity owned by Template Manager.

Each item contains:

- permanent entity name and Entity ID;
- source entity;
- source integration/platform;
- current source state;
- permanent type: Light or Fan.

### Edit

Edit can change the display name and Entity ID. The entity must stay in its original domain; a Light cannot be renamed into a Fan Entity ID and vice versa.

Entity-ID changes use Home Assistant's Entity Registry so the existing managed entity is renamed rather than creating an unrelated duplicate.

### Source

Source changes the physical switch behind an existing permanent entity. This is useful after replacing a Tuya device or after Tuya creates a new Entity ID.

The permanent Light/Fan Entity ID does not need to change.

### Delete

Delete removes only the permanent Template Manager entity and its stored mapping. It does **not** delete or remove the physical Tuya switch.

## Missing tab

A managed item is placed in **Missing** only when its configured source entity no longer exists after the startup recovery period.

Temporary `unavailable` or `unknown` states do not delete the mapping.

For a missing source, Template Manager calculates candidate replacements from available Tuya switches. Suggestions are ranked by similarity between the previous source Entity ID and the available Entity IDs.

You can use a suggested source or manually enter a replacement source.

## Startup protection

Template Manager does not immediately classify sources as missing during Home Assistant startup. It waits for Home Assistant and source integrations to initialize, with a bounded startup grace period.

This prevents a slow Tuya startup from incorrectly turning all managed templates into Missing items.

## Live state tracking

Permanent entities listen to state changes from their source switch. When the physical switch changes from Home Assistant, Tuya, a wall button or another automation, the managed Light/Fan state is updated immediately.

## Automatic migration from the old standalone method

v2.3 performs a transactional migration when the old `eshtaya_template_manager` method is detected.

The sequence is intentionally strict:

1. Detect old config entries, runtime sensor and known legacy files.
2. Wait for `sensor.eshtaya_template_manager` when a legacy config entry exists but its runtime has not finished loading.
3. Read the old `managed` mappings.
4. Compare the readable mapping count with the count reported by the old manager.
5. Capture Entity Registry metadata for every managed entity.
6. Create a rollback backup under `/config/eshtaya_smart_control_backups/`.
7. Copy the legacy custom-component directory and known legacy storage/package files into that backup.
8. Disable and unload the old config entry so two control engines can never run at the same time.
9. Release the legacy Entity Registry ownership for the managed Entity IDs.
10. Import all mappings into the native Eshtaya Smart Control Template Manager store.
11. Start the new Light/Fan/Sensor entities.
12. Verify that every expected Entity ID exists and is owned by `eshtaya_smart_control`.
13. Restore user-facing registry metadata such as name, icon, area and labels where available.
14. Remove the old config entry.
15. Remove known legacy files from `/config` only after successful verification.
16. Keep the backup for recovery/audit.

If the old runtime cannot be read completely, migration stops and cleanup is refused.

If verification fails after the old engine was stopped, the migration records a rollback state and attempts to re-enable/reload the old config entry instead of silently deleting it.

## Duplicate prevention

The old engine is unloaded **before** the new entities claim their permanent Entity IDs. Cleanup happens **after** verification.

This ordering is the central duplicate-prevention rule:

```text
capture -> backup -> stop old -> import new -> verify -> delete old
```

Never:

```text
start new -> leave old running
```

## Compatibility services

The new integration exposes native services under `eshtaya_smart_control`:

```text
eshtaya_smart_control.template_scan
eshtaya_smart_control.template_create
eshtaya_smart_control.template_edit
eshtaya_smart_control.template_delete
eshtaya_smart_control.template_relink
```

It also keeps compatibility aliases for old automations when the old service domain is no longer registered:

```text
eshtaya_template_manager.scan
eshtaya_template_manager.create_template
eshtaya_template_manager.edit_template
eshtaya_template_manager.delete_template
eshtaya_template_manager.relink
```

## Compatibility sensor

The integrated manager provides:

```text
sensor.eshtaya_template_manager
```

Its attributes continue to expose `managed`, `candidates`, `missing`, their counts, readiness, migration status and update time.

## Access Control

Template Manager has two Eshtaya permissions:

- `template.view`: view the module and scan current status.
- `template.manage`: create, edit, delete and relink templates.

Home Assistant administrators retain full Eshtaya permissions.

## Recovery guidance

If Missing is shown immediately after a restart, use Refresh only after the source integration has had time to initialize. The manager itself already applies startup protection; persistent Missing means the source Entity ID is genuinely absent from Home Assistant.

If migration reports an error, do not manually delete the old integration or backup directory before reviewing the migration state.
"""

DOCUMENTATION.setdefault("ar", {})["TEMPLATE_MANAGER"] = r"""
# إدارة الكيانات الدائمة — Template Manager

## ما وظيفة هذا القسم؟

Template Manager هو طبقة الكيانات الدائمة داخل **Eshtaya Smart Control**. هذا القسم يحل محل الإضافة القديمة المستقلة `eshtaya_template_manager` والطريقة السابقة المبنية على `switch_as_x`.

الفكرة الأساسية: يبقى مفتاح Tuya الحقيقي هو المصدر الفيزيائي، وفوقه يكون عندك كيان Home Assistant ثابت من نوع Light أو Fan.

مثال:

```text
المصدر الحقيقي: switch.living_main_light
الكيان الدائم: light.living_main_light
```

الكيان الدائم يرسل ON/OFF إلى المفتاح الحقيقي ويعكس حالته مباشرة. بهذه الطريقة تظل الأوتوميشنز والداشبورد وأليكسا والسكريبتات تعتمد على Entity ID ثابت حتى لو تغير جهاز Tuya أو تغير المصدر.

## تبويب المتاح — Available

يعرض مفاتيح Tuya من نوع `switch` التي ليست مستخدمة حاليًا كمصدر لكيان دائم.

لكل سطر يوجد:

- **Type / النوع**: Light أو Fan.
- **Name / الاسم**: الاسم الظاهر داخل Home Assistant.
- **Entity ID**: الـEntity ID النهائي الذي سيتم إنشاؤه.
- **Create / إنشاء**: حفظ الربط وإنشاء الكيان كجزء أصلي من Eshtaya Smart Control.

النوع الافتراضي هو Light. إذا كان المصدر:

```text
switch.office_light
```

فالاقتراح الافتراضي يكون:

```text
light.office_light
```

وعند اختيار Fan يصبح Domain هو `fan`.

لن يسمح النظام بإنشاء Entity ID مستخدم أصلًا من كيان آخر أو موجود في Entity Registry.

## تبويب المدار — Managed

يعرض كل الكيانات الدائمة التي يديرها Template Manager.

لكل كيان ستشاهد:

- اسم الكيان الدائم؛
- Entity ID؛
- Source Entity؛
- منصة المصدر؛
- حالة المصدر الحالية؛
- النوع Light أو Fan.

### Edit — تعديل

يسمح بتعديل الاسم وEntity ID.

لا يمكن تحويل Light إلى Fan بمجرد تغيير Entity ID؛ يجب أن يبقى Domain مطابقًا لنوع الكيان الأصلي.

عند تغيير Entity ID يستخدم النظام **Entity Registry** في Home Assistant بدل إنشاء كيان unrelated جديد، والهدف هو المحافظة على ملكية الكيان وتجنب الدبلكيت.

### Source — تغيير المصدر

يستخدم عندما تبدل جهاز Tuya أو يتغير Entity ID للمفتاح الحقيقي.

مثال:

```text
light.salon_main
```

كان مرتبطًا بـ:

```text
switch.old_salon_main
```

وبعد تبديل الجهاز أصبح المصدر:

```text
switch.new_salon_main
```

تغيّر Source فقط، بينما يبقى `light.salon_main` ثابتًا.

### Delete — حذف

يحذف الكيان الدائم وربطه من Template Manager فقط.

**لا يتم حذف مفتاح Tuya الفيزيائي.**

## تبويب المفقود — Missing

لا يعتبر النظام المصدر Missing لمجرد أنه `unavailable` أو `unknown` مؤقتًا.

الكيان يدخل Missing فقط عندما لا يعود Source Entity موجودًا بعد انتهاء مرحلة الحماية عند الإقلاع.

عند وجود Source مفقود، النظام يبحث في مفاتيح Tuya المتاحة ويعطي اقتراحات مرتبة حسب تشابه Entity ID القديم مع Entity IDs الحالية.

يمكن اختيار اقتراح أو إدخال Source جديد يدويًا.

## حماية الإقلاع Startup Protection

عند Restart لـHome Assistant قد تحتاج Tuya وقتًا قبل ظهور كل الكيانات.

لذلك Template Manager لا يعمل حكم Missing مباشرة عند بداية التشغيل. ينتظر Home Assistant وتكاملات المصادر ضمن فترة Grace محدودة ثم يعمل Reconciliation.

هذا يمنع المشكلة القديمة التي كانت تظهر عشرات الكيانات Missing كذبًا لأن Scan سبق تحميل Tuya.

## متابعة الحالة المباشرة

الكيان الدائم يستمع لتغييرات المصدر الحقيقي.

إذا تغير المفتاح من:

- تطبيق Tuya؛
- زر حائط؛
- Home Assistant؛
- Automation أخرى؛

تتحدث حالة Light/Fan الدائم مباشرة.

# الهجرة التلقائية من الطريقة القديمة

الإصدار v2.3 يعمل Migration تلقائية إذا اكتشف الطريقة القديمة `eshtaya_template_manager`.

الترتيب متعمد ولا يسمح بتشغيل المحركين معًا:

1. يفحص Config Entries القديمة والـruntime sensor والملفات المعروفة للطريقة القديمة.
2. إذا وجد Config Entry قديم ولم يظهر `sensor.eshtaya_template_manager` بعد، ينتظر الـruntime القديم بدل افتراض أن القائمة فارغة.
3. يقرأ كل عناصر `managed` القديمة.
4. يقارن عدد العناصر المقروءة مع `managed_count` الذي يبلغه النظام القديم.
5. يأخذ Metadata من Entity Registry لكل كيان: Entity ID والاسم والأيقونة والمنطقة والـLabels عند توفرها.
6. ينشئ Backup تحت:

```text
/config/eshtaya_smart_control_backups/
```

7. ينسخ داخل الـBackup ملفات الإضافة القديمة وملفات Storage/Packages القديمة المعروفة.
8. يعطل ويعمل Unload للطريقة القديمة **قبل تشغيل الكيانات الجديدة**.
9. يحرر ملكية Entity IDs القديمة من Entity Registry.
10. ينقل كل الـMappings إلى Storage الجديد الخاص بـEshtaya Smart Control.
11. يشغل Light/Fan/Sensor الجديدة من نفس Config Entry تبع Smart Control.
12. يتحقق حرفيًا أن كل Entity ID متوقع رجع وملكيته أصبحت `eshtaya_smart_control`.
13. يعيد الاسم والأيقونة والمنطقة والـLabels المحفوظة حيث أمكن.
14. يحذف Config Entry القديم.
15. ينظف ملفات الطريقة القديمة داخل `/config` فقط بعد نجاح التحقق.
16. يبقي نسخة الـBackup ولا يحذفها.

## ماذا لو لم يقدر يقرأ القديم؟

إذا اكتشف النظام القديم لكنه لم يستطع قراءة الـmanaged mappings كاملة، **يمنع Cleanup بالكامل**.

مثال: القديم يقول إن عنده 52 Managed لكن النظام الجديد قدر يقرأ 51 فقط؛ في هذه الحالة لا يعتبر النقل ناجحًا ولا يحذف الطريقة القديمة.

## ماذا لو فشل التحقق بعد النقل؟

إذا لم يرجع Entity ID معين أو ظهر أنه مملوك لمنصة أخرى، تعتبر الهجرة فاشلة.

يتم تسجيل حالة Rollback ويحاول النظام إعادة تفعيل/Reload الـConfig Entry القديم بدل حذف بياناته بصمت.

## قاعدة منع الدبلكيت

الترتيب هو:

```text
قراءة القديم
→ Backup
→ إيقاف القديم
→ نقل الإعدادات
→ تشغيل الجديد
→ Verify
→ حذف القديم
```

وليس:

```text
تشغيل الجديد
→ إبقاء القديم شغال
```

بهذا لا يكون عندك محركان يتحكمان بنفس الكيانات في نفس الوقت.

# الخدمات الجديدة

داخل Eshtaya Smart Control:

```text
eshtaya_smart_control.template_scan
eshtaya_smart_control.template_create
eshtaya_smart_control.template_edit
eshtaya_smart_control.template_delete
eshtaya_smart_control.template_relink
```

وللمحافظة على Automations القديمة، عند عدم وجود Service Domain القديم يتم توفير aliases:

```text
eshtaya_template_manager.scan
eshtaya_template_manager.create_template
eshtaya_template_manager.edit_template
eshtaya_template_manager.delete_template
eshtaya_template_manager.relink
```

# Sensor التوافق

يبقى موجودًا:

```text
sensor.eshtaya_template_manager
```

لكن بعد الهجرة يصبح مملوكًا لـEshtaya Smart Control.

Attributes تشمل:

- `managed`
- `candidates`
- `missing`
- `managed_count`
- `available_count`
- `missing_count`
- `ready`
- `migration`
- `updated_at`

# الصلاحيات

القسم له صلاحيتان داخل Access Control:

```text
template.view
template.manage
```

`template.view` للمشاهدة والفحص.

`template.manage` للإنشاء والتعديل والحذف وتغيير Source.

مدير Home Assistant يحصل على صلاحيات Eshtaya كاملة تلقائيًا.

# عند وجود مشكلة

إذا ظهر Missing مباشرة بعد Restart، لا تحذف أي Mapping. النظام عنده Startup Protection أصلًا؛ اعمل Refresh بعد استقرار Tuya.

إذا استمر Missing بعد الاستقرار، فهذا يعني أن Source Entity ID القديم غير موجود فعليًا ويحتاج Re-Link.

إذا Migration Center أظهر خطأ، لا تحذف مجلد الـBackup ولا الإضافة القديمة يدويًا قبل معرفة سبب فشل التحقق.
"""
