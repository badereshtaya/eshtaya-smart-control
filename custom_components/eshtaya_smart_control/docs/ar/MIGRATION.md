# الهجرة — Migration

ابتداءً من الإصدار 2.4.0 لم تعد Migration من أدوات Eshtaya القديمة عملية تلقائية تعمل في الخلفية. أصبحت **اختيارية ومتحكمًا بها بالكامل من Configure**.

من المهم التفريق بين ثلاث حالات مختلفة:

1. نقل أدوات Eshtaya القديمة retired integrations.
2. البيانات التي أصبحت أصلًا داخل Eshtaya Smart Control مثل Template Manager الموحد.
3. اكتشاف واستلام Home Assistant Groups الأصلية.

# الوضع الافتراضي في 2.4.0

إذا كنت نقلت كل أدواتك القديمة وانتهيت منها، الإعداد المناسب هو:

```text
Enable legacy Eshtaya migration = Off
Legacy HACS cleanup = Off
Legacy service aliases = Off
```

عندما يكون Master Migration مطفأ، لا يبدأ النظام Migration جديدة تقوم عمدًا بـ:

- فحص Entity Manager / Multi-Way / Template Manager القديمة بغرض النقل.
- تعطيل Config Entry قديمة.
- نسخ Storage قديمة.
- حذف Config Entry قديمة.
- حذف HACS repositories قديمة.
- تسجيل أسماء Services القديمة كـaliases.

أما بياناتك الموجودة أصلًا داخل المنصة الموحدة فتتحمل طبيعيًا.

# إعدادات Migration

افتح:

```text
Settings → Devices & services → Eshtaya Smart Control → Configure
```

ستجد:

| الإعداد | الافتراضي | الوظيفة |
|---|---:|---|
| Enable legacy Eshtaya migration | Off | Master switch لأي Migration جديدة من الأدوات القديمة |
| Migrate old Entity Manager | On | يطبق فقط إذا كان الـMaster مفعّلًا |
| Migrate old Multi-Way / Smart Groups | On | يطبق فقط إذا كان الـMaster مفعّلًا |
| Migrate old Template Manager | On | يطبق فقط إذا كان الـMaster مفعّلًا |
| Legacy HACS cleanup | Off | حذف مستودعات HACS القديمة بعد نجاح التحقق |
| Legacy service aliases | Off | إبقاء توافق أسماء الخدمات القديمة |

الخيارات الفرعية مستقلة. إذا عطلت Entity Manager القديم من إعدادات Migration، المهاجر لا يفترض أن له الحق في نسخ أو Unload أو حذف هذا الدومين أثناء نقل أداة ثانية.

# استثناء أمان: Migration بدأت قبل 2.4

لا يجوز أن يؤدي إطفاء Migration الجديدة إلى ترك Transaction بدأ سابقًا في منتصف مرحلة حساسة.

لذلك إذا كانت Migration قد وصلت قبل التحديث إلى حالة مثل:

```text
prepared
legacy_disabled
validated
cleanup_partial
restart_required
```

يمكن للنظام السماح لها بالإكمال تلقائيًا حتى لو صار Master Migration الافتراضي Off في 2.4.

هذا الاستثناء فقط لإنهاء Cutover بدأ فعليًا؛ لا يعني Scan تلقائيًا جديدًا لكل الأدوات القديمة.

# Entity Manager / Multi-Way القديمة

عند تفعيل Migration عمدًا، المنسق:

1. يكتشف فقط الدومينات التي اخترت نقلها.
2. يقرأ Storage الخاصة بالأدوات المختارة فقط.
3. ينشئ Backup.
4. ينسخ البيانات إلى الهدف الموحد فقط ضمن شروط الأمان.
5. يعطل Config Entry القديمة المختارة قبل انتقال Ownership.
6. يتحقق من أعداد القواعد/المجموعات.
7. يحذف Config Entries المختارة فقط بعد نجاح Validation.
8. يعيد تفعيل القديم عند Rollback إذا فشل النقل.

أي Legacy component غير محدد خارج هذا Transaction.

# Template Manager القديم

Template Manager لديه Migration خاصة لأن العملية تتعامل مع Entity IDs دائمة من نوع:

```text
light.*
fan.*
```

عند تفعيلها يمكنها استرجاع mappings من runtime القديم أو ملفات مثل:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

ويتم إنشاء Rollback backup قبل أي Cleanup.

## restart_required

إذا بقيت الكيانات القديمة محملة داخل ذاكرة Home Assistant بعد إزالة تعريفاتها من القرص، لا ينشئ Eshtaya نسخ `_2`.

تبقى الكيانات الجديدة Deferred، ويكمل Restart التالي نفس Entity IDs بعد أن تختفي التعريفات القديمة من Runtime.

إذا كنت أصلًا في `restart_required` قبل التحديث، تعتبر هذه Migration قيد التنفيذ ويُسمح لها بالإكمال حتى لو كانت Migration الجديدة مطفأة افتراضيًا.

# HACS cleanup

أصبح خيارًا مستقلًا وOff افتراضيًا.

تشغيل Master Migration لا يعني تلقائيًا حذف مستودعات HACS. التنظيف لا يتم إلا عندما:

- يكون النقل في حالة مناسبة بعد Verification؛ و
- يكون `legacy_hacs_cleanup` مفعّلًا.

# Legacy service aliases

كذلك أصبحت مستقلة وOff افتراضيًا.

فعّلها فقط إذا كانت لديك Automations قديمة ما زالت تستدعي:

```text
eshtaya_multiway.*
eshtaya_template_manager.*
```

المشاريع الجديدة يجب أن تستخدم Services تحت `eshtaya_smart_control`.

# Home Assistant Groups ليست Legacy Migration

اكتشاف Group helpers الأصلية وعمل Transactional Take Over لها يبقى متاحًا بغض النظر عن Master Migration.

المسار مثلًا:

```text
Home Assistant Group helper
→ Eshtaya يكتشفها
→ أنت تختار Take Over
→ يتم فحص التوافق
→ يحافظ Eshtaya على Entity ID وRegistry metadata عندما يكون ذلك مدعومًا
```

هذا تحويل يدوي مقصود لإعداد حالي داخل Home Assistant، وليس نقلًا تلقائيًا من Custom Integration قديمة.

# الإعداد الموصى به بعد إنهاء كل النقل القديم

```text
legacy_migration_enabled = false
legacy_hacs_cleanup = false
legacy_service_aliases = false
```

اترك الخيارات الفرعية كما هي؛ لا تعمل طالما Master Migration مطفأ.

Native HA Group discovery وTake Over يظلان شغالين.

# Diagnostics

System Report يعرض فقط إعدادات Startup/Migration غير الحساسة وحالة Migration التاريخية بشكل Sanitized. لا يعرض Tuya credentials ولا محتويات Backup الخام.

إذا قررت تفعيل Migration قديمة لاحقًا، خذ Home Assistant Backup أولًا واحتفظ بـEshtaya migration backup حتى تتأكد أن Cutover مكتمل.
