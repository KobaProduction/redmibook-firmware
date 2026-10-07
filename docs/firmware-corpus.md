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


## Firmware-volume map

Evidence state: **CONFIRMED** from UEFI firmware-volume headers in both A0A and B0B embedded images.

Both versions expose the same 15 validated firmware-volume headers at the same offsets and with the same declared lengths. Representative volumes include:

- `0x00211AF0` length `0xAA000`
- `0x002BEAF0` length `0x2B0000`
- `0x0056EAF0` length `0x70000`
- `0x005E2AF0` length `0x3FE000`
- `0x00A01AF0` length `0xC0000`
- `0x00B41AF0` length `0x1D5000`
- `0x00D16AF0` length `0x170000`
- `0x00E86AF0` length `0xB0000`
- `0x00F36AF0` length `0xC0000`
- `0x01097AF0` length `0x14A000`

There are also nested/overlapping firmware-volume headers, including volumes at `0x0029BAF8`, `0x00D6FEF0`, and `0x00E86B60`. These must be treated as nested container evidence, not as fifteen independent top-level regions.

Because A0A and B0B preserve the same FV map, the next analysis pass can compare corresponding volumes and FFS modules directly.


## A0A -> B0B changed-volume localization

Evidence state: **CONFIRMED**.

The version delta is highly localized:

- FV at `0x005E2AF0`, length `0x3FE000`: 3,510,383 changed bytes, **83.858%** of that volume.
- Nested/overlapping FV at `0x0029BAF8`, length `0xAA000`: 5 changed bytes.
- All other validated FV ranges in the current map compare byte-identical between A0A and B0B.

This means the B0B update is not a broad platform-image rewrite. The primary next behavior-analysis target is the `0x005E2AF0..0x009E0AF0` firmware volume and its contained FFS modules. Other identical volumes can be deprioritized until a cross-component dependency requires them.


## Decompressed A0A -> B0B module delta

Evidence state: **CONFIRMED**.

The primary changed outer FV contains one large `EFI_FV_FILETYPE_FIRMWARE_VOLUME_IMAGE` FFS file:

- GUID: `20BC8AC9-94D1-4208-AB28-5D673FD73486`
- wrapped by GUID-defined section `EE4E5898-3914-4259-9D6E-DC7BD79403CF`
- section payload is LZMA-compressed
- decompressed size is `0x14F8080` in both A0A and B0B
- decompressed image contains one top-level FV at offset `0x80`, length `0x14F8000`

That FV contains 356 parsed FFS files. Cross-version matching by FFS GUID localized the meaningful changed set to three files:

1. `80CF7257-87AB-47F9-A3FE-D50B76D89541` — UI name `PcdSmmDxe`, file type `0x0C` (combined SMM/DXE).
2. `F9D88642-0737-49BC-81B5-6889CD57D9EA` — UI name `SmbiosDxe`, file type `0x07` (DXE driver).
3. `FE3542FE-C1D3-4EF8-657C-8048606FF670` — UI name `SetupUtility`, file type `0x07` (DXE driver).

PE32 section comparison:

- `PcdSmmDxe`: 40,960 bytes, A0A and B0B PE32 payloads are byte-identical.
- `SmbiosDxe`: 89,248 bytes, only 2 PE32 bytes differ.
- `SetupUtility`: 3,526,432 bytes, only 2 PE32 bytes differ.

Therefore the apparently large compressed-image delta is mostly compression avalanche and/or non-PE data changes. The executable code delta between these releases is extremely small. Future version analysis should compare decompressed FFS sections rather than raw compressed bytes.

Stable Analysis module names are stored in Files under `artifacts/redmibook-tm2309/modules/`, preserving version, source, UI name and FFS GUID.


## Correction: compressed-volume delta was not a behavior delta

Evidence state: **CONFIRMED**.

The earlier bytewise comparison of the compressed outer firmware volume showed 83.858% changed bytes. That result must **not** be interpreted as an 83.858% firmware behavior change.

The dominant FFS object in that volume is a firmware-volume image containing a GUID-defined section with GUID `EE4E5898-3914-4259-9D6E-DC7BD79403CF`, which identifies an LZMA-compressed UEFI section.

After LZMA decompression:

- both releases produce an inner firmware image of exactly 21,987,456 bytes;
- only **7 bytes** differ across the complete decompressed images.

The seven differences localize to:

1. `PcdSmmDxe` raw-data section — 3 bytes, changing the embedded release date text from `06/04/2024` to `06/10/2025`. Its PE32 executable section is byte-identical.
2. `SetupUtility` PE32 image — 2 bytes inside the embedded BIOS-ID string, changing `RMAMT6B0P0A0A` to `RMAMT6B0P0B0B`.
3. `SmbiosDxe` PE32 image — 2 immediate values changing `0x0A` to `0x0B`. Both are **CONFIRMED** writes to the SMBIOS Type 0 System BIOS Minor Release field (`+0x15` within the 16-bit major/minor pair at `+0x14`), changing the published BIOS release from 1.10 to 1.11 in two construction paths.

Therefore the previous interpretation that the 2025 package broadly changes the large firmware volume is **WITHDRAWN**. The large compressed-byte delta is explained by LZMA recompression sensitivity. Current evidence does not yet prove a functional behavior change between these two releases.


## Release 2024-04-07 -> installed release 2024-06-04

Evidence state: **CONFIRMED structural/module delta**. Per-action behavior claims remain separately classified.

The earlier Microsoft package reports driver version `1.9.1.9` and firmware-resource revision `0x72195031`. Its decompressed firmware-volume payload is materially different from the installed 2024-06-04 release.

Module-level FFS/PE matching by FFS GUID gives:

- 314 valid PE modules in the 2024-04-07 payload;
- 319 valid PE modules in the installed 2024-06-04 payload;
- 143 byte-identical PE modules;
- 171 same-GUID PE modules with changed files;
- 5 added PE modules;
- 0 removed PE modules.

Added modules are:

- `CheckBootGuardKeyDxe` — GUID `25264B72-7A80-4856-A7EC-15802270EE1B`;
- `StatusCodeLoggerDxe` — GUID `9498F6C5-1B77-4AE7-A045-DBC29EB5541D`;
- `DnsDxe` — GUID `B219E140-DFFC-11E3-B956-0022681E6906`;
- `StatusCodeLoggerSmm` — GUID `EF0D2ECB-AE7B-4ED2-8848-F39290D19322`;
- one currently unnamed PE-bearing FFS file — GUID `FEA01457-E381-4135-9475-C6AFD0076C61`.

### Control-path triage

Raw file-size/hash differences were rechecked against each PE section's meaningful `VirtualSize`, so file-alignment padding is not treated as behavior evidence.

- `OemWMISmmCallback` — GUID `FAD93433-76B9-4482-4567-3BEACEA9B35D`: all meaningful section bytes are identical. **CONFIRMED: no code/data behavior delta**; the file difference is alignment/padding only.
- `ThermalSmm` — GUID `8C916319-1334-419A-9F2C-976CABFDBBCA`: all meaningful section bytes are identical. **CONFIRMED: no code/data behavior delta**; the file difference is alignment/padding only.
- `DxeCpuPowerManagement` — GUID `FDBC2130-2A17-4830-8477-544F3669772F`: real code/data changes exist and were analyzed instruction-by-instruction.

### DxeCpuPowerManagement semantic delta

Normalized instruction comparison removes relative-address/layout shifts while retaining opcode/operand behavior:

- old release: 2102 decoded instructions;
- installed release: 2103 decoded instructions;
- normalized similarity: 99.88%;
- three diff blocks total:
  1. one added CPUID/platform-signature check;
  2. one padding `INT3` difference;
  3. one classifier-table bound change.

The module contains a 12-byte-entry classifier keyed by:

- masked CPUID family/model signature;
- 16-bit processor Host Device ID;
- a small result/class code.

The installed release adds CPUID signature `0x000B0650` to an existing special-case route and adds two classifier rows for that signature. Intel public documentation identifies `B0650` as Arrow Lake U / Core Ultra Series 2. The existing `0x000A06A0` family is the stepping-masked Meteor Lake family. Host Device IDs in the table (`0x7Dxx`) match Intel's documented processor Host Device IDs.

The classifier table changes from 34 to 23 entries:

- all 11 `A06A0` rows are retained unchanged;
- all four `A06C0` rows are removed;
- two `C0650` rows are removed while six remain;
- four `C0660` rows returning class 3 remain, while seven class-1 rows are removed;
- two new `B0650` rows are added (`0x7D30`, `0x7D37`), both returning class 0.

The caller uses class `4` as the unmatched/fallback result. In the recovered route it only distinguishes `class <= 3` from fallback `4`; semantic meanings of classes `0/1/3` remain **UNKNOWN**.

### Target-specific implication for Core Ultra 7 155H

Intel documents Core Ultra 7 155H as Meteor Lake H with 6 performance cores, 8 efficient cores and 2 low-power efficient cores. Intel's Meteor Lake processor datasheet maps H 6P+8E to Host Device ID `0x7D01`.

The firmware classifier row:

`masked CPUID A06A0 + Host Device ID 7D01 -> class 0`

is byte-identical in the 2024-04-07 and installed 2024-06-04 releases. The added `B0650` special-case test also does not alter the already-existing `A06A0` branch.

Therefore the version delta provides **implementation proof that the known 155H/Meteor-Lake classifier path itself is unchanged**. Actual runtime CPUID/Host-DID observation on this individual laptop has not yet been collected, so hardware/runtime identity remains a separate evidence level.

### CPU Power NVS behavior contract

The same module scans AML for an `OperationRegion` named `PNVS`, patches its SystemMemory base address and writes region length `0x126`. It zero-initializes a `0x126`-byte backing block and fills it from CPU feature state and MSRs including `0x194` and `0x1A2`.

This establishes the recovered object as a **CPU Power NVS** region at implementation-proof level. Individual field names remain provisional until their exact AML/MSR consumer semantics are closed.

The module also references dynamically loaded power-management SSDTs named `Cpu0Cst`, `Cpu0Hwp`, `Cpu0Ist`, `Cpu0Psd`, `Cpu0Tst` and `CpuSsdt`, consistent with the recovered CPU power-management route.

## Canonical ThermalSmm import checkpoint (2026-10-08)

**Analysis-state evidence, not additional firmware execution proof.** The canonical persistent project is `RedmiBook_TM2309_Firmware_Analysis`, project ID `ghp_2bf17493ef188f564a68d8ae`. Following a stalled Analysis worker, the project was successfully reattached and its existing saved program list was retrieved. The 2024-06-04 `ThermalSmm` binary was then staged using the dedicated `import_workspace_file` route from verified workspace artifact `artifacts/redmibook-tm2309/control-candidates/TM2309_2024-06-04_ThermalSmm_8C916319-1334-419A-9F2C-976CABFDBBCA_PE32.efi`; the tool reported successful import into canonical folder `/control_modules/installed_2024-06-04/`, with SHA-256 `b60df77765204a751ba2bc83e31b8f260548a1928d4d5b865add3cb5bb83e587` and auto-analysis deliberately disabled.

Immediately after import, program metadata returned **`action_count=0`**. A later `refresh_program_behavior(dry_run=true)` operation unexpectedly initiated backend `run_analysis` and timed out, despite the request being a dry run; after emergency worker recovery, the project session detached. Subsequent read-only attempts to reattach were blocked because no Analysis worker was both enabled and idle (four slots disabled, the remaining slot owned by a separate project). The imported **program's post-recovery persistent state has not been verified**. Do not claim decompiled/named actions or saved semantic annotations for this `ThermalSmm` program based on this attempted import. Do not retry a broad/automatic analysis while the service is unhealthy; restore worker availability through the supported infrastructure path first.

The independently retained EFI image and the instruction-level evidence in `docs/cpu-power-tuning.md` remain the verified source for the firmware contract. This checkpoint tracks the Analysis infrastructure limitation separately from the target's behavior.
