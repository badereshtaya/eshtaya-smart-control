# HomeAssistant Entity Control

## الهدف

هذا القسم مسؤول عن إدارة كيانات Home Assistant وما يظهر منها في Alexa من داخل لوحة واحدة، وهو مناسب خصوصًا للمشاريع التي تحتوي مئات الكيانات.

## تغيير الأسماء

تغيير الاسم يتم من خلال Entity Registry في Home Assistant نفسه، بدون Long-Lived Token وبدون صفحة PHP خارجية. زر الإرجاع يزيل الاسم المخصص ويعيد الاعتماد على الاسم الأصلي/الافتراضي.

## أولوية قواعد Alexa

1. إظهار إجباري Force Show.
2. إخفاء إجباري Force Hide.
3. Domain موقوف.
4. استثناء تلقائي حسب Entity Category.
5. استثناء تلقائي حسب الكلمات.
6. ظاهر في Alexa.

## الملفات الناتجة

يتم إبقاء الملفين التاليين متطابقين دائمًا:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

إذا كان التثبيت جديدًا ولا يوجد أي منهما، يتم إنشاؤهما كقائمة YAML فارغة صحيحة `[]`.

## الأدوات الجماعية

يمكن تحديد عدة Entities يدويًا ثم Show/Hide/Auto، أو استخدام البحث بالكلمة. الفلاتر تشمل Domain وArea والـIntegration/Platform والتوفر وحالة Alexa.

## النسخ والاسترجاع

يدعم `alexa_rules.json` لنقل Domains وForce Show/Hide وقواعد Auto بين أكثر من Home Assistant، مع Backup تلقائي قبل الاستيراد.
