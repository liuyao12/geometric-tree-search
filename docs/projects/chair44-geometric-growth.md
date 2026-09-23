# Chair44: geometric matching in the live tiler

Historical geometry: the live viewer now uses the [tetrahedral relief](chair44-tetra-relief.md). The results and prototype below refer to the earlier geometry.

Apply one and Run now use the actual selected bump/dent profile through its
exact occupancy model. They do not check arrow direction or color agreement.
The Arrows/Relief buttons change the display; Offset/Centered changes the
geometry used by search. The active geometry is named beside the scene.

[Open the live tiler](https://liuyao12.github.io/geometric-tree-search/3d-reptiles/).
Choose **Relief → Centered**, then **Apply one** and **Run**. Branch decisions,
backtracks, and active frontier-point counts appear in the side panel.

## Branching comparison

Starting from the same single root, using the same complete enumeration,
generation ordering, distance/key candidate order, and $64$-tile checkpoint:

| Matching rule | Initial non-overlapping neighbors | Branch decisions | Backtracks | Forced placements attempted |
|---|---:|---:|---:|---:|
| Original arrows, retained as a test control | $44$ | $4$ | $0$ | $59$ |
| Offset relief geometry | $128$ | $4$ | $0$ | $59$ |
| Centered relief geometry | $316$ | $12$ | $7$ | $51$ |

These are measurements of this deterministic run, not a claim that weakening a
rule increases branch or backtrack counts for every seed and search order. A
geometrically legal contact can create an unfillable pocket immediately or
force a further placement that exposes a contradiction. The live solver detects
those through its complete frontier, rather than prefiltering by the arrows or
using the exclusion certificates from the earlier research.

## Geometry and point-value contract

Allowed poses remain integer translations and the $24$ proper cubic rotations.
This is exact matching for those lattice-aligned copies, not a search over
arbitrary translations and rotations in continuous space.

The engine uses binary occupancy $t\in\{0,1\}$ on cell centers and panel probes:
$24$ probes per panel for offset relief, $10$ for centered relief. No $m$-values
are present in the geometric search. Colors select the authored profiles only;
no color compatibility predicate is invoked. Coordinates are represented exactly
in $\mathbb Q(\sqrt2)$ and all occupancy comparisons use integers.

The [offset](chair44-relief-search.md) and
[centered](chair44-centered-relief.md) reports give the geometric sufficiency
checks: every facing configuration has the same overlap/gap result in the
continuous profile and its point model. All modifications lie in disjoint
panel neighborhoods, so bulk cell-center and panel-probe occupancy together
capture all collisions and pockets for the allowed poses.

The browser and research scripts now import the same
[relief point model](../../3d-reptiles/chair/relief-points.js).
The [shared growth engine](../../3d-reptiles/chair/chair-gcts.js) selects the
appropriate model using the state's `rule`. Its existing arrow mode is retained
for historical controls and tests; the browser explicitly selects geometric
mode even while drawing arrows.

At every move, the complete point/candidate graph is rebuilt. Global degree-zero
obligations take priority, followed by global singleton propagation, then
branching in the earliest frontier generation. Candidate count breaks generation
ties. Relief probes are included as obligations even between two occupied cells.
Candidates are shared across all incidences. Generations and the full branch
stack are retained during rollback. No substitution positions, supertile test,
known adjacency list, or extra arrow filter participates in geometric search.

A step makes up to $32$ search attempts before yielding. A budget pause remains
unfinished search, not an exhausted branch or a tiling certificate. A finite
checkpoint is accepted only after the whole active frontier has no dead point.
The initial single-seed checkpoint is $64$ tiles; Apply one continues beyond it.

## UI transactions and cancellation

Search runs in a module worker so the browser can continue rendering and accept
Pause while geometric enumeration is in progress. Canceling terminates pending
work and keeps the last accepted snapshot; a late result cannot add a tile.
Worker replies carry solver state and branch alternatives. UI undo history stays
on the main thread, avoiding recursive serialization of the snapshot history.
Placement caches are cleared between resumable search batches to bound retention.

- Apply one after inflation preserves every current tile as a fixed root,
  including its position and full orientation.
- Undo restores the complete state before Run began, including counters and
  remaining branch alternatives. Even a Run canceled before its first result
  has an undoable start snapshot.
- Changing Offset/Centered pauses search, rechecks geometric non-overlap, and
  makes the unchanged current patch the fixed root under the new rule. Old
  branch decisions and counters are discarded. Undo restores the previous rule,
  generations, counters, and branch stack.
- If the current patch overlaps under a requested profile, the change is refused
  with an explanation; tiles are not silently deleted or moved.
- Arrows/Relief changes the drawing without changing any search state.

As in the earlier engine, incremental dependency updates are not yet implemented:
the graph is rebuilt. Arbitrary fair coverage of the infinite point domain is
also not established. These are finite growth checkpoints. The specialized
geometry-to-point correspondence and lattice restriction are explicit, in line
with the [master algorithm contract](../basic-tiling-algorithm.md).

## Verification

The engine tests cover both geometric neighbor counts, complete facing-profile
checks, proper rotations, imported inflation roots, real backtracking, immutable
rollback, and continuation beyond a checkpoint. A centered-only pair that fails
the arrow test is accepted into the geometric search, forces one tile, and then
exhausts through a dead point: the test guards against hidden arrow filtering.

Browser tests cover the worker's centered $64$-tile result and counters, immediate
cancellation and late-response exclusion, whole-Run Undo, geometry-change Undo,
unchanged matching while drawing arrows, normal/reduced motion, orientation
dimming, inflation import, mobile layout, and constant opacity during Run.

```sh
node scripts/test-chair-geometric-growth.mjs
node scripts/test-chair-gcts-growth.mjs
node scripts/test-chair-relief-points.mjs
node scripts/test-chair-geometric-browser.cjs
node scripts/test-chair-run-browser.cjs
node scripts/test-chair-marking-view-browser.cjs
```

Browser tests use Playwright with a local server at port `8765`; set
`CHAIR_TEST_URL` to check the deployed site. `CHROME_PATH` optionally selects the
browser executable. They expose inspection helpers only inside the test harness.
