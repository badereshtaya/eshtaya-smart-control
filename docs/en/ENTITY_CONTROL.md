# HomeAssistant Entity Control

## Purpose

Entity Control is the Home Assistant and Alexa administration module of Eshtaya Smart Control. It is designed for installations with many entities where renaming and voice-assistant exposure need to be managed quickly and consistently.

## Entity names

Renaming is performed through Home Assistant's Entity Registry. It changes the display name without requiring an external Home Assistant token or PHP endpoint. Reset removes the user-defined registry name and lets Home Assistant use the original/friendly name again.

## Alexa rule priority

The effective rule uses the following precedence:

1. Force Show.
2. Force Hide.
3. Domain disabled.
4. Automatic entity-category exclusion.
5. Automatic keyword exclusion.
6. Included.

`Force Show` is intentionally stronger than a disabled domain so a small exception can be exposed without enabling the entire domain.

## Generated files

Entity Control maintains these two files as identical copies:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

If neither exists on a fresh installation, both are created as a valid empty YAML list (`[]`). The public `/www` copy is useful for systems that retrieve the generated list through Home Assistant's `/local/` path.

## Bulk tools

Use multi-select for explicit entities, or keyword bulk edit when a naming convention identifies many entities. Filters include domain, Area, source integration/platform, availability and Alexa status.

## Import / export

`alexa_rules.json` preserves domain settings, explicit entity overrides and automatic defaults. Before a rules import, Entity Control creates a backup of the current rules.
