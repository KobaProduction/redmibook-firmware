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


## Exported Xiaomi firmware package

Evidence state: **CONFIRMED** from the target system.

Installed Windows firmware driver package `oem77.inf` exports as `wufu.inf` and contains:

- `wucapsule.bin` — 23,337,736 bytes
- `wufu.cat`
- `wufu.inf`

The INF targets UEFI firmware resource GUID `7084A80E-AAFF-5B13-B343-35EB8DCBD86A` and declares:

- provider: Xiaomi
- driver version: `1.9.1.9`
- firmware version: `0x72195031`
- capsule filename: `wucapsule.bin`

The currently exposed Windows firmware resource reports version `0x72195032`, one numeric revision above the exported INF's `0x72195031`. The reason for this mismatch is not yet established; likely explanations include a newer installed capsule than the retained driver package or version transformation/staging behavior. Treat the relationship as **UNKNOWN** until the capsule and firmware history are inspected.

No firmware write or SPI access has been performed.


## Firmware payload container format

Evidence state: **CONFIRMED** from target-exported `wucapsule.bin`.

- File size: 23,337,736 bytes
- SHA-256: `E059052DD9F149CD246D52E400493CCD7472EE1224D8C358B40D3FD13750CCE5`
- File begins with DOS `MZ` signature.
- PE signature is present at offset `0xC8`.
- Machine field is `0x8664` (x86-64).
- Optional-header magic is `0x20B` (PE32+).

Therefore the exported `wucapsule.bin` is not a raw UEFI capsule at file offset 0. It is a PE/COFF container or executable-style firmware package that must be unpacked/inspected before assuming the embedded firmware layout.

The previous assumption that the whole file was directly the capsule payload is superseded by this evidence.
