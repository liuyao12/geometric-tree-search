# Boron family: first pre-search diagnostic, 14 September 2026

All six coordinate models in the [2016 paper's supplement](https://authors.library.caltech.edu/records/dcaev-djw82)
passed independent symmetry expansion, full-occupancy, atom-count and periodic
minimum-distance checks. These are six models, not six distinct established phases.
The later [2017 Reply](https://doi.org/10.1103/PhysRevLett.118.089602) is not an erratum.
No ground-state claim is needed for this geometric benchmark.

| Model | Atoms in supplied cell | Exact positive pair-cover prechecks / 6 | Other outcomes |
| --- | ---: | ---: | --- |
| alpha | 12 | 5 | 1 positive-support/rational gate failure |
| beta-105 | 105 | 0 | 6 numerical LP infeasibility reports |
| beta-106 | 106 | 0 | 6 numerical LP infeasibility reports |
| gamma | 28 | 5 | 1 numerical LP infeasibility report |
| tau-105 | 210 | 0 | 6 numerical LP infeasibility reports |
| tau-106 | 212 | 0 | 6 numerical LP infeasibility reports |

## Precisely what was tested

For each supplied periodic cell, enumerate one minimum-image unordered pair per
pair of distinct atom IDs. Choose radius = median nearest-neighbor distance times
1.15, 1.35 or 1.6. Group pair lengths in sorted first-fit bins with maximum width
0.01 or 0.05 angstrom. These six settings were run for every input, without
per-material tuning. All observed pairs in the chosen domain are included.

Learn one shared endpoint-symmetric t-value per length class by linear programming,
maximizing the minimum t. Substitute rational reconstructions into the integer
incidence equations and require exact sums of 1 and strictly positive weights.
Learn scalar equality labels from type incidence at shared atoms. All ten passing
settings have one connected positive-support graph and **only one scalar label**.
Those markings are valid but cannot distinguish connections. Failures refer only
to this restricted all-occurrences pair dictionary, not to GCTS, the structure's
existence, or all possible occurrence selections. Numerical infeasibility statuses
are not independent exact infeasibility certificates.

This is a finite periodic-quotient control, not a proof about the infinite lift:
distinct periodic images of an atom pair are not included separately. No blind
growth or tree search has been run. Pair classes do not test B12/B57 recovery,
arbitrary irregular motifs, learned non-atomic anchors, or general m representations.
The next experiment must address those deficiencies rather than treat successful
pair filling as a finished growth model.

## Importer issue found

tau-B105 lists space-group number 0 and an empty group name, but provides eight
explicit operations. The ASE validation copy uses a nominal P1 importer placeholder
with those original operations unchanged. Independently applying the original
operations with Gemmi gives the same 210 positions. The original CIF is untouched;
the placeholder is not a reassignment of physical symmetry.

## Reproduce

Python dependencies: numpy 2.5.3, scipy 1.18.1, ase 3.29.0, gemmi 0.7.5.

```
python boron-input-audit.py output-boron
python test-boron-precheck.py
python boron-pair-precheck.py output-boron/input-audit.json output-boron/pair-precheck.json
```

Keep `presearch-markings.py` beside the scripts. Downloads check the repository's
MD5 and record SHA256. Synthetic tests check tetrahedron weights, rigid-transform
invariance, and an infeasible three-point path. Raw publisher CIFs are fetched
from their original host, not redistributed here.

## Coverage still pending

Tetragonal variants, delta-orthorhombic/B52, reported pseudo-cubic B52 and
high-pressure alpha-Ga-type boron remain in the acquisition queue. Occupancy-resolved
configurations must be distinguished from partial-occupancy refinements. This batch
does **not** exhaust boron polymorphs. The production app is unchanged.
