# First periodic-field transfer run — positive witnesses independently replayed

The frozen protocol is `ICE-FIELD-TRANSFER-PROTOCOL.md`. The runner is
`ice-field-transfer.py`; local output is `/tmp/gcts-ice-field-transfer-v1.json`.
It finished in 42.62 seconds (evaluation loop only; excludes input/preparation).

Eighty field-fitting configurations contribute 8,074 paired decorations.
Twenty other original training frames calibrate the diagnostic tolerance;
100 developmental frames are then evaluated. The previously learned geometry
dictionary has seen calibration geometry, so this is not a fresh end-to-end
split. Preparation conditions and trajectory independence are still unverified.

The calibration gate **does not pass**: 17 occurrences in eight calibration
covers lack a decoration for their assigned base among the fitting frames.
No finite marking radius can fix this fixed-base absence. Only 12/20
calibration covers are fully represented. The declared diagnostic fallback,
maximum distance over represented calibration occurrences plus 1e-8, gives
1.1063594889735058 in field-norm units. This is not a complete-calibration
threshold or a recommended production setting.

With that frozen diagnostic threshold, producer-side evaluation reports:

| Developmental phase | Complete supplied covers / 25 |
| --- | ---: |
| Ih | 23 |
| II | 9 |
| VI | 13 |
| VIII | 22 |
| Total | 67 / 100 |

Of 9,200 selected occurrences, 9,159 admit a fitting paired decoration under
their stored base pose and the observed common fields. Forty lack a fitting
decoration for their assigned base; one represented occurrence exceeds the
diagnostic threshold. Thus most remaining failures in this particular precheck
are fitting-library/base-assignment gaps, not field-radius failures.

This is not evidence of specificity, successful tree search, or superiority
over the raw-cloud controls. The model, radius units and fitting split differ.
A broad tolerance may preserve positives while allowing many unsuitable joins.
The nearest observed common-field witness is sufficient, not a necessary
radius over all possible common fields and poses. Missing base matches are
not proofs of geometric impossibility; alternative fitting bases/poses may work.

Next gates:

1. Independently rebuild query fields and replay the stored fitting-motif
   witnesses, including the calibration threshold, t totals and shared fields.
2. Test specificity with explicitly scoped geometric alternatives; do not call
   challenge constructions physically impossible.
3. Test all compatible fitting base assignments before adding target examples.
4. Only then use the rule in a restricted reference-scheduled search and compare
   verified reconstruction, costs and failures. The production engine is unchanged.

Independent replay subsequently checked all 120 calibration/developmental
frames, rebuilding fields without producer imports. It verified 21,966 endpoint
distances using a signed quadratic form in world coordinates; maximum squared
distance discrepancy is 6.3283e-15. Fitting-split membership, missing assigned
bases, source-derived common fields, integer filling totals and the frozen
diagnostic threshold were checked. The 67 complete developmental cover witnesses
pass. This does not independently prove nearest-neighbor optimality or absence
of an alternative witness for the single over-threshold occurrence.

Four corruption controls (altered distance, removed occurrence, altered split,
and altered radius) are required to be rejected by the verifier. The checker is
`verify-ice-field-transfer.py`, its controls are
`test-ice-field-transfer-verifier.py`, and the result is
`/tmp/gcts-ice-field-transfer-check-v1.json`.
