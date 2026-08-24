# إدارة الكيانات الدائمة — Template Manager

Template Manager هو طبقة الكيانات الدائمة داخل **Eshtaya Smart Control**. وظيفته إنشاء كيان Home Assistant ثابت من نوع `light` أو `fan` فوق مفتاح فعلي من نوع `switch`، غالبًا من Tuya.

## لماذا نستخدمه؟

بدل أن تعتمد الأوتوميشنز والداشبورد وأليكسا على Entity ID للمفتاح الفيزيائي مباشرة، يمكن اعتماد كيان دائم ثابت.

مثال:

```text
المصدر الفيزيائي: switch.living_main_light
الكيان الدائم:     light.living_main_light
```

إذا تغير جهاز Tuya أو تغير Entity ID للمصدر، يمكنك عمل **Relink** للمصدر مع إبقاء:

```text
light.living_main_light
```

كما هو. هذا يقلل تعديل الأوتوميشنز والواجهات بعد استبدال جهاز.

# التبويبات

## Available — المتاح

يعرض مفاتيح `switch` المتوافقة التي ليست مستخدمة حاليًا كمصدر لكيان دائم.

لكل سطر:

- **Type**: Light أو Fan.
- **Name**: الاسم الظاهر.
- **Entity ID**: المعرف النهائي.
- **Create**: إنشاء الربط.

الاقتراح الافتراضي يحول مثلًا:

```text
switch.office_light
```

إلى:

```text
light.office_light
```

إذا اخترت Fan يصبح domain هو `fan`.

لا يسمح بإنشاء Entity ID مستخدم أصلًا في State Machine أو Entity Registry أو Store الخاصة بـTemplate Manager.

## Managed — المدار

يعرض كل الكيانات الدائمة التي تملكها الإضافة.

لكل عنصر سترى:

- الاسم.
- Entity ID الدائم.
- `source_entity`.
- حالة المصدر.
- Platform للمصدر.
- النوع Light/Fan.

### Edit

يمكن تغيير الاسم وEntity ID، لكن الكيان يجب أن يبقى في نفس domain. Light لا يتحول إلى Fan بمجرد Rename.

عند تغيير Entity ID يتم استخدام Entity Registry بدل إنشاء كيان مستقل جديد قدر الإمكان.

### Source

يغير المصدر الفيزيائي خلف الكيان الدائم.

مثال بعد استبدال مفتاح Tuya:

```text
قديم: switch.living_light_old
جديد: switch.living_light_new
دائم: light.living_light
```

تغير Source فقط وتبقى الأوتوميشنز على `light.living_light`.

### Delete

يحذف الكيان الدائم والـmapping الخاصة به فقط. لا يحذف مفتاح Tuya الفيزيائي.

## Missing — المفقود

يظهر الكيان هنا عندما لا يعود `source_entity` موجودًا بعد انتهاء حماية Startup.

الحالة `unavailable` المؤقتة لا تعني بالضرورة أن mapping يجب حذفها.

Template Manager يحسب Suggestions لمصادر بديلة اعتمادًا على تشابه Entity IDs، لكن الاقتراح ليس ضمانًا؛ راجع الجهاز قبل تنفيذ Relink.

# تتبع الحالة

الكيان الدائم يقرأ حالة المصدر ويحدّث نفسه عند تغير المفتاح. وعند `turn_on` أو `turn_off` يرسل الأمر إلى `source_entity`.

الفكرة هي:

```text
Permanent entity state ← Physical switch state
Permanent entity command → Physical switch service
```

# حماية Startup

عند تشغيل Home Assistant قد تتأخر Tuya أو integration أخرى في إنشاء states.

Template Manager ينتظر فترة محدودة عندما يكون المصدر ما زال موجودًا في Entity Registry لكنه لم يظهر في State Machine بعد. هذا يمنع نقل كل شيء مباشرة إلى Missing بسبب بطء الإقلاع.

# النقل من الطريقة القديمة في 2.3.1

الإصدار 2.3.1 يدعم أكثر من شكل للطريقة القديمة.

## مصادر الاكتشاف

يبحث عن:

- Config Entries للدومين القديم `eshtaya_template_manager`.
- `sensor.eshtaya_template_manager` عندما يكون مملوكًا للطريقة القديمة.
- Services للدومين القديم.
- مجلد custom component القديم.
- ملفات التخزين والحزم القديمة.
- Generated YAML/JSON المستخدمة لإنشاء الكيانات الدائمة.

الملفات المعروفة تشمل:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

## لماذا قراءة الملفات مهمة؟

في بعض التركيبات القديمة لم يكن هناك Config Entry مستقل جاهز يمكن Unload له. الاعتماد على Runtime Sensor وحده قد يفشل إذا تأخر القديم أو لم يحمل قبل الجديد.

2.3.1 يستطيع استخراج mappings من Generated files نفسها، ثم دمجها مع Runtime records إن كانت متاحة. Runtime mapping الصحيحة لها أولوية عند وجودها لأنها تمثل ما كان المحرك يستخدمه فعليًا.

# تسلسل Migration الآمن

```text
Detect legacy evidence
→ Wait for old runtime when useful
→ Read runtime + generated mappings
→ Validate readable count
→ Capture Entity Registry metadata
→ Backup files and mappings
→ Disable/unload old Config Entry إن وجد
→ Remove old services
→ Remove generated legacy files after backup
→ template.reload إن كان متاحًا
→ Wait for old Entity IDs to be released
```

ثم يوجد مساران.

## المسار A — تحررت Entity IDs

```text
Import mappings
→ Start new Light/Fan entities
→ Verify exact IDs + owner platform
→ Restore name/icon/area/labels
→ Remove old Config Entry
→ Mark completed
```

## المسار B — القديم ما زال في الذاكرة

إذا بقيت مثلًا:

```text
light.room_1
```

موجودة في State Machine من Template integration القديمة، لا يتم إجبار الجديد على الإنشاء.

بدل ذلك:

- تحفظ mappings كـ`deferred`.
- لا يتم إنشاء Light/Fan الجديدة.
- لا يتم إنشاء compatibility sensor الجديد على نفس ID.
- تقفل عمليات Create/Edit/Delete/Relink.
- تظهر حالة `restart_required`.

بعد Restart التالي تكون ملفات القديم قد أزيلت، فلا يحمل القديم، ويكمل الجديد الاستيلاء على **نفس Entity IDs**.

هذه الحماية مصممة خصيصًا لمنع:

```text
light.room_1_2
fan.room_1_2
```

ومنع وجود محركين يتحكمان بنفس المصدر.

# Backup

قبل إزالة أي ملف Legacy يتم إنشاء نسخة داخل:

```text
/config/eshtaya_smart_control_backups/template_manager_<timestamp>/
```

وتشمل قدر الإمكان:

- mappings.
- registry metadata.
- config entry information.
- legacy custom component.
- YAML/JSON/storage files.

لا تحذفها قبل التأكد أن Migration مكتملة.

# Migration Lock

عندما تكون Migration فعالة وغير مكتملة، 2.3.1 يمنع تعديل mappings في مستويين:

1. الواجهة تعطل الأزرار والحقول.
2. الـPython backend يرفض mutation حتى لو تم استدعاء WebSocket/Service يدويًا.

الهدف منع تغيير البيانات أثناء cutover.

# الخدمات

الخدمات الأصلية تحت domain الجديد تشمل:

```text
eshtaya_smart_control.template_scan
eshtaya_smart_control.template_create
eshtaya_smart_control.template_edit
eshtaya_smart_control.template_delete
eshtaya_smart_control.template_relink
```

بعد اكتمال النقل، يمكن تسجيل compatibility aliases للدومين القديم عندما لا يكون implementation القديم موجودًا.

# Compatibility Sensor

بعد اكتمال الانتقال يدعم النظام:

```text
sensor.eshtaya_template_manager
```

ويعرض معلومات مثل:

- managed.
- candidates.
- missing.
- counts.
- ready.
- migration.
- updated_at.

# الصلاحيات

```text
template.view
```

للمشاهدة وScan.

```text
template.manage
```

للإنشاء والتعديل والحذف وRelink.

في 2.3.1 تم إصلاح طبقة navigation القديمة حتى تتعرف على `template.view` مثل backend تمامًا.

# ماذا أفعل بعد تحديث 2.3.1؟

إذا كنت جاي من الطريقة القديمة:

```text
HACS Update
→ Restart Home Assistant
→ افتح Template Manager
```

إذا ظهرت **Migration completed** انتهى النقل.

إذا ظهرت **Restart Required**:

```text
Restart Home Assistant مرة واحدة
→ افتح Template Manager
→ تأكد أن Managed موجودة بدون *_2
```

لا تحذف Eshtaya Smart Control ولا تعيد تثبيتها فقط لإكمال النقل.
