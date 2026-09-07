# Catalogue review — 2026-09-06

Retain bounded unresolved research leads, independently verified delayed-failure
controls, and periodic controls with found motifs of at least five tiles. A found
motif size is an upper bound, not a minimum. Ordinary elementary examples remain
available as teaching and solver controls. Never promote finite survival to
aperiodicity or a resource cutoff to non-tiling.

New entries: `a2sa_10_76076`, `a2pair_20_4c8015f2f0fc`, and `a2sa_10_65558`.
The first two have independently replayed 24-copy geometric quotient certificates;
the third is a delayed geometric non-tiler. These exact Kuhn-alcove results use
integer translations and the full 12-element A₂ group. They do **not** classify
the weighted lattice functions explored by the webapp's six interactive lanes.
Both periodic certificates and their source geometry ship in the review module.

The latest engine (including vector-valued global sections) was exercised on all
153 registered systems in six lanes: 918 attempts. The bounded pass recorded
489 finite patches, 376 search cutoffs/incomplete results, 44 certified tiling
results, eight `no_tiling_found` results with `can_tile: null`, and one existing
Conway construction result. The latter is a built-in known construction, not a
cold discovery. The eight null results are **not** non-tiling proofs. No candidate
is newly classified from these null results or from the short cutoffs.

This is a regression pass (250 ms / 500 nodes, target eight tiles), not a complete
re-screening of all finite shells or all periodic domains. It does not establish
that GCTS outperforms the other lanes. Historical deeper exclusions retain their
recorded scope and budgets. Further definitive classification remains open.

Reproduce the runtime pass with `node scripts/review-interesting-catalog.mjs
assets/interesting-catalog-regression.json`. Run `node scripts/test-interesting-tile-review.mjs`
for an independent vertex-based quotient replay and model-separation checks.
`node scripts/test-3d-vector-markings.mjs` checks legal pairs, learned refinements,
rollback, symmetry actions and four-lane real-tile integration. Browser coverage
is in `scripts/test-interesting-catalog-browser.cjs` (requires Playwright).
