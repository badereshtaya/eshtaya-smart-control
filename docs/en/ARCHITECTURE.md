# Architecture

`eshtaya_smart_control` is one Home Assistant integration with modular internal engines.

```text
Eshtaya Smart Control
├── Control Hub / unified panel
├── Entity Control
│   ├── Entity Registry naming
│   └── Alexa rule + YAML generator
├── Tuya Entity Control
│   ├── OpenAPI client/signing
│   ├── account manager/cache
│   └── admin WebSocket API
└── Multi-Way & Smart Groups
    ├── MultiWayManager / storage
    ├── SmartGroupManager / storage
    ├── native HA platforms
    └── commissioning / health / migration tools
```

All tool WebSocket APIs are explicitly namespaced. The unified panel is the only sidebar entry.
