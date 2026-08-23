# الهجرة التلقائية من الإضافات القديمة

## المدعوم
Eshtaya Entity Manager (`eshtaya_entity_manager`) وEshtaya Multi-Way Control (`eshtaya_multiway`).

## الفكرة
الهجرة Cutover محمي وليس نسخاً أعمى. تكتشف القديم، تأخذ Backup مستقل، تنسخ إلى Storage الجديدة فقط عندما تكون الوجهة مناسبة، توقف المحرك القديم قبل تشغيل الجديد، تقارن الأعداد، ثم تحذف Config Entries القديمة فقط بعد نجاح Validation.

## المراحل
1. اكتشاف Entries وStorage القديمة.
2. Backup للإعدادات وبيانات Config Entries.
3. نسخ قواعد Entity وMulti-Way وSmart Groups.
4. تعطيل القديم لمنع محركين على نفس الأجهزة.
5. تشغيل Runtime الجديدة.
6. مقارنة Expected وActual.
7. حذف Config Entries بعد نجاح التحقق.
8. Reconcile لملكية Hidden Members.
9. محاولة تنظيف HACS من خلال API الخاصة بها.

## النسخة الاحتياطية
المفتاح الداخلي `eshtaya_smart_control.migration_backup`. التقرير يظهر اسم النسخة وليس محتواها الخام.

## Rollback
إذا فشل التشغيل أو التحقق قبل التنظيف النهائي، يعيد النظام تفعيل Entries التي عطلها ويسجل السبب. مع ذلك يبقى Full Backup لـHome Assistant أهم شبكة أمان.

## الخدمات القديمة
بعد إزالة Multi-Way القديم، Compatibility aliases تحافظ على خدمات `eshtaya_multiway.*` الشائعة وتوجهها للمحرك الجديد لتقليل كسر الأوتوميشنات أثناء الانتقال.

## تحديث v1.x
إذا كانت الهجرة مكتملة مسبقاً، تحديث Eshtaya Smart Control لا يعيد الاستحواذ بشكل مدمر؛ يستخدم Storage وConfig Entry الموحدة الموجودة.
