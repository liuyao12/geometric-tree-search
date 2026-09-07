# Penrose cyclotomic lattice laboratory

Published app: <https://liuyao12.github.io/geometric-tree-search/penrose-model-set/>.
Use GitHub Pages for previews and publication. The default P3
experiment grows rhombs at exposed edges in ℤ[ζ₅] ≅ ℤ⁴, with GCTS angle-capacity
pruning and an exact local pentagrid predicate. The main canvas is the physical
embedding; the inset contains actual conjugate coordinates colored by mod-5
residue layer. Drag to pan and scroll to zoom.

Every thick rhomb is a rigid copy of one fixed five-stripe prototile; every
thin rhomb is a rigid copy of the other. The catalog uses those same templates.
The solver rejects proposals whose complete edge markings cannot match,
then applies the exact window predicate. These are supplied classical Ammann
markings, not a learned rediscovery. The historical midpoint learner remains
under the diagnostic disclosure. P1, P2, and mixed catalog paths remain available.

Validation from the repository root:

```sh
node scripts/test-penrose-ammann.mjs
node scripts/test-penrose-cyclotomic.mjs
node scripts/test-penrose-exact.mjs
```

See `../../docs/projects/penrose-model-set-gcts.md` for the mathematics,
search limitations, and future marking-learning work.
