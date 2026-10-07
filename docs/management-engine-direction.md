# Intel Management Engine direction

## Goal

Treat Intel Management Engine as a separate platform-security and ownership workstream.

The project should determine which Management Engine functions are mandatory for TM2309 initialization and which functions can be isolated, disabled, or left unavailable to the operating system without breaking required platform behavior.

The objective is not to remove code blindly. The objective is to minimize unnecessary trust and exposure while preserving a bootable and stable machine.

## Current evidence

CONFIRMED on the target system:

- Intel Management Engine Interface is present.
- The operating system exposes an Intel Management Engine communication path.

Not yet established for TM2309:

- the complete set of Management Engine services actually used after boot;
- whether all host communication interfaces can be hidden or disabled safely;
- whether out-of-band network-management capability is present and provisioned;
- whether a supported post-initialization disabled state exists for this exact platform;
- whether a HAP/AltMeDisable-style policy is valid for this firmware generation and platform;
- which boot or power-management paths require continued Management Engine operation.

Do not promote any of these unknowns without target evidence.

## Desired policy levels

The custom firmware should eventually be capable of expressing explicit policy levels, subject to platform validation:

1. **Factory-compatible** — normal Management Engine behavior.
2. **Host-isolated** — required firmware operation remains available, but ordinary operating-system access through the host interface is not exposed.
3. **Reduced-service** — unnecessary optional services are disabled while mandatory platform functions remain.
4. **Post-initialization disabled** — Management Engine performs required early initialization and then enters a supported disabled/minimal state, if the platform proves this safe.
5. **More aggressive neutralization** — only if the exact generation and image format are understood, recovery is available, and hardware testing proves stability.

The highest available level is platform-dependent. The project must not promise complete disable where hardware or Intel firmware requires continued operation.

## Research tasks

- map all host-firmware references to Management Engine interfaces;
- determine which early boot stages depend on it;
- identify operating-system-visible communication devices and services;
- inspect firmware configuration for documented or hidden disable/reduction controls;
- determine whether network or other external paths exist independently of the host operating system;
- compare target behavior with coreboot and Intel platform implementations;
- test suspend/resume, charging, thermals, clocks and security-sensitive functions under any reduced policy;
- maintain an external recovery method before changing Management Engine regions.

## Firmware and Manager boundary

Firmware owns the Management Engine policy.

RedmiBook Manager may:

- report the active policy and capability state;
- request policy changes that firmware explicitly exposes;
- explain when a reboot or firmware-setting change is required.

RedmiBook Manager must not assume that operating-system access to Management Engine is always available. A firmware policy may intentionally hide that interface.

If privileged runtime changes are ever exposed, they require an explicit capability contract and access-control design. No proprietary or encrypted protocol should be invented until the threat model and required operations are established.
