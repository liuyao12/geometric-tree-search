# A2-layered non-polycube search

The first non-polycube family now exposed in the 3D lattice catalogue uses the
affine triangular layers `x + y + z = c`.

The base polygons are the exact A2 hexagon, hat, and turtle already used by
the intrinsic two-dimensional GCTS demo. Each is extruded by `(1,1,1)`, so its
two end faces lie on levels 0 and 3. The resulting vertices remain in `Z^3`;
no voxelization is used.

## Exact lattice-function weights

The A2 engine stores planar angles in twelfths of a full turn. At an end face
of the prism the three-dimensional solid angle is half of the planar cone, so
a planar weight `a` becomes `2a` in the standard forty-eighth convention. At
an intermediate section it would become `4a`. Thus the layered generator is
an exact realization of the lattice-tile function in GCTS-I even when the
visible hat or turtle prism is non-convex.

The hexagonal prism is marked as an ordinary convex polyhedron and is the
positive periodic control. Hat and turtle are deliberately marked
`lattice_function`, not convex polyhedra: legality is decided by exact lattice
solid-angle occupancy, and the engine must not apply convex SAT overlap or a
convex one-tile certificate to them.

## Symmetry scope

These tiles do not use all 24 proper rotations of the cubic lattice. Their
fixed lattice is the foliation by A2 layers, so the direct point group is the
six-element subgroup carrying `(1,1,1)` to `+(1,1,1)` or `-(1,1,1)`. Reflected
copies add the other six A2 isometries only when the UI's reflection option is
enabled. The pre-processing report records this group and the tile stabilizer
before any lane is clocked.

This restriction matters: treating the UI's historical polycube “FCC” tier as
the same object would be incorrect. That tier merely refines polycube sample
points and permits even-sum translations; it does not change the symmetry
group for general non-polycubes.

## Certificate boundary

The extruded hat and turtle are useful structured GCTS benchmarks, but they
are not asserted to be strongly aperiodic three-dimensional monotiles. A
product tiling can retain a translation along the extrusion direction, and
the unrestricted three-dimensional tile may admit configurations not visible
in the planar theorem. Their catalogue label is therefore “layered aperiodic
lead,” not “known aperiodic monotile.”

The next census should move beyond product prisms by enumerating exact lattice
functions on several adjacent A2 layers and retaining only shapes with no
obvious axial period. Periodic certificates remain positive proofs; bounded
failure of translational or isohedral lanes remains inconclusive. Exact GCTS
corona obstructions should be reported only in the explicitly searched
lattice-function model.

## Multi-layer polyprism census

`assets/a2-layered-polyprisms.js` enumerates connected unions of elementary
triangular prisms in the A2-layer honeycomb. Equivalence uses translations and
the fixed six-element proper layer group. Single-layer shapes and repeated
identical cross-section products are flagged as product prisms and omitted
from the search pool.

The complete fixed-lattice census counts through size six are 1, 2, 4, 15,
50, and 237; after the product filter, the first two candidates occur at size
three. The patch-growing translational lane initially certified 44 of the 45
size-five non-products and left `a2lp_5_00003` unresolved. A 30-second rerun
grew 37 copies but exhausted only motifs through three copies, exposing that
patch growth was the bottleneck rather than the quotient decision itself.

The superseding screen solves each weighted HNF quotient directly with Z3.
It requires exactly 48 solid-angle units at every quotient class, fixes one
root copy only by translation and global proper-layer symmetry, and replays
every positive independently using Cramer's-rule quotient coordinates. All 45
size-five non-products have verified two-copy quotients of determinant 5,
including `a2lp_5_00003`. All 222 size-six non-products have verified one-copy
quotients of determinant 3. There are consequently no aperiodic candidates in
this census through size six, and the formerly unresolved catalogue entry has
been removed.

The original patch screens remain as diagnostics in
`data/a2-layered-size5-screen.ndjson` and
`data/a2-layered-size6-screen.ndjson`. The authoritative exact positive
reports are `data/a2-layered-size5-periodic-z3-all.ndjson` and
`data/a2-layered-size6-periodic-z3-all.ndjson`. Bounded failure of a future
quotient size will still be reported as unresolved; only an independently
replayed positive is called periodic.

Size seven is the first selective census. Of 1,119 non-product candidates,
910 have exact two-copy determinant-7 quotients. Direct meet-in-the-middle
search then finds four-copy determinant-14 quotients for 98 of the remaining
209. The other 111 exhaust all 399 HNF bases at four copies with no solver
unknowns. Their report is
`data/a2-layered-size7-periodic-z3-through4.ndjson`; these 111, rather than the
earlier timeout survivors, form the next exact-corona/GCTS pool. Failure
through four copies does not exclude a larger periodic domain.

Every one of the 111 exact-through-four survivors has an independently
replayed root-corona witness. A focused second-corona CEGAR screen then tested
eight especially compact root coronas. For each candidate, eight distinct
first-corona patches were proved unable to saturate their complete support;
the outer first-corona solver still has untested models, so all eight remain
inconclusive. This is recorded in
`data/a2-layered-size7-corona2-focused.ndjson`. Exact-model blocking is used:
the search never generalizes an obstruction to an untested corona merely
because the patches look similar.

The leading compact candidate `a2lp_7_00232` has a longer exact-model CEGAR
run: 64 distinct first coronas are individually proved unable to extend to a
second corona. The outer model is still not exhausted, so this strengthens
the finite obstruction evidence without changing its unresolved status. See
`data/a2-layered-size7-corona2-a2lp_7_00232-deep.ndjson`.

A complete coupled radius-two formulation is also implemented in
`scripts/screen-a2-layered-corona2-direct.py`: Boolean variables choose the
first corona and the final patch simultaneously, while implications require
exact saturation of precisely the support activated by the chosen first
corona. For `a2lp_7_00232` this has 580 first-placement variables, 4,643 final
placement variables, and 88,217 sparse incidences. The QF finite-domain/PB
backend remained undecided at its 180-second limit; the hash-committed report
is `data/a2-layered-size7-corona2-direct-a2lp_7_00232-qffd.ndjson`. This is a
complete formulation but an incomplete solve, so it changes no classification.

`scripts/screen-a2-layered-corona2-core-cegar.py` supplies the next exact
decomposition. An inner UNSAT core is converted into a sound placement-subset
clause: all unselected placements remain available as potential helpers, so
the clause can block every first corona containing that obstruction without
assuming geometric similarity. The initial copy-capped run is retained in
`data/a2-layered-size7-corona2-core-a2lp_7_00232-cap21.ndjson` as a timeout
diagnostic, not as obstruction evidence.

For `a2lp_7_00232`, the first 16-placement core was independently reduced and
replayed as a 12-placement obstruction against 2,291 possible helper
placements. It is sound but not claimed minimal. Resuming the outer search
from that marking learned four further clauses in 38 seconds, then a longer
515-second continuation learned 32 more. The resulting 37 sound clauses are
recorded in
`data/a2-layered-size7-corona2-core-a2lp_7_00232-long.ndjson`; the independently
replayed reduced core is in
`data/a2-layered-size7-corona2-core-a2lp_7_00232-minimized.ndjson`. The outer
first-corona space is still not exhausted, and no radius-two witness has been
found, so the candidate remains unresolved rather than being called a
non-tiler or an aperiodic monotile.

The same resumable core search has now been run on all eight focused
candidates. After a further 32 exact rounds per candidate and removal of
clauses subsumed by stronger learned clauses, the retained family-obstruction
counts are 48 (`00128`), 45 (`00211`), 68 (`00232`), 48 (`00235`), 47
(`00694`), 47 (`00755`), 48 (`00777`), and 47 (`00809`). Every run remains
unresolved: none exhausted the outer first-corona space and none found a
radius-two witness. Per-candidate reports end in `-extended.ndjson`.

A subsequent continuation adds 64 more exact rounds per candidate. After
another subsumption pass, the retained clause counts are 111 (`00128`), 109
(`00211`), 126 (`00232`), 109 (`00235`), 109 (`00694`), 111 (`00755`), 112
(`00777`), and 111 (`00809`): 898 sound family blockers in total. The smallest
retained clauses now contain nine placements. All eight outer models remain
satisfiable and no radius-two witness was found, so these longer runs remain
bounded-inconclusive. Their reports end in `-deeper.ndjson`.

The smallest learned obstruction for each candidate was then greedily reduced
and independently replayed against the full radius-two helper-placement model.
The certified reduced core sizes are 7 (`00128`), 4 (`00211`), 12 (`00232`),
9 (`00235`), 7 (`00694`), 3 (`00755`), 6 (`00777`), and 8 (`00809`). These are
sound conditional obstructions, but are not claimed globally minimal and do
not prove that the tile cannot tile space. Their receipts end in
`-mincore.ndjson`.

A strengthened continuation seeds GCTS with both the full deeper corpus and
the reduced exact core, then performs 32 new rounds per candidate. After
subsumption it retains 130 (`00128`), 136 (`00211`), 156 (`00232`), 131
(`00235`), 139 (`00694`), 142 (`00755`), 140 (`00777`), and 139 (`00809`):
1,113 sound family blockers in total. Every outer first-corona model remains
satisfiable and no radius-two witness was found. The current catalogue points
to these bounded-inconclusive `-strengthened.ndjson` reports and separately
exposes the size of each smallest replayed core.

The eight focused candidates now have a complete six-copy periodic screen.
The original generic pseudo-Boolean run reached its 120-second limit after
only 41--127 of the 741 determinant-21 HNF bases and left solver unknowns.
`scripts/screen-a2-layered-periodic-z3.py` now uses an exact sparse-bitset
multicover GCTS: a root placement is fixed by global translation and proper A2
rotation, the most constrained unsatisfied quotient residue is branched on,
and exact failed capacity/placement-mask states are memoized. Quotients that
exceed 50,000 DFS states switch to a complete 2+3 meet-in-the-middle
enumeration of the five remaining placements. Every five-element choice has
such a partition, so the fallback loses no solutions.

Across the eight candidates this exhausts all 5,928 candidate/HNF cases in
105,449,482 exact search nodes and 73,291,319 memoized failures. There are no
periodic certificates and no solver unknowns. `00128`, the worst case, uses
four disjoint range reports whose hashes and exact interval cover are checked
by `scripts/merge-a2-layered-periodic-exact.py`; the merged report retains
those receipts. Per-candidate reports begin with
`data/a2-layered-size7-periodic-exact6-`. Thus all eight are now exact through
six copies. Periodic quotients of eight or more copies remain open, so this is
still not a non-tiling or aperiodicity proof. The earlier
`data/a2-layered-size7-periodic-z3-focus6to8-part*.ndjson` files remain only as
historical timeout controls.

`scripts/screen-a2-layered-substitution.py` exactly subdivides a scalar-inflated
supertile into atomic A2 prism cells, enumerates every properly oriented copy
contained in it, and solves the resulting finite exact cover. All eight
candidates have certified no scalar self-substitution at scales 2 through 6.
Simple failures carry a separately replayed uncovered-cell obstruction; deeper
failures are replayed by an independent Z3 pseudo-Boolean exact-cover model.
This excludes only scalar `sI` rep-tile rules. Non-scalar integer inflation
matrices, decorated orientation states, and substitutions using several
metatile shapes remain open.

For the cellular anisotropic family, the triangular cross-section can only be
scaled uniformly up to an A2 lattice symmetry; a general Eisenstein multiplier
rotates an edge off the triangular cell complex. The remaining non-scalar
single-supertile maps therefore have independent integer planar and layer
scales `(s,c)`. The exact family screen exhausts all 42 pairs with
`2 <= s,c <= 8` and `s != c` for every focused candidate. All 336 finite
exact covers are certified negative: 246 have an independently replayed local
uncovered-cell obstruction, and 90 are independently replayed UNSAT by Z3.
The combined report is
`data/a2-layered-size7-substitution-anisotropic-s2to8-focused.ndjson`.

The substitution search now also includes cluster-of-clusters rules.
`scripts/screen-a2-layered-two-cluster-substitution.py` enumerates every
face-connected union of two monotile copies, quotients the enumeration by
translation and the proper A2-layer symmetry group, and independently replays
the two-copy decomposition. This gives 95, 93, 85, 89, 73, 73, 73, and 71
metatile types for `00128`, `00211`, `00232`, `00235`, `00694`, `00755`,
`00777`, and `00809`, respectively: 652 types in total.

For scalar inflations 2 and 3, each inflated parent was allowed to use any of
the candidate's two-copy metatile types as children, not merely copies of its
own type. At scale 2, 639 of the 652 parents have an independently replayed
cell that no child type can cover; the remaining 13 exact covers are
independently replayed UNSAT by Z3. At scale 3 the split is 627 local
obstructions and 25 exact UNSAT replays. Thus all 1,304 parent/inflation cases
are certified negative, and no nonempty substitution alphabet exists in this
finite family. A unit-prism control finds both connected two-copy metatiles and
a closed one-type substitution alphabet at both scales. The reports are
`data/a2-layered-size7-two-cluster-substitution-scalar2-focused.ndjson` and
`data/a2-layered-size7-two-cluster-substitution-scalar3-focused.ndjson`.

The two-copy result alone does not exclude substitutions based on clusters of
three or more monotiles, non-scalar metatile inflations, or metatile boundaries
that are not unions of two face-connected monotile copies.

The next exact family raises the metatile size to three monotile copies at
scalar inflation 2. Rather than compare every parent with every named child
type, `scripts/screen-a2-layered-three-cluster-substitution.py` constructs the
complete graph of legal monotile placements inside each inflated parent. A
legal child is exactly a connected, pairwise-disjoint triple in that graph.
This indexed formulation is equivalent to the full mixed alphabet but avoids
an otherwise quadratic comparison among thousands of metatile types.

After proper A2 symmetry and translation quotienting, the eight alphabets
contain 10,115 (`00128`), 10,446 (`00211`), 8,878 (`00232`), 9,583 (`00235`),
6,329 (`00694`), 6,406 (`00755`), 6,329 (`00777`), and 5,923 (`00809`) types:
64,009 parent cases in total. Of these, 63,757 have independently replayed
local connected-triple obstructions. The remaining 252 exact-cover systems
are independently replayed UNSAT: 246 belong to `00211` and 6 to `00235`.
There are no rules and no unresolved parents, so the complete connected
three-copy, scalar-2 mixed substitution family is certified negative for all
eight candidates.

One 38,873-placement scalar-2 `00211` parent exceeded the initial five-minute QF_FD
replay. `scripts/resolve-a2-layered-three-cluster-residual.py` re-enumerates
and hash-checks the full family, then independently proves that residual UNSAT
with reverse target and branch order in 200 nodes. The report preserves the
prior timeout and the resolving certificate. Per-candidate reports begin with
`data/a2-layered-size7-three-cluster-substitution-scalar2-`.

The same complete 64,009-parent alphabet has now also been screened at scalar
inflation 3. Explicitly materializing every connected child triple would have
created roughly 0.8 million placements for individual parents. The scalar-3
runner instead solves the contained atomic-monotile exact cover (typically
about 500--750 Boolean variables), partitions each selected placement graph
into connected triples, and blocks any unpartitionable atomic tiling before
continuing. Atomic UNSAT is independently replayed with reverse-order
Algorithm X. Local witnesses reuse a SHA-256-receipted exhaustive placement
graph whose boundary-neighbor index is regression-checked against brute
all-pairs adjacency. Runs are hash-validated and resumable at consecutive
parent prefixes.

At scale 3, 63,037 parents have hash-receipted exhaustive local
connected-triple obstructions and 972 are independently replayed atomic-cover UNSAT: 488 for
`00211` and 484 for `00235`. There are no rules and no unresolved parents.
Thus the complete connected three-copy mixed substitution family is certified
negative at both scalar scales 2 and 3, covering 128,018 parent/scale cases.
The scalar-3 per-candidate reports begin with
`data/a2-layered-size7-three-cluster-substitution-scalar3-`.

The scalar-2 screen has now advanced to every connected four-copy metatile.
`scripts/enumerate-a2-layered-four-clusters.py` adds one face-adjacent,
non-overlapping tile to every connected three-copy representative. This is a
complete enumeration: every finite connected four-vertex adjacency graph has
a spanning-tree leaf whose removal leaves a connected three-copy cluster.
Exact proper A2 isometry and translation canonicalization reduces 19,282,328
raw fourth-copy attachments to 8,322,476 symmetry-distinct parents. The
enumeration is transactional and resumable, and each candidate publishes both
its parent count and a canonical-key-stream SHA-256 receipt.

`scripts/screen-a2-layered-four-cluster-substitution.py` first exhausts atomic
coverage of every inflated parent cell, then exhausts connected pairwise-
disjoint four-copy coverage for survivors. Atomic exact covers are replayed in
both forward and reverse Algorithm X order; connected-four witnesses and local
obstructions are independently replayed. Of the 8,322,476 parents, 8,305,584
have finite local obstructions and the remaining 16,892 are exact-cover UNSAT.
The exact cases are distributed as 5 for `00128`, 16,699 for `00211`, and 188
for `00235`; the other five candidates are entirely rejected locally. There
are no rules and no unresolved parents. Per-candidate reports begin with
`data/a2-layered-size7-four-cluster-substitution-scalar2-`.

Thus connected mixed metatiles through four copies are now excluded at scalar
inflation 2. This still does not exclude connected clusters of five or more
monotiles or non-scalar metatile inflations, and it is not a non-tiling proof
for any of the eight candidates.

The machine-readable screen is `data/a2-layered-size5-screen.ndjson`. Rebuild
it with:

```bash
node scripts/screen-a2-layered-polyprisms.mjs --size=5 --time-ms=1200 --motif-tiles=8
python3 scripts/screen-a2-layered-periodic-z3.py \
  --input data/a2-layered-size5-screen.ndjson \
  --output data/a2-layered-size5-periodic-z3-all.ndjson \
  --max-copies 2
```

Run the regression with:

```bash
node scripts/test-3d-a2-layered-prisms.mjs
node scripts/test-a2-layered-polyprism-census.mjs
```
