# GCTS Matter: live growth and backtracking

A static GitHub Pages visualization of the two-species, three-dimensional
materials-GCTS pipeline. It starts from one finite configuration with 216
known colored atomic positions, then illustrates:

- species-aware discovery of overlapping local clusters;
- reduction to tetrahedral, icosahedral, and corona-like polyhedral symbols;
- finite marked interfaces and compatible-overlap rules;
- reversible reconstruction of the 216-atom input; and
- live macro-cluster growth toward a 2,160-atom configuration.

The five pipeline stages can be selected individually or run continuously.
During reconstruction and deployment, the interface exposes exact-oracle and
learned-interval decisions, the speculative search stack, marking reuse, and
explicit multi-atom rollback.

The fixed benchmark numbers in the interface come from the offline BCI-2P
reference experiments. The browser animation is deliberately labeled as a
structural surrogate rather than a molecular-dynamics trajectory.

Serve the repository root and open `/apps/iqc-growth-live/`.
