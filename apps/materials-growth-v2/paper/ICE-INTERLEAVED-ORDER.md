# Interleaving motifs and endpoint alternatives: a failed ordering control

The previous six-frame test established that each finite factorized ice model
admits a connected full filling, while two reference-scheduled ordering policies
timed out. This follow-up changes candidate order only. It does not relearn
markings, restrict the model, merge equivalent candidates or use oracle answers.

Within each incident geometric block, enumerate endpoint-index pairs along
diagonals of their Cartesian product. Interleave one candidate from each block
in round-robin order. Snapshot parent incidence and endpoint lists before
yielding; resume only after exact parent rollback. Every original candidate
remains distinct and appears exactly once. The full decorated degrees, global
dead/forced checks and earliest-generation scheduler are unchanged.

This addresses one possible source of wasted work: exhausting many decorations
of the same motif with the same first endpoint before trying a different motif
or first endpoint. It is a deterministic heuristic, not learned information or
a proof that its preferred candidates are better.

## Conformance checks

- All 81 rectangular products with side lengths zero through eight are exhausted
  without missing or duplicated pairs.
- 100 tiny models: 6,169 states, 123,380 explicit membership comparisons,
  1,170 state rollbacks and 273 suspended-iterator rollback checks.
- All 409 valid full solutions among 312,500 selections remain replayable;
  complete/exhausted search outcomes agree with independent enumeration.
- Cloud controls retain permutation tolerance, reject a false signature match,
  preserve the two-sided numerical guard and never turn unknown common-value
  verification into an impossibility claim.

## Same six frozen material models

The phase-expansion source, filtered blocks and verified complement indices
are reused unchanged. All six frames and the thirty-second per-frame search
budget were fixed before this follow-up. The library, candidate pool, geometric
tolerance and t/m data are unchanged. No training selection or oracle witness
is read by the ordering policy. These are already-examined developmental data,
not fresh independent holdouts.

| Phase / split | Baseline final placements (earlier) | Interleaved final placements | Interleaved result |
| --- | ---: | ---: | --- |
| Ih / training | 91 | 91 | budget-unknown |
| Ih / developmental | 36 | 47 | budget-unknown |
| II / training | 90 | 73 | budget-unknown |
| II / developmental | 72 | 60 | budget-unknown |
| VI / training | 35 | 35 | budget-unknown |
| VI / developmental | 53 | 65 | budget-unknown |

Independent replay checks every final t total, shared inventory and all 742
cloud assignments. All six root rollbacks pass. Across the runs there are
26,964 backtracks and two degree-one forced placements. Final placement counts
are neither maxima nor success probabilities. Their changes do not establish
an improvement; both earlier orderings and this follow-up have zero complete
fillings on these six frames at this budget.

Setup is 0.13–0.49 seconds per frame; search is about 30 seconds. These figures
exclude learning, registration, preprocessing, file I/O and final verification.
Historical baseline timing is not a paired statistical speed comparison.

## Consequence

This particular diversification policy did not resolve reconstruction. It should
remain an optional research control, not replace the default or be described as
a GCTS advance. A more informative next experiment should study reusable
multi-motif constraints or justified failure reuse rather than select a favorable
partial-placement count. Any learned restriction must preserve supplied
fillings and be tested on fresh whole configurations. Continuous-pose growth,
verified same-condition provenance and general learning of anchors/t-values
remain open.

```
node test-dynamic-factorized-support.mjs --indexed --interleaved
node test-dynamic-factorized-cloud.mjs --interleaved
python ice-interleaved-pilot.py PHASE_EXPANSION NEW_OUTPUT --node NODE
```

The report binds results to the unchanged model hashes, ordering source and
independent final-state checks. The public 3D figure continues to show its
explicitly named original baseline/ranked/feasibility lanes; these new partial
states are not silently substituted into it.
