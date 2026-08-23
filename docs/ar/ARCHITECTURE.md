# البنية التقنية

الإنتجريشن Domain واحد: `eshtaya_smart_control`، لكن داخله Modules منفصلة حتى يبقى التطوير قابلًا للتوسع.

```text
Eshtaya Smart Control
├── Control Hub
├── HomeAssistant Entity Control
├── Tuya Entity Control
└── Multi-Way & Smart Groups
```

كل Module له Manager وWebSocket namespace خاص به، بينما يظهر للمستخدم Sidebar واحد فقط. هذا يسمح بإضافة أدوات جديدة مستقبلًا بدون خلط منطق Tuya أو Alexa أو Multi-Way مع بعضه.
