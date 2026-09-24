# Heesch audit: potentially non-tiling catalog entries

This study focuses on unresolved candidates and non-tiling controls. Known
space-fillers and periodic polycubes are excluded from further corona searches.
The initial catalog audit is retained so that the scope and duplicate entries
can be checked. The planar `p9-48258` cross and `nonacube_cross` are congruent;
they share the previously certified lattice result \(H=1\).

## Convention

For polycubes, use integer translations and all proper cubic rotations, without
reflections. A corona surrounds the entire boundary, including edges and
vertices. At every layer, the complete unit-voxel halo of all inner tiles must
be occupied. All overlaps are forbidden, including outside the required region.
The outermost tiles do not acquire another extension requirement. These are
lattice Heesch numbers, not claims about arbitrary Euclidean placements.

A successful \(k\)-corona proves only \(H\geq k\). A complete checked failure
at depth \(k\), together with a witness at depth \(k-1\), proves
\(H=k-1\). A timeout is unknown. The first corona is allowed to vary in every
second-corona search. Failed extension of a single chosen first corona would
not suffice for an upper bound.

Several old catalog fields named “corona radius” refer to a voxel-distance
window. Their values are not substituted for touching-tile corona counts.
In particular, the old p10-052670 radius-one witness is compatible with the
new result \(H=0\): it was a different target.

The catalog also contains mixtures. The tetrahedron, octahedron and
cuboctahedron entries below are tested **individually**; their mixed systems
are not declared non-tiling. Their edge-angle proofs allow arbitrary rigid
motions, a stronger scope than the polycube search.

## Three candidates resolved by periodic constructions

The 2-semicross, Letter O, and tuning fork each have \(H=\infty\). They are
excluded from further non-tiler searches. `periodic.py` finds and replays exact
two-copy certificates. Earlier bounded corona attempts are retained as discovery
history, not as the final classification.

For coefficients \((1,a,b)\) and modulus \(N\), define
\[
\phi(x,y,z)=x+ay+bz\pmod N.
\]
The two properly oriented copies contain exactly one voxel from each residue.
Repeating both copies by the kernel of \(\phi\) therefore covers every lattice
voxel exactly once. A basis of that kernel is
\((N,0,0),(-a,1,0),(-b,0,1)\), whose determinant is \(N\).
The certificates use \((N,a,b)=(14,3,4)\) for the 2-semicross,
\((20,3,8)\) for Letter O, and \((60,5,2)\) for the tuning fork.
All voxel coordinates, proper-orientation checks, and residue partitions are
recorded in `data/heesch-catalog/periodic/`. Failure to find a certificate in
this restricted family supplies no non-tiling evidence.

```sh
python scripts/heesch-catalog/periodic.py --ids 2_semicross,letter_o,tuning_fork
python scripts/heesch-catalog/periodic.py --ids 2_semicross,letter_o,tuning_fork --verify-only
```

## Exact reductions and certificates

`scripts/heesch-catalog/export.mjs` reconstructs the polycube voxels from the
catalog's corner-occupancy convolution, then replays all corner weights exactly.
It exports the original polyhedron vertices and faces for the angle tests.
Orientations in the SAT reduction are independently generated from the 24
proper signed permutations and normalized modulo integer translation.

For a first corona, enumerate every root-disjoint placement covering any voxel
in the root halo. Require every halo voxel to be covered exactly once. For a
second corona, form the union of the halos of every possible first-layer tile,
and enumerate all placements covering that union. Selecting a root neighbor
activates coverage of its entire halo. Global voxel incidence gives all overlap
constraints, including those outside the target. Sequential cardinality
encodings introduce auxiliary Boolean variables, but all placement identities
remain explicit.

Every positive witness is checked directly using occupied voxel sets and
iterated geometric halos. Every reported polycube upper bound has a regenerated
formula and an independently checked DRAT proof. The p10-052588 checker reports
ignored attempts to delete clauses absent from its database; its final result
is `s VERIFIED`, with zero RAT lemmas in the checked core. The full checker log
and the warning count are retained, rather than treating warnings as proof
failures or suppressing their existence.

Archives for the larger p10-052588 proof use XZ. Python's standard `lzma`
module reads them. The verifier reconstructs the formula before comparing its
bytes and proof hashes; it does not trust the solver's UNSAT status alone.

## Why the three uniform-angle solids have no first corona

At a generic point of an edge of the root, a surrounding finite patch intersects
a small perpendicular disk in sectors. Each incident tile contributes either
its dihedral angle \(\alpha\), or a flat-face angle \(\pi\). Choose the point
away from all vertices and transverse edges of the finite patch. At least one
edge sector belongs to the root. A complete surround therefore requires

\[
n\alpha+m\pi=2\pi,\qquad n\geq1,\quad m\geq0.
\]

Exact outward face normals show that every edge of the tetrahedron has
\(\cos\alpha=1/3\); every octahedron edge has \(\cos\alpha=-1/3\); and
every cuboctahedron edge has \(\cos\alpha=-1/\sqrt3\).
For the tetrahedron, \(\alpha>\pi/3\), so only \(n=1,\ldots,5\) need checking.
For the other two, \(\alpha>\pi/2\), so only \(n=1,2,3\) need checking.
The Chebyshev recurrence computes \(\cos(n\alpha)\) exactly in each case;
its square is never one. None can satisfy the sector equation, hence \(H=0\).
This argument permits face contacts and does not assume a face-to-face tiling.
The regular truncated tetrahedron has two dihedral angles, so this particular
obstruction does not decide it. No unsupported numerical-angle verdict is made.

## Graph search and learned affine markings

The unmarked graph lane has the complete frontier-voxel/candidate incidence.
It checks every active point for degree zero before propagating any singleton.
After all forced moves, it branches in the earliest generation, breaking ties
by degree and then coordinate. All first-corona obligations have generation
zero. In a second-corona problem, obligations activated by a first-layer tile
have generation one. Every candidate depends on all its occupied voxels,
including exterior voxels. Branch state is restored exactly.

At a dead point, the learned lane asks whether the **selected tiles alone**
block every geometric placement that could cover it. It never promotes a dead
point that depends only on branch exclusions. It removes selected tiles from
farthest to nearest while that certificate remains true. For a conditional
second-layer obligation, at least one selected activating tile must remain.
The resulting core is inclusion-minimal for this particular required-point
certificate. It is not claimed to be the smallest forbidden patch, or to have
geometrically extendable proper subsets under all other obligations.

Each certified core receives a private channel at the fixed root anchor:

\[
\sum_{i=1}^{k}z_i=1,\qquad
\text{role }i\text{ contributes }z_i=0.
\]

The atom for a placement with translation \(c_i\) is attached at prototype
offset \(-c_i\), in its oriented tile's field. The inverse-position check
ensures that reaching the active anchor identifies exactly that placement.
An absent role is a wildcard. All roles together conflict; every proper subset
of this channel admits a coordinate-vector witness. Incremental incidences and
counters exclude a last missing role and detect a fully present core. They are
updated on push, pop, and rule insertion; the current prefix remains validated.

Every learned core is independently replayed against every oriented geometric
cover of its certified point. Deletion minimality, inverse anchor positions,
and randomized counter rollback are checked separately. This gives proved
redundant restrictions for the rooted query. The current implementation does
not transport them to arbitrary roots or expand them through symmetry orbits.
It is an experimental affine-section GCTS lane, not a claim of a compact,
fixed-value, symmetry-complete tile decoration.

## Benchmark semantics

The four first-corona non-tiling cases receive three sequential, cold runs per
lane. The report gives medians. There is no pretrained marking or cache reuse
between repetitions. Time is split into formula construction, engine setup,
and search. Search time in the learned lane includes finding, minimizing and
compiling every new core. Total time includes all three phases. Proof recording is disabled in all timed lanes; complete certificates are
recorded and checked in separate runs.

The same geometric candidate universe and coverage target are used by the
unmarked graph, learned graph, and Glucose. Glucose uses the sequential-counter
CNF and its ordinary CDCL search. Python graph engines and native Glucose are
different implementations; these timings do not isolate the asymptotic merit
of an algorithm or justify a broad speedup claim.

For graph search, a visited terminal leaf is a branch reaching a contradiction
or a complete witness. Eliminated subtrees are not expanded or assigned an
invented leaf count. Glucose reports conflicts, decisions, propagations and
restarts. Its learned-clause database, nonchronological backtracking and
restarts form a different search process, so its conflict count is not labeled
as ordinary tree leaves. In particular, contradictions found during formula
loading can precede its recorded search counters; setup time is retained.

The deeper finite p10-052588 case also receives three sequential cold runs per
lane after its initial discovery. All three engines exhaust that target.
Separate bounded screening runs on unresolved candidates supply only partial
counts, never a completed tree size. The
nonacube's earlier hybrid measurements remain linked separately and are not
mixed into this reference graph comparison.

## Reproduce

Use Node for the catalog export, Python 3.12 with `python-sat` for graph
experiments, and a built DRAT-trim executable for independent proof checking.
The recorded graph benchmark uses `python-sat==1.9.dev5`; the discovery SAT
runs used the previously prepared environment. Pin the versions in the
provenance receipt when comparing times.

```sh
node scripts/heesch-catalog/export.mjs
python scripts/heesch-catalog/corona.py --out /tmp/heesch-results \
  --ids 3_cross,t_cross,large_buckled_ring,polycube_p10_052670 --k 1 --seconds 15
python scripts/heesch-catalog/corona.py --out /tmp/heesch-deeper \
  --ids polycube_p10_052588 --k 2 --seconds 180
python scripts/heesch-catalog/verify.py --checker /path/to/drat-trim
python scripts/heesch-catalog/verify.py --checker /path/to/drat-trim --subdir deeper
python scripts/heesch-catalog/edge_angles.py
python scripts/heesch-catalog/benchmark.py
python scripts/heesch-catalog/verify_graph.py
```

The scripts export experiment artifacts; the browser does not silently load
these markings into the production tiler. Conformance evidence: complete point/candidate incidence, global dead-end and
forced-move scans at node entry and after propagation, all-voxel overlap
bookkeeping, and exact rollback are implemented. The point domain here is
integer voxel occupancy with capacity one, a specialized exact polycube
reduction. Root halo obligations have explicit generation zero; conditional
first-neighbor halo obligations have generation one.

Scheduling gap: after a failed child, the parent tries remaining candidates at
its already chosen point. It does not reschedule the whole frontier between
siblings; the next child performs the global scan. Thus these are specialized
fixed-corona graph lanes, not a claim of full conformance to the reference
scheduler's rescan-after-every-change rule. This does not affect exhaustive
coverage or the checked proofs, but it can affect time and leaf counts. Both
graph lanes use this same convention. The affine rule and rooted context are
also explicit experimental extensions. No RL proposals or unproved
sample-trained restrictions are used.

## Graph-generated complete proof

`graph_proof.py` records every certified local core and the selected-prefix
exclusion at each exhausted graph subtree. Each addition is checked by reverse
unit propagation against the exact same corona CNF. The final empty clause
certifies exhaustive failure. Glucose is not called by this proof-producing
search. This checks the complete search, beyond checking its local markings.

```sh
python scripts/heesch-catalog/graph_proof.py --ids polycube_p10_052588 \
  --k 2 --seconds 180 --out data/heesch-catalog/graph-proofs
python scripts/heesch-catalog/verify_graph_proof.py --checker /path/to/drat-trim
python scripts/heesch-catalog/benchmark.py --ids polycube_p10_052588 \
  --k 2 --out data/heesch-catalog/benchmarks-k2
```

Proof recording is a separate run from the timing benchmark. Complete graph
proofs, formula archives, and checker receipts are linked from the study data.


## External source audit and corrections

On 2026-09-24 we audited Georgios Papoutsis's
[whuts-solver repository](https://github.com/gepa71/whuts-solver/tree/81eea57137d46dffb8fdc8c74e3c500845d3276b),
pinned to its 2021-06-02 commit. His [2021 account](https://math.stackexchange.com/questions/4142544/smallest-non-space-filling-polycube/4150301#4150301)
reports constructive periodic searches, later using Knuth's Algorithm X.
An unsuccessful search is explicitly not a non-tiling proof.

**Correction to this audit:** p9-02127 and p9-24025 were incorrectly retained as
unresolved despite published twelve-copy periodic witnesses. Their lattice
Heesch numbers are \(H=\infty\). Our historical bounded searches remain valid
records of those searches; they did not establish the literature status.
The interactive table and tiler catalog now classify both as periodic controls.

| Papoutsis index | Our catalog entry | Published witness / our result |
| --- | --- | --- |
| 1345 | p9-02127 | Twelve-copy periodic witness, independently checked |
| 12982 | p9-24025 | Twelve-copy periodic witness, independently checked |
| 22933 | p9-43172 | Eight-copy periodic witness, independently checked |
| 4921 | p9-08203 | Empty source result; our exact Heesch value remains unresolved |
| 4931 | p9-08219 | Empty source result; our exact Heesch value remains unresolved |
| 10958 | p9-20656 | Empty source result; our exact Heesch value remains unresolved |
| 22768 | p9-42947 | Empty source result; our exact Heesch value remains unresolved |
| 25373 | p9-48258 / nonacube cross | Empty source result; our checked lattice result is \(H=1\) |

The source's three-dimensional input and result file counts agree: 607
heptacubes with no empty result files, 3811 octacubes with only entry 834 empty
(the planar eight-cube ring), and 25413 nonacubes with the five empty files
listed above. **These inventory counts are not an independent verification of
every tiling in that repository.** The audit independently replays ten selected
positive certificates: all seven positive matches to our catalog and the three
heptacube examples 144, 272, and 556 that corrected older non-tiling claims.
All ten pass. Every source-to-catalog correspondence is checked geometrically;
source numbering is not assumed to match ours.

The separate non-tiling claim for the eight-cube ring comes from other work
mentioned in the Stack Exchange discussion, not from Papoutsis's empty file.
The follow-up below independently establishes its lattice Heesch number as \(H=1\); it does not reconstruct the authors’ separate box obstruction.

A witness gives a motif size, not by itself a proof that this is the smallest
possible motif. The author's minimality claim for entry 1345 depends on his
exhaustive smaller-period search, which this replay does not independently
certify. The repository also describes an earlier incomplete period-lattice
enumeration and its subsequent correction; positive witnesses can be checked
without relying on either search implementation.

His [four-dimensional report](https://math.stackexchange.com/questions/4156024/smallest-non-4-space-filling-polytesseract)
claims tilings through ten cells. A later 2022 comment leaves three eleven-cell
candidates without tilings after a bounded search, and says the search was
stopped. Those are unresolved candidates in that report, not proved non-tilers.
We did not replay the four-dimensional census here.

### Independent periodic certificate check

Let the rows of the nonsingular integer matrix \(B\) be the three period
vectors. For every voxel coordinate \(x\), compute exactly
\[
x\operatorname{adj}(B)\pmod{|\det B|}.
\]
Equal keys are equivalent precisely modulo the period lattice. We check that
every motif tile is a proper rotation and integer translation of the prototype,
and that the motif contains exactly \(|\det B|\) voxels with distinct keys.
This proves the translates cover the entire lattice without overlaps.
No floating-point geometry or SAT solver is used by this verifier.

Archived witnesses retain their source coordinates and attribution. Their
source paths, commit, hashes, catalog mappings, and checks are recorded in
[`papoutsis/audit.json`](../../data/heesch-catalog/papoutsis/audit.json).

```sh
python3 scripts/heesch-catalog/verify_papoutsis.py
```


## Positive controls for the corona encoding

The user's concern is whether the reduction tests the intended geometric
problem. Two published twelve-copy periodic tilers, p9-02127 and p9-24025,
therefore serve as positive controls. Their true lattice Heesch numbers are
\(H=\infty\). They are deliberately tested despite exclusion from the
potential-non-tiler classification table.

`positive_control_search.py` imports the original
`search-nonacube-two-corona.py`, replaces only its `SHAPES` table, and runs a
blind two-corona Glucose search. It supplies no periodic motif, preselected
tiles, or learned constraints. Geometry is normalized with all proper cubic
rotations. A three-minute cutoff remains unknown, never non-tiling.
`positive_control_cadical.py` runs a second blind engine on the same original
encoder with a two-minute budget and bounded conflict batches. It also
supplies no periodic motif.

`positive_control_witnesses.py` performs a separate constructive test. For each
of the twelve possible motif root roles, it transforms the entire periodic
tiling so that the root matches the encoder's canonical prototype. Exact
residue lookup identifies the tile covering any integer voxel without using
a guessed finite translation box. It forms the first and second touching
layers using unit-cube vertices and all incident voxel sectors, independently
of the encoder's halo function. It verifies shape congruence, nonoverlap,
root surround, and surround of every first-layer tile directly.

Every extracted placement must occur in the encoder's candidate universe.
All placement variables, selected and unselected, are fixed to that patch;
only cardinality auxiliaries remain free. The returned assignment must satisfy
every clause. Thus this test confirms that actual geometric coronas are
representable in the SAT formula. It is not counted as a blind search success.
For each root, two negative controls fix the same patch after deleting a
first-layer tile or a second-layer tile. Both must be rejected. The second
case specifically checks that first-layer boundary coverage is required.

The original nonacube and later catalog encoders produce byte-identical clause
lists for these controls. Formula hashes also connect the blind search to the
witness tests. Source hashes and complete receipts are archived. Control runs
may overlap with verification work, so their elapsed times are not performance
comparisons with the earlier sequential benchmarks.

```sh
python scripts/heesch-catalog/positive_control_search.py --seconds 180
python scripts/heesch-catalog/positive_control_cadical.py --seconds 120
python scripts/heesch-catalog/positive_control_phases.py
python scripts/heesch-catalog/positive_control_witnesses.py
```

Passing finite positive controls strengthens confidence in the reduction; it
does not independently prove completeness for the nonacube. In particular,
we distinguish a search that finds its own witness, acceptance of a supplied
known witness, and an undecided search.

An additional sixty-second Glucose run on p9-02127 prefers the positive phase
for every placement variable. This changes search order only; it supplies no
motif and adds no restrictions. Its separate result is retained regardless of
outcome.

### Recorded outcome

All 24 complete extracted patches are accepted, and all 48 incomplete fixed
patches are rejected. The blind Glucose searches both remain unknown after
180 seconds; the blind CaDiCaL searches both remain unknown after 120 seconds;
the additional positive-phase Glucose attempt remains unknown after 60 seconds.
No blind attempt returned SAT or UNSAT. Therefore the tests pass known-witness
acceptance and boundary enforcement, but do not report successful blind
reproduction of the hard positive controls. No Heesch classification changes
on the basis of these cutoffs.


## Ring octocube follow-up

The ring is the planar \(3\times3\) square with its center missing, extruded
one cube thick. It matches Papoutsis entry 834. Its three distinct lattice
orientations give a checked result of \(H=1\) under the same full
face/edge/vertex touching convention used above.

- A positive witness contains the root and 27 nonoverlapping neighbors. An
  independent cube-vertex incidence check verifies that every voxel sector at
  every root vertex is filled, and every neighbor is a congruent ring touching
  the root. This proves \(H\geq1\), without asserting that 27 is the smallest
  possible first corona.
- A second-corona search is UNSAT. The formula contains 4,364 placements,
  36,439 variables including cardinality auxiliaries, and 118,689 clauses.
  DRAT-trim independently accepts its proof. This proves \(H<2\) for the
  encoded lattice model.
- To audit candidate completeness separately, a rectangular translation scan
  enumerates every placement meeting the required target. For each coordinate,
  the translation ranges from the target minimum minus the shape maximum to
  the target maximum minus the shape minimum. It recovers all 386 root
  neighbors and all 4,364 second-corona candidates. Requirements are recomputed
  by incident cube vertices, without calling the encoder's halo routine.
- Substituting the ring's three orientations into the original nonacube encoder
  gives exactly the same clauses and placement order as the generic encoder.
  The saved formula is regenerated byte for byte before proof verification.

Completeness of the finite reduction follows as for the other polycubes:
every first neighbor must cover a root-boundary voxel; every second-layer tile
must cover a boundary voxel of some first neighbor. The enumerated target
contains all those voxels for every possible first neighbor. The formula
requires the root surround and conditionally requires the full surround of
every selected root neighbor. It forbids overlap on every occupied voxel,
including outside the target, and imposes no additional surround on the outer
layer. Thus an actual pair of lattice coronas would supply a satisfying
assignment. Its checked unsatisfiability excludes every first-corona choice.

Glucose search times with proof recording were approximately 0.0006 seconds
for one corona and 1.29 seconds for two. Formula construction took approximately
0.0044 and 0.069 seconds respectively; proof verification took approximately
0.95 seconds. These are individual runs on the audit machine, not controlled
GCTS comparisons. This engine uses specialized SAT search, not the reference
frontier-generation scheduler. No GCTS markings were trained in this follow-up.

[The earlier source discussion](https://math.stackexchange.com/questions/4142544/smallest-non-space-filling-polycube/4150301)
already reports the ring non-tiling. Papoutsis's empty periodic witness is not
itself that proof. RavenclawPrefect's updated answer reports that a
\(6\times6\times7\) box can be covered but a \(6\times7\times7\) box cannot.
We have not replayed that box computation here. Our independently checked
corona result agrees with the reported non-tiling status; no novelty claim is
made. The lattice proof does not exclude arbitrary Euclidean placements.

Historical reports of voxel-distance windows of radii one, two, or three for
this ring are compatible with \(H=1\). Such windows do not require surrounding
the whole of every tile that touches the root; they are not successive tile
coronas.

Artifacts: [prototype](../../data/ring-octocube/tile.json),
[first corona](../../data/ring-octocube/ring_octocube-k1.json),
[second-corona run](../../data/ring-octocube/ring_octocube-k2.json),
[CNF](../../data/ring-octocube/ring_octocube-k2.cnf.gz),
[DRUP proof](../../data/ring-octocube/ring_octocube-k2.drup.gz),
[verification receipt](../../data/ring-octocube/verification.json), and
[checker log](../../data/ring-octocube/drat-trim.log).

With Python, python-sat, and the pinned DRAT-trim checker from the main audit:

```sh
python scripts/heesch-catalog/verify_ring.py /path/to/drat-trim
```

To rerun discovery (this overwrites the run artifacts, so use a scratch copy):

```python
import json, pathlib, sys
sys.path.insert(0, 'scripts/heesch-catalog')
import corona
out = pathlib.Path('data/ring-octocube')
row = json.loads((out / 'tile.json').read_text())
for k in (1, 2):
    corona.run(row, k, 180, out)
```
