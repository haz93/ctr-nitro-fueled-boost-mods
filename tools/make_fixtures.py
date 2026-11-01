"""Create private test fixtures from the owner's original EU 01.21 archives.
SPDX-License-Identifier: GPL-2.0-or-later
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'third_party' / 'octr'))
from mod_file_paths import configure
from archive_reader import Archive
from widescreen_startup import IGZ

PLAYER_ROOTS = ('DrivingArchetype_Advanced_driftData', 'DrivingArchetype_Beginner_driftData',
                'DrivingArchetype_IntermediateA_driftData', 'DrivingArchetype_IntermediateB_driftData',
                'DrivingArchetypes_AdvancedB_driftData')
TYPES = ('CKartBoostData', 'CKartBaseBoostData')
sha = lambda blob: hashlib.sha256(blob).hexdigest()
f32 = lambda value: struct.unpack('<f', struct.pack('<f', value))[0]


def generate(game, output):
    configure({})  # Always read original files, never the port's mod-file map.
    manifest = json.loads((ROOT / 'mods' / 'triple-drift-reserves-eu' / 'mod.json').read_text())
    fixtures, records = [], []
    for operation in manifest['operations']:
        archive = Archive(game / 'archives' / operation['archive'])
        try:
            entry = archive.files[operation['index']]
            assert entry['path'] == operation['asset'], 'Archive index/path mismatch'
            original = archive.extract(entry)
            assert sha(original) == operation['original_sha256'], 'Incompatible original resource'
            modified = bytearray(original)
            offsets = set()
            for offset, old, new in operation['runs']:
                assert original[offset:offset+4] == bytes.fromhex(old)
                modified[offset:offset+4] = bytes.fromhex(new)
                offsets.add(offset)
            assert sha(modified) == operation['patched_sha256']
            igz = IGZ(original)
            assert IGZ(bytes(modified)).objects == igz.objects
            selected = []
            for obj in igz.objects:
                name = obj.get('name', '')
                if obj['type'] not in TYPES or not any(name.startswith(root + '_') for root in PLAYER_ROOTS):
                    continue
                assert name.endswith(('_minBoost', '_maxBoost', '_normalDriftBoost', '_maxDriftBoost'))
                pos = obj['offset']
                assert pos + 0x20 in offsets
                ramp, sustain = struct.unpack_from('<2f', original, pos + 0x1c)
                replacement = struct.unpack_from('<f', modified, pos + 0x20)[0]
                assert replacement == f32(3 * sustain + 2 * ramp)
                size = 0x40 if obj['type'] == 'CKartBoostData' else 0x28
                old, new = original[pos:pos+size], bytes(modified[pos:pos+size])
                assert old[:0x20] == new[:0x20] and old[0x24:] == new[0x24:]
                assert math.isclose(ramp + replacement, 3 * (ramp + sustain), rel_tol=1e-6)
                fixtures.append({'archive': operation['archive'], 'name': name, 'type': obj['type'],
                                 'offset': pos, 'ramp': ramp, 'old_sustain': sustain, 'new_sustain': replacement,
                                 'old_award': f32(ramp+sustain), 'new_award': f32(ramp+replacement),
                                 'original_object_hex': old.hex(), 'modified_object_hex': new.hex()})
                selected.append(pos + 0x20)
            assert set(selected) == offsets and len(selected) == len(offsets)
            changed = {position for offset in offsets for position in range(offset, offset + 4)}
            assert all(a == b or pos in changed for pos, (a, b) in enumerate(zip(original, modified)))
            records.append({'archive': operation['archive'], 'modified_fields': len(selected),
                            'original_sha256': sha(original), 'patched_sha256': sha(modified),
                            'only_selected_sustain_fields_changed': True})
        finally:
            archive.data.close()
            archive._file.close()
    assert len(fixtures) == 102
    output.mkdir(parents=True, exist_ok=True)
    (output / 'triple-drift-fixtures.json').write_text(json.dumps(fixtures, indent=2) + '\n', encoding='utf-8')
    (output / 'asset-tests.json').write_text(json.dumps({'all_passed': True, 'fields': 102, 'assets': records}, indent=2) + '\n', encoding='utf-8')
    print('PASS: 102 sustain fields across three original-dependent resources; private fixtures written.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path, help='Original game directory containing archives/')
    parser.add_argument('--output', type=Path, default=ROOT / 'work')
    args = parser.parse_args()
    generate(args.game, args.output)
