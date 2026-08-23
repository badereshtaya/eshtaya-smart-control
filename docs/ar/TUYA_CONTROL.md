# Tuya Entity Control

## الهدف

هذا القسم يحول لوحة Tuya القديمة من صفحة PHP خارجية إلى أداة Native داخل Home Assistant. المتصفح لا يتصل بـTuya مباشرة؛ كل التوقيع والطلبات تتم في Backend الإنتجريشن.

## إعداد الحساب

لكل Home Assistant إعداد مستقل:

- Region.
- Endpoint عند اختيار Custom.
- Client ID.
- Client Secret.
- UID.

استخدم **اختبار الاتصال** قبل الحفظ. عند تعديل حساب موجود يمكنك ترك بيانات الاعتماد فارغة للاحتفاظ بالقيم الحالية.

## إدارة الأجهزة

يدعم:

- قائمة أجهزة المشروع.
- Online / Offline.
- تصنيف ذكي عربي/إنجليزي.
- البحث بالاسم وDevice ID والنوع وProduct ID.
- تفاصيل UUID وProduct وIP عندما توفرها Tuya.
- تعديل الاسم الرئيسي للجهاز.
- قراءة Shadow Properties.
- تعديل `custom_name` للخصائص الفعلية `switch_x` و`socket_x` و`control`.
- Bulk Edit لأكثر من جهاز.
- Pagination للمشاريع الكبيرة.

## الأمان

Client Secret وAccess Token لا يتم إرجاعهما للواجهة ولا حفظهما في JavaScript. يتم حفظ الإعدادات ضمن Config Entry في Home Assistant.
