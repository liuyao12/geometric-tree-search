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

The UI exposes four modes and can run all four concurrently in independent
workers:

1. **Free-range** is the baseline tree search. It applies forced moves first,
   then explores the most sensible legal frontier placements with backtracking,
   growing in all directions without assuming periodicity or tile transitivity.
   Exact scoring ties are resolved by seeded randomness.
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

The interactive Plotly growth chart uses one wall clock for all four workers.
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

The checked-in 2026-08-17 result, including every exact rejection certificate
and the five unresolved survivors, is in
`data/lattice-polyhedron-rescreen-2026-08-17.json`.

The rescreener and the public catalog consume the same 16-entry runtime pool in
`assets/lattice-polyhedron-survivors.js`; regression tests compare that pool to
the archived report so a removed tile cannot silently reappear. Each run also
reports `largestPatch`, maximum frontier size, and maximum candidate count.
These effort fields preserve how long an unresolved search stayed alive even
though isohedral failure correctly rolls the displayed terminal state back to
the seed. A certified local obstruction is classified as
`reject_certified_non_tiler`; a timeout or finite motif cap remains
`inconclusive`.

The strict audit covers every registered system and every deduplicated catalog
figure. It distinguishes exact certificates, certified local obstructions,
completed layer patches, balanced finite patches, and unresolved bounded
searches; strict mode fails if any system or figure remains unresolved.
