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

`engine.js` owns tile geometry, candidate generation, exact placement legality,
periodic certificates, GCTS proposal learning, isohedral reuse, balanced growth,
and ordinary backtracking. The browser executes that same engine in
`solver-worker.js`.

## Solver modes

The UI exposes and compares exactly four solver lanes concurrently in
independent workers:

1. **Free-range** is the baseline tree search. It applies forced moves first,
   then explores the most sensible legal frontier placements with backtracking,
   growing in all directions without assuming periodicity or tile transitivity.
   Exact scoring ties are resolved by seeded randomness.
2. **GCTS** runs the same search while updating geometric
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

The interactive Plotly growth chart uses one wall clock for all four workers.
It records every tile-count transition, including downward backtracking steps,
instead of plotting only record highs. Geometry deltas are transferred in
200-ms batches and UI refreshes are coalesced to at most one every 300 ms, so
retaining the history does not force Plotly to redraw inside the solver's hot
loop. Clicking a marker on the lane selected by the strategy controls replays
that historical patch, the left and right arrows walk that selected lane's
history, and clicking empty chart space restores its current patch. The chart
and its legend cannot switch lanes; selecting a mode in the controls switches
the viewport to its latest patch without stopping the other searches.
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

The exhaustive complete-rank, delayed-nogood, and crystal-rank policies remain
available to the headless research and regression harnesses. They are not extra
public comparison lanes.

## GCTS learned proposals

The concurrent GCTS mode updates proposal priorities during the
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
finite-shell non-tilers, and no unresolved candidate. The research archive
retains all 27 selected controls: 25 periodic and two non-tilers. To keep the
interactive catalogue focused, it displays periodic controls only when their
certified quotient contains at least five tiles; smaller certificates remain
available to regression tests and command-line runs. Receipts are in
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
latter exhausts all 221,381 HNF quotients for every motif size from one through
fourteen copies, has an exact
radius-four corona, and leaves radius five incomplete. Its continuation solver
now learns sound dead-cell clauses: four seeded orderings accumulated 6,573
small placement nogoods and pruned 4,949,332 branches while requiring only 54
full radius-five continuation checks. The portfolio remains incomplete. See
`data/polycube-volume9-deep-screen-2026-08-20.json`,
`data/polycube-volume9-periodic-through13-2026-08-20.json`, and
`data/polycube-volume9-continuation-nogoods-2026-08-20.json`. The copy-fourteen
extension uses 52 audited HNF shards, exact dancing links, and the GF(2)
placement-span prefilter; it exhausts 51,870 new bases and 21,267,747 exact-cover
nodes without a certificate.

Radius five now also has an independent pseudo-Boolean formulation. Its Python
enumerator agrees exactly with the JavaScript solver on 481 target cells and
6,781 legal placements. On the positive radius-four control, generic Z3 needs
13.2 seconds while PB-to-bit-vector preprocessing plus the SAT tactic needs 1.5
seconds and returns a distinct independently verified 75-tile patch. At radius
five, generic SMT, the faster SAT encoding, and four randomized SAT restarts all
time out; a two-million-node GCTS restart likewise remains at depth 84. These
are independent bounded failures, not a non-tiling result. The combined receipt
is `data/polycube-volume9-copy14-multisolver-2026-08-21.json`; reusable entry
points are `scripts/screen-polycube-corona-restarts.mjs` and
`scripts/solve_polycube_corona_z3.py`.

The volume-ten funnel retains five free-isometry representatives. Exact HNF
quotient cover now excludes every translational fundamental domain through
thirteen copies for all five: 248,682 bases per representative cumulatively,
including all 39,711 thirteen-copy bases. Copy thirteen uses 60 explicit
half-open shards and exhausts 198,555 bases without a certificate or timeout.
The hardest achiral candidate, `p10-290795`, consumes 109,633,714 tree nodes
on the first half alone. On its second half, an exact GF(2) span prefilter
rejects 15,862 quotients algebraically; every remaining HNF fails before a
tree node is needed. A fail-closed campaign auditor checks the five expected
candidate keys, every visit count, and the gap-free range `[0,39711)` for each.
This is still only a finite-period exclusion, not evidence that any
representative tiles or is aperiodic. Receipts are
`data/polycube-volume10-periodic-copy12-2026-08-21.json` and
`data/polycube-volume10-periodic-copy13-2026-08-21.json`; reusable
interval and audit entry points are
`scripts/screen-3d-aperiodic-polycubes.mjs --periodic-hnf-start-index=... --periodic-hnf-end-index=...`
and `scripts/audit-polycube-periodic-shards.mjs`. The higher-level
`scripts/run-polycube-periodic-shards.mjs` computes the complete HNF count,
divides a requested range into deterministic half-open intervals, runs them
with bounded concurrency, reuses only shards that pass the single-interval
audit, and writes a final gap-free `audit.json` receipt.
`scripts/audit-polycube-periodic-campaign.mjs` then checks the expected
candidate set and aggregates those receipts without weakening their individual
range audits.

The same five candidates expose a useful proposal-ordering failure in GCTS.
Their original seven-order radius-three portfolio left all five unresolved. A
previously unused deterministic ordering, seed 7, finds and independently
verifies radius-three patches for `p10-054782` and `p10-055695` in 2,037 and
32,178 nodes, respectively. The witnesses use 45 and 47 surrounding tiles.
The other three seed-7 searches run for 600 CPU-seconds each without a witness
or exhaustion, so they remain inconclusive. Direct radius-four searches on the
two new survivors likewise time out after 600 CPU-seconds, at 1,912,832 and
3,885,056 nodes. This confirms that diverse proposal order is part of the
screen, while preserving the distinction between a finite witness, a finite
obstruction, and a timeout. See
`data/polycube-volume10-gcts-seed7-radius4-2026-08-21.json`.

Exact continuation changes the interpretation of those two saved patches. The
45-tile and 47-tile radius-three witnesses each have an immediate radius-four
obstruction. Continuation-guided outer searches then check eleven radius-three
states for `p10-054782` and fourteen for `p10-055695`; all twenty-five are rejected
with sound exact clauses, after which both outer searches time out. Thus the
displayed radius-three patches are verified finite survivors but known dead
ends, while the tiles themselves remain unresolved. See
`data/polycube-volume10-gcts-continuation-radius4-2026-08-21.json`.

For `p10-055695`, a pseudo-Boolean CEGAR supplier now broadens that continuation
sample without conflating it with the earlier portfolio. Forty-nine clause-distinct
radius-three proposals, using 41–47 surrounding copies, are all exactly rejected
at radius four in 62 aggregate continuation nodes. Every staged portfolio starts
with all preceding cuts, so the CEGAR states are mutually distinct. The final
≤41-copy run contributes nine dead states and one timeout; it does not exhaust
that bounded stratum. Each state exposes an immediate dead target and a
two-placement conflict; symmetry closure retains 98 sound clauses. In contrast, two eager
one-step-coverability proposal solves time out
without returning a state, including a staged 43-copy solve seeded with all 40
clauses. This favors cheap proposals plus lazy exact cuts for this candidate.
The radius-three space is still unexhausted, so the tile remains unresolved. See
`data/polycube-p10-055695-z3-cegar-radius4-2026-08-21.json`.

Continuation-guided GCTS now has an optional exact partial-patch filter. While
building a radius-L corona it maintains, for every radius-(L+1) ring cell, the
number of congruent placements still compatible with the selected tiles. A
zero count is a sound branch contradiction; a hitting set of the placements
that block every choice becomes an ordinary exact nogood. The index can be
activated only after a configured number of surrounding copies, because its
incremental maintenance is much more useful near complete patches than near
the root. On `p10-055695`, activation at 40 copies eliminates all fourteen
doomed complete proposals in the matched seed-7 run, makes 28 earlier prunes,
and preserves 92.6% of baseline node throughput. On `p9-42947`, activation at
60 copies likewise eliminates all 46 complete continuation calls but preserves
only 36.8% of baseline throughput; a 100-second run reaches depth 66 without a
radius-five witness. The filter therefore remains opt-in and thresholded. It
improves proposal rejection but exhausts neither finite outer search. Two fresh
`p10-055695` orderings add 4,985,856 outer nodes, 127 exact early prunes, and no
complete proposal or radius-four witness; the next bottleneck is supplying a
qualitatively different outer patch rather than rejecting the same local trap.
See
`data/polycube-corona-partial-next-layer-lookahead-ab-2026-08-21.json`.

Exact-cover row ordering now has three explicit profiles. `compact` preserves
the historical preference for covering more current-ring cells with less
exterior protrusion; `expansive` reverses those geometric preferences; and
`seeded` places the deterministic seed hash before them. The profiles preserve
the same search space and agree on every volume-at-most-four radius-two audit.
For `p10-055695`, neither alternative supplies a complete patch in matched
seed-7 and seed-10 windows where compact supplies fourteen, so compact remains
the default. For `p9-42947`, seeded profile seed 3 does reach a reproducible
79-copy radius-four boundary state distinct from the archived 75- and 78-copy
Z3 states. Its patch independently verifies, but exact radius-five continuation
rejects it in one node with a two-placement obstruction. Seeded restarts 11 and
12 add 8,602,624 nodes without another complete proposal. This is genuine
boundary-state diversification, but it finds another finite dead end rather
than an aperiodic tiling witness. The full patch and audit are in
`data/polycube-corona-placement-order-diversity-2026-08-21.json`.

The pseudo-Boolean supplier can now impose both minimum and maximum selected-
copy bounds. This makes high-copy strata explicit instead of relying on solver
luck, while UNSAT remains correctly scoped to the configured count range. A
staged and focused `p9-42947` runs produce twenty-two 79-copy, nine 80-copy,
and five 81-copy radius-four states. All 36 patches independently verify;
exact radius-five GCTS rejects them in 44 aggregate nodes and grows the
symmetry-closed cut set to 108 clauses. Nine lightweight solves time out.
Adding eager one-step coverability removes the immediate-dead-cell proposals,
but the original edge-CNF encoding's five 60-second solver attempts time out
without SAT or UNSAT. Thus the minimum bound materially broadens proposal
supply, while that eager encoding remains too expensive and the 79-plus-copy
space remains unexhausted. See
`data/polycube-p9-42947-high-copy-cegar-2026-08-21.json`.

Lazy single-cell obligations and grouped pseudo-Boolean conflict implications
now make that lookahead usable. On a matched 15-cell instance, grouping the
same 198,683 logical conflicts reduces asserted constraints from 200,044 to
5,342 and solve time from 23.4s to 14.3s. The grouped full model constrains all
180 next-ring cells with 4,533 conflict groups rather than 1,187,699 edge-CNF
implications. It finds 19 verified radius-four states with 66–72 copies; every
one avoids immediate dead cells and instead needs an exact resolved-subtree
radius-five proof. Those proofs total 74 GCTS nodes and reach nine nodes in
the best case. Lazy pair learning reaches 42 symmetry-expanded obligations;
prioritizing the pair that blocks the most current placement combinations
produces the nine-node state.
No radius-five witness is found and neither the outer space nor aperiodicity is
settled. The reproducible receipt is
`data/polycube-p9-42947-staged-coverability-2026-08-21.json`.

The next hierarchy now bootstraps all local distance-two pair obligations,
then learns the remaining global pairs and higher-order counterexamples. The
combined full-single-coverability portfolio contains 41 exact radius-four
states with 62–73 copies; radius-five rejection uses 208 aggregate GCTS nodes
and reaches 13 nodes in the deepest state. A cubic triple DNF exceeds two
330-second process limits, while the equivalent choice-CNF returns a 62-copy
proposal in 76.0s. Most importantly, an independently audited 72-copy state
has no incompatible pair and no incompatible triple anywhere on the 180-cell
next ring. It still fails exact radius-five continuation in nine nodes; the
first audited inconsistency is instead a diameter-six quadruple whose
1×1×3×11 choices give 33 blocked combinations. This raises the observed
finite obstruction order to four without proving non-tiling or aperiodicity.
See `data/polycube-p9-42947-higher-order-coverability-2026-08-21.json`.

The outer solver now expresses that audited quadruple exactly with four groups
of continuation-choice variables and pairwise non-overlap clauses. Preloading
its three-member root-symmetry orbit produces thirteen further verified
radius-four states with 60–72 copies. Every state again fails exact radius-five
GCTS, using 122 aggregate nodes and a new maximum of 28 nodes. The new patches
also correct an important completeness assumption: eight expose pair defects
not present in the previous 666-obligation formula, while five are pairwise
complete but expose new triples. The carried formula reaches 699 pair, 18
triple, and three quadruple obligations, but the last state still has a missing
pair. This is a stronger benchmark portfolio, not an exhausted hierarchy or an
aperiodicity result. See
`data/polycube-p9-42947-quadruple-coverability-2026-08-21.json`.

Complete per-state triple batching removes another avoidable outer-solver
loop. Across 16 trials, 12 exact outer states are found and all fail radius-five
GCTS. Six pairwise-complete states contribute 30 complete-audit triple orbits,
or 90 symmetry-expanded constraints, in six passes rather than one orbit per
proposal. The carried formula reaches 720 pair, 108 triple, and three
quadruple obligations. At that point three of the final four 360-second process
budgets expire; the next bottleneck is the monolithic outer proposal encoding,
not tuple-audit throughput. See
`data/polycube-p9-42947-batched-triple-coverability-2026-08-21.json`.

The higher-order obligations can instead be enforced lazily. In a matched
ablation starting from the same 336 clauses, 717 pair constraints, 108 triple
constraints, three quadruple constraints, and seeds 275–278, the monolithic
formula returns one proposal and times out three times. Encoding pairs while
auditing triples and quadruples after each proposal returns all four proposals
without a timeout. All four have exact tuple obstructions before GCTS. Eight
additional chained seeds likewise return eight exact tuple-defective states,
ending at 744 pair, 141 triple, and three quadruple constraints. This restores
proposal throughput but does not find a tuple-complete radius-four state; the
next useful experiment is a hybrid informative-triple encoding rather than
more undirected lazy restarts. See
`data/polycube-p9-42947-lazy-higher-coverability-2026-08-21.json`.

Hybrid enforcement identifies a narrow useful load point. Encoding one complete
triple orbit returns all four matched seeds with no timeout and reduces their
aggregate Z3 time by 15.7% relative to fully lazy enforcement. Encoding twelve
of the 36 available orbits times out on the first matched seed. Continuing the
one-orbit lane through seed 286 and a two-seed recent-orbit branch yields
thirteen exact proposals, six with pair defects and seven pairwise-complete
states with triple defects. The accumulated formula reaches 759 pair, 174
triple, and three quadruple obligations, but no state clears the full triple
audit. This makes a ranked adaptive orbit window or an incremental outer solver
the next optimization target. See
`data/polycube-p9-42947-hybrid-higher-coverability-2026-08-21.json`.

The next six exact proposals use persistent impact ranking: every learned triple
orbit keeps the largest observed number of candidate combinations it blocks,
and the one-orbit hybrid window selects the highest score. The selected orbit
changes from an unscored fallback to a 110-combination obstruction on the next
solve and survives a restart. Seeds 289–294 all return exact proposals, four
with pair defects and two pairwise-complete states with triple defects, growing
the formula to 771 pair, 207 triple, and three quadruple obligations. None
clears the full triple audit, and each outer solve still takes 186–325 seconds.
The result validates adaptive steering but makes repeated solver construction
the next bottleneck; it is not evidence of non-tiling or aperiodicity. See
`data/polycube-p9-42947-ranked-hybrid-coverability-2026-08-21.json`.

Verified smaller coronas can also be supplied as an optional proposal-ordering
hint with `--obstruction-preferred-corona-report=...`. Matching placements are
tried before other exact-cover rows, but are not fixed or assumed; every legal
row remains in the search, so a failed or stale hint cannot become a tiling or
non-tiling claim. The report records how many requested placements matched the
larger corona instance.
The continuation portfolio accepts `--budget-clock=cpu`, so per-seed and
per-continuation budgets remain comparable when exact screens run concurrently.

Continuation conflicts can now be resolved through nontrivial exact-cover
subtrees, not only extracted from an immediately dead target cell. Each child
conflict is resolved against its temporary placement; after every branch at a
pivot fails, the remaining conditions involve only ancestor or fixed outer
placements. A hexacube regression has no initially dead radius-two cell, yet a
two-node subtree reduces to three outer placements. Replaying only those three
placements independently exhausts the same radius-two cover. Budget-limited
runs never emit this certificate.

The first structural-forcing audit for `p9-42947` also guards against search-
order bias. A depth-first sample of 959,539 first coronas appeared to share four
placements, but exact forbidden-placement probes found alternatives for all
four. Extending the probe to every placement in a valid nine-tile baseline
corona found all nine replaceable, with each alternative independently checked
for congruence, non-overlap, forbidden-placement absence, and complete target
coverage. Thus no individual absolute placement is forced in the first corona;
forced disjunctions or larger clusters remain open. See
`data/polycube-volume9-corona-forcing-2026-08-20.json`.

At the coarser contact-type level, the candidate does have a nontrivial local
rule. Its 605 root-compatible placements form 69 face-contact types under the
root stabilizer. A counterexample-guided minimum-hitting-set loop accumulated
92 legal coronas. After excluding all 11 trivial single-cell coverage clauses,
it proved that six contact types are necessary and sufficient as a minimum
forced disjunction: every first corona uses at least one of them. Forbidding
their 36 placements exhausts in four nodes in each of eight seed replays. This
is a local compatibility constraint, not yet a substitution hierarchy. See
`data/polycube-volume9-contact-disjunction-2026-08-20.json`.

Reciprocal normalization shows why the six-state rule is insufficient by
itself. Of its 36 placements, nine remain active when viewed from the neighboring
tile: type 3 pairs with 44, and type 29 pairs with itself. Fixing representative
`3↔44` and `29↔29` contacts still permits exact radius-four coronas with 74 and
66 placements, respectively. These stable local cycles do not prove an infinite
tiling, but they rule out claiming that the six-state disjunction alone forces a
hierarchy. See `data/polycube-volume9-contact-propagation-2026-08-20.json`.

Conditioning the same rule on the contact seen by the neighboring tile produces
12 reciprocal incoming placement orbits. Exact radius-one searches and 753
subset-exhaustion trials give a dense graph with 134 possible orbit-to-orbit
edges. All nine inactive incoming orbits require another active contact, but
their minimum forced type set is only the full set of geometrically possible
outgoing types. More decisively, each of the three active incoming orbits has
an independently verified corona with no further active contact. The local
transition graph contains cycles, but it also has these terminating states, so
the six-contact rule cannot force an unbounded chain or hierarchy. Seeded
replays 0 and 7 agree exactly. See
`data/polycube-volume9-conditional-contact-transitions-2026-08-20.json`.

The next quotient keeps the complete exterior occupancy of a first corona
instead of reducing it to individual contact types. Four 1,000-state seeded
samples contained 2,522 distinct canonical boundary states; repeated states
always had the same exact continuation outcome. Of those distinct states,
1,922 cannot extend to radius two and 600 do extend. Every decision completed
within 41 continuation nodes. A separate on-demand learning run explained
2,070 boundary failures, accumulated 2,089 placement clauses, and used them to
prune 41,824 outer branches. The continuation portfolio now also memoizes
obstructed canonical boundary states across exact-cover leaves and seeds.
Blindly preloading shallow clauses into a radius-four run did not reduce its
node count and added overhead, so transfer is not enabled by default. See
`data/polycube-volume9-corona-boundary-states-2026-08-20.json`.

The same benchmark exposes a search-order phase transition. The first 100
radius-two states in each of four unlearned seeded traversals all fail before
radius three, although a radius-three witness is known. With on-demand
conflict learning, a 1,000-state run instead reaches 462 radius-three
survivors and records 9,365 prunes. At radius three to four, a 30-second learned
run still inspects 41 dead states and makes 10,100,253 prunes without reaching
the independently known radius-four witness. This is now an explicit proposal-
selection stress benchmark for GCTS, not evidence that radius four is absent.

A bounded direct-depth proposal now provides a sound escape hatch for that
ordering failure. It searches the next radius directly before enumerating
complete lower-radius leaves; success advances immediately, while an
incomplete attempt may transfer only exact learned clauses into the ordinary
continuation search. With a one-second cap it finds and independently verifies
the radius-four witness in 4,786 nodes and 139 ms, versus the nested benchmark's
30-second timeout. An equal-total-time radius-five ablation was negative: a
two-second proposal followed by ten seconds of outer search covered less work
than twelve seconds of outer search alone and found no radius-five witness.
The proposal phase therefore remains opt-in rather than silently consuming the
default search budget.

An adaptive profile caps that pilot at 250 ms. It still catches the radius-four
witness in 129 ms; on radius five it falls back after 270 ms and preserves
98.2% of the equal-total-time baseline's node coverage. This bounds the cost
but still does not improve the radius-five conclusion. A second exact
ablation closes every learned placement clause coherently under the root
stabilizer. At one million nodes it adds 1,820 symmetry clauses yet produces
essentially the same runtime, prunes, depth, and continuation checks. Symmetry
closure is therefore exposed only as an experimental switch and remains off
by default.

The independent pseudo-Boolean backend and GCTS can now run as a sound
counterexample-guided pair:

```bash
node scripts/screen-polycube-corona-z3-cegar.mjs \
  --id=p9-42947 --outer-layer=4 --inner-layer=5 \
  --iterations=50 --max-placements=64 --symmetry-clauses=true \
  --learn-cell-coverability=true \
  --lookahead-conflict-encoding=grouped-pb \
  --learn-pair-coverability=true --pair-orbit-limit=2 \
  --pair-selection=max-blocked-combinations \
  --bootstrap-pair-distance=2 \
  --learn-triple-coverability=true --triple-max-cell-distance=3 \
  --triple-audit-limit=32 --triple-orbit-limit=0 \
  --triple-encoding=choice-cnf \
  --learn-quadruple-coverability=true --quadruple-max-cell-distance=6 \
  --pair-encoding=witness-cnf --z3-formula-cache=true
```

Z3 proposes a complete outer corona; exact fixed-placement GCTS either extends
it or returns a proved obstruction clause. The loop never learns from a
timeout. Imported clauses make a final UNSAT result conditional until their
continuation proofs are independently replayed, and a copy-count bound can
only certify exhaustion of that bounded stratum. A low-copy radius-two to
three positive control recovers a verified witness after 17 dead proposals.
When continuation identifies an immediately unfillable next-ring cell,
`--learn-cell-coverability` adds that cell's full root-symmetry orbit as an
exact outer-solver obligation. This is stronger than its blocker clause but
much smaller than eagerly constraining the whole next ring. The `grouped-pb`
conflict encoding replaces one implication per conflicting outer/lookahead
placement pair with one equivalent pseudo-Boolean implication per outer
placement; `edge-cnf` remains available as the baseline. Pair learning can
retain the historical lexicographic order or prioritize the obstruction that
blocks the most or fewest currently available placement combinations. A
formula cache is available when the entire next layer is constrained. It
serializes the validated static exact-cover, grouped-lookahead, and accumulated
pair formula, then reloads it under each new solver seed; selected triple and
quadruple steering constraints and all forbidden-state clauses are still added
fresh. Cache metadata includes the complete pair-key set and every structural
encoding option, so a missing pair or changed configuration forces a rebuild.
On the 771-pair `p9-42947` benchmark this reduces measured construction from
57.0 seconds on a cache miss (including a 4.0-second write) to 3.6 seconds on a
no-change hit, before the same one-second timed check. This is formula reuse,
not a tiling inference or a persistent Z3 learned-clause state. See
`data/polycube-p9-42947-formula-cache-profile-2026-08-21.json`. A
positive `--bootstrap-pair-distance` adds every next-ring cell-pair obligation
within that Manhattan distance, closed under the root stabilizer, before the
first proposal solve. Once a proposal has no incompatible pair,
`--learn-triple-coverability` can learn a nearby incompatible cell triple.
`--triple-audit-limit` bounds how many counterexamples are collected from one
state, while `--triple-orbit-limit=0` admits every collected symmetry orbit;
each trial records whether the audit hit its bound.

Using that cache, the one-ranked-orbit lane returns five proposals from seeds
295–300 with one additional timeout. Four consecutive proposals pass all 771
carried pair obligations and fail only the exact full triple audit; the fifth
exposes one new pair orbit. The portfolio grows from 393 to 408 symmetry-closed
state clauses, 771 to 774 pair constraints, and 207 to 264 triple constraints,
with the three quadruple constraints unchanged. The narrowest returned state
has 63 copies and one incompatible triple orbit. A separate seed with the two
highest-scoring encoded orbits (scores 110 and 99) times out at 330 seconds.
No proposal clears the triple audit, so no radius-five continuation starts and
the finite outer search remains unexhausted. See
`data/polycube-p9-42947-cached-ranked-extension-2026-08-21.json`.
The default triple choice-CNF selects one available placement per cell and
forbids pairwise-overlapping selections, avoiding the cubic compatible-triple
DNF while expressing the same exact condition. Quadruple learning uses the
same exact choice-CNF construction across four cell groups after pair and
triple audits pass; `--initial-quadruple-report` can preload an independently
audited obstruction orbit.
When the higher-order formula itself becomes the bottleneck,
`--tuple-enforcement=lazy-higher` keeps pair obligations in Z3 but audits
triples and quadruples on each proposed state before GCTS. A failed audit adds
the symmetry orbit of the entire fixed outer state as a monotone separation
cut: adding more outer placements cannot restore a blocked continuation, so
the cut is sound. `lazy-all` also removes pair formulas; `encoded` remains the
default baseline. `hybrid-higher` plus a positive
`--encoded-triple-orbit-limit` encodes only that many complete root-symmetry
orbits from the accumulated triple set and audits every remaining triple and
quadruple lazily. The generated `encoded-triple-coverability.json` makes the
actual steering subset explicit and resumable. The optional
`--encoded-triple-selection=recent` window follows newly learned obstruction
orbits instead of permanently retaining the earliest ones. The
`max-blocked-combinations` policy records the largest observed number of
currently available placement triples eliminated by each obstruction orbit,
persists those scores beside `triple-coverability.json`, and encodes the
highest-scoring complete orbits. Ties prefer newer observations.
For `p9-42947`, 284 radius-four proposals are now exactly rejected at radius
five, including fifteen 63-copy states and one 62-copy state. An exact one-step coverability filter
removes immediate dead cells before proposal; its four satisfiable patches all
require resolved-subtree conflicts. Pairwise coverability then promotes two
more proposals to five-node continuation proofs and learns 114 symmetry-closed
cell-pair obligations; the full 114-pair formula remains timeout-inconclusive.
A factored witness-CNF encoding replaces the 322,977 compatible-pair DNF terms
with 8,208 local witness choices. Under an equal 60-second solver budget it
finds a new 63-copy proposal where both the DNF and two-sided choice-CNF
encodings time out. Across the extended witness-CNF portfolio, two 63-copy
proposals are exactly rejected at radius five in two and four GCTS nodes. After
eight earlier 62-copy attempts timed out, the same encoding finds a 62-copy
proposal; exact GCTS rejects it in eleven nodes. The exact clause set grows to
807. Two 61-copy runs remain timeout-inconclusive. An exact lex leader under
the three-element proper-rotation stabilizer removes equivalent proposal
orbits but does not improve the 61-copy result, so it remains optional.
The same obligations now run lazily inside continuation-guided GCTS. Two fixed
production states independently replay their extracted pair clauses; the
smaller clause uses four placements instead of the exact continuation proof's
seven and blocks 2,288 mutually compatible next-ring placement pairs. A
5,000,000-node seeded A/B run is neutral: both searches remain incomplete and
all 46 newly encountered continuation failures have simpler immediate-cell
obstructions, so pair lookahead is never invoked on the live branch.
Radius four remains unexhausted. See
`data/polycube-volume9-z3-cegar-2026-08-21.json`.

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
