# A decomposition challenge weakens the binary marking result

14 September 2026. Training-only sensitivity analysis, followed by developmental
validation. This extends rather than replaces ICE-BINARY-VARIANTS.md.

## Why this test matters

The earlier binary marking experiment admitted 238 selected training covers.
Those witnesses were connected degree-two graphs with even cycle length. Giving
every motif opposite binary marks on its two geometric ports therefore satisfied
the selected examples almost by construction. The gain from 27 to 85 connected
search results could reflect this chosen decomposition, not a material-specific
connection rule.

We now select three alternative degree-two covers for each of the same 100
training configurations. The candidate library, admitted 347 motif types,
geometrically registered occurrences and half-weights remain frozen. A MILP
uses random linear costs (seeds 0, 1 and 2) and a two-second budget, with no
connectivity cut or marking/parity preference. These are not uniform random
samples of all covers, new independent configurations or reference-tree-search
runs. Seeds can return repeated covers; 300 denotes attempts, not necessarily
distinct decompositions.

All 300 attempts yield independently checked exact point covers; 51 are
connected. The old all-contrasting marking cannot lift 152 of the 300 covers.
All these rejected covers are disconnected: the connected degree-two covers
still have even length. This is evidence of decomposition sensitivity, not
proof that a marking must accept every disconnected decomposition of an input.

## Refit within the same restricted hypothesis class

For each motif type, learn whether its two port marks agree or differ. Both
global binary flips remain allowed. Each individual cycle contributes a parity
equation. Combine these new equations with the original training constraints;
do not use validation data to fit the contrasts. Maximize contrasting types as
before, now subject to the augmented training set.

The 347 binary variables have exact rank 344 and nullity three. Pointwise
verification proves 340 type contrasts must be zero; only seven types can
contrast. Enumeration of all eight remaining assignments independently proves
that seven is the exact maximum, rather than trusting the optimizer status.
Thus the earlier 347-type contrast largely disappears when the description is
required to accept this wider set of decompositions.

On the 300 previously selected, connected developmental validation covers,
the refitted marking admits 295 and rejects five. The old marking admitted
all 300. Rejecting one chosen cover does not prove that the corresponding
configuration has no other compatible cover. No validation witness was added
to the refit. The chosen maximum-contrast solution is not a probabilistic model
or a statistically established rule.

## Search after refitting

Run the same relative-mark quotient with the refitted contrasts on all 300
developmental validation configurations, without supplying selected answers.
Under the same 10,000-advance / one-second per-case limits, it finds 284 exact
finite covers, of which 25 are connected; 16 cases remain budget-unknown.
By phase, completed/connected counts are Ih 60/18, II 75/4, VI 75/3 and VIII
74/0 (75 attempts each). An independent verifier checks every final point sum,
binary lift, physical placement identity and connectivity.

For context, the previous all-contrasting quotient returned 289 complete and
85 connected covers, and the unmarked reference returned 289 complete and 27
connected covers. The earlier connected-cover gain does not survive this
refit. This is not a controlled timing comparison: the rules change the
admitted problem, wall-time limits can affect completion counts, and the
quotient incurs full-refresh overhead. Budget failures do not establish that
the refitted model cannot reconstruct those configurations. Search still uses
known target positions and generation-zero roots, not coordinate-blind growth.

## Independent checks

The verifier reconstructs binary relative equations from the actual atom-site
incidences and transported template ports, not the stored cycle summaries.
It checks exact half-weight sums, physical placement uniqueness, complete
configuration/seed coverage, training-only IDs and source hashes. Dense boolean
row reduction independently checks the generator's integer-bitset rank and
forced-zero coordinates. Exhaustive controls cover 160 small systems and
10,200 assignments, plus four odd/even-cycle controls and eight rejections of
duplicated or incomplete covers. No production search engine is changed.

## Consequence for the research programme

Positive coordinates do not specify a unique decomposition into motifs or a
unique marking. Requiring agreement with one arbitrarily selected cover can
give misleadingly strong constraints; accepting more covers can erase them.
Neither accepting every geometric cover nor privileging Hamiltonian cycles is
an established solution. We need justified joint occurrence/marking learning,
richer motifs with branching interfaces, and tests of configuration-level
reconstructibility. Merely maximizing binary contrast is not enough.

This is a useful negative diagnostic, not a general impossibility result for
GCTS, a physical claim about ice, or a publication-level materials advance.
Condition/trajectory provenance and coordinate-blind growth remain open.

## Reproduce

```
python ice-binary-cover-challenge.py PILOT_DICTIONARY PILOT_COVER ORIGINAL_MARKING CHALLENGE
python verify-ice-binary-cover-challenge.py PILOT_DICTIONARY ORIGINAL_MARKING CHALLENGE VALIDATION_DICTIONARY VALIDATION_SELECTION CHECK REFIT_MARKING
python test-ice-binary-cover-challenge.py
node ice-binary-reference.mjs VALIDATION_DICTIONARY REFIT_MARKING KERNEL REFIT_SEARCH quotient
python verify-ice-binary-reference.py VALIDATION_DICTIONARY REFIT_MARKING REFIT_SEARCH VALIDATION_PROVENANCE SEARCH_CHECK
```

Outputs must be new paths. Training generation requires NumPy, SciPy and
NetworkX; the independent challenge verifier uses NumPy but no optimizer.
Source coordinate dictionaries remain local because redistribution permission
has not been established. The public checks contain aggregates and hashes.
