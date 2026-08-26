# Dashboard

The Dashboard is the operating overview for **Eshtaya Smart Control**. It is designed to show the health of the platform and provide fast access to the modules the current user is actually allowed to use.

## What it can show

Depending on permissions and enabled modules, the Dashboard can show:

- Eshtaya Smart Control version.
- Home Assistant version.
- Overall health score.
- Entity counts and unavailable entities.
- Alexa-hidden entity count.
- Tuya activation state.
- Multi-Way and Smart Group counts.
- Template Manager status.
- Local recommendations.
- Module shortcuts.

## Health score

The health score is an operational summary based on information the integration can verify, for example:

- Alexa file synchronization.
- unavailable entities;
- degraded Multi-Way or Smart Groups;
- migration state;
- Template Manager missing sources;
- Tuya state when Tuya is enabled.

It is a diagnostic signal, not a replacement for Home Assistant logs.

## Recommendations

Recommendations are deterministic and generated from local platform state. They are intended to point you to the right repair surface, for example:

- repair Alexa files;
- inspect a migration;
- inspect degraded groups;
- configure Tuya;
- investigate unavailable entities.

## Module visibility and permissions

A module card is shown only when the current access profile contains the matching View permission:

```text
Dashboard        → dashboard.view
Entity Control   → entity.view
Tuya             → tuya.view
Multi-Way        → multi.view
Template Manager → template.view
Documentation    → docs.view
System Center    → system.view
Access Control   → access.manage
```

Version 2.3.1 synchronizes the frontend view map with the backend permission map. This fixes a 2.3.0 issue where Template Manager could be visible but clicking it produced:

```text
This role does not have access to that module.
```

although `template.view` was present in the backend.

## If a module is missing

1. Check whether the account is a Home Assistant administrator. HA admins always receive full Eshtaya module permissions.
2. For normal users, open **Access Control** as an admin.
3. Check the assigned role.
4. Check Force Allow / Force Deny overrides.
5. Read **Effective Permissions**, which is the final result.
6. Refresh the UI after changing an assignment so the access profile is fetched again.

## Dashboard vs System Center

Dashboard is for status and navigation. System Center is the deeper operational surface for:

- repair actions;
- reports;
- migration details;
- file health;
- system diagnostics.

Use Dashboard to identify what needs attention and System Center or the affected module to investigate the cause.

## Frontend cache after updates

Frontend assets are served with cache headers. The current integration version is included in the JavaScript URL, for example:

```text
smart-control-panel-v23.js?v=2.3.1
```

After a HACS update, restart Home Assistant. Version 2.3.1 changes the asset version so the browser requests the corrected JavaScript instead of reusing the 2.3.0 module.
