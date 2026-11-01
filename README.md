# CTR Nitro-Fueled boost mods

Two experimental offline mods for **OCTR Nitro-Fueled PC**, tested on the portable v0.6.4 installation with European **CUSA14876 update 01.21** data.

| Mod | Version | Effect |
| --- | --- | --- |
| Brake Without Losing Reserves | 0.2.0 | Braking preserves accumulated boost reserves. They still drain normally over time. |
| Triple Drift Reserves | 0.1.0 | Good and Perfect drift boosts each add **3× their original stored boost time**, across all three boosts in a chain and all five player driving styles. |

The mods work independently or together. Good and Perfect retain their different rewards. Triple reserves does not triple kart speed. The braking mod keeps the existing brake and steering physics; it does not automatically activate the special U-turn steering state.

## Download and install

Download the two ZIPs from the [latest release](https://github.com/haz93/ctr-nitro-fueled-boost-mods/releases/latest), or use the identical packages in [`releases/`](releases). Keep the ZIPs intact.

1. Close the game. Use an OCTR launcher supporting schema-version-2 packages and the `xml-patches`, `code-signatures` and `archive-assets` capabilities used here.
2. Put the desired ZIPs in the port's `mods` directory, then open or reload the launcher's Mods list.
3. Turn online mode off and enable the desired packages. Start a fresh game process after changing the selection.
4. To revert, disable the packages and restart the game.

These packages declare `offline-only`. Their code signatures and original-asset hashes reject incompatible data. Other regions, game updates and port versions have not been validated. Mods that edit the same boost predicate or DrivingArchetypes resources need a compatibility merge.

No game executable, archives, saves, game assets or PC port binary are included. The loader applies the packages without rewriting the original game files.

## Optional reserve meter

The separate [Reserves + CNK Drift Gauge EU mod](https://github.com/Majed-allababedi/CTR-CNK-Drift-Gauge-EU) makes reserves visible; select the **Speedometer** HUD when using it. Original HUD by **tomtotom**, EU adaptation by **Majed-allababedi**. It was used during testing but is not required by either mod and is not redistributed here.

## What is preserved here

- [`mods/`](mods): exact editable contents of both tested packages, including manifests, the brake patch and original-dependent drift deltas.
- [`releases/`](releases): the original tested ZIPs and their SHA-256 checksums.
- [`tools/`](tools): package verification, rebuilding and private test-fixture generation.
- [`tests/`](tests): repeatable machine-code tests, using the owner's own game files.
- [`evidence/`](evidence): sanitized test reports and the recorded driving confirmations.
- [`docs/TECHNICAL.md`](docs/TECHNICAL.md): implementation, test scope and reproduction instructions.

The repository and release downloads are sufficient to keep and reinstall these mods after deleting the local game installation. Running the game or repeating game-dependent tests still requires your own compatible game and port installation.

## Build and verify

Python 3.10+ is sufficient to verify and rebuild the packages; no game files are needed:

```console
python tools/verify_packages.py
python tools/pack.py
```

New ZIPs are written under the ignored `build/` directory. Rebuilt package payloads match the source; the ZIP container metadata may differ from the preserved releases. Game-dependent tests require Unicorn and privately generated fixtures; see the [technical notes](docs/TECHNICAL.md#repeat-the-game-dependent-tests).

## Validation

The brake mod passed **558** checks executing the real boost eligibility, active-list update and duration helper, including normal expiry and damage invalidation. The triple mod passed **1,023** award checks covering **102** endpoint definitions and **819** sampled interpolation cases. Tests run isolated game routines, not the whole game.

Both mods also started offline together with the optional HUD. Runtime inspection confirmed the brake patch and all three modified archive views. A driving test confirmed normal reserve depletion under braking and larger awards for both Good and Perfect drifts. The exact 3× multiplier is established by the asset and arithmetic checks; the driving confirmation was qualitative. This is limited experimental validation, not exhaustive track or kart coverage.

## License and credits

Project code and patch definitions are licensed under **GPL-2.0-or-later**; see [LICENSE](LICENSE) and [THIRD_PARTY.md](THIRD_PARTY.md). Small unmodified OCTR parsing helpers are included with attribution so fixture generation remains reproducible. The game and optional HUD have their own owners and terms.
