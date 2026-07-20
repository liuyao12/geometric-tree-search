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

- [A₂ Online Tiler](./apps/a2-online-tiler/)
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
- [A2 Tiling Studio](./apps/turtle-tiling-game/)
  Repeat a Turtle, Hat, or custom closed A2-lattice loop around a single tile,
  Trefoil, or Hexagon center. The point editor validates loop closure,
  simplicity, and area before compiling boundary angles and occupancy for the
  same search engine. Online GCTS starts without marks, encodes immediate
  dead-frontier branches as sparse lattice mismatches, and replays the accepted
  prefix before committing each update.
- [3D Lattice Tiler](https://liuyao12.github.io/geometric-tree-search/apps/3d-lattice-tiler/)
  A browser playground for lattice polyhedra and polycubes on the integer
  lattice. It supports mixed tile systems, custom polycube construction, search
  tree inspection, and intermediate tiling snapshots.
- [Hat GCTS online memoization demo](./apps/hat-gcts-online-demo/)
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
http://127.0.0.1:5174/apps/3d-lattice-tiler/
```

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

## Headless Runner

The 3D tiler can also run without the frontend UI. This is useful for baseline
runs, long searches, and comparing later GCTS heuristics against the current
engine.

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
