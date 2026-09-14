# Boron: shared three-site filling, 14 September 2026

One geometry-only dictionary and one learned positive t assignment can satisfy
all six coordinate models in the 2016 supplement simultaneously, at a 0.01 Å
registration tolerance. This is a verified training-configuration precheck,
not held-out reconstruction, a learned growth mechanism, or GCTS acceleration.

## Results

| Supplied model | Atoms | Three-site precheck, 0.05 Å | Three-site precheck, 0.01 Å |
| --- | ---: | --- | --- |
| alpha | 12 | Exact positive filling | Exact positive filling |
| beta-105 | 105 | Exact positive filling | Exact positive filling |
| beta-106 | 106 | Numerical LP infeasibility | Exact positive filling |
| gamma | 28 | Exact positive filling | Exact positive filling |
| tau-105 | 210 | Exact positive filling after rational polishing | Exact positive filling |
| tau-106 | 212 | Numerical LP infeasibility | Exact positive filling |
| All six, one shared t assignment | 673 | Numerical LP infeasibility | Exact positive filling after rational polishing |

Both runs register 9,147 three-site occurrences. At 0.05 Å there are 89 motif
types, with no singleton occurrences. At 0.01 Å there are 857 types, including
60 that occur only once; 406 types appear in just one of the six configurations.
Thus success comes with substantially less geometric compression. The tighter
tolerance was investigated after inspecting the wider-tolerance failures, not
as a preregistered held-out experiment.

The successful separate 0.05 Å fits all yield one scalar marking class. At
0.01 Å the separate beta-105 and tau-105 fits allow two scalar classes, but
pooling the six configurations merges all 2,571 site variables into **one**
class. The pooled marking therefore cannot discriminate connections. Positive
overlap equations permit constant markings; they do not establish forbidden
connections or a useful nonconstant representation.

## Method and exactness

Inputs are the independently audited, fully occupied coordinate models from
https://authors.library.caltech.edu/records/dcaev-djw82 . They share element B,
but are not documented as a common temperature/pressure ensemble. No phase
label, chemical rule, force field, or formation-history rule enters fitting.

For each periodic quotient, choose radius 1.35 times its median nearest-neighbor
distance. Propose every distinct three-atom-ID support containing a two-edge
path within that radius. If several image lifts share the same three IDs,
retain the first encountered lift: this is a finite-quotient control and not
complete periodic-image enumeration. Lift the two edges with minimum-image
vectors, without converting crystallographic occupancy into t weights.

Fit each support to the first acceptable training representative over all six
site permutations using proper Kabsch rotations. The error criterion is maximum
site displacement. Templates have a centroid coordinate gauge; these are not
learned non-atomic anchor locations. All six configurations construct the
dictionary, including in the separate-weight fits. There is no holdout here.

Each template site has a shared t variable. Template self-matches within the
same tolerance tie corresponding site t and scalar m variables. This declared
approximate-symmetry restriction avoids assigning arbitrary directional weights
to interchangeable sites; it is not an exact symmetry-group certificate.
Every proposed occurrence is included, and each observed atom's contributions
must sum to one. Linear programming maximizes the minimum site weight.

Floating solutions are reconstructed as fractions. Where direct rounding fails,
exact sparse Gaussian elimination enforces the integer incidence equations,
using rounded LP values only for free variables. A witness passes only if all
active weights are strictly positive, every point total is exactly one, and
the symmetry equalities hold exactly. Marking labels are equality components
of overlaps and template self-matches. The exact claim concerns t/m arithmetic
on atom IDs; geometric registration remains floating-point within tolerance.

The independent verifier checks all 9,147 poses, determinant +1, orthogonality,
point maps, lattice-image congruence, path geometry, rational coverage, and
marking agreement. Mutation tests reject altered transforms, point identities,
weights, and markings. Numerical infeasibility reports are not independent
infeasibility certificates.

## Algorithm conformance boundary

No tree search is run. There is no complete continuous candidate universe,
frontier graph, generation scheduler, or rollback claim in this experiment.
Known-position occurrences cannot be passed off as blind proposals. The
all-occurrences restriction may itself prevent a feasible shared fit; its
failure does not exclude other selections or larger motifs. Learned anchor
placement, informative marking representations, held-out family transfer, and
coordinate-blind reconstruction remain unresolved.

## Reproduction

Use Python with NumPy, SciPy, ASE and Gemmi. Keep the listed scripts together;
the geometry helper is `ice-motif-dictionary.py` (its import does not read ice
data). The audit downloads original CIFs and verifies their hashes. Source
coordinate geometry is not redistributed with this aggregate report.

```
python boron-input-audit.py boron-data
python boron-triple-precheck.py boron-data/input-audit.json triples-005.json .05
python boron-triple-precheck.py boron-data/input-audit.json triples-001.json .01
python verify-boron-triples.py boron-data/input-audit.json triples-005.json
python verify-boron-triples.py boron-data/input-audit.json triples-001.json
python test-boron-triples.py boron-data/input-audit.json triples-001.json
python summarize-boron-triples.py boron-triple-summary.json triples-005.json triples-001.json
```

Other dependencies: `presearch-markings.py`. These scripts deliberately refuse
to overwrite output artifacts. The production growth app is unchanged.
