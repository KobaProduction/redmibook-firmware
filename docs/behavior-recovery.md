# Firmware behavior recovery

This document records recovered behavior contracts with explicit evidence state. Raw GUIDs, addresses and numeric values are evidence identities, not semantic names.


## TM2309 fan / performance profile control

### Canonical EC state

**CONFIRMED — static firmware evidence**

The platform fan/performance profile is stored in the Embedded Controller field `QFAN`.

- ACPI device: `\\_SB.PC00.LPCB.Q_EC` (`PNP0C09`)
- EC operation region: `ERAM`, SystemMemory `0xFE0B0300`, length `0x100`
- field: `QFAN`, byte offset `0x60` in ERAM
- effective address: `0xFE0B0360`

Do not use the address as the semantic name; the canonical semantic object is **EC performance/fan profile state (`QFAN`)**.

### MIFS WMI control route

**CONFIRMED — static firmware evidence**

WMI device `\\_SB.PC00.WMID` has UID `MIFS`.

Control interface:

- GUID: `B60BFB48-3E5B-49E4-A0E9-8CFFE1B3434B`
- WMI object ID: `AA`
- ACPI method: `WMAA`
- input/output packet size: 32 bytes

Canonical protocol fields:

- operation byte 1: `MIFS_OPERATION_GET = 0xFA`
- operation byte 1: `MIFS_OPERATION_SET = 0xFB`
- function byte 3: `MIFS_FUNCTION_PLATFORM_PROFILE = 0x08`
- success status byte 1 in output: `0x80`

AML word views appear as `0xFA00`, `0xFB00`, and `0x0800` because the fields are little-endian word overlays.

For platform-profile GET, firmware reads `QFAN` and only returns values 1, 2, 3 or 4; other values are normalized to 0.

For platform-profile SET, ordinary values are written directly to `QFAN`. Values 5 and 7 take a separate `SMMD` route and must not be merged semantically with ordinary QFAN profile values without further evidence.

Event interface:

- GUID: `46C93E13-EE9B-4262-8488-563BCA757FEF`
- WMI notify ID: `0x20`

### Profile values

**CONFIRMED — firmware contract plus runtime evidence on TM2309**

| QFAN value | Semantic profile |
| --- | --- |
| 0 | balanced-compatible state; GET normalizes it to 0/unknown |
| 1 | balanced |
| 2 | quiet / low-power |
| 3 | performance / Turbo |
| 4 | full-speed / Geek |

The EC/firmware path itself proves the accepted values and notifications. Runtime testing on TM2309 independently confirms the profile meanings and readback behavior.

### Notifications

**CONFIRMED — static firmware evidence**

`NTDP(profile)` maps profile changes into `ODV1` and sends device-specific notification `0x88` to `IETM`.

Observed mapping:

- `QFAN=2` -> `ODV1=2`
- `QFAN=3` -> `ODV1=1`
- `QFAN=4` -> `ODV1=4`
- other values, including balanced 0/1 -> `ODV1=0`

EC query handlers `_Q24` and `_Q30` also propagate current `QFAN` through `NTDP`.

### Huaqin WMI route

**CONFIRMED — static firmware evidence**

A second WMI device, `\\_SB.HQWI`, exposes a generic Huaqin command path. In method `WM01`, command `0x09` is explicitly the **Set performance mode** action:

1. convert the caller's payload to an integer;
2. write it directly to `QFAN`;
3. wait 5 ms;
4. read `QFAN` back;
5. call `NTDP` with the resulting profile.

This independently confirms `QFAN` as the platform's canonical performance/fan profile state.

### Stability across firmware releases

**CONFIRMED — static comparison**

The MIFS SSDT (`XMCC1806`) and Huaqin SSDT (`HQNVS000`) are byte-identical between the 2024-04-07 and 2024-06-04 official firmware releases. Therefore the WMI→EC profile contract described above is unchanged across those two releases.

### Setup UI relationship

**PARTIALLY CONFIRMED**

`H2ODisplayEngineLocalMetroDxe` contains the OEM fan UI and runtime controls such as `TurboMode`, CPU/GPU fan RPM fields and temperature fields. Its consumer-side behavior includes calls into OEM protocol GUID `754F7701-3C51-4F73-8FEF-314FDFA6DC5B`.

The UI code proves how values would be displayed and synchronized, but it does **not yet prove** that this protocol is the same path as MIFS `QFAN`. `OemODMDxeDriver` installs one interface under that GUID, but several relevant slots in that implementation return `EFI_UNSUPPORTED`. Until the actual runtime provider/variant is resolved, do not merge the H2O TurboMode boolean with the WMI/EC QFAN profile contract.


### Native DXE profile application

**CONFIRMED — static firmware evidence**

The DXE driver `HQDxeService` is a native producer of the same EC performance/fan profile state.

Identity:

- FFS GUID: `EA8D05BC-E348-4B75-BF6B-92E6B1E98068`
- FFS type: DXE driver
- UI name: `HQDxeService`
- version: `1.00`

The module reads a 0x4B0-byte UEFI configuration variable named `Setup` using GUID
`A04A27F4-DF00-4D42-B552-39511302113D` and applies several configuration fields directly to the EC operation region.

Its selector-dispatch action uses selector `5` for the performance/fan profile. Corrected structure typing proves that the input is Setup/SystemConfig byte `+0x103`, the visible **System Performance Mode** field. Earlier `+0x43` reporting was an RBP-relative local-stack coordinate and is **WITHDRAWN**, not a Setup offset.

| Setup/SystemConfig +0x103 | Setup label | Written QFAN profile |
| ---: | --- | ---: |
| 0 | Turbo Mode | 3 — performance / Turbo |
| 1 | Balance Mode | 1 — balanced |
| 2 | Silence Mode | 2 — quiet |
| 3 | Full Speed Mode | 1 at this boot-time HQDxeService normalization path; the native WMI bridge separately maps SystemConfig value 3 to external/QFAN value 4 |

The native WMI bridge remains the authoritative bidirectional mapping for the user-facing four-mode performance capability. This HQDxeService path is an early-boot synchronization path and must not be silently substituted for the runtime WMI mapping.

The relevant action runs during the `HQDxeService` DXE entrypoint initialization chain, immediately after service/protocol initialization. This establishes an early-boot Setup → EC profile synchronization path in addition to the runtime WMI paths.

### Release stability of native profile application

**CONFIRMED — static comparison**

The complete `HQDxeService` PE image is byte-identical between the official 2024-04-07 and 2024-06-04 firmware releases (same SHA-256:
`0FA91B79DD98D6629BB3ABF4386D90B3173357CE1566163BD3AE3141501E779E`).

Therefore the native Setup → QFAN mapping above did not change between these releases.


### HQDxeService Setup → EC selector map

**CONFIRMED — corrected static target evidence**

The entrypoint reads the persisted 0x4B0-byte Setup configuration into a local buffer and applies six fields to EC state through one selector-dispatch action. Earlier reports that named Setup offsets `+0x29/+0x2A/+0x33/+0x34/+0x42/+0x43` are **WITHDRAWN**: those values were local RBP-relative stack coordinates. Structure typing and the independent H2O Setup UI route establish the real Setup offsets below.

| Native selector | Setup/SystemConfig offset | EC target | Recovered semantic contract |
| --- | ---: | --- | --- |
| 1 | `+0xF3` | `AOUF`, EC byte `0x18` bits 0..1 | USB Charge mode: 0 Off, 1 Always on, 2 One time only. |
| 2 | `+0xF4` | `UCBT`, EC byte `0xAC` | USB Charge Battery Threshold: 10/20/30 percent. |
| 3 | `+0xE9` | `IKBW`, EC byte `0x18` bit 5 | Internal-keyboard wake enable. |
| 4 | `+0x102` | `KBMD`, EC byte `0xB2` bit 7 | Keyboard-backlight policy: 0 Standard, 1 Power Saving. This is distinct from live backlight level field `KBLL`. |
| 5 | `+0x103` | `QFAN`, EC byte `0x60` | Boot-time performance/fan profile synchronization. |
| 6 | `+0xEA` | `WOUB`, EC byte `0x18` bit 6 | Wake-on-USB enable. ACPI deep-standby logic disables XHCI PME when `WOUB == 0`. |

The action preserves unrelated bits when writing packed EC bytes. Selector 1 replaces only the low two `AOUF` bits; selectors 3 and 6 toggle only their individual bits.

This selector map is byte-identical in the 2024-04-07 and 2024-06-04 releases because the complete `HQDxeService` PE is identical.

### Persisted fine fan-policy fields

**CONFIRMED semantics; hardware apply route not yet proven**

The H2O Setup UI and typed `TM2309_PlatformControlSetup` structure close four additional persisted fan-policy fields:

| Setup/SystemConfig offset | Canonical semantic field | User values |
| ---: | --- | --- |
| `+0xF5` | CPU Auto Mode fan preset | 0 Gaming, 1 Normal, 2 Office |
| `+0xF6` | GPU Auto Mode fan preset | 0 Gaming, 1 Normal, 2 Office |
| `+0xF7` | CPU FAN Turbo Mode Speed | 0 Max, 1 Medium; raw value 2 is a platform-compatibility alias for Medium on one variant |
| `+0xF8` | GPU FAN Turbo Mode Speed | 0 Max, 1 Medium; raw value 2 is a platform-compatibility alias for Medium on one variant |

The BIOS UI change path persists these fields, reloads/normalizes the Setup model and refreshes UI/telemetry state. No direct EC write or OEM hardware-control apply call is present in that immediate route. Therefore these are **persisted firmware-policy capabilities**, not proven live controls. RedmiBook Manager must not promise immediate effect until a separate apply route receives execution/static proof.
