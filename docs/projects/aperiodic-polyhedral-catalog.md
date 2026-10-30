# Spatial tile-set catalog and independent specimen viewers

The catalog at [`apps/quasicrystal-exact`](../../apps/quasicrystal-exact/) covers
Euclidean three-dimensional tile sets of arbitrary finite cardinality, with
lattice or algebraic coordinate descriptions. It records named families and
construction families rather than claiming a finite enumeration of every
colour refinement, compiler output, or equivalent encoding. Research checked
28 October 2026. Chair44 and its derived rule variants are omitted at the
user's request.

## Coverage and exactness

Eleven source entries supply 44 selectable specimens. Of those, 43 use exact
coordinate records, while the Socolar–Taylor spatial illustration uses an
attributed rounded print mesh. Two entries describe general construction
families without inventing prototype meshes.

| Entry | Geometry and rules available in this page |
| --- | --- |
| Ammann golden rhombohedra | Four chiral decorated prototypes, exact face-centre markings, live geometric search and local GCTS field learning. |
| Socolar–Steinhardt | Four exact zonohedral carriers; full three-mark face table not ported. |
| Danzer ABCK | Four exact tetrahedra; exact identification of right dihedral angles and the source's reflection rule. |
| Danzer octahedral compounds | Four exact, possibly nonconvex reflected compounds; source's face-to-face theorem cited. |
| Goodman–Strauss pair | Exact I and L carriers; full boundary marking functions not ported. |
| Goodman–Strauss connected variant | Exact L and two cross identities; full boundary markings not ported. |
| Čulík–Kari cubes | All 21 symbolic face records and exact face-centre assignments; explicit transcription caveat. |
| Schmitt–Conway–Danzer screw family | One rational convex member; proper motions only, infinitely many exact orientations, sliding issue disclosed. |
| Spatial Socolar–Taylor | Attributed display mesh; a stacking translation is allowed; exact field recipe not ported. |
| Schmitt three-tile compiler | Primary publication and construction-family status; complete geometric recipe unavailable for transcription. |
| General finite-state and marked substitution families | References and instance-specific hypotheses; no fictitious canonical inventory. |

All exact specimens are represented in \(\mathbb Q(\sqrt5)\), with rationals as
its subfield. Predicates, plane hulls, reflections, face identity, and signed
volume use the existing BigInt field operators. Only the display adapter and
camera code use approximate coordinates. The SCD parameter choice is
\(b_1=3,b_2=4,c=1,\lambda=1/2\); its rotation matrix has rational entries
\(4/5\) and \(\pm3/5\), and infinite order. This demonstrates why a number
field does not imply finitely many orientations or discrete attachment choices.

The symbolic Wang tuple follows the figures' cyclic order:
left, front, back, right, top, bottom. Opposite index pairs are
\((0,3),(1,2),(4,5)\). Figure 4 contains the transition
\((0',1,0',1/2)\). Two places in the printed cube formula instead refer to
\((0',1,1,1/2)\), absent from that table. The data use the actual transition
consistently in both places. Tests project every cube to its source transition;
they do not prove the corrected set aperiodic. This transcription is not
activated in a live search.

Sources and the print-mesh license are linked next to each entry and in
[`data/ATTRIBUTION.md`](../../apps/quasicrystal-exact/data/ATTRIBUTION.md).

## Contract conformance

This change authors and inspects source data; it does not introduce a new
coverage/search engine. The Ammann live lane retains its specialized geometric
face-obligation model and earlier audit. The catalog never labels carrier-only
previews as complete rule ports, supplied rules as learned constraints, or
finite patches as infinite-tiling proofs. Adding a catalog entry does not enable
it as a GCTS point-capacity solver.

Each specimen canvas has its own camera and OrbitControls. One shared WebGL
renderer copies into separate canvas surfaces, avoiding one graphics context
per tile. The tile scenes form the left column; dragging rotates each scene
independently and clicking a face opens its exact data below the search.
There are no per-tile action buttons. The main view is exclusively live search,
with visible Run/Pause, Step and Reset controls above the scene. It starts idle,
from the seed, without generating a reference patch. Catalog entries without
a connected engine explicitly disable search and retain their prototype scenes.
The former constructed-patch, library and acceptance-window tabs are removed.
The geometric conformance limits remain. The later GCTS lane adds learned point
fields through the same global section and dependency graph; see the
[learning audit and measured checks](icosahedral-gcts-learning.md). It does not
automatically enable the other catalog entries as search systems.

## Verification

- Rebuild the exact mesh data with `node scripts/build-aperiodic-polyhedra.mjs`.
- Run `node scripts/test-aperiodic-polyhedra.mjs` for exact facet planarity,
  oriented edge cancellation, volume and source-coordinate checks, Danzer
  compound multiplicities, all Wang source projections, and adapter/reflection
  checks for all 44 specimens.
- Existing exact/search/worker suites remain the regression checks for the
  unchanged live engine.
- Browser checks cover loading each finite family, all 21 paginated cube
  viewers, exact inspection, absent-mesh entries, search availability, Run/Pause,
  Step and Reset, and the unmarked control. An actual pointer drag and aligned screenshot comparisons verify that
  rotating one left specimen changes only its canvas. Browser checks also
  verify idle initialization, Step, Run/Pause, Reset, a 60-tile checkpoint
  with 93 placement trials and 34 backtracks, and preserved state while
  inspecting catalog entries without a connected search engine.
