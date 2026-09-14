# Different decompositions, the same learned point rules

14 September 2026. A training-decomposition robustness control, not a GCTS
reference-search success or a new set of material observations.

We froze the original learned t-values and gave each stored occurrence its own
binary selection variable. Unlike the earlier training fit, selections were
not locked into primitive translation orbits. Each atom must receive exactly
12 integer units. The parent requirement to retain each finite-face type where
observed remains. No marking equalities were imposed on this optimization.
Two reproducible random linear objectives (seeds 101 and 202) were tried per
configuration. These do not uniformly sample covers or physical states.

A specialized MILP solver searches the full observed occurrence pool. If a
cover is disconnected, crossing constraints for its components are added and
the solver is called again, at most eight calls with two-second per-call limits.
These connectivity cuts define a connected-training-cover problem, not the
unmodified reference tree search. No chemistry, energy or formation-history
inputs are used. The coordinates and candidate pool are supplied.

## Results

All twelve attempts returned connected exact fillings. Independent integer
reconstruction, graph traversal and marking checks accepted all twelve; 24
mutated fillings (missing or duplicated occurrence) were rejected.

| Structure | Changes from original selection, seed 101 / 202 | Old marking disagreements |
| --- | ---: | ---: |
| α | 0 / 0 | 0 |
| β-105 | 0 / 0 | 0 |
| β-106 | 1,077 / 1,144 | 0 |
| γ | 0 / 0 | 0 |
| τ-105 | 0 / 0 | 0 |
| τ-106 | 890 / 865 | 0 |

Changes count symmetric differences of selected occurrence sets, not atom
displacements. Both hard configurations have two distinct new decompositions;
the easier cases reproduced their parent witnesses. This does not prove those
easier decompositions unique. The alternative hard-case covers were found
without enforcing the learned m-values, but all satisfy them afterwards.

Adding these twelve fillings to the original six introduces **no new distinct
weight equations**: the union still has 166 rows of rank 156 on 157 roles.
All added overlap equalities are already compatible with the 78 original scalar
classes, so they do not force any merger of those classes. This restricted
stress test does not reveal the decomposition sensitivity previously seen in
the separate ice binary-marking experiment. It does not prove that every valid
boron decomposition preserves the markings.

## What this changes

There are substantially different connected decompositions of the difficult
configurations under the same learned point model. Training against one chosen
occurrence list as though it were unique would therefore be unjustified. The
new witnesses can be used as alternative positive fillings in subsequent
learning. They do not themselves add new local equality information.

The specialized optimizer completes cases that our audited reference-tree runs
leave budget-unknown. This is a useful baseline and a warning against claiming
a GCTS advantage, not a controlled timing comparison: solver objectives,
connectivity constraints, implementation and budgets differ. We did not route
these witnesses into the production growth engine or replace the user's search
algorithm with the optimizer. The next learning step must produce useful
connection constraints or cluster compositions, not merely replay these covers.

These six boron inputs remain cross-structure controls, not a verified
same-condition ensemble. The shared-family, held-out, seed-driven growth goal
is still open.

## Reproduce

```
python boron-alternative-fillings.py INPUT LEARNING ALTERNATIVES
python verify-boron-alternative-fillings.py INPUT LEARNING ALTERNATIVES CHECK
python boron-ensemble-weight-audit.py INPUT LEARNING ALTERNATIVES WEIGHT_CHECK
```

Use the original `precheck-v2.json` and `periodic-connected-c12-v1.json`.
The generator requires NumPy, SciPy and NetworkX. The filling verifier uses
only the standard library and does not import the solver. Selection hashes and
aggregate checks are published; coordinate input remains local.
