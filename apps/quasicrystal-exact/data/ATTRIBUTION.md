# Polyhedral specimen data

`polyhedra-exact.json` is authored from exact mathematical recipes in the linked
papers. Every scalar is the canonical integer-string triple for
\((a+b\tau)/d\), with \(\tau^2=\tau+1\). The authoring script is
[`build-aperiodic-polyhedra.mjs`](../../../scripts/build-aperiodic-polyhedra.mjs).

- Ammann decorations: Hann, Socolar and Steinhardt,
  [Figure 1](https://arxiv.org/html/1604.02479#S2).
- Golden zonohedron carriers: Socolar and Steinhardt,
  [Quasicrystals II](https://paulsteinhardt.org/wp-content/uploads/2020/10/QuasiPartII.pdf).
- Danzer coordinates and reflected octahedral compounds: Dirk Frettlöh,
  [Table 1 and §1.2](https://www.math.uni-bielefeld.de/~frettloe/papers/ikosa.pdf).
- Goodman–Strauss carriers: [§3 and connected-interior variants](https://www.math.ucdavis.edu/~deloera/MISC/LA-BIBLIO/trunk/Goodman2.pdf).
- SCD biprism: Baake and Frettlöh,
  [§1](https://www.math.uni-bielefeld.de/~frettloe/papers/scdart.pdf).
- Wang symbols: Čulík and Kari,
  [Figure 4 and Theorem 3](https://www.jucs.org/jucs_1_10/an_aperiodic_set_of/Culik_II_K.pdf).
  The explicit transcription correction is recorded on the page and in the
  symbolic data module. It is not an independently certified new tile set.

`socolar-taylor-display.json` is a format conversion of the spatial tile mesh
by **Edmund Harriss**, supplied via
[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Socolar-Taylor_3D_monotile.stl),
originally shared on Thingiverse. The mesh and its JSON conversion are licensed
under [Creative Commons Attribution–ShareAlike 3.0 Unported](https://creativecommons.org/licenses/by-sa/3.0/).
Changes: decoded the binary STL, shared identical vertex records, and wrote JSON.
The source contains rounded numerical coordinates. This file is exclusively a
visual illustration; it supplies no exact predicates, placement model, marking
assignments, or tiling certificate.
