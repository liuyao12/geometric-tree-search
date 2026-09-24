# Nonacube two-corona proof and chronological replay

[Open the player](../docs/projects/nonacube-search-replay.html).

[Browse the collapsible directory](../docs/projects/nonacube-search-tree.html).
Every recorded decision visit is a folder, every conflict is a numbered leaf,
and backjumps and the terminal result are selectable entries. Search phases
group restarts. Long single-child decision paths are compacted visually; their
Choices dialog exposes every individual decision. Numbered conflicts can be
opened directly with a URL fragment such as `#conflict=265000`; arbitrary events
use one-based fragments such as `#event=1452067`. The full replay's `frame`
query parameter is zero-based for compatibility with the recording.

The directory is an index of the existing trace, not a new solver. Generate and
verify it with:

```sh
python3 scripts/export-nonacube-search-tree.py
python3 scripts/verify-nonacube-search-tree.py
```

The tree verifier checks every event and its decision-stack parent against the
source recording, traverses all first-child/next-sibling links to verify unique
reachability and chronological order, and checks every leaf ordinal and subtree
count. All 1,965,589 events and 529,855 conflict leaves are reachable. Folder
counts are conflict counts; return entries are not additional contradictions.
The browser loads phases on demand and renders only the visible directory rows.
This display does not change the search algorithm or expand learned pruning
into invented visits to unvisited branches.

The recorded Glucose 3.0 run has 900,768 Boolean decisions, 529,855 conflicts,
532,409 backjumps and 2,556 search starts, including the initial start. Every
one is retained in 1,965,589 playback events. Positive tile enqueues and removals
between events are retained in their original order. Auxiliary-variable
propagations are omitted from the visual recording; auxiliary decisions remain.
The recording ends in UNSAT. It is not an unrolled, chronological binary DFS:
CDCL learns clauses, backjumps and restarts, excluding many branches without
visiting each unpruned leaf. See the [Glucose authors' repository](https://github.com/audemard/glucose).

The instrumented run emitted exactly the original DRUP proof, SHA-256
`5f96de32a53f381a96af9d9959bca1cce0fff080976586a6b2c809eabfa93f03`.
The recording is an explanation of that run; the separately checked proof
establishes impossibility. Playback itself is not a proof checker.

## Largest patch

The maximum at propagation-complete states just before a decision is **39
crosses, including the root**, containing **351 unit cubes**. All 39 are
connected to the root by face/edge/vertex contacts. The maximum occurs first at
zero-based event 1,452,066. It covers 77 of the 90 required root-surround cells.
There are 23 other selected tiles touching the root and 15 outer selected tiles.
It is not a completed first corona. The previously verified first corona is
a different 35-tile patch, including its root.

This is a maximum over the recorded run, not an optimization result over all
finite patches. Conflict states can include transient overlapping placements;
they are excluded. The independent playback verifier replays every delta,
checks all 900,768 stable states for nonoverlap, establishes a maximum of 39
selected tiles, and separately checks the 39-tile witness's rooted connectivity.
Since the witness attains the maximum over all selected patches, it also proves
the connected run maximum.

## Exact reduction and completeness

`search-nonacube-two-corona.py` independently constructs the three planar cross
orientations under cubic rotations. All translations are integer physical
translations. Root-neighbor placements are obtained by aligning every cube
of every orientation with every cell in the root's Chebyshev-one halo and
rejecting root overlaps. This yields 686 possible first-layer placements.

For every possible first-layer placement, activate the cells in its complete
halo conditionally on selecting that placement. Enumerate all root-disjoint
placements covering any potentially required cell. This yields 8,140 tile
variables. At-most-one constraints cover every occupied voxel in their entire
support, including voxels outside the required set. Root-halo coverage is
unconditional; first-layer halo coverage is conditional. No surround is demanded
of the outer layer, and no infinite-tiling exclusion or marking is used.

Every two-corona gives a satisfying assignment. A first-layer tile's center
lies in the coordinate box from negative five to five; an outer tile's center
lies in the box from negative ten to ten. `audit-nonacube-two-corona.py` checks
the placement inventory by independent brute-force enumeration in those boxes.
The unsatisfiable formula has 76,614 variables and 261,282 clauses. A checked
34-tile first corona surrounding the root establishes \(H\geq1\), and this
formula establishes \(H<2\), hence \(H=1\) under complete face/edge/vertex
surrounds. No topological-ball condition is part of this claim.

## Replay the audits

Python requires `python-sat==1.9.dev15`. Node requires no external dependencies.
From the repository root:

```sh
node scripts/verify-nonacube-cross.mjs
node scripts/verify-nonacube-search-replay.mjs
python3 scripts/audit-nonacube-two-corona.py
python3 scripts/test-nonacube-corona-encoding.py
python3 scripts/verify-nonacube-two-corona-proof.py --drat-trim /path/to/drat-trim
```

The proof verifier builds the formula fresh, checks byte equality against the
published compressed formula, validates both hashes and invokes DRAT-trim.
Omitting `--drat-trim` verifies the reduction and hashes only. The checker used
here is [DRAT-trim](https://github.com/marijnheule/drat-trim) at commit
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`; its output is stored with the receipt.
The positive control solves the same two-corona encoding for a unit cube and
checks that the known nonacube one-corona is rejected as a two-corona.

## Reproduce the recording

Prepare Glucose 3.0 from PySAT commit
`152884a6d1889f56a61049aaa773be23f0a8d8c1`. The receipt contains the original
Glucose archive URL and hash. Within that checkout, download the archive to
`solvers/glucose30.tar.gz`, then call the following preparation functions:

```python
import solvers.prepare as p
p.extract_archive('solvers/glucose30.tar.gz', 'glucose30')
p.adapt_files('glucose30')
p.patch_solver('glucose30')
```

From this repository, install observational hooks and compile (substitute the
actual checkout directory for `/path/to/pysat`):

```sh
python3 scripts/instrument-nonacube-glucose.py /path/to/pysat
c++ -std=c++11 -O3 -DNDEBUG -Wno-deprecated \
  -I/path/to/pysat/solvers scripts/trace-nonacube-glucose.cc \
  /path/to/pysat/solvers/glucose30/core/Solver.cc \
  /path/to/pysat/solvers/glucose30/utils/Options.cc \
  /path/to/pysat/solvers/glucose30/utils/System.cc \
  -o /tmp/nonacube-trace
gzip -dc data/nonacube-search-replay/proof.cnf.gz > /tmp/nonacube-replay.cnf
/tmp/nonacube-trace /tmp/nonacube-replay.cnf /tmp/nonacube-events.bin \
  /tmp/nonacube-replay.drup > /tmp/nonacube-result.json
python3 scripts/export-nonacube-search-replay.py \
  --events /tmp/nonacube-events.bin --result /tmp/nonacube-result.json \
  --output /tmp/nonacube-reproduced-replay
node scripts/verify-nonacube-search-replay.mjs /tmp/nonacube-reproduced-replay
```

The hooks only emit observations and do not affect branching or propagation.
The binary format uses little-endian signed 32-bit triples; this recording was
made on an Apple ARM64 host. On a different-endian host adjust serialization
before reproducing. The runner mirrors PySAT's one-based variable numbering,
including its unused variable zero.

## Algorithm-contract conformance

This is a separately labeled **specialized SAT control**, not the reference
GCTS growth scheduler. Voxel centers carry exact binary occupancy. Complete
point/candidate incidence is compiled into the Boolean formula; global clauses
include outside-target overlaps. The generic CDCL scheduler branches on tile
and auxiliary variables, learns clauses, and rolls back Boolean trails. It does
not use earliest-frontier-generation scheduling. There are no geometric
markings, RL proposals, trained restrictions or same-problem speedup claims.
Independent inventory, formula, proof, positive-control and complete playback
audits are supplied. General GCTS incremental-domain and generation conformance
is not claimed for this specialized control.
