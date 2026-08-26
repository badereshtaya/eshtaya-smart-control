# Smart Groups

Smart Groups provide a higher-level grouping engine inside Eshtaya Smart Control. They are intended to represent a collection of compatible Home Assistant entities as one logical control surface while preserving domain-aware behavior.

## Supported concepts

Depending on the group type, the platform can work with domains such as:

- `light`
- `switch`
- `fan`
- `cover`
- `lock`
- `media_player`
- `valve`
- `sensor`
- `binary_sensor`
- `button`
- `event`
- `notify`

There is also an **Action Group** concept for scenes, scripts, automations, buttons, and other operations that should be executed rather than represented as a continuously synchronized state.

## Creating a Smart Group

Review these items before saving a group:

1. Group/domain type.
2. Members.
3. Direction of control: group-to-members only or bidirectional where supported.
4. State policy.
5. Whether member entities should be hidden from selected UI surfaces.
6. Reliability options such as cooldown, member delay, failure policy, or quarantine when available for that group type.

Avoid mixing incompatible domains just because they expose an ON/OFF concept. Correct domain behavior is more important than forcing everything into a switch abstraction.

## State policy

State policy determines when the logical group is considered active. Typical policies include concepts such as:

- **Any** — one active member is enough.
- **All** — every required member must be active.
- **Majority** or domain-specific policies where implemented.

The selected policy affects the state seen by dashboards and automations, not only visual presentation.

## Bidirectional behavior

When bidirectional behavior is enabled, a physical member state change can update the logical group. The runtime includes echo protection so this does not become an endless loop:

```text
Group command
→ member state change
→ group state update
→ accidental second group command
```

Use Activity/Diagnostics when a group appears to oscillate or repeat commands.

## Failure handling

A multi-member command can partially succeed. Depending on configuration, the engine may:

- continue with remaining members;
- stop on an error;
- mark the group degraded;
- quarantine a repeatedly failing member when supported.

Do not hide repeated member failures with arbitrary delays. Identify the member, transport, and command path first.

## Action Groups

Action Groups are appropriate for:

- scenes;
- scripts;
- automations;
- buttons;
- stateless service-like actions.

Execution may be parallel or sequential depending on configuration. Sequential execution can include a member delay when an external system needs pacing.

## Configuration lock

For commissioned installations, configuration lock can be used where available to protect a stable group structure from accidental edits while still allowing normal operational control according to the user’s permissions.

## Health and diagnostics

Review:

- missing members;
- unavailable members;
- recent failures;
- retries and delays;
- group health state;
- Activity history.

## Permissions

Smart Groups are part of the Multi-Way module and normally use:

```text
multi.view
multi.control
multi.manage
```

- `multi.view` — inspect groups and diagnostics.
- `multi.control` — operate or synchronize groups.
- `multi.manage` — create, edit, and delete configuration.

## Commissioning advice

- Use stable names and entity IDs.
- Avoid overlapping control logic unless the interaction is intentional.
- Test physical wall changes as well as UI commands.
- Test unavailable-member behavior.
- Inspect Activity after rapid or repeated commands.
- Run the available test/diagnostic tools before project handover.
