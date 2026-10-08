from __future__ import annotations

import hashlib
import re
import struct
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

CORPUS = Path("corpus")
FV = CORPUS / "TM2309_0A0A_MS_GUIDED_EE4E5898-3914-4259-9D6E-DC7BD79403CF_decompressed.bin"
PRIMARY_FV_SHA256 = "7649b202fb354d87f1f2e4c69b072aac8bf2cf70a9416bce476d5710ebaae546"
DSDT = CORPUS / "acpi-2024-06-04/TM2309_2024-06-04_DSDT_INTEL_SKL.dsl"
HQNVS = CORPUS / "acpi-2024-06-04/TM2309_2024-06-04_SSDT_HQNVS000.dsl"
XMCC = CORPUS / "acpi-2024-06-04/TM2309_2024-06-04_SSDT_XMCC1806.dsl"

@dataclass(frozen=True)
class Module:
    name: str
    file_guid: str
    pe: bytes

    def sha256(self) -> str:
        return hashlib.sha256(self.pe).hexdigest()

    def sections(self) -> list[tuple[str, int, int, int]]:
        pe_off = struct.unpack_from("<I", self.pe, 0x3C)[0]
        assert self.pe[pe_off:pe_off + 4] == b"PE\x00\x00"
        count = struct.unpack_from("<H", self.pe, pe_off + 6)[0]
        optional_size = struct.unpack_from("<H", self.pe, pe_off + 20)[0]
        table = pe_off + 24 + optional_size
        out = []
        for idx in range(count):
            x = table + idx * 40
            name = self.pe[x:x + 8].split(b"\0")[0].decode("ascii", "replace")
            rva = struct.unpack_from("<I", self.pe, x + 12)[0]
            raw_len, raw_start = struct.unpack_from("<II", self.pe, x + 16)
            out.append((name, rva, raw_len, raw_start))
        return out

    def at(self, rva: int, length: int) -> bytes:
        for name, v, n, raw in self.sections():
            if v <= rva and rva + length <= v + n:
                return self.pe[raw + rva - v:raw + rva - v + length]
        raise ValueError(f"{self.name} RVA={rva:#x} length={length}")

    def find_rva(self, seq: bytes) -> list[int]:
        refs = []
        start = 0
        while True:
            i = self.pe.find(seq, start)
            if i < 0:
                break
            for name, v, length, raw in self.sections():
                if raw <= i < raw + length:
                    refs.append(v + i - raw)
            start = i + 1
        return refs

    def disasm(self) -> list[str]:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".efi") as temp:
            temp.write(self.pe)
            temp.flush()
            r = subprocess.run(
                ["objdump", "-d", "-M", "intel", temp.name],
                capture_output=True, text=True, timeout=24, check=False,
            )
            if r.returncode != 0 and not r.stdout:
                raise RuntimeError(r.stderr[:500])
            return r.stdout.splitlines()

    def disasm_window(self, start: int, stop: int) -> list[str]:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".efi") as temp:
            temp.write(self.pe)
            temp.flush()
            r = subprocess.run(
                ["objdump", "-d", "-M", "intel", f"--start-address={start}", f"--stop-address={stop}", temp.name],
                capture_output=True, text=True, timeout=15, check=False,
            )
            return [x for x in r.stdout.splitlines() if re.match(r"^\s*[0-9a-f]+:", x)]


def extract_unique_pe() -> list[Module]:
    raw = FV.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PRIMARY_FV_SHA256:
        raise ValueError(f"Only installed TM2309 A0A 2024-06-04 FV is permitted: {digest}")
    end = 0x80 + struct.unpack_from("<Q", raw, 0xA0)[0]
    pos = 0xC8
    modules: list[Module] = []
    seen: set[str] = set()
    while pos + 24 <= end:
        file_size = int.from_bytes(raw[pos + 20:pos + 23], "little")
        attributes = raw[pos + 19]
        head = 24
        if file_size == 0xFFFFFF and attributes & 1:
            file_size = struct.unpack_from("<Q", raw, pos + 24)[0]
            head = 32
        if not head <= file_size <= end - pos:
            break
        limit = pos + file_size
        section = pos + head
        name = ""
        pe: bytes | None = None
        while section + 4 <= limit:
            length = int.from_bytes(raw[section:section + 3], "little")
            kind = raw[section + 3]
            h = 4
            if length == 0xFFFFFF:
                length = struct.unpack_from("<I", raw, section + 4)[0]
                h = 8
            if not h <= length <= limit - section:
                break
            content = raw[section + h:section + length]
            if kind == 0x15:
                name = content.decode("utf-16le", "replace").split("\0")[0]
            if kind == 0x10 and content[:2] == b"MZ":
                pe = content
            section = (section + length + 3) & ~3
        if pe is not None:
            digest = hashlib.sha256(pe).hexdigest()
            if digest not in seen:
                seen.add(digest)
                modules.append(Module(name or "(unnamed)", str(uuid.UUID(bytes_le=raw[pos:pos + 16])), pe))
        pos = (limit + 7) & ~7
    return modules


def by_name(modules: list[Module], name: str) -> Module:
    hits = [m for m in modules if m.name == name]
    if len(hits) != 1:
        raise ValueError(f"{name}: expected 1 PE, found {len(hits)}")
    return hits[0]


def guid(value: str) -> bytes:
    return uuid.UUID(value).bytes_le


def ensure(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print("PASS", label)


def asm_lookups(module: Module, needle: str, around: int = 3) -> list[list[str]]:
    lines = module.disasm()
    positions = [i for i, line in enumerate(lines) if needle.lower() in line.lower()]
    return [lines[max(0, i - around): min(len(lines), i + around + 1)] for i in positions]


if __name__ == "__main__":
    modules = extract_unique_pe()
    print("UNIQUE_DIRECT_PE", len(modules))
    for n in ("ThermalSmm", "GpioV2ProtocolInitSmm", "GpioV2ProtocolInitDxeSoc", "AdvancedAcpiDxe", "OemODMDxeDriver"):
        m = by_name(modules, n)
        print(n, m.sha256(), len(m.pe), [(s[0], hex(s[1])) for s in m.sections()][:2])

