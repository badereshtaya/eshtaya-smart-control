# الهجرة التلقائية من الأدوات القديمة

Eshtaya Smart Control صُممت لتستبدل عدة أدوات منفصلة بمنصة واحدة بدون تشغيل محركين على نفس الأجهزة وبدون إجبارك على حذف الإضافة الموحدة وإعادة تثبيتها عند كل تحديث.

## ما الذي يمكن نقله؟

يوجد مساران رئيسيان للهجرة:

### الهجرة الموحدة القديمة

تشمل الأدوات مثل:

```text
eshtaya_entity_manager
eshtaya_multiway
```

وتنقل قواعد Entity/Alexa وإعدادات Multi-Way وSmart Groups إلى Storage الموحدة.

### Template Manager القديم

ابتداءً من 2.3.x أصبح Template Manager جزءًا أصليًا من Eshtaya Smart Control. الإصدار 2.3.1 يوسع اكتشاف القديم ليشمل:

- Config Entry قديم إن وجد.
- `sensor.eshtaya_template_manager` القديم.
- Services للدومين القديم.
- مجلد custom component القديم.
- Generated YAML/JSON وStorage/Packages المعروفة.

## القاعدة الأساسية

الهجرة ليست Copy ثم Delete. الترتيب الآمن هو:

```text
Detect
→ Capture
→ Backup
→ Quiesce / stop legacy
→ Import or stage new state
→ Verify
→ Final cleanup
```

إذا لم يستطع النظام إثبات أن البيانات المطلوبة قابلة للنقل، لا يفترض النجاح ولا يكمل حذفًا مدمرًا.

# Migration Center

System Center يعرض حالة ومراحل الهجرة. الحالات المهمة تشمل:

```text
not_found
prepared
restart_required
completed
rolled_back
error
```

## not_found

لم يتم العثور على Legacy يحتاج نقلًا في هذه الجولة.

هذه الحالة ليست سببًا دائمًا لتجاهل القديم في الإصدارات اللاحقة؛ 2.3.1 يعيد فحص الأدلة الفعلية عند التشغيل، لذلك تحديث عادي فوق 2.3.0 يمكن أن يكتشف ملفات Template Manager التي لم يلتقطها المهاجر السابق.

## prepared

تم أخذ البيانات والـBackup وتجهيز المحرك الجديد للاستحواذ.

## restart_required

هذه حالة أمان، وليست Failure.

في Template Manager تعني عادة:

- تمت قراءة mappings القديمة.
- تم أخذ Backup.
- تمت إزالة تعريفات Generated القديمة من القرص.
- لكن Light/Fan أو compatibility sensor القديم ما زال محملًا داخل ذاكرة Home Assistant.
- الكيانات الجديدة موسومة `deferred` ولا يتم إنشاؤها بعد.

الهدف منع:

```text
light.example_2
fan.example_2
sensor.eshtaya_template_manager_2
```

الحل الصحيح:

```text
Restart Home Assistant مرة واحدة
```

وبعد التشغيل التالي يكمل الاستحواذ على نفس Entity IDs.

## completed

تم التحقق من الكيانات/القواعد المطلوبة وأصبحت الطريقة الجديدة هي المالكة الفعلية.

## rolled_back

بدأ cutover ثم اكتشف النظام مشكلة قبل الإنهاء، فحاول استعادة الطريقة القديمة والملفات المحفوظة بدل مواصلة Cleanup خطير.

# Backup

## Entity/Multi-Way migration

تستخدم Migration Center نسخة احتياطية داخل Storage الموحدة وتحفظ معلومات كافية لإعادة التفعيل عند فشل Validation.

## Template Manager migration

يتم إنشاء Backup فعلي تحت:

```text
/config/eshtaya_smart_control_backups/template_manager_<timestamp>/
```

ويحتوي قدر الإمكان على:

- mappings.
- Entity Registry metadata.
- Config Entry metadata.
- Generated YAML/JSON.
- Storage/package files المعروفة.
- custom component القديم إن وجد.

لا يحذف النظام هذا الـBackup بعد نجاح النقل.

# هجرة Entity & Alexa

المسار العام:

1. اكتشاف Storage القديمة.
2. Backup.
3. نسخ القواعد إلى UnifiedEntityManager عندما تكون الوجهة مناسبة.
4. مقارنة الأعداد.
5. التحقق من ملفات hidden entities.
6. تعطيل/إزالة القديم بعد النجاح.

الملفات المدارة تبقى:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

# هجرة Multi-Way وSmart Groups

المسار العام:

1. قراءة Config/Storage القديمة.
2. Backup.
3. منع تشغيل المحرك القديم والجديد معًا.
4. تشغيل runtime الموحدة.
5. مقارنة Expected/Actual groups.
6. Reconcile للـhidden members.
7. إزالة Config Entry القديم بعد نجاح التحقق.

Compatibility aliases تبقي خدمات `eshtaya_multiway.*` الشائعة تعمل بعد النقل لتقليل كسر الأوتوميشنز.

# هجرة Template Manager في 2.3.1

## مصادر mappings

المهاجر يقرأ Runtime القديم عندما يكون متاحًا، ويقرأ أيضًا ملفات مثل:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

عند وجود نفس permanent entity في ملف وRuntime حي، Runtime له أولوية لأنه يمثل الربط المستخدم فعليًا في تلك اللحظة.

## التحقق قبل Cleanup

قبل الاستحواذ النهائي يتم حفظ:

- permanent `entity_id`.
- `source_entity`.
- النوع Light/Fan.
- الاسم.
- metadata من Entity Registry مثل Area/Icon/Labels عند توفرها.

بعد تشغيل الجديد يتم التحقق أن Entity IDs المتوقعة موجودة وملكيتها أصبحت `eshtaya_smart_control`.

## إذا القديم بدون Config Entry

بعض التركيبات القديمة مبنية على YAML أو custom component يتم تحميله مع Startup ولا يمكن Unload له بشكل نظيف فورًا.

2.3.1 لا يتجاهل هذا السيناريو. بعد Backup يحذف تعريفات Legacy المعروفة ويحاول `template.reload` عندما يكون متاحًا. إذا ظل أي permanent entity أو sensor قديم في الذاكرة، ينتقل إلى `restart_required` بدل إنشاء duplicate.

# عمليات HACS Cleanup

تنظيف مستودعات HACS القديمة هو خطوة لاحقة بعد نجاح التحقق، وليس شرطًا لإثبات صحة البيانات.

إذا HACS API غير متاحة مؤقتًا، يمكن أن ينجح cutover بينما يظهر HACS cleanup كحالة منفصلة تحتاج انتباهًا.

# هل أحذف Eshtaya Smart Control وأعيد تثبيتها؟

لا. في التحديث العادي:

```text
HACS Update
→ Restart Home Assistant
→ راجع Migration Center / Template Manager
```

حذف Config Entry الموحدة قد يزيل الحالة التي يحتاجها المهاجر لمعرفة ما تم نقله وما لم يتم نقله.

# بعد اكتمال الهجرة

تحقق من:

- عدم وجود Entity IDs بنهاية `_2` بشكل غير متوقع.
- عمل الأوتوميشنز القديمة.
- سلامة Alexa files.
- Multi-Way/Smart Groups.
- Template Manager Managed/Missing.
- عدم وجود Legacy engine فعّال يتحكم بنفس الأجهزة.

Full Backup لـHome Assistant يبقى شبكة الأمان الأساسية قبل تحديثات أو migrations كبيرة.
