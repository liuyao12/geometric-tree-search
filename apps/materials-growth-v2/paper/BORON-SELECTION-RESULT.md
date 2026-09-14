# Boron: select occurrences during training, then freeze the model

14 September 2026. Development follow-up, not an independent benchmark.

## Two changes tested separately

First, keep the previous learned site weights and enumerate every template and
site permutation, not just the first acceptable match. Each gets a proper
Kabsch fit within 0.01 Å to a known-coordinate support. Every fold still has
points where the exact sum of all available weights is below one:

| Held out | Distinct mapped candidates | Under-capacity points |
| --- | ---: | ---: |
| alpha | 153 | 12 |
| beta-105 | 2285 | 18 |
| beta-106 | 1981 | 27 |
| gamma | 336 | 20 |
| tau-105 | 3986 | 28 |
| tau-106 | 3474 | 62 |

Thus no subset of these **finite pools** can fill all points with the old
weights. This is an exact capacity obstruction for the stored candidate pool,
not a continuous-geometric impossibility certificate. Replacing the original
proposal radius with a library-derived bound (largest second-shortest template
edge plus twice the fit tolerance) gives the same candidate counts.

Second, change the training model. Keep the training-only geometric dictionaries
from the five-input holdout runs, but allow occurrence selection. Choose the
smallest feasible denominator k from {2,3,4,6,12}, assigning every template site
the same t=1/k. For each training configuration, select binary occurrences whose
integer incidences sum to k at every atom. This is a declared, simpler uniform
weight hypothesis, not unrestricted learned site weights. Its search space was
chosen after observing the prior failures.

In every fold, k=2 fails an exact divisibility test and k=3 admits verified
training covers. Freeze k before reading the omitted configuration's candidate
pool. With this frozen model, subset selection produces exact integer covers
for all six held-out configurations:

| Held out | Selected three-site placements | Positive-support components |
| --- | ---: | ---: |
| alpha | 12 | 3 |
| beta-105 | 105 | 7 |
| beta-106 | 106 | 1 |
| gamma | 28 | 1 |
| tau-105 | 210 | 1 |
| tau-106 | 212 | 6 |

## What this establishes

The old all-occurrences rule was too restrictive for these transfer tests.
A simpler weight model coupled to occurrence selection can transfer finite
coverage, using the same frozen geometric dictionaries and candidate pools.
The independent verifier checks training and test integer incidences, all
registered candidate poses, the old-weight rational capacity deficits, and
the connected-component counts. Tests reject missing, repeated and invalid
placement indices. Counts and witnesses are reproducible from the scripts.

## What remains unresolved

- Three covers are disconnected. They do not establish connected seed growth;
  even connected covers do not establish arbitrary extension.
- Selection uses SciPy/HiGHS mixed-integer optimization, not the reference GCTS
  frontier scheduler. It is a feasibility control for a model to test next.
- This lane is unmarked. No nonconstant m-values, GCTS pruning, or speedup is
  demonstrated. The earlier constant-marking result is not silently replaced.
- Known target coordinates and periodic cells supply candidate registration.
  There is no blind placement or complete continuous-rotation enumeration.
- Fits are geometrically approximate; coverage is exact on source atom IDs.
  One periodic lift per three-atom-ID support is retained, not all image lifts.
- Candidate identity is a template and its decorated target-ID point function.
  Equivalent role maps within a template are deduplicated; different template
  identities remain distinct. No one-placement-per-three-atom-support rule is
  imposed. Several templates may share the same support.
- The denominator family and selection variant were chosen during development.
  All models share one publication source and are not a documented common-T/P
  ensemble. This is not independent-source or pristine held-out validation.
- The geometric templates and atom-site anchors remain those previously
  learned/proposed; general non-atomic anchor discovery is not addressed.

The production growth app is unchanged. Next, test this feasible finite model
with the master point-search engine and learn markings on selected training
covers without using held-out arrangements to set those markings.

## Reproduce

Use the scripts and dependencies from BORON-HOLDOUT-RESULT.md, plus the new
scripts below. Output directories must not already exist. Two workers are used.

```
python boron-alternative-matches.py boron-data/input-audit.json boron-holdout boron-alternatives library-bound
python boron-selected-training.py boron-holdout boron-alternatives boron-selected
python verify-boron-selected.py boron-data/input-audit.json boron-holdout boron-alternatives boron-selected
python test-boron-selected.py
```

Public summaries omit source coordinate geometry. Local artifacts include the
frozen input hashes, candidates, training selections and held-out selections.
