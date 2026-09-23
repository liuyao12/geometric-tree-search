# Chair44: testing the relief as occupancy only

This experiment tests the **displayed relief**, without an arrow-matching or
color-matching predicate. It asks whether additional nonoverlapping pairs can
extend, and whether the resulting patches exhibit the eight-chair reptile
structure. It does not test centered pyramids, the proposed letter labels, or
arbitrary continuous placements.

## Model and verification

The tile is the chair with the existing offset pyramids: red protrudes, green
recedes, and blue joins a protrusion and recess into a sloping face. Color names
select the authored geometry only; color compatibility is never consulted by
the search. There are no marking values, only occupancy values $t\in\{0,1\}$.

Allowed placements are the $24$ proper cubic rotations and integer translations
of the physical tile. The required point domain is a periodic union of finitely
many translates of $\mathbb Z^3$: unit-cell centers, plus $24$ probes at each
unit-panel center. Relative to a panel center, probe coordinates are

$$
\left(\frac{\sqrt2\,x}{100},\frac{\sqrt2\,y}{100},\frac{h}{400}\right),
\qquad h\in\{-47,47\},
$$

in its two tangent axes and positive normal direction. Tangential pairs are
$(\pm5,\pm5)$ and $(\pm4,\pm12),(\pm12,\pm4)$. The program uses exact integer
identifiers and integer height comparisons; coordinates belong to
$\mathbb Q(\sqrt2)$, rather than being rounded onto a voxel grid.

These probes are sufficient for this placement domain, rather than merely a
visual sampling heuristic:

1. All relief modifications lie strictly inside the $\ell^1$ ball of radius
   $1/2$ around their unit-panel center. Balls for different panels have disjoint
   interiors. Exact squared inequalities check the bound at every pyramid
   vertex. No modification changes a unit-cell center.
2. Thus cell-center occupancy detects overlapping underlying cubes. Only the
   owners of a panel's two adjacent cells can supply material within its relief
   neighborhood; another tile cannot reach a gap there without overlapping a
   cell center.
3. For every facing-panel configuration, the difference of the two interfaces
   is piecewise linear. Its extrema occur at intersections of the pyramid base
   and ridge lines. The verifier enumerates $493$ exact intersection vertices
   and compares the existence of a geometric overlap or gap with the probes.
   All $864$ configurations agree, including reversed and perpendicular arrows.
4. The positive point support transforms correctly under all $24$ rotations.
   The exact model also agrees with the rendering's height function. This
   establishes the geometry-to-point correspondence for the declared poses.

Two recesses illustrate the difference between packing and tiling: their
interiors can avoid overlap, while neither fills part of their shared panel.
The corresponding zero-occupancy point remains a required obligation.

## Search contract

The experiment uses the project's complete frontier point/candidate graph:
check all dead points, then all forced moves, then branch in the earliest
frontier generation. Candidate count breaks generation ties. Every proper
orientation and every positive cell-center alignment is enumerated. A relief
probe can only be covered by a tile owning one of its adjacent cells, so this
also exhausts the candidates for probe obligations. Candidate nodes are shared
across all incident obligations, including gaps inside an already occupied
pair of cells.

Both seed tiles stay fixed. Branches use immutable placement snapshots and exact
rollback. An exhausted branch, a witnessed finite extension, and a budget stop
are distinct outcomes. This implementation rebuilds the complete graph after
moves; incremental dependency updates remain an implementation gap, as in the
existing Chair44 demo. No inflation positions, permitted-neighbor catalog,
arrow test, or known supertile is used to choose or reject a search move.

For radius $r$, the target contains every unit cell at face-adjacency distance
at most $r$ from the two seed tiles. Newly exposed cells and relief probes remain
active frontier obligations. A success covers the entire target and checks that
no active frontier point has degree zero. The initial budgets were $500$ search nodes and
$256$ tiles per pair and radius. A budget stop is **unknown**, and a retry uses
an explicitly recorded larger budget without reclassifying the stopped attempt.
This is finite extension testing, not a claim of covering all of space.

## Results

The root tile is fixed in one decorated orientation. Counts are distinct marked
placements relative to that root, without symmetry reduction.

- Relief-only non-overlap admits **128** face-adjacent neighbors.
- The full arrow rule admits **44** of those.
- Each of the **84 extra pairs** leaves an unfillable relief gap. Every pair has
  a recorded probe and its two already-occupied adjacent cells as a certificate.
- **14** of the remaining pairs fail elsewhere on the initial global frontier.
- **30** pairs pass that check and proceed to larger-neighborhood searches.

| Surrounding cell layers | Pairs extended | Tiles in witnesses | Seeds with one compatible parent | Seeds with complete parent present |
|---|---:|---:|---:|---:|
| 1 | 30 / 30 | 13–98 | 60 / 60 | 51 / 60 |
| 2 | 30 / 30 | 49–238 | 60 / 60 | 60 / 60 |
| 3 | 30 / 30 | 85–260 | 60 / 60 | 60 / 60 |

Every reported extension passed independent geometric replay and the global
frontier check. The $90$ witnesses passed $1{,}898{,}712$ rendered-profile height
comparisons. All also passed the full arrow rule when checked afterward.

One radius-three case, `4@1,-1,-1`, initially reached the $256$-tile budget.
It was retried with $1000$ nodes and $512$ tiles and succeeded at $260$ tiles
($263$ nodes). Its original **unknown** attempt remains in the record; it was
never treated as an exhausted branch. All other cases used the initial budget.


The arrow-rule check and supertile recognition are **post-search diagnostics**.
For recognition, all eight possible first-level parent positions/orientations
of each seed tile are enumerated. The audit counts complete eight-chair clusters
already present, and independently checks which parent hypotheses could fit the
whole patch without relief or cell-center overlap. Neither diagnostic is fed
back to the search.

## Interpretation and limits

Additional local non-overlapping fits do not by themselves disprove hierarchy
enforcement. Here they occur, but the occupancy algorithm rejects all additional
pairs through gaps that no third lattice-aligned tile can fill. The surviving
finite extensions obey the full arrow contacts and exhibit the reptile clusters
in the hierarchy audit. This supplies concrete computational evidence about the
relief, without using the arrow rule to guide the search.

The finite witnesses are not a new proof of infinite extension, unique global
tiling, or strong aperiodicity. In particular, the experiment does **not** certify
that a freely placed physical relief tile forces integer translations and cubic
orientations. Goodman–Strauss's discussion of the hierarchy and conversion to
bumps and nicks is in [Section 2 of the paper](https://arxiv.org/html/2609.24779v1#S2).

## Reproduction

```sh
node scripts/test-chair-relief-points.mjs
CHAIR_RELIEF_RADIUS=3 node scripts/run-chair-relief-search.mjs
CHAIR_RELIEF_MIN_RADIUS=3 CHAIR_RELIEF_RADIUS=3 CHAIR_RELIEF_RETRY_UNKNOWN=1 \
  CHAIR_RELIEF_NODES=1000 CHAIR_RELIEF_TILES=512 node scripts/run-chair-relief-search.mjs
node scripts/verify-chair-relief-search.mjs
```

The default output directory is `output/chair44-relief-search`; override it with
`CHAIR_RELIEF_OUT`. `CHAIR_RELIEF_NODES` adjusts the per-case node budget. To
resume an existing saved run at a later radius, set `CHAIR_RELIEF_MIN_RADIUS`;
completed cases at that radius are retained. `CHAIR_RELIEF_TILES` sets the tile
budget, and `CHAIR_RELIEF_RETRY_UNKNOWN=1` retries stopped cases while retaining
the previous attempts in the record. Timings in the raw files are
observations, not a performance comparison with the arrow solver.

The occupancy model is in [chair-relief-points.mjs](../../scripts/lib/chair-relief-points.mjs).
Saved counts, gap certificates, and hierarchy audits are in
[results.json](../data/chair44-relief-search/results.json). All raw finite placement
witnesses and that summary are in the [replay archive](../data/chair44-relief-search/witnesses.zip).
