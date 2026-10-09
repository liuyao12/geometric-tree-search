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
python mixed_reflections.py
python compute_modes.py
python elementary_modes.py
python additional_tiles.py
python compute_additional_modes.py
python build_page.py
python verify_elementary.py
python verify_additional.py
python verify_notes.py
python verify_modes.py
```

Run these commands from this directory. The original family and chair scripts
only need to be rerun when their inputs change. For a prose edit, update the
HTML directly; `build_page.py` refreshes only its data tables and explorer
payload. It never creates a PDF. The existing `build_report.py` belongs to the
older PDF workflow and is not part of the current reproduction commands.

The current reading order starts with an elementary cell. `elementary_modes.py`
generates 289 explicit functions independently of numerical eigenvalues:
separated unit-square functions and the compatible lattice-periodic scalar
reflection sectors of a unit equilateral triangle. Sine/cosine or odd/even
median parity determines the tile's boundary assignment before comparison
with FEM. The triangle catalogue is a subset of its full homogeneous spectrum.
`elementary-modes.json` retains all exact integer frequencies and coefficients;
`verify_elementary.py` independently checks source geometry, source and tile
boundary conditions, median symmetry and frequency covariance. The receipt is
`elementary-verification.json`. After changing only the catalogue, rerun its
generator, `build_page.py`, and its verifier; the FEM fields need no new solve.

`elementary-viewer.js` displays the exact levels with proportional spacing and
evaluates the same formula on both the elementary cell and the selected tile.
The two plots share a color normalization. These are formula evaluations,
clearly distinguished from the computed FEM eigenfunctions below. A link
opens a recorded numerical family match, an unresolved candidate, or the
computed spectrum when the exact level lies above its truncation.
The numerical viewer initially hides recorded family matches and the known
Neumann constant. This
display filter retains unknown modes and unresolved candidates and preserves
their original ranks; it is not a certified continuum deflation or a
classification of all remaining eigenvalues as non-algebraic. All 2010
computed fields and complete unfiltered lists remain available.

The additional atlas contains the Sphinx hexiamond, the bare regular hexagon
underlying Socolar–Taylor, the pinwheel triangle, both Penrose rhombi, and
the Ammann–Beenker rhombus. Each has 60 Dirichlet and 60 Neumann fields on two
nested meshes. `additional-tiles.json` records the geometries, primary sources,
tiling status and 120 further exact elementary functions. Matching rules and
substitutions remain separate from the bare-polygon boundary operators.
`additional-mode-data.json` retains numerical diagnostics, projection matches
and image checksums; `additional-verification.json` checks every field and
boundary certificate. These datasets are embedded separately in the HTML,
preserving the preceding numerical receipt and its input hashes.

Every nonconstant exact family now has an exact certificate for each tile
edge, source edge and triangle median: the affine reflection, integer phase
and odd/even parity imply Dirichlet/Neumann conditions. Square products use
integer coordinate lines. The universal Neumann constant has zero gradient
on any polygon. The sampled traces and fluxes supplement these identities.
The FEM Dirichlet trace is imposed strongly and remains zero on interpolated
boundary edges. FEM Neumann conditions are natural weak conditions; the
normal derivative of a displayed P1 field need not vanish pointwise.
Corners and mixed junctions use the weak trace formulation. Numerical
residuals and refinement movements do not certify continuum error bounds.

`arithmetic_spectra.py` adds exact integer checks of triangular-lattice
reflections for the natural Hat and Turtle, four nested meshes with ninety
L-triomino Dirichlet modes each, and twelve Turtle low modes. Its
`arithmetic-spectra.json` receipt includes eigenfunction-subspace projection
scores used to identify the known arithmetic modes. `exact-modes.png` shows
explicit functions evaluated from their formulas. The gap explorer is
`gap-explorer.js`; its data are embedded by `build_page.py`, so the page
does not depend on a second data request to initialize.

`compute_modes.py` retains and renders 1290 numerical eigenfunctions: ninety
Dirichlet, ninety Neumann (including the constant), and ninety mixed modes on
the L-triomino; twelve Dirichlet and twelve Neumann controls plus 240 modes
for each complementary short/long mixed assignment on each of Hat and Turtle;
and twelve Dirichlet modes on the equilateral polygon. Hat now uses level four:
the preceding mesh reproduces its original level-three Dirichlet values.
The `modes-*.png` files are image atlases of the computed P1 fields, not
evaluations of analytic formulas. Pixel sampling preserves aspect ratio;
each field is divided by its maximum absolute nodal value. The matrix
residuals, mass orthogonality, mesh refinement, analytic-subspace projections
and image checksums are in `mode-data.json`. `verify_modes.py` checks
provenance, every image cell, ordered spectra and the explicit gluing control.
New atlases use 255 color levels and lossless palette PNG encoding, with up
to sixty fields per image page to limit download and image memory. Every
page and decoded cell has a checksum. The viewer loads the selected page.

The mixed control assigns Dirichlet to vertical edges and Neumann to horizontal
edges, constraining junction vertices belonging to the Dirichlet trace. Its
explicit sine–cosine family glues with translation phases on the known
periodic chair lattice. This claim covers that subset, not every mixed mode,
and is not a model of Chair44 markings. The webpage explains the construction
and the distinction between comparing spectra, taking a direct sum, and
coupling interfaces. `spectrum-viewer.js` positions numerical estimates
proportionally on a shared axis with separate operator rows. Its mode selector
and zoom controls distinguish nearly coincident modes. The gold rings indicate
projection matches to constructed families; other values have unknown
normalized algebraicity. All data are embedded by `build_page.py`.

The primary mixed experiments are Hat and Turtle with Dirichlet on short
primitive edges and Neumann on long edges, and the complementary assignment.
`mixed_reflections.py` and `mixed-reflections.json` record the two real
characters of the dihedral group that alternate sign between its reflection
classes. Their nonzero sine orbit sums are exact mixed eigenfunctions with
normalized levels \(16Q/3\). The first shell is \(Q=1\) for short Dirichlet
and \(Q=3\) for long Dirichlet. The exact construction includes singular
orbits when their stabilizer character is positive. All fourteen primitive
segments are retained, so merging two short segments never changes their
boundary assignment. The characters give coherent value and gradient
transport for placements in the specified lattice semidirect dihedral group;
this compatibility calculation does not reconstruct or verify an entire tiling.

The first Turtle levels and Hat's short-Dirichlet level pass the numerical
projection checks. Hat's long-Dirichlet level remains unresolved, with its
analytic projection spread across nearby eigenvectors. Dashed candidate nodes
retain this information without assigning them the exact continuum value.
The receipts also retain preceding-mesh identification and candidate scores.

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
