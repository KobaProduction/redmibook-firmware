"""Static acceptance for primary-A0A CPU-power PEI HOB producer and DXE/ACPI transfer.
Target instruction evidence only; no MSR execution or OS/hardware probing.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,struct,uuid
from tm2309_corpus import Module,by_name,extract_unique_pe,ensure

RAW=Path('corpus/TM2309_0A0A_MS_firmware_raw.bin')
RAW_SHA='b04f0d9954aa6d8589d814bf8c26bd69d73afb570aa8bd9c1aad1ff9b6906c23'
PE_SHA='723bd6eb40ccaec27942f531845cec20e6728a8aa0f16c7ecfe4859215abf82c'
GUID_POWER='266e31cc-13c5-4807-b9dc-39a6ba88ff1a'
GUID_STATUS='21ac65f8-96e5-43f4-a168-ef2c62e9764b'
ensure(hashlib.sha256(RAW.read_bytes()).hexdigest()==RAW_SHA,'installed A0A raw BIOS identity')
root=Path('corpus/TM2309_A0A_PEIM_COMPRESSED_FV_E86B60.bin.dump')
found=[p for p in root.rglob('body.bin') if 'SiInitFsp' in str(p) and 'PE32 image section' in str(p)]
ensure(len(found)==1,'single decompressed SiInitFsp PE32')
m=Module('SiInitFsp', '15c8dcef-e7d9-41e2-a89c-8d1c61f07e9c',found[0].read_bytes())
ensure(m.sha256()==PE_SHA,'SiInitFsp primary image digest')
pe=struct.unpack_from('<I',m.pe,0x3c)[0]
ensure(struct.unpack_from('<H',m.pe,pe+4)[0]==0x14c,'SiInitFsp is PEI IA32 image (not DXE x64)')
g1=uuid.UUID(GUID_POWER).bytes_le;g2=uuid.UUID(GUID_STATUS).bytes_le
ensure(m.find_rva(g1)==[0x29b64],'CPU power HOB GUID A literal')
ensure(m.find_rva(g2)==[0x29d34],'separate two-byte status HOB GUID B literal')
def check(mod,addr,hex_bytes,title):
    expected=bytes.fromhex(hex_bytes)
    ensure(mod.at(addr,len(expected))==expected,title)
check(m,0xf882,'bf00040000','SiInitFsp CPU power HOB payload length = 0x400')
check(m,0xf888,'68649b0200','SiInitFsp passes GUID A to HOB allocator')
check(m,0xf88d,'e818d9ffff','SiInitFsp BuildGuidHob call')
check(m,0xd1af,'6a04','BuildGuidHob specifies type GUID_EXTENSION 0x04')
check(m,0xd1b2,'8d5218','BuildGuidHob allocates payload size + 0x18 header')
check(m,0xf99e,'6a02','SiInitFsp separate GUID B HOB has 2-byte payload')
check(m,0xf9a0,'68349d0200','SiInitFsp status GUID B allocation')
check(m,0xfd75,'68649b0200','CPU power HOB producer reacquires GUID A')
check(m,0xfdf9,'83c62a','producer PL2 target HOB header + 0x2a')
check(m,0xfe1b,'668946fa','producer writes PL1 = HOB header + 0x24 = payload+0x0c')
check(m,0xfe25,'668906','producer writes PL2 = HOB header + 0x2a = payload+0x12')
check(m,0xfe1f,'668b07','producer loads 16-bit second source vector value')
check(m,0xfe2b,'83eb01','producer repeats three mode records')
check(m,0x10115,'b9ce000000','producer source selects MSR_PLATFORM_INFO 0xCE')
check(m,0x10138,'b948060000','producer source selects cTDP nominal MSR 0x648')
check(m,0x10141,'b914060000','producer source selects PKG_POWER_INFO MSR 0x614')
check(m,0x101d1,'b949060000','producer source selects cTDP level1 MSR 0x649')
check(m,0x10255,'b94a060000','producer source selects cTDP level2 MSR 0x64A')
check(m,0x102c5,'83c63c','board-config override records begin policy+0x3c')
check(m,0x102d6,'0fb74604','read optional 16-bit override value at +4 of record')
check(m,0x102f8,'0fb74606','read optional 16-bit override value at +6 of record')
check(m,0x10357,'83c608','board-config record stride = 8 bytes')
check(m,0xa947,'b906060000','power unit helper uses RAPL_POWER_UNIT MSR 0x606')
check(m,0x10cf2,'b910060000','boot power policy selects PKG_POWER_LIMIT MSR 0x610')
check(m,0x10cf7,'0f30','boot power policy actually issues WRMSR 0x610')
check(m,0x10d2b,'b910060000','later MSR 0x610 write intent')
check(m,0x10d30,'0f30','later boot power policy WRMSR instruction')
d=by_name(extract_unique_pe(),'DxeCpuPowerManagement')
check(d,0xb9c,'488d0dad170000','DXE searches GUID A first')
check(d,0xbbb,'488d7818','DXE obtains GUID A HOB payload at header+0x18')
check(d,0xbbf,'e8f80d0000','DXE second HOB search follows payload assignment')
check(d,0xe9b,'66890c02','DXE transfers PL1 values to NVS as 16-bit')
check(d,0xeb2,'66890c02','DXE transfers PL2 values to NVS as 16-bit')
check(d,0xec2,'41884c001c','DXE transfers first PLW window byte to NVS+0x1C')
print('CONFIRMED_STATIC: A0A PEI SiInitFsp -> GUID A 0x400B HOB -> three PL1/PL2/window rows -> DXE PNVS -> Intel DPTF PPCC')
print('UNPROVEN: individual board-config source ownership, exact active machine MSR values, CpuSetup-to-boot-policy coupling, OS control and hardware acceptance')
