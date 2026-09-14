# Larger boron clusters: exact filling before search

14 September 2026. Geometry-only, all-occurrences training diagnostic.

The previous face-connected proposal covered the atoms but did not provide
additive tile weights. We now complete that missing pre-search check on all six
2016 coordinate models, using the 3×3×3 observations at radius multiplier 1.15.

## Model and learning

Keep the 12 registered finite templates and retain every fallback pair with
its periodic image offset. Centered pair templates are grouped greedily when
their maximum site-fit error is at most 0.03 Å (half their length difference).
This adds four pair types: 16 types and 219 site variables in total.

Learn one shared t-value per template site, maximizing the minimum weight,
subject to every atom's occurrence contributions summing to one. All proposed
occurrences are used; selecting a subset is not part of this model. Repeated
supercell equations are deduplicated for fitting, but verification checks every
atom. A second lane ties roles under witnessed proper self-registrations and
ties the endpoints of each pair by their exact proper rotational symmetry.
Approximate self-registration enumeration is not certified exhaustive.

Successful weights are reconstructed as rational numbers and independently
checked. Scalar m-labels are learned by equality closure on observed overlaps
and the declared role ties. They are invariant scalars on atom-site anchors,
not physical potentials. These anchors remain proposed from observed atom
positions; non-atomic anchor discovery is not solved here.

## Results with role ties

| Input | Exact positive filling | Minimum t | Scalar equality classes |
| --- | --- | --- | --- |
| α | Pass | 1/2 | 2 |
| β-105 | Pass | 1/6 | 5 |
| β-106 | Exact restricted obstruction | — | — |
| γ | Pass | 1/3 | 2 |
| τ-105 | Pass | 1/6 | 5 |
| τ-106 | Exact restricted obstruction | — | — |
| All six jointly | Exact restricted obstruction | — | — |

The untied lane has the same pass/fail pattern. Thus symmetry ties are not
responsible for the failing cases. The successful fits are separate fits
within a common geometry dictionary; there is no successful shared family-wide
t-field yet. Nonconstant m-labels do not by themselves establish useful pruning.

Failures are stronger than an LP status: exported rational Farkas witnesses
satisfy Aᵀy ≥ 0 and bᵀy < 0 exactly. If nonnegative weights w satisfied Aw=b,
then yᵀAw would be nonnegative and yᵀb negative, a contradiction. The verifier
reconstructs permitted equations from the actual occurrences, checks each
witness row belongs to them, and evaluates the certificate with rational
arithmetic. It also checks source hashes, pair image lifts, role-fit witnesses,
all positive filling sums and m-agreement. Eight successful lane/input fits and
six restricted obstructions are verified. Mutation tests reject a zeroed
weight, altered obstruction value and missing occurrence.

## Interpretation and next experiment

This rejects the particular all-occurrences, shared-template weighting model,
not the existence of these crystals or the GCTS approach. The hard β-106 and
τ-106 cases have winding components represented by many fallback pairs. The
next experiment should jointly learn occurrence selection and weights, and/or
propose finite irregular supports from that network. It must retain the hard
cases, not silently replace them with easier crystals or a unit-cell copier.

No tree search was run on these new large templates. All six inputs contribute
to the dictionary, their supercell replicas are not independent samples, and
they are not a condition-matched thermodynamic ensemble. This does not establish
blind reconstruction, extension, physics, or a materials-science speedup.

## Reproduce

With the previously audited face-cluster folder and its dictionary:

```
python test-rigid-cluster-match.py
python boron-face-precheck.py boron-face-clusters precheck.json
python verify-boron-face-precheck.py boron-face-clusters precheck.json verification.json
python test-boron-face-precheck.py boron-face-clusters precheck.json
```

Dependencies: NumPy, SciPy and the existing local helper modules (whose imports
also require ASE). Output files must not already exist. The public summary
omits input coordinates; local artifacts retain full fits and proof witnesses.
