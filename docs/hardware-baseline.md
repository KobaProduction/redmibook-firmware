# Hardware baseline — Redmi Book Pro 16 2024

Evidence state: **CONFIRMED** from the target system.

## Platform

- System: Xiaomi Redmi Book Pro 16 2024
- Baseboard product: `TM2309`
- Baseboard revision: `V24C1`
- CPU: Intel Core Ultra 7 155H
- Current BIOS: `RMAMT6B0P0A0A`
- BIOS release date reported by SMBIOS: 2024-06-04

## Firmware-related devices

- Intel SPI controller: PCI device `8086:7E23`
- Intel Management Engine Interface present
- Intel Management Engine WMI Provider present
- Intel SMBus controller: PCI device `8086:7E22`
- Three UEFI firmware-resource devices are exposed by Windows
- Secure Boot: enabled

## Evidence boundary

The presence of Secure Boot does **not** establish Intel Boot Guard state.

The presence of an Intel SPI controller does **not** establish whether the host can read or write all SPI regions.

No SPI dump, flash modification, or firmware update has been performed yet.

## Next decision boundary

Identify the exposed UEFI firmware resources and determine read-only BIOS/SPI protection state before selecting a dump method.
