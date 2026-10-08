# Tetrahedron structure atlas

Static educational exhibit for the existing GitHub Pages site. Open `index.html` through an HTTP server. Three.js and OrbitControls are bundled from the repository's established vendor files; MathJax uses the established CDN renderer.

## Provenance

- `data/approximant.json`: 82 decimal position/quaternion records transcribed from pages 25–26 of https://arxiv.org/pdf/1012.5138. Box dimensions are 10.2088453514, 2.5716864401, 9.8233760813. Quaternion order in the source is scalar first. Local vertices have coordinates (1,1,1), (1,-1,-1), (-1,1,-1), (-1,-1,1). Volume per tetrahedron is 8/3; calculated density is 0.8478659094371408.
- The 85.0267% result describes a separately compressed 656-particle supercell. The displayed 82-particle data must not be described as that configuration.
- `figures/packing.jpg`, `structure.jpg`, `diffraction.jpg`: scientific figures extracted from the authors' arXiv paper (Figures 1, 3 and S6), attributed on the page. These are original research images, not generated reconstructions. The original full quasicrystal dataset was linked from a now-missing lab wiki; no invented 3D quasicrystal is substituted.
- Double dimer: https://arxiv.org/abs/1001.0586, Definition 1, Definition 2 and Theorem 1. Basis vectors are a+b, b+c, c+a, with negative dimer offset d+a. Both positive and inverted dimers contain two tetrahedra. The entire construction is uniformly rescaled by 2/3 to match the approximant's tetrahedron edge length.

## Algorithm contract / conformance scope

Read `docs/basic-tiling-algorithm.md` before implementation. This is a geometric rendering of published packings, not a tiling/search engine. It performs no frontier search, point-value legality checking, learned pruning or RL proposals. Complete candidate incidence, generation ordering and rollback are therefore not applicable. Published decimal coordinates and browser rendering are floating-point approximations, not exact certificates. Repetition and clipping are visualization controls and make no density/search claims. Particle shrinking is explicitly visual only.

## Validation performed

- Parsed exactly 82 records and reproduced the published cell density within 1e-10.
- Separating-axis checks on all 178,145 relevant particle/neighbor pairs found no interior overlap above 1e-8 in the approximant, including adjacent periodic cells.
- Independently reproduced the dimer determinant density 4000/4671 and checked its neighboring-cell geometry with a 1e-9 overlap tolerance.
- Browser checks: all three selections; 27-cell count (2,214 approximant / 108 dimer tetrahedra); view buttons, colour selection, source figures, MathJax rendering; no browser errors. Phone viewport has no horizontal overflow.

These tolerance-based checks support the transcription/rendering. They are not exact packing certificates.
