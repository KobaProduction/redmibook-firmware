# Cooling telemetry and fan-state contracts

Target: Xiaomi Redmi Book Pro 16 2024 / TM2309.

This document records only behavior supported by target firmware evidence. Raw ACPI/EC identifiers are evidence identities, not semantic names.

## Manager-facing status

### CPU fan speed

**CONFIRMED — static firmware contract**

The platform exposes a thermal telemetry descriptor named **CPU Fan #1 Speed** with unit **RPM**.

The descriptor is paired with the second element of the platform operating-state data returned through the Intel PTID thermal interface.

On TM2309, the base platform method fills that element from raw EC method ERCF.

Canonical semantic capability:

CpuFan1SpeedRpm

Evidence boundary:

- static firmware proves the source/value position and RPM unit;
- local execution proof on the target operating system is still pending;
- the exact implementation behind EC method ERCF is not present in the recovered static ACPI tables and remains UNKNOWN.

### CPU fan duty cycle

**CONFIRMED — static firmware contract**

The first operating-state element is described as **CPU Fan Duty Cycle**, unit **RAW**.

The base platform method fills it from raw EC method ERPN.

Canonical semantic capability at current evidence strength:

CpuFanDutyRaw

Do not convert it to percent until the value range/scaling is proven by runtime evidence or an authoritative producer.

### Skin temperature

**CONFIRMED — static route; raw scaling UNKNOWN**

In the extended operating-state variant, the third element is described as **Skin Temp 0**, unit **RAW**.

The value is taken from element 2 of the raw EC method ERSP result.

Canonical semantic capability at current evidence strength:

SkinTemperature0Raw

The physical conversion to degrees Celsius is not yet established.

## Intel PTID descriptor contract

The valid ACPI table with OEM TrmRef, table ID PtidDevc, publishes two operating-state descriptor sets.

The descriptors are ordered triplets of:

1. data type/width code;
2. human-readable sensor label;
3. unit label.

For the relevant operating-state sets the first entries are:

1. CPU Fan Duty Cycle — RAW
2. CPU Fan #1 Speed — RPM
3. Skin Temp 0 — RAW
4. Thermistor 1 — RAW
5. Thermistor 2 — RAW
6. Thermistor 3 — RAW
7. Thermistor 4 — RAW

The extended descriptor set additionally contains:

8. Thermistor 5 — RAW

The runtime value arrays use the same ordering.

The PTID wrapper selects the 7- or 8-value layout according to platform thermal-data mode and forwards the request to the TM2309 base platform methods.

## Base platform operating-state method

**CONFIRMED**

The TM2309 base method accepts two arguments: layout selector and destination value package.

When the extended layout is selected:

- index 0 = result of raw EC method ERPN;
- index 1 = result of raw EC method ERCF;
- index 2 = element 2 from raw EC method ERSP;
- remaining values are not populated by this base method and retain the caller's unavailable sentinel.

When the basic layout is selected:

- index 0 = ERPN;
- index 1 = ERCF;
- remaining values are not populated by this base method.

This closes the semantic mapping of the first two telemetry values without guessing the raw EC method names.

## Separate RPM data method

**PARTIALLY CONFIRMED**

A separate method named RPMD returns the result of raw EC method ERPC when the EC provider is present. Its fallback is a 26-byte buffer, and the paired write method accepts only a 26-byte buffer.

The name and surrounding PTID interface show that this route is RPM-related, but the layout of the 26-byte ERPC payload has not yet been recovered.

Do not treat ERPC as equivalent to CpuFan1SpeedRpm until its payload structure is proven.

## EC performance/fan-related bit fields

The directly mapped EC operation region ERAM is SystemMemory base 0xFE0B0300.

Structural parsing of its field definition confirms:

| Raw field | EC byte / bits | Width | Current semantic state |
| --- | --- | ---: | --- |
| FNSP | byte 0x17, bit 2 | 1 bit | UNKNOWN; returned by selector 0x17, but it is not a numeric fan-speed field |
| MIUT | byte 0x17, bit 4 | 1 bit | microphone-mute state/control route |
| FNRV | byte 0x17, bits 5..7 | 3 bits | UNKNOWN |
| AOUF | byte 0x18, bits 0..1 | 2 bits | LIKELY USB/always-on charging mode |
| QFAN | byte 0x60 | 8 bits | confirmed performance/fan profile state |
| ADPW | byte 0x81 | 8 bits | adapter/power-derived status |
| SOH1 | byte 0xAB | 8 bits | UNKNOWN status |
| KBLL | byte 0xB2, bits 0..6 | 7 bits | keyboard-backlight state |
| KBMD | byte 0xB2, bit 7 | 1 bit | keyboard-backlight mode |

FNSP must not be named or exposed as fan RPM: target evidence proves it is only one bit.

The same region contains twelve consecutive raw 8-bit sensor fields TSR0..TSRB at bytes 0x08..0x13. Their individual physical identities are not yet closed.

## Setup display relationship

The factory Setup UI contains fields for:

- CPU current fan speed;
- GPU current fan speed;
- CPU current temperature;
- GPU current temperature;
- system temperature.

It locates OEM protocol GUID 754F7701-3C51-4F73-8FEF-314FDFA6DC5B and attempts to obtain telemetry through one protocol slot.

However, the base provider OemODMDxeDriver installs EFI_UNSUPPORTED in that telemetry slot. No static evidence yet proves which runtime provider supplies the values on TM2309.

Therefore this Setup protocol is **not** yet a valid Manager telemetry backend.

Prefer the independently recovered PTID/ACPI telemetry contract above until the Setup-side provider is resolved.

## Next evidence boundaries

1. obtain execution proof for CPU fan RPM through the operating-system-visible PTID/ACPI route;
2. establish the numeric range/scaling of CPU fan duty cycle;
3. recover the 26-byte ERPC RPM payload;
4. map TSR0..TSRB and the raw thermal methods to physical sensors;
5. determine whether a second physical fan has a distinct operating-system-visible telemetry route.
