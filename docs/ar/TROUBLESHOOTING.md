# استكشاف المشاكل — Troubleshooting

ابدأ دائمًا من العرض ثم انزل إلى السبب. لا تحذف الإضافة أو ملفاتها كأول خطوة؛ أغلب المشاكل يمكن تشخيصها بدون خسارة الإعدادات.

# 1. التاب ظاهر لكنه لا يفتح

إذا ضغطت على تبويب وظهرت:

```text
This role does not have access to that module.
```

راجع **Access Control** وEffective Permissions.

في 2.3.0 كان هناك خطأ محدد: Template Manager أُضيف إلى backend والـnavigation الجديد، لكن طبقة click قديمة كانت تستخدم View map لا تحتوي `template`. في 2.3.1 تم توحيد الخريطة وإضافة `template.view` لكل طبقات التنقل.

بعد تحديث 2.3.1:

```text
HACS Update
→ Restart Home Assistant
→ افتح الصفحة من جديد
```

رقم إصدار JavaScript تغير أيضًا لكسر الكاش القديم.

# 2. Template Manager القديم ما زال ظاهرًا

وجود ملفات أو sensor من الطريقة القديمة لا يعني أن عليك حذف Eshtaya Smart Control.

2.3.1 يبحث عن:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

كما يبحث عن Config Entry وRuntime Sensor وخدمات الـdomain القديم.

إذا تم اكتشاف Legacy ولكن الكيانات لا تتحرر من الذاكرة، الحالة تصبح:

```text
restart_required
```

وهذا يعني: ملفات القديم تم Backup لها وإزالتها، والجديد مؤجل لمنع duplicate. نفذ Restart واحد لـHome Assistant.

# 3. ظهر light.xxx_2 أو fan.xxx_2

لا تعِد تسمية الكيان الجديد مباشرة.

السبب غالبًا أن Entity ID الأصلي ما زال مملوكًا لكيان قديم في State Machine أو Entity Registry.

راجع:

- Migration state.
- Entity Registry owner/platform.
- هل القديم ما زال محملًا.
- هل تم إنشاء كيان يدوي أثناء Migration.

2.3.1 يمنع إنشاء الكيانات الجديدة في مرحلة `restart_required` تحديدًا لتجنب هذه الحالة.

# 4. Template Manager يعرض Missing

Missing تعني أن `source_entity` غير موجود بعد فترة حماية Startup.

لا تعتبر `unavailable` المؤقت وحده Missing دائمًا.

الحل:

1. تأكد أن Tuya/المصدر انتهى من التحميل.
2. اضغط Refresh.
3. ابحث عن Entity ID الجديد للمفتاح.
4. استخدم Suggested Relink أو Source لتغيير المصدر.
5. لا تغيّر Entity ID الدائم إذا لم تكن بحاجة لذلك.

# 5. Tuya لا تحمل أو الصفحة تبقى Loading

من تحسينات الإصدارات الحديثة:

- WebSocket frontend timeout محدود.
- قراءة البيانات لها retry آمن في الطلبات التي لا تغيّر الحالة.
- قائمة Tuya تستخدم lock لمنع refresh storms.
- يمكن استخدام آخر Cache ناجح في القراءة العادية إذا فشل Cloud مؤقتًا.
- Forced refresh يعرض الخطأ بدل إخفائه.

افحص:

- اتصال الإنترنت.
- Region/Endpoint.
- Client ID/Secret/UID.
- صلاحيات Tuya project.
- Logs Home Assistant.

# 6. Groups أو Entities لا تحمل أحيانًا

الواجهة تستخدم تحميلًا مستقلًا للوحدات. فشل Tuya مثلًا لا يجب أن يمنع Entity Control أو Multi-Way من فتح Shell.

Multi-Way يستخدم `Promise.allSettled` في عمليات القراءة الأساسية وdebounce للأحداث لمنع تراكب refresh متكرر.

إذا بقي قسم معين لا يحمل:

- افتح Browser Console.
- ابحث عن أول Error قبل الرسائل التابعة له.
- راجع WebSocket error message.
- راجع Home Assistant Logs للـbackend المقابل.

# 7. ملفات Alexa غير متزامنة

يجب أن يكون الملفان المدَاران متطابقين:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

استخدم **System Center → Repair Alexa Files** أو عملية regeneration من Entity Control.

# 8. Multi-Way يستجيب مرتين أو يتذبذب

راجع:

- Mode الصحيح للـcontroller.
- debounce.
- cloud echo guard.
- physical priority.
- settle/source stable settings.
- output confirmation/retries.
- Activity history لمعرفة من أرسل كل أمر.

لا تعالج التكرار بإضافة delays عشوائية قبل معرفة مصدر الأمرين.

# 9. الصلاحية موجودة لكن API يرفض

هناك طبقتان:

- Eshtaya permission.
- Home Assistant native permission على الكيان/الحساب في بعض العمليات.

قد يملك المستخدم `entity.manage` داخل Eshtaya لكن Home Assistant نفسه يمنع Edit لكيان لا يملك عليه POLICY_EDIT.

راجع Effective Permissions في Eshtaya ودور المستخدم في Home Assistant.

# 10. بعد تحديث HACS الواجهة قديمة

الإصدار يضاف إلى رابط الملف:

```text
smart-control-panel-v23.js?v=<VERSION>
```

2.3.1 يغيّر VERSION وبالتالي يجب تحميل asset جديد بعد Restart.

إذا لم يتغير:

- تأكد أن HACS ثبت فعلًا 2.3.1.
- Restart Home Assistant.
- اعمل Refresh للمتصفح.
- افحص Network tab إذا لزم وتأكد أن `?v=2.3.1` مستخدم.

# ما المعلومات التي ترسلها عند وجود خطأ؟

أرسل:

1. إصدار Home Assistant.
2. إصدار Eshtaya Smart Control.
3. اسم التبويب/الوحدة.
4. نص الخطأ كاملًا.
5. Browser Console إذا كان UI issue.
6. Home Assistant Log trace إذا كان backend issue.
7. Migration state إذا كانت المشكلة مرتبطة بالنقل.
8. هل التثبيت Update فوق نسخة سابقة أم تثبيت جديد.

لا ترسل Tuya Client Secret أو access tokens.
