# Catalogue audit of the learned GCTS lane

**2026-09-21 follow-up:** [p9-48258 has a checked integer-grid non-tiling
certificate](p9-48258-grid-obstruction.md), discovered through pair-corona learning
and verified without learned assignments. The original screening below is
historical; this result does not establish a true aperiodic monotile. The
[next complete catalogue](3d-point-corona-sat.md#p9-42947-complete-classification-and-limits-of-the-pair-marking)
for p9-42947 fits all 1,408 labels, but shows mixed warm growth and no infinite
classification. The [viable-frontier follow-up](3d-viable-frontier-search.md)
adds p10-346304's first ten positive pair classes and four proof-checked negative
classes. Its catalogue remains incomplete; no marking has been activated.

Follow-up: [geometric voxel checks](3d-voxel-marking-research.md) found overlaps
in the six successful historical-polycube point windows and introduced an
explicit center-and-corner research model. The point results below keep their
original scope; they must not be interpreted as geometric packing certificates.

The [v2.3.0 live catalogue](3d-research-catalogue.md) now exposes all fourteen
polycube records directly, using the center-and-corner model in v2. Its 54-entry
selector and five-case research suite are distinct from the historical sweep below.

## Purpose and scope

This September 21, 2026 experiment tests the new pair-corona learner against
the unmarked lane on every system in the deployed catalogue, then separately
on the 14 historical polycube research records. The latter include 11 records
marked inconclusive and three controls; they are imported from their actual
voxel coordinates, not substituted with the cube fallback for unknown IDs.

The discovery objective remains a geometric monotile that tiles space and
forces aperiodicity. An exact finite point window, a successful learned
classifier, and a bounded miss in periodic search each fall short of that
objective. In particular, the current fractional vertex model has not been
proved equivalent to nonoverlapping geometric polycubes. Results below do not
replace the earlier voxel-corona or quotient certificates.

## Reproducible protocol

```sh
node scripts/screen-3d-learned-catalog.mjs \
  --time-ms=3000 --output=/tmp/gcts-catalog-screen
node scripts/screen-3d-learned-catalog.mjs \
  --catalog=polycubes --time-ms=3000 --output=/tmp/gcts-polycube-screen
```

Each tile receives one cold free-range run and one cold GCTS run: proper
rotations, no reflected placements, seed 1, radius 1, 10,000 search attempts,
500 attempts per corona pair, and a three-second total lane budget. Full 3D
windows have 27 required points; the Hat/Turtle slab windows have 14. Worker
startup is included in `elapsedMs`, whereas `stats.totalMs` starts inside the
engine and includes model construction, learning, graph construction and
verification. This is a short diagnostic sweep, not a statistical speedup
benchmark. Runs are sequential.

The runner independently replays every reported finite solution, writes each
full artifact as gzip JSON, and updates a summary after every case. A worker
has a 1 GiB heap bound and a watchdog ten seconds beyond the requested lane
budget. Worker failure or timeout is reported explicitly. Source hashes record
the engine used by the run. Only aggregate results are checked into the
repository; experimental markings remain in the local run directory.

The aggregate receipts, including all per-system outcomes and source hashes,
are in [the audit data](../../data/3d-learned-catalog-audit-2026-09-21.json).

## Defects exposed and corrected

The first sweep exposed two implementation problems:

1. The hexagonal slab had three orientation records describing the same
   translated solid. Its point-group lookup was therefore noninvertible.
   Deduplication now compares exact weighted support and geometric vertices
   modulo permitted lateral translation, retaining one orientation. Both
   reflection settings have a bijective induced label action.
2. Counting candidate objects alone did not bound memory: each FCC/HCP
   candidate contains hundreds of point dependencies. Four GCTS workers hit
   their heap cap. The corona oracle now bounds stored dependency entries at
   one million and reports a resource-limited unresolved pair. It never turns
   an incomplete candidate graph into a negative label.

The post-fix sweep is recorded separately from the original run. The existing
Turtle and Hat reflected-slab regression scores remain unchanged.

## Research implications

The corrected 40-system sweep gives:

| Lane | Verified finite window | Unresolved | Unsupported exact model | Exhausted learned restriction |
| --- | ---: | ---: | ---: | ---: |
| Free-range | 16 | 15 | 9 | 0 |
| GCTS | 4 | 25 | 9 | 2 |

No worker crashed after the dependency limit was added. The four successful
GCTS systems were cube, hexagonal slab, rhombic dodecahedron and truncated
octahedron. On these small targets learning made the cold run slower:

| Tile | Pair labels | Valid passed | Invalid blocked | Free total ms | GCTS total ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cube | 26 | 26/26 | 0/0 | 5.6 | 115.7 |
| Hexagonal slab | 24 | 6/6 | 18/18 | 5.5 | 101.2 |
| Rhombic dodecahedron | 98 | 18/18 | 80/80 | 8.3 | 1028.0 |
| Truncated octahedron | 146 | 14/14 | 132/132 | 12.4 | 2337.2 |

The Hat and Turtle slabs with reflections **disabled** perfectly classify their
resolved pair catalogues but exhaust the learned finite-window search. This is
a concrete reason to retain the separate marked-growth check: fitting all pairs
does not establish that a marking admits a tiling. These are different runs from
the successful reflected-slab regressions, and neither result proves unmarked
non-tiling. No new hard-case infinite tiling, non-tiling proof, or aperiodic
monotile follows from this sweep.

All 14 historical polycube records remain unresolved in the cold GCTS lane;
the free lane finds six finite point windows and leaves eight unresolved.
The GCTS runs label only 1–8 pairs each before stopping. None produces an
accepted marking. These finite-window results do not upgrade or overturn any
historical geometric classification, including the known non-tiler controls.

Two larger-window follow-ups use radius 3 (343 required points) and a ten-second
budget. Both lanes finish and independently verify both windows:

| Tile | Free branches | GCTS branches | Marking eliminations | Free total ms | GCTS total ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rhombic dodecahedron | 6 | 1 | 882 | 45.1 | 1095.1 |
| Truncated octahedron | 3 | 1 | 610 | 55.1 | 2396.5 |

This demonstrates candidate elimination through actual point markings, but
still does not demonstrate a cold speedup. Both tiles are periodic controls.

Pair labeling is the main bottleneck on the historical hard polycubes. A
learner cannot reject their unresolved pairs, and increasing its equality
solver speed will not resolve that labeling cost. The next useful experiments
are deeper, resumable unmarked pair searches and comparisons on larger windows
for systems whose pair catalogues already complete. Any optimization must
preserve complete candidate incidence, global dead/forced checks, generation
order, exact rollback, and the distinction between exhausted and unresolved.
One concrete optimization to investigate is excluding candidates incompatible
with the permanently fixed seed pair before allocating their dependency
records. Such an exclusion would need an independent complete-domain audit;
it must not exclude candidates merely incompatible with a reversible prefix.

For a surviving geometric candidate, the subsequent proof work remains:

- establish that its point model faithfully represents geometric placements;
- produce an infinite construction, not just larger finite patches;
- prove that all geometric tilings obey a recognizable hierarchy, or another
  condition excluding every nonzero translation;
- if learned markings support that argument, prove their necessity or realize
  them in the geometry. A learned restriction alone cannot prove aperiodicity.

A new external lead is Tsiokos's September 16 proof submission,
[A Strongly Aperiodic Monotile in Three Dimensions](https://arxiv.org/abs/2609.19214).
It claims a rational decorated chair with a forced hierarchy. Its
[companion repository](https://github.com/ioannist/six-birds-tiles) is available,
but this audit has not replayed or independently established its geometric
or formal proof. It is not a discovery or verified result of this project.
