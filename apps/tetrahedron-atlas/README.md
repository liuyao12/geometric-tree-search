# Tetrahedron structure atlas

Static educational exhibit for the established GitHub Pages site. Serve `index.html` through HTTP. Three.js and OrbitControls are bundled from the repository's vendor files. MathJax uses the established CDN renderer. Direct entry links support `#approx` and `#dimer`.

## Coordinate provenance

`data/approximant.json` contains 82 decimal position/quaternion records transcribed from pages 25–26 of https://arxiv.org/pdf/1012.5138. The box lengths are \((10.2088453514,2.5716864401,9.8233760813)\); source quaternions are scalar first. Local vertices are \((1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1)\). Each tetrahedron has volume \(8/3\), giving density \(0.8478659094371408\). The separate 85.0267% result describes a compressed 656-particle supercell; these coordinates do not reproduce it.

`figures/packing.jpg`, `structure.jpg`, and `diffraction.jpg` are Figures 1, 3, and S6 from the authors' arXiv paper, attributed on the page. The old full-quasicrystal dataset link is gone; no fabricated 3D quasicrystal is substituted.

The double dimer follows Definitions 1–2, Equations (6)–(7), (11), (13), and Theorem 1 of https://arxiv.org/abs/1001.0586. Basis vectors are \(a+b,b+c,c+a\), with negative-dimer offset \(d+a\). The construction is uniformly rescaled by \(2/3\) so its edge length matches the approximant.

## Unit cell and periodic assembly

The current UI starts with the published packed unit cell. The separation slider is an exploded view: particle centres move away from the cell centroid while particle sizes and orientations stay fixed. The periodic assembly slider moves up to seven translated copies into a bounded block, with two cells along each lattice basis direction. It is neither an inflation hierarchy nor a physical compression trajectory. The older compression helpers remain geometry utilities but are not exposed in this UI. Aperiodic hierarchy controls require a documented substitution or inflation rule; none is claimed for the source-figure quasicrystal view.

Particle shrinking, slicing, transparency and orientation filtering affect only rendering. Density labels refer to the published packed endpoint, not the exploded view or incomplete assembly.

## Orientations

The rotatable ball uses axis–angle representatives of \(\mathrm{SO}(3)\), with antipodal boundary points identified. Rotations are relative to the reference tile. Labelled-frame mode retains source vertex labels. The default identifies the 12 proper tetrahedral symmetries, so geometry-equivalent vertex permutations are identified. It chooses the closest-to-identity quaternion representative from \(qT\), not from improper reflections. Frame orientations are merged only within a numerical angular tolerance of \(10^{-7}\) radians. Small differences in the 82 source poses remain visible.

The selected-neighborhood slider measures geodesic angular distance (minimum over the 12 symmetries in quotient mode). Dot selection and a labelled menu support isolation, hiding, restoration and optional angular neighborhoods. Filter state persists through periodic copy assembly and separation. Changing orientation convention resets filters. Counts refer to the patch before slicing; the reference outline remains as a frame marker when its orientation is hidden.

## Algorithm contract / conformance scope

Read `docs/basic-tiling-algorithm.md` before implementation. This is a geometric visualization, not a tiling/search engine. It performs no frontier search, point-value legality checking, learned pruning or RL proposals. Candidate incidence, generation scheduling and rollback therefore do not apply. Decimal coordinates and rendering are floating-point approximations, not exact certificates. The periodic display is not a GCTS generation sequence.

## Validation

Original transcription checks reproduced the published approximant density within \(10^{-10}\) and found no interior overlap above \(10^{-8}\) across 178,145 particle/neighbor checks. The new dimer pose representation and path were independently checked with separating axes at 21 deformation samples, across 8,862 neighboring-pair checks, with tolerance \(10^{-8}\).

Model checks verified all 12 proper symmetries preserve the vertex set, symmetry-equivalent quaternion representatives/distances agree, analytical density endpoints match, all growth counts agree, and the reference pose remains unchanged at every stage and sampled compression position.

Earlier browser QA covered the superseded shell/compression controls. Current QA checks the unit cell, separation, bounded periodic assembly and orientation filters. These approximate checks support the visualization; they are not exact packing certificates.

## Quasicrystal comparison

The comparison toggle opens published Figure 3 beside the interactive approximant on wide screens. Source panels are identified in the caption, with a local/long-range comparison table and the existing source diffraction figure below. It makes no coordinate-matched overlay claim. `?compare=1#approx` opens this comparison directly.
