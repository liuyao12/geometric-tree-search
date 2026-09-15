# Periodic Gaussian marking representation control

This is an unfinished research control, not a replacement for the material
growth engine and not evidence of successful family reconstruction.

## Change and motivation

Earlier raw-cloud marking agreement required equal point cardinalities. Earlier
ambient clouds were independent of the selected cover but still depended on a
hard component-neighbor graph and one minimum image per neighbor. Neither gives
smooth behavior as geometric neighbors enter or leave a fixed window.

`gaussian-section-markings.py` now extracts every periodic image inside a stated
radius R. Each point contributes a Gaussian kernel section of width sigma with
amplitude `max(0, 1 - |v|²/R²)³`, separately for opaque labels. The whole field
rotates with the motif. It is not a physical potential, rotationally averaged
descriptor, or new atomic configuration. No stoichiometry enters extraction.
Gaussian representations and kernel metrics are established methods; their use
here is a proposed representation for covariant GCTS marking agreement.

For a row-vector cell C, an image within R satisfies
`|(v C⁻¹)_k| <= R ||C⁻¹[:,k]||`. Wrapped fractional coordinates and these bounds
give a finite image enumeration, including skewed cells. The implementation
rejects excessive enumeration and ill-conditioned cells, rather than silently
cropping. Floating-point boundary membership is approximate; its contribution
vanishes cubically at the cutoff. Coincident input sites retain multiplicity.

## Evidence obtained in this control

Eight unit tests pass. They check field rotation covariance, label separation,
permutation invariance, midpoint fields, low-moment descriptor collisions,
independent high-precision arithmetic, cutoff crossings, skewed periodic cells,
equivalent cell bases, independently translated source sites, and invalid inputs.

The actual ice extraction check covers 48 inherited component-centroid anchors
(first eight in each of the first training/developmental Ih, II and VI frames).
With diagnostic R = 4 Å and sigma = 0.4 Å, it checks 1,570 field contributors.
All extracted vectors agree with a separate fixed-box image enumeration;
maximum observed coordinate discrepancy is zero. An independent singular-value
bound checks that the reference image box suffices for these particular inputs.
All joint rotation/translation checks pass within the engineering roundoff guard.
These counts are not independent samples or a family-wide validation result.

Reproduce from this directory:

```sh
python test-gaussian-section-markings.py
python check-ice-periodic-fields.py COORDINATES.json OVERLAP-BROAD.json NEW_REPORT.json
```

The checker writes exclusively to a new output and binds input and code hashes.
Current local result: `/tmp/gcts-ice-periodic-field-check-v1.json`.

## Remaining gates before search

1. Learn/calibrate the field representation on training configurations, comparing
   same-base contexts under one shared motif rotation. R and sigma above are
   diagnostic parameters, not optimized or validated settings.
2. Calibrate uncertainty in field-norm units, not Å; the old 0.15 Å cloud radius
   cannot be reused as a field threshold.
3. Verify that supplied training tilings admit common m-values before search,
   and test whole developmental configurations and connection specificity.
4. Integrate field agreement into complete candidate dependencies, preserving
   global dead/forced/earliest-generation scheduling and exact state rollback.
   Numerical uncertainty must not become proved pruning.
5. Two field balls have a midpoint witness when their centers are sufficiently
   close; more than two assignments need a genuine common-witness check.
6. Learn anchors and t-values generally, resolve condition/trajectory provenance,
   and test reconstruction and beyond-input growth. None is supplied by this
   extraction control. Do not equate labels alone with identical conditions.

No web or production search code changed in this control.

## All-training catalogue and paired-context diagnostic

The next run built fields for all 100 training configurations and reused their
168 supplied covers. It retained 278 base motifs and 10,090 exactly interned
observed field decorations. All 29,120 endpoint round-trip transports pass,
with maximum coordinate residual 2.1761e-14 Å. Every supplied atom-level
integer-capacity total remains two, and repeated occurrences have identical
field decorations across covers. These are producer-side checks; independent
all-cover verification is still required. A marking tolerance is deliberately
left unset, rather than copying the raw-cloud tolerance into different units.

The training-only variation diagnostic selects the first observed occurrence
of each base in each frame, before computing distances. It compares 3,139
base/frame representatives in 36,951 cross-frame pairs. Of these representatives,
72 have no other frame with the same base. For each remaining representative,
the nearest distance is the maximum of the two endpoint RKHS distances under
the stored shared base rotation. Quantiles are:

| Quantile | Paired field distance |
| --- | ---: |
| Minimum | 0.0421229 |
| Median | 0.412752 |
| 90% | 0.532985 |
| 95% | 0.580407 |
| Maximum | 1.144640 |

Distances are unnormalized field-norm units, **not Å**. All compared fields
are finite even when neighborhood cardinalities differ. The vectorized
calculation agrees with 74 sampled scalar reference endpoint calculations;
maximum squared-distance difference is 1.7764e-15. Eight representation tests
still pass. Source/code hashes are included in both output reports.

This supports retaining environment-dependent decorations on shared geometry;
it does not prove these particular fields are sufficient or that each observed
decoration must remain distinct. The selected subset is not the full nearest
neighbor library, and no per-endpoint rotations were optimized. Neither the
median nor the 95% quantile should be promoted directly to a growth threshold.
Next: independent training-cover field checks, training/calibration separation,
and paired whole-configuration transfer before any search substitution.

```sh
python ice-periodic-field-library.py COORDINATES.json OVERLAP-BROAD.json DICTIONARY.json PRIOR_LIBRARY.json NEW_LIBRARY.json
python ice-field-variation.py NEW_LIBRARY.json NEW_VARIATION_REPORT.json
```

Current outputs are `/tmp/gcts-ice-periodic-field-library-v1.json` and
`/tmp/gcts-ice-field-variation-v1.json`. The 60 MB catalogue is a local research
artifact, not a new public coordinate redistribution.

## Independent all-cover precheck

`verify-ice-periodic-field-library.py` subsequently reconstructed all 100
training frames independently, without importing the field constructor,
rotation helper, or periodic extractor. Fixed image enumeration is checked
using singular-value bounds for each cell. Direct component unwrapping is
checked against every pair, rather than relying on the producer's spanning tree.
Label-preserving assignment compares each transported field to the same
source-derived field at its shared anchor.

All 168 supplied covers pass: 29,120 endpoint assignments, 14,560 common-anchor
fields, and 43,680 integer atom totals across covers. Maximum coordinate residual
is 2.4308e-14 Å and maximum amplitude residual is 1.8319e-15. Counts across
alternative covers are not counts of unique atoms or independent samples.
This closes the independent positive precheck for the diagnostic representation,
not its calibration, specificity, transfer, or search-integration gates.

```sh
python verify-ice-periodic-field-library.py COORDINATES.json OVERLAP-BROAD.json DICTIONARY.json PRIOR_LIBRARY.json NEW_LIBRARY.json NEW_CHECK.json
```

The report is `/tmp/gcts-ice-periodic-field-library-check-v1.json` and binds the
library SHA-256 `70aa5b589a6cb58d5491812b18c230deb02804fd438a1b7e92007d9d3c38e39e`.
