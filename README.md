# Geometrically Constrained Tree Search

**Geometrically Constrained Tree Search (GCTS)** is a working name for search problems where a
combinatorial object is built step by step under geometric constraints, and
where markings, macros, symmetries, or certificates can guide or prune the
search tree. In short: **GCTS is memoization by way of encoding failures
geometrically.**

This repository publishes the GCTS notes and playgrounds as a static GitHub
Pages site. The main way to use it is to open the page in a browser:

- [Geometrically Constrained Tree Search](https://liuyao12.github.io/geometric-tree-search/)

## Browser Pages

- [Held Circle Packing Search](./circle-packing-search/)
  Search corner-generated packings of circles with integer bends inside the
  unit disk. The browser solver removes rotational and reflectional symmetry,
  requires every circle to be locally held by surrounding contacts, and ships
  with a catalog of verified positive examples.
- [Materials Growth Lab: imported atomic structures and off-lattice growth](https://liuyao12.github.io/geometric-tree-search/iqc-growth-live/)
  A live 3D, multi-species GCTS laboratory for crystalline, quasiperiodic, and
  amorphous controls. Choose one to eight species from a mini periodic table to
  sample a random public bulk structure with exactly that element set from
  NOMAD, or use the advanced local CIF/POSCAR/XYZ/JSON import.
  It learns overlapping environments and finite SE(3) attachment
  rules, trains bounded connection sections, and continues the same explicit
  tree search beyond the observed configuration.
- [Penrose Model-Set Tiler](./penrose-model-set/)
  An exact cyclotomic search laboratory for genuine P2 kite–dart and P3 rhomb
  prototiles. Family presets stage a catalog that can be edited before running;
  mixed P2/P3 searches use a common exact atomization and expose placements,
  early prunes, and rollbacks live.
- [A₂ Online Tiler](./a2-online-tiler/)
  A separate live GCTS laboratory with outward growth around an arbitrary seed
  and exact finite-boundary decision modes. Its catalog supports Hat, Turtle,
  mixed systems, and custom closed A₂ loops; custom tiles can also be used as
  the initial seed. Trial, acceptance, explicit backtrack, and learned-marking
  frames use the same frontier/backtracking engine as the article demo. The
  growth outline is a target/view scale rather than a hard wall in the plane.
- [Geometrically Constrained Tree Search I: Learning matching rules in tiling](https://liuyao12.github.io/geometric-tree-search/GCTS-I.html)
  The primary browser version of the essay, with margin notes and a sticky
  draggable/zoomable Turtle side app that shows t-values in units of 1/12. Its
  known Turtle marking, its unmarked comparison, and the online learner are
  separate constraint add-ons to the shared A₂ tiler rather than separate
  search implementations.
- [A2 Tiling Studio](./turtle-tiling-game/)
  Repeat a Turtle, Hat, or custom closed A2-lattice loop around a single tile,
  Trefoil, or Hexagon center. The point editor validates loop closure,
  simplicity, and area before compiling boundary angles and occupancy for the
  same search engine. Online GCTS starts without marks, encodes immediate
  dead-frontier branches as sparse lattice mismatches, and replays the accepted
  prefix before committing each update.
- [3D Lattice Tiler](https://liuyao12.github.io/geometric-tree-search/3d-lattice-tiler/)
  A browser playground for lattice polyhedra and polycubes on the integer
  lattice. It supports mixed tile systems, custom polycube construction, search
  by exact rooted face-adjacency shells, tree inspection, intermediate tiling
  snapshots, and reproducible non-tiler and periodic controls—including the
  difficult prism that survived deep GCTS screening before an exact two-tile
  translational quotient resolved the full size-12 pass, and `10_16113`, whose
  corrected shell-1 witness leads to an exact shell-2 non-tiler certificate.
  The complete 1,502,640-entry size-13 pass contributes an isohedral-only
  periodic regression and two harder exact shell-2 non-tiler controls. For
  polycube candidate `p10-055695`, lazy next-ring cell CEGAR has now checked 22
  additional radius-three proposals and promoted 22 symmetry-distinct dead-cell
  orbits; an incremental Z3 path installs those exact obligations without
  rebuilding the formula. Across the old and new portfolios, all 71 proposals
  fail immediate radius-four continuation, but the outer space remains
  unexhausted, so this is neither a non-tiling nor an aperiodicity certificate.
  The same incremental funnel now has a cross-candidate result for
  `p10-054782`: 22 exact proposals down to 41 copies, 20 distinct dead-cell
  cuts, and no surviving radius-four subtree. Its best solver instance returned
  seven strengthened models from one construction before a randomized restart
  was needed. Candidate `p10-052588` now has stronger positive finite evidence:
  an unbounded-copy radius-2-to-3 CEGAR chain rejected 119 proposals before GCTS
  found and independently verified a 39-copy radius-three corona. Independent
  replay validates all 114 retained obstruction clauses. That particular
  survivor has twelve immediate radius-four dead cells, so radius four—and any
  claim of tiling or aperiodicity—remains unresolved. The exact continuation
  now returns every immediate dead cell in one pass; this promotes seven cells
  at once on the non-tiler control and twelve on the recorded `p10-052588`
  witness instead of rediscovering them through separate solver round trips.
  Interactive CEGAR can now stage those exact cell obligations four at a time
  while retaining the full learned queue across restarts. In a matched
  seed-175, 30-second A/B screen this raises the number of exact radius-three
  proposals from one to five. Three staged seeds supply nineteen distinct
  37–39-copy states; exact radius-four GCTS rejects every one, and an
  independent replay verifies all 216 learned clause instances. The ≤39-copy
  proposal space remains unexhausted. A matched joint clause-and-cell schedule
  reaches four states rather than the cell-only lane's five, so it is not the
  production policy; nevertheless, three are absent from the entire prior
  portfolio, bringing the exact corpus to 22 distinct states. All four fail
  immediately at radius four, and independent replay verifies all 57 new
  clauses. Joint staging is retained as a diversity lane. A fresh cell-only
  run with the proposal cap relaxed to 42 adds four more unique states,
  including three 40-copy coronas; all four still fail immediately at radius
  four, and all 40 new clauses replay exactly. The corpus therefore contains
  26 distinct exact states. Retrying a timed-out check in the same strengthened
  solver process extends the matched run from four to six states without a
  rebuild; the recovered state and its next ordinary check add two 41-copy
  coronas. Both fail immediately at radius four, and all 60 clauses from the
  escalated run replay exactly. The corpus now contains 28 distinct states,
  and exact partition restarts add five more, including four 42-copy coronas.
  The restart advances from 20 to 32 applied cell obligations; at that frontier
  a four-cell/six-clause step times out after 60s plus a 120s retry, while two
  one-cell/two-clause steps solve and reach 34 applied cells. This supports
  adaptive feedback batching. The 33-state corpus still consists entirely of
  immediate radius-four failures, all 97 accumulated clauses replay exactly,
  and transactional feedback now automates the recovery. On the matched hard
  seed it rolls back timed-out 6/4 and 3/2 clause/cell increments before a 2/1
  increment succeeds; on another seed the four-cell increment solves directly
  and reaches 36 applied cells. These add two more states, taking the exact
  corpus to 35. Exact retained-policy restarts then add distinct 40- and
  42-copy states and advance the applied-cell prefix from 36 to 41. Both still
  fail immediately at radius four; all 107- and 114-clause reports replay with
  zero failures. Two fresh attempts at the 41-cell prefix time out cleanly on
  the minimum 2-clause/1-cell increment. The 37-state ≤42-copy corpus remains
  unexhausted. Exact partial-formula caching then cuts matched construction
  from 52.7s to 2.65s. Cache-backed seeds 208 and 210 each advance one more
  applied cell and add a distinct 42-copy state, taking the verified corpus to
  39 and the applied-cell prefix to 43. Their 118- and 127-clause reports replay
  with zero failures, but both states still fail immediately at radius four.
  This remains inconclusive, not evidence of non-tiling or aperiodicity.
- [Hat GCTS online memoization demo](./hat-gcts-online-demo/)
- [Offline 2D / online 3D GCTS learning protocol](./docs/projects/gcts-offline-online-learning.md)
  A recorded, step-through run that begins with an empty marking. Immediate
  dead-frontier branches are encoded as sparse A2 mismatch certificates, with
  accepted-prefix replay checked before each update is committed.

Regenerate the Hat demo trace with:

```bash
PYTHONPATH=scripts python3 scripts/hat_online_memo_demo.py
```

## Big Picture

The primary article is maintained in this repository as the canonical browser
version of the essay.

The in-repository source for the primary article is
[GCTS-I.html](./GCTS-I.html), and a Markdown export of that post is included at
[docs/blog/tree-search-with-geometric-constraints.md](./docs/blog/tree-search-with-geometric-constraints.md).

## Local Development

The site does not require a build step. To preview changes locally from the
repository root:

```bash
python3 -m http.server 5174
```

Then open:

```text
http://127.0.0.1:5174/
```

or go directly to the local app preview:

```text
http://127.0.0.1:5174/3d-lattice-tiler/
```

### Materials structure import

The primary Materials Growth Lab input queries public [NOMAD](https://nomad-lab.eu/)
bulk entries containing exactly the selected element set, chooses a random
matching entry, reads its normalized atomic archive, and expands a small unit
cell into a roughly 128–512 atom learning supercell. The entry identifier,
database link, original atom count, replication, symmetry metadata, and query
population remain visible as provenance. NOMAD public reads require no API key.

Local import remains available under the advanced disclosure and is parsed
entirely in the browser; files are not uploaded. The import contract preserves
atomic species,
Cartesian coordinates in ångströms, three general cell vectors, per-axis
periodicity, occupancies, provenance, and a supplied CIF space-group label.
CIF symmetry operations are expanded before validation. Imports are rejected
for singular cells, invalid coordinates, unresolved duplicate atoms closer
than 0.1 Å, or more than 1,200 atoms. Partial occupancies are retained and
warned about, not stochastically resolved.

The published page is still a static application, not a remote simulation
service. Its current O(N²) neighbor and overlap construction is appropriate for
the intended hundreds-of-atoms learning window; a worker/job backend is needed
before direct database queries, trajectory ingestion, or substantially larger
training sets. See the [Materials Growth Lab architecture and audit](./docs/projects/materials-growth-lab-architecture.md).

### A₂ marking-learning benchmark

The A₂ benchmark trains from an empty rank-3 marking, validates several learned
revisions on a fresh branch order and a longer patch, freezes the best one, and
compares its replay with the geometry-only and human-marked Turtle controls:

```bash
node scripts/benchmark-a2-marking-learning.mjs \
  --tile=turtle --training-target=30 --target=60 --nodes=5000 \
  --validation-seeds=2,5 --seeds=1,3,6,7
```

In the current deterministic run, validation selects revision 3 with six sparse
support entries. Across the four fresh 60-Turtle searches, median search nodes
fall from 820 without marking to 493 with the learned frozen marking (the known
human marking reaches 193). For Hat, the same validation procedure rejects an
overfit late revision rather than assuming that every geometrically encoded
failure is a useful global rule.

The same learner contains no Hat-specific rule. Training a Hat run at 30 tiles,
validating at 40, and replaying revision 8 on four disjoint test branch orders
reduced median nodes from 283 to 54:

```bash
node scripts/benchmark-a2-marking-learning.mjs \
  --tile=hat --training-seed=3 --training-target=30 --target=40 --nodes=3000 \
  --validation-seeds=2,5 --seeds=1,4,6,7
```

The A₂ and 3D playgrounds also include an in-page growth chart. Each chart
records actual best tile count versus wall-clock time for naive search, online
GCTS, and a GCTS run with learned cluster proposals. The A₂ cluster policy is
learned from translation-equivariant local relations in the preceding GCTS
trace; the 3D comparison uses the engine's exhaustive online agent and
cluster/template proposals. All three series retain the full legal move set, so
the policy changes ordering while geometric failure clauses perform pruning.

The default A₂ GCTS now has a cheap, complete layer beneath the optional
rank-local inequalities. Every exhausted placement/context is retained exactly,
and every genuinely blocked frontier neighborhood is canonicalized relative to
its frontier point. Because every candidate touching that point lies inside one
tile diameter, the recorded local angle-sum pattern is a sufficient geometric
certificate: a translated recurrence can be rejected without re-entering its
subtree. On four deterministic 30-tile branch orders, this reduced median nodes
from 379 to 265 for Turtle and from 586 to 391 for Hat. Median measured runtime
fell from 1.70 s to 1.34 s and from 2.16 s to 1.64 s respectively. The learned
proposal replay then reached 30 tiles without backtracking in both examples.

## Headless Runner

The 3D tiler can also run without the frontend UI. This is useful for baseline
runs, long searches, and comparing later GCTS heuristics against the current
engine.

The two chart protocols are directly reproducible without rendering:

```bash
node scripts/benchmark-a2-growth-curves.mjs --tile=turtle --target=30
node scripts/benchmark-a2-growth-curves.mjs --tile=hat --target=30
node scripts/benchmark-3d-growth-curves.mjs --mode=1_cross --target=8
```

Use `--output=ndjson` to stream every growth point. Each summary reports the
measured ordering and returns a nonzero status when the deterministic search
work ordering is not `GCTS+clusters < GCTS < naive`.

```bash
node scripts/run-tiler-cli.mjs --figure letter_o::0 --target 80 \
  --output runs/letter-o-summary.json \
  --trace runs/letter-o-trace.ndjson
```

Useful options:

- `--list-figures` prints figure ids and names.
- `--criterion layer --target 4` switches from tile count to target layers.
- `--move-order repeat` tries same-orientation placements first.
- `--move-order periodic` prefers placements that continue a spacing already
  seen between same-orientation copies of the tile.
- `--move-order isohedral` tries to reuse the first corona around the root tile:
  it prefers placements whose displacement is a rotation/reflection-equivalent
  copy of a first-layer displacement around another placed tile.
- `--move-order rl` first probes generic two-copy periodic templates for z3
  polycubes, then seeds reusable first-corona/isohedral moves, then falls back
  to the online policy agent. Branch traces include the template vectors, motif
  orientations, and agent feature vector when `--branch-details` is enabled.
- `--isohedral-check 6` is a convenience shortcut for a fast, greedy
  single-tile isohedral-style smoke test to frontier layer/corona 6.
- `node scripts/benchmark-tiler-policies.mjs --figures cube::0 --policies coverage,isohedral`
  compares move-order policies, which is a lightweight harness for testing
  whether a learned/RL policy beats the built-in heuristics on the same engine.
  See `docs/projects/rl-tiler-agents.md` for the intended offline training and
  future interactive-agent integration plan.
- `--move-order symmetric` prefers placements whose resulting frontier has more
  reflected pairs of exposed faces and a less lopsided bounding box.
- `--move-order layer` prioritizes moves that advance the earliest frontier
  layer; `balanced` combines that with same-orientation and periodic preference.
- `--face-order constrained` chooses the earliest-added frontier point with the
  fewest legal candidates before ordering that point's candidate moves.
- `--face-order pocket` chooses the earliest-added, heaviest frontier point
  first, which tends to fill tight spots before loose boundary growth.
- `--face-order mrv` chooses the frontier point with the fewest legal candidate
  moves first, a generic CSP-style ordering for avoiding late dead ends.
- `--forced-layer-lag-cap 3` throttles automatic singleton/forced propagation
  and periodic-template repeats: if the next auto move would land more than
  this many tile layers beyond the minimum active frontier-point layer, the
  solver stops auto-placing in that corridor and reopens nearer frontier
  choices. Use `0` to disable the cap.
- In 3D searches, legal candidate placements must attach along at least three
  non-collinear active frontier points; planar/2D systems use two by default.
- `--polycube-lattice z3|fcc|half` chooses the polycube lattice tier. `z3` is
  the basic cube-vertex lattice, `fcc` adds the face-center cosets, and `half`
  uses the full `(1/2)Z^3` refinement.
- `--wall-time-ms 120000` stops gracefully after two minutes and still writes a
  best-effort JSON summary.
- `--trace` writes compact NDJSON events that can be inspected or summarized by
  scripts without rendering images.
- `--branch-details` adds candidate translations and heuristic scores to branch
  events in the trace.
- `--placement-details` adds the current placement translations and orientations
  to snapshots.

These are branch-ordering preferences, not pruning rules. Less symmetric or
less human-looking branches remain in the tree unless an explicit cap is set.

## Repository Shape

- `apps/`: interactive browser playgrounds.
- `scripts/`: local runners and analysis tools.
- `docs/blog/`: essays and long-form explanations.
- `docs/projects/`: project notes for individual GCTS examples.

The current repo is intentionally small. More experiments can move here once
they have a clear public-facing page, demo, or reproducible result.
