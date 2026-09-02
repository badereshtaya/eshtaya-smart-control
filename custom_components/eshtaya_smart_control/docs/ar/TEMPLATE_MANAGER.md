# إدارة الكيانات الدائمة — Template Manager

Template Manager هو طبقة الكيانات الدائمة داخل **Eshtaya Smart Control**. ينشئ أو يدير كيانات Home Assistant ثابتة من نوع `light` أو `fan` فوق `switch` فيزيائي، وغالبًا يكون مصدره Tuya.

# لماذا نستخدم كيانًا دائمًا؟

مثال:

```text
المصدر الفيزيائي: switch.living_main_light
الكيان الدائم:     light.living_main_light
```

إذا استبدلت الجهاز أو تغير Entity ID للمصدر لاحقًا، استخدم **Relink** واربط الكيان الدائم بمفتاح جديد بدون تغيير Entity ID الذي تعتمد عليه الداشبورد والأوتوميشنز وAlexa.

# التبويبات

## Available — المتاح

يعرض مفاتيح متوافقة ليست مستخدمة كمصدر لكيان دائم. يمكنك اختيار:

- Light أو Fan.
- الاسم.
- Entity ID النهائي.
- Create.

يرفض النظام إنشاء Entity ID مستخدم أصلًا في State Machine أو Entity Registry أو Template Manager Store.

## Managed — المدار

يعرض كل الكيانات التي يديرها Template Manager، سواء mappings أصلية داخل Eshtaya أو mappings معروفة قادمة من ملفات Generated Packages.

العمليات:

- **Edit**: تعديل الاسم أو Entity ID مع البقاء في نفس domain.
- **Source / Relink**: استبدال المصدر الفيزيائي مع إبقاء الكيان الدائم.
- **Delete**: حذف الكيان الدائم والـmapping فقط، وليس المفتاح الفيزيائي.

# إدارة ملفات Generated Packages في 2.4.2

أي ملف Generated معروف من Eshtaya أصبح يظهر تلقائيًا كـ **Managed** حتى لو كانت Legacy Migration مطفأة. يشمل ذلك تحديدًا:

```text
/config/packages/eshtaya_generated_lights.yaml
/config/packages/eshtaya_generated_templates.yaml
/config/eshtaya_template_manager/generated_templates.yaml
```

في بعض نسخ Home Assistant يظهر مجلد الإعدادات على المضيف باسم `/homeassistant` بدل `/config`، لذلك المسار الذي عندك:

```text
/homeassistant/packages/eshtaya_generated_lights.yaml
```

هو نفس موقع الـpackage المنطقي داخل Home Assistant في هذه البيئة.

هذا السلوك مختلف عمدًا عن Legacy Migration الكاملة:

- ملف YAML يبقى في مكانه ولا يتم حذفه.
- Home Assistant `template` integration يبقى Runtime Owner لهذه الكيانات.
- Eshtaya يقرأ الـmappings من الملف ويعرضها داخل تبويب Managed.
- يتم تعليم هذه السجلات داخليًا كـDeferred حتى لا ينشئ Eshtaya Duplicate بنفس Entity ID.
- السويتشات المستخدمة داخل الملف لا تبقى ظاهرة كأنها Available جديدة.

عند استخدام Edit أو Relink أو Delete على سجل قادم من Generated Package، يقوم Eshtaya بتعديل **نفس ملف YAML**، ويأخذ Backup أولًا، ثم يكتب عبر ملف مؤقت ويعمل `template.reload`.

النسخ الاحتياطية تحفظ تحت:

```text
/config/eshtaya_smart_control_backups/generated_packages/<timestamp>/...
```

لا تحتاج لتفعيل Legacy Migration فقط حتى تدير ملف `eshtaya_generated_lights.yaml` الموجود عندك.

## Missing — المفقود

يظهر الـmapping كمفقود عندما يبقى `source_entity` غير موجود بعد حماية Startup الخاصة بـTemplate Manager. حالة `unavailable` مؤقتة وحدها لا تعني أن المصدر حُذف.

Suggestions للمصدر البديل مساعدة فقط؛ افحص الجهاز الحقيقي قبل Relink.

# سلوك التشغيل

```text
حالة الكيان الدائم ← حالة switch المصدر
أمر الكيان الدائم  → خدمة switch على المصدر
```

أي تغيير يأتي من Tuya أو زر الحائط أو Home Assistant أو Automation ينعكس على الكيان الدائم.

# حماية Startup

Template Manager لديه حماية محدودة خاصة بتأخر ظهور مصادره، وفوق ذلك Eshtaya 2.4 يتم ترتيبه بعد Tuya الرسمية عندما تكون مفعلة.

Startup Barrier في Multi-Way منفصل عن منطق Template Manager، لكن الهدف في الحالتين واحد: عدم اعتبار بطء Provider أثناء Restart حذفًا حقيقيًا للكيان.

# إعدادات Startup وMigration في 2.4.2

الإعدادات أصبحت ظاهرة مباشرة داخل:

```text
Eshtaya Smart Control → System Center
→ Startup & Migration Settings
```

وتبقى أيضًا متاحة من Configure الخاص بالانتجريشن في Home Assistant.

إذا كانت الماجريشنات التاريخية عندك منتهية، الإعداد الموصى به:

```text
Enable legacy Eshtaya migration: Off
Legacy HACS cleanup:             Off
Legacy service aliases:          Off
```

كل selectors الفردية تبقى ظاهرة حتى تستطيع اختيار Entity Manager القديم أو Multi-Way/Smart Groups أو Template Manager كل واحد بشكل مستقل إذا احتجت Migration مقصودة مستقبلًا.

اكتشاف Home Assistant Groups وميزة **Take Over** مستقلان تمامًا عن Legacy Migration ويستمران بالعمل حتى لو كان المفتاح الرئيسي Off.

# Legacy Template Manager Migration

**Migration من Template Manager القديم لا تبدأ تلقائيًا مع Updates العادية.**

إذا أردت عمدًا إلغاء Template Manager قديم مستقل ونقل الملكية إلى كيانات Eshtaya الأصلية:

1. فعّل **Legacy Eshtaya migration**.
2. فعّل **Migrate old Template Manager**.
3. خذ Home Assistant Backup.
4. احفظ الإعدادات وانتظر Reload للانتجريشن.
5. راجع Template Manager وMigration Center.

المهاجر يستطيع قراءة runtime/config entry القديم أو ملفات Generated معروفة مثل:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

هذه Migration الصريحة هي Takeover/Retirement كامل. ليست مطلوبة للإدارة العادية لملف YAML الموضحة بالأعلى.

# تسلسل النقل بدون Duplicate

عند تفعيل Migration عمدًا:

```text
Detect selected legacy evidence
→ Recover mappings
→ Validate readable data
→ Capture Entity Registry metadata
→ Create rollback backup
→ Quiesce old implementation
→ Release exact Entity IDs
→ Start unified entities
→ Verify IDs and ownership
→ Final cleanup when enabled
```

## restart_required

إذا بقيت الكيانات القديمة محملة في ذاكرة Home Assistant، لا ينشئ النظام بدائل `_2`.

تبقى الكيانات الجديدة Deferred، ويكمل Restart التالي نفس Entity IDs بعد أن تختفي تعريفات القديم من Runtime.

إذا كانت Migration سابقة وصلت إلى `restart_required` يسمح لها النظام بالإكمال حتى مع كون Legacy Migration الجديدة Off افتراضيًا، حتى لا تبقى Transaction عالقة في منتصف Cutover.

# Backup وMigration Lock

أثناء مرحلة Cutover فعلية فقط (`prepared` أو `restart_required`):

- الواجهة تقفل Create/Edit/Delete/Relink.
- الـBackend يرفض نفس العمليات حتى لو تم استدعاؤها مباشرة.
- الكيانات Deferred لا تحاول أخذ IDs ما زال القديم يملكها.

حالة Migration قديمة Failed أو Rolled Back لم تعد تترك Template Manager مقفلاً بشكل دائم.

# الخدمات

الخدمات الموحدة:

```text
eshtaya_smart_control.template_scan
eshtaya_smart_control.template_create
eshtaya_smart_control.template_edit
eshtaya_smart_control.template_delete
eshtaya_smart_control.template_relink
```

Compatibility aliases القديمة تحت `eshtaya_template_manager.*` خيار مستقل و**Off افتراضيًا**. فعّلها فقط إذا كانت Automations قديمة ما زالت تعتمد عليها.

# Compatibility Sensor

يمكن للنسخة الموحدة امتلاك:

```text
sensor.eshtaya_template_manager
```

مع managed/candidates/missing counts وحالة readiness وMigration.

# الصلاحيات

```text
template.view
template.manage
```

`template.view` للمشاهدة وScan، و`template.manage` للإنشاء والتعديل والحذف وRelink.

# الوضع الموصى به بعد إنهاء النقل القديم

- اترك Legacy Migration Off.
- اترك Legacy HACS Cleanup Off إلا إذا كنت تنفذ Cleanup مقصودًا بعد Verification.
- اترك Legacy Service Aliases Off إلا إذا احتاجتها Automations قديمة.
- اترك Generated Package mappings تحت الإدارة العادية لـTemplate Manager.
- فعّل Legacy Migration فقط عندما تريد Takeover/Retirement كامل للطريقة القديمة عمدًا.
