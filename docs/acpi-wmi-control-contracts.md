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
| 0xF5 | 0x31 | fan-related Setup field, semantics not yet closed |
| 0xF6 | 0x32 | fan-related Setup field, semantics not yet closed |
| 0xF7 | 0x34 | fan-related Setup field, semantics not yet closed |
| 0xF8 | 0x35 | fan-related Setup field, semantics not yet closed |
| 0xF9 | 0x33 | fan-related Setup field, semantics not yet closed |

No value conversion occurs in this backup/restore module.

## Other confirmed Setup controls

### USB charging

**CONFIRMED HII semantics; hardware apply route still UNKNOWN**

`SystemConfig+0xF3`: USB Charge

- 0 = Off (default)
- 1 = Always on
- 2 = One time only

`SystemConfig+0xF4`: USB Charge Battery Threshold

- 10 = 10%
- 20 = 20%
- 30 = 30% (default)

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

### Keyboard backlight Setup mode

**CONFIRMED HII semantics**

`SystemConfig+0x102`:

- 0 = Standard
- 1 = Power Saving (default)

A direct mapping from this Setup field to EC `KBLL` has not been established.

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
