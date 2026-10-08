"""Primary RedmiBook TM2309 A0A: two bounded reverse-route checks.
Nothing is written to BIOS/EC/MSR. Uses retained verified image bytes only.
"""
import hashlib
import struct
import uuid
from pathlib import Path
from tm2309_corpus import Module,ensure
RAW = Path("corpus/TM2309_0A0A_MS_firmware_raw.bin")
assert hashlib.sha256(RAW.read_bytes()).hexdigest() == "b04f0d9954aa6d8589d814bf8c26bd69d73afb570aa8bd9c1aad1ff9b6906c23"
prefix=Path("corpus/TM2309_A0A_PEIM_COMPRESSED_FV_E86B60.bin.dump")
def child(match,tag):
    paths=[p for p in prefix.rglob("body.bin") if match in str(p) and "PE32 image section" in str(p)]
    ensure(len(paths)==1,"one decoded "+tag+" module")
    return paths[0]
si=Module("SiInitFsp","",child("/4 SiInitFsp/","SiInitFsp").read_bytes())
fsp=Module("FspInit","",child("/5 FspInit/","FspInit").read_bytes())
pol=Module("SiliconPolicyPeiPreMem","",Path("corpus/peim-controls-primary-a0a/SiliconPolicyPeiPreMem.efi").read_bytes())
expected={"SiInitFsp":"723bd6eb40ccaec27942f531845cec20e6728a8aa0f16c7ecfe4859215abf82c",
          "FspInit":"0d18814ed27cc8c4189104bb36c0cea73204d312b158d00ab9412a9e6ad3b7a7",
          "SiliconPolicyPeiPreMem":"a59b77972f7e78d26b47449939a41dea2f09c65fbcdacf97e4e63e76890946b2"}
for m in (si,fsp,pol):ensure(m.sha256()==expected[m.name],m.name+" SHA-256 verified")
def check(m,rva,opcode,label):
    test=bytes.fromhex(opcode)
    ensure(m.at(rva,len(test))==test,label+" opcode "+hex(rva))
def find_guid(m,name,offset):
    ensure(m.at(offset,16)==uuid.UUID(name).bytes_le, m.name+" GUID "+name+" at "+hex(offset))
find_guid(si,"3996397f-19b8-4b3e-8cd3-5b37b21792fc",0x29eb4)
find_guid(fsp,"3996397f-19b8-4b3e-8cd3-5b37b21792fc",0x47b0)
check(si,0xaa3,"8d44241c","PEI gets address of power-policy HOB pointer slot")
check(si,0xaa8,"bab49e0200","PEI passes policy HOB GUID to lookup")
check(si,0xaad,"e844b70000","PEI resolves policy HOB pointer")
check(si,0xc4c,"8b4c241c","PEI passes same HOB policy pointer to HOB population")
check(si,0xc50,"e81eec0000","PEI executes CPU policy/HOB population path")
check(fsp,0x352b,"bab0470000","FspInit also looks up same policy GUID")
check(fsp,0x3533,"e887daffff","FspInit GUID record search helper")
check(fsp,0x3744,"8b742424","FspInit consumes looked-up pointer")
print("CPU_POLICY: CONFIRMED two PEI consumers of same GUID HOB, SiInitFsp uses that HOB as HOB/PL producer input; HOB original owner and user-Setup linkage remain UNKNOWN")
p_off=struct.unpack_from("<I",pol.pe,0x3c)[0]
base=struct.unpack_from("<I",pol.pe,p_off+24+28)[0]
ensure(base==0xffb64200,"PEI relocated code-base")
find_guid(pol,"a04a27f4-df00-4d42-b552-39511302113d",0x5e30)
find_guid(pol,"c56c73d0-1cdb-4c0c-a957-ea62a9e6f50c",0x5eb0)
check(pol,0xffb666dc-base,"8d45cc","PEI obtains separate policy block pointer destination")
check(pol,0xffb666df-base,"bab0a0b6ff","PEI resolves non-Setup GUID for policy block")
check(pol,0xffb666e7-base,"e8e8e1ffff","PEI configuration block search")
check(pol,0xffb6799f-base,"8b5dcc","PEI loads that block as EBX")
for va,rawop in [(0xffb68771,"8883f5000000"),(0xffb68799,"8893f6000000"),(0xffb687a2,"8883f7000000"),(0xffb687b0,"8883f8000000")]:
    check(pol,va-base,rawop,"PEI writes different policy block numeric field")
# The other PEI Setup-GUID carrier here is a GUID/size discriminator, not a fan writer.
pre=Module("PlatformInitPreMem","",Path("corpus/peim-controls-primary-a0a/PlatformInitPreMem.efi").read_bytes())
ensure(pre.sha256()=="0e784dde2402ba67d667b20607570cd70e03b635b3097e67532a2ead57ea2322","PlatformInitPreMem primary PE digest")
pe=struct.unpack_from("<I",pre.pe,0x3c)[0]
pb=struct.unpack_from("<I",pre.pe,pe+24+28)[0]
ensure(pb==0xffb58e60,"PlatformInitPreMem relocated PE base")
find_guid(pre,"a04a27f4-df00-4d42-b552-39511302113d",0x74e8)
check(pre,0xffb5a978-pb,"ba4803b6ff","PlatformInitPreMem Setup GUID comparison operand")
check(pre,0xffb5a97d-pb,"e84cf2ffff","PlatformInitPreMem GUID equality helper")
check(pre,0xffb5a986-pb,"b8b0040000","PlatformInitPreMem returns Setup size 0x4B0")
print("FAN_POLICY: PlatformInitPreMem Setup GUID mention is a GUID/VarStore-size discriminant, not a fan-field consumer")
print("FAN_POLICY: CONFIRMED misleading +F5..F8 quartet belongs to distinct C56C73D0 configuration block, not direct Setup/SystemConfig offset proof")
print("BOUNDARY: neither new hardware fan-setter nor CPU voltage/power OS setter is established")
