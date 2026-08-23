# Tuya Control

## Design in version 2
Tuya is an optional module. The Home Assistant integration installs without asking for any Tuya data. The first time an administrator opens Tuya Control, the module presents an activation form. After a successful test, the credentials are stored in the Home Assistant config entry and the device workspace becomes active.

## Required Tuya information
- Region/data center.
- Client ID / Access ID.
- Client Secret / Access Secret.
- User UID whose linked devices should be managed.
- Custom endpoint only when using Custom region mode.

## Activation workflow
1. Open Eshtaya Smart Control → Tuya Control.
2. Select the data center matching the Tuya IoT project.
3. Enter Client ID, Client Secret and UID.
4. Press Test Connection.
5. Confirm the returned device count/endpoint.
6. Press Activate. Save performs validation before making the account active.

The first activation timestamp and later update timestamp are tracked without exposing the secret to the frontend.

## Editing an account
Open Account Settings from Tuya Control. Existing secret values are not displayed. Leave the secret field blank to preserve the current secret when supported; enter a new value to rotate it. Test before saving.

## Deactivation
Deactivate Tuya from its dashboard. This removes only Tuya-specific fields from the unified config entry; Entity Control and Multi-Way remain installed and configured.

## Device workspace
The module lists devices for the configured UID and supports name/ID/category/product searches, online/offline filtering and pagination. Device list requests use a short backend cache to avoid excessive OpenAPI calls.

## Device details
Where returned by Tuya, details can include device ID, UUID, product ID, category, IP information and Shadow Properties. Availability of fields depends on Tuya's API and device schema.

## Rename main device
Main-name edits call Tuya OpenAPI directly. This changes the Tuya-side device name rather than only changing a Home Assistant friendly name.

## Property / gang custom names
Supported Shadow Property codes such as `switch_1`, `switch_2`, `socket_1` and `control` can expose Tuya `custom_name`. The tool only edits properties actually returned by the device; it does not invent unsupported DP codes.

## Bulk editor
Bulk loading uses bounded concurrency. Review all changes before saving because they update Tuya cloud metadata. Partial failures are reported per device where possible.

## Security model
- Client Secret stays in the backend config entry.
- Access tokens are memory-managed by the backend client.
- Request signing uses HMAC-SHA256 server-side.
- Browser status returns a masked Client ID and boolean UID state, never the secret.
- Sanitized support reports exclude Tuya credentials and tokens.

## Common failures
### Cannot connect
Verify region, credentials, UID, API service subscription and device linkage.
### Empty device list
The UID may not be linked to the project accessible by the configured cloud credentials.
### Rename rejected
The cloud project may lack permission, the device may not support the requested operation, or the property may not be exposed in Shadow Properties.
### Wrong region
Correct credentials can still fail when the project belongs to another Tuya data center.
