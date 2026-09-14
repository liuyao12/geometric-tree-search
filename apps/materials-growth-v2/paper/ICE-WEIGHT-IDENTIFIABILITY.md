# What the selected ice tilings determine about t

14 September 2026. Exact conditional inference, not unrestricted inverse-tiling learning.

The previous positive-cover control chose two-incidence tilings compatible with
t=1/2. That choice cannot itself demonstrate discovery of the denominator. We now
solve the full shared-weight equation family **conditional on those selected
tilings**, without prescribing numerical weights in this inference step.

## Complement equations versus equality markings

Every training point has two selected incidences, so its equation is
`w_u + w_v = 1`. Treat this as an edge on template-site variables; a self-edge is
allowed when the same role contributes through two distinct occurrences.

Following a path alternates `a` and `1-a`. An odd cycle forces `a=1/2`;
a connected bipartite component retains one free parameter in [0,1]. An unobserved
site retains its own unconstrained weight. These are complete solutions to this
conditional linear system, with no numerical rank tolerance.

This also explains why t and m behave differently on the same incidence graph:
scalar m-equalities identify all variables in a connected component, whereas
t-complement equations distinguish its parity. Equality-component counts alone
do not establish that the t-values have been learned.

| Training witnesses per configuration | Forced-half sites | Free complementary sites | Unobserved sites | Total free parameters |
| --- | --- | --- | --- | --- |
| One | 1,596 | 18 (9 parameters) | 486 | 495 |
| Two | 1,806 | 12 (6 parameters) | 282 | 288 |

There are 2,100 site variables. The two-witness system has 55,200 training rows
and 15,127 distinct complement edges. Stored odd-cycle certificates establish
the forced values. An independent verifier rebuilds every equation from the
training selections, checks component connectivity and odd cycles, and verifies
the complete affine solution using rational arithmetic.

## Does the remaining ambiguity matter for validation?

For each original selected validation cover, we ask whether its point sums equal
one for **every** training-consistent weight assignment, not merely the chosen
half-weight representative. Shared free parameters are kept shared across all
occurrences; there is no per-atom normalization.

| Phase | Validation covers | Covers whose filling is independent of remaining weight choices |
| --- | --- | --- |
| Ih | 25 | 24 |
| II | 25 | 17 |
| VI | 25 | 22 |
| VIII | 25 | 23 |

Thus 86/100 covers are invariant under all remaining weight choices. In the other
14, a total of 87 atom sums depend on free parameters. This does not prove those
configurations cannot be reconstructed: the half-weight choice already fills
them, and alternative covers may avoid the underdetermined sites. It does show
that reporting all their weights as learned from these training witnesses would
be unjustified.

A second implementation perturbs each of the 288 independent parameters separately
using integer quarter-units. It verifies all training sums and reproduces the
86-cover result. Testing this affine basis establishes constancy of each linear
point sum over the parameter domain. Perturbations use strictly positive weights;
the dependence is not an artifact of allowing empty tiles at zero endpoints.

## Scope and next experiment

This is an exact identifiability audit within a restricted observed candidate
model. It does not fix the selection bias toward two-incidence tilings, learn
new geometric support, prove continuous-pose completeness, or improve the earlier
97/100 finite-search result. The pilot remains developmental, not an independent
confirmatory test. It is not evidence of a Nature-level result.

Here “unobserved” means unused by the selected training tilings, not absent from
the raw geometric candidate pool: every template was proposed from training data.
Targeted additional occurrence witnesses should therefore be tested before assuming
that new coordinate data are the only remedy. Independent configurations can then
test whether the resulting constraints transfer consistently. The 288 free parameters
must not silently receive fitted-looking values or be removed just to improve
the reported completion rate. Joint occurrence and weight inference, with reusable
motifs and nontrivial positive overlaps, remains the intended problem.

## Reproduction

```
python ice-weight-identifiability.py DICTIONARY WEIGHT_MODEL FIRST_SELECTION SECOND_SELECTION
python verify-ice-weight-identifiability.py DICTIONARY WEIGHT_MODEL WEIGHT_CHECK FIRST_SELECTION SECOND_SELECTION
python ice-weight-transfer.py DICTIONARY WEIGHT_MODEL FIRST_SELECTION PROVENANCE TRANSFER
python verify-ice-weight-transfer.py DICTIONARY WEIGHT_MODEL FIRST_SELECTION TRANSFER TRANSFER_CHECK
```

The first selection supplies the validation covers; only training rows from both
selections enter inference. Omit the second selection for the one-witness audit.
Dependencies are NumPy, SciPy and NetworkX. The geometric dictionary and selection
artifacts are those described in ICE-THERMAL-OVERLAP.md and ICE-SELECTED-MARKINGS.md.
