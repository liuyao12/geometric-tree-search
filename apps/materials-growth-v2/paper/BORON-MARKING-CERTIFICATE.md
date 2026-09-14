# Exact finite-model certificate for the learned boron markings

14 September 2026. A solution-preservation result, not a speedup or transfer claim.

## Statement

For each of the six original fixed observed candidate pools and original learned
t-values, every complete unmarked point filling satisfies the learned scalar
m-values. Thus marked and unmarked **complete solution sets coincide** in these
finite models. Partial-state legality need not coincide: markings can reject
partial choices that cannot be completed. This is precisely a setting in which
redundant markings could accelerate search, though our runs do not establish
an advantage.

The statement concerns the supplied atom IDs, complete target obligations and
stored occurrences. It is not an infinite-growth theorem, a guarantee under
new rotations/registrations, or a same-condition material-generalization result.
It concerns the original weights, not the separately balanced-weight control.

## Exhaustive conflict coverage

Enumerate every pair of distinct occurrences whose assigned scalar labels
disagree at any shared atom. Missing labels would be unconstrained; all labels
in this fitted model are observed. First check whether the pair exceeds t
capacity at any shared point, not merely the point with the marking conflict.

| Structure | Distinct m-conflicting pairs | Direct capacity exclusion | Exact completion exclusion |
| --- | ---: | ---: | ---: |
| α | 0 | 0 | 0 |
| β-105 | 0 | 0 | 0 |
| β-106 | 648 | 621 | 27 |
| γ | 324 | 324 | 0 |
| τ-105 | 0 | 0 | 0 |
| τ-106 | 1,485 | 1,431 | 54 |

Counts are pairs, not the earlier local point-pair comparison counts. Each of
the remaining 81 pairs is t-compatible as a two-placement partial state but
cannot occur together in any complete unmarked filling. No conflict remains
uncertified. Pairwise coverage suffices because scalar marking agreement is
a pairwise condition.

## Rational certificate

Let A contain each candidate's integer t-contributions, b be the all-12 target,
and x be the selection vector. Relax binary selection to `0 <= x <= 1` while
retaining `A x = b`. For a conflicting pair (i,j), let c have ones at i and j.
Any rational vectors y and z satisfying

```
z >= 0
A^T y + z >= c
```

give the upper bound `c^T x <= b^T y + sum(z)`. For all 81 pairs, the exported
certificate has bound exactly **1**, so both candidates cannot be selected.
The bound even holds for the relaxed fractional completion problem.

A numerical linear optimizer proposes y. We rationalize it and reconstruct
`z_k = max(0, c_k - (A^T y)_k)` exactly. A separate standard-library verifier
rebuilds the candidate matrix from the original input, checks every rational
inequality, checks the bound, and independently enumerates all marking-conflict
pairs to establish coverage. The verifier neither imports nor calls the solver.
It rejects 162 mutations that remove the proof coefficients or falsify bounds.
Proofs use 2–10 nonzero atom multipliers and 1–2 nonzero upper-bound multipliers;
the inequalities are still checked against every candidate column. Sparse
support alone does not authorize transferring them to another candidate pool.

No selected training witness, finite-face-retention constraint, connectedness
cut or periodic selection lock enters these completion proofs. They apply to
all complete fillings of the frozen base point model, including disconnected
ones, with each stored placement usable at most once.

## Consequence for learning

The earlier alternative-fillings experiment provided empirical preservation
checks. This audit strengthens that observation to an exact statement for the
full finite solution sets, rather than just the tested witnesses. It does not
prove that the original equality-learning procedure always produces redundant
markings. Such a claim would require a general argument or certificates for
each new model.

The project still needs useful, transferable connection markings and successful
reference search on the two difficult models. These certified markings are
safe but have not demonstrated adequate acceleration. A next candidate rule
can now be compared against an explicitly solution-preserving marked baseline,
without conflating rejection counts with scientific or computational benefit.

## Reproduce

```
python boron-marking-redundancy.py INPUT LEARNING PAIRS
python boron-conflict-completion.py INPUT LEARNING PAIRS PROOFS
python verify-boron-conflict-completion.py INPUT LEARNING PROOFS CHECK
```

Use `precheck-v2.json` and the original `periodic-connected-c12-v1.json`.
The proof generator requires NumPy/SciPy. Public proofs contain sparse
coefficients and candidate/point indices, not atomic coordinates. The production
growth engine and reference scheduler are unchanged.
