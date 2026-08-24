# مركز النظام — System Center

System Center هو طبقة التشخيص والإدارة العامة فوق وحدات Eshtaya Smart Control. استخدمه عندما تريد معرفة **لماذا** ظهر Warning في Dashboard أو عندما تحتاج تقريرًا أو إجراء إصلاح مركزي.

## ما الذي يعرضه؟

حسب الصلاحيات وحالة الوحدات يمكن أن يعرض:

- Health Score وحالة المنصة.
- إصدار Home Assistant وإصدار Eshtaya Smart Control.
- حالة Entity & Alexa files.
- مؤشرات unavailable entities.
- حالة Tuya الآمنة بدون كشف Client Secret.
- ملخص Multi-Way وSmart Groups.
- حالة Migration.
- Recommendations.
- Quick Actions.
- System Report.

## Quick Actions

الإجراءات تظهر فقط إذا كان لدى المستخدم الصلاحيات اللازمة. أمثلة:

### Repair Alexa Files

يعيد توليد/مزامنة ملفات:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

استخدمه عندما تظهر حالة file sync غير سليمة.

### Refresh Tuya

يجبر تحديث قائمة أجهزة Tuya. التحديث القسري لا يخفي خطأ Cloud خلف Cache قديم؛ إذا فشل الطلب يتم إظهار الخطأ بدل اعتباره نجاحًا.

### Sync Groups

يطلب مزامنة مجموعات التحكم. بعض عمليات المزامنة قد تؤدي إلى أوامر فعلية للأجهزة، لذلك الواجهة تميز الإجراءات التي لها تأثير فيزيائي.

## System Report

التقرير مصمم للدعم الفني ويعرض معلومات تشخيصية بدون أسرار حساسة معروفة.

لا يجب أن يحتوي على:

- Tuya Client Secret.
- Tuya access token.
- محتويات خام حساسة من Migration backup.

قبل مشاركة أي تقرير خارجيًا، راجعه دائمًا إذا كان المشروع يحتوي على أسماء أو Entity IDs تعتبرها خاصة.

## Migration Center

يعرض مراحل النقل من الأدوات القديمة. من الحالات المهمة:

```text
not_found
prepared
restart_required
completed
rolled_back
error
```

### restart_required

في Template Manager تعني هذه الحالة عادة:

- تم أخذ Backup.
- تم حذف تعريفات Generated القديمة من القرص.
- الكيانات القديمة ما زالت محملة في ذاكرة Home Assistant.
- الكيانات الجديدة مؤجلة عمدًا لمنع duplicate Entity IDs.

الحل الصحيح هو Restart واحد لـHome Assistant، وليس حذف Eshtaya Smart Control وإعادة تثبيتها.

## Recommendations وكيف تقرأها

Recommendation ليست مجرد رسالة تجميلية؛ حاول تتبع مصدرها:

- Entity/Alexa → افتح Entity Control.
- Tuya → افتح Tuya Control.
- Multi-Way/Smart Group → افتح تبويب Multi-Way.
- Template migration → افتح Template Manager وMigration Center.
- Permission mismatch → افتح Access Control بحساب Admin.

## الصلاحيات

الصلاحيات الأساسية:

```text
system.view
system.actions
system.reports
```

قد يحتاج الإجراء أيضًا صلاحية الوحدة نفسها. مثال: Repair Alexa Files يتوقع صلاحية إدارة الكيانات، وSync Groups يتوقع صلاحية تحكم بالمجموعات.

## متى تستخدم Logs Home Assistant؟

System Center يعطي ملخصًا منظمًا، لكنه لا يستبدل Logs. إذا وجدت:

- Setup failure.
- Exception متكرر.
- Integration reload يفشل.
- Entity لا يظهر رغم أن المصدر موجود.

راجع **Settings → System → Logs** وابحث عن `eshtaya_smart_control` مع اسم الوحدة المتأثرة.

## نصيحة للدعم

عند فتح مشكلة، اجمع بالترتيب:

1. إصدار Home Assistant.
2. إصدار Eshtaya Smart Control.
3. حالة الوحدة.
4. System Report.
5. السطر/الـtrace المتعلق بالمشكلة من Logs.
6. الخطوات التي تعيد المشكلة بشكل ثابت.

هذا أسرع بكثير من الاعتماد على صورة شاشة فقط.
