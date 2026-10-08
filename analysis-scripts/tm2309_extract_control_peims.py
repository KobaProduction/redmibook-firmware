from pathlib import Path
import hashlib,struct,uuid
src=Path("corpus/TM2309_0A0A_MS_firmware_raw.bin")
raw=src.read_bytes()
assert hashlib.sha256(raw).hexdigest()=="b04f0d9954aa6d8589d814bf8c26bd69d73afb570aa8bd9c1aad1ff9b6906c23"
out=Path("corpus/peim-controls-primary-a0a")
out.mkdir(exist_ok=True)
targets={"PlatformInitPreMem":0xd3a8d8, "SiliconPolicyPeiPreMem":0xd45c58,
         "PlatformInitPostMem":0xb45858, "SiliconPolicyPeiPostMem":0xb515d8,
         "PlatformInitAdvancedPreMem":0xd4d2d8}
for name,at in targets.items():
    fsize=int.from_bytes(raw[at+20:at+23],"little")
    assert 24 <= fsize < 0x200000, (name,fsize)
    guid=str(uuid.UUID(bytes_le=raw[at:at+16]))
    p=at+24
    while p+4<=at+fsize:
        length=int.from_bytes(raw[p:p+3],"little")
        typ=raw[p+3]
        h=4
        if length==0xffffff:
            length=int.from_bytes(raw[p+4:p+8],"little");h=8
        assert h<=length<=at+fsize-p,(name,p,length)
        if typ==0x10:
            b=raw[p+h:p+length]
            assert b[:2]==b"MZ",(name,b[:2])
            path=out/(name+".efi")
            path.write_bytes(b)
            pe_off=struct.unpack_from("<I",b,0x3c)[0]
            print(name,"FFS",guid,"PE",len(b),"machine",hex(struct.unpack_from("<H",b,pe_off+4)[0]),"sha256",hashlib.sha256(b).hexdigest(),"file",path)
        p=(p+length+3)&~3
