# Joint decoration assignment works on four supplied ice decompositions

This control moves Gaussian field markings into the actual point-value search
kernel, rather than only checking a saved assignment. It deliberately isolates
decoration choice: the geometric supports, component partitions and poses are
supplied from earlier verified witnesses. It is not full material reconstruction.

## Frozen setup

Use c00400 (Ih), c00900 (II), c01400 (VI) and c01900 (VIII), the first available
developmental configuration of each phase in the repaired-cover study. At each
geometric placement include every fitting-library decoration of its base, with
both endpoint fields coupled. The saved decoration is neither selected nor
preferred. Candidate ordering is deterministic ID order. Both lanes use exactly
the same candidates and integer half-weight atomic supports. Radius 0.6 retains
its previously declared developmental, not calibrated, status.

The model exporter produces 42,563, 6,558, 4,608 and 12,779 candidates respectively.
Its 344 MB generated model is a local diagnostic artifact, not bundled into the
public page. The lack of compressed shared field storage is an implementation
cost, not an inherent GCTS requirement.

## Results and independent replay

| Phase | Placements | Unmarked search seconds | Marked search seconds | Marked decorations differing from saved witness |
| --- | ---: | ---: | ---: | ---: |
| Ih | 128 | 4.168 | 4.620 | 124 |
| II | 96 | 0.504 | 0.590 | 88 |
| VI | 80 | 0.274 | 0.332 | 78 |
| VIII | 64 | 0.647 | 0.816 | 63 |

All eight runs fill their supplied atomic targets. Independent replay checks
integer t totals, shared placement inventory, fitting-library membership and
the selected fields under the known poses. All four marked runs have valid
common midpoint values. The unmarked VI result has one incompatible field
pair at radius 0.6 (distance 1.24089 > 1.2); the marked run avoids it, with
maximum pair distance 1.17052. The other unmarked results also satisfy the
field condition, despite not using it during search.

There are zero backtracks in all eight runs. Each II run has one forced move;
all remaining placements are branch decisions. Markings change the selected
VI assignment without reducing the number of branch decisions. These are
single-run diagnostics, not statistical timing comparisons. Marked search is
slower here; no speedup is established. Setup, export and independent replay
costs are excluded from the displayed search times and reported separately
where measured.

## Algorithm contract and gaps

- Point domain: all supplied atom IDs, with integer capacity 2 and contribution
  1 per motif atom; separate marking-only component-anchor IDs.
- Candidate domain: all coupled fitting decorations on the fixed listed poses;
  one inventory item per geometric placement, irrespective of decoration.
- Search: the existing PointSearch kernel with the previously tested linear
  implementation of global dead ends, global forced moves, then earliest
  generation. All supplied target points are active roots.
- Markings: Gaussian Hilbert balls with common radius 0.6, rotated as fields.
  Every mark point has at most two geometry inventories; the adapter rejects
  models violating this restriction. Pair separation removes candidates from
  the same frontier graph. Numerically uncertain pairs remain candidates and
  prevent a claimed complete marking witness.
- Dependencies and rollback: full graph refresh includes mark-only dependencies
  and inventory. Cached pair checks use immutable field identities. Each run
  restores the root semantic state, field assignments and inventory exactly.
- Tests: a small analytic one-Gaussian fixture independently audits eight graph
  states, a dead-end branch, a backtrack and root rollback, and rejects a
  three-inventory marking anchor. This is not a complete adapter-conformance
  suite; full randomized/exhaustive tests remain to be added. Material graph
  audits share the runtime numerical predicate; final field replay does not.
- Arithmetic: integer t values, guarded floating-point Gaussian comparisons.
  Independent replay uses signed world-coordinate quadratic forms. No exact
  interval-arithmetic field certificate is claimed.

The important remaining task is removing the supplied geometric decomposition
while retaining complete finite-pool bookkeeping. These four results show that
joint marking selection alone is not a difficult search problem under the
current broad fields. They do not establish complete continuous-pose search,
growth beyond input positions, learned anchors/t-values, same-condition data
provenance or useful search acceleration. Historical geometry-search failures
must not be relabeled as successes because this narrower control completes.

Artifacts: `export-ice-gaussian-search.py`, `gaussian-point-filter.mjs`,
`test-gaussian-point-filter.mjs`, `ice-gaussian-search.mjs`,
`verify-ice-gaussian-search.py`, `ice-gaussian-search-results.json`,
`ice-gaussian-search-check.json`. The search summary records exact kernel,
model and adapter hashes; the independent check records its input hashes.
