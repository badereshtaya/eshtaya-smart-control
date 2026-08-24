"""Detailed packaged documentation for Eshtaya Smart Control v2.2."""
from __future__ import annotations

AR = {
"GETTING_STARTED": r'''# البدء والتثبيت

## ما هي Eshtaya Smart Control؟
Eshtaya Smart Control هي منصة إدارة داخل Home Assistant تجمع في واجهة واحدة: إدارة الكيانات وأسماء Alexa، إدارة Tuya Cloud، Multi‑Way Control، Smart Groups، Commissioning، System Center، Migration Center، إدارة مستخدمي الإضافة، وإدارة الدور الحقيقي للمستخدم داخل Home Assistant ضمن الحدود التي يدعمها Core.

## المتطلبات قبل التثبيت
1. Home Assistant بإصدار متوافق مع `manifest.json` أو أحدث.
2. HACS محدث.
3. Backup كامل من Home Assistant قبل أول تثبيت أو أي ترقية كبيرة.
4. إذا كان لديك تكامل Eshtaya قديم، لا تحذفه قبل أول تشغيل لأن Migration Center يحتاجه لاكتشاف الإعدادات وترحيلها.
5. Tuya Cloud اختيارية بالكامل؛ لا تحتاج Client ID أو Client Secret لتثبيت المنصة أو استخدام بقية الوحدات.

## التثبيت عبر HACS
1. افتح HACS ثم Integrations.
2. افتح المستودع `badereshtaya/hacs-eshtaya-smart-control`.
3. ثبّت آخر إصدار Stable.
4. أعد تشغيل Home Assistant Restart كامل، وليس Reload للواجهة فقط.
5. افتح Settings → Devices & Services → Add Integration وابحث عن Eshtaya Smart Control.
6. أنشئ Config Entry واحد فقط؛ التكامل مصمم كـ `single_config_entry`.

## ماذا يحدث في أول تشغيل؟
يتم إنشاء Access Control storage، تشغيل Entity Manager، تجهيز Tuya Manager بدون إلزامك بتفعيل Tuya، تحميل Multi‑Way وSmart Groups، ثم تشغيل Migration Center عند وجود تكاملات قديمة. بعد ذلك يتم تسجيل لوحة Eshtaya Smart Control في Sidebar.

## أول فحص بعد التثبيت
- افتح Dashboard وتأكد أن الصفحة تحمل بدون Error banner.
- افتح Entity & Alexa وتأكد أن عدد الكيانات ليس صفراً إذا Home Assistant يحتوي كيانات.
- افتح Multi‑Way وانتظر حتى يصبح Engine Ready بعد انتهاء Startup Protection.
- افتح System Center وراجع Health Score والتوصيات.
- إذا ستستخدم Tuya، افتح Tuya Control وأدخل بيانات الحساب ثم نفّذ Test Connection قبل الحفظ.
- افتح Access Control واضبط المستخدمين غير المديرين.

## بعد أي تحديث
1. حدّث التكامل من HACS.
2. أعد تشغيل Home Assistant.
3. نفّذ Hard Refresh للمتصفح (`Ctrl+F5`) إذا بقيت واجهة قديمة.
4. راجع System Center وMulti‑Way Health.
5. لا تحذف ملفات Storage يدوياً لمعالجة مشكلة واجهة؛ استخدم أدوات Repair/Backup أولاً.

## إذا لم تظهر النسخة الجديدة في HACS
نفّذ Update information داخل HACS، ثم راجع أن GitHub Release الجديد موجود. رقم النسخة الحقيقي موجود في `custom_components/eshtaya_smart_control/manifest.json` ويجب أن يطابق الإصدار المنشور.
''',
"DASHBOARD": r'''# لوحة التحكم الرئيسية

## الهدف
Dashboard ليست مجرد صفحة إحصائيات؛ هي نقطة تشخيص سريعة لحالة المنصة قبل الدخول إلى الأدوات التفصيلية. البيانات تأتي من Backend ولا تعتمد على قراءة DOM أو تخمينات الواجهة.

## Health Score
الدرجة من 0 إلى 100. تنخفض بسبب مشاكل مادية مثل فشل Migration، اختلاف ملفات Alexa، نسبة كيانات unavailable، Multi‑Way degraded أو Smart Groups degraded. عدم تفعيل Tuya بحد ذاته حالة Informational لأنه قسم اختياري.

## بطاقات القياسات
حسب صلاحيات المستخدم قد تظهر: إجمالي الكيانات، unavailable، المخفي عن Alexa، عدد Multi‑Way groups، عدد Smart Groups، وحالة Tuya. إذا المستخدم لا يملك صلاحية مشاهدة قسم معين فلا يتم فقط إخفاء البطاقة؛ Backend أيضاً ينظف Snapshot ولا يرسل تفاصيل القسم غير المسموح.

## Smart Recommendations
كل Recommendation تحتوي Severity وTarget. الترتيب العملي: Critical أولاً، ثم Warning، ثم Info. زر Details يفتح القسم المرتبط عندما يكون المستخدم مخولاً له. رسالة System Healthy تعني عدم وجود تحذير مادي في الفحوص الحالية، وليست ضماناً أن كل جهاز في البيت يعمل فعلياً.

## أزرار الوصول السريع
Dashboard تعرض فقط الأقسام المسموحة للمستخدم. المدير يرى عادة Entity، Tuya، Multi‑Way، Documentation، System Center وAccess Control. المستخدم المقيد يرى فقط ما سمح به Role/Overrides.

## Refresh
زر Refresh يعيد جلب Access profile وOverview وبيانات الإدارة المتاحة. في v2.2 فشل طلب واحد لا يلغي بقية الصفحة؛ يتم التعامل مع الطلبات بشكل مستقل وتوجد إعادة محاولة تلقائية للانقطاعات المؤقتة.
''',
"ENTITY_CONTROL": r'''# إدارة الكيانات وAlexa

## الوظيفة الأساسية
القسم يجمع Entity Registry/State Machine مع قواعد ظهور Alexa ويدير نسختين من `hidden_entities.yaml`. الهدف أن تتحكم بالأسماء والاستثناءات بدون تعديل YAML يدوياً في كل مرة.

## تبويب Entities
يعرض Entity ID، الاسم الحالي، الجهاز، المنطقة، Platform، Availability وحالة Alexa. الفلاتر تشمل Domain، Area، Platform، Available/Unavailable، Included/Excluded/Overrides والبحث النصي. يمكن ترتيب القائمة بالاسم أو Entity ID أو Domain أو Area.

## قواعد Alexa لكل كيان
- **Inherit / Auto:** يتبع Domain rules والكلمات/التصنيفات التلقائية.
- **Force Allow:** يفرض السماح حتى لو القاعدة العامة تستثني النوع.
- **Force Exclude:** يفرض الإخفاء مهما كانت القاعدة العامة.
التعديل يحفظ في Storage ثم يعيد توليد الملفات اللازمة.

## تغيير الاسم
عندما يكون الكيان موجوداً في Entity Registry يمكن وضع Custom Name أو Reset للاسم الأصلي. التغيير هو Home Assistant Registry update حقيقي، لذلك ينعكس في واجهات HA التي تعتمد الاسم المسجل.

## التعديل الجماعي
حدد عدة كيانات أو استخدم Bulk Rule حسب Keyword/Domain. قبل تعديل كبير صدّر القواعد. لا تستخدم Bulk Exclude بدون مراجعة الفلتر لأن التأثير قد يشمل كيانات كثيرة.

## Domain Rules
يمكن منع Domain كامل افتراضياً. Force Allow على كيان محدد له أولوية على Domain exclusion. هذا مناسب لحذف كيانات diagnostic/config من Alexa مع إبقاء استثناءات محددة.

## Automatic exclusions
Categories وKeywords تعمل فقط على كيانات Inherit. الكلمات تُفحص في الاسم وEntity ID. اجعل الكلمات محددة قدر الإمكان حتى لا تخفي كيانات صحيحة بالخطأ.

## ملفات Alexa
يتم الحفاظ على نسختين متزامنتين:
- `/config/hidden_entities.yaml`
- `/config/www/hidden_entities.yaml`
إذا كانت واحدة مفقودة تُنشأ. System Center يقارن التزامن ويستطيع Repair. لا تعتمد على تعديل يدوي دائم لأن Regenerate سيكتب النموذج المخزن من جديد.

## Import / Export / Cleanup
Export يعطي نسخة قواعد قابلة للحفظ. Import يجب مراجعته قبل التطبيق. Cleanup Orphans يزيل قواعد لكيانات لم تعد موجودة؛ استخدمه فقط بعد التأكد أن الكيان حُذف فعلاً وليس مجرد Integration لم يكتمل تحميلها.

## الصلاحيات
`entity.view` للمشاهدة و`entity.manage` للتعديل. الحماية في Backend WebSocket، لذلك استدعاء endpoint يدوياً بدون صلاحية يُرفض حتى لو شخص عدّل JavaScript في المتصفح.

## الاستقرار في v2.2
إذا فشل أول WebSocket أثناء فتح الصفحة، لا تبقى الصفحة معلقة. يوجد timeout وإعادة محاولة تدريجية واستعادة عند رجوع الشبكة أو إعادة Focus للنافذة.
''',
"TUYA_CONTROL": r'''# إدارة Tuya Cloud

## متى تحتاج هذا القسم؟
Tuya اختيارية. استخدمها إذا كنت تريد قراءة أجهزة مشروع Tuya Cloud وتعديل أسماء الأجهزة/خصائصها من Home Assistant. Multi‑Way وبقية المنصة لا تتطلب تفعيل Tuya Cloud من هذا القسم.

## بيانات الحساب
- Region/Data Center يجب أن يطابق Project في Tuya IoT Platform.
- Client ID هو Access ID للمشروع.
- Client Secret يبقى داخل Home Assistant ولا يُعاد عرضه بعد الحفظ.
- UID يجب أن يطابق المستخدم المرتبط بالمشروع عندما يحتاج API ذلك.
- Custom endpoint يستخدم فقط إذا لديك Endpoint خاص ومعلوم.

## Test Connection
قبل Save استخدم Test. الاختبار يفحص صحة التوقيع والاتصال والبيانات المطلوبة. إذا فشل لا تحفظ عشوائياً؛ راجع Region، API services المرتبطة بالمشروع، Authorization وUID.

## قائمة الأجهزة
بعد نجاح التفعيل يتم تحميل الأجهزة مع Online state، Category، Product ID وDevice ID. يمكن فلترة Online/Offline، Category والبحث بالاسم أو المعرف.

## Device Details وShadow Properties
Details تعرض معلومات الجهاز من Tuya API. Shadow Properties تساعد على فهم DP codes/values المدعومة. لا تفترض أن كل DP قابل للكتابة؛ بعض القيم Read‑only أو تعتمد على Product schema.

## تعديل أسماء الأجهزة والخصائص
Update Device Name يكتب الاسم في Tuya. Property Custom Name مخصص للأسماء القابلة للإدارة حسب API. Bulk Save يجمع تعديلات متعددة، لذلك راجع القائمة قبل الإرسال.

## Rate limits والبطء
Tuya خدمة Cloud وقد تتأخر أو تحد الطلبات. لا تعمل Force refresh بشكل متكرر بدون حاجة. v2.2 يستخدم timeout مختلف للـstatus والقائمة وForce refresh ويعيد المحاولة تدريجياً عند أخطاء الاتصال المؤقتة.

## إذا الصفحة بقيت فارغة سابقاً
في الإصدارات القديمة كانت أول محاولة تحميل هي الوحيدة. إذا حصل WebSocket disconnect وقتها لم يعاد bootstrap. v2.2 أصلح ذلك: Status وDevice list لهما recovery مستقل، Error banner واضح، وإعادة محاولة عند Online/Focus.

## الصلاحيات
- `tuya.view`: قراءة الحالة والأجهزة والتفاصيل.
- `tuya.control`: تعديل أسماء الأجهزة/الخصائص.
- `tuya.configure`: إضافة أو تغيير بيانات الحساب وإلغاء التفعيل.
Client Secret لا يدخل في System Report ولا Overview.
''',
"MULTIWAY": r'''# Multi‑Way Control

## المفهوم
Multi‑Way يربط Output فعلياً بواحد أو أكثر من Controllers ليصبح لديك 2‑way/3‑way/multi‑way برمجياً. المحرك يراقب state changes ويمنع feedback loops ويستخدم transaction/echo guards حتى لا يتحول التزامن إلى اهتزاز ON/OFF.

## مكونات المجموعة
- **Output:** الكيان الذي يمثل الحمل الفعلي النهائي.
- **Controllers:** الأزرار/الكيانات التي تقود الحمل أو تعكس حالته.
- **Virtual entity:** كيان اختياري يمثل الجروب داخل Home Assistant.
- **Behavior:** إعدادات debounce، confirmation، retries، restore policy والأداء.

## Controller modes
- Mirror: حالة Controller تتطابق مع Output.
- Toggle: كل تغير فعلي يُعتبر طلب Toggle.
- Momentary ON/OFF: مناسب للأزرار التي تعطي نبضة باتجاه واحد.
- Event: يعتمد تغير event كإشارة.
- Follow: Controller يتبع Output ولا يقوده بنفس الطريقة.
استخدم Test قبل اعتماد mode لأن أجهزة Tuya/Zigbee قد تبلغ states بشكل مختلف.

## Performance modes
- Instant: أسرع استجابة ويرسل التغيير فوراً ثم يتحقق بالخلفية.
- Balanced: يتأكد من Output قبل تحديث followers.
- Safe: ينتظر تأكيدات أكثر ويعطي أولوية للصحة على السرعة.

## Startup Protection وv2.2
عند Restart قد تكون Entity Registry جاهزة قبل State Machine أو العكس، خصوصاً Tuya/Cloud. المحرك لا يعتبر غياب state لحظياً دليلاً أن الكيان حُذف. يوجد grace/retry ويُفحص Entity Registry أيضاً. أثناء الاستعادة تظهر Recovering بدلاً من Missing كاذب.

## Health states
Healthy، Degraded، Out of Sync، Recovering، Missing، Offline وDisabled. Health لا تعتمد فقط على state الحالي؛ تدخل فيها confirmations، failures والـlatency.

## Tests
Test Group يفحص الجاهزية. End‑to‑End يمر عبر منطق التحكم الحقيقي. Rapid Toggle يضغط الدارة فعلياً عدة مرات ويستخدم لاختبار السباقات؛ لا تشغله على حمل حساس أو بدون شخص بالموقع.

## Activity
Activity يسجل المصدر، العملية، النتيجة، transaction والlatency. إذا صار oscillation راجع source sequence وابحث عن Controller يبلغ تغييرات متأخرة أو automation خارجية تعكس الحالة.

## Repair Center
Missing الحقيقي يجب أن يعني أن الكيان غير موجود في State Machine ولا Entity Registry بعد انتهاء startup grace. Remap يربط الجروب بEntity ID بديل. لا تعمل Remap لمجرد أن جهاز Cloud Offline مؤقتاً.

## Backup
Export قبل أي Import/Replace. Full Import قد يغير عدة جروبات، لذلك نفذه بعد Home Assistant Backup أيضاً.

## الصلاحيات
`multi.view` للمشاهدة، `multi.control` للمزامنة/الاختبارات/الأوامر، و`multi.manage` لتغيير البنية، import، repair، takeover والحذف.
''',
"SMART_GROUPS": r'''# Smart Groups

## ما الفرق عن Multi‑Way؟
Multi‑Way مبني حول Output رئيسي وControllers. Smart Groups تجمع عدة أعضاء ويمكن أن تمثل Aggregate entity أو جروب مربوط Controller أو Action Group لتشغيل Scene/Script/Automation.

## أنواع الاستخدام
- Virtual Aggregate: كيان افتراضي يتحكم بمجموعة أعضاء.
- Physical Controller Group: Controller فعلي يقود أعضاء متعددين.
- Action Group: زر/كيان ينفذ Scene أو Script أو Automation حسب النوع.

## Group Type وCompatibility
نوع الجروب يحدد domains/actions المقبولة. Strict compatibility يمنع أعضاء غير متوافقين. Domain‑only أوسع لكنه يتطلب منك معرفة أن كل عضو يدعم الخدمة المطلوبة.

## Members
كل Member له Entity ID وEnabled. العضو المعطل يبقى في الإعداد لكن لا يدخل في التنفيذ. لا تكرر نفس Entity ID في الجروب ولا تستخدم Controller نفسه كعضو إذا المنطق سيخلق loop.

## State Policy
ANY يعني الجروب ON إذا عضو واحد على الأقل ON. ALL يعني ON فقط إذا كل الأعضاء المطلوبين ON. اختر السياسة حسب معنى الجروب، وليس حسب شكل البطاقة فقط.

## Hide Members
عند تفعيلها يمكن إخفاء الأعضاء الذين تملكهم الإضافة لتقليل الفوضى في HA. Takeover/Import يحافظ قدر الإمكان على ملكية وإخفاء صحيحين ولا يفترض أن أي native group يمكن الاستيلاء عليه.

## Native Groups وTake Over
صفحة Commissioning تعرض native HA groups القابلة للاكتشاف. Import ينشئ Smart Group من التعريف الأصلي. Take Over يستخدم فقط عندما النوع مدعوم وبنية الجروب آمنة للنقل. احتفظ Backup قبل العملية.

## Reliability
Smart Manager يستخدم echo guards، member result tracking، latency/quality، quarantine وفشل جزئي. فشل عضو لا يجب أن يخفي هوية العضو المتسبب؛ Diagnostics يعرض member-level status.

## Quarantine
إذا عضو يسبب فشل متكرر يمكن عزله حسب أدوات النظام بدل تعطيل الجروب كله. بعد إصلاح الجهاز اختبره قبل إزالة quarantine.

## الصلاحيات
عمليات القراءة ضمن `multi.view`، تشغيل الجروبات ضمن `multi.control`، وتعديل البنية/templates/import/takeover ضمن `multi.manage`.
''',
"COMMISSIONING": r'''# Commissioning والتجهيز

## لماذا توجد صفحة Commissioning؟
الهدف منع إنشاء جروب ثم اكتشاف مشاكله بعد تسليم المشروع. Commissioning يجبرك عملياً على فحص الكيانات، اختيار Controller/Output الصحيح، تجربة الاتجاه، قياس الاستجابة وتوثيق النتيجة.

## تسلسل مقترح لكل دائرة
1. تأكد أن كل Entity IDs موجودة ومتاحة.
2. شغّل Output وحده من Home Assistant وتأكد أن ON/OFF يطابق الواقع.
3. اختبر Controller فعلياً بدون الجروب وسجل كيف تتغير حالته.
4. أنشئ الجروب بController واحد فقط.
5. اختبر من الواجهة ومن المفتاح الفعلي.
6. جرّب Rapid Toggle فقط إذا الحمل يسمح.
7. أضف بقية Controllers واحداً واحداً.
8. راجع Activity وHealth بعد كل إضافة.
9. نفّذ Full Test في نهاية المشروع.

## Learn
Learn mode يراقب التغييرات خلال نافذة زمنية ويقترح كيانات مرشحة. النتيجة Candidate وليست حقيقة مطلقة؛ طابق الاسم/Area والstate الفعلي قبل Use.

## Areas
فلترة Area تساعدك تمنع اختيار زر من غرفة أخرى بالخطأ. Unassigned لا يعني سيئاً لكنه إشارة أن Registry بحاجة تنظيم.

## معيار القبول قبل Production
- لا يوجد Missing.
- لا يوجد oscillation بعد 20+ تبديل طبيعي.
- latency مقبولة للجهاز/البروتوكول.
- كل Controller يعطي النتيجة نفسها.
- بعد Restart يعود الجروب Healthy أو Recovering ثم Healthy بدون Repairs كاذبة.
- تم أخذ Backup وتسمية الجروب بشكل واضح.

## أجهزة Cloud
Tuya Cloud entities قد تتأخر أكثر من local Zigbee/Z‑Wave. لا تستخدم نفس thresholds بشكل أعمى لكل البروتوكولات.
''',
"SYSTEM_CENTER": r'''# System Center

## الوظيفة
System Center يجمع صحة المنصة، Recommendations، Alexa file sync، Migration state، Quick Actions والتقارير. هو مركز تشخيص وليس بديلاً عن Settings → System → Logs في Home Assistant.

## Quick Actions
- Repair Alexa Files: يعيد بناء النسختين من النموذج المخزن.
- Refresh Tuya: يطلب قائمة حديثة إذا Tuya مفعلة.
- Sync Groups: قد يرسل أوامر فعلية ويطلب Confirmation.
- System Report: ينزل JSON تشخيصي sanitized.

## System Report
يتضمن نسخة من Overview ومعلومات تشغيل مفيدة للدعم. لا يتضمن Client Secret، access tokens أو raw migration backup payload. مع ذلك راجع الملف قبل مشاركته لأنه قد يحتوي Entity IDs وأسماء أجهزة تعتبر معلومات عن بنية المنزل.

## Migration Report
يعرض مراحل الترحيل والcounts والنتائج بدون raw secrets. استخدمه إذا migration توقف أو rollback حدث.

## Health Score
هو تجميعي. إذا النتيجة منخفضة، لا تصلح الرقم مباشرة؛ افتح Recommendations وحدد السبب الأساسي. إصلاح unavailable integration مثلاً أفضل من إخفاء التحذير.

## الصلاحيات
`system.view` للمشاهدة، `system.actions` للإجراءات و`system.reports` للتقارير. بعض الإجراءات تتطلب أيضاً صلاحية الوحدة المستهدفة مثل `multi.control` أو `entity.manage`.
''',
"ACCESS_CONTROL": r'''# مركز الصلاحيات والمستخدمين

## يوجد مستويان مختلفان للصلاحيات
v2.2 يفصل بوضوح بين **Home Assistant System Access** و**Eshtaya Smart Control Access**. هذا مهم لأن إخفاء تبويب داخل الإضافة لا يساوي منع مستخدم من التحكم بباقي Home Assistant.

## 1) Home Assistant System Access
هذا القسم يعدّل المجموعات الحقيقية للمستخدم عبر `hass.auth.async_update_user`، لذلك التأثير على Home Assistant كله وليس على الإضافة فقط. لا يستطيع فتحه للتعديل إلا Administrator حقيقي في Home Assistant.

### الأدوار المدعومة من Core حالياً
- **Administrator:** إدارة كاملة وواجهات admin إضافة إلى التحكم بالكيانات.
- **User:** مستخدم عادي؛ عمليات Core المحجوزة للمدير تبقى ممنوعة.
- **Read Only:** سياسة Core للقراءة فقط على الكيانات.
- **Owner:** مالك Home Assistant، لا يمكن خفضه أو تعطيله من اللوحة.

### Active Account
إلغاء Active يعطل الحساب وفق Home Assistant auth manager. لا يمكنك تعطيل حسابك الحالي من اللوحة، ولا Owner.

### Local Only
يقيد بيانات دخول المستخدم حسب دعم Home Assistant بحيث تكون Local only. استخدمها للحسابات الداخلية التي لا يجب أن تدخل من خارج الشبكة.

### حدود Home Assistant 2026
Core لا يوفر API عام لـHACS لإنشاء Custom Core Roles أو Deny Rules أو ACL على كل Service. لذلك لا ندعي وجود صلاحية غير حقيقية. Eshtaya تستخدم فقط المجموعات الرسمية المدعومة؛ أي RBAC أعمق يحتاج دعماً من Home Assistant Core نفسه.

## 2) Eshtaya Smart Control Access
هذه طبقة إضافية خاصة بواجهات/API الإضافة نفسها. الأدوار: No Access، Viewer، Operator، Technician، Platform Manager وأدوار مخصصة.

### Permissions
Dashboard، Entity view/manage، Tuya view/control/configure، Multi‑Way view/control/manage، Documentation، System view/actions/reports وAccess manage.

### Allow / Deny overrides
يمكن إضافة Allow أو Deny فوق Role لمستخدم واحد. Deny يتغلب على Allow داخل طبقة Eshtaya. Expiration يجعل assignment مؤقتاً.

## Backend Enforcement
كل endpoints الحساسة تفحص الصلاحية في Python/WebSocket backend. JavaScript فقط يحسن UX ويخفي الأدوات غير المسموحة؛ ليس هو حاجز الحماية.

## قاعدة مهمة
لا تمنح مستخدم Home Assistant Administrator فقط لكي يستطيع فتح قسم واحد من Eshtaya. أعطه User/Read Only في Core حسب الحاجة، ثم اضبط Eshtaya Role منفصل. العكس صحيح: إعطاء Platform Manager داخل Eshtaya لا يحوله إلى Home Assistant Administrator.
''',
"MIGRATION": r'''# Migration Center

## الهدف
ترحيل إعدادات إضافات Eshtaya القديمة إلى المنصة الموحدة بدون تشغيل محركين على نفس الدائرة وبدون حذف المصدر قبل التحقق.

## المراحل التسع
1. Detect: اكتشاف القديم.
2. Backup: حفظ نسخة rollback.
3. Copy: نسخ القواعد والجروبات.
4. Quiesce: إيقاف المحركات القديمة عن التحكم.
5. Runtime Start: تشغيل المحرك الجديد.
6. Validate: مقارنة counts/سلامة البيانات.
7. Remove Legacy: إزالة Config Entries القديمة فقط بعد النجاح.
8. Reconcile: تصحيح ownership/hidden members.
9. HACS Cleanup: تنظيف تسجيلات المستودعات القديمة Best effort.

## إذا فشل Validation
لا يكمل الحذف. يحاول Rollback ويعيد تفعيل القديم ضمن ما تسمح به الحالة. راجع Migration Report وHome Assistant Logs قبل أي حذف يدوي.

## Backup Store
مسار/معرف النسخة قد يظهر في التقرير لكن raw payload لا يدخل System Report. لا تعدل Storage يدوياً أثناء migration.

## بعد نجاح الترحيل
اختبر Entity/Alexa وMulti‑Way وSmart Groups، ثم تأكد أن التكاملات القديمة لم تعد تتحكم بنفس الكيانات.
''',
"ARCHITECTURE": r'''# البنية التقنية

## Config Entry واحد
المنصة تستخدم domain واحد `eshtaya_smart_control` وConfig Entry واحد. الوحدات تتشارك lifecycle لكن لكل وحدة Manager/Storage/API واضح.

## Backend
- UnifiedEntityManager: Registry/Alexa rules والملفات.
- TuyaManager: credentials، signing وCloud API.
- Multi‑Way Manager: state propagation والtransactions.
- SmartGroupManager: aggregate/action groups.
- MigrationCenterCoordinator: backup/validation/rollback.
- AccessControlManager: صلاحيات Eshtaya.
- Home Assistant Access adapter: الأدوار الحقيقية المدعومة من HA.
- Documentation service: محتوى الدليل داخل الحزمة.

## WebSocket API
الواجهة لا تفتح ملفات Storage مباشرة. كل عمليات القراءة/الكتابة تمر WebSocket endpoints مع schemas وصلاحيات backend. هذا يقلل coupling مع frontend ويمنع الاعتماد على DOM كطبقة أمان.

## Frontend
Web Components داخل static path مسجل من التكامل. ملف entrypoint versioned لكسر browser cache. v2.2 يضيف resilience layer مشتركة للـEntity/Tuya/Multi‑Way وshell.

## Startup
Access storage يحمّل أولاً داخل Config Entry، ثم managers. Multi‑Way يستخدم StartupSafe manager لتجنب missing repairs أثناء استعادة integrations. Panel يسجل بعد نجاح runtime setup.

## Storage
كل module يستخدم Home Assistant Store أو Config Entry options بدل ملفات عشوائية. Client Secret لا يرسل للواجهة بعد الحفظ.

## حدود الأعطال
v2.2 يفصل bootstrap لكل embedded module: فشل Tuya لا يجب أن يمنع Entity أو Multi‑Way، وفشل Catalog داخل Multi‑Way لا يجب أن يمحو بيانات runtime التي نجحت.
''',
"SECURITY_BACKUP": r'''# الأمان والنسخ الاحتياطي

## الأسرار
Tuya Client Secret وaccess tokens لا تُعرض في Overview/System Report. لا تضع secrets داخل screenshots أو issues عامة.

## مبدأ أقل صلاحية
على مستوى HA استخدم Read Only عندما تكفي القراءة، User للتحكم العادي، Administrator فقط لمن يحتاج إدارة النظام. داخل Eshtaya استخدم Viewer/Operator/Technician بدلاً من Platform Manager لكل شخص.

## Backup قبل تغييرات خطرة
خذ Full Home Assistant Backup قبل: Major update، Migration، Full Import، Replace all groups أو تغييرات صلاحيات واسعة.

## Exports داخل Eshtaya
Entity rules وMulti‑Way/Smart Groups exports مفيدة لاسترجاع الوحدة لكنها ليست بديلاً عن Full HA Backup لأنها لا تحتوي كل Home Assistant configuration.

## استرجاع
إذا المشكلة مجرد إعداد جروب استخدم Export/Undo المناسب. إذا التكامل نفسه لم يعد يبدأ بعد تعديل ملفات يدوي، رجع Full Backup بدلاً من الاستمرار بتحرير `.storage` يدوياً.

## الصلاحيات الحقيقية
تغيير HA role من Access Control يمر auth manager الرسمي. Owner محمي، الحساب الحالي لا يمكنه نزع صلاحياته الأساسية من اللوحة، وsystem-generated users لا يتم تعديلهم.

## مشاركة التقارير
التقارير sanitized لكنها قد تحتوي أسماء مشاريع، Entity IDs وعدد أجهزة. تعامل معها كمعلومات تشغيل داخلية.
''',
"TROUBLESHOOTING": r'''# حل المشاكل

## صفحة Entity/Tuya/Groups لا تحمل أو تبقى Loading
في v2.2 يوجد recovery تلقائي. إذا ظهر Error banner انتظر retry ثم جرّب Refresh. إذا استمر: افتح Settings → System → Logs وابحث عن `eshtaya_smart_control`، تأكد أن WebSocket متصل، ثم جرّب Reload الصفحة/Restart HA. إذا الثلاث صفحات تفشل معاً فالاحتمال الأكبر backend setup أو WebSocket/auth، وليس Tuya وحدها.

## لماذا كانت المشكلة متقطعة؟
الإصدارات السابقة نفذت أول load مرة واحدة لبعض components. خطأ لحظي أثناء startup/reconnect كان يترك component بدون data. v2.2 يضيف request timeout، backoff retry، online/focus recovery ويفصل فشل كل module.

## Tuya timeout
راجع الإنترنت، Region، Project authorization وUID. لا تكرر Force Refresh بسرعة. إذا Status يعمل والقائمة تفشل فالمشكلة غالباً API list/rate limit وليست Config Entry.

## Multi‑Way Recovering بعد Restart
طبيعي لفترة startup grace. لا تعمل Remap خلال الاستعادة. إذا استمر Missing بعد استقرار كل integrations، افحص Entity Registry والEntity ID.

## Oscillation ON/OFF
افتح Activity. ابحث عن Controller يعكس state متأخر، automation أخرى تتحكم بنفس output، أو mode غير مناسب. اختبر Controller واحداً ثم أضف الباقي.

## Documentation 404
التوثيق يُرسل عبر WebSocket ولا يعتمد على `/docs` static path. إذا ظهر 404 بعد تحديث فأنت غالباً تشغل frontend قديم من cache؛ Restart + Ctrl+F5 وتأكد من رقم النسخة في header.

## Access denied
حدد هل الرفض من HA Core أم Eshtaya. رسالة admin-required تعني دور Home Assistant. `Missing permission: ...` تعني Eshtaya role/override. لا تحلها بتحويل الجميع Administrator.

## ملفا Alexa مختلفان
System Center → Repair Alexa Files. إذا استمر، تحقق من صلاحية الكتابة إلى `/config` و`/config/www` ومن وجود مجلد `www`.

## UI قديم أو أزرار غير متوافقة
Hard Refresh، ثم امسح cache للموقع فقط إذا لزم. ملفات entrypoint تحمل رقم نسخة جديد، لكن Service Worker/browser قد يحتفظ بوحدة مستوردة أثناء جلسة قديمة.

## ما الذي أرفقه في بلاغ مشكلة؟
رقم الإصدار، Home Assistant version، الخطوات التي تكرر المشكلة، System Report sanitized، والأسطر المتعلقة بـ`eshtaya_smart_control` من Logs. لا ترسل Tuya Client Secret.
'''
}

EN = {
"GETTING_STARTED": """# Getting Started\n\nEshtaya Smart Control combines Entity/Alexa management, optional Tuya Cloud, Multi-Way, Smart Groups, commissioning, migration, diagnostics and access control in one Home Assistant integration. Before installation create a full HA backup, update HACS, and keep legacy Eshtaya integrations installed until first-run migration finishes. Install from HACS, restart Home Assistant, add the single Eshtaya Smart Control config entry, then verify Dashboard, Entity Control, Multi-Way health and System Center. Tuya credentials are optional and are configured later from Tuya Control. After upgrades restart HA and hard-refresh the browser if an older frontend remains cached.\n""",
"DASHBOARD": """# Dashboard\n\nThe dashboard is an operational snapshot, not a decorative page. Health score is reduced by migration failures, Alexa file mismatch, unavailable entities and degraded Multi-Way/Smart Groups. Tuya being disabled is informational because it is optional. Metrics and recommendations are permission-filtered in the backend. Refresh reloads the current access profile and available snapshots; v2.2 isolates request failures so one module cannot blank the whole shell.\n""",
"ENTITY_CONTROL": """# Entity & Alexa Control\n\nManage registry names, Alexa exposure rules, domain defaults, automatic exclusions and the synchronized `/config/hidden_entities.yaml` and `/config/www/hidden_entities.yaml` files. Inherit follows defaults, Force Allow overrides exclusions and Force Exclude always hides the entity. Bulk operations should be preceded by an export. Cleanup Orphans is for truly deleted registry entities, not temporarily offline integrations. `entity.view` reads and `entity.manage` writes. v2.2 retries failed first-load WebSocket requests automatically.\n""",
"TUYA_CONTROL": """# Tuya Control\n\nConfigure the correct Tuya data center, Client ID, Client Secret and UID, then test before saving. The secret stays in Home Assistant. Device lists support status/category/search filters; details and shadow properties expose supported cloud metadata. Name/property changes require Tuya control permission while credentials require configure permission. Cloud latency and rate limits are expected; v2.2 uses timeouts, backoff and reconnect recovery instead of a single first-load attempt.\n""",
"MULTIWAY": """# Multi-Way Control\n\nA group contains a physical output, one or more controllers, optional virtual entity and behavior settings. Controller modes include Mirror, Toggle, Momentary, Event and Follow. Performance modes trade latency against confirmation depth. Startup protection prevents false Missing repairs while cloud integrations restore. Use Activity and Diagnostics for oscillation, confirmation failures and latency. Rapid tests physically toggle the circuit and must be used carefully. `multi.view`, `multi.control` and `multi.manage` separate read, operation and structural changes.\n""",
"SMART_GROUPS": """# Smart Groups\n\nSmart Groups can be virtual aggregates, physical-controller groups or action groups for scenes/scripts/automations. Compatibility mode controls member validation; ANY/ALL controls derived state. Diagnostics track member failures, quality and latency, and quarantine can isolate repeated failures. Native groups can be imported/taken over only when supported. Back up before structural imports.\n""",
"COMMISSIONING": """# Commissioning\n\nCommission each circuit before production: verify entities, test the real output, observe controller state behavior, start with one controller, run end-to-end tests, add controllers incrementally, review activity/latency, restart HA and confirm the group recovers cleanly, then save a backup. Learn candidates are suggestions and must be verified against the physical device and area.\n""",
"SYSTEM_CENTER": """# System Center\n\nSystem Center combines health, recommendations, Alexa-file repair, Tuya refresh, physical group synchronization, migration status and sanitized support reports. System reports exclude known cloud secrets and raw migration payloads but can still contain entity names/IDs. Actions and reports use separate backend permissions.\n""",
"ACCESS_CONTROL": """# Access Control\n\nVersion 2.2 has two layers. Home Assistant System Access changes the real HA built-in user group: Administrator, User or Read Only, plus account active/local-only state. Only a real HA administrator can make these changes. Home Assistant 2026 does not expose supported custom Core RBAC roles, explicit deny rules or per-service ACL to HACS integrations, so the integration does not pretend otherwise. Eshtaya Access is a second backend-enforced layer for this integration only, with roles, Allow/Deny overrides and optional expiration.\n""",
"MIGRATION": """# Migration Center\n\nMigration follows Detect → Backup → Copy → Quiesce → Runtime Start → Validate → Remove Legacy → Reconcile → HACS Cleanup. Legacy entries are not removed before validation succeeds. A failed validation triggers rollback handling and preserves diagnostic state. Use Migration Report instead of deleting storage manually.\n""",
"ARCHITECTURE": """# Architecture\n\nOne config entry hosts separate managers for entities/Alexa, Tuya, Multi-Way, Smart Groups, migration, access and documentation. Frontend components call schema-validated WebSocket APIs; sensitive authorization is enforced in Python. v2.2 adds a shared resilience layer for transient WebSocket/startup failures and keeps module failures isolated.\n""",
"SECURITY_BACKUP": """# Security & Backup\n\nUse least privilege at both Home Assistant and Eshtaya layers. Keep Tuya secrets out of screenshots/issues. Take full HA backups before major updates, migration or replace-all imports; module exports complement but do not replace full backups. HA role changes use the native auth manager, protect the owner, and block self-deactivation/system-user edits.\n""",
"TROUBLESHOOTING": """# Troubleshooting\n\nIf Entity, Tuya or Groups fail to load, v2.2 retries automatically; persistent failure across all three points to backend setup/WebSocket/auth rather than one cloud service. Check Home Assistant logs for `eshtaya_smart_control`. Tuya-only timeouts usually indicate region/project/rate-limit issues. Multi-Way Recovering after restart is expected during startup grace. Documentation is served through WebSocket; a 404 usually means an old cached frontend. Distinguish Home Assistant admin denial from `Missing permission` Eshtaya denial.\n"""
}

DOCUMENTATION = {"ar": AR, "en": EN}
