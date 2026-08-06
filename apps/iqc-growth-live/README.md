# Materials Growth Lab: hundreds to one million atoms

A static GitHub Pages visualization of a multi-element, three-dimensional
materials-GCTS pipeline. It replaces the earlier IQC-only presentation while
keeping its richer live search, RDF, and coordination interactions. It starts
from one finite configuration with 216
element-labelled atomic positions, then illustrates:

- element-aware discovery of local-environment clusters;
- reduction to tetrahedral, icosahedral, and corona-like polyhedral symbols;
- finite marked interfaces and compatible-overlap rules;
- one continuous search that reconstructs the 216-atom input and naturally
  continues through its exposed frontier. The browser materializes a bounded
  2,160-atom sample while the hierarchy counter addresses a 1,048,576-atom
  target, without copying the starting window as a block.

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

Each coordination bin is interactive. Selecting a value emphasizes every
matching center in the currently available comparison sample, retains the union
of their actual first-shell neighbors, and draws every unique center-neighbor
segment. Shared neighbors remain single atoms, while their connections to
different centers remain visible. During reconstruction the highlighted shells
are recomputed after every accepted site, so the view works before the 216-site
window is complete. The same bin or the compact clear control restores the
unfiltered view.

The live order panel classifies the current geometry rather than echoing the
selected scenario. Once at least 32 reconstructed atoms are available, it
compares normalized RDF and coordination distributions against every prototype
in the small built-in library and reports the best structural class, prototype,
symmetry assignment, and a sample-size-adjusted match score. For crystals this
includes the candidate space group; for the IQC prototype it reports
icosahedral point symmetry instead of inventing an ordinary 3D space group.
After continuation begins, the readout keeps auditing the reconstructed
216-atom core so that adding a differently shaped outer shell does not create a
finite-window RDF artifact; frontier-window classification is a separate future
test.

This is deliberately a provisional prototype classifier, not a proof of
symmetry. A publishable evaluator should add translation closure or `spglib`
for crystals, reciprocal-module and diffraction tests for quasicrystals, and
structure-factor plus local-motif tests for amorphous systems. Prototype labels
and space groups are never supplied to the growth search.

The million-atom number is an implicitly represented target, not a claim that
the browser has evaluated one million force-bearing MD atoms. Establishing MD
replacement requires held-out million-atom configurations, multiscale ensemble
statistics, force and relaxation audits, and complete cost accounting.

Serve the repository root and open `/apps/iqc-growth-live/`.
