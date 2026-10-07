# ACPI / WMI control contracts

Target: Xiaomi Redmi Book Pro 16 2024, board TM2309.

This document records recovered control behavior. Raw identifiers remain evidence; semantic labels are only as strong as the evidence state shown.

## Evidence levels

- **CONFIRMED**: directly supported by target firmware bytes / AML / IFR.
- **LIKELY**: target static evidence is consistent with independent same-model runtime evidence, but this exact installed firmware/EC combination has not yet been observed executing that behavior.
- **UNKNOWN**: semantic meaning is not yet closed.

## WMI control surface

### Multiplexed control method

**CONFIRMED**

- WMI method GUID: `B60BFB48-3E5B-49E4-A0E9-8CFFE1B3434B`
- WDG object ID: `AA`
- instance count: 1
- flags: METHOD
- AML method: `\\_SB.PC00.WMID.WMAA`

`WMAA` is exposed as the single WMI method for object `AA`. The AML only handles WMI method ID `1`; read/write direction is encoded inside the payload rather than by separate WMI method IDs.

Input buffer layout used by `WMAA`:

| Offset | Width | Semantic name |
| --- | ---: | --- |
| 0x00 | u16 | function group (`FUN1`) |
| 0x02 | u16 | selector (`FUN2`) |
| 0x04 | u16 | sub-selector/value0 (`FUN3`) |
| 0x06 | u32 | value1 (`FUN4`) |

Return buffer layout:

| Offset | Width | Semantic name |
| --- | ---: | --- |
| 0x00 | u16 | status (`SGER`) |
| 0x02 | u16 | returned function (`FUTR`) |
| 0x04 | u16 | value0 (`FRD0`) |
| 0x06 | u32 | value1 (`FRD1`) |
| 0x0A | u32 | value2 (`FRD2`) |
| 0x0E | u32 | value3 (`FRD3`) |

Observed operation groups:

- `FUN1=0xFA00`: read/query.
- `FUN1=0xFB00`: write/set.
- successful implemented branches use status `0x8000`.
- unsupported top-level selectors use status `0xE000`.

### Data/query block

**CONFIRMED**

- GUID: `05901221-D566-11D1-B2F0-00A0C9062910`
- WDG object ID: `AB`
- instance count: 1

The firmware exposes a static `WQAB` buffer.

## WMI event surface

**CONFIRMED**

The firmware exposes four event GUIDs:

| Notify | GUID |
| ---: | --- |
| 0x20 | `46C93E13-EE9B-4262-8488-563BCA757FEF` |
| 0x21 | `FA78E245-2C0F-4CA1-91CF-15F34E474850` |
| 0x22 | `1DCEAF0A-4D63-44BB-BD0C-0D6281BFDDC5` |
| 0x23 | `3F9E3C26-B077-4F86-91F5-37FF64D8C7ED` |

`_WED(0x20..0x23)` returns the shared 32-byte event buffer `EVBU`. For the primary `EV20` route:

- byte 0 = event type,
- byte 1 = event code,
- byte 2 = event value/state.

Confirmed target-static event codes include:

- `0x05`: keyboard-backlight state event; value is derived from EC `KBLL`.
- `0x16`: performance/fan-mode event; value is read from EC `QFAN`.
- `0x21`: event generated from EC `MIUT`, with inverted outward boolean.

Independent same-model runtime evidence identifies `0x21` as microphone mute and `0x16` as OEM performance mode. Those human labels remain **LIKELY** for the exact 2024-06-04 BIOS + EC 1.10 target until execution evidence is captured on that target.

## EC field map

The DSDT field `ERAM` exposes the following directly relevant fields.

| EC location | Raw field | Current semantic state |
| --- | --- | --- |
| byte 0x17, bit 4 | `MIUT` | **LIKELY** microphone-mute state/control |
| byte 0x60 | `QFAN` | **CONFIRMED** performance/fan-mode control byte |
| byte 0x81 | `ADPW` | **UNKNOWN** adapter/power-derived status byte |
| byte 0xA4 | `LONL` | **LIKELY** charge-protection bitfield; WMI uses bit 0 |
| byte 0xAB | `SOH1` | **UNKNOWN** status byte; name suggests state-of-health but not promoted |
| byte 0xB2, bits 0..6 | `KBLL` | **CONFIRMED** keyboard-backlight state used for WMI events |
| byte 0xB2, bit 7 | `KBMD` | **UNKNOWN** adjacent keyboard-backlight mode bit |

### EC helpers

**CONFIRMED**

- `ECRD(field)`: reads an EC field.
- `ECWT(value, field)`: writes an EC field.
- `FUNR(selector)`: returns selected EC state.
- `FUNR(0x16)`: returns `QFAN`.
- `FUNR(0x20)`: returns `MIUT`.
- `NTDP(value)`: publishes a device-specific thermal/platform notification; for QFAN values it updates `ODV1` and notifies `IETM`.

## Performance / fan mode contract

### Direct WMI control

**CONFIRMED**

Read:

- `WMAA`: `FUN1=0xFA00`, `FUN2=0x0800`.
- firmware reads `FUNR(0x16)` / `QFAN`.
- accepted returned values are 1, 2, 3, 4.

Write:

- `WMAA`: `FUN1=0xFB00`, `FUN2=0x0800`.
- values other than special 5/7 are written directly to `QFAN`.
- firmware emits event `QV20(1, 0x16)`.
- special values 5 and 7 are routed to `SMMD`, not normal QFAN mode storage.

The OEM `HQNVS000` SSDT provides a second route:

- method `WM01`, command 0x09 writes the supplied integer directly to `QFAN`,
- waits 5 ms,
- reads the new QFAN value,
- calls `NTDP(value)`,
- returns the success string `Set performance mode Success!`.

### Setup-side mode enum

**CONFIRMED**

UEFI HII VarStore:

- name: `SystemConfig`
- GUID: `A04A27F4-DF00-4D42-B552-39511302113D`
- VarStore ID: `0x1234`
- size: `0x4B0`

Field `SystemConfig+0x103`: **System Performance Mode**

| Setup value | Label |
| ---: | --- |
| 0 | Turbo Mode |
| 1 | Balance Mode (default) |
| 2 | Silence Mode |
| 3 | Full Speed Mode |

The static transformation is now **CONFIRMED** in native module `OemWMISmmCallback`. Its selector `0x0800` loads `SystemConfig` and accesses exactly byte `+0x103`.

Mapping:

| SystemConfig+0x103 | Setup label | QFAN / WMI value |
| ---: | --- | ---: |
| 0 | Turbo Mode | 3 |
| 1 | Balance Mode | 1 |
| 2 | Silence Mode | 2 |
| 3 | Full Speed Mode | 4 |

The native read handler implements the table `{0→3, 1→1, 2→2, 3→4}`; the write handler implements the exact inverse `{1→1, 2→2, 3→0, 4→3}`.

Independent same-model runtime evidence on later firmware reports QFAN:

- 1 = balanced,
- 2 = quiet/silence,
- 3 = performance/turbo,
- 4 = full speed.

For the exact installed firmware image, the numeric and human label mapping is **CONFIRMED static target evidence**. Runtime behavior on the local machine remains a separate execution-proof level.

## SystemConfig backup mapping

### AutoBackupSCUSetting

**CONFIRMED**

- module: `AutoBackupSCUSetting`
- FFS GUID: `2EACAEEE-6254-4FAC-9B32-9B12CC56514F`

Backup variable:

- name: `ABSS`
- GUID: `89CB0E8D-393C-4830-BFFF-65D9147E8C3B`

The module copies fields one-for-one in both directions. Relevant mappings:

| SystemConfig | ABSS | Semantic name |
| ---: | ---: | --- |
| 0x101 | 0x15 | CPU Convertible Turbo Mode |
| 0x102 | 0x16 | KB Backlight Mode |
| 0x103 | 0x1E | System Performance Mode |
| 0x105 | 0x22 | Type-C non-PD input threshold |
| 0x104 | 0x23 | UNKNOWN |
| 0x106 | 0x24 | Turbo Mode Hotkey Event |
| 0x107 | 0x25 | Display Configuration |
| 0x108 | 0x26 | UNKNOWN 0..3 value |
| 0x109 | 0x0F | UNKNOWN numeric byte |
| 0xF3 | 0x13 | USB Charge |
| 0xF4 | 0x14 | USB Charge Battery Threshold |
| 0xF5 | 0x31 | CPU Auto Mode fan preset: 0 Gaming, 1 Normal, 2 Office |
| 0xF6 | 0x32 | GPU Auto Mode fan preset: 0 Gaming, 1 Normal, 2 Office |
| 0xF7 | 0x34 | CPU FAN Turbo Mode Speed raw preset: 0 Max, 1 Medium, 2 Medium compatibility alias |
| 0xF8 | 0x35 | GPU FAN Turbo Mode Speed raw preset: 0 Max, 1 Medium, 2 Medium compatibility alias |
| 0xF9 | 0x33 | fan-related Setup field, semantics not yet closed |

No value conversion occurs in this backup/restore module.

## Other confirmed Setup controls

### Native Setup → EC synchronization

**CONFIRMED — corrected static target evidence**

`HQDxeService` reads the persisted 0x4B0-byte Setup configuration and applies six fields directly to EC state during DXE initialization:

| Setup/SystemConfig offset | EC state | Semantic contract |
| ---: | --- | --- |
| `+0xE9` | `IKBW` | internal-keyboard wake enable |
| `+0xEA` | `WOUB` | wake-on-USB enable |
| `+0xF3` | `AOUF` | USB Charge mode |
| `+0xF4` | `UCBT` | USB Charge Battery Threshold |
| `+0x102` | `KBMD` | keyboard-backlight policy |
| `+0x103` | `QFAN` | performance/fan profile boot-time synchronization |

Earlier reports using `+0x29/+0x2A/+0x33/+0x34/+0x42/+0x43` as Setup offsets are **WITHDRAWN**. Those were RBP-relative local-stack coordinates; typed Setup-buffer recovery establishes the offsets above.


### USB charging

**CONFIRMED HII semantics; boot-time hardware apply CONFIRMED, live OS apply UNKNOWN**

`SystemConfig+0xF3`: USB Charge

- 0 = Off (default)
- 1 = Always on
- 2 = One time only

`SystemConfig+0xF4`: USB Charge Battery Threshold

- 10 = 10%
- 20 = 20%
- 30 = 30% (default)

`HQDxeService` selector 1 applies `SystemConfig+0xF3` to EC `AOUF` at boot, and selector 2 applies `SystemConfig+0xF4` to EC `UCBT`. The persisted policy and boot-time hardware path are therefore CONFIRMED. A live operating-system setter for these two fields is not yet proven.


### Type-C non-PD input threshold

**CONFIRMED HII semantics**

`SystemConfig+0x105`, visible Setup item `Type-C Power Supply(non PD protocol) Input Threshold`.

The default value is 2 = 5V/0.5A. Other option labels remain to be materialized when needed.

### Turbo hotkey

**CONFIRMED HII semantics**

`SystemConfig+0x106`: Turbo Mode Hotkey Event

- 0 = Disable
- 1 = Enable (default)

### CPU Convertible Turbo Mode

**CONFIRMED HII semantics**

`SystemConfig+0x101`:

- 0 = Standard
- 1 = Boost (default)


### Fine fan preset policy

**CONFIRMED HII/UI semantics; live hardware apply UNKNOWN**

The persisted Setup structure contains paired CPU/GPU fan-policy selections:

- `SystemConfig+0xF5`: CPU Auto Mode fan preset — 0 Gaming, 1 Normal, 2 Office.
- `SystemConfig+0xF6`: GPU Auto Mode fan preset — 0 Gaming, 1 Normal, 2 Office.
- `SystemConfig+0xF7`: CPU FAN Turbo Mode Speed — 0 Max, 1 Medium; raw value 2 is treated as a platform-compatibility alias for Medium on one variant.
- `SystemConfig+0xF8`: GPU FAN Turbo Mode Speed — same encoding.

The BIOS UI update path persists these values and refreshes its control model. The immediate post-update route contains no direct EC write or OEM hardware-control apply operation for these four fields. Treat them as persisted firmware policy until another target route or runtime evidence proves when/how they become active.

### Keyboard backlight Setup mode

**CONFIRMED HII semantics**

`SystemConfig+0x102`:

- 0 = Standard
- 1 = Power Saving (default)

`HQDxeService` selector 4 maps this field to EC `KBMD` (byte 0xB2 bit 7) during boot-time Setup → EC synchronization. This policy bit is distinct from live keyboard-backlight level/state field `KBLL` (bits 0..6).

## Keyboard-backlight event contract

**CONFIRMED**

EC `KBLL` resides at byte 0xB2, bits 0..6. WMI event code `0x05` maps:

| KBLL | WMI event value |
| ---: | ---: |
| 1 | 0 |
| 2 | 5 |
| 4 | 10 |
| 8 | 0x80 |

The extracted ACPI tables show this as a read/event contract. A target-static ACPI setter for `KBLL` has not been found.

## Version stability

**CONFIRMED static evidence**

The key fan/WMI ACPI methods `WMAA`, `EV20`, `WM01`, DSDT `QFAN`, `FUNR`, and `NTDP` are semantically identical between the 2024-04-07 and 2024-06-04 firmware packages.

The analyzed decompressed firmware volume for 2024-06-04 vs 2025-06-10 has only seven changed bytes, all accounted for by release date/version metadata. All 319 PE modules retain the same layout; only `SmbiosDxe` and `SetupUtility` differ, and those differences are version strings / SMBIOS release fields rather than recovered behavior changes.


## Battery / charge-protection WMI group

### Charge protection

**CONFIRMED static target contract**

WMAA read:

- function group: `0x1000`
- sub-selector: `2`
- firmware reads EC byte `LONL` at offset `0xA4`
- returned value is exactly `LONL.bit0`.

WMAA write:

- function group: `0x1000`
- sub-selector: `2`
- `FUN4=1` sets only `LONL.bit0`
- any other `FUN4` value clears only `LONL.bit0`
- other bits in `LONL` are preserved
- success status is `0x8000`.

Independent same-model runtime evidence reports that this bit controls the EC battery charge limit: set = 80% protection, clear = 100% normal charging. For the exact installed target, the static WMI/EC bit contract is CONFIRMED; the 80% physical effect is corroborated by same-model runtime evidence and remains pending local execution proof.

### Adapter power threshold

**CONFIRMED static target contract**

WMAA read `0x1000/3` reads EC byte `ADPW` at offset `0x81` and returns:

- 0 when `ADPW >= 140`
- 1 when `ADPW < 140`.

Independent same-model runtime evidence reports `ADPW=140` with the stock 140 W USB-C supply.

### Unknown status byte

WMAA read `0x1000/1` returns EC byte `SOH1` at offset `0xAB`.

Evidence state: **UNKNOWN semantic meaning**. The raw name alone is insufficient to promote it to a battery-health interpretation.

## Mic-mute WMI group

### Static contract

**CONFIRMED**

WMAA read `0x0A00/5`:

- reads EC selector `FUNR(0x20)`, which returns `MIUT`
- returns outward boolean `!MIUT`.

WMAA write `0x0A00/5`:

- outward `FUN4=1` writes EC `MIUT=0`
- any other value writes EC `MIUT=1`
- waits 150 ms
- emits WMI event code `0x21`
- returns status `0x8000`.

The physical/user-facing identity of this route as microphone mute is independently confirmed on the same TM2309 model. The exact outward 0/1 user-state polarity is intentionally left neutral until a target execution trace or authoritative caller implementation closes it.


## Native SMM WMI dispatch

### OemWMISmmCallback

**CONFIRMED**

The firmware contains native SMM module `OemWMISmmCallback`, FFS GUID `FAD93433-76B9-4482-4567-3BEACEA9B35D`.

It implements the same packet family using explicit selector→handler tables.

Read table (`FUN1=0xFA00`):

- `0x0800 → 0x1BDC`
- `0x0900 → 0x1C60`
- `0x0A00 → 0x1810`
- `0x0B00 → 0x19C8`
- `0x0C00 → 0x18AC`
- `0x0D00/0x0E00/0x0F00 → 0x1D38`
- `0x1000 → 0x1A7C`

Write table (`FUN1=0xFB00`):

- `0x0800 → 0x1AD0`
- `0x0A00 → 0x17C8`
- `0x0B00 → 0x1900`
- `0x0C00 → 0x1860`
- `0x0D00/0x0E00/0x0F00 → 0x1CEC`
- `0x1000 → 0x1A30`

Selector `0x0800` is the native System Performance Mode bridge described above.

Selector `0x0B00` reads/writes `SystemConfig+0x107`, which IFR identifies as **Display Configuration**. The native write handler accepts only values 0 or 1, saves the modified SystemConfig when changed, and invokes the associated OEM apply callback. This selector is therefore **CONFIRMED** as the Display Configuration control route.


## Unresolved native service groups

**UNKNOWN semantic meaning; structural dispatch CONFIRMED**

The native SMM WMI dispatcher forwards several still-unclassified groups into an internal OEM SMM service.

Confirmed structure:

- group 0x0900 read returns four 16-bit values from one internal service operation;
- group 0x0C00 read/write forwards a selector and value through paired internal service operations;
- groups 0x0D00, 0x0E00 and 0x0F00 share another paired read/write operation keyed by the top-level group identifier.

The internal service used by these routes is identified by raw GUID
D6CA51D1-6E56-4359-9ACA-663A247D39CD.

Multiple Insyde/OEM SMM modules locate or subscribe to this service. The inspected ODM service module does not establish itself as the D6CA owner; it registers its own service object and separately waits for D6CA availability. No authoritative source name for the D6CA protocol was found.

Do not assign user-facing semantics to groups 0x09, 0x0C or 0x0D..0x0F until their actual producer is recovered or runtime behavior closes the contract.

These groups are not current RedmiBook Manager implementation candidates.


## Operating-system-visible command surface

**CONFIRMED static route; same-model runtime corroboration**

The existence of native SMM handlers does not imply that every handler is reachable through the operating-system-visible WMAA method.

Independent execution testing on TM2309 firmware 1.11 reports the OS-visible WMAA command surface as:

- 0x08 — performance profile: implemented;
- 0x0A / subcommand 5 — implemented;
- 0x10 / GET subcommands 1..3 — implemented;
- 0x10 / SET subcommand 2 — implemented;
- 0x09 — unsupported through WMAA;
- 0x0D — unsupported through WMAA;
- 0x12 — unsupported through WMAA;
- 0x13 — unsupported through WMAA;
- 0x14 — unsupported through WMAA;
- 0x16 — unsupported through WMAA.

Unsupported top-level operations return status 0xE000.

This distinction is mandatory for Manager capability discovery. Internal native handlers and dormant generic-MIFS functionality must not be published as user capabilities unless the actual OS-visible route is proven on the target.

The same runtime report also documents a firmware response quirk: successful SET branches apply the operation and set the status code but may leave the returned function identifier at zero. A backend must validate SET responses according to the TM2309 contract rather than requiring GET-style function echo.

Published evidence:
- https://lkml.rescloud.iu.edu/2609.3/14028.html
- https://lkml.iu.edu/2609.3/14043.html


## Huaqin S5 wake and RTC-wake routes

**CONFIRMED — static target ACPI route, installed 2024-06-04 AML; argument domain and physical outcome UNKNOWN.**

The distinct Huaqin WMI device `\_SB.HQWI` implements two S5-related commands, separate from the MIFS `WMAA` interface:

- `WM01`, low command selector `0x03`: interpret the input as an integer, invoke `HSMI(value, 0x82)`, and, when `\_SB.PC00.LPCB.Q_EC.ECD2` exists, invoke `ECD2(0xDD, value)`. The returned success **string is unconditional** and is not proof that the EC or S5 wake policy accepted the value.
- `WMAB`, `Arg1 == 1`: interpret the input as an integer, prepare CMOS index/data access `0x72/0x73`, invoke `HSMI(value, 0x82)`, wait 5 ms, then read CMOS index `0x61`. It returns a success string only when the readback byte equals zero, otherwise a failure string. This is the route whose firmware-facing text identifies **S5 RTC wake**.

The `HSMI` helper uses SystemIO `0xB3` for its first argument and `0xB2` for its second argument. The DSDT `ECD2` helper waits for `EC6C.bit1` (busy) to clear, writes its first argument to EC command port `EC6C`, waits again, writes its second argument to EC data port `EC68`, and waits once more. This establishes the EC-side command transport, **not** the valid input range or an observed wake event.

The two retained ACPI `HQNVS000` AML tables dated 2024-04-07 and 2024-06-04 are byte-identical (matching SHA-256 in the extracted corpus). Both WMI routes are therefore present in the installed static image. The distinction from MIFS, the command argument's bit semantics, actual OS-client reachability, RTC timing representation, and target-machine execution are still separate gates. Neither route should be published as an unrestricted runtime setter.

Evidence: `corpus/acpi-2024-06-04/TM2309_2024-06-04_SSDT_HQNVS000.dsl` (`WM01`, `WMAB`, `HSMI`); `corpus/acpi-2024-06-04/TM2309_2024-06-04_DSDT_INTEL_SKL.dsl` (`ECD2`). 

## OEM-derived fan preset encoding variant

**CONFIRMED native callsites in both 2024-04-07 and installed 2024-06-04 H2O UI images; OEM ODM implementation independently CONFIRMED as unsupported at this particular slot. Runtime provider identity/hardware apply still UNKNOWN.**

The H2O UI obtains a raw 0/1 fan-selection variant by invoking OEM protocol GUID `754F7701-3C51-4F73-8FEF-314FDFA6DC5B` at interface slot `+0x48`. The call has three output arguments, with the third pointing at the variant byte. If the provider is absent or returns EFI_ERROR, the UI sets that byte to zero. This is independently present at old UI call `0x145E0` (variant `0x79F8C`, error fallback `0x145E8`) and **installed June UI** call `0x14648` (variant `0x7A11C`, error fallback `0x14650`). The installed route was verified from the retained PE machine instructions even though its Analysis action index was temporarily unavailable.

The variant is consumed when the BIOS UI normalizes the persisted CPU/GPU Turbo fan speed fields at `SystemConfig+0xF7/+0xF8`. UI `Medium` has distinct stored raw forms `1` and `2` depending on the variant. A raw value must therefore not be assumed globally portable.

**Important provider boundary:** In the extracted June `OemODMDxeDriver.efi`, a `EFI_BOOT_SERVICES.InstallProtocolInterface` call at `0xB33` installs the GUID with an interface base at object offset `+0x28`. This base matters: interface method `+0x48` resolves to object slot `+0x70` (populated at `0xA98`), which points to function `0x1A90`, returning `EFI_UNSUPPORTED (0x8000000000000003)`. The nearby functional methods `0x1BE0` and `0x1A9C` belong to *different* interface slots. Treating `[object+0x48]` as interface slot `+0x48` is an ABI/base-offset mistake.

Therefore the factory ODM implementation cannot supply the requested variant through this slot; with that implementation, the H2O UI takes its documented fallback. Whether an alternate provider is selected at runtime and whether the persisted fan policy is actually applied by an EC/native consumer remains **UNKNOWN**. This is **not** proof that the complete firmware lacks a hardware fan-preset route, and it is not a safe OS setter.

Evidence: retained `corpus/analysis-modules/TM2309_{old,new}_OEM_SetupFanUi_candidate.efi`, `corpus/oem-protocol-candidates/OemODMDxeDriver.efi`, x86-64 instruction views of `0x145C2..0x145EF`, `0x1462A..0x14657`, and `0xA32..0xB33`.

**Investigation checkpoint (selected fine-fan-control static route only): 40% → 60%, 2/5 → 3/5 known decision gates.** Covered: HII/Setup semantics, UI persistence, and the OEM protocol slot's known factory implementation. Still open: actual downstream EC/runtime fan-policy apply and an independently proven safe OS control path. This is not fan hardware acceptance or whole cooling-system coverage.

### Bounded direct-access audit of fine fan fields

**CONFIRMED bounded static audit; negative reachability conclusion NOT established.**

A read-only disassembly scan of **38 unique extracted PE images** (deduplicated by SHA-256 across the current analysis/control/power/SystemConfig module corpus) looked for direct x86-64 memory references at displacement `+0xF5/+0xF6/+0xF7/+0xF8`. The matching grouped fan-policy accesses in this corpus were located in the H2O Setup UI and `AutoBackupSCUSetting`. The latter copies the four bytes from `Setup+0xF5..+0xF8` to backup entries `+0x31,+0x32,+0x34,+0x35` (`0xC45..0xC66`), with the inverse copies at `0xF5C..0xF7A`. This is a **configuration backup/restore** contract, not a demonstrated EC fan writer.

The audit does not cover every firmware volume or indirect/computed address, so it cannot prove the absence of a separate fan-application route. Continue through a new concrete consumer/provider lead or controlled runtime correlation, not repetitive unsupported WMI calls.

### Bounded OEM protocol provider census (2026-10-07)

**CONFIRMED bounded corpus inventory; installed runtime provider selection still UNKNOWN.**

A deduplicated (by binary SHA-256) read-only scan of the retained EFI module corpus located the raw `754F7701-3C51-4F73-8FEF-314FDFA6DC5B` GUID in **11 unique extracted PE images**. The ordinary observed consumers use `EFI_BOOT_SERVICES.LocateProtocol` (boot-services slot `+0x140`); `guid_owner_139451c.efi` also has a protocol notification-registration path (`RegisterProtocolNotify`) that must not be misread as installation. The confirmed provider-install action in this bounded set belongs to `OemODMDxeDriver`, with the interface base and unsupported fan-variant slot described above.

This significantly narrows the **retained candidate corpus**: no second installer is established by the inspected direct GUID references. It is **not** proof of exclusivity in the entire factory volume, because GUID indirection or an unextracted provider remains possible. With the confirmed ODM slot returning `EFI_UNSUPPORTED`, the BIOS UI's fallback branch has a concrete explanation for that implementation. No independent route has yet linked `SystemConfig+0xF5..+0xF8` to a live EC fan-duty/mode write.

**Progress denominator unchanged:** the fine-fan route remains **3/5 (60%)** against the preceding checkpoint. Runtime apply and safe OS access are still open. Do not increase the score for negative candidate screening alone.

## Huaqin WMI GUID/object discovery (2026-10-08)

**CONFIRMED — installed factory ACPI `_WDG` metadata and method bodies; operating-system client execution and accepted wake argument values UNKNOWN.**

The second, independent TM2309 `PNP0C14` device `\\_SB.HQWI` (UID 0) exposes a static `_WDG` buffer of exactly `0x3C = 60` bytes, holding three 20-byte WMI GUID blocks. Decode the 128-bit GUID fields in the standard mixed little-endian ACPI WMI representation; do not treat the first 16 bytes as a big-endian display UUID.

| ACPI/WMI GUID | Object ID | Instances | Flags | Target method / contract |
| --- | --- | ---: | ---: | --- |
| `05901221-D566-11D1-B2F0-00A0C9062910` | `00` | 1 | `0x00` | Standard WMI BMOF/metadata data block, backed by the target's `WQ00` buffer; **not a separate hardware control method** |
| `657B6048-310C-4A90-A211-10A17922A0AF` | `01` | 1 | `0x06` | Huaqin `WM01` method group, including S5 wake selector `0x03` and alternative performance-mode selector `0x09` |
| `F80A5498-23F3-4053-A244-B39067EC476F` | `AB` | 1 | `0x06` | Huaqin `WMAB` method group, including RTC wake method index `1` |

For the latter two entries, flags `0x06` are **WMI method (0x02) | ASCIZ string (0x04)**, not an asynchronous WMI event. The Linux ACPI WMI interface documentation specifies these flags and the `WMxx` name construction; the GUID values and method bodies themselves are established by the retained TM2309 AML.

The firmware method ABI is **ACPI `WM01(Arg0, Arg1, Arg2)` / `WMAB(Arg0, Arg1, Arg2)`**: `Arg0` is the WMI instance, `Arg1` selects the operation inside the GUID, and `Arg2` contains the payload. The firmware converts selected wake/performance payloads using `ToInteger(Arg2)` and returns literal text such as `CONFIG S5 WAKE SUCCESS!` / `CONFIG S5 RTC WAKE FAIL!`. **Do not infer a fixed 32-byte MIFS binary packet** or an accepted numeric range from this string-flagged interface.

**Per-method boundaries:**

- `WM01`, `Arg1 & 0xFF == 0x03`: the previously recovered S5 wake path calls `HSMI(value,0x82)` and optionally EC `ECD2(0xDD,value)`. Its success string is unconditional and **not** a readback/validation guarantee.
- `WM01`, `Arg1 & 0xFF == 0x09`: writes the parsed mode into EC `QFAN` through guarded ACPI helpers and calls `NTDP`; this is an alternate method surface for the **same profile state**, not a distinct fan curve or a new mode enum. Conditional helper existence and exact OS-side marshaling remain relevant.
- `WMAB`, `Arg1 == 1`: invokes the HSMI/CMOS RTC wake path and reports success only if CMOS index `0x61` reads zero; `Arg1 == 2` returns a fixed text token `0x00013100`, whose product meaning has not been proven.
- `WM01` also includes **unsafe/mutating BIOS-maintenance commands** (load BIOS defaults `0x02`, secure-boot key operations `0x05/0x06`, test and boot-order settings). These must **not** be surfaced as ordinary user controls or probed for capability detection.

The WMI GUIDs show **OS discoverability in the factory AML**, not proven Windows/Linux API access, input validity, hardware wake behavior, or safe caller-side validation. Code must not use write commands as discovery probes. The installed 2024-06-04 `HQNVS000` AML and retained 2024-04-07 counterpart are byte-identical, so the three blocks and methods are stable across both imaged versions.

**Selected HQWI S5/RTC wake investigation (new fixed four-gate metric): 25% -> 50% (1/4 -> 2/4).** Known before this pass: SMI/EC wake-command transport. Newly closed: exact `_WDG` GUID/object IDs, string/method flags and ACPI WMI dispatch. Still UNKNOWN: accepted and safe wake argument encoding/domain, and actual OS-client/hardware wake acceptance on the target. This is not whole platform-power coverage.

Evidence: `corpus/acpi-2024-06-04/TM2309_2024-06-04_SSDT_HQNVS000.dsl` `_WDG`, `WM01`, `WMAB`, `HSMI`; byte-identical `corpus/acpi-2024-04-07/TM2309_2024-04-07_SSDT_HQNVS000.aml`. WMI block flags/naming spec: https://www.kernel.org/doc/html/v6.6/wmi/acpi-interface.html .
