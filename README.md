# RedmiBook Firmware

Open-source firmware research and development for RedmiBook laptops.

## Initial target

- Xiaomi Redmi Book Pro 16 2024
- Intel Core Ultra 7 155H / Meteor Lake
- Board TM2309

## Project direction

The long-term goal is a buildable, auditable firmware stack for the target platform that preserves the capabilities required for normal operation while making platform policy and hardware controls open to modification.

This is not limited to reproducing the factory firmware byte-for-byte. The project may reuse open-source firmware components, vendor initialization binaries that cannot yet be replaced, preserved factory modules, and newly implemented board-specific modules.

Primary documents:

- [Project goals and acceptance](docs/project-goals.md)
- [Open firmware and component reuse strategy](docs/open-firmware-strategy.md)
- [Intel Management Engine direction](docs/management-engine-direction.md)
- [Recovered firmware behavior](docs/behavior-recovery.md)
- [ACPI/WMI control contracts](docs/acpi-wmi-control-contracts.md)
- [Firmware corpus](docs/firmware-corpus.md)

## Current scope

The current phase is behavior recovery and platform decomposition. Work focuses on firmware volumes and modules, platform initialization, ACPI, embedded-controller contracts, Setup configuration, boot protections, recovery paths, and identifying which proprietary components can be retained, replaced, or reimplemented.

No replacement-firmware implementation is considered validated merely because a module can be rebuilt. Boot, hardware, recovery, and integration acceptance remain separate gates.

## Status

Research and architecture definition. There is currently no validated replacement firmware or flashable release.
