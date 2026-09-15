# Field replacement control: no observed local pruning

On all 67 independently accepted developmental coverings, replace each selected
decoration by every fitting decoration of the same base, retaining geometry,
pose, occupancy and all other decorations. This is a test of decoration
constraints in already witnessed contexts, not a physical-negative benchmark.
Each shared anchor has exactly one retained neighboring tile. With radius r
field balls, a replacement is incompatible there only when the two field centers
are farther apart than 2r (with numerical ambiguity left unresolved).

The frozen diagnostic radius remains 1.1063594889735058; the pair-separation
threshold is 2.2127189779470116. The completed producer-side control reports:

- 67 configurations and 6,256 selected placements;
- 1,367,236 replacements including 6,256 identities;
- **zero rejected and zero numerically unresolved replacements**;
- every original witnessed decoration retained;
- maximum endpoint distance 1.4041444402339631, below the threshold;
- 1,446 scalar reference checks, with maximum squared-distance disagreement
  1.7764e-15 against the vectorized calculation.

This directly limits the interpretation of positive transfer. Within these
known-pose witness neighborhoods, the broad diagnostic marking radius provides
no decoration pruning. It is not a useful demonstrated GCTS acceleration. The
result does not show that arbitrary geometry or arbitrary simultaneous changes
are admitted: the test fixes other decorations and supplied motif poses, and
every alternate decoration belongs to the same base. Unobserved alternatives
are not automatically wrong connections.

No field radius was retuned on this outcome. Independent exhaustive replay of
all replacements is pending; sampled numerical cross-checks are not that replay.
The next gate should examine whether a better calibrated representation or
base-conditioned uncertainty yields useful exclusions while preserving whole
configurations, rather than installing this broad threshold in production.
Any conditioned radii must be learned without phase IDs or evaluation leakage,
and shared-anchor feasibility must use the sum of the two declared radii.

Runner: `ice-field-replacement-control.py`.
Local result: `/tmp/gcts-ice-field-replacement-control-v1.json`.
The source/check hashes and per-configuration maximum-distance witnesses are
recorded in that report. No production search or web files changed in this turn.

## Independent audit follow-up

`verify-ice-field-replacements.py` independently reconstructs incidence and
world-coordinate endpoint fields without importing producer helpers. It confirms
all 1,367,236 replacements are compatible after 2,734,472 explicit endpoint
kernel checks. The arithmetic uses guarded floating-point bounds, not certified
intervals. It does not certify the producer's exact maximum-distance statistic.

The independent norm calculation in `ice-field-norm-bound.py` first tests the
inequality `||a - Rb||² <= ||a||² + ||b||²`, valid because the Gaussian kernel
and all amplitudes are nonnegative. That orientation-free bound is inconclusive:
its universal upper squared distance is 6.58544, above the 4.89613 threshold.
It also resolves none of the tested endpoints individually. Explicit kernel
evaluation, rather than this coarse magnitude bound, establishes compatibility.

Reports: [independent audit](ice-field-replacement-check.json),
[norm dependency](ice-field-norm-bound.json),
[replacement results](ice-field-replacement-control.json).
The failed first norm export was a NumPy-boolean serialization error; the v2
report was generated successfully after fixing serialization, with unchanged
mathematics. No partial v1 norm report is used or published.

This result blocks promotion of this diagnostic tolerance as demonstrated
useful pruning. It does not block research on different learned representations,
base-conditioned uncertainty, alternative geometric motif assignments, or
continuous-space GCTS generally. No search schedule or physical rule was added.
