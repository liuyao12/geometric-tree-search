# Progress report: weighted filling before growth

14 September 2026. Preliminary computational result; not peer reviewed.

The revised target is to infer reusable weighted tiles. Their t-values add to
one at shared points; their m-values agree on overlaps. Filling deficits, not
an obligation to place a neighborhood centered at every atom, drive growth.
The older 34-atom example below this update concerns that previous model.

## Verified transfer, not generation

Two 216-atom development configurations supply a restricted pair-cover control.
A shared pair weight of 1/3 is solved from its incidence equations. Partitioning
the selected pairs into two-edge paths and grouping their geometry within 0.1 Å
gives 16 three-site motif types, with inherited weights (1/3,2/3,1/3).
These are derived weights, not independently learned unconstrained site values.
The regular-pair proposal family is a disclosed restriction, not a chemical
coordination model or general cluster-discovery algorithm.

Without changing this library, frames 2,100,400 admit covers of all 216 atoms,
each using 162 motifs and 324 distinct constituent pairs. Positive overlaps are
connected. The selected type counts are 10,10,14; maximum rigid-pose residuals
are 0.099154,0.099513,0.099404 Å. Integer units of one third verify filling exactly;
the geometry is approximate. Periodic cells are supplied by the source.

These are same-source configurations, not independent specimens. The candidate
generator uses their known coordinates. No atom-count increase, blind growth,
medium-range structural fidelity or advantage over materials generators has
been demonstrated. A bounded constructive cover procedure finds these witnesses
after 3,4,28 proposals; three 15-second MILP attempts return Unknown. This is not
a benchmark of marked versus unmarked GCTS.

## A useful negative result before search

At the three atomic sites, the 48 scalar type/site marking variables are linked
into a single equality component by training overlaps. Therefore all exact
scalar markings with trivial rotation action must be constant. More copies of
those scalar channels cannot add discrimination. This is a statement about this
library and marking domain, not all GCTS representations.

A numerical pilot with ordinary rotation-covariant 3-vectors likewise has full
column rank (144) across both frames; smallest singular value 0.950517. At unit
RMS site-vector magnitude, minimum RMS reference-pair discrepancy is 0.283389.
This is floating-point evidence, not an exact impossibility certificate. Refitted
poses, alternative domains and other representations were not exhausted.

## Reproduce the strongest claims

Download `weighted-reset-evidence.json` and `verify-weighted-reset.mjs` from this
directory, then run:

```
node verify-weighted-reset.mjs weighted-reset-evidence.json
```

The standalone verifier checks five supplied covers, fixed one-third filling,
single use of constituent pairs, connected positive overlap, proper stored
rotations and <=0.1 Å residuals. For transfer configurations it additionally
checks periodic agreement with supplied atom coordinates. It reconstructs the
training scalar equality graph and verifies that it has one component. It does
not reproduce discovery, certify all continuous placements or verify the vector
singular-value study. Source artifact hashes are retained in the bundle.

The silicon source is the published CC BY 4.0 dataset credited in the paper's
connection-transfer section (Rosset, Drabold and Deringer). Only geometric input
is used here; no energies, forces, bonding rules or formation-history labels
enter these algorithms. Original dataset SHA256:
`da49808517c35d7b77bfe8eaa0e446dc97c908cc6652b1fad82b88f10d8ce1d2`.

Next: identify recurrent, transferable marking context while retaining verified
weighted filling, then test genuinely blind extension against structural and
algorithmic baselines. Passing the observed t/m equations is the admission gate,
not the final scientific result.
