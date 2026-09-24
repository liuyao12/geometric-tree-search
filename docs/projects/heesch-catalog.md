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
