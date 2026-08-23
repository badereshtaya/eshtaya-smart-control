# البنية التقنية

## النطاق الموحد
Domain هو `eshtaya_smart_control`. Config Entry واحدة تمثل المنصة، بينما كل وحدة لها Managers وStorage وWebSocket namespaces معزولة.

## الطبقات
- Bootstrap في `__init__.py`: الهجرة، Entity Control، Tuya الاختيارية، Multi-Way، Panel والخدمات المتوافقة.
- Entity Control: سجل الكيانات، القواعد والملفات المولدة.
- Tuya: OpenAPI Client وManager وAdmin WebSocket؛ المتصفح لا يوقع طلبات السحابة.
- Multi-Way: Storage versioned وRuntime وNative platforms.
- Smart Groups: Store وRuntime وكيانات Domain-aware وActions وDiagnostics.
- System/Migration: Overview وتقارير منزوعة الأسرار وهجرة Transactional.
- Frontend: Sidebar واحدة Full Width تحمل الأدوات الداخلية وتنشر اختيار اللغة عبر `window.__ESHTAYA_SMART_LANG__`.

## Storage
تستخدم المفاتيح الجديدة `eshtaya_smart_control.*` حتى لا يتم الكتابة فوق Storage القديمة قبل Validation.

## الأمان
كل WebSocket إدارية require_admin. أسرار تويا تدخل عبر قناة Home Assistant الموثقة ولا تعود في Status.

## الأصول
الشعار والتوثيق والـJS موجودة محلياً داخل الحزمة بدون CDN أساسي.

## كيانات Home Assistant
Multi-Way وSmart Groups تنشئ كيانات Native ضمن المنصات المدعومة حتى تستخدمها dashboards والأوتوميشنات ككيانات حقيقية.
