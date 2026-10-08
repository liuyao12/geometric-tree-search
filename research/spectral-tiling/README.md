# Notes on spectra, markings and tilings

The [web notebook](../../docs/projects/spectral-tiling-study.html) is the current
document. It collects exact eigenfunction families, numerical spectral
descriptions, boundary models, and connections with nonperiodic tilings.
The earlier PDF and LaTeX files are archived snapshots; they are no longer
updated alongside the webpage.

The computation estimates the first twelve Dirichlet modes of ten members of
the Hat–Turtle family. Tiling labels come from the cited published family
theorem. They are never inferred from finite growth or a spectral classifier.

Install `requirements.txt` into a temporary environment, then run:

```sh
python compute.py
python verify.py
python chair_control.py
python arithmetic_spectra.py
python build_page.py
python verify_notes.py
```

Run these commands from this directory. The original family and chair scripts
only need to be rerun when their inputs change. For a prose edit, update the
HTML directly; `build_page.py` refreshes only its data tables and explorer
payload. It never creates a PDF. The existing `build_report.py` belongs to the
older PDF workflow and is not part of the current reproduction commands.

`arithmetic_spectra.py` adds exact integer checks of triangular-lattice
reflections for the natural Hat and Turtle, four nested meshes with ninety
L-triomino Dirichlet modes each, and twelve Turtle low modes. Its
`arithmetic-spectra.json` receipt includes eigenfunction-subspace projection
scores used to identify the known arithmetic modes. `exact-modes.png` shows
explicit functions evaluated from their formulas. The gap explorer is
`gap-explorer.js`; its data are embedded by `build_page.py`, so the page
does not depend on a second data request to initialize.

Eleven intervals through the normalized endpoint \(32\) have numerical counts
that pass the stated refinement and endpoint-distance checks. Two intervals
near \(34\) remain pending. All counts include multiplicity and exclude exact
ladder endpoints. Other normalized eigenvalues are not proved non-algebraic.
Even stable counts need rigorous continuum enclosures for certification.

`verify_notes.py` independently checks the new receipt's hashes, lattice
areas, sample boundary traces and fluxes, multiplicities, projection ranks,
counts, refinement movements, and local HTML references. It writes
`notes-verification.json`; sample evaluations support, rather than replace,
the analytic reflection proof in the notes.

`results.json` contains all eigenvalues, meshes, geometry, residuals, square
controls, versions and the SHA-256 hash of the executed computation.
`verification.json` records independent checks and exact rational calculations
in the quadratic field for the heat-invariant counterexample.

The continuum mesh model uses floating arithmetic. Its eigenvalues are
numerical estimates, without certified continuum error bounds. The exact
heat-coefficient equality uses rational arithmetic with the square root of
three. It does not establish full isospectrality.

The L-triomino follow-up adds `chair_control.py` and `chair-control.json`.
They check an explicit periodic translation lattice for the planar triomino
and the spatial seven-cube chair, the exact planar corner heat coefficient,
and the sufficient height-scaling conditions stated in Tsiokos's Chair44
preprint. They also estimate twelve planar Dirichlet modes and the unit-height
prism modes using separation of variables. No numerical spectrum is computed
for the geometric Chair44. Its tiling label comes from the cited theorem,
whose full proof is not independently verified by this study. The project's
centered tetrahedral relief has no inherited aperiodicity label.

No tiling/search engine is created or modified. This is a specialized
continuum spectral experiment, not the GCTS point-value reference baseline.
The notes describe the requirements for any later sound integration.
