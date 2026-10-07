# CPU power and voltage tuning

Target: Xiaomi Redmi Book Pro 16 2024 / TM2309.

This document separates settings that are proven to exist in the target firmware from controls that are only suggested by dormant Intel resources.

## CPU configuration storage

**CONFIRMED**

The target Setup forms define a CPU configuration variable:

- semantic role: CPU setup/configuration
- raw variable name: CpuSetup
- VarStore ID: 0x3
- GUID: B08F97FF-E6E8-4193-A997-5E9E9B0ADB32
- size: 0x5E0 bytes

The settings below are real questions bound to this target variable.

## Package power limits

### Platform PL1

**CONFIRMED — target Setup contract**

- enable field: CpuSetup +0x2E
- power field: CpuSetup +0x2F, 32-bit
- time-window field: CpuSetup +0x33
- power range: 0 .. 0x3E7F83
- power step: 125 mW

The target help text states that the value is expressed in milliwatts/percent according to the platform mode, is rounded by firmware to the nearest 1/8 W, and becomes the Package RAPL PL1 value.

### Platform PL2

**CONFIRMED — target Setup contract**

- enable field: CpuSetup +0x34
- power field: CpuSetup +0x35, 32-bit
- power range: 0 .. 0x3E7F83
- power step: 125 mW

### Processor PL1 override

**CONFIRMED — target Setup contract**

- override enable: CpuSetup +0x16
- PL1 value: CpuSetup +0x12, 32-bit
- PL1 time window: CpuSetup +0x17
- power step: 125 mW

Target help semantics:

- value is in milliwatts;
- firmware rounds to the nearest 1/8 W;
- zero means no custom override and firmware programs Processor Base Power / TDP;
- on non-overclocking SKUs the accepted range is constrained between the minimum power limit and Processor Base Power.

### Processor PL2 override

**CONFIRMED — target Setup contract**

- override enable: CpuSetup +0x18
- PL2 value: CpuSetup +0x19, 32-bit
- power step: 125 mW

Target help semantics:

- value is in milliwatts;
- firmware rounds to the nearest 1/8 W;
- zero makes firmware program 1.25 × Processor Base Power / TDP;
- the processor package power policy uses this as the upper PL2 limit.

## Thermal throttling offset

### TCC activation offset

**CONFIRMED — target Setup contract**

- field: CpuSetup +0x6D
- range: 0 .. 63
- unit: degrees Celsius of offset from the factory TCC activation temperature

The target firmware explicitly defines the effective activation point as:

factory TCC activation temperature - configured offset.

This is a thermal-policy setting, not a direct temperature target.

## Visibility / capability gates

### Intel SpeedStep

Some power-limit questions are suppressed when the target Intel SpeedStep question is disabled.

### Computed CPU feature flag

The processor PL1/PL2 override questions are additionally gated by a volatile feature byte:

- variable role: SetupCpuFeatures
- VarStore ID: 0x100C
- GUID: EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9
- size: 0x2A bytes
- gate field: +0x1A
- target form question ID: 0x1C48

**UNKNOWN semantic meaning**

The value is used as a computed capability gate, not as a normal user setting. Its producer and exact meaning have not yet been recovered. Do not label it as an overclocking-lock or SKU flag without direct evidence.

The variable name is independently consumed by MeSmbiosUpdateConfig, but that module only reads feature bytes; it does not prove ownership or production of +0x1A.

## Overclocking lock

**CONFIRMED existence; runtime effect not yet closed**

- field: CpuSetup +0xF9
- values: 0 / 1
- target label: Overclocking Lock

The existence and storage contract are proven. The exact hardware lock action and whether it blocks all voltage/power mechanisms on TM2309 remain to be traced before Manager uses it.

## Voltage / undervolt resources

**LIKELY capability family; exact target control contract UNKNOWN**

The factory SetupUtility contains target-resident English resources for:

- P-core Voltage Offset
- E-core Cluster 0..7 Voltage Offset
- GT Voltage Offset
- NGU Voltage Offset
- MemSS Voltage Offset
- P-core Adaptive Voltage
- P-core Voltage Override
- additional Intel overclocking / mailbox descriptions

Recovered HII string tokens include:

- E-core Cluster 0 Voltage Offset: 0x904
- P-core Voltage Override: 0x938
- P-core Voltage Offset: 0x93A
- P-core Adaptive Voltage: 0x9BB
- MemSS Voltage Offset: 0xA28
- NGU Voltage Offset: 0xA34

However:

- the static target form does not contain questions bound to these labels;
- SetupUtility code does not directly construct them from those token IDs;
- public CpuSetup layouts from other Intel firmware do not match TM2309 offsets;
- the sign/value encoding and target apply route are not yet proven.

Therefore these resources are evidence that the firmware family contains voltage-tuning support, but not proof that TM2309 currently exposes a usable undervolt control.

Manager must not expose a voltage-offset write until the target field layout, sign encoding, accepted range, lock behavior and hardware apply path are closed.

## Manager capability status

Current semantic status:

- PackagePowerLimit1: PARTIAL — configuration contract confirmed; safe operating-system write/apply path not yet proven.
- PackagePowerLimit2: PARTIAL — configuration contract confirmed; safe operating-system write/apply path not yet proven.
- TccActivationOffset: PARTIAL — configuration contract confirmed; runtime application path not yet proven.
- OverclockingLock: PARTIAL — storage exists; hardware effect needs recovery.
- VoltageOffset / Undervolt: UNKNOWN for implementation; supporting resources exist but no target write contract is closed.

## Next evidence boundaries

1. recover the producer/meaning of SetupCpuFeatures +0x1A;
2. trace CpuSetup PL1/PL2 values into the native Intel policy / hardware programming path;
3. determine whether the values can be changed safely at runtime or require reboot;
4. identify the dynamic voltage-control producer and target-specific offset/sign encoding;
5. determine whether silicon/firmware locks make voltage offsets unavailable on this exact machine.

## Native CpuSetup variable consumers (2026-10-07 checkpoint)

**CONFIRMED — installed firmware static machine-code evidence, not power-limit hardware application.**

The extracted June `PolicyInitAdvancedDxe.efi` contains the genuine `CpuSetup` variable GUID `B08F97FF-E6E8-4193-A997-5E9E9B0ADB32` at file/RVA `0x3D20` and the `CpuSetup` UTF-16 name at `0x49C0`. Its instruction path `0xD24..0xD4E` prepares an explicitly sized `0x5E0` buffer and calls the UEFI runtime-services `GetVariable` slot `+0x48`. This confirms a native consumer of the CPU configuration, beyond HII/IFR question existence.

An independent native `CpuSetup` read is present in `AdvancedAcpiDxe.efi` (GUID at `0xDB70`, name at `0xDF70`, call at `0x2262`, same size `0x5E0`). Additional extracted GUID/name carriers include `PlatformInitDxe` and `PlatformInitAdvancedSmm`, but their specific downstream field consumers have **not** been established by this bounded scan. Module inventory does not by itself prove use of PL1/PL2 bytes.

The next evidence boundary is **data flow from `CpuSetup+0x2F/+0x35` and processor overrides through a native policy/CPU power-management consumer to the actual power-control programming**. This trace is not closed by the variable reads alone. `SetupCpuFeatures+0x1A` remains semantically UNKNOWN.

**Investigation checkpoint (selected PL1/PL2 control route only): 25% → 50%, 1/4 → 2/4 gates.** Covered: target HII/VarStore fields and at least one verified native GetVariable consumer. Open: concrete hardware policy/programming link and safe live/OS apply. This is neither board execution proof nor an estimate of overall CPU tuning support.

## CpuSetup consumer discriminants and CPU-PM MSRs (2026-10-07)

**CONFIRMED — bounded static machine-instruction evidence; PL1/PL2 hardware programming still UNKNOWN.**

Following the `PolicyInitAdvancedDxe.efi` `CpuSetup` `GetVariable` call at `0xD4E` into its immediate consumer reveals the accessed field: the destination buffer begins at `rbp-0x80`, and the conditional read `movzx ecx, byte ptr [rbp+0x210]` at `0xD5F` corresponds to `CpuSetup+0x290`, **not** either of the PL1/PL2 HII fields. After status evaluation, this byte is selected against a fallback into local global state at `0x50E9`. Its product meaning is still UNKNOWN. The mere fact of a native full-variable read must not be counted as proof of native PL1/PL2 consumption.

The installed `DxeCpuPowerManagement` extracted PE image contains `RDMSR` instructions, including direct read selections `MSR 0x194`, `0x1A2` and `0xCE`; no direct `WRMSR` opcode was found in its disassembled executable section. This module therefore supplies **no established direct MSR write evidence** for Package Power Limit programming in the inspected image. Indirect calls, another native module, a firmware policy handoff or SMM code may still implement writes; absence of `WRMSR` here is not a platform-wide negative proof.

Static comparison of the native `CpuSetup` consumers also shows `PlatformInitDxe`, `PlatformInitAdvancedDxe` and `PlatformInitAdvancedSmm` references, but their specific PL1/PL2 field dataflow is unverified. Continue from a concrete policy-structure field, parameter passing or CPU policy-programming entrypoint rather than assuming semantics from file/module names.

**Progress denominator unchanged:** the selected PL1/PL2 route remains **2/4 (50%)**. The remaining two gates are actual parameter-to-policy/hardware programming evidence and a safe live/OS control path. These findings refine candidate selection; they do not close either gate.

## SetupCpuFeatures GUID and MTRR false-positive audit

**CONFIRMED bounded static behavior; `SetupCpuFeatures+0x1A` producer and native PL1/PL2 application still UNKNOWN.**

The canonical `SetupCpuFeatures` vendor GUID `EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9` has little-endian bytes `43 D6 87 EC A4 EB B5 4B A1 E5 3F 3E 36 B2 0D A9`. A previous local search used the incorrect sequence `...EC E4 EB...` and falsely returned no firmware GUID matches. A corrected read-only scan identified **16 file copies containing the proper GUID** across extracted PE images; these are **GUID byte occurrences, not proof of 16 consumers of the named UEFI variable**.

The native `PlatformInitAdvancedDxe` instance of this GUID at `0x8FE0` is used with UTF-16 variable name `Setup` at `0x9460` and a `0xC2C` byte read at `0x14B1`. It also has a `SetVariable` call at `0x151B` using the same variable-name/GUID pair. **These are `Setup` variable accesses, not the 0x2A-byte `SetupCpuFeatures` varstore**. They must not be merged solely because their vendor GUID bytes match.

A true read of the named `SetupCpuFeatures` variable is present in `MeSmbiosUpdateConfig.efi` at `0x9B5..0x9BC`: UTF-16 name at `0xFE0`, matching GUID at `0xE70`, requested size `0x2A`. In the successful-read branch `0x9C4..0x9E9` the module tests **byte `+0x05` and byte `+0x07`**, selectively rewriting bits 5 and 2 of one 32-bit SMBIOS-associated flag word. This is confirmed as a **feature-to-SMBIOS flag consumer**; it does not read or produce **`SetupCpuFeatures+0x1A`**, whose visibility-gate meaning remains UNKNOWN.

The native `PlatformInitAdvancedDxe.efi` also contains several real `WRMSR` instructions, but these must not be misreported as PL1/PL2 writes. The observed actions read/update `MSR 0x2FF` (MTRR default type), iterate indexed `0x250/0x258/0x259/0x268..0x26F` entries from table `0x9550`, and use `MSR 0xFE` to bound variable MTRRs `0x200/0x201` and following pairs. The corresponding native module is therefore carrying out **MTRR save/reprogram/restore behavior**, not a proven write to package power-limit `MSR 0x610` or to a confirmed processor power policy. This closes a misleading `WRMSR` candidate, not the PL1/PL2 route.

**Report checkpoint:** PL1/PL2 static-to-OS route remains **2/4 = 50%**, unchanged from the preceding checkpoint. The remaining steps are a verified native consumption/programming edge for the actual `CpuSetup` limit fields and a safe runtime/OS access path. For the `SetupCpuFeatures+0x1A` subproblem, the only presently closed fact is that it exists as an HII visibility gate; a named consumer at **other offsets** does not make its producer known.

Evidence: retained installed modules `corpus/analysis-modules/TM2309_2024-06-04_PlatformInitAdvancedDxe.efi`, `corpus/analysis-modules/TM2309_2024-06-04_MeSmbiosUpdateConfig.efi` and existing HII form inventory. Only static PE disassembly; no target execution or NVRAM modification.

## ThermalSmm native package power-limit writer (2026-10-08)

**CONFIRMED static x86-64 MSR write and three-row data table on the installed 2024-06-04 image; SMM callback registration and its ACPI trigger are confirmed below. Actual runtime execution, hardware outcome, and connection to `CpuSetup` remain UNKNOWN.**

A targeted PE executable-section inspection found a concrete candidate for **native RAPL power-limit programming** in `ThermalSmm` (FFS GUID `8C916319-1334-419A-9F2C-976CABFDBBCA`). Its writer routine at RVA `0x14F0` reads EC status through the serialized legacy ports `0x66/0x62` (helper `0x1C6C`), queries one OEM platform classifier `0x140C04`, selects one of three data rows, and executes these read/modify/write MSR operations:

- `0x65C` (**platform/PSys power-limit MSR**, per Linux's Intel RAPL MSR definitions): `mov edi,0x65C` at RVA `0x159F`; `RDMSR` at `0x15C2`, `WRMSR` at `0x1613`. Two raw policy values are shifted left by three and inserted into the two halves. Each half preserves bits 15..31 with the low/high `0x8000` enable bit explicitly set.
- **`0x610` (IA32_PACKAGE_POWER_LIMIT / MSR_PKG_POWER_LIMIT)**: `lea ecx,[rdi-0x4C]` at `0x1615`, `RDMSR` at `0x1618`, `WRMSR` at `0x1656`. This is a **direct hardware-register programming code path**; the selected pair of table values is shifted left by three and inserted into the low/high power-limit fields while preserving the other bits.
- `0x601` (**MSR_VR_CURRENT_CONFIG, Intel PL4 register family**, per Linux's Intel RAPL definitions): `lea ecx,[rdi-0x5B]` at `0x1658`, `RDMSR` at `0x165B`, `WRMSR` at `0x1687`; a third table value is shifted left by three and inserted into low 13 bits (mask `0xFFFFE000`). This identifies a static instantaneous/package PL4-configuration path, not proof of supported PL4 adjustment on the target CPU or of its physical effect.

The data table at RVA `0x20F0` is made of three six-dword rows: a **raw 0/1/2 row selector** and five encoded values. The exact native row literals are:

| Internal row | MSR 0x610 low field source | MSR 0x610 high field source | MSR 0x601 field source | MSR 0x65C low field source | MSR 0x65C high field source |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 50 | 50 | 75 | 56 | 64 |
| 1 | 70 | 115 | 215 | 87 | 95 |
| 2 | 45 | 43 | 105 | 56 | 61 |

All five values are shifted by `<<3` before insertion. **These are native table values, not verified watt limits or a user-facing Normal/Gaming/Office/Turbo mapping.** The mode-selection branches depend on the platform-classifier comparison against `3` and several EC bytes, including raw offsets `0x80`, `0x92`, `0xA9`, and `0x0E`. The precise product meanings of all predicates and their potential relationship to `QFAN` remain unproved. Importantly, this function does not show a `CpuSetup+0x2F/+0x35` input or a setup-variable read.

**Release comparison:** the .text section bytes and the above three data rows are byte-identical in the retained `ThermalSmm` images dated 2024-04-07 and 2024-06-04, despite different PE file packing/section raw sizes.

**Callback dispatch recovered (static):** no ordinary inbound direct `call` to RVA `0x14F0` exists because the firmware registers callback `0x16A0` via `EFI_SMM_SW_DISPATCH2_PROTOCOL` with software-SMI input `0xC2`; that callback jumps to `0x14F0`. The installed ACPI EC query `_Q35` writes `0xC2` to I/O port `0xB2`, providing the triggering route. Full instruction and GUID evidence is recorded in the later `ThermalSmm SW-SMI dispatch and ACPI EC trigger` section. **Runtime event delivery/execution is not proven**, and this is not a user-accessible PL1/PL2 setter.

**Report checkpoint definitions (current):** **CpuSetup→PL1/PL2→safe OS control** remains **2/4 = 50%** because the actual `CpuSetup` field-to-writer edge is not closed. The selected **ThermalSmm package-power-policy** route is now **3/4 = 75%**: exact MSR writes, row literals/selection, and SMM dispatch with an ACPI EC event trigger are statically confirmed. Hardware execution/operational acceptance and a safe OS setter remain open. These percentages are limited to their respective route denominators, not total CPU-power feature coverage.

Evidence: `corpus/control-modules/TM2309_2024-06-04_ThermalSmm_8C916319-1334-419A-9F2C-976CABFDBBCA_PE32.efi` (instructions `0x14F0..0x169D`, table `0x20F0..0x2137`) and retained 2024-04-07 counterpart. No device memory/register writes or hardware probes were performed during this analysis.

## ThermalSmm SW-SMI dispatch and ACPI EC trigger (2026-10-08)

**CONFIRMED — static UEFI SMM registration and installed ACPI trigger; actual SMI delivery/execution and public OS setter UNKNOWN.**

The earlier absence of a direct incoming `call 0x14F0` is explained by an **indirect SMM-dispatch callback**, not by an unreachable/stale routine. The following chain is visible in the retained June `ThermalSmm` PE and June ACPI DSDT:

1. The `ThermalSmm` PE entry point `0x1234` calls initialization routine `0x1428` at `0x1246`. The initializer gets an SMM protocol through `SmmLocateProtocol` (SMM System Table `+0xD0`) at `0x148A..0x1491` using the GUID at RVA `0x20E0`.
2. The GUID bytes `DC C6 A3 18 EA 5E C8 48 A1 C1 B5 33 89 F9 89 99` resolve to **`EFI_SMM_SW_DISPATCH2_PROTOCOL`** (`18A3C6DC-5EEA-48C8-A1C1-B53389F98999`), whose first interface method is `Register`. The static module sets `EFI_SMM_SW_REGISTER_CONTEXT.SwSmiInputValue = 0xC2` at `0x14A6`, passes handler `0x16A0` at `0x14AF`, and invokes `Register` through `[rax]` at `0x14B9`. Registration has status/error handling; a positive OS-level observation of success is not available.
3. The supplied callback `0x16A0` is an unconditional branch to `0x14F0`. That target is the recovered direct `MSR 0x65C / 0x610 / 0x601` power-policy writer.
4. In the installed ACPI DSDT, `\_SB.PC00.LPCB.Q_EC._Q35` calls `P8XH(0, 0x35)`, then assigns `SSMP = 0xC2`. `SSMP` is explicitly the first byte of `OperationRegion(SPRT, SystemIO, 0xB2, 0x02)`. A write of `0xC2` to the legacy software-SMI port therefore matches the registered SMM input `0xC2`. This establishes the target's **EC query -> ACPI write -> SW-SMI dispatch-registration -> native MSR writer route** at the static-instruction level. The actual EC conditions that generate query `0x35`, successful SMM registration, and on-device handler execution remain unobserved.

The same `_Q35` and `SPRT/SSMP` ACPI method/field appear in the retained April 2024 DSDT. The `ThermalSmm` `.text` bytes and three-row policy data match across the retained April/June PE images, so the static route is stable across those two factory releases.

**Policy row selection — confirmed at the branch and raw-data level, not at user-facing profile level:**

- Default internal table row is `0`.
- The SMM handler **reads raw indexed EC offsets** `0x80`, `0x92`, `0xA9`, and `0x0E` through EC host I/O ports `0x66/0x62` (command `0x80`), not through the ACPI `ERAM` memory-mapped field. The DSDT gives independently named fields `ACIN` and `BTIN` at `ERAM+0x80`, `RSOC` at `ERAM+0x92`, and `TSR6` at `ERAM+0x0E`. **Equivalence of the legacy indexed EC transport and memory-mapped `ERAM` has not been independently established**; those DSDT names are plausible aliases, not proven ownership of the host-indexed data.
- A nondefault row is considered only if `(EC[0x0E] & 0x20) != 0`, `BTIN == 1`, and `((EC[0xA9] & 0x02) != 0 || ACIN == 0)`. At that gate, the independent platform classifier result `0x140C04 == 3` selects internal row **2**, and any other classifier result selects internal row **1**. Otherwise internal row **0** remains selected.
- This code path reads its inputs from the **legacy EC indexed interface** and classifier; there is **no proven connection to `CpuSetup+0x2F/+0x35`**, `QFAN` or an external direct manual PL1/PL2 setter. The raw index/bit predicates are CONFIRMED, while translation to named memory-mapped `ERAM` fields remains LIKELY pending an alias check. Do not guess the product semantics of `EC[0xA9]` or turn a mode index into a fan preset.

**Progress checkpoint:** the previously defined selected `ThermalSmm package-power-policy` denominator moves from **2/4 = 50% to 3/4 = 75%**: (1) native write contract, (2) policy row table/selector, (3) registration and ACPI SW-SMI trigger path are statically confirmed. Remaining gate (4) is target execution/operational validation and a verified safe interface if any. The distinct **CpuSetup -> PL1/PL2 -> OS setter** scope remains **2/4 = 50%** (no target `CpuSetup` field-to-writer edge). Do not generalize either percentage to CPU tuning, Manager readiness or a flashable firmware.

Evidence:
- `corpus/control-modules/TM2309_2024-06-04_ThermalSmm_8C916319-1334-419A-9F2C-976CABFDBBCA_PE32.efi`, PE entry `0x1234`, registration `0x1428..0x14E1`, callback `0x16A0`, writer `0x14F0..0x169D`;
- `corpus/acpi-2024-06-04/TM2309_2024-06-04_DSDT_INTEL_SKL.dsl`, methods/fields `_Q35`, `SPRT` and `SSMP`;
- UEFI reference protocol identity/signature: `https://github.com/tianocore/edk2/blob/master/MdePkg/Include/Protocol/SmmSwDispatch2.h`.

## ThermalSmm MSR field preservation and control-domain boundaries

**CONFIRMED from installed PE instructions; register names/layout corroborated by external Intel/Linux reference code; runtime state UNKNOWN.**

The `ThermalSmm` policy writer updates **three distinct hardware power-control domains**, rather than one generic "PL1/PL2" variable: package RAPL `0x610`, platform/PSys `0x65C`, and the VR current configuration/PL4 family `0x601`. The register-family names follow Linux's `intel_rapl_msr.c`; the fact that this exact TM2309 module accesses and writes these addresses follows from the retained x86-64 instructions. This distinction is relevant to a future Manager HAL because package, platform and short/instantaneous limits are not interchangeable.

**Exact `MSR 0x610` mask/preservation contract:** the handler reads the old 64-bit register, forms its new low 32 bits as `(old_low & 0xFFFF8000) | (row_pkg_pl1 << 3)`, and its new high 32 bits as `(old_high & 0xFFFF8000) | (row_pkg_pl2 << 3)`, then writes the combined result. Given the Intel/Linux bit layout, it replaces only bitfields `[14:0]` and `[46:32]`. It **preserves** both enable bits, clamp flags, time windows and lock bits in the retained remainder, rather than enabling package PL1/PL2 itself. A set hardware lock bit may prevent the write from taking effect; the static code does not prove a successful on-device MSR update.

**`MSR 0x65C`** uses the same `<<3` encoding but forcibly sets bit 15 in each constructed 32-bit half (`| 0x8000`), unlike package `0x610`. **`MSR 0x601`** preserves the upper bits of the old low dword (`& 0xFFFFE000`) and replaces only bits `[12:0]` with `row_pl4 << 3`; the upper 32 bits remain read/preserved. The 0x601/PL4 mapping is an architecture-reference identification; target silicon support and actual resulting power constraints require execution proof.

**Power-unit condition:** every row literal is multiplied by eight in the resulting MSR field. Intel power-limit fields express power in the unit specified by `MSR_RAPL_POWER_UNIT (0x606)` low four bits. The static BIOS code analyzed here does **not** read that unit. Therefore the effective wattage is `row_literal × 8 × (2^-PWR_UNIT)` W, subject to hardware interpretation. If the target reports `PWR_UNIT == 3`, the three package PL1/PL2 pairs would decode to `50/50 W`, `70/115 W`, and `45/43 W`. **That target unit value has not been measured** and these are *conditional* examples, not confirmed TM2309 real-world limits.

**Separate event/control ownership:** the installed DSDT `_Q35` method writes `0xC2` to I/O port `0xB2`, matching the registered `ThermalSmm` SW-SMI callback. Its preceding `P8XH(0,0x35)` is only a conditional debug/POST-port helper: `P8XH` invokes `D8XH` only when `MDBG` exists, and `D8XH` writes debug state to port `0x80`. Conversely, `_Q24` and `_Q30` propagate `QFAN` through `NTDP` and do not explicitly invoke SW-SMI `0xC2`. Thus, from the visible AML, profile/DPTF notifications and an EC-requested power-policy reapply are **separate paths**. A future user-space RAPL write might be superseded by a later `_Q35` event, but that ordering and effect have **not** been observed on the target laptop.

**Remaining evidence gate:** execution-level comparison of `MSR 0x606`, `0x610`, `0x65C` and `0x601` before/after a naturally occurring `_Q35` event (without injecting SMI or writing unsafe values), together with the actual EC event source, is needed to establish effective hardware behavior. This analysis does not authorize a user-mode `PL1/PL2/PL4` setter. Scoped progress remains **ThermalSmm 3/4 = 75%** and **CpuSetup-to-OS power control 2/4 = 50%**, unchanged.

Evidence: TM2309 June `ThermalSmm.efi`, instruction ranges `0x15C0..0x1687`; installed `DSDT_INTEL_SKL.dsl` methods `_Q24`, `_Q30`, `_Q35`, `P8XH`, `D8XH`. Reference identities/bitfields (context, *not* TM2309 hardware acceptance): https://github.com/torvalds/linux/blob/master/drivers/powercap/intel_rapl_msr.c and https://github.com/torvalds/linux/blob/master/drivers/powercap/intel_rapl_common.c .

## Native CpuSetup ACPI consumers and Meteor Lake PL4 support (2026-10-08)

**CONFIRMED target PE input-field consumers; exact user-facing semantics UNKNOWN. Separate Linux driver family capability corroborated; target hardware acceptance UNKNOWN.**

The installed 2024-06-04 `AdvancedAcpiDxe.efi` has two independent `CpuSetup` `GetVariable` read sites (vendor GUID `B08F97FF-E6E8-4193-A997-5E9E9B0ADB32`, variable name `CpuSetup`, expected size `0x5E0`). Native machine-code consumers now traced:

- At `0x2233..0x2262`, the destination buffer begins at stack address `rbp-0x80`. Immediately after `GetVariable`, `cmp byte ptr [rbp+0x2D],0` at `0x2265` reads **`CpuSetup+0xAD`**. When nonzero, code invokes routine `0x644`, which enumerates UEFI handles via a protocol GUID, accesses per-handle interfaces and invokes a related table/configuration service. This is **not** a proven PL1/PL2 field consumer. The branch does not check this particular `GetVariable` return status before the comparison; do not assume the path always uses valid initialized configuration without further initialization proof.
- At `0x283C..0x286E`, a second buffer begins at `rbp+0x4D0`. Code at `0x2A7F` tests **`CpuSetup+0x42`** (`rbp+0x512`), then tests a separate local condition (`rbp+0x51`); if both allow the branch, at `0x2A95` it reads **`CpuSetup+0x43`** (`rbp+0x513`) and copies that byte into a constructed firmware/ACPI-side configuration object at `object+0x75`. If either check fails, that output field is set to zero. The identities and physical effects of `+0x42/+0x43` are not yet known; do not rename them as package power limits or an undervolt knob.

This closes two **specific non-PL1/PL2 `CpuSetup` consumption edges**. No evidence here proves use of the actual package-power question bytes `+0x2F/+0x35`, nor their processor override equivalents, by the recovered SMM `MSR 0x610` handler. A buffer read does not establish a complete Setup-to-hardware limit contract.

**Linux family-level PL4 availability:** Linux `drivers/powercap/intel_rapl_msr.c` maps both `INTEL_METEORLAKE` and `INTEL_METEORLAKE_L` to `rapl_defaults_core_pl4`, which enables `msr_pl4_support`, and associates that RAPL domain with `MSR_VR_CURRENT_CONFIG (0x601)`. This is a **CONFIRMED upstream Linux driver capability for the CPU family**, independently consistent with the target `ThermalSmm` writing `0x601`. It is **not** proof that this particular TM2309 boots with an unlocked, writable PL4 limit, exposes a useful Windows API, or will retain a user value after EC-triggered SW-SMI events. Treat `PackagePowerLimit4` as a **research-only capability candidate** until actual MSR-unit/lock/readback and operating-system access evidence exists.

**Scoped progress unchanged:** `ThermalSmm` 3/4 = **75%** (static policy and event routing, no target execution), `CpuSetup -> PL1/PL2 -> safe OS control` 2/4 = **50%** (no target field-to-hardware edge). The newly identified fields are useful for platform decomposition but close neither outstanding acceptance gate.

Evidence: retained `corpus/power-modules/AdvancedAcpiDxe.efi` native code at `0x2233..0x2270`, `0x644..0x70A`, `0x283C..0x286E` and `0x2A7F..0x2AAB`. Linux RAPL family support: https://github.com/torvalds/linux/blob/master/drivers/powercap/intel_rapl_msr.c (the `rapl_ids` table and `rapl_defaults_core_pl4`).

## Native SetupUtility RAPL power readback (2026-10-08)

**CONFIRMED target static native readback in the installed A0A SetupUtility; neither a package-power write route nor ordinary OS-visible telemetry is proven.**

A fresh bounded inspection of **317 SHA-256-unique PE images** directly extractable from the complete decompressed 2024-06-04 inner firmware volume (356 FFS envelopes) found raw `0F 30` candidate byte sequences within executable `.text` in **21 PE images**. The 21-image count is **opcode-pattern candidate screening**, not proof that all 21 contain reachable `WRMSR` action nodes or package PL1/PL2 writes. Individual instructions must be classified before assigning semantics. This extends the earlier 41-module extracted sample and prevents relying on that sample as exhaustive.

The concrete useful consumer in `SetupUtility` is an **MSR read/formatting route**:

- At RVA `0x14A20..0x14A3C`, the code reads **`MSR_RAPL_POWER_UNIT = 0x606`** through local helper `0x2802C` (native `RDMSR` at `0x2802C`, combines `EDX:EAX`). It extracts the low four power-unit bits and constructs the divisor using `0x28020` (left-shift helper). Display formatting uses division and factor `1000` to express the fractional portion.
- At `0x14C2B` it reads **`MSR_PKG_POWER_LIMIT = 0x610`** via the same `RDMSR` helper; the code masks the low 15 bits (`& 0x7FFF`) at `0x14C45`, then formats those power bits using the previously recovered power unit, passing values into the HII display/string update route around `0x14C10..0x14CBC`.
- The high 32-bit power-limit half is read from the same value (`>>32 & 0x7FFF`) at `0x14CC1..0x14CD3`, also undergoing formatting before HII presentation. A second `MSR 0x610` read at `0x15039` follows the same low-field formatting style; both high/low fields are also included in a later HII update around `0x150C9..0x151EF`.
- At `0x151F4` it also reads raw **`MSR 0x64C`** and tests its high-order state bit, but the intended product meaning and display label for that register have not been fully classified here.

The readout route is adjacent to reads of the named `SetupCpuFeatures` (size `0x2A`) and `CpuSetup` (size `0x5E0`) variables at `0x147D5` and `0x14828`. Proximity **does not** prove `CpuSetup+0x2F/+0x35` drives the `0x610` writer, and the inspected `0x610` callsites invoke `RDMSR` rather than `WRMSR`. The three direct `WRMSR` instructions elsewhere in the same SetupUtility belong to other inspected flows (`0x607/0x608` and `0x8B`), not this package readback operation.

**Binary-version observation:** the A0A and B0B SetupUtility PE files have different whole-file SHA-256 digests, but direct instruction checks confirm the same `0x606` read at `0x14A20`, two `0x610` reads at `0x14C2B` and `0x15039`, `0x64C` read at `0x151F4`, and `RDMSR` helper at `0x2802C` in both images. Thus the selected **static BIOS-side package-power display route** is stable at these anchors, without claiming all code or data is byte-identical.

**User-facing capability boundary:** this can support a *future* semantic `PackagePowerLimitCurrentReadback` contract at the firmware UI/static level, but does **not** by itself expose a safe user-space backend. It complements the independent `ThermalSmm` writer/automatic EC-event route. `CpuSetup → PL1/PL2 → OS control` remains **2/4 = 50%**, and the `ThermalSmm` route remains **3/4 = 75%**; neither outstanding gate is closed by BIOS UI telemetry. In particular the fixed plant-policy rows, active unit exponent and package lock state are not determined by this analysis alone.

Evidence: `corpus/analysis-modules/TM2309_0A0A_MS_SetupUtility_FE3542FE-C1D3-4EF8-657C-8048606FF670_PE32.efi` and B0B counterpart (selected instruction offsets above), plus the already characterized installed `ThermalSmm` action. All evidence is static and read-only.
