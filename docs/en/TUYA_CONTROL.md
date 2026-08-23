# Tuya Entity Control

## Purpose

Tuya Entity Control replaces the former external PHP dashboard with a native Home Assistant tool. Browser code talks only to Home Assistant WebSocket APIs; Tuya OpenAPI requests and signing happen in the backend.

## Account configuration

Each Home Assistant installation has its own account configuration:

- Region.
- Endpoint (for Custom region).
- Client ID.
- Client Secret.
- UID.

Use **Test connection** before saving. When editing an existing account, blank credential fields keep their saved values.

## Device management

The tool can:

- List devices for the configured Tuya UID.
- Show online/offline state and category.
- Search and filter the project.
- Read device details.
- Read Tuya Shadow Properties.
- Rename the main Tuya device.
- Rename available `switch_x`, `socket_x` and `control` properties using `custom_name`.
- Load and save many devices from the Bulk Editor.

## API paths used

```text
GET  /v1.0/token?grant_type=1
GET  /v1.0/users/{uid}/devices
GET  /v1.0/devices/{device_id}
GET  /v2.0/cloud/thing/{device_id}/shadow/properties
PUT  /v1.0/devices/{device_id}
POST /v2.0/cloud/thing/{device_id}/shadow/properties
```

Requests use Tuya's HMAC-SHA256 signing flow. Access tokens and Client Secret never need to be exposed to the browser.

## Large projects

Device-list results are cached in the backend for 20 seconds. Bulk Shadow Property loading uses bounded concurrency to reduce API bursts. The frontend paginates the project for easier operation.
