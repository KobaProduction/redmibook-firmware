# TM2309 A0A research scripts

Read-only, source-level reverse evidence for the installed June 2024 BIOS of Xiaomi Redmi Book Pro 16 2024 / TM2309. No firmware writes, EC writes, MSR operations, application code or flashable image are involved.

The repository deliberately excludes vendor binaries. Scripts expect the retained research workspace corpus tree. They verify the primary A0A raw BIOS SHA-256 B04F0D9954AA6D8589D814BF8C26BD69D73AFB570AA8BD9C1AAD1FF9B6906C23 and/or nested decompressed FV SHA-256 7649B202FB354D87F1F2E4C69B072AAC8BF2CF70A9416BCE476D5710EBAE546.

The nested FSP FV begins at raw-image offset 0xE86B60 and is 0x60000 bytes long. SiInitFsp and FspInit PE images are extracted from its UEFIExtract A75 dump tree. The scripts do not download or redistribute those bytes.

- tm2309_corpus.py: SHA-pinned image parser, section/RVA reader and assertions.
- tm2309_extract_control_peims.py: locally extracts five primary PEI image copies for analysis only.
- tm2309_cpu_power_source_trace_acceptance.py: exact HOB, MSR-read/programming and DXE copy static checks.
- tm2309_dual_route_deep_acceptance.py: CPU policy HOB pointer identity and fan-policy false-positive disambiguation.
- tm2309_pei_fan_route_census.py: bounded candidate discovery. Numeric-offset matches are NOT semantic proof.

Run these scripts from a directory containing the verified corpus/ tree. Python is required; objdump is used only for disassembly inspection. Static proof does not imply on-device execution, controller routing or safe user-mode control.
