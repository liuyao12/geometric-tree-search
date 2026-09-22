# Fixed-window search versus the GCTS-I growth demo

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
