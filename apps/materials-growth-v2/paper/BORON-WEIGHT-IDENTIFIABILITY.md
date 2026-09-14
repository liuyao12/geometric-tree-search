# What do the boron observations determine about t?

14 September 2026. Exact conditional identifiability and a regularization control.

Fix the existing 16 geometric motif types, 157 symmetry-tied site roles, and the
six connected selected training fillings. Reconstruct each atom's equation
`sum(incidence multiplicity × shared weight) = 12`. The 18,171 equations reduce
to 166 distinct rows. Exact rational elimination gives **rank 156, nullity one**.
154 weights are individually fixed. The only variable roles, numbered 46, 75
and 118 in this dictionary, have weights `(a, 12-a, a)`. Positivity requires
`0<a<12`; the original twelfths grid admits exactly 11 choices, `a=1,...,11`.
The original fit used `a=1`. This is conditional on the selected occurrences:
it does not establish uniqueness under alternative decompositions or motifs.

An independently reconstructed incidence matrix has rank at least 156 modulo
the prime 1,000,003. The exported rational null vector proves rank at most 156.
Together these certify the exact rank, without floating-point thresholds.
Two hundred synthetic matrices check the rational elimination against modular
elimination. The full result exports equations and the null vector, without
atomic coordinates.

## Which family members supply constraints?

Remove one configuration's equations, leaving the geometric dictionary and
the other five selected witnesses fixed:

| Omitted configuration | Equality rank | Remaining weight degrees of freedom |
| --- | ---: | ---: |
| None | 156 | 1 |
| α | 154 | 3 |
| β-105 | 150 | 7 |
| β-106 | 128 | 29 |
| γ | 149 | 8 |
| τ-105 | 138 | 19 |
| τ-106 | 104 | 53 |

These are equality-space dimensions, not counts of independent physical
parameters, admissible bounded solutions, or unseen material states. Some
roles become unobserved when a configuration is removed. The dictionary itself
was learned from all six inputs: this is a constraint-contribution audit, not
a wholly held-out learning experiment. The high-information difficult variants
should not be replaced by more replicas of easy structures. Repeated periodic
equations do not increase rank.

## Balanced-weight reconstruction control

Enumerate the 11 conditional grid solutions and maximize the minimum weight
among the three non-fixed roles. This selects `a=6`, giving `(6,6,6)` in capacity
12 units. All other t-values, all scalar m-values and all occurrences remain
unchanged. An independent verifier checks all 18,171 atom sums, marking
equalities and six connected training witnesses again.

Run the full candidate pools, without supplying the selected answer to search,
with and without markings: 12 runs, each capped at 100,000 advances or 15 seconds.
The reference generation-first scheduler uses the previously audited linear
decision implementation and justified parent-local failed-choice exclusions.
All target points are generation-zero roots. The search still completes α,
β-105, γ and τ-105 with connected exact covers; β-106 and τ-106 remain unknown
in both lanes. Independent final-state reconstruction and incidence audits pass.
This changes the admitted t-model, so it is not a same-problem speedup comparison.
No advantage in completion is demonstrated, and the other ten parameter values
have not all been searched in this experiment.

## Consequence

For these selected fillings, arbitrary weight choice is confined to three roles;
balancing them alone does not solve the reconstruction bottleneck. The broader
learning problem must still consider alternative occurrence selections, shared
geometric motifs and informative overlap markings. Neither the exact rank nor
this control establishes continuous-pose completeness, seed-driven growth,
condition-matched ensemble learning or a useful transferable GCTS marking.

## Reproduction

Use the original `precheck-v2.json` and `periodic-connected-c12-v1.json`:

```
python boron-weight-identifiability.py INPUT LEARNING CERTIFICATE
python test-boron-weight-identifiability.py INPUT LEARNING CERTIFICATE
python boron-balanced-weights.py LEARNING CERTIFICATE BALANCED
python verify-boron-face-joint-selection.py INPUT BALANCED TRAINING_CHECK
node boron-face-reference-search.mjs INPUT BALANCED KERNEL SEARCH_DIR linear-exclusions 100000 15
python verify-boron-face-search.py INPUT BALANCED SEARCH_DIR SEARCH_CHECK
```

The refit artifact records its parent hash and changed roles. Inherited MILP
metadata describes the parent fit, not a second MILP solve. Production growth
code is unchanged; this is an isolated research control.
