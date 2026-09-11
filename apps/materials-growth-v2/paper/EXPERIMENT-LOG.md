# Geometry-only experiment log

## Round 1 — local safety exposes a failure

Protocol and implementation were committed before executing the new held-out
evaluation. See EXPERIMENT-PROTOCOL.md and configuration-safety.mjs.
Frames 24–95: 48 training, 12 calibration, 12 test configurations; nested
training counts 4, 12, 48. All 18 settings failed the prospective exploratory gate.

With 48 training configurations, the joint-distance 99th-percentile cutoff
retains 99.51% of test connections but only 6/12 complete diagnostic connection
sets. Its conditional twist rejection is 0.70%. Maximum-calibration cutoffs
preserve 12/12 configurations but reject only 0–0.11% of eligible twists across
the three scores. Larger training libraries alone did not solve this trade-off.

This is not evidence that GCTS itself cannot work. It falsifies the adequacy of
these particular nearest-example scores for the declared transfer-and-selectivity
gate. Diagnostic preservation is weaker than complete structural coverage.

## Round 1b — changing representation does not beat the baseline

After observing round 1, a second protocol and runner were committed before
evaluating untouched frames 96–167. See ENVELOPE-PROTOCOL.md and envelope-study.mjs.
The 48/12/12 split uses a different fixed seed. Coordinate-wise joint-distance
envelopes preserve all 12 test configurations but reject 9/5,487 eligible twists
(0.164%). The learned minimum-distance baseline rejects 14/5,487 (0.255%),
including all nine envelope rejections. The envelope contributes zero additional
rejections; their conjunction also fails the gate. There are no unknown strata.

The exclusion cutoff is calibrated on positives by exactly the frozen maximum
score policy; it can be stricter than the training minimum when calibration
minimum distances are larger. It is not asserted to retain every training item.

## Interpretation and next iteration

Neither round supports a materials-generation advantage. Twists are geometric
perturbations, not physically invalid negative examples. This benchmark cannot
prove that rejecting more twists is intrinsically desirable. Small periodic cells
and only twelve held-out configurations do not support broad transfer claims.

Next: test closure of connected multi-motif neighborhoods on independently held-out
larger configurations. The mechanism to test is whether locally admissible relative
poses fail when composed around a loop, and whether reusable neighborhood markings
detect those failures before the base geometric consistency check would do so.
Include consistent loops under global rotations, contradictory loops with known
geometric certificates, and unknown sampled continuous domains as separate cases.

The comparator must already enforce shared-point agreement and overlap consistency.
Otherwise markings merely repair an artificially weakened baseline. Compare the
same finite candidate universe and accepted configurations first; learn broader
restrictions only after measuring preservation of held-out configurations.
Count compilation, training, graph maintenance, search, verification, and memory.

Only after the loop study should we attempt blind cavity completion. Its candidate
generator must never see hidden reference atoms. Report geometric structural
statistics and output diversity; keep external physical evaluation separate from
the physics- and formation-history-agnostic learner.

## Reproduce

Download the CC BY 4.0 coordinate file linked in configuration-safety-results.json.
From this directory, with Node.js:

```sh
node configuration-safety.mjs /path/to/216-atoms.xyz configuration-safety-results.json
node envelope-study.mjs /path/to/216-atoms.xyz envelope-results.json
node test-configuration-safety.mjs
```

Both result files include exact splits, raw calibration/test scores and runner
hashes. Round 1 additionally records descriptive execution time, not a speedup.
The protocols, result files, and this negative record remain public. No production
growth rule was changed or promoted from these unsuccessful experiments.
