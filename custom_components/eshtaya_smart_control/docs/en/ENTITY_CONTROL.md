# Entity & Alexa Control

## Purpose
Entity & Alexa Control is the large-installation administration surface for Home Assistant entity display names and Alexa exposure rules. It writes through Home Assistant's Entity Registry and maintains two generated exclusion files from one rule model.

## Core concepts
### Display name
Changing the display name updates the Home Assistant Entity Registry name override. It does not blindly change `entity_id`, so dashboards and automations are not rewritten unexpectedly.

### Exposure modes
Each entity has three explicit states:
- Auto: evaluate domain and automatic rules.
- Force Show: expose even when a broader automatic rule would hide it.
- Force Hide: always place it in the generated exclusion output.

Effective precedence is Force Show → Force Hide → disabled domain → entity-category exclusion → keyword exclusion → included.

## Domain rules
Domain rules are useful when voice assistants should never receive whole technical domains such as diagnostics. A Force Show exception can still expose a deliberate individual entity.

## Automatic categories and keywords
Entity categories such as diagnostic/config and installer-defined name keywords can be excluded automatically. Use precise keywords to avoid hiding legitimate user controls.

## Search and filters
Use text search, domain, area, integration/platform, availability, effective Alexa state and explicit override filters. On large installations, combine filters before selecting entities for bulk actions.

## Bulk actions
Select many entities and set Auto, Force Show or Force Hide in one operation. Changes regenerate the authoritative output. Review the result count before applying a broad rule.

## Orphan rules
An orphan rule points to an entity no longer present in the current registry. The tool does not silently delete it because a temporarily unavailable integration may return. Cleanup is an explicit maintenance operation.

## Generated files
The module manages:
- `/config/hidden_entities.yaml`
- `/config/www/hidden_entities.yaml`

Both copies are generated from the same source and are expected to be byte-identical. A fresh installation creates valid empty YAML (`[]`) when necessary.

## File health and repair
System Center and the module report synchronization state using metadata/hashes. Repair regenerates both copies from the stored rule model. Manual edits to generated files can be overwritten.

## Import and export
`alexa_rules.json` is a portable rules format for domain settings, per-entity overrides, automatic category exclusions and keyword exclusions. Import validates/normalizes data and preserves a safety backup before replacement where supported.

## Naming workflow
1. Search for the entity.
2. Confirm the device and area.
3. Edit the display name.
4. Confirm the new Registry name appears in Home Assistant.
5. Set Alexa rule only when an explicit exception is needed.
6. Review file health after bulk changes.

## Troubleshooting
If an entity remains hidden, check explicit Force Hide, domain rules, category and keyword rules in precedence order. If file health is red, use Repair from System Center. If an entity is missing, verify its source integration is loaded before deleting its orphan rule.
