# System Center

System Center is the platform-level diagnostics and operations surface for Eshtaya Smart Control. Use it when the Dashboard reports a warning, when you need a repair action, or when preparing a support report.

## What it can show

Depending on permissions and module state, System Center can include:

- platform health score;
- Home Assistant and Eshtaya Smart Control versions;
- Entity/Alexa file health;
- unavailable-entity indicators;
- sanitized Tuya status;
- Multi-Way and Smart Group summaries;
- migration state;
- recommendations;
- quick actions;
- downloadable system report.

## Quick actions

Actions are shown only when the user has the required permissions.

### Repair Alexa Files

Regenerates or repairs:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

Use it when the file-sync status is not healthy.

### Refresh Tuya

Forces a Tuya device-list refresh. A forced refresh reports the real cloud failure instead of silently presenting stale cache as a successful refresh.

### Sync Groups

Requests synchronization for managed groups. Some synchronization actions may generate real device commands, so use them as operational actions rather than read-only diagnostics.

## System report

The report is intended for support and should avoid known secrets such as:

- Tuya Client Secret;
- Tuya access tokens;
- raw migration-backup content.

It can still contain operational identifiers such as entity IDs and project-specific names, so review it before posting publicly.

## Migration Center

Important migration states include:

```text
not_found
prepared
restart_required
completed
rolled_back
error
```

### `restart_required`

For Template Manager, this is an intentional safe checkpoint. It normally means:

- legacy files were backed up;
- legacy generated definitions were removed from disk;
- old entities are still resident in Home Assistant memory;
- unified replacement entities are deferred to prevent duplicate IDs.

The correct next step is one Home Assistant restart—not removing and reinstalling Eshtaya Smart Control.

## Following a recommendation

Use the recommendation source to decide where to investigate:

- Entity/Alexa warning → Entity Control.
- Tuya warning → Tuya Control.
- Multi-Way/Smart Group warning → Multi-Way.
- Template migration warning → Template Manager and Migration Center.
- Access mismatch → Access Control as an HA admin.

## Permissions

Core System Center permissions are:

```text
system.view
system.actions
system.reports
```

An action can also require the permission of the affected module. For example, an Alexa repair should not bypass entity-management permissions.

## When to use Home Assistant logs

System Center summarizes known state but does not replace Logs. Review **Settings → System → Logs** when you see:

- setup failure;
- repeated exceptions;
- failed integration reloads;
- an entity that should exist but is not created;
- a migration that rolls back.

Search for `eshtaya_smart_control` and the affected module name.

## Useful support package

When reporting an issue, collect:

1. Home Assistant version.
2. Eshtaya Smart Control version.
3. Affected module.
4. System Report.
5. Relevant Home Assistant traceback.
6. Exact steps that reproduce the issue.
7. Migration state if migration is involved.

Do not include Tuya secrets or access tokens.
