# 3D lattice search stress census

Searched **1,230 connected polycubes through seven cubes**, modulo translations and proper cubic rotations, with mirrors kept distinct. The counts by size are 1, 1, 2, 8, 29, 166 and 1,023.

| Result | Count |
| --- | ---: |
| Exact periodic point-value witness | 1,230 |
| Exact isohedral point-value witness within the short budget | 1,227 |
| Returned witness also passes geometric voxel coverage | 905 |
| Returned witness satisfies point equations but fails voxel coverage | 325 |

The last row does not say those shapes cannot tile geometrically. It says the particular returned witness is a point-function tiling only. Likewise, the three short-budget isohedral misses are unknown, not proved non-isohedral.

Each cold lane gets 750 ms, at most eight motif copies, 512 quotient points, 1,000 HNF domains and 1,000 nodes per quotient. If the first periodic witness is already isohedral, symmetry replay establishes that directly; otherwise a fresh isohedral search runs. Enumeration, orientation construction and verification are included in the total 34.5 seconds. Timings are a local observation, not a guaranteed speedup or fair comparison with the four growth lanes.

## Cases to stress next

These candidates were selected by unresolved isohedral status, found motif size, then node count. A two-tile returned motif is not a proof that the minimum period has two tiles.

| ID | Found periodic motif | Isohedral in 750 ms | Voxel replay | Periodic search nodes |
| --- | ---: | --- | --- | ---: |
| p7-0244 | 2 | unknown | pass | 528 |
| p7-0970 | 2 | unknown | pass | 136 |
| p7-0109 | 2 | unknown | pass | 12 |
| p7-0060 | 2 | yes | pass | 828 |
| p7-0059 | 2 | yes | pass | 827 |
| p7-0345 | 2 | yes | pass | 763 |
| p7-0360 | 2 | yes | pass | 670 |
| p7-0343 | 2 | yes | pass | 579 |
| p7-0391 | 2 | yes | pass | 558 |
| p7-0251 | 2 | yes | pass | 555 |
| p7-0625 | 2 | yes | pass | 527 |
| p7-0571 | 2 | yes | pass | 526 |

The first three are especially useful: they have genuine geometric periodic two-tile witnesses but the short isohedral search did not find a tile-transitive tiling. All three also remained unresolved in a fresh four-second isohedral run. All three also remained unresolved in a fresh four-second isohedral run. This is an empirical separation of the two lanes, not an anisohedrality theorem.

[Importable shortlist and certificates](../../runs/3d-periodic-rewrite-20260910/stress-shortlist.json) · [Every candidate and certificate (compressed JSONL)](../../runs/3d-periodic-rewrite-20260910/stress.jsonl.gz) · [Machine-readable summary](../../runs/3d-periodic-rewrite-20260910/stress-summary.json)

Run `node scripts/search-3d-lattice-stress.mjs 7` to reproduce the systematic family and bounds. `scripts/refine-3d-lattice-stress.mjs` reruns the unresolved isohedral cases with a four-second budget. No new candidates are automatically added to the main picker.

## Eight-tile positive regression

Both rebuilt lanes rediscover the supplied 16-vertex tile in an eight-tile 6×6×6 unit, using four original and four reflected tiles. The witness is discovered from orientations and point data, without reading a stored tiling. An independent rational geometric replay verifies 216 point residues, 255 clipped faces and 868 edge segments, with zero uncancelled boundary lines. The volume is 216, so the periodic geometric covering multiplicity is exactly one. The isohedral lane also supplies eight affine orbit witnesses.

[Algorithm audit and exactness scope](3d-periodic-rewrite-audit.md) · [Geometric verification](../../runs/3d-periodic-rewrite-20260910/eight-tile-geometry-verification.json)
