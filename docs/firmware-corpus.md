# Firmware analysis corpus

This document tracks external firmware artifacts before they enter the canonical behavior-analysis project.

## Naming contract

Source artifacts:

`TM2309_<version>_<source>_<container>.<ext>`

Analysis programs/components:

`TM2309_<version>_<source>_<component>`

Examples:

- `TM2309_0B0B_MS_CAB.cab`
- `TM2309_0B0B_MS_wucapsule`
- `TM2309_0A0A_4PDA_TM2309_fd`
- `TM2309_0909_4PDA_TM2309_fd`

Do not import archive/container files into Analysis as if they were firmware programs. Extract and classify the contained component first.

## Acquired artifacts

### Microsoft Update Catalog / 0B0B

Evidence state: **CONFIRMED**

- Target: Xiaomi Redmi Book Pro 16 2024 / TM2309
- Firmware resource GUID: `7084A80E-AAFF-5B13-B343-35EB8DCBD86A`
- Catalog title: `XIAOMI - Firmware - 1.11.1.11`
- Update ID: `098b4286-6e60-41a9-9c70-1f3264fc2c76`
- CAB size: 7,615,058 bytes
- CAB SHA-256: `DB58503ED90EA104F96AB814BD5EED1E0FCB55FB96B78C2ABFDC2F4B30AD6F30`
- Local corpus name: `TM2309_MS_1.11.1.11_0B0B.cab`

The CAB uses LZX compression. The current lightweight extractor in the terminal workspace cannot unpack LZX, so component extraction remains pending.

## Identified but not yet acquired

### 4PDA TM2309 release archives

Evidence state: **CONFIRMED as published attachments; acquisition pending**

- `RMAMT6B0P0505.7z`
- `RMAMT6B0P0909.7z`
- `RMAMT6B0P0A0A.7z`

The forum exposes direct attachment URLs, but non-browser downloads currently receive HTTP 403 and the browser-download bridge times out on these files.

### NB6835A service dump

Evidence state: **REFERENCE ONLY**

Chinafix publishes an original-machine backup for `REDMI W4220 NB6835A_PCB_MB_V2_P2` containing two BIOS programs. The thread later identifies W4220 as a 14-inch machine. Do not import or label this dump as TM2309 firmware unless compatibility is independently established.

## Analysis project

Reserved canonical project name:

`RedmiBook_TM2309_Firmware_Analysis`

Project creation is currently blocked by Analysis worker capacity. The only enabled worker is attached to an unrelated existing project; it will not be released or reused for this work.
