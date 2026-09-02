# إدارة الكيانات الدائمة — Template Manager

Template Manager هو طبقة الكيانات الدائمة داخل **Eshtaya Smart Control**. ينشئ كيان Home Assistant ثابت من نوع `light` أو `fan` فوق `switch` فيزيائي، وغالبًا يكون مصدره Tuya.

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

يعرض الكيانات الدائمة التي يملكها Template Manager الموحد ومصادرها وحالة كل مصدر.

العمليات:

- **Edit**: تعديل الاسم أو Entity ID مع البقاء في نفس domain.
- **Source / Relink**: استبدال المصدر الفيزيائي مع إبقاء الكيان الدائم.
- **Delete**: حذف الكيان الدائم والـmapping فقط، وليس المفتاح الفيزيائي.

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

Startup Barrier الجديد في Multi-Way منفصل عن منطق Template Manager، لكن الهدف في الحالتين واحد: عدم اعتبار بطء Provider أثناء Restart حذفًا حقيقيًا للكيان.

# Legacy Template Manager Migration في 2.4.0

**Migration من Template Manager القديم لم تعد تبدأ تلقائيًا مع كل Update عادي.**

افتح:

```text
Settings → Devices & services
→ Eshtaya Smart Control
→ Configure
```

إذا كان النقل القديم عندك مكتملًا، الإعداد الموصى به:

```text
Enable legacy Eshtaya migration: Off
Legacy HACS cleanup:             Off
Legacy service aliases:          Off
```

كل mappings الموجودة أصلًا داخل Template Manager الموحد تستمر بالتحميل والعمل طبيعيًا عندما تكون Legacy Migration مطفأة.

إذا احتجت لاحقًا نقل Template Manager قديم عمدًا:

1. فعّل **Legacy Eshtaya migration**.
2. اترك **Migrate old Template Manager** مفعلة.
3. خذ Home Assistant Backup.
4. احفظ Configure وانتظر Reload.
5. راجع Template Manager وMigration Center.

المهاجر يستطيع قراءة runtime/config entry القديم أو ملفات Generated معروفة مثل:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

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

إذا كانت Migration وصلت إلى `restart_required` قبل تحديث 2.4.0، يسمح لها النظام بالإكمال حتى مع كون Legacy Migration الجديدة Off افتراضيًا. هذا يمنع ترك Transaction قديم في منتصف Cutover.

# Backup وMigration Lock

قبل إزالة تعريفات قديمة يتم إنشاء Backup تحت:

```text
/config/eshtaya_smart_control_backups/template_manager_<timestamp>/
```

وأثناء Migration فعالة وغير مكتملة:

- الواجهة تقفل Create/Edit/Delete/Relink.
- الـBackend يرفض نفس العمليات حتى لو تم استدعاؤها مباشرة.
- الكيانات Deferred لا تحاول أخذ IDs ما زال القديم يملكها.

# الخدمات

الخدمات الموحدة:

```text
eshtaya_smart_control.template_scan
eshtaya_smart_control.template_create
eshtaya_smart_control.template_edit
eshtaya_smart_control.template_delete
eshtaya_smart_control.template_relink
```

Compatibility aliases القديمة تحت `eshtaya_template_manager.*` أصبحت خيارًا مستقلًا و**Off افتراضيًا**. فعّلها فقط إذا كانت Automations قديمة ما زالت تعتمد عليها.

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

إذا كل بيانات Template Manager القديمة أصبحت داخل Eshtaya Smart Control:

- اترك Legacy Migration Off.
- اترك Legacy HACS Cleanup Off إلا إذا كنت تنفذ Cleanup مقصودًا بعد Verification.
- اترك Legacy Service Aliases Off إلا إذا احتاجتها Automations قديمة.
- استخدم Template Manager الموحد لكل mappings وRelink جديدة.
