# Dynamic latent-point filling: preliminary reconstruction evidence

20 September 2026. Not peer reviewed; not blind growth or an acceleration claim.

## Result and scope

The unchanged reference kernel reconstructs 6 of 44 beta and 0 of 44 alpha
oxalic-acid evaluation frames. Source atom positions, motif partitions, poses
and periodic cells remain inputs. The generated latent point domain is no
longer obtained from a selected successful cover. Every active positive
support is verified, including latent sites activated by search.

The source-order split uses 120 fitting and 44 evaluation frames per phase.
One beta fitting frame has an incomplete recurring motif partition and is
excluded. Frame-level temperature/pressure and independent trajectory
provenance are unverified. Do not interpret 6/88 as independent-trial statistics.

## Evidence files

- [results.json](results.json): all 88 outcomes, recorded occupancy stages and
  search counters. No atom coordinates are included in this display export.
- [check.json](check.json): independent finite-pool re-enumeration, all active
  rational t-sums, geometric/marking-ball checks and periodic connectivity.
- [weight-check.json](weight-check.json): 4,774 training equations and exact
  minimum-norm stationarity checks. There are 4,612 free parameters before
  regularization; the weights are not uniquely identified by observations.
- [RESEARCH-LOG.md](RESEARCH-LOG.md): intermediate diagnostics, failed controls,
  model changes, hashes and limits. Earlier pair tests are not the same lane.

## Method

1. Assemble complete training contexts without discarding rare ports.
2. Infer shared-point partitions from common positional and vector-marking
   balls using an explicit minimum-point-count prior. Fit context-local t
   by minimum norm subject to training sums equal to one. The resulting
   fractions are 1/2, 1/3 and 2/3. Atomic t=1 is a separate occupancy prior.
3. For every evaluation frame, propose all weight-compatible pair/triple
   contacts from frozen contexts at original fitted poses. No selected cover
   or evaluation latent-site coordinates are used. Only the training-fitted
   weights field is used from the weight artifact.
4. Remove incompatible context/contact alternatives by necessary consistency
   propagation under one context per supplied motif occurrence. This is
   learned-marking preprocessing, not an unmarked candidate baseline.
5. Compile all surviving contact representatives into a finite numerical point
   domain (fractional coordinates rounded to 12 decimals). Enumerate every
   compatible port alignment. Atom roots are initially required; latent sites
   become active only when selected positive support touches them.
6. Run `PointSearch` without modifying its scheduler. Capacity six represents
   rational occupancy exactly. Native interval markings enclose vector balls;
   replay verifies actual common Euclidean balls after search.

The six nonempty pools have 2, 2, 4, 416, 2 and 2 candidates. Each successful
run selects two motifs. Total genuine branches: three; backtracks: zero.
These tiny, preprocessed finite problems do not demonstrate GCTS speedup.
Exhaustion means only failure of this declared fixed-pose domain.

## Reproduction

Python dependencies are NumPy, SciPy and ASE; the engine runner uses Node.js.
The earlier [periodic-interface protocol](../nested-motif-transfer/PERIODIC-LEARNING.md)
and [nested-motif protocol](../nested-motif-transfer/README.md) describe source
acquisition and the base library. The full local model/cloud artifacts are not
bundled with this web report; recreate them through the published learning
pipeline. The research log records the intermediate file identities. Numerical
pose optimizations are bounded and should not be expected to be bitwise
identical across numerical-library versions.

With coordinates, metadata, motifs, interfaces and the training-fitted weight
artifact available, run the following (arguments are file paths):

```
python propose-unseeded-anchor-contacts.py COORD META MOTIFS INTERFACES CONTEXTS WEIGHTS CONTACTS
python compile-dynamic-context-filling.py CONTACTS COORD MOTIFS POOL
node run-context-filling.mjs POOL ../../kernel.mjs SEARCH marked-only
python verify-dynamic-context-filling.py COORD MOTIFS INTERFACES CONTEXTS WEIGHTS CONTACTS POOL SEARCH CHECK
```

`search-unseeded-contacts.py` is a separate diagnostic; its selected covers
are **not an input** to the reference-kernel compilation above.

Controls:

```
python test-anchor-neighborhoods.py
python test-context-point-weights.py
python test-unseeded-contacts.py
python test-unseeded-contact-search.py
node test-dynamic-context-kernel.mjs ../../kernel.mjs
node ../../test-kernel.mjs
```

The reference kernel hash used in these receipts is
`747db2cb5e626968d4bbf18fc1cb804b4a66ad2f177f3d5b097bc4b53257ba85`.
Checks cover the finite declared domain, not all continuous rotations and
translations. No claim of a Nature-level result, matched-condition transfer,
physical growth kinetics or formation-history inference is made.
