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

### Earlier weighted-formula and graph controls

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
of these cases. A next research direction is a proved equivalent binary-cover
encoding for the center-and-corner voxel model, retaining the same independent
frontier check and keeping its specialized scheduling separate from the app.

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

These are label experiments on previously unresolved pairs. They do not complete
any tile's pair catalogue, certify a redundant learned marking, resolve any
unknown tile's infinite tilability, or establish an aperiodic monotile.
