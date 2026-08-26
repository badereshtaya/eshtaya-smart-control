# Access Control

Eshtaya Smart Control has **two distinct access layers**. Keeping them separate prevents accidental privilege escalation and avoids pretending Home Assistant Core supports a custom RBAC feature that it does not currently expose publicly.

# 1. Eshtaya Smart Control permissions

These permissions control what a user can see or execute **inside Eshtaya Smart Control**.

Current permissions include:

```text
dashboard.view
entity.view
entity.manage

tuya.view
tuya.control
tuya.configure

multi.view
multi.control
multi.manage

template.view
template.manage

docs.view

system.view
system.actions
system.reports

access.manage
```

## Built-in roles

### No Access

No Eshtaya module access.

### Viewer

Read-only access to the normal operational modules.

### Operator

Adds normal operational control without broad configuration privileges.

### Technician

Broad technical management permissions for entities, groups, Template Manager, and diagnostics.

### Platform Manager

All Eshtaya Smart Control permissions.

A real Home Assistant administrator always receives full Eshtaya module permissions and cannot be restricted by the local Eshtaya role layer.

## Force Allow and Force Deny

A user assignment can override the base role:

- **Force Allow** adds a permission.
- **Force Deny** removes a permission.

The resulting **Effective Permissions** list is the final access profile used by the backend and frontend.

## Temporary assignments

Assignments can include an expiry time. After expiration the user falls back to the configured default behavior rather than retaining temporary access indefinitely.

# 2. Home Assistant Core access

This layer changes the actual Home Assistant account role, not only Eshtaya modules.

The integration uses supported Core concepts such as:

- Administrator
- User
- Read Only

when they can be applied safely using Home Assistant’s current auth model.

## Administrator

Administrator is a Home Assistant system-wide privilege level. Do not grant it simply because a user needs to control lights or open a specific Eshtaya tab.

## User

A normal Home Assistant user. Core still protects administrative pages and operations.

## Read Only

Uses Home Assistant’s built-in read-only group and its native permission behavior.

# Current Home Assistant limitations

Home Assistant does not currently expose a supported public HACS API for arbitrary custom system-wide RBAC roles with explicit deny policies for every service, dashboard, and entity operation.

Eshtaya therefore distinguishes between:

- **Home Assistant Core account role** — enforced by Home Assistant.
- **Eshtaya module permission** — enforced by Eshtaya Smart Control’s backend APIs and UI.

# The `This role does not have access to that module.` bug

In 2.3.0, `template.view` existed in the backend and the new Template Manager navigation layer, but an older frontend click guard still used a view map from before Template Manager existed.

The result was contradictory behavior: the tab could be visible, then clicking it displayed:

```text
This role does not have access to that module.
```

Version 2.3.1 synchronizes Template Manager across:

- the canonical view-permission map;
- built-in roles;
- permission labels;
- first-allowed-view selection;
- navigation filtering;
- click protection.

The message should now appear only when the current **Effective Permissions** genuinely do not contain the permission required for that module.

# Backend enforcement

Hiding a button is not sufficient security. Sensitive operations are checked in the backend as well.

Template Manager, for example, uses:

```text
template.view   → snapshot / scan
template.manage → create / edit / delete / relink
```

Version 2.3.1 adds an additional backend migration lock: even a direct WebSocket or service call cannot mutate template mappings while a legacy migration is incomplete.

# Diagnosing an access problem

As a Home Assistant administrator:

1. Open Access Control.
2. Find the user.
3. Check the assigned role.
4. Check Force Allow and Force Deny.
5. Read Effective Permissions.
6. Verify the required permission:

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

If a permission is present in Effective Permissions but 2.3.1 still denies the view, capture the browser console and Home Assistant logs because that is an implementation error rather than intended policy behavior.
