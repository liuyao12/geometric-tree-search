# 3D Lattice Tiler

A standalone, generic lattice-tiling playground derived from the polyhedron
catalog in the original Observable notebook:

https://observablehq.com/@liuyao12/3d-lattice-tiler

Run it from the repository root with any static server:

```bash
python3 -m http.server 5174
```

Then open:

```text
http://127.0.0.1:5174/3d-lattice-tiler/
```

There is no GCTS runtime in this app. `engine.js` owns tile geometry, candidate
generation, exact placement legality, periodic certificates, isohedral reuse,
balanced growth, and ordinary backtracking. The browser executes that same
engine in `solver-worker.js`.

## Solver modes

The UI exposes four solver families and runs eight comparison lanes concurrently
in independent
workers:

1. **Free-range** is the baseline tree search. Its balanced and no-brainer move
   orders run as separate comparison lanes, so long growth cannot be mistaken
   for a heuristic-independent result. It applies forced moves first,
   then explores the most sensible legal frontier placements with backtracking,
   growing in all directions without assuming periodicity or tile transitivity.
   Exact scoring ties are resolved by seeded randomness.
   A separate **Proof search · complete rank** lane removes the generational
   frontier band and heuristic branch caps. It branches over every legal tile
   that can be attached through any exposed face and memoizes exact failed
   placement sets. A temporarily stranded frontier vertex is diagnostic only:
   growth elsewhere can expose a later continuation, so it is neither a dead
   end nor evidence that its current sole candidate is forced. Reaching the
   requested tile count is still only a finite-patch witness; only exhausting
   this global face-extension search before that count certifies that no
   connected patch of that size exists in the configured face-to-face lattice
   model. A time or node limit remains inconclusive. Node limits count applied
   placements, never unvisited alternatives allocated for the tree UI.
2. **Learning Free-range** runs the same search while updating geometric
   proposal priorities from successful and failed branches. Its best legal
   patch is stored per tile in the browser and revalidated on later runs, so
   repeated comparisons improve without hard-coding a translational or
   isohedral strategy.
3. **Translational** progressively checks increasingly large motifs using an
   exact finite-quotient (3-torus) cover test. It succeeds only when translated
   copies of the certified whole patch tile 3-space. Certified translation
   motifs may contain multiple orientations and multiple prototile species.
   Polycubes use a lattice-cell exact cover fast path; general lattice
   polyhedra use connected motif enumeration followed by exact boundary-face
   pairing, a rank-3 period-lattice check, and equality of motif volume and
   lattice covolume.
   Certified translation
   cells use an RGB parity code applied relative to each motif tile's assigned
   base color: moving by the first period vector changes red by 128 modulo 256,
   the second changes green, and the third changes blue. Thus a multi-tile unit
   patch keeps its individual tile colors while each tile exposes eight
   directional variants across translated copies.
4. **Isohedral** treats every tile as an image of the root tile. Each
   root-to-tile rigid motion lifts, rotates, and translates the entire known
   patch onto that tile; exact duplicates are skipped and a patch image is
   committed only when every new tile is legal. A single successful neighbor
   relation can therefore generate first, second, and later surroundings very
   quickly. Forced patch images and searched relations must touch the oldest
   active frontier layer before newer layers may advance; balanced rank-3
   growth breaks ties and is required for count targets. Reaching a finite
   tile-count horizon is not success: the lane mines a rank-3 periodic
   quotient from the patch, pairs every quotient face, checks volume against
   lattice covolume, and verifies symmetries carrying the root tile to every
   tile class. Without that certificate the result is exhausted or
   inconclusive and the displayed patch rolls back to the root.

The interactive Plotly growth chart uses one wall clock for all six workers.
Every plotted sample retains its exact 3D snapshot: clicking a marker replays
that historical patch, while clicking empty chart space restores the latest
patch for that marker's mode. Selecting a mode also switches the viewport to
its latest patch without stopping the other searches.
An exhausted isohedral search drops to zero and restores the root view. An uncertified translational search
continues increasing the motif size until certified, stopped, or limited by an
explicit search cap.

The lower-level API uses `generic` internally and retains `freestyle` as a
backward-compatible alias of `free_range`. It also retains `auto` for regression
and research use. No strategy makes decisions from catalog names. Candidate
generation matches oriented faces, checks lattice solid-angle occupancy,
rejects overlaps, and requires a full 3D attachment.

Every mode keeps explicit frontier layers and prioritizes the oldest active
layer. Within a layer, balanced growth first establishes three independent
directions, then maximizes the ratio between the shortest and longest center
spans. Periodic motifs are consumed in centered cell shells, avoiding long
one-dimensional tendrils. The viewport renders the active frontier lattice
points for the selected Z³, FCC, or ½Z³ tier.

## Learned proposals

The concurrent Learning Free-range mode updates proposal priorities during the
active search. The reusable headless trainer additionally evolves tile-specific
proposal programs. A program may contain an ordered cycle of move-scoring
stages plus the complete locally legal patch discovered by its best episode.
On reuse, the engine revalidates and replays that patch relative to the initial
tile, then returns to ordinary backtracking when the patch ends or no longer
fits. The learner can therefore discover a translational-looking sequence for
one tile, an isohedral-looking neighborhood for another, or a different patch
without switching to either human baseline.

Offline training refines the winning patch in expanding-horizon rounds. Each
round replays the known prefix, spends progressively more time extending it,
and finally measures the completed proposal again at the original inference
horizon. Training time is therefore not confused with the tiles-versus-time
curve for reusing the learned construction.

For repeatable headless training:

```bash
node scripts/learn-3d-proposals.mjs --modes cube,1_cross,gyrobifastigium
node scripts/benchmark-3d-proposal-catalog.mjs --modes=cube,hex_prism,trunc_oct,gyrobifastigium
```

Terminal results distinguish evidence strength. `certified_tiling` means the
engine has an exact translational quotient certificate or an exact finite
region fill. `patch_found` means it found a locally legal finite patch; that is
useful search evidence, but is not presented as proof that all of 3-space can
be tiled. Bounded searches that exhaust their limits report
`search_incomplete` or `no_tiling_found` rather than a false certificate.

## Finite regions

Set `criterion: "region"` and pass `target_region`. Every candidate must lie
inside the region, and success requires the placed tile volumes to equal the
region volume.

```js
{
  criterion: "region",
  target_region: {
    type: "box",
    center: [3, 2, 1.5],
    size: [6, 4, 3]
  }
}
```

The core also accepts spheres and convex halfspace regions. A halfspace region
must include its exact volume:

```js
{
  type: "halfspaces",
  center: [0, 0, 0],
  volume: 8,
  planes: [
    { normal: [ 1, 0, 0], offset: 1 },
    { normal: [-1, 0, 0], offset: 1 },
    { normal: [0,  1, 0], offset: 1 },
    { normal: [0, -1, 0], offset: 1 },
    { normal: [0, 0,  1], offset: 1 },
    { normal: [0, 0, -1], offset: 1 }
  ]
}
```

The UI exposes exact centered boxes. Other region types are available to
headless callers and future UI panels.

## Catalog and custom tiles

The catalog keeps the old app's systems and deduplicated figures, including
polycubes, the five Fedorov solids, tetrahedral/octahedral systems, space
fillers, Laves and perovskite systems, and Barlow/FCC/HCP cells.

Convex monohedral systems also receive a necessary edge-angle check. When no
combination of matching edge dihedral angles can close to `2π`, the engine
returns `result_kind: "no_tiling"`, `can_tile: false`, and a
`local_edge_obstruction` certificate instead of treating a failed bounded
search as a proof.

Custom systems accept voxel unions and convex integer-lattice polyhedra:

```js
custom_system: {
  name: "My lattice solids",
  polycubes: [{ name: "Domino", voxels: [[0, 0, 0], [1, 0, 0]] }],
  polyhedra: [{
    name: "Lattice tetrahedron",
    vertices: [[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2]]
  }]
}
```

Coordinates must be integers. Explicit faces are optional; when supplied they
must form a closed convex shell.

## Regression checks

```bash
node scripts/test-3d-balanced-growth.mjs
node scripts/test-3d-strategies.mjs
node scripts/test-3d-isohedral-certificates.mjs
node scripts/test-3d-proposal-learning.mjs
node scripts/test-3d-translational-polyhedra.mjs
node scripts/test-3d-general-translational-motif.mjs
node scripts/test-3d-mixed-periodic.mjs
node scripts/test-3d-custom-polyhedron.mjs
node scripts/test-3d-region.mjs
node scripts/audit-3d-catalog.mjs --quick
node scripts/audit-3d-catalog.mjs --strict
```

To repeat the resource-bounded screen of the original 16 census candidates:

```bash
node scripts/rescreen-lattice-polyhedra.mjs --time-ms=20000 --periodic-max=8 --isohedral-target=60
```

`--isohedral-target` is the proof-search horizon. `--display-target` may be set
independently to stress the preview path; changing it must not change whether
an exact isohedral quotient is discovered. Runtime statistics report the proof
horizon, certificate-attempt patch sizes, successful certificate patch size,
and the maximum number of simultaneously live tiles. Failed quotient checks
are memoized by the exact live placement set, so different move orders do not
repeat the same expensive certificate calculation.

For a repeatable control-plus-survivor matrix:

```bash
node scripts/benchmark-lattice-candidate-suite.mjs --target=24 --time-ms=1000 --exact-time-ms=3000 --seeds=1,2,3
```

The suite gates a two-tile translational control, the 24-tile isohedral
`10_27010` control, a certified local non-tiler, and the known Conway
construction before reporting all five unresolved candidates. Each survivor
runs translational, isohedral, balanced free-range, no-brainer free-range, and
unbanded proof lanes, with live-patch depth, frontier size, tree effort,
certificate work, and duplicate quotient reuse in the JSON result. The
heuristic portfolio summary separates
robust target growth (every policy/seed trial), policy- or seed-sensitive
growth (only some trials), and bounded runs where no trial reaches the target;
none of these bounded growth labels is treated as a tiling proof. Unresolved
candidates run all three free-range lanes under three deterministic seeds by
default, and every row
records its effective seed plus whether it stopped at the node limit, time
limit, natural exhaustion, or the requested target. Use `--node-limit=N` to
hold the tree-work cap fixed across machines and `--seeds=...` to expand or
reduce the stability sample. A separate unbanded lane disables the generation
lag heuristic: only that branch-complete lane may turn exhaustive failure to
reach the requested patch size into a certified finite-patch obstruction.
Banded failure is explicitly inconclusive because deferred legal moves were
not searched. Its separate proof-search portfolio reports robust, median, and
best patch depth across seeds, plus the number of independently completed
non-tiler certificates. The unbanded lane memoizes canonical failed placement
sets, so commuting placement orders share one exact dead-state proof. Rows
report memo states, hits, and capacity; use `--failure-memo=false` for an
ablation or `--failure-memo-max-states=N` to control memory without pruning the
search.
Use `--lanes=free_range_unbanded` to isolate that proof lane for longer runs
or memoization ablations.
The compatibility lane name remains `free_range_unbanded`; its current default
move order is `global`, and it sets `generic_connected_patch_enumeration`.
Use `--connected-patch-enumeration=false` only to replay the superseded
instantaneous vertex-MRV heuristic for historical ablations; such a run cannot
produce a finite-patch obstruction certificate.

As an opt-in work-budget experiment, the proof lane can also record each fully
failed patch as translation-
equivariant geometric nogoods anchored at every tile. A clause retains the
entire failed context and therefore prunes only exact translated subpatches,
not radius-truncated or statistically generalized neighborhoods. Enable it
with `--geometric-nogood=true`, compare against the default off arm, and use
`--geometric-nogood-max-clauses=N` for its independent memory cap. Clause
matching uses an exact rare-token pivot index; `--geometric-nogood-index=false`
runs the same clauses through the reference linear scan for a semantic and
performance ablation. Translation-equivariant clauses are automatically
disabled for finite target regions, where moving a failed context can change
its relationship to the boundary. Use
`--geometric-nogood-activation-failures=N` to learn clauses immediately but
delay applying them until `N` failed states have accumulated; a threshold
larger than the run preserves the baseline path while still auditing the
learned clause set.
Use `--geometric-nogood-stagnation-failures=N` to test a one-way adaptive
variant that activates learned clauses only after `N` encoded failures without
increasing the captured maximum patch size. This is an experimental control,
not the web proof-lane default.

The following vertex-MRV and nogood comparisons are retained as historical
heuristic diagnostics. They were run before the global-extension and node-
accounting correction described below and must not be read as proof-search
depth comparisons. The four-candidate, three-seed A/B did not support replacing the baseline
proof order with nogoods: five paths deepen, one ties, and six become
shallower. It does support a complementary proof lane. The second policy finds
a new checked 40-tile witness for `10_45033`, and its 1,109 completed quotient
checks add 823 proper-rigid-motion patch geometries to the baseline union. The
combined two-policy screen covers 1,874 distinct checked patches with no
timeout or periodic certificate. The full paths, fingerprints, and policy
decision are archived in
`data/lattice-polyhedron-nogood-proof-portfolio-2026-08-19.json`; the web
comparison exposes the two proof policies as separate traces.

A follow-up activation sweep tested 25, 50, and 100 failed states. Threshold
25 weakly dominated immediate nogood application on all 12 paths: two paths
deepened and ten tied, with no regression. It produced two independently
hashed 40-tile `10_45033` witnesses, both rejected as translational quotients.
Its 1,116 exact checks completed without timeout or periodic certificate and
added 199 rigid-motion geometries beyond the earlier two-policy union, for
2,073 checked geometries across all three policies. The web proof-nogood trace
now uses this delayed policy. Milestone curves and exact fingerprints are in
`data/lattice-polyhedron-delayed-nogood-screen-2026-08-19.json`.

Five unseen seeds (4 through 8) then tested whether that three-seed result
generalizes. Delayed-25 beat immediate nogoods on 5 of 20 paths, tied 14, and
worsened 1, so it is not a universal dominance result. It nevertheless found
two 40-tile witnesses versus one for immediate nogoods and one for baseline.
Exact hybrid checking replayed all 60 policy paths without changing them:
5,540 checks completed with no timeout or certificate. The holdout contributed
2,758 new rigid-motion geometries and raised the eight-seed, three-policy union
from 2,073 to 4,831. Full milestones and fingerprints are archived in
`data/lattice-polyhedron-holdout-screen-2026-08-19.json`.

An adaptive stagnation gate was then tested as a possible replacement for the
fixed 25-failure delay. Thresholds 10, 25, and 50 improved no training policy
overall; stagnation-10 was least harmful but improved 0 of 12 training paths
and worsened 1. On the five-seed holdout it improved 0 of 20 paths, tied 16,
worsened 4, and reached one 40-tile target versus two for fixed delayed-25.
The option remains available for controlled experiments, but the live proof
lane retains fixed delayed-25. The complete negative ablation is archived in
`data/lattice-polyhedron-stagnation-nogood-ab-2026-08-19.json`.

All regenerated summaries distinguish a captured witness from a transient
engine peak at a work-budget boundary. `largest_patch` and `witness_hash`
always refer to the last emitted placement snapshot; `max_live_tiles` retains
the uncaptured peak for diagnostics.

A subsequent controlled budget-and-order screen raised the target to 60 tiles.
Balanced MRV weakly deepened every training path when its budget increased
from 1,000 to 2,000 nodes, raising target hits from one to four; all four exact
target-patch quotient checks completed without a certificate. At 1,000 nodes,
MRV was the only tested frontier order to reach 60 tiles and its median depth
of 32 was well above pocket (15), constrained (16), and coverage (18), so MRV
remains the frontier default. The benchmark accepts `--face-order=...` to
replay that control.

Holding MRV fixed, crystal move ordering beat balanced on 8 of 12 training
paths and 13 of 20 unseen holdout paths. Across all eight seeds it improved 21
paths, worsened 11, and raised 60-tile target hits from one to seven. Its gain
is candidate-specific: `10_45026` reaches 60 tiles in four of eight paths as
two distinct witnesses, while `9_11683` still favors balanced on six of eight.
All eight selected balanced/crystal target checks completed without timeout or
translational certificate. Crystal is therefore added as an eighth,
complementary proof-search trace rather than replacing balanced MRV. Replay it
from the benchmark with `--unbanded-move-order=crystal`; full milestones and
proof receipts are archived in
`data/lattice-polyhedron-budget-order-screen-2026-08-19.json`.

That tile-count result exposed a dimensional blind spot. Retrospective
translation-overlap analysis showed that all four 60-tile `10_45026`
witnesses repeated 57 placements along one vector: a few off-axis starter
tiles made the patch formally three-dimensional while most growth was still a
single limb. The current crystal policy therefore prioritizes gains in the
linear rank of repeated, same-orientation translation vectors, rather than the
affine rank of tile centers.

The generic GCTS proof hook now also looks inside a reached patch for a smaller
periodic motif. It ranks observed translations by support, enumerates up to 48
candidate vectors, reduces placements to cosets for each independent basis,
and accepts only an exact face pairing whose motif volume equals the lattice
covolume. This recovered the known three-tile quotient of control `10_24775`
on the first tested basis. A focused rank-aware run produced a 60-tile
`10_16113` witness with repeated-translation rank 3; all 9,139 candidate bases
were rejected without timeout, and its strongest translation occurred only
five times. This excludes periodic motifs exhibited by that finite witness,
not every possible periodic tiling of the tile. The eight-seed five-second
breadth screen, focused receipt, old-witness diagnostics, and positive control
are archived in
`data/lattice-polyhedron-internal-period-screen-2026-08-19.json`; regenerate
the archive with `scripts/analyze-lattice-internal-period-screen.mjs`.

A correctness audit then found two independent causes of artificially shallow
proof paths. The solver had treated any incomplete frontier vertex with no
immediate candidate as a dead end and its current sole candidate as forced,
even though a tile attached through another exposed face can create a later
continuation there. It also charged the node budget when it allocated IDs for
every displayed alternative, before those alternatives were visited. The
complete proof lane now enumerates the union of all legal exposed-face
extensions and counts only placements actually applied.

Under that corrected search, all four unresolved candidates reached 60 tiles
in all three seeds: 12/12 target hits, nine distinct witnesses, no backtracking,
and rank 3 in both geometric spans and repeated same-orientation translations.
All 12 exact target checks completed without timeout or periodic certificate;
the embedded-motif miner rejected 148,471 candidate period bases. This sharply
strengthens the evidence that the candidates support large genuinely 3D local
patches, while remaining only finite evidence rather than a proof of tiling or
aperiodicity. The full receipts are in
`data/lattice-polyhedron-global-extension-screen-2026-08-19.json`; validate
them with `scripts/analyze-lattice-global-extension-screen.mjs`.

Connected-patch size was still the wrong discriminator: a patch can extend
through easy faces while permanently ignoring an unfillable face near the
root. The exact **complete-shell** lane instead recomputes shortest
face-adjacency distance from the root for every current patch. To complete
shell `r`, every exposed face owned by a tile at distance less than `r` must be
covered. It prioritizes the oldest face-adjacency generation, applies MRV
within that generation, and prunes a
state immediately when *any* exposed face has no legal mate. This is sound in
the configured face-to-face proper-lattice model: a future placement elsewhere
cannot create a new mate for an already fixed face; it can only invalidate a
current mate. Exact search uses raw geometric validity for these face-mates,
not the finite-growth heuristics used by the preview lanes.

The original sampled-solid-angle screen rejected `10_16113`, `10_45026`, and
`9_11683` before an indefinitely extendable first shell. Exact convex overlap
confirms the latter two obstructions, while `10_16113` completes shell 1 with
nine tiles. A follow-up exact shell-2 run exhausts the full 50-node tree under
full cubic isometries, with failure memoization and zero-face pruning disabled;
three seeded traversal orders produce the same obstruction. Thus `10_16113` is
a compact non-tiler control, despite a 60-second translational run completing
motif sizes 1–5 and a 30-second isohedral preview reaching 72 tiles before
their respective limits. `10_45033` reaches shells 1–4 in all
three direct runs, shell 5 in one of three, then reaches shells 6 and 7 by
validated checkpoint continuation (764 and 1,174 tiles). Mining the shell-7
witness reveals an exact six-tile translational quotient with period vectors
`(-2,-2,2)`, `(0,-1,3)`, and `(-3,0,1)` and determinant 14. The quotient
replay pairs all 54 motif faces modulo that lattice and matches motif volume
to covolume, so `10_45033` is periodic and the former four-tile candidate pool
has one corrected survivor. The receipts are in
`data/lattice-polyhedron-extendable-shell-screen-2026-08-19.json`,
`data/lattice-polyhedron-10_45033-shell-continuation-2026-08-19.json`, and
`data/lattice-polyhedron-10_45033-periodic-certificate-2026-08-19.json`.
The corrected `10_16113` receipts are the `corrected-shell1`,
`corrected-periodic-screen`, `corrected-isohedral`, and final
`corrected-shell2-nontiler` reports.
Regenerate the direct screen with
`scripts/screen-lattice-complete-shells.mjs --target=5 --cascade=true`, and
validate it with `scripts/analyze-lattice-complete-shell-screen.mjs`.

The next census pass enumerates all 156,464 size-11 Blanco–Santos lattice
polytopes from the 16 published source parts. An exact local-edge filter rejects
156,400, and exhaustive extendable-shell-one search rejects another 56, leaving
only eight first-shell witnesses and no bounded-search timeouts. The old
sampled-solid-angle search incorrectly rejected `11_34718` and `11_34757` at
shell 3. Under exact convex overlap both reach shell 3 immediately and have
two-tile translational quotients; the other six have replayable quotients of
2–5 tiles. Thus the entire size-11 survivor pass is resolved as eight periodic
tilers and zero aperiodic candidates. The first-stage, historical shell, and
quotient receipts are
`data/lattice-polyhedron-size11-first-stage-2026-08-19.json`,
`data/lattice-polyhedron-size11-shell3-2026-08-19.json`, and
`data/lattice-polyhedron-size11-periodic-summary-2026-08-19.json`.
Regenerate the census shards with `scripts/screen-next-lattice-polytope-pool.mjs`,
merge them with `scripts/merge-next-lattice-polytope-screens.mjs`, and pass the
merged report to `scripts/screen-lattice-complete-shells.mjs --candidates-file=…`.

The size-12 pass uses the complete 503,443-record polyDB collection
`Polytopes.Lattice.FewLatticePoints3D`. Exact local-edge checks reject 503,353
representatives. The corrected full-isometry, unpruned shell-one search rejects
25 more and leaves 65 witnesses with no timeouts. Quotient certificates now
undergo a complete neighboring-cell audit. Polycubes use exact discrete
occupancy; convex lattice polyhedra use a separating-axis interior-overlap
test, avoiding false rejections from numerically approximated solid angles.
Of the 65 witnesses, the corrected easy lanes initially
certify 54 periodic quotients. The historical sampled-angle shell pass rejected
eight of the remaining eleven; the corrected convex rescreen retains only two
of those obstructions. Shell-6 GCTS patches then expose overlap-validated
translational quotients for `12_204255` (8 tiles) and `12_405129` (24 tiles).
The last survivor, `12_235174`, is a triangular prism. The earlier solid-angle
audit overestimated one vertex total as 48.097 against an exact value of 48;
the convex audit instead certifies its two-tile parallelepiped cell with period
vectors `(-1,0,0)`, `(-2,-1,5)`, and `(-2,1,5)`. The same correction recovers
two-tile quotients for six shapes previously misclassified by shell search.
The corrected size-12 result is therefore 63 periodic tilers, two exact
finite-shell non-tilers, and no unresolved candidate. The catalogue retains all
27 selected controls: 25 periodic and two non-tilers. Receipts are in
`data/lattice-polyhedron-size12-full-isometry-first-stage-2026-08-20.json`,
`data/lattice-polyhedron-size12-full-isometry-shell2-2026-08-20.json`, and
`data/lattice-polyhedron-size12-full-isometry-easy-lanes-2026-08-20.json`, with
the deeper shell receipts in the corresponding `shell3`, `shell4`, and `shell6`
reports and the three extracted quotient receipts in the
`12_204255-shell6-periodicity`, `12_405129-shell6-periodicity`, and
`12_235174-periodic` reports, plus the combined `corrected-convex-periodic-rescreen`
and `corrected-convex-shell2-nontilers` receipts. Before the final prism certificate, seeds 1–20
had produced 20 distinct 49-tile shell-3 witnesses; each tested witness had an
exact shell-4 extension obstruction and the internal-period checker tried
303,583 bases without recognizing the smaller cell. Those historical receipts
remain useful GCTS stress tests under the `12_235174-shell3-portfolio`,
`shell4-extension-portfolio`, and `shell3-periodicity-portfolio` filenames.
For sizes 12–15, `scripts/screen-next-lattice-polytope-pool.mjs` downloads
bounded aggregate pages from polyDB and records contiguous source ranges and
SHA-256 receipts; the merge script refuses gaps and overlaps.

The complete size-13 pass covers all 1,502,640 polyDB representatives without
a source gap or search timeout. A geometry-only exact edge-angle preflight
rejects 1,502,508; exhaustive shell-one search rejects 39 more and leaves 93
witnesses. The easy lanes certify 88 translational quotients and two additional
eight-tile quotients found only by the isohedral lane. The remaining three
(`13_0492735`, `13_1072824`, and `13_1429971`) make useful GCTS stress tests:
both bounded easy lanes are inconclusive, but three independent unpruned
full-isometry searches exhaust identical root trees and prove shell 2
impossible. Thus this census also closes with no unresolved aperiodic
candidate. The catalogue keeps `13_0635270` as the isohedral-lane regression
and the first two hard non-tilers as compact tree-search controls. A
translation-normalized oriented-face index preserves those exact trees while
reducing `13_0492735` face-match attempts from 1,851,648 to 27,844 per trial.
The receipts are
`data/lattice-polyhedron-size13-full-isometry-first-stage-2026-08-20.json`,
`data/lattice-polyhedron-size13-full-isometry-easy-lanes-2026-08-20.json`, and
`data/lattice-polyhedron-size13-full-isometry-shell2-2026-08-20.json`.

The one-sided polycube census now extends through volume nine. The first pass
certified 48,260 of 48,311 shapes with motifs through six copies. A deeper
eight-copy pass resolves two more, `p9-43172` and its enantiomer `p9-43188`,
with an exact 8-tile quotient. The webapp independently replays that quotient;
doing so exposed and fixed a concave-volume bug that had caused the
Translational lane to reject valid nonconvex polycube certificates. The four
original catalogue entries are two mirror pairs, so the catalogue now keeps
one exact periodic regression (`p9-43172`) and one genuinely distinct bounded-
inconclusive representative (`p9-42947`, mirror-equivalent to `p9-42969`). The
latter exhausts all 46,730 HNF quotients through eight copies, has an exact
radius-four corona, and leaves radius five incomplete. See
`data/polycube-volume9-deep-screen-2026-08-20.json`.

The checked-in 2026-08-17 result, including every exact rejection certificate
and the five unresolved survivors, is in
`data/lattice-polyhedron-rescreen-2026-08-17.json`.

The follow-up unbanded GCTS proof portfolio is archived in
`data/lattice-polyhedron-proof-screen-2026-08-18.json`. It fixes the target at
40 tiles, the configured node limit at 500, and seeds at 1, 2, and 3.
Candidate `10_26470` reaches the 40-tile target in every trial; the other four
retain robust largest patches between 21 and 25 tiles before the node limit.
All five conclusions remain inconclusive: a finite patch is not a space-tiling
certificate, and a node-limited run is not a non-tiler certificate.

The original rescreener and its regression archive still share the same
16-entry runtime pool in `assets/lattice-polyhedron-survivors.js`; the public
catalog now combines that pass with the fully screened size-11 and selected
size-12 controls. Regression tests verify all three groups so a removed tile
cannot silently reappear. Each run also reports `largestPatch`, maximum
frontier size, and maximum candidate count.
These effort fields preserve how long an unresolved search stayed alive even
though isohedral failure correctly rolls the displayed terminal state back to
the seed. A certified local obstruction is classified as
`reject_certified_non_tiler`; a timeout or finite motif cap remains
`inconclusive`.

The strict audit covers every registered system and every deduplicated catalog
figure. It distinguishes exact certificates, certified local obstructions,
completed layer patches, balanced finite patches, and unresolved bounded
searches; strict mode fails if any system or figure remains unresolved.
