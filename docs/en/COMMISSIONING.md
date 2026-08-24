# Commissioning and Project Handover

This guide is for preparing a real installation before handing it to an end user. A successful commissioning process verifies repeatable behavior, restart behavior, permissions, and failure recovery—not only that a device worked once.

## Before commissioning

Confirm that:

- required integrations load without critical errors;
- entities have clear names and correct Areas;
- the physical source behind each Template Manager entity is known;
- no migration is left in an unexplained state;
- Home Assistant time/date are correct;
- a current backup exists before major structural changes.

## Recommended order

### 1. Entities and Alexa

Start with Entity & Alexa Control:

- finalize important entity IDs before building many automations;
- correct display names;
- investigate unavailable entities;
- configure Alexa exposure rules;
- verify the two hidden-entity files are synchronized.

### 2. Template Manager

For permanent Light/Fan wrappers:

- select the correct physical switch;
- choose Light or Fan;
- use the final permanent entity ID;
- prefer using the permanent entity in dashboards and automations instead of the physical source.

If a legacy migration is active, do not create manual replacements with the same IDs. Wait for migration completion or the documented `restart_required` step.

### 3. Multi-Way

For every Multi-Way group:

- identify the real output;
- add controllers only after final entity IDs are known;
- choose the correct mode: Mirror, Toggle, Momentary, Event, Follow, or the mode appropriate for the physical device;
- test rapid repeated presses;
- test changes from the wall and Home Assistant;
- review Activity and health.

### 4. Smart Groups and Action Groups

Test:

- group ON/OFF or equivalent actions;
- one member changing independently;
- unavailable members;
- failure policy;
- sequential/parallel execution for Action Groups.

### 5. Tuya Cloud

If Tuya Control is enabled:

- refresh the device list;
- verify realistic online/offline state;
- test rename or cloud edits on a known device first;
- avoid a large bulk change before validating a small sample.

## Response and race-condition tests

Use scenarios such as:

```text
ON → OFF → ON quickly
repeated controller presses
change state from Tuya while HA is open
restart HA and test the first command after startup
lose internet and restore it
make a member unavailable and bring it back
```

These tests reveal cloud echo, startup timing, race conditions, and retry problems before the end user finds them.

## Restart test

Before handover:

1. Take a backup.
2. Restart Home Assistant.
3. Allow source integrations to initialize.
4. Test critical Multi-Way groups.
5. Verify permanent entities did not become `_2` or `_3`.
6. Verify Template Manager migration is completed or clearly reports a deliberate restart checkpoint.

## Test a real non-admin user

Use an account that represents the customer and verify:

- only intended modules are visible;
- required control actions work;
- administrative modules remain hidden;
- `This role does not have access to that module.` appears only for a genuinely denied module.

Do not validate permissions only with an Administrator account because HA admins receive full Eshtaya module access.

## Handover checklist

Before considering the installation complete:

- no unexplained critical recommendation;
- Alexa files synchronized;
- no unintended Missing template sources;
- stable Multi-Way and Smart Group behavior;
- permissions verified with real accounts;
- current backup available;
- clear device names and Areas;
- known project-specific exceptions documented.

## After handover

When changing a production project later:

- change one control assumption at a time where practical;
- review Activity/Diagnostics after changes;
- keep migration backups until the issue is fully resolved;
- take a full Home Assistant backup before major updates.
