# Multi-Way Control

## Purpose
Multi-Way creates software-defined 2-way, 3-way and N-way behavior around a real output and one or more Home Assistant controller entities. It is intended for reliable wall-control workflows without requiring every controller location to be electrically wired as a traditional multi-way circuit.

## Group anatomy
A group contains a physical output, controller entities, virtual entity type and behavior. Each controller can define a mode, inversion and whether state should be reflected.

## Controller modes
- Mirror: controller state requests the same target state.
- Toggle: a qualifying edge toggles the output.
- Momentary On: event/edge requests ON.
- Momentary Off: event/edge requests OFF.
- Event: button/event-style input becomes a control event.
- Follow Output: controller follows the authoritative output state.

## Performance modes
Instant favors perceived wall speed, Balanced combines speed and confirmation, Safe increases verification for slower or unreliable devices. Choose according to the underlying integration rather than assuming one mode fits every device.

## Source authority
Source policy decides how the engine resolves physical input versus output state. Rapid input handling serializes edges and uses settle/reconciliation logic to reduce stale cloud echoes and out-of-order state updates.

## Confirmation and retry
Global and per-group command timeout, confirmation and bounded retry settings control verification. Excessive retry is intentionally avoided to prevent fighting a disconnected device indefinitely.

## Health states
Health can indicate healthy, disabled, missing output, output offline, out of sync or recovering. Diagnostics expose source, latency and member information so the installer can distinguish logic faults from slow/cloud device behavior.

## Creation workflow
1. Select the real output.
2. Add controllers.
3. Choose controller modes.
4. Select performance profile.
5. Review confirmation and source policy.
6. Save the group.
7. Test ON/OFF from the virtual entity.
8. Test every wall controller individually.
9. Run rapid-toggle stress testing where appropriate.
10. Confirm health returns to healthy.

## Safety
Do not assign the same physical output/controller to conflicting groups. The store validates overlap. When repairing renamed entities, use the remap/repair tools instead of recreating groups blindly.

## Backup and recovery
Use full backup before large commissioning edits. Configuration snapshots and supported Undo operations protect normal edits, while full import/restore is the appropriate disaster-recovery tool.
