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


## Windows firmware resource

Evidence state: **CONFIRMED** from the target system.

- System Firmware resource GUID: `7084A80E-AAFF-5B13-B343-35EB8DCBD86A`
- Provider: Xiaomi
- Installed firmware-driver package: `oem77.inf`
- Driver version: `1.9.1.9`
- UEFI firmware resource type: `1`
- Firmware resource version property: `1914261554` (hex `0x72195032`)
- Lowest supported version property: `1380122624` (hex `0x52430000`)
- Hardware ID revision string: `REV_72195032`
- VBS status: running (`VirtualizationBasedSecurityStatus = 2`)
- Configured/running security service set includes value `2`

The Windows firmware resource metadata is distinct from the SMBIOS BIOS version string `RMAMT6B0P0A0A`; the exact encoding relationship is not yet established.

## Next evidence path

Export and inspect the installed `oem77.inf` driver package. This may provide the Xiaomi capsule/update payload already staged in the Windows Driver Store without requiring SPI access.
