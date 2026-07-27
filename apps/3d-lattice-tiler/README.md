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
http://127.0.0.1:5174/apps/3d-lattice-tiler/
```

There is no GCTS runtime in this app. `engine.js` owns tile geometry, candidate
generation, exact placement legality, periodic certificates, isohedral reuse,
balanced growth, and ordinary backtracking. The browser executes that same
engine in `solver-worker.js`.

## Solver modes

The UI exposes three distinct modes:

1. **Translational** progressively checks 1-, 2-, 3-, and 4-tile motifs using
   an exact finite-quotient (3-torus) cover test. It succeeds only when
   translated copies of the certified whole patch tile 3-space.
2. **Isohedral** builds the first corona and records its
   tile-type/displacement rules. Each legal rule is then applied around every
   subsequent tile whenever possible.
3. **Freestyle** performs face-to-face frontier search without assuming
   periodicity or tile transitivity.

The lower-level API accepts `generic` as an alias of `freestyle` and retains
`auto` for regression and research use. No strategy makes decisions from catalog names. Candidate
generation matches oriented faces, checks lattice solid-angle occupancy,
rejects overlaps, and requires a full 3D attachment.

Every mode keeps explicit frontier layers and prioritizes the oldest active
layer. Within a layer, balanced growth first establishes three independent
directions, then maximizes the ratio between the shortest and longest center
spans. Periodic motifs are consumed in centered cell shells, avoiding long
one-dimensional tendrils. The viewport renders the active frontier lattice
points for the selected Z³, FCC, or ½Z³ tier.

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
node scripts/test-3d-translational-polyhedra.mjs
node scripts/test-3d-mixed-periodic.mjs
node scripts/test-3d-custom-polyhedron.mjs
node scripts/test-3d-region.mjs
node scripts/audit-3d-catalog.mjs --quick
node scripts/audit-3d-catalog.mjs --strict
```

The strict audit covers every registered system and every deduplicated catalog
figure. It distinguishes exact certificates, certified local obstructions,
completed layer patches, balanced finite patches, and unresolved bounded
searches; strict mode fails if any system or figure remains unresolved.
