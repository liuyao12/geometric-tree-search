# Notes on spectra, markings and tilings

The [web notebook](../../docs/projects/spectral-tiling-study.html) is the current
document. It collects exact eigenfunction families, numerical spectral
descriptions, boundary models, and connections with nonperiodic tilings.
The earlier PDF and LaTeX files are archived snapshots; they are no longer
updated alongside the webpage.

The current focus is the seven-cube 3D chair. The dedicated
[chair Notes](../../docs/projects/chair-boundary-modes.html) transfer the given
Chair44 arrow rule to one prescribed scalar homogeneous-Neumann field.
`chair_boundary_field.mjs` checks the polynomial trace encoding, all 864 facing
panel cases and 3,000 relative tile placements, recovering the 44 legal face
neighbors. Integer translations and all 24 proper cubic rotations are allowed;
reflections and unrestricted placement registration are outside this result.
The infinite existence and decorated aperiodicity conclusion uses
Goodman–Strauss's cited Chair44 preprint theorem. No field-erasure theorem is
claimed. The exact field is an infinite eigenmode expansion, with exactly zero
constant coefficient. A separate seam-tolerance argument supplies a finite
continuum cutoff in principle, without a computed or certified value.
`chair_modal_projection.py` computes 60 modes on two nested P1 tetrahedral
meshes and projects the sampled target. The low truncation captures little of
the carrier and does not inherit its exact matching rule. The 3D viewer plots
surface traces and shows coefficients on a proportional spectral axis.
`build_chair_page.py` builds the webpage, and `verify_chair_field.py` independently
checks geometry, contact equivalence, numerical controls and artifacts.
No search engine or learned marking is modified.

The preceding sphinx investigation is retained. The dedicated
[sphinx Notes](../../docs/projects/sphinx-boundary-modes.html) give an explicit
twenty-two-state palette of smooth homogeneous-Neumann fields on the exact
sphinx. `sphinx_boundary_palette.py` verifies forced pairing into parallelograms
and all 13,310 candidate contacts; the matching system is exactly Jeandel–Rao.
The resulting decorated tilings are aperiodic; erasing the fields leaves
periodic sphinx pairs. Triangular-lattice translations and six rotations are
allowed, with reflections excluded and amplitudes fixed. Each field has an
infinite Neumann expansion. `sphinx_modal_projection.py` retains 180 modes on
two meshes, all state coefficients, truncation diagnostics and three numerical
eigenfunction atlases. The page's field selector and spectrum viewer connect
those coefficients to clickable numerical eigenfunctions. Finite projections
disturb the exact matching traces and have no inherited tiling claim.
Under a separate fixed \(L^2\) seam tolerance, the Notes prove that sufficiently
large finite continuum eigenmode sums preserve the same contact table and
force decorated aperiodicity. No numerical cutoff is certified, and this
changed matching rule does not give continuous gluing.
`build_sphinx_page.py` builds the page, and `verify_sphinx.py` independently checks
geometry, the encoded adjacency, coefficients and images. Goodman–Strauss's
sphinx-substitution system is a separate route using auxiliary edge/vertex
pieces; its transfer to a verified finite boundary-only palette on exact
sphinxes has not been completed here. This work is a specialized continuum
construction and contact audit, not a GCTS search engine.

The preceding L-triomino investigation is retained. Its dedicated webpage is
[L-triomino boundary-mode Notes](../../docs/projects/l-triomino-boundary-modes.html).
`l_boundary_palette.py` constructs twenty-two smooth Neumann field states on
that shape, with exact unit-segment traces. An exhaustive contact audit checks
unique pairing and reduction to Jeandel–Rao's aperiodic palette. Integer
translations and quarter-turn rotations are allowed; reflections are excluded.
Every state uses an infinite ordinary Neumann eigenfunction expansion. A
finite-mode construction is not established. The fields are static, and the
allowed palette is an extra constraint beyond homogeneous Neumann conditions.
The aperiodicity includes the field states; erasing the fields leaves a
periodic arrangement of L-triomino pairs.
`l_modal_projection.py` projects all twenty-two fields onto the first 180
Neumann FEM modes on two meshes. Its finite projections disturb the exact
traces and have no inherited tiling or aperiodicity claim. The construction,
contact audit, projection coefficients and images are retained in the two
`l-*.json` receipts. No search engine is modified. The broader datasets below
are preceding work.

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
python analyze_patterns.py
python boundary_mode_palette.py
python l_boundary_palette.py
python l_modal_projection.py
python sphinx_boundary_palette.py
python sphinx_modal_projection.py
python build_sphinx_page.py
python verify_sphinx.py
node chair_boundary_field.mjs
python chair_modal_projection.py
python build_chair_page.py
python verify_chair_field.py
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

The webpage's small boundary-matching construction is reproduced by
`boundary_mode_palette.py`. Four edge carriers are superpositions of seven
ordinary Neumann square eigenfunctions at normalized levels \(0,1,4,5\).
A finite eleven-state coefficient palette exactly encodes Jeandel–Rao's
Figure 4 Wang set. Every total static field has zero normal derivative;
value matching also gives flux cancellation. The total field combines
several eigenvalues, and its components generally do not match separately.
The receipt `boundary-mode-palette.json` retains the source tuples, rational
cosine coefficients, both adjacency matrices and analytic-projection checks.
`boundary-mode-palette.png` samples the formulas on a shared absolute scale.
Infinite existence and aperiodicity follow from the cited theorem, not from
finite adjacency checks. Translations only and fixed amplitudes are essential.
The Notes also derive a common nonlocal self-adjoint boundary operator with
one four-dimensional ground eigenspace encoding the same palette; that
single-frequency alternative fails flux matching. No standard homogeneous
Dirichlet/Neumann single-eigenvalue aperiodicity claim is made.

The cross-example synthesis is the webpage's “Patterns across the examples”
section. `analyze_patterns.py` writes `pattern-analysis.json`: integer lattice
areas give the constructed-mode densities; root-lattice affine certificates
show that the full triangle basis extends to Sphinx and the bare regular
hexagon; quadratic-field identities and reflection-generated periods support
the Penrose and Ammann–Beenker finite-plane-wave obstructions. The larger
triangle-derived families are not yet implemented in the interactive viewer
or used for numerical projection matches. Their asymptotic fraction is
\(1/6\), compared with \(1/36\) for each currently displayed sector.
This is a derived subspace size, not a classification of all algebraic values.
The Notes now cite McCartin's partial/mixed trigonometric classification and
Rowlett and collaborators' theorem on whole-space analytic continuation of
the Dirichlet ground state. These distinguish reflection mechanisms from
placement rules and from forced aperiodicity.

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
