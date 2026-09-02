# البدء مع Eshtaya Smart Control

هذا الدليل يشرح التثبيت والتحديث وأول تشغيل بطريقة مناسبة للاستخدام الفعلي داخل Home Assistant.

## ما هي الإضافة؟

**Eshtaya Smart Control** منصة إدارة موحدة داخل Home Assistant تشمل:

- إدارة الكيانات وسياسة إظهارها أو إخفائها في Alexa.
- إدارة Tuya Cloud عند الحاجة.
- Multi-Way وSmart Groups وAction Groups.
- Template Manager لإنشاء كيانات Light/Fan دائمة فوق مفاتيح فعلية.
- مركز النظام والتشخيص والتقارير.
- صلاحيات Eshtaya الداخلية وأدوات الوصول المدعومة من Home Assistant.
- مركز Documentation عربي/إنجليزي.

# التثبيت عبر HACS

1. افتح **HACS → Integrations**.
2. أضف المستودع المخصص:

```text
https://github.com/badereshtaya/hacs-eshtaya-smart-control
```

3. ثبّت **Eshtaya Smart Control**.
4. أعد تشغيل Home Assistant.
5. افتح **Settings → Devices & services → Add integration**.
6. ابحث عن **Eshtaya Smart Control** وأكمل الإضافة.

لا يتم طلب بيانات Tuya OpenAPI أثناء التثبيت الأول. Tuya Control اختيارية.

# التحديث من إصدار سابق

المسار الصحيح:

```text
HACS → Eshtaya Smart Control → Update
→ Restart Home Assistant
→ افتح Eshtaya Smart Control
```

**لا تحذف Config Entry الموحدة فقط لأجل التحديث.**

# ما الجديد المهم في 2.4.0؟

الإصدار 2.4.0 يضيف Startup Barrier حقيقي للتكاملات البطيئة أو Cloud-backed مثل Tuya الرسمية.

المحرك القديم كان يعتمد تأخيرًا ثابتًا يبدأ من وقت تحميل Eshtaya. إذا انتهت المدة قبل أن تعيد Tuya إنشاء كيان مثل:

```text
light.updown
```

كان ممكن يظهر Repair كاذب:

```text
Multi-way output entity is missing
```

في 2.4.0 أصبحت الحماية على خمس طبقات:

1. ترتيب تحميل Eshtaya بعد Tuya الرسمية عندما تكون مفعلة.
2. انتظار Home Assistant startup-complete.
3. انتظار Config Entries المالكة للكيانات المرجعية إذا كانت ما زالت تحمل أو تعيد المحاولة.
4. فترة Settle إضافية بعد استقرار المصادر.
5. Repair Grace بعد الإقلاع مع عدة تأكيدات قبل اعتبار الكيان مفقودًا فعليًا.

خلال Startup المحمي تظهر Multi-Way كـ`starting/recovering` وليس Fault، ولا يتم إصدار Missing Output/Controller Repair.

الإعدادات الافتراضية الموصى بها:

```text
Wait for Home Assistant startup:       On
Wait for referenced integrations:      On
Startup settle:                         15 ثانية
Startup maximum wait:                  240 ثانية
Missing Repair grace:                  90 ثانية
Missing confirmations:                 3
```

# إعدادات Startup وMigration

افتح:

```text
Settings → Devices & services
→ Eshtaya Smart Control
→ Configure
```

عند حفظ الإعدادات يتم Reload للـConfig Entry تلقائيًا.

## الإعداد المناسب بعد إنهاء Migration القديمة

إذا نقلت كل أدوات Eshtaya القديمة وانتهيت منها، استخدم:

```text
Enable legacy Eshtaya migration: Off
Legacy HACS cleanup:             Off
Legacy service aliases:          Off
```

يمكن ترك خيارات Entity Manager / Multi-Way / Template Manager الفرعية مفعلة؛ لا تعمل طالما Master Legacy Migration مطفأ.

إذا كان هناك Cutover قديم بدأ فعليًا قبل التحديث ووصل إلى مرحلة حساسة مثل `restart_required`، يسمح له النظام بالإكمال حتى لا يبقى النظام في منتصف Migration.

## Home Assistant Groups تبقى شغالة

اكتشاف Group helpers الأصلية وعمل Transactional Take Over لها **ليس Legacy Migration**، ويظل متاحًا عندما تكون Migration الأدوات القديمة مطفأة.

# إذا كان Template Manager القديم ما زال بمنتصف النقل

إذا كانت الحالة:

```text
restart_required
```

نفذ Restart المطلوب. تبقى الكيانات الجديدة Deferred حتى تتحرر Entity IDs القديمة، وهذا يمنع `_2` وتشغيل محركين لنفس المصدر.

إذا كانت Migration عندك مكتملة أصلًا، اترك Legacy Migration مطفأة.

# أول جولة داخل المنصة

راجع بالترتيب:

1. **Dashboard**: Health Score وحالة Startup والوحدات.
2. **Entity & Alexa Control**: الكيانات وملفات hidden entities.
3. **Tuya Control**: فعّلها فقط إذا احتجت إدارة Cloud مباشرة.
4. **Multi-Way**: افحص المجموعات وحالة Startup/Health.
5. **Template Manager**: افحص Managed / Available / Missing.
6. **System Center**: Startup Barrier وMigration history والتقارير والتنبيهات.
7. **Access Control**: راجع صلاحيات المستخدمين قبل التسليم.

# الصلاحيات

هناك طبقتان مختلفتان:

- **Eshtaya permissions** تتحكم بمن يستطيع دخول أو إدارة وحدات Eshtaya.
- **Home Assistant Core access** يتحكم بأدوار الحساب الأساسية المدعومة من Home Assistant.

إعطاء `template.manage` لا يجعل المستخدم Home Assistant Administrator.

# قبل التسليم

تأكد من:

- Startup Barrier يصل إلى `ready` بعد Restart.
- عدم ظهور Missing Output Repair كاذب أثناء تحميل Tuya أو أي Provider بطيء.
- عدم وجود Migration Error غير مفهوم.
- عدم وجود Managed Template بمصدر مفقود إلا إذا كان ذلك مقصودًا.
- Multi-Way وSmart Groups سليمة بعد انتهاء Startup.
- ملفي Alexa متزامنين.
- الصلاحيات مجربة بحساب مستخدم عادي.
- وجود Home Assistant Backup حديث.

للتفاصيل راجع الأدلة المتخصصة داخل `docs/ar` أو Documentation Center داخل الإضافة.
