# Architecture

## Unified domain
The integration domain is `eshtaya_smart_control`. One config entry owns the administrative platform while internal modules maintain isolated manager/storage/WebSocket namespaces.

## Core layers
### Bootstrap
`__init__.py` coordinates migration, Entity Control, optional Tuya manager, Multi-Way runtime, panel registration and compatibility services.
### Entity Control
Registry-aware manager plus persistent rules and dual generated YAML output.
### Tuya
Backend OpenAPI client, account manager and admin-only WebSocket API. The frontend never signs cloud requests.
### Multi-Way
Versioned store, runtime manager, native entity platforms and services.
### Smart Groups
Versioned high-level store, runtime, domain-specific virtual entities, actions, diagnostics and takeover workflows.
### System/Migration
Sanitized overview/report endpoints and transactional migration coordinator.
### Frontend
A single full-width sidebar shell loads embedded module custom elements. Language choice is propagated through `window.__ESHTAYA_SMART_LANG__` so embedded modules follow the unified setting.

## Storage namespaces
Unified stores use `eshtaya_smart_control.*` keys to avoid overwriting live legacy storage before migration validation.

## WebSocket security
Management APIs are registered with Home Assistant WebSocket API and require administrator access. Tuya credentials are accepted only over authenticated admin calls and are not returned in status.

## Static assets
The panel serves local frontend assets through the Home Assistant static path. Documentation and logo assets are packaged locally; no CDN is required for core operation.

## Platform entities
Multi-Way/Smart Groups forward supported native Home Assistant platforms so managed controls remain first-class entities usable by dashboards, scripts and automations.

## Failure isolation
Module errors should not expose secrets. Migration uses rollback. Tuya is optional. Smart recommendations summarize known faults without replacing module-specific diagnostics.
