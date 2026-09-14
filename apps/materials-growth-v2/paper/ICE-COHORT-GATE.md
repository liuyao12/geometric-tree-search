# Ice family: distinguish protocol support from independent validation

14 September 2026. This is a provenance safeguard, not a new growth result.

The [authors' preprint, methods II.2](https://arxiv.org/html/2405.20217v1#S2.SS2)
specifies NPT sampling at 100 K and 1 bar, random selection of validation
configurations, and nested training sets. It also distinguishes the sampling
ensemble from the more accurately evaluated target ensemble. The preprint
lists 80 molecules for VIII, whereas our acquired files contain 64; that mapping
remains unresolved. These observations support a paper-level common protocol,
not independent trajectories or verified file-level conditions.

## Executable claim gate

The new sidecar generator binds all 2,000 existing ice configuration IDs to
source hashes and the reviewed evidence. It preserves missing numerical
conditions and trajectory IDs rather than inventing them. Paper-level 100 K /
1 bar support is stored separately from verified file-linked conditions.

The generic family gate requires a common element set, finite declared
temperature/pressure values and file-linked protocol evidence for a verified
same-condition claim. A separate independent-holdout gate additionally requires
documented independent runs, traceable trajectory IDs, and no run shared across
training and test. Distinct labels alone are not independence evidence.

All 2,000 ice records currently fail those stronger claim gates. Exploratory
geometry learning remains allowed. One positive and thirteen negative controls
test missing metadata, nonfinite values, differing conditions/elements, shared
trajectories and unsupported independence. Matching null values must never be
mistaken for matching conditions.

The gate is a standalone research admission check; it does not intercept every
existing training script or change historical results. Evidence categories are
curated inputs, not facts automatically proved by a metadata string.

## Physics-agnostic boundary

No temperature, pressure, force, energy, phase or formation-history field is
passed to motif discovery, t/m fitting, candidate generation or search. The
metadata govern what dataset claims we can make, not the geometry algorithm.
Equal elements and nominal conditions do not imply identical composition,
equilibrium, independent observations or the same sampling distribution.

We need traceable independent coordinate runs, or a new documented sampling
campaign, for the stronger evaluation. Generating more tilings of existing
frames, repeating periodic cells, or renaming train/test IDs cannot supply that
evidence. Existing ice results remain developmental known-coordinate tests.
This gate does not resolve the still-open cluster/marking-learning and growth
problems, but prevents promoting an unsuitable split to an independent result.

```
python ice-cohort-provenance.py ICE_PROVENANCE COHORT_RECORDS
python family-cohort-gate.py COHORT_RECORDS COHORT_CHECK
python test-family-cohort-gate.py
```

The [pinned coordinate repository](https://github.com/venkatkapil24/fine-tuning-MLPs-ice-polymorphs/tree/c9a4bb534b35bfc8f467d7388f3056325bd2dd4e)
remains the source. Raw coordinate data are not republished. This source review
uses the accessible preprint version explicitly; it does not assert that the
final publication resolves the file discrepancy.
