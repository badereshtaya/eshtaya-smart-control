# التجهيز والتسليم — Commissioning

هذا الدليل مخصص لمرحلة تجهيز مشروع حقيقي قبل تسليمه للزبون. الهدف ليس فقط أن تعمل الأجهزة مرة واحدة، بل أن يكون النظام قابلًا للاعتماد والصيانة بعد التسليم.

## قبل البدء

تأكد من:

- كل integrations الأساسية محملة بدون أخطاء حرجة.
- الأجهزة تحمل أسماء واضحة ومناطق Areas صحيحة.
- مصدر كل جهاز معروف، خصوصًا Tuya switches المستخدمة خلف Template Manager.
- لا توجد Migration عالقة.
- وقت وتاريخ Home Assistant صحيحان.
- لديك Backup حديث قبل تغييرات كبيرة.

## ترتيب التجهيز المقترح

### 1. الكيانات والأسماء

ابدأ من Entity & Alexa Control:

- صحح Friendly Names.
- تأكد من Entity IDs المهمة قبل بناء أوتوميشنز كثيرة عليها.
- راجع الكيانات unavailable.
- اضبط سياسة Alexa.

### 2. Template Manager

إذا كنت تريد كيان Light/Fan دائم فوق switch:

- اختر المصدر الصحيح.
- حدد النوع Light أو Fan.
- استخدم Entity ID نهائي منطقي.
- لا تغيّر المصدر الفيزيائي في الأوتوميشنز بعد اعتماد الكيان الدائم؛ اجعل الأوتوميشن تعتمد على الكيان الدائم قدر الإمكان.

إذا كان هناك نقل من الطريقة القديمة، لا تنشئ يدويًا كيانات بديلة أثناء Migration. انتظر انتهاء النقل أو Restart Required حتى لا تصنع Duplication بنفسك.

### 3. Multi-Way

لكل مجموعة:

- حدد Output الفعلي بشكل واضح.
- أضف Controllers فقط بعد التأكد من Entity IDs.
- اختر Mode المناسب: Mirror / Toggle / Momentary / Event / Follow حسب نوع الزر وسلوك النظام.
- اختبر الضغط السريع والمتكرر.
- اختبر تغيير الحالة من الجهاز الفعلي ومن Home Assistant.
- راقب Activity وHealth.

### 4. Smart Groups وAction Groups

اختبر:

- تشغيل المجموعة.
- إطفاء المجموعة.
- تغير عضو منفرد.
- Member unavailable.
- Failure policy.
- Sequential/Parallel execution في Action Groups.

### 5. Tuya Cloud

إذا كانت الوحدة مفعلة:

- اعمل Refresh لقائمة الأجهزة.
- تأكد من Online/Offline بشكل واقعي.
- اختبر Rename أو Shadow Properties فقط على جهاز معروف.
- لا تعمل Bulk change كبير قبل تجربة جهاز أو جهازين.

## اختبارات الاستجابة

لا يكفي اختبار زر واحد مرة واحدة. استخدم سيناريوهات مثل:

```text
ON → OFF → ON بسرعة
ضغط متكرر على controller
تغيير من تطبيق Tuya أثناء فتح Home Assistant
إعادة تشغيل Home Assistant ثم اختبار أول ضغطة
فصل الإنترنت ثم عودته
جهاز unavailable ثم رجوعه
```

الهدف اكتشاف race conditions وcloud echo وstartup timing قبل التسليم.

## اختبارات Restart

قبل تسليم مشروع يعتمد على Multi-Way أو Template Manager:

1. احفظ Backup.
2. أعد تشغيل Home Assistant.
3. لا تلمس الأزرار أثناء مرحلة الإقلاع الأولى إلا إذا كنت تختبر startup behavior عمدًا.
4. بعد اكتمال integrations اختبر كل مجموعة حرجة.
5. تأكد أن Entity IDs لم تتحول إلى `_2` أو `_3`.
6. تأكد أن Template Manager لا يعرض Migration Error.

## اختبار المستخدم النهائي

أنشئ/استخدم حسابًا غير Admin يمثل الزبون واختبر:

- هل يرى فقط الأقسام المطلوبة؟
- هل التحكم المطلوب يعمل؟
- هل الأقسام الإدارية مخفية؟
- هل رسالة `This role does not have access to that module` تظهر فقط عند محاولة دخول قسم غير مسموح فعلًا؟

لا تعتمد على تجربة حساب Administrator فقط لأن Admin يتجاوز صلاحيات Eshtaya الداخلية.

## التسليم

قبل اعتبار المشروع منتهيًا:

- Health Score مقبول ولا توجد Recommendations حرجة غير مفهومة.
- ملفات Alexa synchronized.
- لا توجد Missing Templates غير مقصودة.
- مجموعات Multi-Way وSmart Groups مستقرة.
- حسابات المستخدمين وصلاحياتهم مجربة.
- Backup محفوظ.
- أسماء الأجهزة والمناطق مفهومة للزبون وللدعم الفني.
- وثّق أي استثناء معروف في المشروع.

## بعد التسليم

عند أي تعديل لاحق:

- غيّر شيئًا واحدًا في كل مرة قدر الإمكان.
- راقب Activity/Diagnostics بعد التغيير.
- لا تحذف ملفات Migration backups أثناء وجود مشكلة غير محسومة.
- قبل تحديث كبير للإضافة أو Home Assistant خذ Backup كامل.
