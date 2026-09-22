# Seed-based growth and the archived fixed-window control

## Current behavior: v2.5 and the original explorer's tile-count lanes

The main web comparison now uses `growth-search.js` through the shared
`growth-experiment.js`. Free-range starts with an unmarked seed. GCTS collects
unmarked neighboring-pair corona labels, validates a browser-local marking, and
starts the same growth engine with that field. No fixed target window is active.
RL and GCTS + RL use the same graph, with optional validated three-placement
rollouts and online return estimates for ordering. Preparation, learning and
verification are included in v2's timings.

The default is 1,000 tiles, random seed 10, and 120 seconds per lane. Every newly
exposed positive-support point becomes a frontier obligation. Candidate domains
are complete; mark-only dependencies can invalidate distant candidates. Global
dead ends precede forced moves, then the earliest generation is selected, with
candidate degree as a tie break. Candidate order follows the article's fill,
frontier-incidence, occupied-support, new-point and seeded-random priorities.
The two slab caps use their common planar coordinates for point-order ties.
Generations, totals, component assignments and candidate incidence roll back.

A checkpoint is a consistent finite patch whose entire exposed frontier has a
legal candidate, independently replayed from point data and assigned m-values.
It is not an infinite-tiling certificate. Resource limits remain unknown, and
marked exhaustion says nothing about the unmarked problem. Positive-support
activation alone is not a fair enumeration of every untouched lattice point;
there is no whole-domain coverage claim.

The original explorer's ordinary **tile-count** free-range/GCTS/RL lanes use the
same runner via `legacy-growth.js`. Hat and Turtle use the same slab model as v2.
Other legacy models retain their point data. Layer, shell, region and structural
experiments remain explicitly labeled specialized legacy controls; their
historical semantics are not silently changed. Legacy comparison preprocessing
remains separately reported as before.

### Evidence and limits

- `test-3d-reference-growth.mjs`: exhaustive re-enumeration of all active point
  domains; generations and exact rollback; extended-mark conflicts and individual
  free components; rejection of dead-frontier checkpoints; independence from
  display-window points; identical free/marked-mode traces with no assigned
  markings; real cold Hat marking synthesis followed by verified marked growth;
  and legacy count-mode dispatch.
- Direct differential check against `solveA2Tiling`: identical first ten
  unmarked Hat placements at seed 10, both as a planar model and its slab lift.
  This prefix has no failed branch. It is not full trace equivalence: the article
  caches exhausted context/candidate branches, while the new DFS retains complete
  one-step legal domains and tries each frame's alternatives. Deeper backtracking
  paths and timing can differ. Both comparison lanes use the exact same new DFS.
- `test-3d-reference-growth-browser.cjs`: all four lanes reach a 30-tile Hat
  checkpoint, free-range has no assigned marks, GCTS uses the learned field,
  learning and growth remain visible, both entry URLs and legacy marked growth
  work, and all 40 original catalogue entries remain available.

No speedup over reference growth is claimed. An initial 30-tile Hat run found
free-range faster than cold GCTS; the previous fixed-window ratios must not be
reused here. The old experiment is available only as `?experiment=window`, with
its recorded timings separated from the main growth comparison.

## Historical mismatch (v2.4)

The v2.4 Hat timing result compares marked and unmarked **fixed-window** searches.
It does not measure a speedup over the seed-based search shown in GCTS-I.html.
The distinction was insufficiently explicit in the demonstration UI.

Source inspection compares `createSharedLiveTilingSearch` in
[GCTS-I.html](../../GCTS-I.html), `solveA2Tiling` in the
[shared A₂ engine](../../assets/a2-tiling-engine.js), and `PointGraph` / `search`
in the [v2 window engine](../../apps/3d-lattice-tiler/v2/search.js).

| Property | GCTS-I live growth | V2 fixed-window control |
| --- | --- | --- |
| Start | A placed seed tile | Empty placement set |
| Obligations | Seed support, then newly exposed positive tile support | Every target point is active immediately, including untouched points |
| Generations | Minimum incident tile generation, restored on rollback | Every target point is a fixed generation-zero root |
| Branch point | Global dead/forced checks, then earliest generation; degree breaks ties | Global dead/forced checks, then minimum degree because all generations tie |
| Candidate order | Fill the chosen point, graph incidence, existing-support coverage, new-point count, seeded random tie; optional marking/cluster scores precede these | Seeded hash of placement identity; RL optionally promotes a rollout proposal |
| Finish | Growth checkpoint; the Hat complete-point-growth path checks exposed frontier viability | Every required point in the finite window is filled; exterior points need capacity legality, not completed or viable frontier obligations |

The article currently uses random seed 10 and a 1,000-placement target. The v2.4
measured preset uses seeds 1–3 and 2,054 required slab points. These are different
experiments even though both use point values, complete candidate bookkeeping,
global dead/forced decisions, and reversible search state.

The window engine is a declared finite-target variant allowed by the master
contract. It must not be presented as the article's outward-growth algorithm.
The recorded Hat timings remain measurements of that window variant only.
Changing to reference growth requires matching target/activation rules, seed,
ordering and stop semantics in every compared lane, followed by new measurements;
the previous speedup ratios cannot be carried across that change.

## Marking inset

The side marking previously followed only the active lane. After GCTS finished,
the comparison automatically selected free-range and hid the marking. The inset
now retains the learned GCTS field during unmarked lanes, with an explicit
reference-only caption. Free-range and RL still receive models without learned
m-values. Selecting a marked lane restores its own marking. A new system or run
clears old fields. The main-view overlay remains independently optional.

`test-3d-marking-inset-lanes-browser.cjs` checks automatic GCTS-to-free-range
transition, actual unmarked main-model state, manual lane switching, inset
visibility controls and cancellation. The existing finite-window engine tests
remain scoped to that engine; they do not certify parity with the A₂ growth trace.
