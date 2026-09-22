# Interesting and difficult tiles in the live catalogue

The v2.3.0 catalogue restores fourteen polycube census geometries to both 3D
interfaces. The v2 selector now has 54 entries. Ten unresolved polycubes lead
the selector; three integer-grid obstruction controls and one periodic control
have separate groups. Existing slab, solid, and stress cases remain available.
This is a curated view of recorded evidence, not a new classification sweep.

## Where to start

| Tile | Why retain it | Current scope |
| --- | --- | --- |
| p10-346304 | Threefold symmetry; slow pair-corona classification | 54 positive, 24 proof-checked negative and 1,846 unresolved pairs; finite viable-frontier patches, no infinite classification |
| p9-42947 | Completed local classification without an infinite resolution | 1,405 positive and 3 negative pairs; larger growth remains a separate problem |
| p10-054782 | Ten-cube extension stress case | Recorded verified radius-three corona; larger extension unresolved |
| p9-48258 | Delayed contradiction to test pruning | Independently checked integer-grid non-tiling proof; unrestricted Euclidean placements outside its scope |
| p9-43172 | Difficult periodic comparison control | A verified eight-copy quotient; the found motif size is not a minimum-period claim |

These five entries form **Run catalogue suite**. The other unresolved entries
are p10-055695, p10-290795, p9-02127, p9-08203, p9-08219, p9-20656, and p9-24025.
The other obstruction controls are p10-052588 and p10-052670. Their notes link to
the corresponding recorded searches. The original v2.0 five-case table keeps
its historical tile IDs and measurements independently of catalogue ordering.

## Models and evidence

V2 builds these fourteen entries with `prepareVoxelPointModel`: full-capacity
voxel centers plus fractional corner weights, proper cubic rotations by default,
and integer physical translations. Coordinates are represented in half-unit
steps. This point model forbids voxel overlap. A radius-one target has 27 voxel
centers and 64 corners, hence 91 required points; filling corner obligations
also requires tiles outside the target's core. The UI reports this explicitly.

The ordinary point/candidate graph, generation ordering and exact rollback are
unchanged. Positive corona witnesses and completed search results receive an
additional independent voxel replay. Learning remains cold, uses no catalogue
labels or bundled assignments, and keeps budget-limited checks unresolved.
Saved markings remain keyed by the actual tile and lattice. The optional
reflection setting changes the model; recorded proper-rotation evidence is not
silently reclassified as evidence for a reflected run.

V1 adds the same geometries to its existing registry and thumbnail catalogue,
with current status notes and evidence links. It retains its legacy point and
geometric search semantics; its fields are not interchangeable with v2's
center-and-corner model. Adding the catalogue does not complete v1's algorithm
conformance migration.

The old structural probe adapter constructs the legacy point model, so it is
unavailable for v2's voxel entries. The worker checks this as well as the UI.
Recorded exact voxel-period experiments remain linked from the catalogue.
Neither an unresolved search nor a missed bounded periodic probe establishes
aperiodicity. The catalogue supplies geometry and research context, not hidden
constraints or search solutions.

## Validation

`test-3d-research-catalog.mjs` checks all fourteen source geometries and registry
entries, both reflection settings, exact model identity, empty initial markings,
translation parity, independent voxel overlap replay, unresolved cold learning,
the structural-probe guard, evidence paths, and fixed historical suite IDs.

`test-3d-research-catalog-browser.cjs` checks both pages, grouped counts, selected
geometry, status/evidence links, target point counts, cold learning, switching
back to existing controls, and the unchanged historical table. The ordinary
point-engine scheduler, incidence and rollback regressions remain passing.
