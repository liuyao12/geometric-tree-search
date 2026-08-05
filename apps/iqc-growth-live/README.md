# GCTS Matter: live growth and backtracking

A static GitHub Pages visualization of the two-species, three-dimensional
materials-GCTS experiment. It shows the search mechanism rather than replaying
the full Python Monte Carlo calculation:

- compatible patch proposals on a live 3D frontier;
- overlapping finite marking domains;
- exact-oracle and learned-interval decisions;
- speculative search-stack growth; and
- visible rollback when a branch accumulates geometric conflicts.

The fixed benchmark numbers in the interface come from the offline BCI-2P
reference experiments. The browser animation is deliberately labeled as a
structural surrogate rather than a molecular-dynamics trajectory.

Serve the repository root and open `/apps/iqc-growth-live/`.
