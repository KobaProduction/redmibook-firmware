# Project goals and acceptance

## Mission

The project exists to make the Redmi Book Pro 16 2024 platform firmware as open, understandable, rebuildable, and modifiable as practical.

The target is not only an open copy of the factory firmware. The final firmware should preserve the platform behavior required for reliable boot and normal hardware operation, then expose additional controls that are useful to the owner and are currently hidden, restricted, or available only through proprietary software.

The first target is Xiaomi Redmi Book Pro 16 2024 / TM2309. Porting to other RedmiBook models is secondary until this platform is understood and accepted on hardware.

## Functional goals

The firmware should ultimately provide or preserve:

- reliable processor, memory, chipset and device initialization;
- storage, USB, PCIe, Thunderbolt/USB4 and other required boot-device support;
- operating-system handoff through standard UEFI interfaces;
- ACPI and SMBIOS data required by Windows and Linux;
- embedded-controller integration and platform event handling;
- Secure Boot and recovery mechanisms where they remain useful and compatible with the chosen trust model;
- cooling-system controls, fan profiles and temperature reporting;
- performance and power-policy controls;
- battery and charging controls;
- keyboard, backlight, hotkey and other platform-specific controls already present in the factory firmware;
- optional low-level telemetry that can be safely exposed to the operating system.

Additional owner-oriented goals include:

- configurable cooling behavior rather than only factory presets;
- configurable Intel Management Engine policy, including stronger isolation or post-initialization disable where the target platform safely supports it;
- undervolting and power-efficiency tuning where the silicon and platform allow it;
- processor and memory tuning where it can be implemented with recoverable limits;
- firmware-interface localization, including Russian and other languages;
- explicit control of optional platform devices and controllers where disabling or reconfiguring them is safe;
- stable interfaces for RedmiBook Manager to query capabilities and apply settings from the operating system.

## Architecture goal

The expected end state may be hybrid.

A valid result can combine:

1. open-source firmware infrastructure;
2. vendor initialization components that are still mandatory;
3. preserved proprietary modules whose behavior is understood but whose replacement gives no useful benefit;
4. newly implemented TM2309-specific modules;
5. recovered ACPI, embedded-controller and Setup behavior;
6. project-owned interfaces for operating-system management.

A component does not need to be rewritten merely because it is proprietary. Replacement priority is driven by trust, modifiability, missing functionality, maintainability and ownership value.

## Development stages

The project should advance through distinct evidence levels:

1. **Structure recovery** — identify firmware regions, volumes, modules, tables and their relationships.
2. **Behavior recovery** — recover required platform and control contracts.
3. **Component classification** — match standard modules to open-source equivalents and identify unavoidable vendor binaries.
4. **Buildable hybrid image** — produce a reproducible firmware image from an explicit component manifest.
5. **Boot validation** — demonstrate controlled boot with a recovery path.
6. **Hardware acceptance** — validate memory, storage, display, USB, power, cooling, sleep/resume and other required platform behavior.
7. **Operating-system integration** — validate Windows/Linux handoff and RedmiBook Manager contracts.
8. **Open replacement expansion** — replace additional proprietary components only when their contracts are understood and hardware validation exists.

Build success is not hardware acceptance. A booting image is not by itself a production-ready firmware.

## Current priority

The current priority remains behavior recovery and classification, not writing replacement modules prematurely.

The most valuable recovered areas currently include embedded-controller state, performance/fan profiles, battery/charging behavior, keyboard/backlight behavior, ACPI/WMI control surfaces and native firmware consumers of those states.


## Current execution priority

The near-term project priority is intentionally narrower than full firmware replacement.

1. Close the user-relevant hardware-control contracts exposed by the factory firmware.
2. Materialize those contracts as stable semantic capabilities for RedmiBook Manager.
3. Use Manager on real hardware to obtain execution proof for recovered controls and telemetry.
4. Continue deeper firmware replacement only after the useful platform-control surface is understood and exercised.

Firmware research should currently prioritize controls that unlock concrete Manager capabilities over exhaustive recovery of unrelated standard UEFI modules.

Full open-firmware replacement remains the long-term goal, but it is not the immediate blocker for delivering useful hardware control.
