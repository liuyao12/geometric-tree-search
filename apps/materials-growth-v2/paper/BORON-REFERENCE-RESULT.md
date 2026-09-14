# Boron reference-search pilot: nonconstant markings, mixed outcomes

14 September 2026. This follows the selected-occurrence training control.

## Result

The reference point-value search finds exact finite covers for all six omitted
boron configurations without additional markings. Scalar markings learned
from the five selected training covers permit verified covers in five cases;
the sixth reaches the 100,000-step budget without completion.

| Omitted model | Training scalar classes | Unmarked backtracks | Marked backtracks | Marked outcome |
| --- | ---: | ---: | ---: | --- |
| alpha | 46 | 3 | 6 | Finite cover |
| beta-105 | 42 | 21 | 177 | Finite cover |
| beta-106 | 37 | 0 | 24 | Finite cover |
| gamma | 43 | 258 | 258 | Finite cover |
| tau-105 | 58 | 843 | 44 | Finite cover |
| tau-106 | 19 | 78707 | 88390 | Budget unknown |

The tau-105 reduction is not a general acceleration result. Three cases require
more backtracking, gamma is unchanged, and tau-106 remains unresolved in the
marked lane. These are single deterministic candidate-order pilots, not a
multi-seed benchmark. Timings include audit overhead but exclude training and
candidate construction; they must not be presented as end-to-end speedups.

## Marking learning

Unlike the earlier all-occurrences fit, use only the selected training covers
whose t=1/3 coverage was independently verified. Each template site has a scalar
variable. Union variables at overlapping training atoms and through the declared
template self-correspondence ties. Assign separate scalar values to the resulting
observed equality components. Components with no training observations are
**unassigned**, not zero or an invented negative class.

This yields nonconstant markings, but distinct values between separate equality
components are a chosen learned hypothesis: positive observations do not prove
those components must disagree. The markings may encode arbitrary choices of
training covers, not necessary properties of the material. We have not shown
that rejected connections are geometrically or physically impossible.

Assigned template variables / total by fold are 978/2553, 981/2538, 837/2190,
945/2487, 870/2466 and 648/1899. In the five completed marked test covers,
markings are assigned at 5/12, 98/105, 88/106, 19/28 and 202/210 atoms. Missing
markings remain unconstrained. Held-out coordinates do not enter learning.

## Search model and conformance boundary

- The unmodified `apps/materials-growth-v2/kernel.mjs` PointSearch engine runs
  both lanes. Integer capacity is 3, and every candidate contributes 1 at each
  of its three target atom IDs. Scalar markings are exact singleton intervals.
- Every finite target atom is an active root obligation at generation zero.
  The scheduler checks global dead points, global forced moves, then earliest
  generation/minimum candidate count within generation. Real runs therefore
  exercise a generation tie; a separate synthetic test checks generation order.
- Both lanes use identical candidate IDs, t data, ordering, target and budgets.
  Marked role variants are retained. Variants with the same template and atom
  support share an explicit base-placement inventory and may be selected only
  once. Its dependencies are on shared t-support. This is a declared finite
  adapter identity rule, not a new geometric gate in the kernel.
- Each run has a 100,000-step or 15-second budget, whichever occurs first.
  Budget exhaustion means unknown, not impossibility.
- Independent exhaustive incidence/reverse-incidence checks rebuild legality
  from selected placements, including marking and inventory conflicts. They run
  every 100 steps and on completion, alongside the kernel's own audit.
- Exact final integer coverage, scalar agreement, inventory uniqueness and
  training marking partitions are checked in a separate Python verifier.
  Root point/mark/graph state is checked after rollback. This does not certify
  stack serialization, arbitrary restart or every dynamic-domain behavior.
- Candidate completeness is only relative to the declared finite pool. Poses
  were registered using known target coordinates, proper Kabsch rotations and
  a 0.01 Å tolerance. This is not blind growth, continuous-pose exhaustion or
  an infinite periodic-lift certificate.

## Connectivity caveat

Unmarked cover component counts are 1, 4, 1, 1, 1, 1. Completed marked cover
counts are 1, 1, 1, 1, 3. In particular, the faster tau-105 marked result is
disconnected whereas its unmarked result is connected. The declared finite
point-cover task permits both, but they are not equivalent evidence of connected
material growth. No connectedness constraint was silently added.

The proposed marking hypothesis is therefore not ready to replace the app's
growth rules. Independent data at documented matching conditions, richer anchor
learning, robustness to occurrence-selection choices, and coordinate-blind
growth remain open. The production growth app is unchanged.

## Reproduce

Use the previous boron holdout/selection artifacts and dependencies. Keep the
new scripts with `presearch-markings.py`. Pass the exact kernel file as an
explicit argument; its SHA256 is recorded in the search summary.

```
python boron-selected-markings.py boron-holdout boron-selected boron-marks
node test-ice-search-order.mjs /path/to/kernel.mjs
node boron-reference-search.mjs boron-alternatives boron-marks boron-selected /path/to/kernel.mjs boron-search
python verify-boron-reference.py boron-holdout boron-alternatives boron-selected boron-marks boron-search verification.json
```

The scheduler test's historical filename does not imply ice-specific test data.
Output directories must be new. Local search artifacts contain the full point
models and selected IDs. Public summaries and methods omit source coordinates.
