# Round 1b — prospective envelope and exclusion baseline

Motivation, after round 1: nearest-example scores failed every promotion gate.
Test a different representation before attempting hard-constrained growth.
This is a second exploratory round, not confirmation of round 1.

Use untouched frames 96–167 of the same coordinate file, shuffled by the same
uint32 LCG Fisher–Yates algorithm with seed 2718; split 48/12/12 configurations.
No preparation metadata enters selection, training, calibration or scoring.
Keep the six-point hinge extractor and three twist angles unchanged.

Fit two geometric hypotheses on the 48 training configurations:
1. **Exclusion baseline**: lower bound on the minimum pair distance in each
   six-point support. This is a simple learned geometric spacing constraint,
   NOT a GCTS-specific advance and NOT a chemistry-derived atomic radius.
2. **Connection envelope**: coordinate-wise min/max ranges of the sorted,
   role-and-label-stratified joint-distance descriptor. Score the largest
   excursion outside these training ranges in Å. This is a permissive box,
   not a complete isometry classifier or a learned physical potential.

For each score use the maximum calibration-positive score as its cutoff.
Unknown strata abstain. Do not tune cutoffs on test data. Evaluate the envelope,
baseline, and their conjunction. Report configuration survival, local retention,
and conditional twist rejection, plus incremental rejection beyond the baseline
on connections whose original is retained by BOTH methods.

Use the same exploratory gate (11/12 configurations, 10% conditional twist
rejection, no unknowns). Passing the gate is NOT a scientific advantage:
if the spacing baseline explains the rejection, report that explicitly.
Test configurations are independent split units, not independent equilibrium
replicates; all conclusions remain restricted to this dataset and diagnostic.
