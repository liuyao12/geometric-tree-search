# GCTS Matter: learned clusters and continuous growth

A static GitHub Pages visualization of the two-species, three-dimensional
materials-GCTS pipeline. It starts from one finite configuration with 216
known colored atomic positions, then illustrates:

- species-aware discovery of overlapping local clusters;
- reduction to tetrahedral, icosahedral, and corona-like polyhedral symbols;
- finite marked interfaces and compatible-overlap rules;
- one continuous search that reconstructs the 216-atom input and naturally
  continues through its exposed frontier toward a 2,160-atom
  configuration, without copying the starting window as a block.

The four pipeline stages can be selected individually or run continuously.
The search crosses the 216-atom observation boundary without changing modes or
resetting its learned finite states. The interface exposes exact-oracle and
learned-interval decisions, the accepted search stack, and marking reuse;
internal branch revisions are intentionally not called out visually.

Continuation does not target a cube or impose a hard spherical boundary. It
samples among locally near-best cluster attachments on the exposed frontier.
A soft penalty for overrepresented angular sectors, plus stochastic tie
breaking, keeps growth approximately radial unless compatibility genuinely
forces a preferred direction.

Two live structural checks compare the observed window with the sites recovered
by the search. A finite-window radial distribution function uses the reference
median nearest-neighbor spacing `a`, while the coordination-number distribution
uses a fixed first-shell cutoff of `1.32a`. During continuation, both charts keep
the recovered 216-site window as the comparison sample so the larger frontier
does not silently change the validation domain.

Each coordination bin is interactive. Selecting a value emphasizes atoms with
that first-shell coordination in the current comparable scene, dims unrelated
atoms, and keeps bonds touching the selected sites visible. The same bin or the
compact clear control restores the unfiltered view.

The fixed benchmark numbers in the interface come from the offline BCI-2P
reference experiments. The browser animation is deliberately labeled as a
structural surrogate rather than a molecular-dynamics trajectory.

Serve the repository root and open `/apps/iqc-growth-live/`.
