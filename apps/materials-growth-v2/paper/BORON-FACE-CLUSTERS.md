# Larger geometry-only boron cluster proposals

14 September 2026. Discovery control, not a completed weighted growth model.

## Method

Build a periodic short-contact graph with radius equal to 1.15 or 1.35 times
the supplied model's median nearest-neighbor distance. Enumerate graph
triangles and merge triangles that share an edge. No atom is designated a
cluster center, and no cluster size, polyhedron, chemical bond or boron-specific
coordination is supplied. These are geometric graph edges, not assigned bonds.

Track integer periodic-image offsets while traversing each component. A nonzero
offset around a loop identifies winding: such a component is not exported as a
finite motif. Keep every graph edge outside finite face components as a fallback
pair and any uncovered atom as a singleton. This preserves atom coverage but
does **not** establish additive t-values or learn matching rules.

## Observed proposals

At radius multiplier 1.15, the finite components per supplied primitive/model
cell are:

| Source model | Finite component counts per supplied cell | Winding components present? |
| --- | --- | --- |
| alpha | one 12-site group | No |
| beta-105 | four 12-site and two 28-site groups | No |
| beta-106 | one 28-site and one 29-site group | Yes |
| gamma | two 14-site groups | No |
| tau-105 | eight 12-site and four 28-site groups | No |
| tau-106 | two each of 12-, 28- and 29-site groups | Yes |

All finite size counts scale exactly between 2×2×2 and 3×3×3 supercells, at
both tested radii. This rules out a simple boundary/corner counting artifact
for these counts. It is not a proof of universal cluster correctness.
Winding components in beta-106 and tau-106 remain unresolved by this proposal
rule; their edges are retained as fallback pairs instead of cutting arbitrary
finite clusters out of the periodic network.

The second radius exposes sensitivity: beta-105 and tau-105's 28-site groups
become 29-site groups, gamma's 14-site groups become 18-site groups, and alpha
acquires additional three-site groups. Neither radius is claimed optimal.

## Proper-rotation dictionary and figure

Fit the finite components at multiplier 1.15 across all six 3×3×3 samples using
a greedy, maximum-site-error tolerance of 0.03 Å. Distance-compatible anchor
triples propose proper rotations; full-site assignment and Kabsch refinement
verify the fit. No reflected poses are admitted. Accepted registrations are
witnesses; failed proposals do not certify absence of every approximate isometry.

The 783 finite component occurrences register to 12 templates: seven 12-site,
one 14-site, three 28-site and one 29-site templates. None is a singleton
occurrence. All 405 observed 12-site components have graph connectivity
isomorphic to the icosahedral graph, checked **after** discovery. This does not
claim their coordinates form perfect regular icosahedra.

The figure shows actual recovered template coordinates in separate projections,
rescaled independently. It excludes fallback pairs. Consequently 12 is not the
size of a complete growth library, and comparing it directly with the earlier
857-triangle dictionary would mix different supports and tolerances.

## Independent checks

The verifier rebuilds the periodic neighbor graph with a separate image-tree
calculation. A reciprocal-cell plane-height bound validates the neighboring-image
enumeration range for these supercells. It checks replicated source coordinates,
triangle partitions with an independent graph-components routine, integer winding,
finite lifts, fallback coverage, every accepted proper-rotation fit and graph
isomorphism claims. All 24 supercell/radius runs pass; all atoms are represented
by a finite component, fallback pair or singleton.

Synthetic registration tests cover rotated/permuted 4-, 12- and 29-site groups,
and reject a reflected generic tetrahedron and a scaled distortion. These are
not complete tests of arbitrary continuous registration or search.

## What this changes

We now have larger, irregular, recurring geometric supports with explicit
periodic-boundary handling, rather than only three-site motifs and abstract
environment labels. This is a useful input to the next learning stage.
Shared t-values, extended m-domains, support selection and matching still need
to be learned and verified on these larger proposals before tree search.

All six inputs construct this exploratory dictionary. Replicated cells are not
independent training samples, and no held-out transfer is claimed. The models
are not a documented common-temperature/pressure ensemble. No production app
or growth rules were changed.

Source: [An et al. (2016), supplementary coordinate models](https://authors.library.caltech.edu/records/dcaev-djw82).

## Reproduce

Use the audited source input and Python with ASE, NumPy, SciPy and NetworkX.
Keep the new helper scripts together; output directories must be new.

```
python boron-face-clusters.py boron-data/input-audit.json boron-face-clusters
python test-rigid-cluster-match.py
python boron-face-dictionary.py boron-face-clusters boron-face-clusters/dictionary.json
python verify-boron-face-clusters.py boron-data/input-audit.json boron-face-clusters verification.json
python render-boron-face-dictionary.py boron-face-clusters templates.svg
```

Local artifacts include edge-image offsets, winding witnesses, finite lifts and
registration poses. Public summaries and the derived figure are not substitutes
for those replay artifacts; raw source CIF files are not republished here.
