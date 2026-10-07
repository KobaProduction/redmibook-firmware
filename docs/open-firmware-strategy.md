# Open firmware and component reuse strategy

## Purpose

The factory TM2309 firmware contains hundreds of modules. Reversing every module independently would waste effort because a large part of the image implements standard UEFI or common Intel platform behavior.

The project should classify each module before deciding whether to reverse, retain, replace, or reimplement it.

## Reference implementations and reusable foundations

### TianoCore EDK II

EDK II is the primary open-source reference for UEFI and Platform Initialization architecture. It is the first place to look for standard drivers, libraries, protocols, firmware-volume construction, boot services, runtime services and platform-independent UEFI behavior.

Official resources:

- https://github.com/tianocore/edk2
- https://github.com/tianocore/edk2-platforms
- https://www.tianocore.org/tianocore-wiki.github.io/

Potential use in this project:

- source-level reference for standard modules found in the Xiaomi/Insyde image;
- replacement source for standard UEFI components where interfaces match;
- build infrastructure for project-owned UEFI modules;
- possible UEFI payload or eventual primary firmware framework.

### coreboot

coreboot is an open-source boot firmware project whose design is to initialize the hardware with the minimum required code and then transfer control to a payload.

Official resources:

- https://github.com/coreboot/coreboot
- https://doc.coreboot.org/

Potential use:

- reference implementation for early Intel platform initialization and board-port structure;
- possible long-term base for a TM2309 port;
- reusable hardware-initialization architecture with a UEFI payload on top.

There is currently no assumption that TM2309 already has a complete upstream coreboot port. Support must be established by evidence before treating coreboot as a drop-in replacement.

### Intel Firmware Support Package

Intel FSP provides Intel-authored binary initialization components intended to be integrated into host firmware. Intel publishes a Meteor Lake package in its public FSP binary repository.

Official resources:

- https://github.com/intel/FSP
- https://www.intel.com/FSP

Potential use:

- preserve required silicon and memory initialization without independently recreating every proprietary Intel algorithm;
- compare expected initialization boundaries against the factory firmware;
- support an open host firmware while retaining unavoidable vendor initialization binaries.

FSP availability does not mean the implementation is open source. Treat it as a vendor binary dependency unless source for a specific component is proven available.

### Slim Bootloader

Slim Bootloader is an Intel-oriented modular boot-firmware project and is useful as another reference for integrating Intel silicon initialization with a smaller host firmware.

Official resources:

- https://slimbootloader.github.io/
- https://github.com/slimbootloader/slimbootloader

Use primarily as an architectural and platform reference unless TM2309 compatibility is demonstrated.

### LinuxBoot

LinuxBoot uses a Linux kernel and initramfs as a later boot environment. It is useful as a reference for replacing large late firmware stacks with well-tested Linux drivers.

Official resources:

- https://www.linuxboot.org/
- https://github.com/linuxboot/linuxboot

It is not currently the primary TM2309 target, but may be useful for future payload experiments.

### oreboot

oreboot explores minimal open firmware written largely in Rust.

Official resource:

- https://github.com/oreboot/oreboot

Use as a design reference unless direct Meteor Lake/TM2309 support becomes relevant.

## Module classification workflow

For every significant factory module:

1. preserve its exact raw identity: file GUID, module name, version and location;
2. recover enough behavior to classify its role;
3. search EDK II, coreboot, Intel platform sources and other authoritative implementations for the same standard role;
4. compare interfaces and behavior rather than relying on similar names alone;
5. classify it as one of:
   - standard/open-source equivalent available;
   - Intel/vendor initialization dependency;
   - Insyde framework component;
   - Xiaomi/Huaqin board-specific component;
   - unknown;
6. choose a disposition:
   - reuse open source;
   - retain original binary;
   - replace with project implementation;
   - continue behavior recovery.

The goal is to minimize manual reverse engineering of code whose behavior is already represented by trustworthy source.

## Expected build strategy

The first practical custom firmware is likely to be hybrid rather than fully source-built.

A likely composition is:

- open UEFI/core firmware infrastructure;
- Intel initialization binaries required by the platform;
- selected retained factory modules;
- project-owned TM2309 board modules;
- recovered ACPI and embedded-controller contracts;
- project-owned Setup and operating-system control interfaces.

As knowledge increases, retained binaries can be replaced incrementally.

## Contribution strategy

If a suitable upstream project becomes the primary base and TM2309 support can be implemented cleanly, generic platform support should be contributed upstream where appropriate.

Board-specific policy, experimental controls and owner-specific tuning can remain in this project while generic Meteor Lake or reusable RedmiBook support is proposed upstream.

## Evidence boundary

Source similarity does not prove binary identity or target behavior. An open module can replace a factory module only after its consumed/provided interfaces, configuration data, ordering constraints and hardware effects are shown to be compatible.
