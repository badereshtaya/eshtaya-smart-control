# البدء مع Eshtaya Smart Control

هذا الدليل يشرح التثبيت والتحديث وأول تشغيل بطريقة مناسبة للاستخدام الفعلي داخل Home Assistant.

## ما هي الإضافة؟

**Eshtaya Smart Control** منصة إدارة موحدة داخل Home Assistant تشمل:

- إدارة الكيانات وسياسة إظهارها أو إخفائها في Alexa.
- إدارة Tuya Cloud عند الحاجة.
- Multi-Way وSmart Groups وAction Groups.
- Template Manager لإنشاء كيانات Light/Fan دائمة فوق مفاتيح Tuya.
- مركز النظام والتشخيص والتقارير.
- صلاحيات Eshtaya الداخلية، بالإضافة إلى إدارة أدوار Home Assistant الأساسية للمستخدمين عندما يسمح Core بذلك.
- مركز Documentation عربي/إنجليزي.

## التثبيت الجديد عبر HACS

1. افتح **HACS → Integrations**.
2. أضف المستودع المخصص:

```text
https://github.com/badereshtaya/hacs-eshtaya-smart-control
```

3. اختر **Integration** ثم ثبّت **Eshtaya Smart Control**.
4. أعد تشغيل Home Assistant.
5. افتح **Settings → Devices & services → Add integration**.
6. ابحث عن **Eshtaya Smart Control** وأكمل الإضافة.

لا يتم طلب بيانات Tuya أثناء التثبيت الأول. Tuya اختيارية ويتم تفعيلها من داخل تبويب Tuya Control.

## التحديث من إصدار سابق

التحديث الطبيعي هو السيناريو المدعوم والمفضل:

```text
HACS → Eshtaya Smart Control → Update
→ Restart Home Assistant
→ افتح Eshtaya Smart Control
```

**لا تحتاج إلى حذف الإضافة وإعادة تثبيتها.** حذف الـConfig Entry ليس مطلوبًا للتحديث وقد يزيل حالة أو إعدادات كان يمكن نقلها تلقائيًا.

الإصدار 2.3.1 يغيّر رقم نسخة ملفات الواجهة، لذلك بعد Restart يجب أن يحمّل Home Assistant JavaScript الجديد بدل النسخة المخزنة في الكاش. إذا بقي المتصفح يعرض واجهة قديمة بشكل غير طبيعي يمكن عمل Refresh للصفحة، لكن مسار التحديث نفسه لا يعتمد على حذف الإضافة.

## إذا كنت تستخدم Template Manager القديم

الإصدار 2.3.1 يدعم النقل من الطريقة القديمة حتى عندما كانت تعتمد على ملفات Generated YAML/JSON وليس Config Entry مستقل فقط.

المهاجر يبحث عن مصادر مثل:

```text
/config/packages/eshtaya_generated_templates.yaml
/config/packages/eshtaya_generated_lights.yaml
/config/eshtaya_template_manager/generated_templates.yaml
/config/eshtaya_template_manager/templates.json
/config/eshtaya_template_manager/mappings.json
```

قبل أي حذف يتم إنشاء Backup داخل:

```text
/config/eshtaya_smart_control_backups/
```

ثم تتم محاولة تحرير Entity IDs القديمة. إذا بقيت كيانات Template القديمة محملة في ذاكرة Home Assistant، يتم إيقاف إنشاء الكيانات الجديدة مؤقتًا وتظهر حالة **Restart Required**. هذا مقصود لمنع ظهور `*_2` أو تشغيل محركين لنفس الإضاءة. بعد Restart التالي يكمل النقل بنفس Entity IDs.

## أول جولة داخل المنصة

بعد فتح لوحة Eshtaya Smart Control راجع بالترتيب:

1. **Dashboard**: تأكد من Health Score وحالة الوحدات.
2. **Entity & Alexa Control**: افحص الكيانات وملفات hidden entities.
3. **Tuya Control**: فعّل حساب Tuya فقط إذا احتجت إدارة Cloud مباشرة.
4. **Multi-Way**: افحص المجموعات وحالة Health لكل مجموعة.
5. **Template Manager**: افحص Managed / Available / Missing وحالة Migration.
6. **System Center**: راجع التنبيهات وMigration Center والتقارير.
7. **Access Control**: راجع صلاحيات المستخدمين قبل تسليم المشروع.

## الصلاحيات عند أول تشغيل

مدير Home Assistant الحقيقي يحصل على صلاحيات Eshtaya كاملة. المستخدمون العاديون يحتاجون دورًا أو صلاحيات داخل Access Control.

هناك طبقتان مختلفتان:

- **Eshtaya permissions**: تتحكم بمن يستطيع دخول أو إدارة وحدات الإضافة.
- **Home Assistant Core access**: أدوار الحساب الأساسية مثل Administrator / User / Read Only، وتطبق على النظام كله حسب قدرات Home Assistant الحالية.

لا تخلط بين الطبقتين؛ إعطاء `template.manage` مثلًا لا يجعل المستخدم Home Assistant Administrator.

## متى تعتبر المنصة جاهزة؟

قبل تسليم مشروع فعلي تأكد من:

- عدم وجود Migration عالقة أو Error غير مفهوم.
- عدم وجود Managed Template بمصدر مفقود إلا إذا كان ذلك مقصودًا.
- Multi-Way وSmart Groups بحالة سليمة.
- ملفي Alexa متزامنين.
- الصلاحيات مجربة بحساب مستخدم عادي، وليس بحساب Admin فقط.
- وجود Backup حديث لإعدادات Home Assistant.

للتفاصيل راجع الأدلة المتخصصة داخل مجلد `docs/ar` أو من Documentation Center داخل الإضافة.
