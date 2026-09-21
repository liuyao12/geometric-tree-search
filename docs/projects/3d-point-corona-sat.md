# Exact finite corona constraints for the 3D catalogue

This research control addresses the label-collection bottleneck in
[the geometric polycube study](3d-voxel-marking-research.md). It uses the same
integer point model and the same definition of a viable pair corona. It uses
Z3 pseudo-Boolean constraints rather than the reference graph scheduler and is
**not** enabled in either app lane. It has no geometric collision predicate,
known marking, periodic motif or preclassified pair table in its constraints.

## Why a finite candidate universe is complete

Let K be the positive t-support of the two fixed seed placements. Let C contain
every allowed placement whose positive support meets K. Enumerating each seed
support point, each orientation, and each positive anchor gives this finite set
without a bounding-box cutoff. Placements conflicting with the fixed seeds can
be omitted permanently. Placement identity and the allowed translation domain
are retained exactly.

Suppose a finite legal patch S completes K and has a viable exposed frontier.
Remove every placement not in C, giving S'. The seeds remain and every sum on K
is unchanged. All other sums decrease, preserving legality. Consider a point
that is positive but incomplete in S':

- If it was incomplete in S, its legal additional candidate is still legal
  after removal, since every t-sum has decreased.
- If it was complete in S, some removed placement contributes to it. That
  placement is a legal additional candidate in S', since adding it gives a
  subset of the original legal patch.

Thus S' also has a viable frontier. Conversely, any valid witness drawn from C
is already a valid witness for the original local problem. Existence of a
finite viable pair corona can therefore be decided within C. This argument
uses positive t-values, nonnegative sums, distinct placements and **no markings**.
It does not assert that a viable corona extends infinitely.

`test-3d-corona-projection.mjs` projects 14 positive reference-search witnesses,
removing 17 non-core placements in total. Independent point/frontier replay
remains positive, including a genuinely 3D polycube example.

## Formula and frontier refinement

One Boolean variable chooses each candidate in C. The seed variables are true.
At every point in the union of candidate supports, the weighted sum is at most
capacity; at every point of K it is exactly capacity. All weights and bounds are
integers. The finite formula initially asks only for a complete core.

Every SAT assignment is then checked at **every exposed point**. This separate
enumeration considers every orientation and support alignment at that point,
including additional placements outside C. If all points have candidates, the
assignment is a positive witness. JavaScript then independently replays both
the point sums/frontier and voxel nonoverlap.

A dead frontier is a monotone obstruction: no legal superset can repair it,
because every placement touching that point is already selected or exceeds
capacity somewhere. This control shrinks that obstruction by removing
irrelevant placements and adds a clause forbidding its selected subset.
All recorded obstructions are independently replayed in JavaScript. A time,
candidate or refinement limit is unresolved, never negative. An exhausted
formula is a negative local label conditional on the trusted Z3 solver and the
complete construction above; this implementation does not emit a standalone
checked UNSAT proof.

## Reproduction and checks

### Validated binary-cover reduction

`--encoding=voxel-cover` specializes the formula after checking every orientation's
explicit t-data against its distinct unit voxels. It requires capacity 8 and
translations in even half-unit coordinates. Missing center constraints, changed
corner weights, duplicate voxels or a different translation domain are rejected.

For a legal packing, a seed corner reaches 8/8 exactly when all eight incident
voxels are occupied. Expand each core corner into those eight voxel centers and
retain the seed centers. The formula then requires exactly one selected copy at
each required center and at most one at every other center. Distinct occupied
voxels already imply every corner's upper bound. Thus both the core completion
and all capacity constraints are equivalent to the original weighted formula.
The candidate universe and subsequent weighted frontier check are unchanged.

In the same fourteen-pair sample with a twenty-second budget, this encoding
resolves **five** cases: the previous three, plus a positive p9-48258 pair and a
negative p10-054782 pair. The new positive passes independent weighted-point,
viable-frontier and voxel replay. The new negative exhausts the core formula.
The other nine remain unresolved. These remain local results, with no new
infinite-tiling classification. The [binary-cover receipt](../../data/3d-voxel-cover-corona-2026-09-21.json)
records all cases and source hashes.

`test_voxel_corona_encoding.py` checks all 256 voxel subsets around one corner,
137 complete/defective/overlapping patches, both solver encodings on a cube
pair, and rejection of invalid reductions. The generic weighted oracle retains
its independent 43-case exhaustive regression.

```sh
python3 scripts/test_voxel_corona_encoding.py
node scripts/screen-3d-point-corona-sat.mjs \
  --input=/tmp/gcts-voxel-screen-final \
  --output=/tmp/gcts-voxel-cover-screen --time-ms=20000 --encoding=voxel-cover
```

### Whole-point frontier constraints and resumable catalogues

The optional `--frontier=occupancy` control requires `--encoding=voxel-cover`.
It replaces patch-specific rejection clauses with an exact condition on each
encountered dead corner. Let B(v) mean that a selected placement occupies voxel
v, and let A(c) mean that every voxel of an additional placement c is unoccupied.
For a corner q with its eight incident voxels N(q), enforce:

```
all v in N(q) are unoccupied
OR all v in N(q) are occupied
OR some allowed placement c touching q has A(c).
```

The first two cases mean q is absent from the frontier. The third supplies a
legal candidate. All placements touching q are enumerated, including those
outside the finite core-covering SAT universe. Occupancy variables are exactly
the disjunction of the corresponding placement variables, and availability
variables are exactly the conjunction of empty voxel tests. Hence this is the
original viable-frontier condition, not a learned generalization of a failed
patch. Independent weighted-point replay still checks every final positive and
every recorded failed patch.

On the previously unresolved second p9-42947 pair, a fresh 30-second run produces
a **37-tile viable corona in 28.9 seconds**, after adding 89 corner conditions.
The witness passes independent point sums, full exposed-frontier enumeration
and voxel nonoverlap. All 89 intermediate obstructions also replay as dead. The
[witness receipt](../../data/3d-occupancy-frontier-2026-09-21.json) records the
exact pair, source hashes, replay checks and local artifact digest.
This is a local witness for that pair, not an infinite tiling of p9-42947.

The oracle can save these corner locations and rebuild their necessary
conditions in a later run. `--resume=<previous result>` verifies an exact
input digest and frontier mode before reuse; it never reuses provisional labels
as constraints. Reported cumulative time includes both runs. Tests check resume,
reject a changed pair, and exercise outer-corner candidates outside the SAT pool.

`learn-3d-voxel-pair-catalog.mjs` adds exact proper-rotation and seed-exchange
orbits. Each transform maps every orientation's weighted t-support exactly, and
its normalization offset must belong to the declared translation lattice.
Every member carries an explicit transform from its representative. Positive
witnesses are transformed and independently replayed for **every raw pair**;
negative labels transfer by the same bijection of the complete local problem.
Unknown labels remain unknown throughout the orbit.

For p9-48258 this reduces 686 pairs to 60 representatives. The regression also
checks every weighted seed transport across all fourteen catalogue tiles and
checks all 26 cube pairs via their three orbits. A partial cube pass does not
activate a marking; resuming to all three orbits accepts the empty marking and
verifies marked finite growth. Successful and failed local labels are fed to the
same `OnlineMarking` encoder, with every raw pair independently rescored. A
complete catalogue, no unknowns, all positives passed and a majority of negatives
blocked are still required before marked search can start.

The [first p9-48258 catalogue pass](../../data/3d-p9-48258-orbits-pass1-2026-09-21.json)
checks all 60 representatives with five seconds each. Nine orbits resolve
positive, covering **70 of the 686 raw pairs**; their transported witnesses all
pass independent replay. The other 51 orbits, covering 616 pairs, remain
unresolved. The provisional encoder passes the 70 positives with an empty
marking, but the unresolved catalogue prevents activation. The pass takes about
287 seconds including collection, replay and encoding. It does not establish
that the unresolved pairs are valid or that there are no negative connections.
The checkpoint retains their necessary frontier-point conditions for larger
subsequent attempts without repeating the nine resolved searches.

Run one process per output directory. Resume only after the previous process is
terminal; checkpoints alone are not evidence that a process has stopped:

```sh
node scripts/learn-3d-voxel-pair-catalog.mjs \
  --tile=p9-48258 --output=/tmp/gcts-cross-orbits \
  --pair-ms=5000 --frontier=occupancy
node scripts/learn-3d-voxel-pair-catalog.mjs \
  --tile=p9-48258 --output=/tmp/gcts-cross-orbits \
  --pair-ms=20000 --frontier=occupancy --resume=true
```

These helpers are headless research controls. The app's reference scheduler,
browser storage and acceptance threshold are unchanged. Full learned assignments
remain in the requested local output directory and are not bundled into the app.

### Earlier weighted-formula and graph controls (measurements)

The 14-case refinement takes the first unresolved pair of every historical
polycube record from the earlier five-second faithful-model sweep. The reference
search receives 10,000 attempts, four million dependency entries and 20 seconds
per pair. Its largest sampled worker heap is about 317 MiB; this is not a peak
process-memory measurement. The app retains its original one-million-entry cap.
The separate SAT control receives 20 seconds including formula construction.

| Previously unresolved pair | Larger reference search | Finite PB/SAT control |
| --- | --- | --- |
| p9-20656, pair 0 | Valid, 62 attempts | Valid, independently replayed |
| p10-052588, pair 3 | Unresolved, 10,000 attempts | Invalid; core formula exhausted |
| p10-052670, pair 0 | Invalid, 326 attempts | Invalid; core formula exhausted |
| Other 11 sampled pairs | Unresolved | Unresolved |

The SAT run independently replays 151 recorded dead-frontier obstructions. In
particular, merely filling the seed support would have mislabeled many trial
assignments as positive. The two SAT-negative rows exhaust their core formulas
without needing a frontier clause. Both tiles were already known non-tilers;
these local labels are controls, not new global classifications. The p9-20656
witness is a new positive local label, not an infinite construction.

Exact pair descriptors, budget outcomes and source hashes are in the
[reference refinement receipt](../../data/3d-corona-refinement-2026-09-21.json)
and [SAT receipt](../../data/3d-point-corona-sat-2026-09-21.json). The campaigns
ran sequentially within each runner, but small diagnostics also ran during
collection, so these timings are not isolated speed benchmarks. Together they
resolve three of the fourteen selected local questions. No complete catalogue
or accepted marking results from this sample.

The current bottleneck is now explicit: many finite core completions fail at an
outer frontier, while several large formulas time out before producing a first
core completion. More time or a larger dependency cap alone does not solve most
of these cases. These measurements motivated the binary-cover and whole-point
frontier controls above. Their specialized scheduling remains separate from
the app. The subsequent full p9-48258 catalogue below closes that local collection gap.

Python requires `z3-solver`; the recorded runs use Z3 4.16.0. For one input file
containing `model` and `pair`:

```sh
python3 scripts/solve_point_pair_corona.py \
  --input=/tmp/pair.json --output=/tmp/result.json --time-ms=20000
python3 scripts/test_point_pair_corona.py
node scripts/test-3d-corona-projection.mjs
```

The Python tests compare 43 tiny problems with independent exhaustive subset
enumeration, including exposed-frontier checks, and check that budgets return
unresolved. The JavaScript sweep verifies every emitted obstruction, not just
positive final witnesses. Raw witnesses remain in the requested run directory;
aggregate research receipts contain no learned marking assignments.

```sh
node scripts/refine-3d-corona-pairs.mjs \
  --input=/tmp/gcts-voxel-screen-final \
  --output=/tmp/gcts-pair-refinement-20260921 \
  --time-ms=20000 --nodes=10000 --dependencies=4000000
node scripts/screen-3d-point-corona-sat.mjs \
  --input=/tmp/gcts-voxel-screen-final \
  --output=/tmp/gcts-point-sat-screen-20260921 --time-ms=20000
```

The fourteen-case screens are label experiments on previously unresolved pairs.
They do not complete any tile's pair catalogue, certify a redundant learned marking, resolve any
unknown tile's infinite tilability, or establish an aperiodic monotile.


## Complete p9-48258 catalogue and conditional free values

The continued occupancy-frontier run classifies all 686 pairs through 60 verified
symmetry orbits: **622 valid, 64 invalid, no unresolved pairs**. All 622 transported
positive witnesses and 1,415 recorded frontier obstructions were independently
replayed. Negative exhaustion is trusted Z3 UNSAT; no independently checkable
UNSAT proof is exported. Collection across the 5-, 20-, and 60-second passes cost
723.82 seconds (about 12.1 minutes). See the [complete catalogue receipt](../../data/3d-p9-48258-complete-2026-09-21.json).

The all-assigned equality encoder blocks none of the 64 negatives. Free values
require a different operation: remove their equality edges **before** recomputing
connected components. A symmetry-preserving support-mask search then passes all
622 positives and blocks all 64 negatives with 60 scalar assignments across three
orientations (20 each), using six categorical labels at extent 1. Interior points
remain eligible. Support search is heuristic, with no minimality claim.

An exhaustive audit of every possible active-mark overlap finds no additional
rejected pair outside the known negatives, including noncontact placements.
This preservation statement is conditional on the local negative labels and the
declared grid-aligned transformation group. It neither supplies an infinite
construction nor justifies unrestricted geometric alignment.

Sequential warm searches of the same 91-point window all pass independent point
and voxel replay:

| Seed | Unmarked time / attempts | Marked time / attempts |
| --- | --- | --- |
| 1 | 4.19 s / 53,479 | 12.55 s / 64,848 |
| 2 | 11.89 s / 151,531 | 2.67 s / 12,948 |
| 3 | 18.96 s / 229,323 | 4.48 s / 24,369 |

These exclude the 12.1-minute collection cost and roughly 1.1 seconds of support
search over three extents. They show mixed warm performance, not a cold speedup.
[Full synthesis, contact audit and growth receipt](../../data/3d-p9-48258-masked-2026-09-21.json).
Raw markings and patches remain in the local output directory; no learned
assignments are bundled. Reproduce with `scripts/learn-3d-voxel-pair-catalog.mjs`
and `scripts/train-masked-3d-catalog.mjs`. These measurements use the headless
research encoder and specialized SAT oracle, not a browser SAT dependency.

## Larger growth and period proposals after complete pair learning

The p9-48258 marking was tested beyond its successful 91-point target. Two seeds
at each of two larger sizes were run both unmarked and marked, with 20 seconds
and one million attempts per run. All eight stop **unknown** at the time limit:

| Radius | Required weighted points | Equivalent fully covered voxel region | Completed runs |
| --- | ---: | --- | ---: |
| 2 | 341 | 7 × 7 × 7 | 0 / 4 |
| 3 | 855 | 9 × 9 × 9 | 0 / 4 |

The voxel region is larger than the initially required center cube because
requiring complete corner weights forces all eight incident voxels to be present.
Every returned partial patch passes independent nonoverlap and marking replay,
but none fills its target. Runs were sequential within the growth runner; some
separate diagnostics overlapped, so these are cutoff observations, not isolated
speed measurements.

A separate finite-window PB/SAT control (`solve_voxel_point_window.py`) uses the
validated center/corner reduction and exact scalar m-value agreement. It shares
the full 2,205-placement candidate universe at radius 2. Both its unmarked and
marked runs also time out at 20 seconds. Unlike the pair oracle, it imposes no
exposed-frontier viability condition, matching the v2 finite-window target.
A marked UNSAT would remain a restricted-model result. The control passes 72
small exhaustive comparisons, including assigned zero, individual free values,
marking conflicts and independent positive witness replay. It is explicitly a
nonreference scheduler and does not replace the browser graph engine.

Six previously verified radius-1 patches also supplied period proposals. We rank
same-orientation displacement vectors by recurrence, take up to 36 per patch,
and try independent triples with tile-volume-divisible determinant. A quotient
exact-cover search uses only placements present in that patch. Across the six
patches, 5,907 basis proposals were tested; 2,529 had a placement pool covering
every quotient class. None yielded a periodic construction. These counts are
basis proposals, not distinct HNF quotients or a complete periodic search.
Successful proposals must pass the existing independent periodic verifier;
failure says nothing about unproposed bases or placements.

[Aggregate growth, SAT and period-proposal receipt](../../data/3d-p9-48258-larger-windows-2026-09-21.json).
Full patches and learned fields remain local. Reproduce growth with:

```sh
node scripts/grow-3d-learned-voxel-windows.mjs \
  --input=/tmp/gcts-p9-48258-masked-final/marking.json.gz \
  --output=/tmp/gcts-larger-windows --radii=2,3 --seeds=1,2 --time-ms=20000
python3 scripts/test_voxel_point_window.py
node scripts/test-patch-period-proposals.mjs
```

Thus the complete pair classifier is useful local evidence, but has not resolved
this tile's infinite tilability. The next local-catalogue collection targets
p9-42947 using resumable occupancy-frontier constraints and exact pair orbits.
