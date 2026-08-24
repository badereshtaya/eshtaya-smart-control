"""Complete packaged in-app documentation for Eshtaya Smart Control v2.2."""
from __future__ import annotations

DOCUMENTATION = {
    "ar": {
        "GETTING_STARTED": r"""# البدء والتثبيت — الدليل الكامل

## ما هي Eshtaya Smart Control؟
Eshtaya Smart Control هي منصة إدارة موحدة داخل Home Assistant تجمع عدة أدوات كانت موزعة سابقاً: إدارة الكيانات وأسماء Alexa، إدارة Tuya Cloud، محرك Multi-Way، Smart Groups وAction Groups، Commissioning، مركز الصحة والتقارير، الهجرة من إضافات Eshtaya القديمة، والتوثيق والصلاحيات.

الهدف أن تبقى كل العمليات داخل Home Assistant، وأن تكون الأدوات الحساسة محمية في الـBackend وليس فقط مخفية من الواجهة.

## المتطلبات قبل التثبيت
1. استخدم إصدار Home Assistant المتوافق مع الإصدار المكتوب في `hacs.json`.
2. حدّث HACS إلى إصدار حديث.
3. خذ Full Backup من Home Assistant قبل أول تثبيت أو قبل ترقية كبيرة.
4. إذا عندك إضافات Eshtaya القديمة فلا تحذفها يدوياً قبل أول تشغيل؛ Migration Center يحتاج أن يكتشفها ويأخذ نسخة منها قبل النقل.
5. تأكد أن `/config` قابل للكتابة لأن Entity/Alexa Control يولّد ملفات YAML هناك.
6. Tuya اختيارية تماماً؛ لا تحتاج أي بيانات Tuya كي تثبت المنصة أو تستخدم باقي الأقسام.

## التثبيت من HACS
1. افتح HACS.
2. افتح Integrations.
3. ابحث عن Eshtaya Smart Control، أو أضف المستودع إذا كان ما زال Custom Repository.
4. اختر الإصدار المطلوب وثبته.
5. أعد تشغيل Home Assistant بالكامل، وليس Reload للواجهة فقط.
6. افتح Settings → Devices & Services → Add Integration.
7. ابحث عن Eshtaya Smart Control وأنشئ الـConfig Entry الوحيد.

المنصة مصممة على Single Config Entry؛ لا تنشئ أكثر من نسخة لنفس Home Assistant.

## ماذا يحدث عند أول تشغيل؟
الـBackend يهيئ الوحدات بهذا التسلسل العام:
- Access Control metadata.
- Native Home Assistant Access manager.
- Migration Center.
- Entity/Alexa manager.
- Tuya manager بدون إجبار التفعيل.
- Multi-Way وSmart Groups.
- Control Hub frontend.

إذا اكتشفت المنصة إضافات Eshtaya القديمة تدخل Migration Center في مسار آمن: Detect → Backup → Copy → Quiesce → Runtime Start → Validate → Remove Legacy Entries → Reconcile → HACS Cleanup. لا يتم حذف القديم قبل نجاح التحقق.

## أول خمس دقائق بعد التثبيت
### 1. افتح Dashboard
تأكد أن الصفحة الرئيسية تظهر إصدار المنصة وحالة الصحة. في v2.2 كل Module يحمل بشكل مستقل؛ تعطل Tuya مثلاً يجب ألا يمنع فتح Groups أو Entity/Alexa.

### 2. افتح Entity & Alexa
تأكد أن قائمة الكيانات ظهرت وأن عداد Total Entities منطقي. لا تعمل Bulk operations قبل التأكد من القواعد الحالية.

### 3. افتح Groups
إذا عندك Multi-Way قديم، انتظر حتى ينتهي Startup Protection ثم راجع Health. حالة Recovering في أول الإقلاع ليست خطأ بحد ذاتها.

### 4. افتح System Center
راجع Health Score، Migration state، Alexa file sync وأي Recommendation.

### 5. افتح Access Control
إذا عندك مستخدمين غير المدير، قرر شيئين منفصلين لكل مستخدم:
- ماذا يستطيع أن يرى/يتحكم به في Home Assistant نفسه.
- ما الأقسام التي يستطيع استخدامها داخل Eshtaya Smart Control.

## تفعيل Tuya لأول مرة
افتح Tuya Control ثم Account Settings. تحتاج:
- Region / Data Center.
- Client ID.
- Client Secret.
- UID.

استخدم Test Connection قبل Save. الـClient Secret يبقى في Config Entry ولا يعاد للواجهة بعد الحفظ. إذا لم تحتج Tuya اتركها غير مفعلة؛ بقية المنصة تعمل طبيعياً.

## بعد كل Update
1. حدث من HACS.
2. أعد تشغيل Home Assistant.
3. اعمل Hard Refresh للمتصفح (`Ctrl+F5`) إذا بقيت واجهة قديمة.
4. افتح System Center وتأكد من Version.
5. راجع Groups Health وEntity/Alexa وTuya.
6. إذا كان التحديث يغير الصلاحيات، راجع Access Control ولا تفترض أن المستخدمين أخذوا صلاحيات جديدة تلقائياً.

## كيف تعرف أن التثبيت سليم؟
التثبيت السليم يعني:
- لا توجد أخطاء Setup للإضافة في Logs.
- Control Hub يفتح.
- كل Module يفتح بشكل مستقل.
- HACS/Hassfest validation للإصدار ناجح.
- Multi-Way لا يبقى Recovering بعد انتهاء فترة الحماية إلا إذا هناك جهاز فعلاً غير متاح.
- Alexa YAML sync إما Healthy أو يظهر سبب واضح يمكن إصلاحه.
- Tuya، إذا مفعلة، تعرض Last Success أو الأجهزة من Cache عند انقطاع مؤقت.
""",

        "DASHBOARD": r"""# لوحة التحكم — شرح كل جزء

## وظيفة Dashboard
Dashboard ليست مكان التحكم التفصيلي بالأجهزة؛ هي شاشة تشغيلية سريعة تخبرك هل المنصة سليمة وأي وحدة تحتاج اهتمام. من هنا تدخل إلى Entity/Alexa، Tuya، Groups، Documentation، System Center وAccess Control حسب صلاحية المستخدم.

## Version
الرقم أعلى الصفحة هو إصدار Eshtaya Smart Control المحمّل فعلياً من ملفات الـFrontend. بعد تحديث HACS إذا بقي الرقم قديماً، أعد تشغيل Home Assistant ثم Hard Refresh.

## Health Score
Health Score رقم تشخيصي من 0 إلى 100، وليس بديلاً عن Home Assistant Repairs أو Logs. يتأثر عادةً بـ:
- Migration فاشلة أو غير مكتملة.
- Alexa files غير متزامنة.
- نسبة كيانات Unavailable.
- Multi-Way groups متدهورة.
- Smart Groups متدهورة.

Tuya غير المفعلة لا تعتبر خطأ؛ هي Module اختيارية.

## بطاقات الوحدات
### Entity & Alexa
تعرض عدد الكيانات إذا كانت صلاحية `entity.view` موجودة. فتح البطاقة ينقلك إلى إدارة الكيانات والقواعد.

### Tuya
تعرض Activated / Not Activated حسب إعداد الحساب. تعطل Tuya Cloud لا يجب أن يوقف Dashboard أو أي Module آخر في v2.2.

### Groups
تعرض مجموع Multi-Way + Smart Groups. الرقم لا يعني أن كل الجروبات Healthy؛ افتح القسم لرؤية Health وDiagnostics.

### Documentation
تعرض عدد الأدلة المضمنة في الإصدار. محتوى التوثيق يأتي من Backend عبر WebSocket، وليس من رابط Static `/docs`.

### System Center
تعرض Health Score وتفتح أدوات التقرير والصيانة.

### Access Control
للـHome Assistant administrators تظهر أدوات صلاحيات Home Assistant الأصلية، إضافة إلى صلاحيات أقسام Eshtaya.

## التحميل المستقل في v2.2
الـDashboard في v2.2 لا ينتظر كل البيانات حتى يرسم الصفحة. Profile permissions تتحمل أولاً، ثم Overview تتحمل بشكل مستقل. إذا Overview فشلت ترى رسالة Retry بدل شاشة معلقة.

كل Child Module يستعمل WebSocket timeout محدد. الطلبات الآمنة للقراءة يمكن إعادة محاولتها مرة، أما أوامر الكتابة والتحكم فلا يعاد إرسالها تلقائياً حتى لا يتكرر أمر فعلي مرتين.

## زر Refresh
زر Refresh العام يعيد Overview ويحاول تحديث الوحدة المفتوحة. لا يستخدم كبديل عن Restart بعد تثبيت ملفات جديدة؛ Restart مطلوب عند تحديث Python integration.

## اللغة
Auto يتبع لغة Home Assistant. Arabic وEnglish يثبتان اختيار مستقل في Local Storage للمتصفح. تغيير اللغة لا يغير أسماء الكيانات أو أسماء الأجهزة المخزنة.

## ماذا أفعل عند رسالة Timeout؟
- إذا كانت Tuya: انتظر قليلاً واضغط Refresh؛ قد يتم عرض آخر Cache ناجحة.
- إذا كانت Groups: افتح Logs إذا تكرر؛ الواجهة لن تطلق Refreshات متداخلة بلا حد.
- إذا كانت Entity: اضغط Refresh. إذا تكرر، راجع Logs وEntity Registry.
- إذا كل الأقسام Timeout بنفس الوقت، المشكلة غالباً اتصال المتصفح بـHome Assistant WebSocket وليست Module محددة.
""",

        "ENTITY_CONTROL": r"""# إدارة الكيانات وAlexa — الدليل التفصيلي

## الفكرة
هذا القسم يجمع Entity Registry data وحالة الكيانات وقواعد إظهارها في Alexa. التعديل هنا لا يغير `entity_id` عشوائياً؛ تغيير الاسم يستخدم واجهات Home Assistant المناسبة، وقواعد Alexa تُخزن في Storage ثم يولد منها ملفا `hidden_entities.yaml`.

## تبويب Entities
كل سطر يمثل كياناً. المعلومات الرئيسية:
- Friendly Name / Custom Name.
- Entity ID.
- Domain مثل `light`, `switch`, `sensor`.
- Device وArea إن وجدا.
- Availability.
- قاعدة Alexa الفعلية.

### البحث
يبحث في Entity ID والاسم واسم الجهاز والمنطقة والمنصة. البحث لا يغير أي بيانات.

### الفلاتر
يمكن فلترة:
- Domain.
- Area.
- Platform.
- Available / Unavailable.
- Included / Excluded.
- Overrides only.

### حالات Alexa
#### Automatic / Inherit
لا يوجد Override خاص للكيان. القرار يأتي من Domain rules + Default categories + Keywords.

#### Force Allow / Show
يفرض ظهور الكيان حتى لو كانت القاعدة العامة تخفي نوعه، ضمن منطق Entity Manager.

#### Force Exclude / Hide
يفرض إخفاء الكيان.

أي تغيير في Rule يعيد توليد ملفات Alexa لضمان أن Storage والملف متوافقان.

## تغيير الاسم
حقل Rename يغير الاسم المخصص للكيان في Entity Registry إذا كان الكيان مسجلاً هناك. Reset يعيد الاعتماد على الاسم الأصلي. الكيانات الموجودة فقط في State Machine بدون Registry entry لا يمكن Rename لها من هذه الشاشة.

لا يوجد زر Save عام لجدول الكيانات: عمليات Rename وAlexa Rule تحفظ مباشرة عند تنفيذها.

## التحديد الجماعي
يمكن تحديد عدة كيانات ثم وضع Rule واحد عليها. قبل Bulk change:
1. استخدم Filter لتتأكد من المجموعة المستهدفة.
2. راجع عدد Selected.
3. إذا العدد كبير، خذ Export للقواعد أولاً.
4. نفذ التعديل.
5. افتح Alexa File وتأكد من النتيجة.

## تبويب Devices
يجمع الكيانات حسب الجهاز ليسهل فهم أي Device يملك أي Entities. هذا العرض لا يغير Device Registry ownership.

## تبويب Rules
### Domain Rules
تحدد هل Domain كامل مسموح افتراضياً أو مخفي. مثال: إذا عطلت `sensor`، الكيانات التي تعمل Inherit تخضع للقاعدة، بينما Force Allow يمكنه استثناء كيان محدد وفق منطق النظام.

### Automatic Categories
Categories مثل diagnostic/config يمكن استثناؤها تلقائياً. هذه تطبق فقط على Inherit.

### Keywords
كلمات يتم البحث عنها في الاسم وEntity ID لاستثناء كيانات غير مرغوبة من Alexa. استخدم كلمات دقيقة؛ كلمة عامة جداً قد تخفي كيانات أكثر مما تريد.

## تبويب Alexa File
يعرض المحتوى الناتج من القواعد. النظام يحافظ على نسختين:
- `/config/hidden_entities.yaml`
- `/config/www/hidden_entities.yaml`

وجود نسختين هدفه التوافق مع الاستهلاك المحلي والـWWW. System Center يقارن SHA256 للنسختين. إذا اختلفتا يظهر File Sync warning.

### Regenerate
يعيد بناء الملف من Storage. لا يعتمد على التعديلات اليدوية داخل YAML.

### Repair Sync
يعيد توليد النسختين ويعيد فحصهما.

## Import / Export
Export يحفظ القواعد بصيغة يمكن استرجاعها. Import يجب استخدامه بعد مراجعة الملف. الاستيراد الكبير يغير Rules ولذلك يفضل Full Backup قبل العملية.

## Cleanup Orphans
Orphan Rule هي قاعدة مخزنة لكيان لم يعد موجوداً في State Machine أو Registry حسب منطق المدير. Cleanup يحذف القواعد اليتيمة فقط؛ لا يحذف أجهزة أو كيانات من Home Assistant.

## الصلاحيات
داخل Eshtaya يوجد:
- `entity.view`: فتح وعرض القسم.
- `entity.manage`: تعديلات Eshtaya المتعلقة بالأسماء والقواعد.

وفوق ذلك يمكن أن يكون للمستخدم Native Home Assistant entity policy من Access Control. صلاحيات Home Assistant الأصلية هي المرجع عند التحكم الطبيعي بكيانات HA.

## إذا الصفحة بقيت Loading
v2.2 يضع WebSocket timeout بدلاً من انتظار أبدي. إذا فشل Get تظهر Error/Toast وتستطيع Refresh. إذا تكرر:
- راجع Logs باسم `eshtaya_smart_control`.
- تأكد أن Entity Registry يعمل.
- تأكد أن Home Assistant WebSocket نفسه متصل.
- لا تعتبر Tuya سبباً تلقائياً؛ Entity/Alexa لا يعتمد على Tuya Cloud حتى يفتح.
""",

        "TUYA_CONTROL": r"""# إدارة Tuya Cloud — الدليل الكامل

## لماذا يوجد هذا القسم؟
Tuya Control يسمح بإدارة معلومات أجهزة Tuya Cloud من داخل Home Assistant بدون صفحة PHP خارجية. هو Module اختيارية ولا يجب أن تمنع المنصة من العمل إذا الحساب غير مفعّل أو Tuya Cloud متوقفة.

## Account Settings
### Region
اختر Data Center المطابق لمشروع Tuya Cloud. الخيارات تشمل Central Europe، Western Europe، America، China، India، Singapore وCustom endpoint.

اختيار Region غلط قد يعطي Token ناجح أحياناً لكن لا يعيد أجهزة UID الصحيحة، أو يفشل بالكامل.

### Client ID
Access ID من Tuya Cloud Project.

### Client Secret
سر المشروع. بعد حفظه لا يعاد إرساله للواجهة. إذا فتحت Settings لاحقاً سيظهر الحقل فارغاً/Masked؛ تركه فارغاً أثناء تعديل إعداد آخر يعني الاحتفاظ بالسر المخزن.

### UID
معرف المستخدم الذي ترتبط به الأجهزة في المشروع.

### Test Connection
يطلب Token ثم يجرب endpoint قائمة أجهزة المستخدم. لا يحفظ الإعدادات إذا كنت فقط تختبر.

### Save / Activate
يفحص الإعدادات ثم يخزنها في Config Entry ويعيد تهيئة Client. أول تفعيل يحفظ `activated_at`، وكل تعديل يحفظ `updated_at`.

### Deactivate
يمسح إعدادات Tuya فقط ولا يحذف Config Entry الرئيسي ولا Multi-Way ولا Entity Manager.

## قائمة الأجهزة
تظهر:
- Name.
- Device ID.
- Online / Offline.
- Category.
- Product ID.
- Icon إذا توفر.

يمكن البحث بالاسم، Device ID، Category أو Product ID، والفلترة Online/Offline/Category.

## Cache في v2.2
القائمة تحفظ آخر نتيجة ناجحة لفترة قصيرة. التحسينات المهمة:
- يوجد Lock يمنع أكثر من Cloud refresh في نفس الوقت.
- إذا عدة أجزاء طلبت القائمة بنفس اللحظة، الطلبات تتشارك التسلسل بدل عمل Storm على Tuya API.
- Normal page load يستطيع استخدام آخر Cache ناجحة إذا Tuya Cloud أعطت خطأ مؤقتاً.
- Full Refresh الإجباري لا يخفي الخطأ؛ إذا فشل يخبرك أن التحديث الإجباري لم ينجح.
- Status يحتوي Last Success وLast Error بدون أي Secrets.

هذا يعني أن انقطاع Tuya مؤقتاً لا يجب أن يجعل الصفحة عالقة للأبد ولا يجب أن يؤثر على Groups أو Alexa page.

## Edit Device
عند فتح جهاز يتم طلب Device Details وShadow Properties. هذه طلبات Cloud وقد تكون أبطأ من القائمة.

### Device Name
يحدث اسم الجهاز في Tuya Cloud. بعد التعديل يتم إبطال Cache حتى تأتي القائمة الجديدة بالاسم الصحيح.

### Property Custom Name
لبعض Shadow properties يمكن حفظ Custom Name. الكود الأساسي للـDP لا يتغير؛ يتم تعديل الاسم المخصص فقط.

## Bulk Edit
يجلب تفاصيل مجموعة أجهزة بتزامن محدود حتى لا يفتح عشرات الطلبات دفعة واحدة. Semaphore في الـBackend يحد الحمل. النتيجة لكل Device مستقلة؛ فشل جهاز لا يعني بالضرورة فشل كل Bulk request.

## Timeouts
Tuya Cloud request في الـBackend لها Timeout، والـFrontend v2.2 لديه Timeout أكبر قليلاً حتى يستقبل خطأ الـBackend بشكل طبيعي. القراءة الآمنة يمكن Retry لها مرة؛ PUT/POST لا يعاد إرسالها تلقائياً حتى لا يتكرر تعديل الاسم مرتين.

## أخطاء شائعة
### Token failed
راجع Client ID / Secret / Region وTuya Project authorization.

### No devices
راجع UID وData Center وأن الأجهزة مرتبطة بنفس Cloud Project.

### Permission denied من Tuya
فعّل APIs المطلوبة في Tuya IoT Platform للمشروع.

### Connection timed out
مشكلة شبكة أو Tuya Cloud. الصفحة لن تنتظر بلا نهاية. إذا لديك Cache سابقة قد تظهر الأجهزة القديمة في Normal load.

### Invalid JSON
Tuya أو Proxy أعاد Response غير JSON. راجع Endpoint وReverse proxy/network.

## الأمان
- Client Secret لا يظهر في System Report.
- Access tokens لا تحفظ في Documentation أو Audit log.
- `tuya.configure` مخصصة لإعداد الحساب.
- `tuya.control` لتعديلات الأسماء/Properties.
- `tuya.view` للعرض.
""",

        "MULTIWAY": r"""# Multi-Way Control — شرح المحرك والإعدادات

## ما هو Multi-Way؟
Multi-Way يربط خرجاً فعلياً واحداً `Output` مع Controller واحد أو أكثر بحيث يتصرف النظام مثل 2-way/3-way/multi-way إلكتروني. الهدف أن أي تغيير فعلي أو برمجي يُفهم كمصدر واحد ثم تنتشر الحالة المطلوبة بدون Feedback loops أو اهتزاز مستمر.

## مكونات الجروب
### Name
اسم إداري واضح مثل `Living Main Light Multi-Way`.

### Physical Output
الكيان الذي يمثل الحمل الفعلي أو المرجع الرئيسي. يجب أن يكون كياناً يمكن للمحرك التحكم به.

### Controllers
الأزرار أو الكيانات الفرعية التي تُراقب لتوليد أمر أو تعكس الحالة.

### Virtual Type
نوع الكيان الافتراضي الذي ينشئه النظام للجروب إذا كان ذلك جزءاً من الإعداد.

### Area
منطقة Home Assistant للمساعدة في التنظيم والـCommissioning.

## Controller Modes
### Mirror
حالة Controller ON/OFF تعني الحالة المطلوبة نفسها.

### Toggle
أي Edge معتبر يبدل الحالة الحالية.

### Momentary ON
النبضة ON فقط تعتبر كبسة Toggle.

### Momentary OFF
النبضة OFF فقط تعتبر كبسة Toggle.

### Event
تغير الحدث يستخدم كنبضة.

### Follow
Controller يتبع Output ولا يملك سلطة تغيير الحمل بنفس منطق Toggle.

### Invert
يعكس معنى ON/OFF للكيان المحدد.

### Reflect State
يحدد هل يجب أن يحاول النظام إرجاع حالة المجموعة إلى Controller بعد تنفيذ الأمر.

## سرعة الاستجابة
### Instant
الأسرع. يرسل المسار المطلوب بسرعة ويعمل التحقق بالخلفية. مناسب للأجهزة المحلية السريعة.

### Balanced
يتأكد من Output بدرجة أكبر قبل مزامنة Followers. غالباً هو الخيار الأفضل للأجهزة Cloud أو التركيبات المختلطة.

### Safe
ينتظر تأكيدات أكثر. أبطأ لكنه مفيد أثناء Commissioning أو مع أجهزة غير موثوقة.

## Debounce
مدة تتجاهل تغيرات متقاربة جداً كي لا تعتبر Bounce أو Echo كبسات مستقلة. رفعها كثيراً يجعل الضغط السريع لا يُلتقط؛ خفضها كثيراً قد يسمح بالتكرار.

## Manual / Physical Priority
نافذة تعطي آخر تغيير فعلي أولوية على Echo أو أوامر متأخرة. الهدف أن "آخر كبسة فعلية تربح" بدل أن يرجع Cloud acknowledgement قديم ويعكسها.

## Rapid Settle وSource Stable
إعدادات تثبيت المصدر بعد التغييرات السريعة. تستخدم لمنع Final Sync مبكر قبل أن يستقر آخر تغيير.

## Command Timeout
كم ينتظر المحرك تأكيد الحالة بعد Service call قبل اعتباره Failure.

## Retries
عدد محاولات إعادة تنفيذ أمر لم يتأكد. لا ترفع الرقم بلا داعٍ مع أجهزة Cloud لأن ذلك قد يضاعف الأوامر.

## Auto Heal
إذا عضو خرج عن الحالة أو فشل، Auto Heal يسمح بمحاولة استرجاع التزامن ضمن سياسة المحرك.

## Restore Policy
### Adopt Physical Output
بعد Restart يعتمد الحالة الفعلية الموجودة على Output كمرجع.

### Enforce Last Desired
يحاول فرض آخر Desired state محفوظة. استخدمه فقط إذا متأكد أن الحالة المحفوظة يجب أن تكون المرجع بعد الإقلاع.

## Fallback Output
خرج احتياطي اختياري. في v2.1+ لا يمنع Fallback غير الموجود Startup readiness للخرج الأساسي؛ هو اختياري وليس Required dependency.

## Startup Protection في v2.2
تكاملات Cloud، خصوصاً Tuya، قد تستغرق وقتاً بعد Restart حتى تعيد States. لذلك المحرك:
1. يبدأ بوضع Recovering.
2. لا يصدر Missing Repairs مباشرة.
3. يفحص State Machine وEntity Registry.
4. ينتظر Required Output/Controllers ضمن Startup grace.
5. يعيد الفحص دورياً.
6. بعد انتهاء الحماية يطبق التشخيص الطبيعي.

هذا يمنع Warning كاذب لمجرد أن Entity لم تسترجع State بعد.

## Health states
- Healthy: الجروب يعمل ومتزامن.
- Recovering: Startup أو استرجاع مؤقت.
- Degraded: يوجد Failure أو عضو غير سليم.
- Out of Sync: الحالات لا تطابق Desired state.
- Missing: كيان Required غير معروف بعد انتهاء الحماية.
- Disabled: الجروب متوقف إدارياً.

## Sync
Sync يجبر الجروب على إعادة مزامنة الحالة وفق المرجع. يمكن أن يرسل أوامر حقيقية.

## Test
اختبار End-to-End يجب أن يمر عبر نفس منطق الجروب، وليس مجرد تغيير UI. استخدمه وأنت في الموقع لأن الحمل قد يعمل/ينطفئ.

## Rapid x4
اختبار Stress يبدل الدارة عدة مرات بسرعة لقياس قدرة النظام على التعامل مع Latest-Wins وEcho guards. لا تستخدمه على أحمال لا يجوز تبديلها بسرعة.

## Learn Mode
يستمع لتغيرات الكيانات أثناء ضغط زر فعلي ويعرض Candidates. لا يقبل أي Candidate بشكل أعمى؛ تأكد من Entity ID والدور قبل الحفظ.

## Activity
يعرض Transactions، Source، Result، Latency، Commands وFailures. استخدمه لتشخيص "الزر رجع لحاله" أو "أمر تأخر ثم قلب الحالة".

## v2.2 Frontend stability
صفحة الجروبات سابقاً كانت تعمل عدة `Promise.all` وقد يسقط Refresh كامل إذا Call واحد فشل، ومع Events كثيرة كان يمكن أن تبدأ Refreshات متداخلة. v2.2 يستخدم:
- bounded WebSocket timeout.
- `Promise.allSettled` للبيانات المستقلة.
- تحديث جزئي لما نجح بدلاً من رمي كل Snapshot.
- Debounce لأحداث المحرك.
- Refresh lock/coalescing لمنع Storm.

## الصلاحيات
- `multi.view`: عرض.
- `multi.control`: Sync/Test/Run والتحكم التشغيلي.
- `multi.manage`: Create/Edit/Delete/Import/Takeover/Repair والإعدادات البنيوية.

هذه صلاحيات Eshtaya. Native Home Assistant entity access في Access Control طبقة منفصلة تتحكم بما يسمح به Core HA للكيانات بشكل عام.
""",

        "SMART_GROUPS": r"""# Smart Groups وAction Groups — الدليل الكامل

## الفرق عن Multi-Way
Multi-Way مبني حول Output رئيسي وControllers. Smart Group يجمع Members ضمن منطق موحد، وقد يكون له Physical Controller أو Virtual entity. Action Group يجمع Actions مثل Scenes/Scripts/Automations تحت Trigger واحد.

## أنواع Smart Group
### Physical Controller Group
يوجد Controller فعلي يرسل تغييرات إلى مجموعة Members.

### Virtual Aggregate Group
كيان افتراضي يمثل مجموعة أجهزة. التحكم بالكيان ينفذ على الأعضاء.

### Action Group
زر/Trigger يشغل مجموعة Actions بدلاً من حالة ON/OFF دائمة.

## Group Domain
يحدد طبيعة الأعضاء والسلوك: Light، Switch، Fan، Cover، Lock، Media Player، Valve، Sensor، Binary Sensor، Button، Event وغيرها حسب ما يدعمه النظام.

## Compatibility
### Strict
يفلتر الأعضاء بحسب Domain وخصائص التوافق مثل Device Class أو نوع القياس عند الحاجة.

### Domain Only
يسمح بنفس Domain مع قيود أقل. هذا Advanced ويجب استخدامه بعد فهم اختلاف خصائص الأعضاء.

## Members
كل Entity يجب أن تكون Unique داخل نفس المجموعة. عند اختيار Entity تختفي من قوائم الصفوف الأخرى لمنع Duplicate membership.

## State Policy
### ANY ON
الجروب يعتبر ON إذا أي عضو ON.

### ALL ON
الجروب يعتبر ON فقط إذا كل الأعضاء ON.

للحساسات قد توجد طريقة حساب مختلفة حسب نوع الجروب.

## Direction
### Controller Only / One Way
أمر الجروب يؤثر على الأعضاء، لكن تغير عضو منفرد لا يفرض بالضرورة مزامنة الجميع.

### Bidirectional
تغيرات الأعضاء تدخل في منطق حالة الجروب وقد تسبب مزامنة حسب الإعداد.

## Hide Members
يخفي Members المملوكين للجروب من واجهات Home Assistant إذا كانت Ownership conditions تسمح. عند حذف/نقل الجروب يجب إعادة الملكية بشكل صحيح؛ النظام يحاول Reconcile ذلك.

## Maintenance Mode
يوقف بعض سلوك المزامنة المقصود أثناء الصيانة بدون حذف الجروب.

## Favorite
يظهر الجروب في بطاقات Favorites داخل Dashboard الخاص بالمجموعات.

## Config Lock
يقفل Create/Edit/Delete البنيوي بينما يبقى Runtime control متاحاً. مفيد بعد تسليم المشروع كي لا يعدل أحد التركيب بالخطأ.

## Continuous Enforcement
يجبر آخر Desired state باستمرار. لا تفعله إذا Automations أو أشخاص يجب أن يتحكموا بأعضاء منفردين خارج الجروب؛ سيبدو كأن الجهاز "يرجع لحاله" لأن Enforcement يفعل ذلك قصداً.

## Command Echo Guard
نافذة تعتبر acknowledgements القريبة من أمر أرسله النظام Echo بدلاً من Input بشري جديد.

## Failure Policy
- Continue on member failure: يكمل بقية الأعضاء ويسجل الفشل.
- Stop on first failure: يوقف السلسلة عند أول مشكلة.

## Member Delay
تأخير بين أوامر الأعضاء. مفيد مع Cloud APIs أو أجهزة لا تتحمل Burst requests، لكنه يزيد زمن تنفيذ الجروب.

## Quarantine
عند تكرار Flapping/Failure يمكن عزل جروب أو عضو مؤقتاً حسب منطق النظام. Release يعيده للعمل بعد مراجعة السبب.

## Quality وLatency
تعطي مؤشرات على نجاح الأوامر وزمن الاستجابة. انخفاض الجودة لا يعني دائماً أن المنطق غلط؛ قد يكون Wi-Fi/Cloud/API latency.

## Undo / Snapshots
قبل تعديلات مهمة، النظام يستطيع الاحتفاظ Snapshots. Undo يعيد آخر تعديل مدعوم وليس Full Home Assistant Backup؛ لا تستبدل به Backup الحقيقي.

## Native Home Assistant Groups
قسم Native Groups يعرض Helpers/Groups المتوافقة التي يمكن استلامها.

### Take Over
المبدأ الآمن:
1. اقرأ الجروب الأصلي.
2. أنشئ بديل Eshtaya.
3. حافظ على نفس Entity ID عندما يكون المسار مدعوماً.
4. تحقق أن البديل يعمل.
5. بعدها فقط أزل Helper القديم.

لا تستخدم Take Over على Group غير متوافق لمجرد أنه ظاهر في Registry.

## Action Groups
يمكن تجميع Scene/Script/Automation.

### Parallel
يشغل Actions معاً، الأسرع لكن قد يزيد الحمل.

### Sequential
يشغلها بالترتيب.

### Automation skip conditions
إذا كان مدعوماً، يحدد هل التشغيل اليدوي يتجاوز Conditions. استخدمه بحذر لأن شروط الأتمتة قد تكون Safety guards.

### Script variables / Scene data
Action Data JSON يمرر بيانات إضافية بحسب نوع العضو. JSON غير صحيح يجب رفضه قبل الحفظ.

## اختبار الجروب
ابدأ بعدد قليل من الأعضاء، اختبر ON/OFF أو Action، راقب Diagnostics، ثم أضف الباقي. لا تبني Group فيه عشرات Cloud devices ثم تبدأ التشخيص من الصفر.
""",

        "COMMISSIONING": r"""# Commissioning — تجهيز وتسليم النظام

## الهدف
Commissioning هو تحويل Config "يبدو صحيحاً" إلى Installation تم فحصه فعلياً. يجب تنفيذه لكل دائرة أو مجموعة قبل اعتبار المشروع جاهزاً.

## قبل الاختبار
- تأكد أن الكهرباء والأحمال آمنة للتشغيل.
- كل الأجهزة Online.
- أسماء الكيانات واضحة.
- Areas صحيحة.
- لا يوجد Automation آخر يفرض حالة متعارضة أثناء الاختبار.
- خذ Backup إذا ستعمل Take Over أو Bulk import.

## Workflow مقترح لـMulti-Way
1. اختر Area.
2. حدد Physical Output الصحيح.
3. شغّل/أطفئ Output منفرداً وتأكد أنه الحمل المطلوب.
4. أضف Controller واحداً فقط.
5. اختر Mode المناسب للزر.
6. اختبر ضغطة فعلية بطيئة ON/OFF.
7. راقب Activity: Source، Desired، Result، Latency.
8. اختبر Rapid toggle إذا الحمل يسمح.
9. أضف باقي Controllers واحداً واحداً.
10. شغّل Final Sync.
11. أعد Restart لـHome Assistant وتأكد أن Startup recovery لا يولد Missing كاذب.

## Workflow لـSmart Group
1. حدد Group Domain.
2. اختر Compatibility Strict أولاً.
3. أضف عدد صغير من Members.
4. اختر ANY/ALL policy.
5. اختبر التحكم من Virtual entity.
6. إذا يوجد Physical Controller اختبره منفرداً.
7. اختبر ماذا يحدث إذا Member واحد Offline.
8. راجع Quality/Latency.
9. قرر Failure Policy.
10. بعد استقرار الجروب فعّل Hide Members أو Config Lock إذا تحتاجهما.

## Learn Mode أثناء Commissioning
Learn يساعدك في معرفة أي Entity تغير عند كبسة حقيقية. لكنه أداة اقتراح وليس إثباتاً نهائياً. إذا عدة Entities تتغير معاً، افحص Candidates وحدد الصحيح يدوياً.

## اختبار Failure
اختبار جيد لا يقتصر على الحالة الطبيعية. جرّب ـ إذا كان آمناً ـ فصل جهاز غير أساسي أو جعل Cloud device Offline، ثم راقب:
- هل الجروب يعلق؟
- هل باقي الأعضاء يكملون حسب Failure Policy؟
- هل Health تتحول Degraded بدل Crash؟
- هل رجوع الجهاز يعمل Auto Heal؟

## اختبار Restart
هذا مهم جداً في أنظمة Tuya/Cloud:
1. سجّل حالة الجروب.
2. Restart Home Assistant.
3. راقب أول 3 دقائق.
4. يجب أن ترى Recovering إذا States لم ترجع بعد.
5. لا يجب إنشاء Missing Repair لمجرد تأخر Cloud integration.
6. بعد استقرار States يجب أن تصبح Health منطقية.

## تقرير التسليم
قبل التسليم سجل:
- اسم الجروب.
- Area.
- Output.
- Controllers/Members.
- Modes.
- نتيجة End-to-End test.
- متوسط latency.
- أي Cloud limitation.
- تاريخ الاختبار.
- إصدار Eshtaya Smart Control.

## متى أعتبر الجروب جاهزاً؟
عندما يمر الاختبار البطيء والسريع المناسب، Restart recovery، Failure behavior، ولا يوجد Loop أو Unexpected revert، والـActivity log يفسر كل تغير بشكل منطقي.
""",

        "SYSTEM_CENTER": r"""# System Center — الصحة والصيانة والتقارير

## Health
يعرض صورة تشغيلية عن الوحدات التي تديرها Eshtaya. الدرجة لا تتحكم بالأجهزة؛ هي Diagnostics فقط.

## Recommendations
### Critical
تعالج أولاً، مثل Migration validation failure.

### Warning
مشكلة تشغيلية مهمة مثل Alexa sync أو Degraded groups.

### Info
معلومة لا تعتبر Failure، مثل Tuya غير المفعلة.

## Repair Alexa Files
يعيد توليد ملفات Hidden Entities من Storage ويقارن النسختين. لا يعدل قواعدك بهدف "حل" التعارض؛ هو يعيد تطبيق Source of Truth المخزن.

## Refresh Tuya
يطلب قائمة أجهزة جديدة من Cloud. هذا Force Refresh؛ إذا Cloud فشلت سيظهر Error بدل استخدام Cache وكأن التحديث نجح.

## Sync Groups
يمكن أن يرسل أوامر فعلية. لذلك يتطلب Confirmation في الواجهة وصلاحية مناسبة.

## System Report
JSON Sanitized للدعم، يشمل Version وHealth ومعلومات Modules التي لا تعتبر Secrets. لا يتضمن:
- Tuya Client Secret.
- Access token.
- Raw auth credentials.
- Raw migration backup payload.

مع ذلك راجع التقرير قبل مشاركته خارج فريقك.

## Migration Report
يعرض مراحل الهجرة والـcounts والـrollback state بدون نسخ Raw secret storage.

## تحميل مستقل
System Center يعتمد على Overview request، لكن فشل Overview لا يسقط بقية Control Hub. يوجد Retry مستقل.

## ماذا تفعل إذا Health منخفضة؟
1. اقرأ Recommendations بدل التركيز على الرقم فقط.
2. أصلح Critical.
3. افتح Module المشار إليها.
4. راجع Logs.
5. لا تستخدم Refresh All بشكل متكرر كبديل عن فهم السبب.

## الفرق بين Repair وRestart
Repair يصلح بيانات/ملفات محددة. Restart يعيد تشغيل Home Assistant كله. لا تعمل Restart متكرر إذا المشكلة Tuya API خارجية؛ v2.2 مصمم ليتحمل الفشل المؤقت بدون إسقاط بقية المنصة.
""",

        "ACCESS_CONTROL": r"""# Access Control — صلاحيات Home Assistant كاملة + صلاحيات Eshtaya

## أهم نقطة: يوجد مستويان مختلفان
v2.2 يفصل بين:

### 1. Home Assistant Native Access
هذه هي صلاحيات Home Assistant الحقيقية للكيانات على مستوى النظام، وليست مجرد إخفاء Tabs في Eshtaya. تستخدم Permission Policy Engine الأصلي في HA، وبالتالي عمليات Core التي تتحقق من صلاحيات Entity ترى Read/Control/Edit الفعلية للمستخدم.

### 2. Eshtaya Module Access
تحدد هل المستخدم يستطيع فتح Entity/Alexa، Tuya، Groups، System Center وما العمليات المسموحة داخل أدوات Eshtaya نفسها.

قد تعطي مستخدماً `multi.view` في Eshtaya لكنه يكون Read-only في Home Assistant، أو العكس. لذلك راجع الطبقتين.

# أولاً: Home Assistant Native Access

## Standard User
يضع المستخدم في مجموعة Users الأصلية. حسب Home Assistant الحالي هذه المجموعة تملك وصول الكيانات الطبيعي الواسع.

## Read Only
يستخدم مجموعة Read Only الأصلية ويمنح قراءة لكل الكيانات بدون Control/Edit وفق سياسة Core.

## No Entity Access
ينشئ Policy مخصصة بدون Grants للكيانات. هذا لا يعطل Login بحد ذاته، لكنه يجعل Core entity permission checks ترفض الوصول الذي يحتاج Permission.

## Restricted
ينشئ Group مخصصة Native داخل AuthStore المحمل في الذاكرة، ثم Home Assistant نفسه يحسب Permissions من Policy. **لا يتم تعديل ملف `.storage/auth` مباشرة.**

قبل استخدام Restricted يقوم النظام بفحص Compatibility. إذا تغيرت بنية AuthStore في إصدار Home Assistant ولم تعد الواجهة الداخلية المطلوبة موجودة، يتم تعطيل Custom Restricted بدلاً من الكتابة بطريقة غير آمنة.

## Administrator
يمكن منحها فقط بواسطة Home Assistant Owner. مستخدم Admin غير Owner لا يستطيع ترقية شخص إلى Admin من هذه اللوحة.

## حماية Owner
حساب Home Assistant Owner لا يمكن تعديله من Eshtaya Access Control إطلاقاً.

## حماية الحساب الحالي
المدير لا يستطيع تغيير صلاحيات حسابه الذي يستعمله حالياً من نفس اللوحة، حتى لا يقفل نفسه خارج النظام.

## حماية System Users
الحسابات `system_generated` غير قابلة للتعديل من هذه الشاشة.

## Backup قبل أول تعديل
قبل أول تغيير Native لأي مستخدم يحفظ Eshtaya:
- Original group IDs.
- وقت أخذ النسخة.

هذه Metadata خاصة بـEshtaya وليست Password backup. زر Restore Original يعيد مجموعات المستخدم الأصلية إذا ما زالت موجودة.

## مستويات الصلاحية في Restricted
### None
لا Grant لهذا Scope.

### Read
`read: true`.

### Control
`read: true` + `control: true`.

### Edit
`read: true` + `control: true` + `edit: true`.

## Scopes
### Base / All Entities
Grant عام لكل الكيانات.

### Domain
مثل `light`, `switch`, `cover`. يمنح المستوى لكل Entities في Domain وفق Permission Engine.

### Area
يمنح المستوى للكيانات التي يستطيع HA ربطها بالـArea ضمن Permission lookup.

### Specific Entity
أدق Scope مثل `light.living_room`.

## أولوية البحث والدمج
Home Assistant يبحث بالترتيب الأكثر تحديداً تقريباً: Entity → Device → Area → Domain → All. لكن عند دمج Policies من مجموعات متعددة يعمل بمنطق **الأكثر سماحاً يفوز**.

### لماذا هذا مهم؟
HA الحالي لا يوفر Explicit Deny في هذا Permission model. لذلك لا تعمل الآتي:
- Base = Control لكل البيت.
- ثم Entity معين = Read وتعتقد أنك خفضته.

الـControl الواسع قد يبقى هو السماح الأعلى. لبناء Restricted صح:
1. ابدأ Base = None أو Read.
2. ارفع الصلاحية فقط للأماكن المطلوبة.
3. لا تستخدم Grants واسعة إذا تحتاج استثناء أضيق أقل صلاحية.

## حدود Home Assistant الحالية
Native policy engine يدعم Entity Read/Control/Edit. Home Assistant Core الحالي لا يقدم Public RBAC عام يسمح لإضافة HACS أن تنشئ Deny لكل Service، أو تتحكم بكل Dashboard/Settings route كأدوار مخصصة بنفس النموذج.

Eshtaya لا تدّعي تجاوز هذا الحد. نحن نستخدم ما يطبقه Core فعلياً ونفصل صلاحيات Eshtaya الخاصة في طبقة ثانية.

# ثانياً: Eshtaya Module Access

## Built-in Roles
### No Access
لا Tabs للمنصة.

### Viewer
Dashboard + View للوحدات + Documentation/System view.

### Operator
يضيف التحكم التشغيلي في Tuya/Multi-Way بدون إدارة بنيوية كاملة.

### Technician
يضيف Entity manage وMulti-Way manage وSystem actions/reports.

### Platform Manager
كل صلاحيات Eshtaya.

## Custom Role
تقدر تنشئ Role وتحدد Permissions واحدة واحدة.

## Permission list
- `dashboard.view`
- `entity.view`
- `entity.manage`
- `tuya.view`
- `tuya.control`
- `tuya.configure`
- `multi.view`
- `multi.control`
- `multi.manage`
- `docs.view`
- `system.view`
- `system.actions`
- `system.reports`
- `access.manage`

## Backend Enforcement
إخفاء Tab فقط لتحسين UX. WebSocket handlers نفسها تتحقق من الصلاحية. استدعاء Endpoint يدوياً بدون Permission يجب أن يرفض.

## كيف تضبط مستخدم "الأولاد" مثلاً؟
مثال آمن:
- HA Native: Restricted، Base=None، Area غرفة الأولاد = Control، وبعض Sensors = Read.
- Eshtaya: ربما No Access إذا لا يحتاج أدوات الإدارة.

هيك التحكم اليومي بالكيانات يظل من Home Assistant dashboards ضمن Native policy، بدون إعطائه أدوات Commissioning أو Tuya admin.

## مستخدم فني صيانة
- HA Native: Restricted أو Standard حسب الثقة، مع Control/Edit في Areas المطلوبة.
- Eshtaya: Technician.
- لا تمنحه Administrator فقط لأنه فني؛ Admin يعطي صلاحيات Core أوسع بكثير.

## Restore عند الخطأ
إذا طبقت Policy غير مناسبة على مستخدم آخر، اختره واضغط Restore Original. إذا المشكلة تخص حسابك الحالي، اللوحة أصلاً تمنع Self-change. الـOwner يبقى غير قابل للتعديل.
""",

        "MIGRATION": r"""# Migration Center — كيف تنتقل من الإضافات القديمة بأمان

## الهدف
دمج إعدادات Entity Manager وMulti-Way القديمة في Eshtaya Smart Control بدون تشغيل محركين على نفس الأجهزة وبدون حذف المصدر قبل التحقق.

## المراحل
### Detect
يبحث عن Legacy config entries/storage.

### Backup
يأخذ نسخة Migration داخل Storage قبل التغيير.

### Copy
ينقل Rules/Groups إلى مفاتيح التخزين الجديدة.

### Quiesce Legacy
يوقف المحركات القديمة حتى لا يرسل القديم والجديد أوامر لنفس الدارة.

### Runtime Start
يشغل Managers الجديدة.

### Validate
يقارن counts وحالة Runtime ويتأكد أن النقل مقبول.

### Remove Legacy Entries
يحدث فقط بعد نجاح Validation.

### Reconcile
يعالج Ownership مثل Hidden members أو Registry mapping.

### HACS Cleanup
Best effort لتنظيف تعريفات repositories القديمة عبر آليات HACS المتاحة، وليس حذف مجلدات عشوائياً.

## Rollback
إذا فشل Runtime/Validation، يحاول النظام الرجوع وتمكين القديم مع الاحتفاظ بتقرير الخطأ. لا تفترض أن كل Failure يمكن إصلاحه تلقائياً؛ راجع التقرير والـLogs.

## لماذا لا نحذف القديم يدوياً أولاً؟
لأن Migration Center يحتاج المصدر حتى يعرف ماذا ينقل ويأخذ Backup. حذف القديم قبل أول تشغيل يلغي هذا المسار الآمن.

## Report
Migration Report يوضح Phase، Steps، counts، Errors، Backup reference وRollback state. لا يحتوي Raw credentials.

## بعد Migration ناجحة
- اختبر Entity/Alexa rules.
- اختبر Multi-Way physically.
- Restart Home Assistant.
- تأكد من Startup recovery.
- فقط بعدها اعتبر النقل منتهياً عملياً.
""",

        "ARCHITECTURE": r"""# البنية التقنية — ماذا يحدث داخل المنصة؟

## Config Entry
يوجد Config Entry واحد للمنصة. Tuya credentials إن فُعلت تحفظ ضمن بيانات هذا Entry، بينما وحدات مثل Multi-Way وAccess metadata لها Stores منظمة.

## Backend Python
الوحدات الرئيسية:
- Entity Manager.
- Tuya Manager + OpenAPI Client.
- Multi-Way Manager.
- Smart Group Manager.
- Migration Coordinator.
- Integration Access Control.
- Home Assistant Native Access Manager.
- Documentation service.
- Core/System WebSocket APIs.

## WebSocket boundary
Frontend لا يقرأ Storage مباشرة. يستعمل WebSocket handlers. العمليات الحساسة تتحقق من الصلاحيات في Backend.

## Frontend v2.2
الـControl Hub الجديد Standalone Custom Element ولا يركب Patch متأخر على v2.0 component. هذا أزال Race كان يمكن أن يجعل أول `hass` setter يعمل قبل تطبيق v2.1 prototype patch.

## Resilient WebSocket layer
Child modules تستقبل Proxy لـ`hass.callWS` يضيف:
- Timeout.
- Retry محدود للقراءات الآمنة فقط.
- لا Retry تلقائي للكتابة/التحكم.

## Multi-Way refresh architecture
Events لا تشغل Refresh غير محدود. يوجد Debounce وRefresh coalescing. Core data requests تستخدم `allSettled` بحيث failure في diagnostics لا يمسح Groups list الناجحة.

## Tuya architecture
Cloud client يحصل Token ويحفظه في الذاكرة حتى قرب انتهاء صلاحيته. Device list لها Cache + Lock. Secrets لا تعاد للFrontend.

## Entity/Alexa storage
Rules هي Source of Truth، وYAML ناتج عنها. File sync health يقارن النسختين.

## Home Assistant Native Access
Restricted policy تستخدم كائنات Group/Policy الأصلية في HA runtime وتعيين المستخدم يتم عبر `hass.auth.async_update_user`. لا يتم تعديل auth JSON file يدوياً. بما أن Home Assistant لا يعرض Public custom-group CRUD، يوجد Compatibility guard قبل استخدام المسار المقيد.

## فلسفة الفشل
Module خارجي مثل Tuya يجب أن يفشل بشكل Local، لا أن يمنع بقية المنصة. لذلك v2.2 يعامل Cloud errors وOptional diagnostics كحالات مستقلة.
""",

        "SECURITY_BACKUP": r"""# الأمان والنسخ الاحتياطي — قواعد التشغيل الآمن

## أسرار Tuya
Client Secret وAccess Token لا يظهران في UI snapshots أو System Report. لا تضعهما في Screenshot أو Issue عام.

## Auth
Eshtaya لا تنشئ Password system منفصل. تستخدم مستخدمي Home Assistant الحاليين. Native access changes تعمل على Groups/Policies وليس Credentials.

## Owner
Owner لا يمكن تعديله من Eshtaya HA Access. هذا Safety boundary لمنع فقدان آخر حساب كامل.

## Self lockout
المستخدم الإداري لا يستطيع تغيير Native access لنفسه من اللوحة الحالية.

## Backup levels
### Full Home Assistant Backup
هذا المرجع الأساسي قبل Update/Migration/Auth changes كبيرة.

### Migration Backup
نسخة مخصصة لمسار Legacy migration.

### Multi-Way Export / Full Export
نسخة من Groups/settings وليست Full HA backup.

### HA Access Original Groups
Eshtaya يحفظ Group IDs الأصلية لكل مستخدم قبل أول تغيير Native، لتسهيل Restore.

## قبل Bulk changes
- Export rules/groups.
- تأكد من Target count.
- لا تنفذ على Production أثناء صيانة كهرباء أو Network unstable.

## Least Privilege
لا تمنح Administrator عندما يكفي Restricted Control. لا تمنح `multi.manage` إذا المستخدم يحتاج فقط تشغيل جروب. افصل صلاحية Home Assistant عن صلاحية أدوات الإدارة.

## مشاركة التقارير
System Report Sanitized لكنه قد يحتوي Entity IDs وأسماء أجهزة/Areas. راجعه قبل مشاركته خارج الجهة الموثوقة.

## Recovery plan
احتفظ دائماً بحساب Owner معروف، Full Backup حديث، وطريقة وصول محلية لـHome Assistant. صلاحيات Access Control ليست بديلاً عن خطة استرجاع النظام.
""",

        "TROUBLESHOOTING": r"""# حل المشاكل — مرجع تشخيص عملي

## صفحة Tuya أو Groups أو Entity/Alexa لا تحمل
### في v2.2
لا يوجد انتظار WebSocket بلا نهاية. بعد Timeout يجب أن يرجع التحكم للواجهة مع Error/Retry.

### إذا قسم واحد فقط متأثر
- Tuya فقط: راجع Cloud/Region/Token/Network.
- Groups فقط: راجع Multi-Way runtime وLogs.
- Entity فقط: راجع Entity Registry/manager initialization.

### إذا كل الأقسام متأثرة
افحص اتصال المتصفح بـHome Assistant WebSocket، Reverse Proxy، Cloudflare/Tunnel، وإعادة تشغيل Core.

## Groups كانت تعلق بعد Events كثيرة
v2.2 يعمل Debounce لEvents ويمنع أكثر من Refresh متداخل. إذا ما زالت المشكلة:
1. افتح Browser Console.
2. راجع Home Assistant Logs.
3. سجل نوع الحدث والجروب الذي يولد تغيرات متكررة.
4. راجع Continuous Enforcement وEcho Guard.

## Tuya Cloud بطيئة
Normal page load قد يعرض Last successful cache. Full Refresh سيبلغك بالفشل إذا Cloud لم ترد. لا تضغط Refresh عشر مرات؛ Manager لديه Lock لكن الضغط المتكرر لن يصلح API خارجي.

## Tuya Token failed
- Region صحيح؟
- Client ID/Secret صحيحان؟
- Project APIs مفعلة؟
- UID مرتبط بالمشروع؟

## Multi-Way Missing بعد Restart
انتظر Startup grace. إذا الكيان موجود في Entity Registry لكن State لم ترجع بعد، لا يجب اعتباره Deleted مباشرة. إذا بقي Missing بعد استقرار النظام، تأكد من Entity ID فعلياً.

## Out of Sync متكرر
راجع:
- Controller mode.
- Invert.
- Echo guard.
- Manual priority.
- Cloud latency.
- Automation خارجية تغير نفس الأعضاء.
- Continuous Enforcement.

## Entity/Alexa File Sync warning
استخدم Repair Alexa Files. إذا يرجع التحذير:
- تحقق أن `/config` و`/config/www` قابلان للكتابة.
- لا تعدل الملفين يدوياً بالتوازي مع المدير.
- راجع Disk errors.

## Documentation لا تفتح
من v2.1+ المحتوى يأتي من WebSocket `documentation/get`. 404 على `/docs/...` ليس المسار المستخدم في v2.2. إذا Endpoint غير موجود، غالباً Python files والFrontend من إصدارين مختلفين: Restart ثم تأكد من HACS version.

## واجهة قديمة بعد Update
- Restart Home Assistant.
- `Ctrl+F5`.
- افتح Version أعلى Control Hub.
- إذا بقيت قديمة امسح Cache للموقع أو افتح نافذة Private للتأكد.

## Access Control: المستخدم فقد تحكمه
إذا هو مستخدم آخر عدلته من لوحة Admin:
1. افتح Access Control.
2. اختر المستخدم.
3. اضغط Restore Original إذا يوجد Backup.
4. إذا تريد Restricted، ابدأ Base=None ثم Grants صغيرة.

## لا أستطيع تعديل Owner
هذا مقصود ولا يعتبر Bug.

## لا أستطيع إعطاء Administrator وأنا Admin
فقط Owner يستطيع Grant/Demote Administrator من هذه الأداة.

## Restricted لا تعمل في إصدار HA جديد
الصفحة تعرض Compatibility. إذا `custom_restricted_groups=false`، Eshtaya أوقفت المسار الخاص بدلاً من محاولة تعديل AuthStore غير معروف. استخدم Standard/Read Only أو انتظر تحديث توافق.

## Read-only أوسع/أضيق مما توقعت
تذكر أن HA policies Grants تراكمية. إذا المستخدم عضو في أكثر من Group، الأكثر سماحاً قد يفوز. Eshtaya Restricted يضع المستخدم في Managed group وحدها لتجنب بقاء Group واسعة، ويحفظ الأصل للRestore.

## Home Assistant Dashboard ما زالت ظاهرة
Native Entity policy تتحكم بما يستطيع المستخدم قراءته/التحكم به من Entities وفق Core. Home Assistant الحالي لا يقدم Custom Integration API لإخفاء كل Route/Settings/Dashboard كـRBAC مخصص. لا تخلط بين UI navigation وEntity permission enforcement.

## Logs المطلوبة عند فتح Issue
أرسل:
- Eshtaya version.
- Home Assistant version.
- أي stack trace باسم `eshtaya_smart_control`.
- Module المتأثرة.
- هل المشكلة بعد Restart أو بعد Cloud outage.
- لا ترسل Client Secret أو Tokens.
""",
    },

    "en": {
        "GETTING_STARTED": r"""# Getting Started — Complete Guide

## Purpose
Eshtaya Smart Control is a single Home Assistant integration that combines Entity/Alexa management, optional Tuya Cloud management, Multi-Way, Smart/Action Groups, commissioning, migration, diagnostics, documentation and access control.

## Before installation
Create a full Home Assistant backup, update HACS, keep legacy Eshtaya integrations installed until automatic migration has inspected them, and verify the integration's required Home Assistant version. Tuya credentials are optional.

## Install
Install Eshtaya Smart Control from HACS, restart Home Assistant, then add one Eshtaya Smart Control config entry from Settings → Devices & Services. The platform is designed for a single config entry.

## First startup
The backend initializes access metadata, native HA access support, migration, Entity/Alexa, optional Tuya, Multi-Way/Smart Groups and the Control Hub. Legacy entries are backed up and validated before removal.

## First checks
Open Dashboard, Entity/Alexa, Groups and System Center. On v2.2 each module loads independently; a Tuya Cloud problem must not prevent Groups or Entity/Alexa from opening.

## Tuya activation
Open Tuya → Account Settings and provide Region, Client ID, Client Secret and UID. Test before saving. The saved Client Secret is not returned to the browser.

## After updates
Update through HACS, restart Home Assistant, hard-refresh the browser if necessary, verify the displayed version, then review System Center and Groups health.
""",

        "DASHBOARD": r"""# Dashboard

The Dashboard is an operational summary, not the detailed device-control screen. It shows the loaded version, health score and module cards allowed by the current Eshtaya role.

v2.2 loads the security profile first and fetches Overview independently. Overview errors display a retry action instead of blocking the whole shell. Entity, Tuya and Groups are separate child modules with bounded WebSocket calls.

A Tuya timeout therefore remains a Tuya problem. It does not hold the entire Control Hub in a permanent loading state.

Use the global Refresh button for current data. A full Home Assistant restart is still required after installing updated Python integration files.
""",

        "ENTITY_CONTROL": r"""# Entity & Alexa Control

## Entities
Search and filter by domain, area, platform, availability and Alexa state. Each row shows entity identity, device/area context and the effective Alexa rule.

## Alexa rules
Inherit uses automatic domain/category/keyword rules. Force Allow explicitly exposes an entity and Force Exclude explicitly hides it according to the manager model. Rule changes regenerate the managed Alexa YAML output.

## Rename
Entity names are changed through the Home Assistant entity registry when a registry entry exists. Reset removes the custom name.

## Rules and bulk operations
Domain defaults, excluded categories and keywords apply to entities using Inherit. Bulk operations should be preceded by an export or Home Assistant backup when the target set is large.

## Managed files
The integration keeps `/config/hidden_entities.yaml` and `/config/www/hidden_entities.yaml` synchronized. System Center can detect and repair differences.

## Maintenance
Export/import provides rule portability. Cleanup Orphans removes stored rules for entities that no longer exist; it does not delete Home Assistant entities.

v2.2 wraps child WebSocket traffic with a timeout so a stalled request returns an error instead of leaving an endless spinner.
""",

        "TUYA_CONTROL": r"""# Tuya Cloud Control

Tuya is optional. Configure Region, Client ID, Client Secret and UID, then test before activation. Secrets remain in the Home Assistant config entry and are excluded from support reports.

The device list supports search, online/offline filtering, categories, device details, shadow-property custom names and bulk operations.

v2.2 serializes device-list refreshes with a lock. A normal page load may use the last successful device cache during a temporary Tuya failure, while an explicit Full Refresh reports the cloud failure. Safe read requests have bounded retry behavior; write requests are not automatically repeated.

For token errors verify data center, project API permissions, credentials and UID. For timeouts check network/Tuya availability rather than repeatedly refreshing.
""",

        "MULTIWAY": r"""# Multi-Way Control

A Multi-Way group contains one primary physical output plus one or more controllers. Controller modes include Mirror, Toggle, momentary edges, Event and Follow, with optional inversion/state reflection.

Performance modes balance response speed versus confirmation. Debounce, physical-priority windows, command timeout, retries, echo guards and settle windows protect against bounce, delayed cloud acknowledgements and rapid physical changes.

Startup protection treats delayed integration restore as Recovering instead of immediately reporting deleted entities. Required output/controllers are checked against both runtime state and the entity registry before persistent missing diagnostics are emitted.

v2.2 also hardens the frontend: core group requests use partial `allSettled` results, event refreshes are debounced and overlapping refresh storms are coalesced.

Use End-to-End and rapid tests only when physically safe because they can operate real loads.
""",

        "SMART_GROUPS": r"""# Smart Groups & Action Groups

Smart Groups aggregate compatible entities under a physical controller or virtual entity. State policies such as ANY/ALL determine the aggregate state; bidirectional behavior determines how member changes feed back into the group.

Compatibility can be strict or domain-only. Strict mode is recommended first because it considers domain/subtype characteristics. Member IDs must remain unique inside one group.

Reliability tools include command echo guards, failure policies, member delay, quarantine, quality/latency diagnostics, maintenance mode, config lock, snapshots and undo.

Action Groups can execute scenes, scripts and automations in parallel or sequence with optional action data. Use automation condition bypass only when you understand the safety implications.

Native Home Assistant groups can be taken over only through the managed migration path that creates and verifies the replacement before removing the original helper.
""",

        "COMMISSIONING": r"""# Commissioning

Commissioning proves a configuration under real conditions. Verify the physical output first, add one controller/member at a time, test normal and rapid input, inspect Activity/Diagnostics, then add remaining members.

Test restart recovery, temporary device failure and cloud latency where safe. A production-ready group should have explainable transactions, no feedback loop, predictable failure handling and healthy restart recovery.

Record group name, area, output, controllers/members, modes, test results, latency, cloud limitations and the Eshtaya version in the handover report.
""",

        "SYSTEM_CENTER": r"""# System Center

System Center presents health, recommendations, migration state, safe maintenance actions and sanitized reports.

Repair Alexa Files rebuilds managed YAML from stored rules. Refresh Tuya performs an explicit cloud refresh. Sync Groups can send real device commands and therefore requires confirmation and appropriate permissions.

System Report excludes Tuya Client Secret, access tokens and raw migration/auth storage. Review it before external sharing because entity IDs and operational names may still be present.

Health is diagnostic. Treat critical recommendations first and investigate the affected module instead of repeatedly using broad refresh/restart actions.
""",

        "ACCESS_CONTROL": r"""# Access Control — Home Assistant + Eshtaya

v2.2 has two separate security layers.

## Native Home Assistant access
Home Assistant administrators can assign Standard User, Read Only, No Entity Access or a Restricted native entity policy. Restricted policies are enforced by Home Assistant's own read/control/edit permission engine and can grant by base/all, domain, area or individual entity.

The Owner cannot be modified. System-generated users cannot be modified. The current administrator cannot modify their own native access from this panel. Administrator promotion/demotion is limited to the Owner.

Before the first native change, Eshtaya records the user's original group IDs. Restore Original returns those groups when possible.

Home Assistant's current entity policy model is additive and does not provide explicit deny semantics. Build restrictive policies from Base=None or Base=Read and grant higher levels only where required. A broad Control grant cannot reliably be reduced by a narrower Read grant when policies merge permissively.

Home Assistant core currently exposes entity read/control/edit permissions, not a general public custom-role API for arbitrary per-service denies or dashboard/settings-route RBAC. Eshtaya does not fake unsupported core capabilities.

## Eshtaya module access
A separate role controls Dashboard, Entity, Tuya, Multi-Way, Documentation, System and Access actions. Built-in roles are No Access, Viewer, Operator, Technician and Platform Manager, and custom Eshtaya roles can be created.

Frontend hiding is convenience only; Eshtaya WebSocket endpoints enforce these permissions on the backend.
""",

        "MIGRATION": r"""# Migration Center

Automatic migration follows Detect → Backup → Copy → Quiesce Legacy → Start Runtime → Validate → Remove Legacy Entries → Reconcile → HACS Cleanup.

Legacy engines are stopped before the replacement engine controls the same groups. Old config entries are removed only after validation. Failures attempt rollback and remain visible in Migration Report.

Do not manually delete legacy integrations before first migration if you expect automatic transfer. After migration, physically test groups and restart Home Assistant to validate startup recovery.
""",

        "ARCHITECTURE": r"""# Architecture

The platform uses one config entry, Python managers with dedicated storage, backend WebSocket APIs and versioned Web Components.

v2.2 replaces the previous prototype-patched shell with a standalone custom element, eliminating an initialization timing race. Child modules receive a resilient `hass.callWS` proxy with bounded timeouts and safe-read retries.

Multi-Way events are debounced and refreshes are coalesced. Tuya device refresh is serialized and may use stale successful cache on normal reads. Entity/Alexa rules remain the source of truth for generated YAML.

Native restricted HA access uses Home Assistant Group/Policy objects in the loaded auth runtime and public user-group assignment; it never edits the auth JSON file directly and disables custom-group support if compatibility checks fail.
""",

        "SECURITY_BACKUP": r"""# Security & Backup

Create a full Home Assistant backup before major upgrades, migrations or broad access changes. Tuya secrets/tokens are excluded from UI reports. Eshtaya uses existing Home Assistant users rather than a parallel password database.

The Owner and current administrator are protected from lockout actions in Native Access. Original Home Assistant group IDs are captured before the first Eshtaya-managed native access change and can be restored.

Use least privilege: native Restricted Control is preferable to Administrator when full administration is not required; Eshtaya `multi.manage` or `tuya.configure` should be granted only to users who need configuration access.

Exports/snapshots are useful operational backups but do not replace a full Home Assistant backup.
""",

        "TROUBLESHOOTING": r"""# Troubleshooting

## A module stays loading
v2.2 uses bounded WebSocket timeouts. A single Tuya/Groups/Entity failure should return an error instead of blocking the full Control Hub. If every module times out, investigate Home Assistant WebSocket connectivity or reverse proxy/tunnel health.

## Groups refresh storm
v2.2 debounces engine events and prevents overlapping refreshes. If a loop remains, inspect external automations, continuous enforcement, controller modes and echo/physical-priority settings.

## Tuya problems
Verify region, project permissions, credentials and UID. Normal loads can use the last good cache; Full Refresh deliberately reports cloud failure.

## Missing after restart
Allow startup protection to finish. Delayed state restoration is Recovering; a persistent missing entity after system stabilization should be checked in the entity registry.

## Documentation 404
v2.2 documentation is delivered through the WebSocket documentation endpoint, not a static `/docs` path. If versions are mixed, restart Home Assistant and hard-refresh the browser.

## Native access mistake
Select the affected other user and use Restore Original. Owner is immutable and self-access changes are blocked. If custom restricted groups are reported unsupported after a Home Assistant update, use built-in Standard/Read Only and update Eshtaya for compatibility.
""",
    },
}
