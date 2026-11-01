Brake Without Losing Reserves — EU 1.21 experiment 0.2.0

Use normal brake + steering without holding Down merely to protect reserves.
This patch makes brake-specific boost eligibility follow the same path as
normal driving. Boost time still expires. The ordinary brake and steering calculations
are unchanged; this version does not force the special U-turn steering state,
increase steering rates, add reserves, or grant infinite boost.

The one-byte change is JE -> JMP at PS4 address 0x0122F213 (image offset
0x00E2F213), bypassing the complete brake-specific eligibility block. A 28-byte signature
and original-byte SHA-256 gate the patch against incompatible executables.
CKartBoostData::_cancelOnBrake is the boolean at +0x3A; the predicate at
image 0x00E2F1D0 is used by boost application and by the active boost update.
All boost assets and the game's executable on disk remain unchanged.

Target: CUSA14876, 01.21; tested against executable SHA-256
39d716b70a299b2546bd39996c8592f9375d3f18f9bb8bf11f9139e9af1eb3f5.
The package declares offline-only and the launcher enforces that restriction.
It applies to the shared boost predicate, including CPU karts using that code.

Version 0.1.0 was incomplete: it followed the cancelOnBrake=false branch, whose
brake-only expiry check uses the boost's base sustain (+0x20 in boost data),
rather than its accumulated sustain (+0x28 in the live boost instance). That
could delete banked reserves. Version 0.2.0 skips this entire brake-only block.
The standard update still advances boost age and expires boosts against their
accumulated duration through the original update and duration helper.

Validation: 558 regression checks execute real x86-64 boost eligibility and list
update code, reproduce the 0.1.0 failure, compare braking to stock coasting,
and run accumulated reserves to normal depletion. The actual duration helper
runs without a stub. Memory management and derived speed/intensity calculations
after the reserve update are stubbed in this isolated test. This is not full gameplay
validation, nor a guarantee that brake-turn handling feels right at every speed.

The Reserves + CNK Drift Gauge mod is optional and useful for observing results.
Select the Speedometer HUD to see its reserve bar.

This package contains only original patch metadata and instructions, no game
executable or game assets. Disable the package and restart to restore normal
brake cancellation. Do not stack another patch that changes the same check.
