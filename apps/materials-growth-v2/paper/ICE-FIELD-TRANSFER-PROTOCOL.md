# Frozen field-transfer diagnostic

This protocol precedes evaluation. It tests field transfer on the existing
dictionary, not a fresh end-to-end held-out experiment. The base dictionary and
anchors were learned earlier using all 100 original training frames.

Within each existing phase block (Ih, II, VI, VIII), use training frame indices
0–19 for field fitting and 20–24 for calibration. Keep all 25 developmental
frames per phase for evaluation. Phase blocks select a balanced split only;
phase identities are not marking channels or matching inputs. File-level
same-condition and independent-trajectory provenance remain unverified.

Use the frozen 4 Å radial window and 0.4 Å Gaussian width. Retain all observed
paired decorations from the 80 fitting frames, including their alternative
covers. Calibration decorations are excluded even though the existing base
dictionary has seen their geometry. No developmental fields enter the library.

At each selected occurrence, keep its stored base and shared proper rotation.
Construct the two observed common-anchor fields independently of which cover
is selected. For each fitting decoration of that base, compute the larger of
its two endpoint field distances to those common fields. The smallest such
paired distance is a sufficient observed-common-witness radius. It is NOT the
distance between two neighboring tiles divided by two; other common fields
could give a smaller feasible radius.

Calibrate at the configuration level: maximum required occurrence radius over
the 20 calibration covers. If any calibration occurrence has no fitting base,
no finite threshold preserves all calibration covers in this fixed-pose test.
Also report the maximum over represented occurrences as a diagnostic, explicitly
separate from complete calibration. Add 1e-8 in field-norm units as an engineering
guard, not a certified error bound or statistical confidence guarantee.

Freeze that threshold before evaluating all 100 developmental covers. Report
whole-cover acceptance, occurrence acceptance, missing-base abstentions, and
per-frame witness IDs/distances. Do not call missing matches forbidden or infer
search impossibility from this fixed-pose positive precheck. A passing cover
has one source-derived common field at every shared anchor, so acceptance is
jointly witnessed, not merely a collection of unrelated pairwise matches.

No challenge negatives are used to tune this threshold. Connection selectivity
must be tested separately before installing a production restriction. The
current study does not claim reconstruction, generation, physics, or superiority.
