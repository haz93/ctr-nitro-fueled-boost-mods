"""Check package integrity and source correspondence without game files.
SPDX-License-Identifier: GPL-2.0-or-later
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import math
import struct
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sha = lambda blob: hashlib.sha256(blob).hexdigest()


def verify(package, source, exact_manifest=True):
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None, 'ZIP CRC failure'
        names = archive.namelist()
        assert len(names) == len(set(names)), 'Duplicate ZIP member'
        for name in names:
            path = PurePosixPath(name)
            assert not path.is_absolute() and '..' not in path.parts and '\\' not in name and ':' not in name
        payloads = {name: archive.read(name) for name in names}
    manifest = json.loads(payloads['mod.json'])
    assert manifest['schemaVersion'] == 2
    assert manifest['compatibility']['online'] == 'offline-only'
    assert payloads['octr-mod.required'] == b'OCTR Mod Package 2\n'
    inventory = manifest['files']
    assert len(inventory) == len({item['file'] for item in inventory})
    assert {item['file'] for item in inventory} == set(payloads) - {'mod.json'}
    for item in inventory:
        content = payloads[item['file']]
        assert sha(content) == item['sha256'] and len(content) == item['bytes']
    originals = {p.relative_to(source).as_posix(): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    assert set(originals) == set(payloads)
    for name, content in payloads.items():
        if name == 'mod.json' and not exact_manifest:
            a, b = json.loads(content), json.loads(originals[name])
            a.pop('files'); b.pop('files')
            assert a == b
        else:
            assert originals[name] == content, f'Source differs: {name}'
    if manifest['id'] == 'brake-with-reserves-eu':
        assert manifest['version'] == '0.2.0' and not manifest['operations']
        assert set(manifest['requiresCapabilities']) == {'xml-patches', 'code-signatures'}
        xml = ET.fromstring(payloads[manifest['patches'][0]])
        lines = xml.findall('.//Line')
        assert xml.findtext('.//ID') == 'CUSA14876' and len(lines) == 1
        line = lines[0].attrib
        assert int(line['Address'], 16) == 0x122f213 and line['Value'] == 'eb'
        assert line['ExpectedSHA256'] == sha(b'\x74')
        signature = bytes.fromhex(line['Signature'])
        assert len(signature) == 28 and signature[int(line['SignatureOffset'], 0)] == 0x74
    elif manifest['id'] == 'triple-drift-reserves-eu':
        assert manifest['version'] == '0.1.0' and not manifest['patches']
        assert manifest['requiresCapabilities'] == ['archive-assets']
        assert {op['archive'] for op in manifest['operations']} == {'permanent.pak', 'update.pak', 'update2.pak'}
        count = 0
        for op in manifest['operations']:
            assert op['kind'] == 'archive_asset' and op['asset'].lower() == 'loosedata/drivingarchetypes.igz'
            assert len(op['runs']) == (38 if op['archive'] == 'update2.pak' else 32)
            offsets = set()
            for offset, old, new in op['runs']:
                assert offset >= 0 and offset % 4 == 0 and offset not in offsets
                offsets.add(offset)
                assert len(bytes.fromhex(old)) == len(bytes.fromhex(new)) == 4
                a = struct.unpack('<f', bytes.fromhex(old))[0]
                b = struct.unpack('<f', bytes.fromhex(new))[0]
                assert math.isfinite(a) and math.isfinite(b) and b > a > 0
                count += 1
        assert count == 102
    else:
        raise AssertionError('Unexpected package')
    return manifest['id']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT / 'releases')
    parser.add_argument('--rebuilt', action='store_true', help='Allow regenerated manifest inventory formatting/order')
    args = parser.parse_args()
    checksums = {}
    if not args.rebuilt:
        for line in (args.directory / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            checksums[name] = digest
    packages = sorted(args.directory.glob('*.zip'))
    assert len(packages) == 2
    for package in packages:
        if checksums:
            assert sha(package.read_bytes()) == checksums[package.name], 'Release checksum mismatch'
        with zipfile.ZipFile(package) as archive:
            identity = json.loads(archive.read('mod.json'))['id']
        verify(package, ROOT / 'mods' / identity, exact_manifest=not args.rebuilt)
        print(f'PASS: {package.name}')
