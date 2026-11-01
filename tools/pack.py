"""Rebuild installable packages without needing the port or game.
SPDX-License-Identifier: GPL-2.0-or-later
"""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(source, destination):
    manifest = json.loads((source / 'mod.json').read_text(encoding='utf-8'))
    payloads = {path.relative_to(source).as_posix(): path.read_bytes()
                for path in sorted(source.rglob('*')) if path.is_file() and path.name != 'mod.json'}
    if payloads.get('octr-mod.required') != b'OCTR Mod Package 2\n':
        raise ValueError('Missing schema-version-2 package marker')
    manifest['files'] = [{'file': name, 'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)}
                         for name, content in sorted(payloads.items())]
    payloads['mod.json'] = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / f"{manifest['id']}-{manifest['version']}.zip"
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(payloads.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build')
    args = parser.parse_args()
    for source in sorted((ROOT / 'mods').iterdir()):
        if (source / 'mod.json').is_file():
            output = build(source, args.output)
            print(f'{output.name}: {hashlib.sha256(output.read_bytes()).hexdigest()}')
