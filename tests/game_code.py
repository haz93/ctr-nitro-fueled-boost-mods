"""Load read-only code bytes from an owner's prepared ELF for isolated tests.
SPDX-License-Identifier: GPL-2.0-or-later
"""
from pathlib import Path
import argparse
import struct

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'work'
HERE.mkdir(exist_ok=True)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--elf', type=Path, required=True, help='Unpatched prepared eboot.elf from your own game')
parser.add_argument('--fixtures', type=Path, default=HERE / 'triple-drift-fixtures.json')
args = parser.parse_args()
FIXTURES = args.fixtures
ELF = args.elf.read_bytes()
if ELF[:6] != b'\x7fELF\x02\x01':
    raise ValueError('Expected a prepared ELF64 little-endian file, not a SELF container')
phoff = struct.unpack_from('<Q', ELF, 0x20)[0]
phentsize, phnum = struct.unpack_from('<HH', ELF, 0x36)
if phentsize < 56 or phoff + phnum * phentsize > len(ELF):
    raise ValueError('Invalid ELF program header table')
LOADS = []
for index in range(phnum):
    kind, flags, offset, vaddr, paddr, filesz, memsz, align = struct.unpack_from('<II6Q', ELF, phoff + index * phentsize)
    if kind in (1, 0x61000010):
        if offset + filesz > len(ELF):
            raise ValueError('Truncated ELF load segment')
        LOADS.append((offset, vaddr, filesz))


def data(addr, size):
    for offset, vaddr, filesz in LOADS:
        if vaddr <= addr and addr + size <= vaddr + filesz:
            return ELF[offset + addr - vaddr:offset + addr - vaddr + size]
    raise ValueError(f'Unmapped ELF range: {addr:#x}+{size:#x}')


signature = bytes.fromhex('48 85 db 74 13 80 bb 14 02 00 00 00 74 0a 80 7b 35 00 0f 85 d1 00 00 00 49 8b 47 68')
if data(0xe2f207, len(signature)) != signature:
    raise ValueError('Unsupported or already patched executable; expected EU 01.21 boost code')
