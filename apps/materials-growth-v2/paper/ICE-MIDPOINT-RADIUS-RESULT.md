# Common marking witnesses need not equal the source-neighborhood field

The previous field precheck asked each learned endpoint field to lie within
radius r of a source-derived neighborhood field. This is a sufficient common
value, not a necessary one. In the current two-contribution model each anchor
has exactly two incident fields. Their Hilbert balls intersect when their
center distance is at most 2r; their midpoint is an explicit common value.
This midpoint is a formal marking, not necessarily a realizable atom cloud.

We froze all 97 verified complete developmental covers from the maximum-error
registration study: geometry, selected decorations, component identities and
half-weight t-values. No new sample or decoration was learned. An independently
replayed grid gives:

| Field radius | Covers with source-field witness | Covers with midpoint witness |
| --- | ---: | ---: |
| 0.2 | 0 | 0 |
| 0.3 | 0 | 9 |
| 0.4 | 0 | 51 |
| 0.5 | 2 | 78 |
| 0.6 | 27 | 97 |
| 0.8 | 54 | 97 |
| 1.1063594889735058 | 97 | 97 |

The independent audit reconstructs all incidence identities and evaluates
8,880 signed Gaussian quadratic forms in world coordinates. Maximum distance
disagreement is 1.12e-14. These guarded floating-point checks are not exact
interval certificates. The three geometric failures remain failures.

## Does the tighter radius remove alternatives?

An exploratory follow-up selects radius 0.6 after inspecting this developmental
grid. It is therefore explicitly not a calibrated threshold or held-out test.
For each retained cover, substitute every fitting decoration of the same base
at each fixed pose, keeping all other decorations unchanged. At both endpoints,
compare to the other incident field. Include identity substitutions.

Across 97 covers, 1,599,419 substitutions are tested. Independent replay confirms 3,083
incompatible substitutions (0.193%), no boundary-uncertain comparisons, and
retention of all 8,880 original placements. The producer loop takes 44.83 seconds;
this excludes learning, preprocessing and the independent audit and is not a
search-performance comparison. The separate audit evaluates world-coordinate
cross kernels with long-double summation, re-enumerates all substitution
identities and checks every accepted/rejected classification and all identities.
It does not independently certify the producer's stored distances or maxima.

The effect is nonzero but small. It does not establish useful GCTS acceleration.
These are incompatible substitutions in fixed witness contexts, not globally
invalid motifs or known physically impossible connections. Changing multiple
decorations simultaneously can change compatibility. No false-positive rate
against independently labeled geometric negatives is measured here.

The next substantive step is more selective connection learning, with positive
cover constraints during training and whole-configuration tests on fresh data.
General learned anchors/t-values, full tree-search reconstruction, growth beyond
the input and file-linked common-condition provenance remain unresolved.

## Reproduction artifacts

- `ICE-PAIR-RADIUS-PROTOCOL.md`: frozen diagnostic grid and semantics.
- `ice-pair-radius.py`, `verify-ice-pair-radius.py`: producer and independent audit.
- `ice-pair-radius.json`, `ice-pair-radius-check.json`: all pairs and witness checks.
- `ice-midpoint-replacements.py`, `verify-ice-midpoint-replacements.py`: all-substitution control and audit.
- `ice-midpoint-replacements.json`, `ice-midpoint-replacements-check.json`: substitution classifications and independent checks when complete.

Inputs are the same hash-bound library, transfer, repaired-pose and prior-check
artifacts as the registration study. No raw coordinate corpus is republished.
