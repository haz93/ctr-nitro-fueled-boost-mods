# Attribution and licensing

This project's original tools, documentation and patch definitions are offered under GNU GPL version 2 or, at your option, any later version. The full version 2 license text is in `LICENSE`.

## OCTR parsing helpers

`third_party/octr/archive_reader.py`, `mod_file_paths.py` and `widescreen_startup.py` are unmodified copies from the locally tested installation of [Ryu7w7/OCTR-NitroFueled-PC](https://github.com/Ryu7w7/OCTR-NitroFueled-PC). That project distributes its source under GPL-2.0-or-later. Existing author and license notices are retained. The exact upstream commit of this installed snapshot was not recorded; file hashes and original paths are recorded in `third_party/octr/PROVENANCE.json`.

The IGZ helper in `widescreen_startup.py` credits **tcosi**. The archive reader credits the PAK layout in [kishimisu/Crash-NST-Modding-Tool](https://github.com/kishimisu/Crash-NST-Modding-Tool). These helpers read the owner's local archives; no extracted game content is distributed.

Only the read-only archive and IGZ APIs are used. The mod-file-map helper is configured with an empty environment, so its optional integration with the port's `mod_components` module is not used.

## Optional HUD, not bundled

[Reserves + CNK Drift Gauge EU](https://github.com/Majed-allababedi/CTR-CNK-Drift-Gauge-EU): original by **tomtotom** ([GameBanana](https://gamebanana.com/mods/729041)), EU adaptation by **Majed-allababedi**. This is a separate project and its license is not changed by this repository. None of its package or assets are included.

## Test dependency

The optional machine-code tests use [Unicorn Engine](https://www.unicorn-engine.org/), installed separately. It is not vendored in this repository.
