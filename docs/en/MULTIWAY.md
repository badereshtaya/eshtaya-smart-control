# Multi-Way Control

Multi-Way provides software-defined 2-way, 3-way and N-way control around one authoritative physical output. Version 2.4.0 adds a lifecycle-aware startup barrier so slow cloud integrations do not create false missing-entity faults during Home Assistant restart.

## Core model

Each group contains:

- one **output** entity: the real physical load;
- one or more **controllers**;
- optional fallback output;
- controller modes and reliability behavior;
- generated control/health entities.

The output remains the physical authority. Controllers request state changes through the protected transaction engine.

## Controller modes

Supported behavior includes:

- Mirror
- Toggle
- Momentary On
- Momentary Off
- Event
- Follow Output

Use the mode that matches the physical device. Avoid adding random delays to hide duplicate input; use the activity/echo diagnostics first.

# Startup protection in 2.4.0

Older builds used a fixed `startup_delay` measured from the moment Eshtaya loaded. That was not enough when official Tuya or another cloud integration restored its entities later.

2.4.0 uses five protection layers.

## 1. Tuya after-dependency

The integration manifest declares official `tuya` as an `after_dependency`. When Tuya is configured, Home Assistant schedules Eshtaya after Tuya integration setup.

## 2. Home Assistant startup-complete barrier

The Multi-Way engine prepares its runtime but remains:

```text
ready = false
starting = true
```

until Home Assistant reaches its startup-complete event, unless that protection is explicitly disabled in Configure.

During this protected phase:

- missing-output/controller Repair issues are suppressed;
- a temporarily absent output is `recovering`, not `missing_output`;
- Dashboard does not count startup recovery as a degraded Multi-Way fault;
- initial physical reconciliation is deferred.

## 3. Referenced integration readiness

For each output, controller and fallback, Eshtaya inspects its Entity Registry owner. If the state is absent but its Config Entry is still setting up, retrying or unloading, the entity is treated as **still loading**.

This is more reliable than checking only whether an Entity Registry row exists.

## 4. Settle window

After referenced providers stop loading, Eshtaya waits an additional quiet window before becoming ready.

Default:

```text
15 seconds
```

## 5. Repair grace and confirmation

A state that is genuinely absent after startup still does not immediately generate a Repair.

Defaults:

```text
repair grace: 90 seconds
missing confirmations: 3
```

The entity must remain absent through the grace period and then be observed missing repeatedly before the Repair Registry issue is created.

If the entity appears at any point, its missing timer and confirmation count are reset.

# Configure the startup barrier

Open:

```text
Settings → Devices & services → Eshtaya Smart Control → Configure
```

Available controls:

- Wait for Home Assistant startup
- Wait for referenced integrations
- Startup settle seconds
- Startup maximum wait
- Missing-entity Repair grace
- Missing confirmations

Recommended production defaults are already selected.

The maximum wait is bounded so a broken provider cannot block Multi-Way forever. Reaching the maximum wait permits startup to continue, but normal post-start Repair grace still applies before a missing reference becomes an error.

# What happens to an old false Repair after restart?

At the beginning of a protected startup, persisted Eshtaya `missing_output_*` and `missing_controller_*` issues are removed. They are not recreated unless the reference remains truly absent after the full barrier, grace and confirmation process.

This specifically prevents a normal Tuya restore from generating errors such as:

```text
Multi-way output entity is missing
```

for an entity that appears moments later.

# Health states

Important states include:

- `healthy`
- `recovering`
- `degraded`
- `output_offline`
- `missing_output`
- `out_of_sync`
- `disabled`

`recovering` during the startup barrier is expected and is not counted as a degraded Dashboard warning.

# Reliability tools

Multi-Way also provides:

- cloud-command echo guards;
- rapid physical-input handling;
- output confirmation;
- bounded retries;
- source stability/settle logic;
- activity history;
- latency/health diagnostics;
- non-destructive group tests;
- missing-reference remap tools;
- full backup/restore.

# Native Home Assistant Groups

Native/UI-created Home Assistant Group discovery and transactional Take Over are **not legacy Eshtaya migration**. They remain available even when legacy migration is disabled in the integration options.

# Troubleshooting

If a real missing-output Repair appears in 2.4.0:

1. confirm the startup barrier is already `ready`;
2. check the System Report startup section;
3. verify the output state is still absent after the configured grace;
4. inspect the Entity Registry owner and provider Config Entry;
5. restore the entity or remap the group output.

Do not treat a `starting` or `recovering` status during restart as a fault.
