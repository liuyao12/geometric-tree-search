# Rotation-invariant connection-transfer study

## What was implemented

`../connection-descriptor.mjs` learns a nearest-exemplar compatibility hypothesis
from labeled, role-decorated joint supports. Distance channels internal to each
rigid motif are the ablation; cross-motif distances are the experimental channels.
Sorted role/label distance multisets are invariant under common translations and
orthogonal transformations, including reflections. They are not injective and
do not certify point correspondence, proper isometry, or physical compatibility.

For two identified shared points, rotation about their line preserves each motif.
Any compatibility rule depending only on separate rigid-motion invariants is
therefore constant under that rotation. Cross distances need not be constant.
This elementary identifiability argument motivates the experiment; it is not
claimed as a new theorem in rigidity theory or as novelty of distance descriptors.

## Frozen data and split

- Silicon: first 24 configurations from the published 216-atoms.xyz. Positions
  and species only; original headers retained for provenance. Train frames 0–7,
  calibrate 8–15, test 16–23. Quench/anneal labels match but preparation parameters
  vary: do not call these independent draws at identical thermodynamic conditions.
  Cell metadata reconstructs boundary-crossing neighborhoods by minimum image;
  it is not supplied to an infinite growth generator as a lattice.
- Cd–Yb: existing repository port of Feuerbacher V1.5, max_index=4, 60 Å box,
  8,302 atoms. Two-anchor connections are retained only if the complete six-point
  support lies in its split slab. Slabs [-24,-9], [-3,3], [9,24] Å on x contain
  803,225,770 examples. Shared atom IDs across splits are explicitly forbidden.
  Six Å outer margin avoids ordinary box truncation, not unproven completeness
  of the underlying finite six-dimensional enumeration.
- Each example is two four-point supports sharing two anchors; the additional
  points are nearest exclusive neighbors. Six Å maximum reach, no bonds,
  valence, energy, chemical templates or prescribed tetrahedral angles.
- This support proposal is intentionally controlled. It is not the production
  adaptive motif-discovery algorithm, nor a search over all irregular motifs.

Nested training sizes: 1,2,4,8 silicon configurations; every 8th,4th,2nd,1st
connection of the quasicrystal training slab. All sizes, the 90th-percentile
calibration rule, 0.06 Å diagnostic, and 60/120/180° challenges are in the script.
These are exploratory, not externally preregistered confirmatory experiments.

Score is minimum over training descriptors of maximum component error (Å).
Unknown label/role strata have no score and abstain. Quantiles use known strata
only. Calibration is pooled across correlated environments: no conformal,
independence, population coverage, or equilibrium sampling guarantee is claimed.
The tight 0.06 Å cutoff is a descriptor tolerance, NOT a rerun of the production
registration algorithm and NOT an atom-position uncertainty recommendation.

The challenges are rigid relative rotations around the shared anchor line;
both constituent motifs remain exactly congruent to their originals. They are
not labeled physical negatives. Rejection is scored conditionally on accepting
the original; rejecting both is not counted as useful discrimination. Retention,
unknown counts and denominators are always reported alongside rejection.
Compare rates descriptively: separately calibrated models are not guaranteed
to achieve identical held-out retention. There are no significance claims.

## Point-value bridge and conformance

`../connection-marking.mjs` accepts a frozen finite candidate list, explicit
pair/support comparisons, a frozen descriptor library, and a threshold. It
compiles known scores exceeding the threshold with the existing exact finite
conflict-marking compiler. Unknown strata abstain. Original t/m values remain.
The point-domain equality is exact conditional on the floating-point decisions;
those decisions are learned hypotheses, never sound pruning of the unmarked
geometry. No chemistry is present.

The 32 finite attachment controls each have one A candidate and four B poses.
Two required points are active initially, all domains are finite and complete,
capacity is integer 1, and witness-only points have no positive t support.
Generation, global dead/forced checks, branching, dependencies and rollback are
provided by the unmodified PointSearch kernel. A direct relation with neutral
witness dependencies is the comparison. All 32 traces and all 1,024 subset
legality/completion decisions are checked. These independent local attachments
do not test multi-connection loop closure or yield a bulk-growth speedup.
The older finite controls separately exercise rollback.

All declarations and motifs remain approximate external geometry. The kernel
does not infer pose completeness. The bridge is candidate-conditioned, not a
reusable local spatial field transported with an arbitrary motif. Changing the
library, threshold or candidate universe requires recompilation and search replay.
No production engine is modified by this experiment.

## Reproduce

From the repository root (Node 22+ and Python 3 standard library):

```sh
node apps/materials-growth-v2/paper/connection-study.mjs /tmp/connection-replay.json
node apps/materials-growth-v2/paper/test-connection-study.mjs
node apps/materials-growth-v2/paper/aperiodic-growth-audit.mjs /tmp/growth-replay.json
```

Frozen `connection-data.json` makes the study network-independent. To regenerate
that data, download the original XYZ linked in the JSON, verify its recorded
SHA-256, and run `prepare-connection-data.py input.xyz output.json`. The Cd–Yb
source port is in `scripts/materials_gcts_cdyb_oracle.py`. Modified data extracts
retain CC BY 4.0 attribution in JSON and the paper. Raw energies and forces are
not included. Source SHA-256 values in the results pin all new method modules.

Timing fields describe a single local run, not a controlled performance
benchmark. The separate production audit preserves occupancy supports in both
modes; only the existing observed-overlap relation changes. Its statuses and
finite prefixes are not proof of physical quality or global extendability.

## What remains

The silicon trade-off is weak: about 91% observed retention with only 9% paired
twist rejection. Some valid observed connections are still excluded. A whole
generated configuration contains many dependent connections, so a per-connection
retention rate does not imply acceptable whole-configuration survival. Further
data, higher-order features, calibrated uncertainty and explicit abstention are
research requirements, not reasons to relabel current failures as success.
