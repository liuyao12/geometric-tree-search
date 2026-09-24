# Planar polyform enumeration and Heesch record reproduction

This is an independent exact lattice experiment using Glucose3 (and a
separate Glucose4 control) through
`python-sat`. It enumerates free polyominoes, polyhexes and polyiamonds, searches
for complete touching-tile coronas, and attempts to reproduce published high
Heesch numbers. See the [interactive results](planar-heesch.html).

## Sources and interpretation

Craig S. Kaplan's [dataset](https://cs.uwaterloo.ca/~csk/heesch/) supplies
prototype coordinates and expected values. The method is informed by his
[paper](https://cdm.ucalgary.ca/article/view/72886); the implementation here is
new Python code, not a wrapper around the author's CryptoMiniSat program.
The downloaded text files retain their source ordering. `catalog.json` records
the source URL and one-based shape row for each entry.

The chosen high-order benchmarks are the two 17-cell polyominoes with
\(H_c=H_h=3\), the 11-cell polyhex with \(H_c=H_h=4\), and the
20-cell polyiamond with \(H_c=H_h=4\). They are record examples in the
published unmarked-polyform census. The literature search on 2026-09-24 found
no newer higher record for these families; that is not a proof that none exists.
Bašić's [general polygon record](https://pmc.ncbi.nlm.nih.gov/articles/PMC7812982/)
is \(H=6\). Its different geometry is outside the current three-grid encoder.
No reproduction of that result or new record is claimed.

Here \(H_c\) forbids holes in the outermost corona and \(H_h\) permits them.
A simply connected witness at depth \(k\) and checked UNSAT at depth
\(k+1\) even with holes allowed establish \(H_c=H_h=k\).
General census finite values are \(H_h\); they must not silently be presented
as \(H_c\). In particular, one of the three non-tiling heptominoes has
\(H_c=0\) but \(H_h=1\).

## Exact model and complete finite reduction

The domain consists of lattice cells, represented by integer tuples
\((x,y,s)\). Each tile contributes \(t=1\) at its occupied cell points
and zero elsewhere. No markings are used. Squares and hexagons use
\(s=0\). Triangles use two cell types: the upward triangle has vertices
\((x,y),(x+1,y),(x,y+1)\), while the downward triangle has vertices
\((x+1,y),(x+1,y+1),(x,y+1)\). The triangular axes meet at
\(\pi/3\). Source triangular coordinates are converted from
\((3x+s,3y+s)\). Reflections and every lattice rotation are allowed.

The halo contains all cells sharing at least one vertex with a tile. Thus
corners are surrounded as well as edges. There is no fixed arbitrary search
box: start with every root-disjoint placement covering the root halo, then
repeatedly add every placement covering the halos of the preceding candidate
shell. Enumerate every orientation and every compatible cell alignment.
After \(k\) expansions this contains every tile that can occur in the first
\(k\) touching-tile coronas. Candidates intersecting the fixed root are
excluded; no other learned or sampled restriction is used.

For each candidate placement \(T\), give it Boolean labels
\(v_{T,j}\) for every permitted layer \(j\) from its minimum candidate
shell through \(k\). At each occupied point a sequential at-most-one
constraint covers every incident placement label. This forbids overlap
everywhere, including outside the required halo, and prevents selecting two
labels for the same placement. A coverage variable \(c_{p,j}\) implies
that some selected placement containing \(p\) has label at most \(j\).
Require \(c_{p,1}\) on the root halo. For each selected label
\(v_{T,j}\) with \(j<k\), require \(c_{p,j+1}\) on its entire halo.
Root cells need no additional placement.

Every actual corona patch supplies a satisfying assignment using its touching
distance from the root. Conversely, nonoverlap forces any selected tile touching
the root to have label one: it occupies a root-halo cell that must be covered
by label one. Inductively, every selected tile at actual touching distance
\(d\leq k\) has label at most \(d\). All such tiles at distance below
\(k\) therefore have complete surrounds. The basic formula may also select
irrelevant components; replay discards everything beyond the root's first
\(k\) touching layers. These components do not weaken an UNSAT upper bound.
No chosen first corona is frozen when searching for further coronas.

A separately recorded `exact-parent` Glucose4 control adds explicit adjacency
to the preceding labelled layer and forbids later labels on root neighbors.
Every actual corona patch satisfies these constraints, so candidate
completeness is preserved. `strengthened.py` defines this encoding; its
results are distinguished from the initial Glucose3 runs.

The hole-free witness search additionally requires a selected earlier-layer
parent for each nonfirst tile. This removes irrelevant components. It flood
fills empty cells using edge adjacency. When a hole occurs, it adds clauses
requiring that retaining its enclosing selected boundary must fill every hole
cell, or that at least one boundary placement changes. These are explicit
geometric enclosure constraints. This extra routine is used to find positive
witnesses; upper-bound claims use the unrestricted outer-hole formula.

## Enumeration and periodic controls

Start from one cell. At each size, append every edge-adjacent cell and
canonicalize by the full lattice dihedral group and integer translation.
Induction gives every edge-connected free shape. Shapes containing holes are
retained during growth and removed only from each reported final size.
Independent known small counts and brute rectangular candidate scans form
implementation checks. The high-order records are imported prototypes;
enumeration does not reach all 17-cell squares or all 20-cell triangles.

Before a corona search, try periodic exact covers on finite quotients with
basis \((a,0),(u,b)\), \(0\leq u<a\), containing one or two tile copies.
The quotient key is
\[
\left((x-\lfloor y/b\rfloor u)\bmod a,\;y\bmod b,\;s\right).
\]
Every tile must have distinct quotient cells and the complete motif must
contain each quotient cell exactly once. Repeating by the period lattice
then proves an infinite tiling. The independent verifier rechecks congruence
and every residue. Failure to find a one- or two-copy construction has no
non-tiling implication. Corpus classification uses bounded corona runs;
a budget cutoff or survival through the depth cap remains unknown.

## Evidence and contract conformance

SAT witnesses are independently replayed by cell congruence, disjoint occupancy,
and counts of occupied sectors incident to every inner vertex: four squares,
three hexagons or six triangles. This verifier does not call the encoder's
halo routine. It reconstructs touching layers and checks outer holes. Negative
controls remove a necessary tile and must fail replay.

Glucose records a DRUP proof for each reported UNSAT. DRAT-trim checks the
proof against the complete DIMACS formula. `verify.py` regenerates each
recorded formula byte for byte, checks formula and proof hashes, replays
positive and periodic certificates, checks small candidate universes with an
independent rectangular translation scan, and compares recovered finite
values to source values where available. Proof receipts retain checker logs.
The mathematical completeness argument above is still required: a proof
checker certifies the formula, not automatically the geometric reduction.

This engine implements the complete point/candidate incidence and exact
capacity semantics required by `docs/basic-tiling-algorithm.md`, specialized
to unit cell occupancy. It uses Glucose's CDCL decisions, propagation,
backtracking and restarts, **not** the reference global frontier generation
scheduler. There is no claim of full GCTS scheduling conformance, no trained
marking, no RL proposal restriction, and no GCTS speedup claim. Topological
halo activation and hole checks are declared geometric controls defining the
Heesch experiment. All results concern lattice placements; off-grid Euclidean
placements are not independently excluded by this implementation.

Reported times separate formula construction and solving, and record proof
checking separately. Some runs overlap; these are diagnostic times rather
than controlled performance comparisons. Time limits apply to solving, not
formula construction. Short and longer attempts are retained separately.

## Reproduction

Requires Python with `python-sat` (the receipt pins the version), plus a
DRAT-trim executable for checked upper bounds. Large CNF and proof archives
are retained locally under `data/planar-heesch`; the website publishes
witnesses, receipts, source coordinates and the encoders, not those large
archives. No third-party source code is required by this implementation.

```sh
python scripts/planar-heesch/run.py --seconds 45 --checker /path/to/drat-trim
python scripts/planar-heesch/holefree.py --seconds 60
python scripts/planar-heesch/enumerate.py --family hex --size 7 \
  --seconds 1 --checker /path/to/drat-trim
python scripts/planar-heesch/enumerate.py --family omino --size 9 \
  --seconds 1 --checker /path/to/drat-trim
python scripts/planar-heesch/enumerate.py --family iamond --size 10 \
  --seconds 1 --checker /path/to/drat-trim
python scripts/planar-heesch/verify.py
python scripts/planar-heesch/report.py
```

The final polyiamond upper bound uses the exact-parent control:

```sh
python scripts/planar-heesch/strengthened.py --seconds 180 --checker /path/to/drat-trim
```

Selected unresolved census matches receive longer runs, preserving the shorter
attempts. Published identity prioritizes these retries; it supplies no corona
placements or constraints. `refine.py` records those separate runs.

`run.py` and the census resume existing result files. Use a separate `--out`
for a new record run. To repeat a census from scratch, use a clean workspace
copy of the scripts and catalog so existing artifacts are preserved.
