from __future__ import annotations
"""Primary A0A PEI-side candidate screen for fan-policy Setup and EC transports.
Search is bounded to directly decoded PE32/TE sections; compressed FSP sections
that were already decoded in the canonical A0A corpus are included separately.
Counts are not hardware-write claims.
"""
import hashlib, struct, uuid
from pathlib import Path
from tm2309_corpus import guid
raw_path=Path("corpus/TM2309_0A0A_MS_firmware_raw.bin")
raw=raw_path.read_bytes()
expect="b04f0d9954aa6d8589d814bf8c26bd69d73afb570aa8bd9c1aad1ff9b6906c23"
assert hashlib.sha256(raw).hexdigest()==expect, "Must scan installed primary A0A"
setup=guid("A04A27F4-DF00-4D42-B552-39511302113D")
selectors=[0xF5,0xF6,0xF7,0xF8]
ec_direct={o:(0xFE0B0300+o).to_bytes(4,"little") for o in (0x17,0x18,0x60,0xAC,0xB2)}
record=[]
def scan(name,typ,body,source):
    hits={}
    if setup in body: hits["SetupGUID"]=body.count(setup)
    addresses={f"EC+{x:02X}":body.count(pattern) for x,pattern in ec_direct.items() if pattern in body}
    if addresses:hits["EC_immediates"]=addresses
    # exact 4-byte displacements, not proof of any Setup variable owner
    quartet={f"+{x:02X}":body.count(bytes((x,0,0,0))) for x in selectors}
    if all(quartet.values()):hits["quartet_literals"]=quartet
    if hits:record.append((name,typ,source,hits))
def find_fv_headers():
    off=0
    while (off:=raw.find(b'_FVH',off))!=-1:
        yield off
        off+=4
for signature in find_fv_headers():
    base=signature-0x28
    if base<0:continue
    length=int.from_bytes(raw[base+0x20:base+0x28],"little")
    header=int.from_bytes(raw[base+0x30:base+0x32],"little")
    if length<0x80 or base+length>len(raw) or not 0x38<=header<=0x2000:continue
    pos=(base+header+7)&~7
    while pos+24<base+length:
        if raw[pos:pos+16]==b"\xff"*16:pos+=8;continue
        size=int.from_bytes(raw[pos+20:pos+23],"little")
        type_=raw[pos+18]
        attr=raw[pos+19]
        fh=24
        if size==0xffffff and attr&1:
            size=int.from_bytes(raw[pos+24:pos+32],"little");fh=32
        if type_ not in range(1,15) and type_ not in (0xf0,0xf1):pos+=8;continue
        if not fh<=size<=base+length-pos:pos+=8;continue
        if type_ in (6,7,8,9):
            ui=""; sections=[]
            p=pos+fh
            while p+4<=pos+size:
                slen=int.from_bytes(raw[p:p+3],"little")
                styp=raw[p+3];sh=4
                if slen==0xffffff:
                    slen=int.from_bytes(raw[p+4:p+8],"little");sh=8
                if not sh<=slen<=pos+size-p:break
                if styp==0x15:ui=raw[p+sh:p+slen].decode("utf-16le","replace").split("\x00")[0]
                if styp in (0x10,0x12):sections.append((styp,raw[p+sh:p+slen]))
                p=(p+slen+3)&~3
            for t,data in sections:scan(ui or str(uuid.UUID(bytes_le=raw[pos:pos+16])),hex(t),data,hex(pos))
        pos=(pos+size+7)&~7
root=Path("corpus/TM2309_A0A_PEIM_COMPRESSED_FV_E86B60.bin.dump")
for path in root.rglob("body.bin"):
    if "PE32 image section" in str(path) or "TE image section" in str(path):
        owner=next((part.split(" ",1)[1] for part in path.parts if part[:1].isdigit() and " " in part and "section" not in part),"?")
        scan(owner,"decompressed",path.read_bytes(),str(path))
print("CANDIDATE_IMAGE_COUNT",len(record))
for row in record:print("HIT",row)
print("SCOPE: exact GUID/immediates only, no indirect writes/EC proof")
