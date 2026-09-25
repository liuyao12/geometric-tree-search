# Standalone GCTS conflict search

This C++17 prototype reproduces the nine-cube two-corona UNSAT result without
linking or calling Glucose, MiniSat, PySAT, or another SAT solver. It maintains
an explicit finite point/candidate graph and implements its own conflict-driven
learning. It is a **finite conditional-target adaptation of GCTS**, not the
full unbounded growth engine or a learned geometric marking construction.

Webpage publication is deferred while this experimental work is reviewed and
validated. Keep new results off the public result pages until confidence is
established; the general automatic-publication preference does not apply to
this research during that period.

## What it takes from CDCL

Every selected or excluded placement has a decision level and, when forced,
a reason. Overlap and coverage constraints use two watched literals. A conflict
is resolved to the first unique implication point (first UIP), producing a
constraint that asserts a new assignment after backjumping. Constraints can
contain both signs: an excluded tile is a meaningful antecedent, not merely
an absent tile. No learned pattern library or existing proof is read by search.

Variable activity ranks candidates **inside the selected frontier point**.
It never chooses an unrelated placement ahead of an earlier-generation point.
Learned-constraint quality counts distinct decision levels (LBD); reduction
protects binary, low-LBD and currently explanatory constraints. Restarts retain
learned constraints. Restart intervals increase from 128 to a cap of 8,192
conflicts. These are simple policies, not a reproduction of Glucose's complete
heuristics or execution trace.

The CDCL design owes its lineage to
[Glucose, by Gilles Audemard and Laurent Simon](https://www.labri.fr/perso/lsimon/research/glucose/),
and [MiniSat](http://minisat.se/). The implementation here is new code, not a
patched or linked copy of either solver. The previous geometric experiment
remains a Glucose hybrid and retains its separate attribution.

## Run it

Requirements: Python 3.9+ standard library and a C++17 compiler. A separate
DRAT-trim executable checks the resulting proof. The checker used for the
published result is commit `2e3b2dc0ecf938addbd779d42877b6ed69d9a985`.

From the repository root:

```sh
python3 scripts/gcts-conflict-search/run.py \
  --output /tmp/gcts-nine --seconds 300 \
  --drat-trim /path/to/drat-trim
```

The runner regenerates the finite geometry and formula, compiles the solver,
runs it, and records source/input/proof hashes and timings in `result.json`.
An UNSAT result is marked verified only after the external checker accepts it.
Budget exhaustion is `unknown`; its partial proof is not a certificate.
Allow several GB of temporary space: the original nine-cube proof is roughly
577 MiB before trimming. The solve-time budget does not include preparation or
proof checking. The runner reports total time separately.

A positive geometric control and the independent regression controls are:

```sh
python3 scripts/gcts-conflict-search/run.py \
  --shape cube --output /tmp/gcts-cube --seconds 10 --audit
python3 scripts/gcts-conflict-search/test.py \
  --solver /tmp/gcts-nine/solver --drat-trim /path/to/drat-trim
```

The audit recomputes the whole graph at every branch and rollback. Small
random conditional-target cases are checked by exhaustive enumeration of
point obligations and capacity conflicts, independently of CNF evaluation.
Every UNSAT control is also checked by DRAT-trim. A pigeonhole instance exercises
restarts and learned-constraint deletion. The unit-cube witness is independently
replayed with integer voxels and both complete surrounds.

## Check the published proof without searching

```sh
python3 scripts/gcts-conflict-search/verify.py \
  --drat-trim /path/to/drat-trim --output /tmp/gcts-proof-check
```

The published file is a trimmed **binary DRAT** proof produced by DRAT-trim
from the solver's ASCII DRUP log. It is checked again against the original
formula, not just a smaller extracted core. See the result receipt for hashes
and checker logs. Proof checking requires no SAT solver.

## Model and conformance scope

The point domain is the integer cubic lattice; tile values are binary voxel
occupancies. There are three orientations and integer translations. The root
is fixed. Every point in its full face/edge/vertex halo is required. A selected
root-neighbor placement conditionally requires its own halo. Outer placements
carry no further surround obligation. Overlaps include support outside the
required region.

The universe contains 8,140 placements, 1,700 potentially required points, and
569,020 base clauses. The standard-library encoder is taken from our standalone
nine-cube certificate package. Its formula is byte-identical to the already
audited certificate formula, SHA-256:

```
102e050db3761b588d87e866168917802f9ad23e53fa40bf7000a476bd469b1d
```

Forward and reverse point/candidate incidence is complete. Each point tracks
unassigned candidates, selected covering tiles and selected activation triggers.
A candidate assignment or rollback updates all of its incident points, including
dormant points. Every propagation reaches a fixed point before branching;
global dead/forced obligations must then be absent. Decisions select the earliest
generation, breaking ties by degree, then choosing by candidate activity.

For this finite experiment **all potential obligations have generation zero**,
including while dormant. Generations are fixed target metadata, not chronological
tile births. Thus the experiment tests finite frontier scheduling; it does not
test the Turtle growth-generation convention. The separate random controls use
several fixed generations and audit reversible counts.

The authoritative candidate state is the reversible assignment trail. Clause
propagation supplies proved exclusions to the graph; the graph supplies decision
domains. Learned clauses are supplementary constraints scoped to this exact
rooted two-corona problem. No translation/rotation transfer, compact marking,
RL proposal, fractional capacity, or infinite tiling claim is implemented.
Mixed-sign learned clauses are not mislabeled as fixed point-value markings.
Within propagation, implications use CDCL watch order. A distant dead point can
therefore be discovered after another implication is queued. The strict reference
rule that a global dead-point check precedes every individual forced placement
is not yet implemented. The engine is not claimed fully contract-conforming.

The first completed run took 108.731 seconds of search and 0.262 seconds of
input loading, with 536,163 conflicts and 95,802 nonchronological backjumps.
DRAT-trim checked the original proof in 31.579 seconds. The earlier ordinary
Glucose control took 26.264 seconds on the same formula; that is a historical
single run, not a controlled current performance comparison. No speedup claim
is made. The next experiment should isolate scheduler and learning policies
while preserving the same candidate graph and independent proof check.
