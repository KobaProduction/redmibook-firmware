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

### Microsoft Update Catalog / A0A

Evidence state: **CONFIRMED**

- Catalog title: `XIAOMI - Firmware - 1.10.1.10`
- Update ID: `3abb160d-0127-494c-b843-7873818fc22e`
- Version date: 2024-06-04
- Firmware resource GUID: `7084A80E-AAFF-5B13-B343-35EB8DCBD86A`
- INF firmware version: `0x72195032`
- CAB SHA-256: `010CAB7B359A6CF02992751C2F765704EE39211C3241F44D6D98993B6DAB729B`
- Extracted `wucapsule.bin`: 23,333,624 bytes
- `wucapsule.bin` SHA-256: `83C51E16D5CE19EF9E9E8A10B4843A69218525DBE43FD19793F576F50C7A327D`

This matches the target system's currently exposed firmware resource revision `REV_72195032` and SMBIOS release date 2024-06-04, so the association with the installed A0A line is **CONFIRMED**.


### Microsoft Update Catalog / 0B0B

Evidence state: **CONFIRMED**

- Target: Xiaomi Redmi Book Pro 16 2024 / TM2309
- Firmware resource GUID: `7084A80E-AAFF-5B13-B343-35EB8DCBD86A`
- Catalog title: `XIAOMI - Firmware - 1.11.1.11`
- Update ID: `098b4286-6e60-41a9-9c70-1f3264fc2c76`
- CAB size: 7,615,058 bytes
- INF firmware version: `0x72195033`
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


## Container structure finding

Evidence state: **CONFIRMED** for the Microsoft 0B0B package.

The extracted `wucapsule.bin` is an x86-64 PE32+ EFI application/DLL with four sections. Its `.reloc` section has a raw size of approximately 23.3 MiB and contains the bulk of the embedded firmware data.

The raw block contains:

- multiple UEFI firmware-volume signatures `_FVH`;
- Intel `$FPT` marker;
- Insyde strings;
- additional UEFI/platform markers.

The updater executable and embedded raw firmware block are therefore tracked as separate analysis artifacts.

## Canonical Analysis project

Project: `RedmiBook_TM2309_Firmware_Analysis`
Worker: dedicated worker 0

Audio Rush remains isolated on worker 4.

Planned Analysis program names:

- `TM2309_0A0A_MS_wucapsule_EFI`
- `TM2309_0A0A_MS_firmware_raw`
- `TM2309_0B0B_MS_wucapsule_EFI`
- `TM2309_0B0B_MS_firmware_raw`

The first 23 MiB staging imports timed out before any project file appeared. This is an Analysis transport/import issue, not target evidence; no ambiguous or partial program was retained in the project.


## A0A -> B0B structural delta

Evidence state: **CONFIRMED** from the two Microsoft firmware packages.

Both `wucapsule.bin` files use the same PE32+ layout:

- PE header offset: `0xC8`
- section count: 4
- `.text`: raw offset `0x280`, raw size `0x5240`
- unnamed section: raw offset `0x54C0`, raw size `0x2C0`
- `.xdata`: raw offset `0x5780`, raw size `0xE0`
- `.reloc`/embedded firmware block: raw offset `0x5860`, raw size `0x1638720` (23,299,872 bytes)

Embedded firmware SHA-256:

- A0A: `B04F0D9954AA6D8589D814BF8C26BD69D73AFB570AA8BD9C1AAD1FF9B6906C23`
- B0B: `F05B2FB3DB50ABB3ADABEC303947DE280E689A708E37180A7E38FDA2DA425DDB`

Bytewise comparison across the equal-sized embedded firmware blocks:

- different bytes: 3,551,766
- changed share: 15.2437%
- first differing byte: `0x188`
- last differing byte: `0x1638703`

Major structural anchors remain at the same offsets in both versions:

- multiple `_FVH` firmware-volume headers
- Intel `$FPT` at `0x11EFAE0`
- Insyde strings
- UEFI markers

This supports a stable-layout version-diff strategy: compare corresponding firmware volumes/modules rather than treating B0B as a wholly different image layout.
