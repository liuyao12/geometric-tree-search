# Rotation-aware vector marking diagnostic

14 September 2026. Training-only study on the nine-cover boron ensembles.

## Question

Scalar equality labels mostly collapsed when valid training covers were pooled.
Would a vector transported by each motif's rotation support a useful nonconstant
marking? Give each template site a three-component vector v. For overlapping
occurrences, require R_a v_a = R_b v_b, where R acts on column vectors. Recompute
the rotations of template self-correspondences; scalar symmetry ties alone do
not specify vector transformation behavior.

No chemical potential, bonding rule, phase label or held-out coordinates enter
these equations. The hypothesis remains one vector per geometric template site,
not multiple marked variants of the same geometry.

## Exact-compatibility diagnostic

A spanning tree transports each vector from a component's root. Every remaining
edge imposes a cycle-closure condition on that three-dimensional root vector.
Stacking these conditions gives a small rank test, avoiding a large dense SVD.

In every fold the largest overlap component has numerical nullity zero at a
normalized singular-value tolerance of 1e-8. These components contain 99.4–100%
of the observed template-site variables. Thus the supplied floating-point pose
graphs exhibit no nonzero exactly consistent vector field on their main
components. This is numerical evidence on fixed poses, not an exact algebraic
certificate and not an exclusion of tolerance-aware fields or alternate poses.

Synthetic checks cover flat transport, a one-axis invariant under a rotation,
incompatible rotation loops, and invariance under a common world rotation.
An independent verifier checks the stored proper transports, existence of a
spanning tree supporting them, cycle residual matrices, ranks and direct vector
residuals. It verifies the supplied constraint graph, not exhaustive geometric
correspondence generation.

## Approximate fitting without forcing tree equations exactly

The tree-based diagnostic is not a global approximation method. We separately
build the full sparse overlap operator B on each largest component and request
the smallest eigenpair of BᵀB. Normalize the site-vector RMS magnitude to one.
The resulting fits have small average errors relative to their worst errors:

| Omitted model | Fitted site variables | Overlap RMS error | Maximum overlap error | Participation fraction |
| --- | ---: | ---: | ---: | ---: |
| alpha | 2250 | 0.128 | 7.14 | 0.633% |
| beta-105 | 2238 | 0.176 | 11.56 | 0.143% |
| beta-106 | 1932 | 0.152 | 5.94 | 0.692% |
| gamma | 2193 | 0.174 | 10.16 | 0.229% |
| tau-105 | 2148 | 0.167 | 10.46 | 0.187% |
| tau-106 | 1471 | 0.153 | 8.31 | 0.228% |

Errors are dimensionless marking-vector discrepancies, **not angstrom errors**.
Participation fraction is (Σ||v||²)² / (N Σ||v||⁴): it equals one for uniform
magnitude and becomes small when magnitude is concentrated. It is not literally
the fraction of nonzero entries. Only 9–81 site variables per fold have vector
norm above 0.1. The apparent low average mismatch is accompanied by severe
localization and large worst-case disagreements.

The direct verifier accumulates BᵀBv without using the sparse eigensolver,
checks the eigen-equation and recomputes RMS, maximum and participation metrics.
Eigen residuals are below 3e-12. These numerical checks are not certified global
optimization bounds. A different norm constraint, minimax objective or multiple
channels has not been ruled out by this experiment.

## Decision

Do not install these vector fits as growth rules. A training tolerance broad
enough to accept the observed worst errors is not evidence of selective useful
matching. No test-set accuracy or search advantage is claimed; the proposed
held-out evaluation was not run because the training diagnostic did not produce
a well-distributed, tightly agreeing field.

This diagnoses the current restricted representation, not GCTS in general.
The next hypothesis should examine context-dependent marked variants sharing a
geometric motif, and/or learned non-atomic anchor domains. Such variants must
be learned from training geometry and checked for transfer, rather than being
assigned by the known phase, unit cell or target coordinates.

The data remain structural controls rather than an independent common-T/P
ensemble. Full continuous pose coverage, connected seed growth and learned
general anchor placement remain open. The production growth engine is unchanged.

## Reproduce

Use the previous training dictionaries and cover ensembles. Keep
`ice-motif-dictionary.py` next to the new scripts; it supplies the already-used
proper rigid fitting helper. NumPy and SciPy are required. Output directories
must be new.

```
python test-transport-holonomy.py
python boron-vector-holonomy.py boron-holdout boron-cover-ensemble vector-cycles
python verify-transport-holonomy.py vector-cycles cycle-checks.json
python boron-vector-least-squares.py vector-cycles vector-fits
python verify-boron-vector-fit.py vector-cycles vector-fits fit-checks.json
```

Public summaries omit source coordinates and pose graphs. Local artifacts retain
source hashes, constraints, transport matrices, vectors and residual diagnostics.
