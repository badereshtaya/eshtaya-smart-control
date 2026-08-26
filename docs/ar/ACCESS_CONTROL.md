# الصلاحيات — Access Control

Eshtaya Smart Control يحتوي على **طبقتين مختلفتين من الصلاحيات**. فهم الفرق بينهما مهم حتى لا تعطي مستخدمًا صلاحية أكبر من المطلوب أو تتوقع من دور Eshtaya أن يغير قدرات Home Assistant Core غير المدعومة.

# 1. صلاحيات Eshtaya Smart Control

هذه الصلاحيات تتحكم بما يستطيع المستخدم رؤيته أو تنفيذه **داخل وحدات Eshtaya Smart Control**.

الصلاحيات الحالية تشمل:

```text
dashboard.view
entity.view
entity.manage

tuya.view
tuya.control
tuya.configure

multi.view
multi.control
multi.manage

template.view
template.manage

docs.view

system.view
system.actions
system.reports

access.manage
```

## الأدوار الجاهزة

### No Access

لا يعطي أي صلاحية داخل منصة Eshtaya.

### Viewer

مشاهدة Dashboard والوحدات الأساسية بدون صلاحيات تعديل.

### Operator

مشاهدة وتحكم تشغيلي في الوحدات التي تحتاج تشغيل يومي، بدون فتح كل إعدادات الإدارة.

### Technician

صلاحيات فنية واسعة لإدارة الكيانات والمجموعات وTemplate Manager والتشخيص.

### Platform Manager

كل صلاحيات Eshtaya Smart Control.

مدير Home Assistant الحقيقي يحصل دائمًا على كل صلاحيات Eshtaya ولا يمكن خفضها من داخل هذا النظام.

## Force Allow وForce Deny

يمكن تعديل صلاحيات مستخدم فوق الدور الأساسي:

- **Force Allow** يضيف Permission محددة.
- **Force Deny** يمنع Permission محددة.

Effective Permissions هي النتيجة النهائية بعد دمج الدور والاستثناءات.

## صلاحيات مؤقتة

يمكن تحديد وقت انتهاء Assignment للمستخدم. بعد انتهاء الوقت يعود المستخدم إلى الدور الافتراضي/الحالة غير المعينة حسب الإعداد.

# 2. صلاحيات Home Assistant Core

هذا القسم يؤثر على الحساب الحقيقي داخل Home Assistant، وليس فقط Eshtaya Smart Control.

الإضافة تستخدم قدرات Core المدعومة مثل مجموعات:

- Administrator
- User
- Read Only

وقد تعرض خيارات أخرى فقط عندما تكون قابلة للتطبيق بأمان في إصدار Home Assistant الحالي.

## ماذا تعني Administrator؟

Administrator يملك إدارة Home Assistant الكاملة تقريبًا حسب Core، بما في ذلك صفحات إعدادات وخدمات إدارية لا تتحكم بها Eshtaya وحدها.

لا تعطِ Administrator لمستخدم فقط لأنه يحتاج تشغيل إضاءة أو فتح تبويب معين.

## User

حساب Home Assistant عادي. ما زالت صفحات وإجراءات المدير محمية من Core.

## Read Only

يعتمد على مجموعة القراءة فقط الأصلية في Home Assistant، ويقيد التحكم حسب سياسة Core.

# حدود Home Assistant الحالية

Home Assistant لا يوفر حاليًا HACS API عامًا ومدعومًا لإنشاء نظام RBAC كامل مخصص لكل Service وDashboard مع Explicit Deny rules كما في أنظمة المؤسسات.

لذلك Eshtaya لا تدعي شيئًا غير موجود في Core. هناك فرق بين:

- **Core account role**: يطبقه Home Assistant نفسه.
- **Eshtaya module permission**: يطبق على APIs وواجهة Eshtaya.

## لماذا كانت تظهر رسالة

```text
This role does not have access to that module.
```

في 2.3.0 تمت إضافة `template.view` في الـbackend، لكن إحدى طبقات الواجهة القديمة كانت ما تزال تستخدم خريطة Views من إصدار أقدم لا تحتوي `template`. لذلك كان يمكن أن يظهر التاب لأن طبقة v2.3 تعرف الصلاحية، ثم تمنع طبقة click قديمة الدخول لأنها لا تعرف اسم التاب.

في 2.3.1 تم توحيد خريطة الـViews مع صلاحيات backend الحالية، وإضافة Template Manager إلى:

- قائمة الـView permissions.
- قائمة الأدوار.
- Permission labels.
- أول صفحة مسموحة للمستخدم.
- حماية click/navigation.

وبذلك الرسالة يجب أن تظهر فقط عندما **Effective Permissions** لا تحتوي فعلًا على Permission المطلوبة.

# حماية Backend

إخفاء زر في الواجهة ليس حماية كافية. العمليات الحساسة في Eshtaya يتم فحصها في الـbackend أيضًا.

مثال Template Manager:

```text
template.view   → snapshot / scan
template.manage → create / edit / delete / relink
```

وفي 2.3.1 يوجد Migration Lock إضافي داخل backend يمنع تعديل Template mappings أثناء النقل حتى لو حاول أحد استدعاء WebSocket أو Service مباشرة.

# قواعد أمان مهمة

- لا يمكن استخدام دور Eshtaya لرفع مستخدم عادي إلى Home Assistant Admin من واجهة غير مصرح بها.
- لا تعدل Owner بنفس قواعد مستخدم عادي.
- اختبر الصلاحيات بحساب غير Admin قبل التسليم.
- لا تعتمد على إخفاء التاب وحده؛ تحقق من Effective Permissions.
- بعد تعديل Role اعمل Refresh للواجهة حتى تجلب Access Profile الجديد.

# تشخيص مشكلة صلاحية

إذا مُنع مستخدم من تبويب:

1. افتح Access Control بحساب Home Assistant Admin.
2. ابحث عن المستخدم.
3. افحص Role.
4. افحص Force Allow وForce Deny.
5. افحص Effective Permissions.
6. تأكد أن Permission المطلوبة موجودة حسب الخريطة التالية:

```text
Dashboard        → dashboard.view
Entity Control   → entity.view
Tuya             → tuya.view
Multi-Way        → multi.view
Template Manager → template.view
Documentation    → docs.view
System Center    → system.view
Access Control   → access.manage
```

إذا كانت Effective Permission موجودة وما زالت الواجهة تمنع الدخول على 2.3.1، راجع Logs والـbrowser console لأن ذلك يصبح خطأ يجب الإبلاغ عنه، وليس سلوكًا مقصودًا.
