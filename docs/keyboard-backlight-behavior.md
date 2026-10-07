# TM2309 keyboard-backlight behavior contract

## Scope

Target: Xiaomi Redmi Book Pro 16 2024, board TM2309.

Primary static evidence comes from the installed firmware release dated 2024-06-04. Same-model runtime evidence from the byte-equivalent control route confirms the user-facing states.

## EC state

Evidence state: **CONFIRMED**.

The DSDT exposes two fields in the embedded-controller shared-memory window:

```text
KBLL  7 bits
KBMD  1 bit
```

They occupy the byte at EC shared-memory offset `0xB2`.

Only the four observed `KBLL` values below currently have recovered semantics.

`KBMD` has a **CONFIRMED** boot-time policy contract with a specific polarity:

- The target HII policy field is `SystemConfig+0x102`, not the previously reported local-stack offset `+0x42` (**WITHDRAWN**).
- Setup value `0 = Standard` sets EC `KBMD=1`; Setup value `1 = Power Saving` sets EC `KBMD=0` through `HQDxeService` selector 4.
- The EC bit resides at shared-memory byte `0xB2`, bit 7, independent of `KBLL` at bits 0..6.
- The mapping is **CONFIRMED static target evidence**; the actual timeout/physical behavior for each setting still needs execution proof on the laptop. The older interpretation of the two labels as an unbound `Always on / Power Saving` question is **WITHDRAWN** for this field.

Canonical state enum:

```text
EC_KEYBOARD_BACKLIGHT_OFF              = 1
EC_KEYBOARD_BACKLIGHT_DIM_AUTO_OFF     = 2
EC_KEYBOARD_BACKLIGHT_BRIGHT_AUTO_OFF  = 4
EC_KEYBOARD_BACKLIGHT_BRIGHT_ALWAYS_ON = 8
```

These names combine the target AML mapping with same-model runtime observations of the F10 cycle.

## Hotkey/event route

Evidence state: **CONFIRMED**.

The embedded controller query method `_Q10` emits:

```text
QV20(event_type = 1, event_id = 0x05)
```

The WMI event handler then reads `KBLL` and translates the raw EC state:

```text
KBLL = 1 -> event value 0x00
KBLL = 2 -> event value 0x05
KBLL = 4 -> event value 0x0A
KBLL = 8 -> event value 0x80
```

Same-model runtime testing maps those event values to:

```text
0x00 -> off
0x05 -> dim, BIOS idle timeout enabled
0x0A -> bright, BIOS idle timeout enabled
0x80 -> bright, always on
```

Thus the normal F10 cycle is a state/event path owned by the EC firmware.

## WMI control boundary

Evidence state: **CONFIRMED unsupported** for the generic setter.

The TM2309 `WMAA` implementation has target-specific branches for functions `0x08`, `0x0A`, and `0x10`. It does not implement the generic MIFS RGB/keyboard-brightness function `0x12`.

Requests using generic function `0x12` therefore fall through to firmware error `0xE000`.

A future manager must not expose a WMI keyboard-backlight setter merely because the generic Bitland MIFS interface defines one.

Direct writes to `KBLL` are not currently part of the supported control contract. The firmware exposes the state and hotkey transition, but a safe software setter has not yet been recovered.

## Validation boundary

- EC state mapping: **CONFIRMED**;
- hotkey/event mapping: **CONFIRMED**;
- same-model execution evidence: **CONFIRMED**;
- WMI setter function `0x12`: **CONFIRMED unsupported**;
- safe software write route: **UNKNOWN**;
- `KBMD` boot-time mode-bit contract and exact **Standard / Power Saving storage polarity: CONFIRMED**. Setup 0 Standard writes KBMD=1; Setup 1 Power Saving writes KBMD=0. Physical backlight timeout and relation to independent `KBLL=8` Always on state remain UNKNOWN.
