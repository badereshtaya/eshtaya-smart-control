# البنية التقنية — Architecture

Eshtaya Smart Control مبني كمنصة Home Assistant واحدة تحتوي وحدات مستقلة نسبيًا تشترك في نفس Config Entry والواجهة والصلاحيات والتشخيص.

## المكونات الرئيسية

```text
Home Assistant Core
└─ custom_components/eshtaya_smart_control
   ├─ Config Entry / lifecycle
   ├─ Access Control
   ├─ Entity & Alexa Control
   ├─ Tuya Control
   ├─ Multi-Way Engine
   ├─ Smart Groups / Action Groups
   ├─ Template Manager
   ├─ Migration Center
   ├─ System Center
   ├─ Documentation API
   └─ Unified frontend panel
```

## مبدأ الوحدة الواحدة

بدل وجود عدة Custom Integrations منفصلة لكل أداة، يتم تجميع الأدوات تحت domain واحد:

```text
eshtaya_smart_control
```

الفوائد:

- Sidebar واحد.
- نظام صلاحيات موحد.
- Lifecycle واحد.
- تقارير وتشخيصات مشتركة.
- Migration منظمة من الأدوات القديمة.
- تقليل تعارض الخدمات والـEntity ownership.

## Lifecycle

عند `async_setup` يتم تسجيل APIs والخدمات المشتركة التي لا تحتاج Config Entry جاهزة بالكامل.

عند `async_setup_entry` يتم:

1. تحميل Access Control.
2. تجهيز Migration للأدوات القديمة.
3. تحميل Template Manager store وإجراء migration الخاصة به.
4. تشغيل Entity Manager وTuya Manager.
5. تشغيل Multi-Way/Smart Group runtime والمنصات.
6. تشغيل Template Manager.
7. التحقق النهائي من migrations.
8. تسجيل Sidebar panel.

إذا حدث خطأ أثناء Cutover، يحاول النظام إيقاف المنصات الجديدة قبل Rollback لمنع أن تعود الكيانات القديمة بأسماء `_2`.

## منصات Home Assistant

الوحدة تدعم منصات متعددة عبر Config Entry، منها:

```text
light
switch
fan
cover
lock
media_player
valve
binary_sensor
sensor
button
event
notify
```

ملفات المنصة الموحدة يمكن أن تجمع أكثر من engine. مثال `light.py` يشغل Light entities التابعة لـMulti-Way وTemplate Manager تحت نفس Config Entry.

## Frontend

الواجهة عبارة عن custom panel داخل Sidebar.

الـassets تقدم من مسار Static خاص:

```text
/eshtaya_smart_control_static/
```

ويتم إضافة رقم الإصدار:

```text
smart-control-panel-v23.js?v=2.3.1
```

هذا مهم لكسر browser cache بعد HACS Update.

### طبقات الواجهة

الواجهة تطورت عبر extensions متراكبة للحفاظ على استقرار الوحدات السابقة. هذا يخلق خطر أن تبقى طبقة قديمة بخريطة Permissions أو Views أقدم من الوحدة الجديدة.

في 2.3.1 تم إصلاح هذا تحديدًا بإضافة Template Manager إلى الخريطة المشتركة في الطبقة القديمة أيضًا، حتى لا يظهر التاب ثم تمنعه طبقة click أقدم.

## WebSocket APIs

كل وحدة تملك endpoints محددة. الحماية لا تعتمد على UI فقط؛ أوامر الإدارة تمر عبر Permission decorators أو فحص Home Assistant admin/native permissions حسب العملية.

أمثلة:

```text
eshtaya_smart_control/access/current
eshtaya_smart_control/overview
eshtaya_smart_control/template/snapshot
eshtaya_smart_control/template/create
eshtaya_smart_control/ha_access/snapshot
```

## Access Control architecture

هناك مستويان:

### Eshtaya RBAC

Store داخلي للأدوار والتعيينات والاستثناءات:

```text
Role permissions
+ Force Allow
- Force Deny
= Effective Permissions
```

### Home Assistant Core access

للتغييرات على الحساب الحقيقي تستخدم الإضافة APIs/نماذج Home Assistant المتاحة، ولا تعتبر Eshtaya roles بديلًا عن Core authorization.

## Entity & Alexa architecture

المصدر الرئيسي للقواعد هو Store/Manager واحد، ويتم توليد ملفي hidden entities منه:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

حالة المزامنة تعتمد على المحتوى/hash وليس فقط وجود الملفين.

## Tuya architecture

Tuya module اختيارية. بيانات الاعتماد تحفظ في backend. قائمة الأجهزة تستخدم:

- bounded HTTP timeout.
- cache لآخر نتيجة ناجحة.
- lock لمنع concurrent refresh storms.
- forced refresh يعرض الخطأ بدل استخدام stale cache بصمت.

## Multi-Way architecture

المحرك يفصل بين:

- Store/configuration.
- Runtime manager.
- Generated entities.
- WebSocket UI APIs.
- Activity/diagnostics.

Startup-safe manager يمنع أوامر غير مناسبة أثناء إعادة التشغيل ويعالج cloud echo والتأكيد وإعادة المحاولة ضمن حدود.

## Template Manager architecture

Template Manager يملك Store للمappings:

```text
permanent entity_id
source_entity
type
name
unique_id
```

Light/Fan entities تنفذ الأوامر على `source_entity` وتتابع حالته.

### Migration 2.3.1

المهاجر يستطيع القراءة من runtime القديم أو Generated YAML/JSON. إذا كانت Entity IDs القديمة ما زالت محملة بالذاكرة بعد إزالة الملفات، يتم تعليم records كـ`deferred` ولا تنشأ المنصات الجديدة حتى Restart التالي.

هذا يجعل شرط ownership واضحًا:

```text
لا يحق للمحرك الجديد إنشاء entity_id قبل أن يختفي owner القديم من runtime/registry.
```

## Documentation architecture

ابتداءً من 2.3.1 ملفات Markdown في `docs/ar` و`docs/en` هي المصدر البشري الأساسي للتوثيق.

نسخة مطابقة يتم تعبئتها في `docs_bundle.json` داخل custom component حتى يعمل Documentation Center بدون إنترنت بعد تثبيت HACS.

CI يقارن ملفات GitHub مع الـbundle، وأي اختلاف يفشل Validation بدل إطلاق نسخة فيها توثيق داخلي قديم.

## مبادئ التصميم

- Backend enforcement قبل UI convenience.
- Safe failure أفضل من duplicate entities.
- عمليات القراءة يمكن أن تستخدم retry/cache، أما عمليات الكتابة فلا يعاد تنفيذها تلقائيًا بدون معرفة أثرها.
- Migration تعمل Backup قبل cleanup.
- الوحدات يجب أن تفشل بشكل مستقل قدر الإمكان؛ فشل Tuya لا يجب أن يمنع Shell كامل المنصة.
- Logs وتقارير التشخيص تبقى جزءًا من التشغيل، وليس فقط واجهة رسومية.
