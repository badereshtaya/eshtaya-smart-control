# Migration

## General rule

Migration is designed to be explicit. Avoid enabling an old engine and the new integrated engine over the same physical devices at the same time.

## Entity Manager

When the new Entity Control storage is empty it can reuse the former standalone Entity Manager storage. Existing `hidden_entities.yaml` files are also imported safely. `alexa_rules.json` remains the portable migration format.

## Multi-Way

Use the old integration's full backup/export feature, then restore/import into the integrated module. Verify all virtual entities and automations before disabling the old integration.

The platform does not silently seize old virtual entity registry entries because doing so while the old integration is loaded could create duplicate or unavailable entities.
