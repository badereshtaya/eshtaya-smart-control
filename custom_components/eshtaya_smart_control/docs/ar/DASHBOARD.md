# لوحة التحكم — Dashboard

لوحة التحكم هي الصفحة التشغيلية الرئيسية لـ **Eshtaya Smart Control**. الهدف منها إعطاؤك صورة سريعة عن حالة المنصة قبل الدخول إلى التفاصيل.

## ماذا تعرض؟

حسب الصلاحيات الممنوحة للمستخدم، يمكن أن تعرض اللوحة:

- إصدار Eshtaya Smart Control.
- إصدار Home Assistant.
- Health Score عام.
- عدد الكيانات وحالة unavailable.
- عدد الكيانات المستثناة من Alexa.
- حالة Tuya وهل الحساب مفعّل أم لا.
- عدد مجموعات Multi-Way وSmart Groups.
- عدد الكيانات الدائمة في Template Manager.
- Recommendations مبنية على حالات فعلية داخل النظام.
- اختصارات للوحدات التي يملك المستخدم صلاحية دخولها.

## Health Score

الـHealth Score ليس اختبارًا سحريًا لكل Home Assistant؛ هو تقييم تشغيلي مبني على المؤشرات التي تعرفها الإضافة، مثل:

- ملفات Alexa غير متزامنة.
- عدد كبير من الكيانات unavailable.
- مجموعات Multi-Way أو Smart Groups في حالة degraded.
- Migration تحتاج انتباه.
- مشاكل في Template Manager مثل مصدر مفقود.
- حالة Tuya عندما تكون مفعّلة.

استخدم الرقم كإشارة للبحث، وليس كبديل عن Logs Home Assistant.

## Recommendations

التوصيات محلية Deterministic ولا ترسل حالة المنزل إلى خدمة AI خارجية. كل Recommendation ناتجة عن شرط معروف ويمكن ربطها بوحدة إصلاح مناسبة.

أمثلة:

- Alexa files need repair.
- Migration requires attention.
- Group health is degraded.
- Tuya is not configured.
- System appears healthy.

## بطاقات الوحدات

كل بطاقة تمثل وحدة داخل المنصة. البطاقة تظهر فقط إذا كان لدى المستخدم صلاحية الـView الخاصة بها.

خريطة الصلاحيات الأساسية:

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

ابتداءً من 2.3.1 أصبح الـFrontend يستخدم نفس خريطة الصلاحيات الحالية بدل قائمة قديمة ثابتة كانت قد تسبب رسالة:

```text
This role does not have access to that module.
```

رغم أن المستخدم يملك الصلاحية فعليًا.

## لماذا قد لا تظهر بعض البطاقات؟

إذا لم تظهر بطاقة، افحص:

1. هل المستخدم Home Assistant Admin؟ المدير يحصل على صلاحيات Eshtaya كاملة.
2. إذا كان مستخدمًا عاديًا، افتح **Access Control** وتأكد من الدور.
3. افحص `Effective permissions` للمستخدم وليس اسم الدور فقط.
4. راجع Force Allow / Force Deny.
5. إذا تم تعديل الدور الآن، اعمل Refresh للواجهة حتى يتم جلب access profile الجديد.

## الفرق بين Dashboard وSystem Center

Dashboard مخصصة للملخص والتنقل السريع.

System Center أعمق ويحتوي على:

- Actions تشغيلية.
- تقارير.
- Migration state.
- File health.
- تشخيصات أكثر تفصيلًا.

إذا ظهر Warning في Dashboard، المكان الطبيعي للتفصيل غالبًا هو System Center أو الوحدة المرتبطة بالتحذير.

## بعد HACS Update

ملفات الواجهة تُقدّم مع Cache Headers، لذلك رقم الإصدار يضاف إلى رابط JavaScript. في 2.3.1 تغيّر رقم النسخة حتى يجبر المتصفح وHome Assistant على تحميل الواجهة الجديدة بعد Restart.

المسار الموصى به:

```text
HACS Update → Restart Home Assistant → افتح اللوحة
```

إذا ظهرت عناصر قديمة بعد ذلك، Refresh للمتصفح يكفي عادة ولا يلزم حذف الإضافة.
