# الهجرة التلقائية من إضافات Eshtaya القديمة

ابتداءً من **Eshtaya Smart Control 1.1.0** يتم فحص الإضافات القديمة تلقائيًا عند أول إعداد للمنصة الجديدة، وابتداءً من **1.2.0** أصبحت العملية معروضة بالكامل داخل **Migration Center**.

الإضافات المدعومة في الهجرة:

- `Eshtaya Entity Manager` — domain: `eshtaya_entity_manager`
- `Eshtaya Multi-Way Control` — domain: `eshtaya_multiway`

## ماذا يحدث تلقائيًا؟

1. يتم اكتشاف Config Entries وStorage القديمة.
2. يتم أخذ نسخة احتياطية مستقلة من قواعد Entity Control وMulti-Way وSmart Groups قبل حذف أي شيء.
3. يتم نسخ البيانات إلى Storage الخاصة بـEshtaya Smart Control فقط عندما تكون الوجهة الجديدة فارغة، حتى لا يتم استبدال إعدادات جديدة موجودة مسبقًا.
4. يتم تعطيل Config Entries القديمة مؤقتًا لإيقاف المحركات القديمة ومنع تشغيل محركين على نفس المفاتيح.
5. يتم تشغيل Entity Control وMulti-Way وSmart Groups من المنصة الجديدة.
6. تتم مقارنة عدد القواعد والجروبات المنقولة مع النسخة القديمة.
7. إذا فشل التحقق، تتم إعادة تفعيل Config Entries القديمة تلقائيًا وتبقى النسخة الاحتياطية محفوظة.
8. إذا نجح التحقق، يتم حذف Config Entries القديمة رسميًا عبر Home Assistant.
9. بعد حذف Multi-Way القديم تتم إعادة مزامنة إخفاء أعضاء Smart Groups.
10. يتم استبدال خدمات `eshtaya_multiway.*` القديمة بطبقة Compatibility تحول الطلبات إلى المحرك الجديد، حتى لا تتعطل الأوتوميشنز والسكريبتات القديمة مباشرة.
11. تحاول المنصة إزالة الريبوين القديمين من HACS باستخدام HACS نفسها، بدون حذف مجلدات `custom_components` يدويًا.

## Migration Center

يعرض **System Center → Migration Center** مسار الانتقال بشكل بصري عبر المراحل التالية:

`Detect → Backup → Copy → Stop Legacy → Start New Runtime → Validate → Remove Legacy → Reconcile → HACS Cleanup`

ويعرض لكل مرحلة:

- الحالة: Pending / Running / Completed / Failed / Rolled Back / Skipped.
- وقت البدء والانتهاء عند توفره.
- شرح مختصر للخطوة.
- الأعداد المتوقعة والفعلية بشكل آمن.

## المقارنة قبل وبعد

يعرض Migration Center مقارنة واضحة بين الإعدادات القديمة والجديدة:

- عدد قواعد Entity / Alexa.
- عدد Multi-Way Groups.
- عدد Smart Groups.

ولا تعتبر الهجرة ناجحة إلا بعد مرور Validation الخاص بالأعداد المنقولة.

## النسخة الاحتياطية

تحتفظ المنصة بنسخة Migration داخل Storage باسم:

`eshtaya_smart_control.migration_backup`

وتحتوي على إعدادات الإضافات القديمة ومعلومات Config Entries قبل عملية الانتقال.

لا يتم عرض محتوى النسخة الاحتياطية الخام في الواجهة أو في Migration Report.

## ماذا يحدث إذا فشل الانتقال؟

إذا فشل نسخ البيانات أو تشغيل الوحدة الجديدة أو التحقق منها قبل الحذف النهائي:

- لا يتم حذف الإعدادات القديمة.
- يتم إعادة تفعيل Config Entries التي عطلتها عملية الهجرة.
- يتم تسجيل سبب الفشل في Migration Center.
- يتم تعليم الخطوات المتأثرة كـRolled Back أو Failed.
- تبقى Migration Backup متاحة للاسترجاع والتحليل.

## Migration Report

يمكن تنزيل تقرير JSON من داخل Migration Center.

التقرير يحتوي على:

- إصدار Eshtaya Smart Control.
- مرحلة الهجرة الحالية.
- Timeline والخطوات وحالاتها.
- الأعداد قبل وبعد.
- نتيجة Validation.
- حالة Rollback.
- نتيجة HACS Cleanup.
- الأخطاء المسجلة إن وجدت.

لأسباب أمنية **لا يحتوي التقرير** على:

- Tuya Client Secret.
- بيانات اعتماد Tuya.
- محتوى Storage القديم الخام.
- محتوى Migration Backup الخام.

## التوافق مع الهجرة السابقة

إذا كانت الهجرة قد اكتملت سابقًا على **v1.1.0** ثم تم التحديث إلى v1.2.0، يقوم Migration Center بتحويل السجل القديم إلى Timeline مكتملة تلقائيًا بدل إظهار خطوات Pending بشكل خاطئ.

## ملاحظة عن HACS

حذف Config Entry القديمة يتم من خلال Home Assistant بعد نجاح التحقق. أما إزالة ملفات الإضافة من HACS فتتم فقط من خلال HACS API إذا كانت HACS جاهزة ومتوافقة. لا تقوم Eshtaya Smart Control بحذف مجلدات الإضافات يدويًا لأن ذلك قد يترك HACS في حالة غير متزامنة.
