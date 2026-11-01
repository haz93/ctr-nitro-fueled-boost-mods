Triple Drift Reserves - EU 1.21, version 0.1.0

Good and Perfect drift boosts each award three times their usual stored boost
time. All three boosts in a drift chain and all five player driving styles are
covered. The original difference between Good and Perfect is retained.

The engine banks boostInDuration + boostSustainDuration. The mod changes only
player drift boost sustain fields, using newSustain = 3*oldSustain + 2*boostIn.
This makes total awarded time three times the original while preserving the
speed ramp, boost speed, timing window, fade-out, jump boosts, turbo pads,
power-ups and AI-specific driving archetypes. Float32 rounding applies.

Three original-dependent archive-entry deltas cover the permanent, update and
latest update2 copies of DrivingArchetypes. No executable edits or original
game payloads are distributed. Turning off the package restores the original
data. Original game files are never rewritten.

Target: the installed CUSA14876 01.21 data, checked by original-entry SHA-256.
The mod is offline-only. It is independent of the optional brake-reserves and
reserves-HUD packages, and is validated alongside both on this installation.
Other mods changing the same driving-archetype resource require a merge.
