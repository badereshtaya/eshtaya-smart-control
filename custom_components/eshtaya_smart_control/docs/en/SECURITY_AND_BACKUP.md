# Security and Backup

This guide explains where sensitive data is handled, what should be backed up, and how to approach migration or support without exposing project secrets.

## Tuya credentials

When Tuya Control is enabled, account configuration is stored in the Home Assistant config entry/backend.

Sensitive values such as the Client Secret should not be returned to the browser after they are saved.

Do not place Tuya secrets in:

- public screenshots;
- public GitHub issues;
- downloadable system reports;
- JavaScript or YAML under `/config/www`.

## WebSocket and backend protection

Administrative modules do not rely only on hidden buttons. Sensitive WebSocket commands are protected in the Python backend.

This matters because a browser user can inspect or manually construct requests. UI visibility is a convenience; backend authorization is the security boundary.

## Alexa files

The managed files are:

```text
/config/hidden_entities.yaml
/config/www/hidden_entities.yaml
```

They may contain entity IDs and project naming information. They are not credentials, but they can still reveal private details about a home or project. Review them before sharing publicly.

## Access Control storage

Eshtaya roles and assignments are persisted through Home Assistant storage. Avoid manually editing the storage file while Home Assistant is running unless you are performing a deliberate recovery from a known backup.

## Template Manager migration backups

When version 2.3.1 detects the old permanent-entity method, it creates a rollback backup before removing legacy definitions:

```text
/config/eshtaya_smart_control_backups/template_manager_<timestamp>/
```

The backup can include:

- legacy mappings;
- Entity Registry metadata;
- generated YAML/JSON files;
- old custom-component files when present;
- old config-entry metadata needed for recovery.

Keep this backup until migration is confirmed complete and all permanent entity IDs work correctly.

## Why cleanup is delayed

The safe order is:

```text
Detect
→ Capture
→ Backup
→ Stop / neutralize legacy
→ Release old entity IDs
→ Start unified entities
→ Verify
→ Final cleanup
```

If an old entity is still resident in Home Assistant memory, the migration uses `restart_required` rather than forcing the replacement to become `_2`.

## Home Assistant backup

Before a major Home Assistant or Eshtaya Smart Control upgrade, take a Home Assistant backup in addition to migration-specific backups.

A proper backup should protect:

- `/config`;
- `.storage` through Home Assistant’s supported backup mechanism;
- project-specific databases or external files;
- automation dependencies stored outside the integration.

## System Report

System Report is designed to be sanitized and should not expose known Tuya secrets or raw access tokens.

It may still contain operational information such as:

- entity IDs;
- integration names;
- versions;
- module health.

Review the report before publishing it outside your organization or project.

## Normal HACS update procedure

```text
Take a backup when appropriate
→ HACS Update
→ Restart Home Assistant
→ Review Dashboard / System Center
```

Do not delete the Eshtaya Smart Control config entry just to perform an update. Removing it can destroy state that a migration needs to read.

## Recovery after a migration problem

If migration does not complete:

1. Do not manually create replacement entities with the same IDs.
2. Review migration state and Home Assistant logs.
3. Keep the migration backup.
4. If the state is `rolled_back`, verify the legacy implementation returned before deleting anything manually.
5. If the state is `restart_required`, perform the documented restart first; it is a safety checkpoint, not an error.

## Least privilege

- End users normally do not need Administrator.
- Technicians should receive only the permissions required for their work.
- Access Control should be tested using real non-admin accounts.
- Any operation that changes configuration must be protected in the backend, not only hidden in the frontend.
