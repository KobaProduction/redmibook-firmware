# TM2309 microphone-mute indicator control contract

## Scope

Target: Xiaomi Redmi Book Pro 16 2024, board TM2309.

Primary static evidence comes from the installed firmware release dated 2024-06-04. Same-model Linux testing independently confirms that the multiplexed MIFS control device owns the microphone-mute indicator route.

## Control route

Evidence state: **CONFIRMED**.

The control interface is the same MIFS WMI method used by the performance-mode route:

- WMI control GUID: `B60BFB48-3E5B-49E4-A0E9-8CFFE1B3434B`
- method: `\_SB.PC00.WMID.WMAA`
- operation GET: `0xFA`
- operation SET: `0xFB`

For the microphone-mute indicator route the firmware uses:

```text
function    = 0x0A
subcommand  = 0x05
```

Canonical target-specific names:

```text
TM2309_MIFS_FUNCTION_INDICATOR_CONTROL = 0x0A
TM2309_INDICATOR_MIC_MUTE              = 0x05
```

The broader semantics of other function-0x0A subcommands remain **UNKNOWN**.

## EC state

Evidence state: **CONFIRMED**.

The firmware field is `MIUT`.

`FUNR(0x20)` returns `MIUT`.

The WMI-facing logical state is inverted relative to the raw EC field:

```text
GET:
  MIUT == 1 -> logical result 0
  MIUT != 1 -> logical result 1

SET:
  logical argument 1 -> MIUT = 0
  other argument     -> MIUT = 1
```

Canonical logical values:

```text
MIC_MUTE_INDICATOR_DEASSERTED = 0
MIC_MUTE_INDICATOR_ASSERTED   = 1
```

Canonical raw-storage relation:

```text
logical_state = !MIUT
```

The terms `ASSERTED/DEASSERTED` are intentional. Static firmware plus current external evidence prove the microphone-mute indicator route and the inversion, but do not yet prove a board-level electrical interpretation of raw MIUT as LED voltage/polarity.

## Event synchronization

Evidence state: **CONFIRMED**.

After a SET, firmware waits 150 ms and emits WMI event type 1 / event ID `0x21`.

The event handler reads `MIUT` directly and exposes the same logical inversion:

```text
MIUT == 1 -> event value 0
MIUT != 1 -> event value 1
```

This explains why a software indicator write produces the same WMI event stream as the physical microphone-mute key: both routes converge on the same EC state.

Same-model Linux work confirms that one driver must coordinate both the control GUID and event GUID because a microphone-mute indicator write reflects back as the same WMI event as a physical key press.

## Validation boundary

- static firmware behavior contract: **CONFIRMED**;
- same-model external execution evidence for microphone-mute indicator ownership/event reflection: **CONFIRMED**;
- execution proof on this specific laptop: not yet collected;
- raw board-level LED electrical polarity: **UNKNOWN**;
- future manager integration proof: not yet collected.
