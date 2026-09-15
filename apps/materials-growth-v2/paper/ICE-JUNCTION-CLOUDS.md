# Ice family: shared motifs need richer connection data

This is a developmental geometry-registration experiment, not a new growth or
independent generalization result. The existing pilot contains 100 author-training
and 100 author-validation configurations of Ih, II, VI and VIII. These validation
frames have already been used developmentally. File-level condition and trajectory
provenance gaps described in `ICE-COHORT-GATE.md` remain unresolved.

## What is learned

The existing geometric component partition and selected connected pair-union
covers are inputs. Each component has two incident selected pair unions, an
explicit property of this earlier uniform-half decomposition—not a chemical
valence rule. Atom coverage is rechecked in integer units: each atom occurs
twice, with t=1/2. This experiment does not refit t.

A junction consists of a root component and the two neighboring components in
that selected cover. Its vectors are centered at the root component centroid.
The learner receives coordinates, opaque species labels, component membership,
and selected incidences. No phase, temperature, pressure, energy, force or
formation-history value enters registration. The data happen to yield nine-site
clouds, but no H2O formula is encoded.

Templates are added greedily only from training configurations. Root-preserving
component permutations and within-component species-preserving permutations are
tested with proper rotations. Maximum atom residual is at most 0.15 Å. Translation
is fixed by the root centroid. No reflection or additional free translation is
allowed. Each accepted fit has a saved bijection and rotation. This uses
least-squares pose proposals followed by maximum-error verification; a failed
proposal is not a proof of geometric non-congruence. These are representative
templates under an approximate, order-dependent procedure, not canonical exact
isometry classes.

## Junction-library learning curve

The same 9,200 junctions in 100 developmental covers are queried at each setting.
The selected training frames are the first 1, 5, 10 or 25 per source phase.
Metadata perform cohort selection outside the learner. Upstream components, pair
dictionary and selected covers remain fixed from the existing 100-training-frame
pilot: this is **not** an end-to-end four-versus-one-hundred-sample comparison.

| Training configurations for junction library | Templates | Development junctions matched | Fully represented developmental covers |
| --- | ---: | ---: | ---: |
| 4 | 329 | 1,408 / 9,200 (15.3%) | 0 / 100 |
| 20 | 1,356 | 3,655 / 9,200 (39.7%) | 0 / 100 |
| 40 | 2,308 | 4,841 / 9,200 (52.6%) | 0 / 100 |
| 100 | 4,423 | 6,356 / 9,200 (69.1%) | 0 / 100 |

The largest library has 2,647 templates observed only once in training. All
9,200 training junctions are represented by construction; independent replay
checks their transformations. At the largest setting, developmental coverage is
2,143/3,200 for Ih, 1,525/2,400 for II, 1,528/2,000 for VI and 1,160/1,600 for VIII.
These correlated observations do not support independent-sample confidence
intervals or a physical sample-complexity law.

All 269 pair-motif types observed in selected training covers are incident to
multiple learned junction templates. This motivates testing context-dependent
markings. It does not prove that every template requires an inequivalent m-value;
opposite endpoints, approximate registration and thermal variation also matter.

## Interpretation and next gate

More training records substantially improve *witnessed local registration
coverage* at the fixed tolerance, but the current dictionary does not represent
any complete selected developmental cover. It must not be installed as a hard
exclusion rule and presented as preserving those covers. Alternative covers might
still be admitted; they have not been enumerated in this experiment. Unmatched
queries can reflect insufficient data, restrictive decomposition choices or an
incomplete pose proposer—not necessarily a forbidden connection.

These rooted clouds can supply candidate marking values at component-centroid
anchors, with rotations acting on their vectors. They are not yet a portable
two-ended decorated pair library. The next required step is to learn joint
endpoint contexts under a common tile pose, verify common-value agreement on
supplied fillings, then evaluate the frozen markings through the reference
frontier graph. Simply assigning a target-local junction ID is not that step.

No new tree-search implementation is introduced here. The reference scheduler,
global dead/forced checks, complete finite candidate incidence and rollback
requirements remain unchanged. No claim of continuous-pose completeness,
negative-connection correctness, connected growth, or speedup follows.

## Verification and reproduction

`test-ice-junction-clouds.py` checks 100 random proper-rotation, permutation and
noise cases, reflection and fixed-origin negatives, and 60 wrapped triclinic
junctions. `verify-ice-junction-clouds.py` uses an independent atom-to-anchor
minimum-image reconstruction, not the learner's spanning-tree lift or fitting
routine. It rechecks all 15,556 accepted fits in the largest experiment, proper
rotations, component/species bijections, training-only template witnesses,
integer cover sums and connected supplied support. The maximum residual is
0.1499994306 Å. Every learning-curve point receives the same independent checks.

```
python test-ice-junction-clouds.py
python ice-junction-clouds.py COORDINATES COVER DICTIONARY SELECTION 0.15 LEARNED
python verify-ice-junction-clouds.py COORDINATES COVER DICTIONARY SELECTION LEARNED PROVENANCE CHECK
python ice-junction-learning-curve.py PILOT_FOLDER NEW_OUTPUT_FOLDER
```

The full run uses `overlap-broad.json`, `thermal-dictionary-e015.json` and
`thermal-selection-k2.json` from the existing pilot. The library and subsets
contain source-derived coordinates and are not republished here. Public checks,
source hashes and code are audit evidence, not a self-contained reproduction
bundle. Python requires NumPy, SciPy and ASE. The learner also imports
`ice-motif-dictionary.py`.
