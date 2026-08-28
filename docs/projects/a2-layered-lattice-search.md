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

Two subsequent eight-way 64-round continuations seed each candidate from the
preceding exact clause set. Together they perform 128 further GCTS/CEGAR
refinements per candidate and learn 1,024 new exact obstruction cores. After
canonical subsumption, the latest retained clause counts are 238 (`00128`),
253 (`00211`), 275 (`00232`), 250 (`00235`), 260 (`00694`), 251 (`00755`),
261 (`00777`), and 258 (`00809`): 2,046 sound placement-subset blockers. The
second continuation contributes 512 new cores and increases the retained set
by 448 because 64 older seeded clauses become redundant under canonical
subsumption. Every latest run consumes all 64 configured continuation rounds,
so its terminal reason is `round_limit`, not a solver timeout. None exhausts
the outer first-corona models and none finds a replayed radius-two witness.
The cumulative reports end in `-longer128.ndjson` and record seed,
continuation, and cumulative effort separately. They strengthen the bounded
result but do not decide tilability.

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

The determinant-28 eight-copy screen now has a proof-producing backend in
`scripts/screen-a2-layered-periodic-scip.py`. It uses SCIP 10 exact mode with
safe rational LP bounds, asks SCIP for a VIPR branch-and-bound certificate,
completes the deliberately abbreviated LP derivations with `viprcomp`, and
accepts a negative only when the independent `viprchk` rational checker prints
`Successfully verified infeasibility.` Floating-point MIP statuses are never
used as rejection evidence. Separators are disabled: this reduces the first
completed proof from 287 MB to 40 MB and also makes completion substantially
cheaper.

The 1,995 determinant-28 HNF sublattices form 384 orbits under the six proper
A2 layer isometries (orbit-size distribution: two of size 1, two of size 2,
97 of size 3, and 283 of size 6). Since the quotient model already contains
all proper tile orientations, every HNF in one such orbit is an isomorphic
feasibility problem. The backend therefore proves one representative and
records every covered HNF index.

As an end-to-end retained control, the first orbit for `a2lp_7_00128` is now
certified negative and covers three HNFs. Its completed proof has 48,370
derivations and is stored compressed at
`data/proofs/a2-exact8-a2lp_7_00128-h0000.vipr.gz`; the exact generated MPS is
beside it. The report
`data/a2-layered-size7-periodic-exact8-a2lp_7_00128-orbit0.ndjson` records the
MPS, compressed proof, uncompressed proof, and executable hashes. This is a
pipeline certificate, not yet a complete eight-copy census. At that checkpoint
383 orbit representatives remained for `00128`, and all 384 remained for each
of the other seven candidates. A negative catalogue entry remains exact only
through six copies until its ranges are completed and merged.

The first parallel checkpoint immediately found a positive that the earlier
bounded search had missed. `a2lp_7_00694` has an independently replayed
eight-copy quotient of determinant 28, with period vectors `(2,0,0)`,
`(0,2,0)`, and `(0,0,7)`. The report is
`data/a2-layered-size7-periodic-exact8-a2lp_7_00694-witness.ndjson`. It is now
a large-domain periodic lattice-function control rather than an
unresolved/aperiodic candidate,
leaving seven focused candidates. The same checkpoint verified 27 negative
orbit representatives across the eight inputs; these are partial exclusions,
not non-tiling claims. Disjoint ranges can be combined with
`scripts/merge-a2-layered-periodic-scip.py`, which checks exact interval
coverage, binary fingerprints, one independently verified VIPR receipt per
representative, and HNF orbit-size accounting. It sets a complete negative
flag only for an exact `[0,384)` cover with no unknowns.

SCIP presolving is disabled in this proof mode. Otherwise a trivially
infeasible quotient can be eliminated before the branch-and-bound certificate
is opened, leaving only a tautological `_ori` file. The same case with
presolving disabled yields a one-derivation VIPR infeasibility proof. If SCIP
ever reports infeasible without a completed, independently verified proof, the
runner records an unknown rather than aborting the shard or counting a
negative.

Long runs should also pass `--checkpoint-directory`. After every orbit solve,
the runner atomically writes one merge-compatible NDJSON report named by the
candidate and zero-based orbit index. A later timeout, interruption, or hard
proof therefore cannot erase earlier verified receipts; completed consecutive
ranges are combined by `scripts/merge-a2-layered-periodic-scip.py`.

This certificate is deliberately checked against the GCTS-I definition, not
against Euclidean polyhedral volume. Eight visible prisms have Euclidean volume
84 while the integer period determinant is 28, so an ordinary solid-space
face-pairing checker would (correctly) reject that different claim. For the
project's lattice tile, the proof instead verifies all 28 lattice cosets and
checks that their exact solid-angle weights sum to 48. The webapp now has a
separate `exact_weighted_lattice_function_quotient` replay path so it neither
rejects a valid GCTS-I quotient on volume grounds nor silently promotes it to
a faithful Euclidean polyhedral tiling.

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

## Layer-essential size-eight pivot

The primary census now favors non-polycubic shapes whose combinatorics
actually use the foliation by `x+y+z=3k`. A shape is called *layer-essential*
when it occupies at least three consecutive elementary A2 slabs and is not a
constant-cross-section product prism. The generator records its layer count,
layer profile, number of distinct cross-sections, cross-section changes, and
lateral/vertical contact counts. These are selection metadata, not tiling
invariants or aperiodicity claims.

There are 4,940 symmetry-distinct size-eight layer-essential shapes. Exact
weighted HNF screening finds independently replayed one-copy periodic
quotients for 4,529. Of the remaining 411, another 405 have two-copy periodic
quotients. All six survivors exhaust every three-copy quotient (455 HNF
bases, zero unknowns). Two then have four-copy quotients; the final four—
`a2lp_8_02131`, `a2lp_8_02151`, `a2lp_8_03411`, and `a2lp_8_04836`—exhaust
all 651 four-copy and 1,085 five-copy bases with zero solver unknowns. The
five-copy sparse multicover searches visit 4,561,662 exact states in total.
All four also exhaust all 2,015 six-copy HNF bases with zero unknowns. Those
four six-copy searches visit 43,320,304 exact multicover states in total.
They now also exhaust all 1,995 seven-copy bases per candidate (7,980 total),
with zero unknowns and 208,268,428 exact states. The two harder candidates use
the complete 3+3 meet-in-the-middle fallback on 32 quotients each after the
rooted DFS reaches its state cap; differential tests compare that fallback
with brute force, and the disjoint HNF range merger rejects gaps or overlaps.

A longer first-corona pass finds independently replayed radius-one witnesses
of 24, 29, 30, and 27 copies for `02131`, `02151`, `03411`, and `04836`,
respectively. The final instance required the finite-domain formulation after
the default solver timed out. The retained merged report is
`data/a2-layered-size8-essential-corona1-verified.ndjson`.

The next-corona CEGAR/GCTS runs retain 16, 72, 72, and 62 sound obstruction
clauses for `02131`, `02151`, `03411`, and `04836`. The middle two stop at
their 72-proposal limits; the outer proposal solver times out for the other
two. None exhausts its finite outer first-corona space, so these are reusable
branch-pruning markings rather than second-corona failures. The report is
`data/a2-layered-size8-corona2-gcts-long.ndjson`.

Direct monotile substitution searches reject every scalar inflation from 2
through 8, and every unequal planar/layer scale pair in the same range: 49
complete inflation checks per candidate. Connected two-copy metatile
alphabets are also exhausted at scalar inflations 2 and 3. Connected
three-copy metatile alphabets are exhausted at scalar inflations 2 and 3 (993
types at each scale for `02131` and `04836`; 8,348 at each scale for `02151`
and `03411`). These are exact negative results for those substitution
families. At scalar inflation 2, the complete connected four-copy screens
also reject 62,134 parents each for `02131` and `04836`, and 1,105,225 parents
each for `02151` and `03411`: 2,334,718 additional certified local
obstructions, with no rule or unresolved parent. This is not evidence that no
more general substitution exists; clusters of five or more remain open.

For this triangular-prism cell complex, a genuinely non-real Eisenstein
multiplier rotates the three cell-edge directions off the honeycomb. A
cellular inflated target therefore requires `a=0`, `b=0`, or `a+b=0`; up to
lattice symmetry, the recorded positive planar scales cover that cellular
case. Non-cellular or regrouped geometric inflations remain outside this
screen.

These four remain the deepest-screened web-catalogue candidates. They are exact only
through seven copies: larger periodic domains, second-corona extension, and
more general substitution rules remain open. The staged machine-readable
reports are
`data/a2-layered-size8-essential-periodic-exact1.ndjson` through
`data/a2-layered-size8-essential-periodic-exact7.ndjson`; compact substitution
evidence is in `data/a2-layered-size8-substitution-screen-summary.ndjson`.

## Directed five-layer size-nine census

The next pivot makes the A2 foliation still more explicit. The complete
focused family consists of size-nine connected cell unions that span at least
five slabs, have a distinct cross-section in every occupied slab, and have a
non-palindromic layer profile. The last condition is a cheap sufficient test
that no symmetry reversing the layer normal can preserve even the section
cardinalities. These filters select geometry; they do not imply aperiodicity.

There are 724 symmetry-distinct shapes in this focused family. Exact weighted
quotient search certifies 430 with two-copy determinant-nine periods and
exhausts every two-copy HNF quotient for the remaining 294 with zero solver
unknowns. A first exact four-copy probe advances five of those survivors:
`a2lp_9_00005` has a replayed determinant-18 period, while
`a2lp_9_00000`, `a2lp_9_00002`, `a2lp_9_00003`, and `a2lp_9_00010`
exhaust all 910 four-copy HNF bases. Each of the final four has an independently
replayed root corona, using 21, 30, 29, and 27 copies respectively. They are
the directed-layer catalogue leads.

The fast exact multicover solver now quotients determinant-27 HNFs by the
proper A2 point group. Its 233 disjoint orbit representatives cover all 1,210
six-copy bases. Gap-checked disjoint shards exhaust that orbit partition for
each of the four candidates: 4,840 HNFs and about 19.9 million exact states in
total, with zero unknowns and no period. Thus all four are exact through six
copies; larger periods remain open.

Direct cellular monotile substitutions are completely excluded for every one
of the 49 planar/layer scale pairs from 2 through 8. Complete connected
two-copy metatile alphabets are excluded at scalar scales 2 and 3 (104/107/
111/120 symmetry-distinct parents per candidate at each scale). Complete
connected three-copy alphabets are also excluded at scalar scales 2 and 3:
11,811, 12,502, 14,254, and 16,710 parent types per candidate, or 110,554
parent-scale checks in total. Of these, 110,549 have independently replayed
atomic boundary obstructions; five scale-three parents for `a2lp_9_00000`
survive the local preflights and have independently replayed exact UNSAT
certificates. There are no rules and no unresolved parents. The atomic
preflight also avoids constructing a full placement graph when a target cell
is contained in no legal monotile copy; bounded runs remain explicitly
inconclusive and resumable until the whole alphabet is exhausted.

Radius-two CEGAR/GCTS retains 32, 15, 6, and 32 sound obstruction clauses for
the four candidates, respectively; none exhausts the finite outer
first-corona space.

The census, complete two-copy screen, focused four-copy screen, and corona
receipts are `data/a2-layered-size9-directed-census.ndjson`,
`data/a2-layered-size9-directed-periodic-exact2.ndjson`,
`data/a2-layered-size9-directed-focus-periodic-exact4.ndjson`,
`data/a2-layered-size9-directed-periodic-exact6.ndjson`, and
`data/a2-layered-size9-directed-focus-corona1.ndjson`. Substitution and
radius-two evidence is in the other `data/a2-layered-size9-directed-*` reports.

## Consecutive-layer alcove pivot

The newer search family removes the remaining product-cell bias.  Its atomic
cell is the cubic Coxeter (Kuhn) tetrahedron with vertices
`(0,0,0)`, `(1,0,0)`, `(1,1,0)`, and `(1,1,1)`.  These vertices lie on the
four consecutive sections `x+y+z=0,1,2,3`, and the six coordinate orders
triangulate a unit cube.  The tetrahedron's exact solid-angle weights are
`1,3,3,1` in the forty-eighth convention.  Connected unions therefore remain
exact GCTS-I lattice functions while changing section at every integer level;
they are neither polycubes nor unions of the earlier height-`(1,1,1)` prisms.

`assets/a2-sliced-alcoves.js` implements exact face adjacency, the proper
six-element A2-layer point group, translation/symmetry canonicalization,
boundary-face cancellation, and weight accumulation.  The complete connected
census counts through six alcoves are 1, 2, 7, 22, 83, and 314.  Of the 314
six-alcove shapes, 222 have a non-palindromic transverse weight profile.  Every
one of those 222 has an independently replayed one-copy determinant-one
period, so unit-volume alcove unions can be discarded immediately.

At seven alcoves there are 1,112 transverse-asymmetric shapes.  Their first
arithmetically possible periodic quotient uses six copies and determinant
seven.  A complete screen over the 15 proper-A2 HNF orbit representatives
finds independently replayed six-copy periods for 853 shapes.  The remaining
259 exhaust all 57 determinant-seven HNFs with no solver unknowns.  The full
run visits 206,993,651 exact multicover nodes and invokes its complete
meet-in-the-middle fallback 2,416 times.  These 259 are unresolved beyond six
copies, not certified non-tilers.  The retained receipts are
`data/a2-sliced-alcove-size6-directed-census.ndjson`,
`data/a2-sliced-alcove-size6-directed-periodic-exact1.ndjson`,
`data/a2-sliced-alcove-size7-directed-census.ndjson`, and
`data/a2-sliced-alcove-size7-directed-periodic-exact6.ndjson`; the eight
disjoint `part0` through `part7` reports preserve the worker receipts.

This is now the primary non-polycube enumeration.  The next screen should
apply the deeper corona/GCTS pipeline before attempting the next
arithmetically possible periodic size: twelve copies and determinant fourteen.
The root-corona portfolio affirms independently replayed coronas for all 259
six-copy survivors.  A Python capacity-GCTS pass initially left four cases
inconclusive after 100,000 nodes, but QF_FD found and replayed 37- or 39-copy
witnesses for all four in under 0.4 seconds each.  A node cap is still reported
as `unresolved`, never as a no-corona certificate.  The merged report is
`data/a2-sliced-alcove-size7-directed-corona1.ndjson`; its prefix, bounded
breadth shards, focused 100k receipts, and QF_FD completions are retained
separately.

Every candidate has also been screened for a direct scalar substitution at
each scale 2 through 8, both under the proper six-element A2 layer group and
with reflected copies enabled: 3,626 exact candidate-scale-model checks in
total.  All are certified negative with zero timeouts and no rule.  The
single-alcove control correctly distinguishes chirality: it has no scale-two
proper-only rule but has the expected replayed eight-copy rule with reflected
alcoves.  Most candidate negatives have an independently replayed atomic
target alcove contained in no legal copy; the remaining reports use exact
cover exhaustion.  These results exclude direct monotile scalar subdivision,
not clustered metatiles or non-scalar substitutions.  Reports are named
`data/a2-sliced-alcove-size7-substitution-scale{2..8}-{proper,reflected}.ndjson`.

The complete connected two-copy metatile alphabets are now also exhausted at
scalar scales 2 and 3 in both symmetry models.  Across 1,036
candidate-scale-model cases this checks 32,876 symmetry-distinct parent
metatiles: 32,731 have independently replayed local obstructions and 145 use
independently replayed exact UNSAT fallbacks.  There are zero rules and zero
unresolved parents.  The reflection-enabled single-alcove control does recover
a closed two-type substitution alphabet, so the mixed-alphabet closure logic
is exercised by a positive oracle.  The four merged reports are named
`data/a2-sliced-alcove-size7-two-cluster-scale{2,3}-{proper,reflected}.ndjson`.
Connected clusters of three or more monotiles remain open.

At radius two, a two-second breadth pass proves that 108 retained first
coronas are unextendible and leaves 151 timeout-inconclusive; this claim is
about those specific coronas, not the tiles.  Their exact UNSAT cores are
translated into outer-placement indices and reused as GCTS clauses.  One
alternate-corona round learns 91 more clauses; two continuation rounds bring
the retained total to 370 clauses over those 108 candidates.  No finite outer
space is exhausted yet.  The merged evidence is in
`data/a2-sliced-alcove-size7-retained-corona-extension.ndjson`,
`data/a2-sliced-alcove-size7-corona2-alternate.ndjson`, and
`data/a2-sliced-alcove-size7-corona2-continuation.ndjson`.  Deeper radius-two
continuation, twelve-copy determinant-fourteen quotients, and connected
metatile substitution alphabets remain the next stages.

Rebuild the earlier size-eight census with:

```bash
node scripts/export-a2-layered-polyprism-census.mjs \
  --size=9 --layer-essential=true --min-layers=5 \
  --min-cross-sections=5 --min-cross-section-changes=4 \
  --transverse-asymmetric=true --all-cross-sections-distinct=true \
  --output=data/a2-layered-size9-directed-census.ndjson
```

Rebuild the focused census with:

```bash
node scripts/export-a2-layered-polyprism-census.mjs \
  --size=8 --layer-essential=true \
  --output=data/a2-layered-size8-essential-census.ndjson
```

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
