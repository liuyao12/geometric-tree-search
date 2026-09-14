# Joint boron training: shared weights, connected covers, search bottlenecks

14 September 2026. Follow-up to the exact all-occurrences obstructions.

## What changed

The same 16 geometric types (12 finite face groups and four fallback pairs)
now admit one common set of positive site weights that fills all six supplied
boron configurations. Every full 3×3×3 observation has a connected selected
positive-support network. Independent verification checks 18,171 atom totals,
13,419 selected occurrences, symmetry-role ties and scalar marking agreement.

This is joint training on all six observations, not held-out generalization.
It changes occurrence selection, not the earlier impossibility result: that
result required using every proposed occurrence simultaneously.

## Learning model and controls

Weights are learned on the declared grid {1/12, 2/12, …, 1}, with 157 roles
after witnessed symmetry ties. The grid is a hypothesis, not unrestricted
real-valued learning. Each occurrence has a binary inclusion variable. Binary
product constraints couple inclusion to the shared weight, and each atom's
total must be exactly 12 integer units. The feasibility objective does not
optimize sparsity, growth, physics or search cost. At least one occurrence of
every proposed finite-face type must remain in every input where it occurs;
this explicit training condition prevents dropping all large clusters.

The full-supercell model has 17,631 independent occurrence choices, 44,140
variables and 97,242 constraints. A 30-second run returned no incumbent:
unknown, not infeasible. A second, restricted training model groups primitive
translations using integer image lifts, template identities and symmetry-tied
site roles. All 653 observed translation orbits contain 27 occurrences. This
periodic selection lock is used only for training, never passed to the search
as a strategy or a unit-cell copying rule.

The first compact fit covers all atoms but is disconnected. For every observed
component, require selection of an occurrence crossing its cut. There are 86
distinct orbit-level cuts after deduplication. The second fit is connected in
all six full observations. Both compact solver calls took about 0.6 seconds
on this host, excluding setup and independent verification; this is not a
runtime advantage over the different unrestricted optimization problem.

All inferred weights are integers in units of 1/12. Scalar m-values are learned
from selected overlap equalities on the same geometric roles. They produce
78 observed equality classes, with no unobserved roles. Rotations act on site
positions; these scalar labels are invariant under the declared role ties.
No physical potential, bonding rule, species-specific coordination or occupancy
fraction was used. Anchors remain observed atom sites rather than learned
non-atomic support points.

## Reference search, not the training solver

Freeze the learned weights and markings. Give the unchanged point-search kernel
the full original occurrence pool, **not** the selected training answer. Remove
the periodic selection lock and connectivity cuts. Compare marked and unmarked
lanes on identical candidates, roots and budgets: 100,000 advances or 15 seconds
per lane. All target atom IDs are active generation-zero roots.

| Model | Candidate occurrences | Selected in connected training witness | Unmarked search | Marked search |
| --- | ---: | ---: | --- | --- |
| α | 108 | 108 | Complete, connected | Complete, connected |
| β-105 | 1,458 | 1,458 | Complete, connected | Complete, connected |
| β-106 | 4,779 | 3,186 | Budget unknown | Budget unknown |
| γ | 486 | 324 | Complete, connected | Complete, connected |
| τ-105 | 2,916 | 2,916 | Complete, connected | Complete, connected |
| τ-106 | 7,884 | 5,427 | Budget unknown | Budget unknown |

All completed searches use zero backtracks. γ needs one branch; α, β-105 and
τ-105 use only forced placements. The hard cases still backtrack extensively.
Different wall-clock cutoffs produce slightly different step counts between
lanes; those differences are not evidence of acceleration.

Nonconstant labels are not sufficient. α, β-105 and τ-105 have no disagreements
in their complete candidate pools. γ has local marking disagreements, but
capacity already forbids every such pair at that point. β-106 and τ-106 have
only 27 and 54 local site-pair disagreements respectively that pass that site's
capacity test. This counts local comparisons, not globally legal pairs or
measured pruning events. There is no demonstrated search-speed advantage.

## Verification and conformance scope

The independent training verifier reconstructs exact sums on all original
supercell atoms, checks retained types, shared roles, scalar equality classes,
selection uniqueness and graph connectivity. Tests reject changed weights,
missing/duplicated selections and altered connectivity counts. A small triangle
control learns half-weights jointly with selection.

The search harness checks global dead-before-forced-before-generation-first
decisions, independently rebuilds point/candidate incidence and reverse indexes
every 100 advances and at terminal states, and checks root semantic rollback.
A separate verifier rebuilds every candidate's t/m-values from the frozen
learning artifact and checks final totals, marking agreement and connectivity.
Synthetic controls exercise generation priority, which these all-root-zero
material tests do not. Root semantic rollback is not a claim of exhaustive
stack-restoration testing. Candidate identity is one stored observed occurrence;
no extra inventory restriction is imposed.

The candidate universe is complete only for the declared stored pool, not all
continuous poses. Geometric registrations are tolerance fits; exact filling is
on source atom IDs. Target coordinates and periodic boundaries are known. The
connected training witnesses establish feasibility within that finite pool, not
seed-driven growth, arbitrary extension or an infinite-lift certificate.

## Next scientific gate

The all-input fitting barrier is now passed for this library. The next bottleneck
is informative, transferable connection rules and search on the two difficult
models. Enlarged marking domains or contextual geometric anchors must be learned
without encoding target IDs or simply returning the training cover. Independent
condition-matched data and held-out reconstruction remain necessary. These six
models are not a common-temperature/pressure ensemble, and periodic replicas
are not independent samples.

## Reproduce

With the previously audited face-cluster folder and `precheck.json`:

```
python boron-face-joint-selection.py precheck.json unrestricted.json 12 30
python boron-face-periodic-selection.py precheck.json boron-face-clusters connected.json 12 30 connected
python verify-boron-face-joint-selection.py precheck.json connected.json verified.json
python test-boron-face-joint-selection.py precheck.json connected.json
node boron-face-reference-search.mjs precheck.json connected.json /absolute/path/kernel.mjs search-results
python verify-boron-face-search.py precheck.json connected.json search-results search-verification.json
```

Use new output paths. Python requires NumPy, SciPy and NetworkX plus the local
helpers; Node runs the unchanged published materials-growth-v2 kernel. Source
coordinate files are not republished; exported training selections, hashes,
summaries and scripts document this finite diagnostic.
