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
