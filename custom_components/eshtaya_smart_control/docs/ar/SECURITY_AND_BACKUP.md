# الأمان والنسخ الاحتياطية

هذا الدليل يوضح أين تُخزّن البيانات الحساسة، ماذا يجب نسخه احتياطيًا، وكيف تتعامل مع Migration أو دعم فني بدون كشف أسرار المشروع.

## بيانات Tuya

عند تفعيل Tuya Control يتم تخزين بيانات الحساب في Config Entry الخاصة بـHome Assistant.

البيانات الحساسة مثل Client Secret تبقى في الـbackend ولا يجب أن تُعاد إلى الواجهة بعد حفظها.

لا تضع Client Secret في:

- Screenshots عامة.
- GitHub Issues عامة.
- System Reports.
- YAML أو JavaScript مكشوف داخل `/config/www`.

## WebSocket والصلاحيات

الوحدات الإدارية لا تعتمد على إخفاء الأزرار فقط. WebSocket commands الحساسة تمر عبر فحص صلاحيات backend.

هذا مهم لأن أي مستخدم قادر على فتح Developer Tools في المتصفح يمكنه محاولة إرسال طلب يدوي؛ لذلك الحماية الحقيقية يجب أن تكون في Python backend أيضًا.

## ملفات Alexa

الملفات المدارة:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

قد تحتوي Entity IDs وأسماء بنية المنزل. ليست أسرار اعتماد مثل كلمة مرور، لكنها قد تكون معلومات خاصة عن المشروع. لا تشاركها علنًا بدون مراجعة.

## تخزين Access Control

صلاحيات Eshtaya تحفظ عبر Home Assistant Storage. لا تعدل ملف التخزين يدويًا أثناء تشغيل Home Assistant إلا في حالة استعادة مدروسة ونسخة احتياطية معروفة.

## Template Manager backups

عند اكتشاف الطريقة القديمة، 2.3.1 ينشئ Backup قبل إزالة ملفات Legacy:

```text
/config/eshtaya_smart_control_backups/template_manager_<timestamp>/
```

يمكن أن يحتوي الـBackup على:

- mappings القديمة.
- metadata من Entity Registry.
- ملفات Generated YAML/JSON.
- نسخة من custom component القديم إن وجدت.
- معلومات Config Entry اللازمة للاستعادة.

لا تحذف هذا المجلد حتى تتأكد أن Migration مكتملة وكل Entity IDs تعمل.

## لماذا لا نحذف القديم مباشرة؟

الترتيب الآمن هو:

```text
Detect
→ Capture
→ Backup
→ Stop / neutralize legacy
→ Release old Entity IDs
→ Start unified entities
→ Verify
→ Final cleanup
```

إذا بقيت الكيانات القديمة محملة في الذاكرة، يتم الدخول إلى `restart_required` بدل إجبار الكيان الجديد على أخذ اسم آخر مثل `_2`.

## Home Assistant Backup

قبل تحديث رئيسي أو Migration مهم، خذ Backup من Home Assistant نفسه بالإضافة إلى Backups الخاصة بالمهاجر.

يفضل أن يشمل النسخ:

- `/config`.
- `.storage` ضمن Backup الرسمي.
- قواعد بيانات/إعدادات مهمة للمشروع.
- أي ملفات خارجية تعتمد عليها أوتوميشنزك.

## System Report

System Report مصمم ليكون Sanitized قدر الإمكان. يجب ألا يتضمن أسرار Tuya أو raw access tokens.

مع ذلك، قد يتضمن معلومات تشغيلية مثل:

- Entity IDs.
- أسماء وحدات.
- إصدارات.
- حالة integrations.

راجع التقرير قبل نشره في مكان عام.

## تحديث HACS

للتحديث الطبيعي:

```text
خذ Backup عند الحاجة
→ HACS Update
→ Restart Home Assistant
→ راجع Dashboard / System Center
```

لا تحذف Config Entry فقط لكي "تنظف" التحديث؛ ذلك قد يحرم Migration من البيانات القديمة التي يحتاجها للنقل.

## الاستعادة بعد مشكلة

إذا فشل Migration:

1. لا تنشئ يدويًا كيانات تحمل نفس Entity IDs.
2. راجع Migration state وLogs.
3. احتفظ بمجلد Backup.
4. إذا ظهر `rolled_back` تحقق أن الطريقة القديمة عادت قبل أي حذف يدوي.
5. إذا ظهر `restart_required` نفذ Restart واحد أولًا؛ هذه ليست حالة فشل.

## مبدأ أقل صلاحية

- الزبون العادي لا يحتاج Administrator.
- الفني يحتاج فقط الصلاحيات اللازمة لعمله.
- Access Control يجب اختباره بحسابات حقيقية قبل التسليم.
- أي Service أو WebSocket يغيّر إعدادات يجب أن يكون محميًا في backend، وليس فقط مخفيًا في UI.
