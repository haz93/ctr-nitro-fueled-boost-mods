# Implementation and reproducibility

Target: CUSA14876, update 01.21, on the tested OCTR portable v0.6.4 installation. Original `eboot.bin` SHA-256:

```text
39d716b70a299b2546bd39996c8592f9375d3f18f9bb8bf11f9139e9af1eb3f5
```

## Brake reserves 0.2.0

The shared boost eligibility predicate starts at image virtual address `0xe2f1d0`. Its brake-specific branch considers both `_cancelOnBrake` and a base-duration expiry check. Skipping only `_cancelOnBrake` is insufficient: accumulated reserves can outlast that base duration.

The working patch changes one byte, `74` (JE) to `eb` (JMP), at image VA `0xe2f213`, corresponding to PS4 patch address `0x122f213`. It skips the entire brake-only eligibility block. Normal aging and removal still run through the game's active boost update and duration helper. The package checks a 28-byte signature and the SHA-256 of the original byte before application.

The shared predicate can affect CPU karts that use it. The patch does not change brake or steering calculations, force a U-turn state, increase speed, or add reserve time.

The brake harness executes the original predicate and list-update code with synthetic kart and boost objects. Its 558 checks compare patched braking to original coasting, cover eligibility flags, ages and damage, reproduce the failed 0.1.0 experiment, and run accumulated reserves through normal expiry. The actual duration helper runs. Reference release and derived speed/intensity calculations are stubbed; memmove is implemented by the harness. Stack and preserved registers are checked. This is an isolated routine test.

## Triple drift reserves 0.1.0

The engine banks `boostInDuration + boostSustainDuration`. Tripling sustain alone would undercount the award. Each selected object keeps ramp-in `r` unchanged and replaces sustain `s` with:

```text
newSustain = float32(3 * s + 2 * r)
r + newSustain ≈ 3 * (r + s)
```

Only the four bytes at object offset `+0x20` change. The ramp is at `+0x1c`. Float32 rounding applies.

The package contains original-dependent deltas for `DrivingArchetypes.igz` in `permanent.pak` (32 fields), `update.pak` (32) and `update2.pak` (38), for 102 fields total. It covers min/max boost endpoints, the three stages of a drift chain, and normal/max drift boosts under these player roots:

```text
DrivingArchetype_Advanced_driftData
DrivingArchetype_Beginner_driftData
DrivingArchetype_IntermediateA_driftData
DrivingArchetype_IntermediateB_driftData
DrivingArchetypes_AdvancedB_driftData
```

Only `CKartBoostData` and `CKartBaseBoostData` under those roots are targeted. Boost speed, ramp-in, fade-out, timing windows, other boost sources and AI-specific archetypes retain their original fields. Each asset operation checks both original and patched resource SHA-256 values. The repository contains only small four-byte replacement deltas and metadata, not original resource payloads.

The award harness executes two actual arithmetic blocks: fresh sustain initialization (`0xe2efe4..0xe2efea`) and weaker-chain reserve addition (`0xe2e98c..0xe2e9a6`). It performs 204 endpoint checks plus 819 sampled interpolation checks across 39 min/max pairs. Interpolation is constructed mathematically in float32; the full drift control flow and chain-head replacement are not emulated.

## Repeat the game-dependent tests

Use your own compatible original game directory and a prepared, unpatched ELF from the port. Tests never fetch or distribute these files. Run from the repository root:

```console
python -m pip install -r requirements-test.txt
python tools/make_fixtures.py "D:\Games\CTR\CUSA14876-1.21"
python tests/test_brake_function.py --elf "D:\Games\OCTR\out\eboot.elf"
python tests/test_drift_awards.py --elf "D:\Games\OCTR\out\eboot.elf"
```

The paths above are examples. The fixture generator reads `archives/` below the supplied game directory and validates all three resource hashes, every old/new delta and every selected object. It writes private object fixtures and an asset report to ignored `work/`. Do not commit the fixtures, which contain extracted object data. The test ELF reader accepts ELF64 little-endian files, not encrypted PS4 executables or SELF containers.

The tests write `work/brake-function-tests.json` and `work/triple-drift-function-tests.json`. Re-running the emulators does not constitute a gameplay test; their reports keep `gameplay_verified: false`. Separate sanitized driving confirmations and runtime checks are retained in `evidence/*-validation.json`.

## Preservation

`tools/pack.py` regenerates the package file inventory from `mods/` and builds schema-version-2 ZIPs using only Python's standard library. It does not require the port or game. `tools/verify_packages.py` checks checksums, inventory hashes, safe package paths, source/release correspondence, the one-byte brake patch, and all 102 drift deltas. The preserved release ZIPs are the exact archives used in the successful driving tests.
