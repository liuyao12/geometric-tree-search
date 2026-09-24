# Nonacube: geometric compilation of learned failures

The completed run reproduces \(H<2\) for the integer-lattice nonacube with full
face/edge/vertex coronas. Its complete proof independently passes DRAT-trim.
This is a **Glucose hybrid with compiled anchor constraints**, not a compact
rank-three marking or a standalone GCTS engine. It learns from no preloaded
bad-patch catalogue, but uses the complete two-corona target from the beginning.

## What was changed

`build.py` enumerates physical placements and expresses overlaps, root coverage,
and conditional coverage around every selected root neighbor. It uses no
auxiliary variables: 8,140 placements and 569,020 clauses. All occupied voxels,
including those outside the required region, participate in overlap constraints.
Outer tiles have no additional surround obligation. The geometry definitions
come from the previously audited `../search-nonacube-two-corona.py`.

Glucose always decides to select a tile. Conflict analysis resolves away every
positive literal, giving a learned clause consisting entirely of negated
placement variables. Every such nonempty addition is a forbidden set of
selected placements **conditional on this rooted two-corona problem**.
These sets are not deletion-minimized, need not be connected, and their proper
subsets need not extend to a corona. The earlier cold-search five-tile example
remains the example with independently tested subset minimality.

For a learned set of \(k\) placements, make a private affine channel at the
root anchor. Its shared value satisfies

\[
V_P=\{z\in\mathbb R^k:\textstyle\sum_i z_i=1\}.
\]

Role \(i\) contributes \(z_i=0\). For its tile center \(c_i\), place that
atom at prototype offset \(-c_i\), with the appropriate tile orientation.
Only the root anchor is active in this query. An atom at that anchor reconstructs
exactly its intended placement. Missing atoms are wildcards. All roles together
contradict the normalization, whereas every proper subset of this channel is
satisfied by a coordinate vector belonging to a missing role. The affine
fiber dimension is \(k-1\); the implementation never constructs dense vectors.

Equivalently, a scalar allowed-state channel can start with
\(\{1,\ldots,k\}\) and role \(i\) can exclude state \(i\). This is a
nonlinear, set-valued rule; its alphabet and number of channels carry the
complexity. Neither formulation is fixed-value, pairwise overlap agreement.

The compiled solver maintains role incidences and zero-coordinate counters.
With \(k-1\) roles present it excludes the final placement; with all roles
present it reports conflict. Learned nonunit clauses are **not attached to
ordinary Boolean watcher lists**. Their clause objects remain as explanation
and proof records. Learned units are root-level exclusions. Base coverage and
overlap clauses still use standard Glucose propagation, and Glucose still
chooses branches, restarts, and backjumps. Newly learned asserting constraints
also enqueue their asserting exclusion directly through that common trail.

This construction is deliberately an exact re-encoding of conflict memory.
The coordinate lookup compiles back to the same placement identifiers; it is
not evidence of geometric compression or reuse at new locations. The full run
has 3,177,277 cumulative patterns and 34,893,205 cumulative role atoms. Deleted
rules cease to propagate, so these counts are not simultaneous active rank.
The largest rule has 43 roles. Peak active storage was not measured.

## Symmetries and context

The successful run uses a fixed root and frame. Its learned store is not closed
under every root symmetry. Applying an isometry to the root, tiles, anchors,
and channel data transports the construction, but that does not make these
rules safe at arbitrary unrooted locations. Such reuse requires retaining and
proving their coverage assumptions.

A separate trial expanded every new rule through the 16 signed permutations
preserving the root's plane. It reached 25,599,264 cumulative patterns at the
last 385.773-second checkpoint without completing. The intended 300-second
limit overran because that binary checked interruption only between phases;
the run was terminated. Its partial proof is not a certificate and is not
published. The portable patch fixes interruption polling. Transforming through
all 48 lattice point symmetries would also require transforming the root's
orientation. No full invariant, bounded-rank tile marking is claimed here.

## Check the published certificate

Use Python with `python-sat` installed (the geometry import also loads its
original SAT helpers). Obtain and build DRAT-trim, pinned here to commit
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`.

From the repository root:

```sh
python3 scripts/geometric-nonacube/verify.py \
  --drat-trim /path/to/drat-trim \
  --output /tmp/nonacube-anchor-verification.json
```

This reconstructs the formula, checks the published inventory and formula,
audits every learned addition as a distinct-role placement-only rule, checks
the anchor inverse-position map, and independently verifies the complete
proof. Without `--drat-trim`, it performs the reduction/representation audit
but explicitly reports `drupVerified: false`. The compressed proof is about
50 MB, and expands to about 436 MB. Verification needs temporary disk space
for the expanded formula and proof. The checked formula proves the upper
bound; the separately published one-corona witness supplies the lower bound.

## Reproduce the solver

Prepare Glucose 3.0 in a **fresh** PySAT checkout at commit
`152884a6d1889f56a61049aaa773be23f0a8d8c1`, following
[the existing preparation instructions](../README-nonacube-replay.md#reproduce-the-recording).
Do not apply these changes to a solver used for unrelated work. Set `PYSAT_SRC`
to that checkout and `GCTS_REPO` to this repository, then:

```sh
python3 scripts/instrument-nonacube-glucose.py "$PYSAT_SRC"
(cd "$PYSAT_SRC" && patch -p0 < "$GCTS_REPO/scripts/geometric-nonacube/glucose-anchor.patch")
c++ -std=c++11 -O3 -DNDEBUG -Wno-deprecated -pthread \
  -I"$PYSAT_SRC/solvers" scripts/geometric-nonacube/solve.cc \
  "$PYSAT_SRC/solvers/glucose30/core/Solver.cc" \
  "$PYSAT_SRC/solvers/glucose30/utils/Options.cc" \
  "$PYSAT_SRC/solvers/glucose30/utils/System.cc" \
  -o /tmp/nonacube-anchor
python3 scripts/geometric-nonacube/build.py --prefix /tmp/nonacube-anchor-input
/tmp/nonacube-anchor /tmp/nonacube-anchor-input.cnf \
  /tmp/nonacube-anchor.drup - 600 geometry \
  /tmp/nonacube-anchor-input.placements.txt > /tmp/nonacube-anchor-result.json
/path/to/drat-trim /tmp/nonacube-anchor-input.cnf /tmp/nonacube-anchor.drup
python3 scripts/geometric-nonacube/test.py --solver /tmp/nonacube-anchor
```

The ordinary baseline is reproduced by `python3 scripts/geometric-nonacube/baseline.py --proof /tmp/nonacube-baseline.drup`. Its original run used the same ten-second solve/resume polling.

The `-` argument skips the optional binary pattern log: all patterns are already
recoverable from nondeletion proof lines. `negative` mode uses the same
placement-only learning with ordinary learned-clause watchers. `symmetry` is
the experimental orbit-expansion mode. The published geometric run took
113.667 seconds; a clean portable-source run took 107.129 seconds and produced
an identical proof byte for byte. Timing varies by machine.

The regression control checks 60 small formulas against exhaustive Boolean
enumeration, including actual anchor propagations. A separate
unit-cube positive control verifies both surrounds geometrically. These do not
replace the full checked nonacube proof.

## Small-rank synthesis trials

```sh
python3 scripts/geometric-nonacube/rank-trials.py --output /tmp/nonacube-rank-models \
  > /tmp/nonacube-rank-trials.jsonl
python3 scripts/geometric-nonacube/rank-pairs.py /tmp/nonacube-rank-models \
  > /tmp/nonacube-rank-pairs.jsonl
node scripts/geometric-nonacube/rank-pair-viability.mjs /tmp/nonacube-rank-pairs.jsonl
```

These train finite allowed-state sets on the previous five-tile core. Scalar
states are \(\{-2,-1,0,1,2\}\), with trivial or determinant action. Vector
states are \(\{-1,0,1\}^3\), with the natural signed-permutation action.
Membership variables are tied under generators of the full cubic point group,
including tile stabilizers. Wildcard means the full state set. Anchor positions
have odd half-unit coordinates in \([-e,e]^3\), with \(e\in\{3,5,7\}\).
The patch's 31 proper subsets must have nonempty intersections at every anchor;
the full patch must have an empty intersection either somewhere (`free`) or
at its known dead point (`gap`). Every fitted model is replayed on all subsets.

For \(e=5,7\), all three actions can fit a free-anchor failure. Requiring
failure at the known gap makes both tested scalar models unsatisfiable, whereas
rank three succeeds. This is a finite synthesis result, not a theorem that all
rank-one approaches fail. The tighter \(e=3\) free-anchor experiments have no
successful fit.

The fitted models are **not certified pruning rules**. For example, the
rank-three gap model at \(e=5\) rejects 40 of 686 root-neighbor pairs. Its first
rejected pair has minimum frontier degree 28 with no forced move or dead point.
The free-anchor scalar trivial and rank-three models reject 288 pairs, with
a first example of minimum frontier degree 41. These are witnesses that the
fit fails to preserve other frontier-viable patterns; they are not witnesses
of full-corona or infinite extendability. The scalar determinant model passes
all 686 pair tests but remains unverified on larger configurations. No compact
fit was used in the proof-producing search.

## Conformance and outstanding work

This is a **specialized SAT control**. The complete finite point/candidate
incidence is compiled into the formula; all base constraints and learned
counter incidences propagate globally before decisions, and counter updates
follow enqueue and exact trail rollback. Integer voxel occupancy expresses
the fixed lattice-corona benchmark. It does not implement the reference
frontier growth generations: VSIDS replaces earliest-generation branching.
Affine/allowed-state sections are an explicitly experimental extension of the
master contract's fixed-value marking rule. There are no RL proposals.

What remains for a Turtle-like GCTS result is substantial: minimize/explain
obstructions locally, retain only necessary coverage context, synthesize
compact equivariant markings without unproved extra exclusions, and run them
inside the reference frontier scheduler. The completed hybrid is a checked
baseline for that work, not a claim that these steps have already succeeded.
