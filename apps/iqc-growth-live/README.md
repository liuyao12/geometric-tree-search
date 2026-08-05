# GCTS Matter: learned clusters and continuous growth

A static GitHub Pages visualization of a multi-element, three-dimensional
materials-GCTS pipeline. It starts from one finite configuration with 216
element-labelled atomic positions, then illustrates:

- element-aware discovery of local-environment clusters;
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

The selectable inputs now use distinct chemical systems rather than generic
blue/green species: an exact 3×3×3 NaCl rocksalt supercell (`a = 5.640 Å`), a
Cu-Zr metallic-glass surrogate, an Al-Cu-Fe icosahedral-approximant surrogate,
and a silicon BC8-like network. Coordinates used by the learner are expressed
in ångströms; the 3D scene applies a uniform display scale. Element-dependent
sphere radii and colors are presentation encodings, not electron densities.

The cluster-finding stage is computed rather than scripted. For every atom it
builds a periodic, rotation-invariant local descriptor containing central and
neighbor element channels, Gaussian radial functions through `1.9a`, a
first-shell angular histogram, and coordination terms. Features are standardized
and grouped by deterministic k-medoids. In the learning view, atom color denotes
the resulting assignment, wireframes and colored bonds identify medoid neighbor
shells, and the inspector reports each cluster's population, medoid element,
coordination, and within-cluster spread. This is a compact ACSF-like descriptor,
not a full SOAP implementation.

The learned classes partition all 216 atom centers: every center receives one
environment label, while the corresponding radius-`1.9a` neighborhoods overlap
and therefore cover the atomic configuration. The encoding stage now preserves
that learned cardinality and shows the actual medoid first shell for every
class; it no longer substitutes the same three demonstration polyhedra.

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

Each coordination bin is interactive. Selecting a value chooses the matching
center nearest the middle of the current comparable scene, emphasizes that
center and its actual first-shell neighbors, and draws one segment from the
center to every counted neighbor. The status retains the number of centers in
the histogram bin while reporting how many neighbors are shown. The same bin or
the compact clear control restores the unfiltered view.

The fixed benchmark numbers in the interface come from the offline BCI-2P
reference experiments. Polyhedral grammar construction and subsequent browser
growth are still deliberately labeled as structural surrogates rather than a
molecular-dynamics trajectory.

Serve the repository root and open `/apps/iqc-growth-live/`.
