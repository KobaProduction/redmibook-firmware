# TM2309 performance-mode control contract

This document records recovered behavior for the Xiaomi Redmi Book Pro 16 2024 (board TM2309).

## Evidence scope

Primary static target evidence:

- installed firmware release dated 2024-06-04, vendor BIOS ID `RMAMT6B0P0A0A`;
- its embedded DSDT;
- OEM SSDT `XMCC1806` containing the WMI method `WMAA`;
- OEM SSDT `HQNVS000` containing a second performance-mode command path.

Runtime corroboration exists from the same TM2309 model on the byte-equivalent 2025 control route. Runtime proof has not yet been collected from this specific laptop.

## MIFS WMI control interface

Evidence state: **CONFIRMED**.

The firmware exposes a `PNP0C14` WMI device at `\_SB.PC00.WMID` with UID `MIFS`.

The control GUID is:

`B60BFB48-3E5B-49E4-A0E9-8CFFE1B3434B`

The corresponding ACPI control method is:

`\_SB.PC00.WMID.WMAA`

The 32-byte input buffer layout recovered from AML matches the MIFS driver contract:

```text
offset  size  semantic name
0x00    u8    reserved_0
0x01    u8    operation
0x02    u8    reserved_1
0x03    u8    function
0x04    28    payload
```

Canonical operation enum:

```text
MIFS_OPERATION_GET = 0xFA
MIFS_OPERATION_SET = 0xFB
```

Canonical function relevant to this route:

```text
MIFS_FUNCTION_SYSTEM_PERFORMANCE_MODE = 0x08
```

The AML decompiler shows `0xFA00` / `0xFB00` and `0x0800` because it reads the adjacent reserved byte and operation/function byte as little-endian 16-bit fields. Those raw words are not separate command IDs.

## Performance-mode write route

Evidence state: **CONFIRMED**.

For a SET request of `MIFS_FUNCTION_SYSTEM_PERFORMANCE_MODE`, the normal branch:

1. clears the separate EC field `SMMD`;
2. writes the first mode byte to EC field `QFAN`;
3. emits the WMI event through `QV20`;
4. the DSDT method `NTDP` maps the applied value to `\_SB.ODV1`;
5. `NTDP` notifies `IETM` with device-specific notification `0x88`.

Two exceptional request values, raw values 5 and 7, use `SMMD` instead of the normal `QFAN` path. Their product semantics remain **UNKNOWN**.

## EC field

Evidence state: **CONFIRMED**.

`QFAN` is an 8-bit field in the embedded-controller operation region at field offset `0x60`.

Canonical semantic name:

`EC_PERFORMANCE_MODE`

Raw firmware name:

`QFAN`

The name is intentionally performance-mode oriented rather than fan-speed oriented: the same value also drives the DPTF policy selector through `NTDP`.

## Performance-mode values

The following names combine byte-identical target control logic with runtime evidence from the same TM2309 model.

```text
EC_PERFORMANCE_MODE_POLICY_BALANCED_ZERO = 0
EC_PERFORMANCE_MODE_BALANCED             = 1
EC_PERFORMANCE_MODE_QUIET                = 2
EC_PERFORMANCE_MODE_TURBO                = 3
EC_PERFORMANCE_MODE_FULL_SPEED           = 4
```

Evidence states:

- value 0 — **CONFIRMED** to map through `NTDP` to DPTF selector 0; runtime evidence shows substantially different cooling from value 1, so it must not be merged semantically with value 1 merely because both select the balanced DPTF policy;
- value 1 — **CONFIRMED** balanced mode selected by the machine's Fn+K cycle;
- value 2 — **CONFIRMED** quiet mode;
- value 3 — **CONFIRMED** performance/Turbo mode;
- value 4 — **CONFIRMED** full-speed/Geek mode.

Fn+K runtime behavior on TM2309 cycles the user-facing modes 1 -> 3 -> 2. Value 4 is accepted by firmware but is not part of that normal Fn+K cycle.

## DPTF mapping

Evidence state: **CONFIRMED** from the installed target DSDT.

`NTDP(mode)` writes the following DPTF selector values:

```text
mode 3 -> ODV1 = 1
mode 2 -> ODV1 = 2
mode 4 -> ODV1 = 4
mode 5 -> ODV1 = 5
mode 6 -> ODV1 = 6
other  -> ODV1 = 0
```

For the normal performance-mode enum this means:

```text
BALANCED / POLICY_BALANCED_ZERO -> DPTF policy 0
QUIET                           -> DPTF policy 2
TURBO                           -> DPTF policy 1
FULL_SPEED                      -> DPTF policy 4
```

## Secondary OEM command path

Evidence state: **CONFIRMED**.

The `HQNVS000` SSDT exposes method `WM01`. Command selector `0x09` converts its argument to an integer and writes it directly to `QFAN`, then calls `NTDP` with the value read back from `QFAN`.

The firmware returns the literal status string `Set performance mode Success!`.

This is a second firmware-visible route to the same canonical semantic object `EC_PERFORMANCE_MODE`; it is not a separate mode enum.

## Event synchronization

Evidence state: **CONFIRMED**.

The MIFS event GUID is:

`46C93E13-EE9B-4262-8488-563BCA757FEF`

For event ID `0x16`, the `EV20` handler reads the platform mode through EC function `FUNR(0x16)`. For values 1, 2, 3 and 4 it mirrors that value into `QFAN`, returns it in the event buffer and calls `NTDP`.

Thus hotkey-originated mode changes and software-originated mode changes converge on the same EC/DPTF state.

## Validation boundary

Current level:

- implementation proof: **CONFIRMED** for the firmware control contract;
- execution proof: available from external runtime testing on the same TM2309 model and byte-identical control route;
- execution proof on this specific laptop: **not yet collected**;
- board/integration proof for a future manager implementation: **not yet collected**.
