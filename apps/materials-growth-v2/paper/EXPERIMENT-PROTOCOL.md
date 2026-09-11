# Geometry-only GCTS experiment programme — frozen round 1

This protocol precedes inspection of the new held-out results. It is a local
prospective protocol, not an externally registered study. Failed rounds remain
in the record. No claim of advantage is guaranteed by the programme.

## Scientific target

Determine whether reusable geometric connection constraints preserve observed
configurations and improve constructive search at matched structural fidelity.
Neither preparation history, temperature, pressure, energy, forces, valence,
chemical templates nor a phase label enters learning or candidate ranking.
Periodic cell metadata may reconstruct neighborhoods; it is not a growth lattice.

## Round 1: configuration-level safety and interaction scoring

Use previously unused frames 24–95 of the public 216-atom silicon coordinate
file. Deterministically shuffle these 72 frame IDs with seed 1709, then split
48 training / 12 calibration / 12 test. Split entire configurations before
extracting neighborhoods. The previously inspected first 24 frames are excluded.
Keep provenance metadata outside the algorithm input. Do not select by physics
or formation history. This is a dataset transfer test, not an equilibrium claim.

Retain the previous six-point/two-shared-anchor diagnostic to isolate scoring.
Nested training counts: 4, 12, 48 configurations. Fixed candidate scores:

1. joint: nearest full joint-distance descriptor discrepancy;
2. excess: joint discrepancy minus nearest individual-motif discrepancy;
3. ratio: joint discrepancy / (individual discrepancy + 0.05 Å).

The 0.05 Å stabilizer is a declared numerical hyperparameter, not a physical
constant or a tuned result. Scores are geometry-only and common-rotation
invariant. Unknown role/label strata abstain. These descriptors remain
reflection-insensitive and are not complete isometry classifiers.

Two cutoff policies, selected ONLY from calibration positives:
- 99th percentile across known connections;
- maximum known score across all calibration configurations.

Primary endpoint: fraction of test configurations with no observed connection
rejected. Also report per-connection retention, unknown rate, worst-frame
retention, and rejection of 60/120/180 degree hinge alternatives conditional on
retaining the original. Alternatives are not physical negatives. Configuration
survival refers only to extracted diagnostic connections, not a complete cover.

Promotion gate (exploratory): at least 11/12 complete test configurations retained,
at least 10% conditional twist rejection, and no unknown test strata. A passing
setting is a candidate for confirmation, not proof of useful bulk generation.
Do not claim statistical significance from 12 test configurations. All settings
are reported; any later tuning requires a new untouched test set.

## Round 2: coupled finite completion and search

Only promote a rule after round-1 safety checks. Use identical finite posed
candidate libraries, required point data, seeds, generations and ordering for
base geometry, explicit learned relations and compiled GCTS markings. Preserve
occupancy/support consistency with markings off. Include shared-atom loops and
failed branches. Verify retained solutions independently and report discarded
known solutions. Candidate libraries containing the known answer are replay
controls, NOT blind held-out completion. Continuous sampled-domain failures
remain unknown. Finite rule-restricted exhaustion is not geometric impossibility.

Record attempts, placements, branches, forced moves, backtracks, eliminations,
graph sizes, total runtime including fitting/compilation/verification, and peak
memory. Compare same-result implementations separately from changed hypotheses.

## Round 3: blind completion, hierarchy, and scale

Hide interiors before proposing candidates. Never use hidden coordinates as
candidate positions, motif sources, registry anchors or acceptance thresholds.
Start with larger reference cells and boundary-fixed cavities; distinguish
geometric boundary conditions from chemical bonds. Train irregular motifs and
hierarchies on training configurations only. Validate ring/dihedral statistics,
orientation correlations, coverage, density and diversity on held-out results.
Compare several hole sizes, then larger free-growth patches. Do not derive
thermodynamic entropy from biased search counts.

## Round 4: meaningful scientific comparison

Compare with available WWW/ARTn, ML-MD and generative reference constructions
under matched information and output fidelity. Physics may be used by independent
evaluators, never supplied to the GCTS learner. Preparation metadata can be
unblinded after results are frozen to interpret geometric differences.
Require independent test data, larger cells, repeated runs, and wall-time/memory
accounting before claims of speedup or a materials-method advantage.

The intended case is explanatory and constructive: identify what additional
geometric relationships recover extended organization, and test that removing
them loses the predicted structure without changing unrelated conditions.
