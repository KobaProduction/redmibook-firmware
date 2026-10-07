# TM2309 battery charge-limit control contract

## Scope

Target: Xiaomi Redmi Book Pro 16 2024, board TM2309.

Primary static evidence comes from the installed firmware release dated 2024-06-04. The relevant WMI/EC route is byte-identical in the later 2025 release used for same-model runtime validation.

## Important model-specific divergence

Evidence state: **CONFIRMED**.

On TM2309, MIFS function ID `0x10` is not safe to interpret using the generic Bitland RGB-keyboard mapping.

The target firmware implements function `0x10` as a multi-subcommand battery/power interface.

Canonical model-specific name:

`TM2309_MIFS_FUNCTION_BATTERY_CONTROL = 0x10`

Do not alias this function to a keyboard-lighting API on TM2309.

## Additional battery/power telemetry subcommands

The same target-specific MIFS function `0x10` exposes two additional **read-only** subcommands around the charge-limit control.

### Subcommand 1: raw `SOH1`

Evidence state: **CONFIRMED** for transport and EC field identity; product-level meaning remains **UNKNOWN**.

```text
GET:
  function = 0x10
  subcommand = 1
  result = EC field SOH1
```

The DSDT places `SOH1` at EC window byte offset `0xAB`:

```text
SOH1 address = 0xFE0B0300 + 0xAB = 0xFE0B03AB
```

The field name strongly resembles “state of health”, but the target firmware does not provide enough semantic evidence to promote that expansion to a canonical name yet. Keep `SOH1` as the exact raw field identity.

No SET branch for subcommand 1 exists in the target `WMAA` method.

### Subcommand 3: `ADPW` threshold status

Evidence state: **CONFIRMED** for the comparison contract; physical-unit interpretation remains **UNKNOWN**.

```text
GET:
  function = 0x10
  subcommand = 3
  if ADPW >= 0x8C (140): result = 0
  if ADPW <  0x8C (140): result = 1
```

The DSDT places the full-byte field `ADPW` immediately after the packed `0x80` status byte, at EC byte offset `0x81`:

```text
ADPW address = 0xFE0B0300 + 0x81 = 0xFE0B0381
```

The firmware name suggests adapter-power telemetry and the threshold is decimal 140, but neither the unit nor the exact public meaning of the returned Boolean is proven by target evidence. Do not publish it as a “<140 W charger” flag until runtime or another authoritative target contract confirms the unit.

No SET branch for subcommand 3 exists.

## 80 percent charge protection

Evidence state: **CONFIRMED**.

Subcommand `2` of the TM2309 battery-control function reads and updates bit 0 of the EC byte whose firmware field name is `LONL`.

Canonical names:

```text
TM2309_BATTERY_CONTROL_CHARGE_LIMIT = 2
EC_BATTERY_CHARGE_LIMIT_80_ENABLE_BIT = 0
```

Request semantics recovered from `WMAA`:

```text
GET:
  function = 0x10
  subcommand = 2
  result = LONL bit 0

SET:
  function = 0x10
  subcommand = 2
  argument = 1 -> set LONL bit 0
  other argument -> clear LONL bit 0
```

Same-model runtime evidence identifies this bit as the 80% battery charge-protection toggle.

## EC storage

Evidence state: **CONFIRMED** for location; unknown bits remain unnamed.

The DSDT maps the embedded-controller shared-memory window as:

```text
ERAM physical base = 0xFE0B0300
ERAM size          = 0x100
LONL byte offset   = 0xA4
LONL address       = 0xFE0B03A4
```

Only bit 0 currently has a recovered semantic contract. The remaining bits in the `LONL` byte are **UNKNOWN** and must not inherit charge-limit names without evidence.

## Access contract

The firmware's normal WMI path accesses EC fields through serialized wrappers:

- `ECRD(field_ref)` — guarded read;
- `ECWT(value, field_ref)` — guarded write;
- both use mutex `ECMT`;
- writes are conditional on `ECAV`, which tracks EC availability.

A future manager should prefer the MIFS WMI control route over raw physical writes to `0xFE0B03A4`. The physical address is evidence/debug context, not the preferred public control API.

## Validation boundary

- static behavior/control contract: **CONFIRMED**;
- same-model external execution evidence: **CONFIRMED** for the 80% charge-protection meaning;
- execution proof on this specific laptop: not yet collected;
- manager integration proof: not yet collected.


## Same-model runtime validation details

Independent testing on the same TM2309 board with the later 1.11 firmware directly exercised the battery-control route.

The tester observed that using function 0x10 / subcommand 2 with a clearing value changed LONL from a protected state to an unprotected state and the EC charge limit changed from 80% to 100%; charging resumed immediately.

This independently validates the user-facing meaning of the recovered LONL bit on TM2309.

A significant compatibility hazard was also demonstrated: a generic third-party MIFS driver treated the same numeric function as a keyboard-mode command and accidentally disabled battery charge protection. Manager must therefore use the TM2309-specific semantic contract and capability table rather than generic Bitland/Xiaomi selector assumptions.

Published evidence:
- https://lkml.rescloud.iu.edu/2609.3/14028.html

## OemODMDxeDriver OEM battery advisory (2026-10-07)

**CONFIRMED static firmware behavior; the product meaning of its thresholds and OS reachability remain UNKNOWN.**

The June native DXE module `OemODMDxeDriver.efi`, which publishes OEM protocol GUID `754F7701-3C51-4F73-8FEF-314FDFA6DC5B`, registers a separate read-only diagnostic method `0x1BE0` at object slot `+0x48` (interface-relative `+0x20` when the interface base is at object `+0x28`). This is **not** the unsupported fan-variant method at interface-relative `+0x48`.

Machine instruction route `0x1BE0..0x1C4F`:

- reads `ERAM+0x80` (packed `ACIN/BTIN/BTST/FCST/PWRV` status), `ERAM+0x81` (`ADPW`) and `ERAM+0x92` (`RSOC`); these raw identities come independently from the installed ACPI DSDT field layout;
- obtains one OEM classifier through local helper `0x2D04(0x140C04, ...)`. When that classifier equals `3`, sets output byte `+0` according to unsigned `ADPW >= 0x85`; otherwise tests `ADPW >= 0x5F`. **Do not assign watts or a battery policy label to this raw threshold flag without further evidence**;
- writes `RSOC` to output byte `+5`;
- **only conditionally** writes output byte `+2` to `1` if `BTIN` (`ERAM+0x80 bit1`) is set, the preceding threshold flag is zero, and `RSOC <= 10`; otherwise that byte is not written in the shown routine. This is an OEM low-charge advisory condition candidate, not a verified standalone battery alarm API;
- returns zero/firmware success; it does not write an EC register or set the charge limit.

The routine adds a **native BIOS-side battery/adapter status producer** to the inventory. It is separate from the confirmed **OS-visible** MIFS battery charge-protection route. No Windows caller, supported user-mode path or real-machine validation is established for this OEM method; do not expose the derived thresholds as public controls or physical charger-power claims.

Evidence: retained `corpus/oem-protocol-candidates/OemODMDxeDriver.efi` instructions `0xA61..0xA68`, `0x1BE0..0x1C4F`; installed `corpus/acpi-2024-06-04/TM2309_2024-06-04_DSDT_INTEL_SKL.dsl`, `ERAM` field.

**Selected OEM battery diagnostic route (new scope): approximately 75% (3/4 evidence gates).** Closed: interface-method linkage, EC field meanings, and exact output-flag algorithm. Open: reliable OS access/target execution. This percentage is *not* global battery-feature progress and does not turn firmware-static analysis into hardware proof.
