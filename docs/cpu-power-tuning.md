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
