# Multi-Way Control

Multi-Way هو محرك التحكم البرمجي 2-way / 3-way / N-way حول خرج فيزيائي أساسي واحد. في الإصدار 2.4.0 تمت إعادة تصميم مرحلة الإقلاع حتى لا تعتبر الكيانات التابعة لتكاملات Cloud مثل Tuya مفقودة وهي ما زالت في طور الاستعادة بعد Restart.

## نموذج المجموعة

كل مجموعة تحتوي عادة على:

- **Output** واحد يمثل الحمل الفيزيائي الحقيقي.
- Controller واحد أو أكثر.
- Fallback output اختياري.
- Mode وسلوك Reliability لكل Controller.
- كيانات تحكم وصحة يتم توليدها من Eshtaya.

الـOutput يبقى المرجع الفيزيائي، والـControllers تطلب التغيير من خلال محرك المعاملات الآمن.

## أوضاع الـController

الأنماط الأساسية تشمل:

- Mirror
- Toggle
- Momentary On
- Momentary Off
- Event
- Follow Output

اختَر النمط حسب الجهاز الحقيقي. لا تضف delays عشوائية لمعالجة ضغطات مكررة قبل فحص Activity والـecho guards.

# حماية الإقلاع في 2.4.0

الإصدارات السابقة كانت تعتمد `startup_delay` ثابت يبدأ من لحظة تحميل Eshtaya. هذا لا يضمن أن Tuya الرسمية أو أي Cloud integration أنهت إنشاء States الخاصة بها.

2.4.0 يستخدم خمس طبقات حماية.

## 1. ترتيب Tuya الرسمي

في `manifest.json` تم تعريف:

```json
"after_dependencies": ["tuya"]
```

إذا كانت Tuya الرسمية مفعلة، Home Assistant يرتب تحميل Eshtaya بعدها.

## 2. Home Assistant startup-complete barrier

يتم تجهيز Runtime وListeners، لكن Multi-Way يبقى:

```text
ready = false
starting = true
```

إلى أن يعلن Home Assistant اكتمال مرحلة الإقلاع، إلا إذا عطلت هذا الخيار يدويًا من Configure.

خلال هذه المرحلة:

- لا يتم إصدار Repair لـmissing output/controller.
- الـOutput الغائب مؤقتًا يعتبر `recovering` وليس `missing_output`.
- Dashboard لا يحسب Startup recovery كـdegraded fault.
- Initial physical reconciliation مؤجل حتى الجاهزية.

## 3. انتظار التكامل المالك للكيان

لكل Output وController وFallback، يفحص Eshtaya الـEntity Registry لمعرفة Config Entry المالكة للكيان.

إذا الـState غير موجودة لكن الـConfig Entry ما زالت:

```text
setup_in_progress
setup_retry
unload_in_progress
```

فالكيان يعتبر **لسا عم يتحمل** وليس مفقودًا.

هذا أقوى من مجرد فحص وجود Entity Registry row.

## 4. Settle window

بعد توقف المصادر المرجعية عن التحميل، ينتظر Eshtaya فترة هدوء إضافية قبل تفعيل المحرك بالكامل.

الافتراضي:

```text
15 ثانية
```

## 5. Repair grace + repeated confirmation

حتى بعد انتهاء Startup Barrier، غياب الكيان مرة واحدة لا يصنع Repair.

الإعدادات الافتراضية:

```text
Repair grace: 90 ثانية
Missing confirmations: 3
```

يجب أن يبقى الكيان غائبًا طوال المهلة ثم يُرصد مفقودًا عدة مرات متتالية قبل إنشاء Repair Registry issue.

إذا ظهر الكيان في أي وقت، يتم تصفير Timer وعدّاد التأكيد الخاص به.

# إعدادات Startup

افتح:

```text
Settings → Devices & services → Eshtaya Smart Control → Configure
```

ستجد:

- انتظار اكتمال Home Assistant startup.
- انتظار التكاملات المالكة للكيانات المرجعية.
- Startup settle seconds.
- Startup maximum wait.
- Missing entity Repair grace.
- Missing confirmations.

القيم الافتراضية مناسبة للاستخدام الفعلي ومفعلة بشكل آمن.

`startup_max_wait_seconds` يمنع أي Provider معطل من إبقاء Multi-Way في الانتظار للأبد. حتى إذا وصلنا للحد الأقصى وسمحنا للمحرك أن يصبح Ready، تبقى Repair Grace فعالة قبل اعتبار أي Entity مفقودة فعليًا.

# ماذا يحدث للـRepair الكاذب القديم بعد Restart؟

عند بداية Startup محمي، Eshtaya يحذف Repairs المخزنة من نوع:

```text
missing_output_*
missing_controller_*
```

ثم لا يعيد إنشاءها إلا إذا أثبتت الفحوصات بعد كامل Startup Barrier والـGrace والـConfirmations أن الكيان فعلًا ما زال غير موجود.

هذا يمنع سيناريو مثل:

```text
Multi-way output entity is missing
```

لكيان مثل `light.updown` يظهر طبيعيًا بعد أن تنتهي Tuya من الاستعادة.

# Health states

الحالات المهمة:

- `healthy`
- `recovering`
- `degraded`
- `output_offline`
- `missing_output`
- `out_of_sync`
- `disabled`

`recovering` خلال Startup Barrier حالة طبيعية ولا تعتبر Degraded warning في Dashboard.

# أدوات الاعتمادية

المحرك يتضمن أيضًا:

- Cloud echo guards.
- Rapid physical-input handling.
- Output confirmation.
- Bounded retries.
- Source stability / settle logic.
- Activity history.
- Health وlatency diagnostics.
- Group tests بدون تغيير الحمل.
- Missing-reference remap.
- Full backup/restore.

# مجموعات Home Assistant الأصلية

اكتشاف UI/Home Assistant Groups وعمل Transactional Take Over لها **ليس Legacy Migration**. هذه الخاصية تبقى متاحة حتى لو عطلت نقل إضافات Eshtaya القديمة بالكامل.

# إذا ظهر Missing حقيقي في 2.4.0

1. تأكد أن Startup Barrier أصبح `ready`.
2. افحص قسم `startup` في System Report.
3. تأكد أن الكيان بقي غائبًا بعد Repair Grace.
4. افحص Entity Registry والـConfig Entry المالكة له.
5. أعد الكيان أو غيّر Output من Multi-Way Control.

لا تعتبر `starting` أو `recovering` أثناء Restart خطأ.
