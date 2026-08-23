# Multi-Way & Smart Groups

This module contains the complete Eshtaya Multi-Way Control engine integrated into Eshtaya Smart Control.

## Multi-Way

Use one physical output with any number of wall controllers. Controller modes include Mirror, Toggle, Momentary On, Momentary Off, Event and Follow Output. The engine preserves rapid physical edges in order, protects against delayed cloud echoes, and performs final source reconciliation.

## Smart Groups

Smart Groups can create domain-native Home Assistant groups for supported domains and include health, verification and commissioning features. Physical-controller groups and virtual groups are supported.

## Action Groups

Scene, script and automation members are represented as stateless Run actions rather than fake switches. Execution can be parallel or sequential with failure policy and per-member timing options.

## Commissioning and diagnostics

The integrated Control Center preserves Learn Mode, Area-aware setup, templates, clone, full-system tests, missing-entity repair, quality/latency telemetry, snapshots, backup/restore and Configuration Lock.

## Services and WebSocket API

Home Assistant service names remain under the unified integration domain `eshtaya_smart_control`. Multi-Way management WebSocket commands are namespaced under `eshtaya_smart_control/multiway`.
