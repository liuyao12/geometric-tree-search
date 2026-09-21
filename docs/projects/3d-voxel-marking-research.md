# Geometric polycube checks and GCTS labeling

## What changed after the catalogue audit

The [first catalogue audit](3d-learned-catalog-audit.md) correctly reported finite
**point** windows, but that success is not sufficient for a geometric monotile
search. An independent replay of its six successful historical-polycube patches
found voxel overlaps in every one:

| Record | Selected tiles | Repeated voxel occurrences |
| --- | ---: | ---: |
| p9-42947 | 25 | 29 |
| p9-02127 | 24 | 39 |
| p9-08203 | 21 | 21 |
| p9-43172 | 20 | 27 |
| p10-055695 | 20 | 19 |
| p10-346304 | 22 | 20 |

The checker first replays the archived t-values, checks orientation identity,
then transforms each original unit voxel using the orientation matrix and
normalization translation. Any repeated occupied voxel is a geometric overlap,
irrespective of its vertex weights. The [receipt](../../data/3d-polycube-geometric-audit-2026-09-21.json)
includes artifact hashes and an explicit pair of conflicting placements for
each patch. This does not invalidate their point-window classification; it
prevents using those patches as geometric tiling evidence.

```sh
node scripts/audit-3d-polycube-patches.mjs /tmp/gcts-hard-audit-final
```

## A faithful model for grid-aligned polycubes

`apps/3d-lattice-tiler/voxel-point-model.js` provides an explicit research model.
Coordinates use half-unit steps. For each unit voxel with lower corner v:

- its center, at coordinate `2v + (1,1,1)`, contributes 8/8;
- its eight corners, at coordinates `2(v + delta)`, each contribute 1/8;
- contributions from voxels of the same tile are combined at shared corners.

Only even coordinate translations are admitted, so physical translations are
integral. The point group consists of proper cubic rotations, optionally with
reflections. The required sites are centers and corners; other parity classes
are not tiling obligations. Markings may still occupy additional sites.

**Packing equivalence.** Two occupied copies of a unit voxel give 16/8 at its
center and are forbidden. Conversely, if all occupied unit voxels are distinct,
each center has at most one contributor and each corner has at most eight
incident voxels, so every t-sum is at most one. Thus capacity legality is
equivalent to geometric nonoverlap under this declared placement group.
Filling every voxel center covers the integer voxel grid; its corner sums then
equal one automatically. This is not a theorem that unrestricted Euclidean
tilings must align to this grid.

For the finite radius-one experiment, the target is 27 voxel centers plus their
64 distinct corners, 91 sites in total. Completing the corners can require
tiles outside the central block. This is a different, stronger target than the
old 27-vertex window. Timings across these two models are not an A/B speedup
comparison.

The new model uses the shared pair enumerator, unmarked corona oracle, learner,
and marked point search. No geometric predicate is inserted into the base
solver: the stronger constraint is entirely explicit t-data. Every positive
corona and completed search is additionally replayed as a voxel packing.
The app's historical point models retain their existing meaning; this model is
selected explicitly in the headless research runner:

```sh
node scripts/screen-3d-learned-catalog.mjs \
  --catalog=polycubes --model=voxel-center-corner \
  --time-ms=5000 --output=/tmp/gcts-voxel-screen
```

The final sequential sweep of all 14 historical records uses seed 1, proper
rotations, 5 seconds per lane, 10,000 search attempts and 500 attempts per pair.
The free lane completes eight of the 91-site windows; all eight pass both the
point verifier and independent voxel replay. The other six remain unresolved.
The GCTS lane remains unresolved on all 14: it processes 3–14 pairs per shape
but has not completely labeled any catalogue, so no marking is activated.
These results and source hashes are in the [research receipt](../../data/3d-voxel-marking-research-2026-09-21.json).

## Oracle memory experiments

The seed pair is permanent during a corona check. Candidates conflicting with
its t-values can therefore be omitted before allocating their dependency
records. Their rejection cache belongs only to that pair. The default oracle
now does this; `fixedSeedFilter: false` preserves the old control. This is an
exact exclusion, not a learned negative label.

Two additional optimizations remain **experimental**, selected together with
`retainBranchCaches: false`:

1. Restore the point/candidate cache to its parent size on rollback, removing
   unused dependency records introduced by the failed child.
2. When a frontier point first appears, omit newly enumerated candidates that
   conflict with the existing branch prefix. A new active point was untouched
   in the parent. That prefix cannot roll back while this point remains active;
   after rollback the point is discarded and any later activation enumerates
   its complete domain afresh. Existing candidate nodes keep all dependencies
   and are updated reversibly. This optimization is prohibited when branch
   caches are retained, because reuse across a different prefix would be wrong.

These experiments reduce some memory counts but substantially slow some fixed-
attempt searches. They are not enabled by default and have not established a
hard-case classification or a speedup. Resource-limited pair checks remain
unresolved. Reproducible diagnostics are:

```sh
node scripts/benchmark-3d-corona-fixed-seeds.mjs
node scripts/benchmark-3d-corona-cache-rollback.mjs
```

For example, on the second sampled pair of p9-42947, both cache policies reach
the same 500-attempt stop with identical placement trace. Deletion plus birth
filtering lowers the peak dependency count from 792,488 to 518,374, but takes
about 5.27 seconds versus 1.44 seconds with caches retained. On one
p10-054782 pair it gets beyond the old memory stop, but still times out without
a label. The permanent seed filter alone preserves resolved traces and gives
modest improvements on some fixed-attempt pairs, with regressions on others;
this small diagnostic is not a general speedup result.

## Verification and remaining discovery work

`test-3d-voxel-point-model.mjs` checks 7,203 translated/oriented pairs against
independent voxel nonoverlap, verifies translation restrictions and point-group
closure, and runs the shared learner and marked search with geometric replay.
`test-3d-corona-fixed-seeds.mjs` compares complete frontier domains with fresh
enumeration, checks nested rollback and sibling branches, forbids rolling back
permanent seeds, and compares labels, node counts and final traces with the old
cache control on sampled cube/hexagon/Turtle pairs. The complete reflected
Turtle and Hat learning regressions retain their previous classification scores.
The same fresh-domain and nested/sibling rollback checks also cover the
genuinely three-dimensional p9-42947 center-and-corner model and compare its
resolved first-pair trace across cache policies.

The next bottleneck remains obtaining complete local extension labels for hard
3D shapes. The corrected geometric model closes a necessary evidence gap; it
does not resolve whether any surviving polycube tiles all of space. A discovery
still needs an infinite construction and proof excluding every periodic tiling,
including a separate alignment argument if the claim allows arbitrary isometries.
Learned markings must be proved necessary or enforced by geometry before they
can support that universal claim. No aperiodic monotile is certified here.

The [finite point-corona follow-up](3d-point-corona-sat.md) raises the reference
budgets and introduces a separately labeled PB/SAT control with a finite-universe
completeness argument. Together they resolve three previously unknown sampled
pairs out of fourteen, with no new global tile classification. The app's oracle
and its resource limits are unchanged by that research experiment.
