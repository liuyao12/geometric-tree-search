# Boron benchmark addition

User proposed boron on 14 September 2026. Add it as a complementary crystalline
stress-test family, without replacing the amorphous-silicon objective.

## Proposed ladder

Scope expanded by the user: test the boron crystal family, not only one phase.
The first batch is all six coordinate models supplied with An et al. (2016):
alpha-B12, beta-B105, beta-B106, gamma-B28, tau-B105 (210 atoms), and tau-B106
(212 atoms). These are separate configurations, not six established phases.
Source: https://authors.library.caltech.edu/records/dcaev-djw82 .
The repository's 2017 attachment is a Reply, DOI 10.1103/PhysRevLett.118.089602.
A separate Erratum, DOI 10.1103/PhysRevLett.118.159902, withdraws the original
ground-state assignment and reports ten tau-B106 occupancy variants. The
original energy calculations mixed pseudopotentials; this dataset must not be
labelled a uniform computational-protocol ensemble. See BORON-PROVENANCE.md and
the versioned provenance register. The ten correction variants are pending
coordinate acquisition, not ten additional tested or necessarily distinct phases.

The wider acquisition queue includes alpha-tetragonal, beta-tetragonal,
delta-orthorhombic/B52, reported pseudo-cubic B52, and the high-pressure alpha-Ga
type. Track reported aliases, disorder, impurities and experimental versus
predicted status separately. “All” means a documented, versioned corpus, not an
unsupported claim to exhaust every hypothetical polymorph. No family may vanish
from the results table just because coordinate acquisition or a test fails.

Additional acquisition references (not yet validated coordinate fixtures):
https://arxiv.org/abs/1602.01796 (alpha-tetragonal geometric frustration, 2016);
https://doi.org/10.1016/0022-5088(79)90067-5 (tetragonal structure);
https://arxiv.org/abs/1302.4236 (reported pseudo-cubic B52);
https://arxiv.org/abs/1903.02400 (delta-orthorhombic transition);
https://epub.uni-bayreuth.de/id/eprint/3335/ (high-pressure structure research).

- Alpha-rhombohedral B12: simplest structural control. Test recovery of recurring
  icosahedral geometry and connections between units.
- Gamma-B28: mixed-motif test. Its published 28-atom orthorhombic cell
  contains B12 icosahedra and B2 pairs. Test whether geometry-only discovery
  identifies useful supports without being told either motif beforehand.
- Beta-rhombohedral boron: harder overlap/orientation and occupancy test.
  Distinguish the ideal hR105 model from partially occupied refinements and
  explicit occupancy-resolved configurations. Do not silently turn every CIF
  site into an simultaneously occupied atom.

References checked:
Oganov et al., Nature 457, 863–867 (2009), doi:10.1038/nature07736,
https://www.nature.com/articles/nature07736 (abstract and author copy available).
Widom and Mihalkovic, “Symmetry-broken crystal structure of elemental boron at
low temperature,” author manuscript, 6 November 2007,
https://euler.phys.cmu.edu/widom/pubs/drafts/Boron/prb.pdf .
Use these as structure references, not a claim about today's equilibrium phase
diagram. Verify coordinate provenance and license before importing/publishing.

## Data admission and tests

Acquire an attributed coordinate file, record source/version/hash, cell setting,
units, multiplicity and occupancy. Expand symmetry independently and check atom
counts and duplicate positions. Use supplied periodicity for training-boundary
treatment; do not leak the unit cell or target coordinates into claimed blind
growth. Start with fully specified alpha/gamma coordinates; beta requires a
clearly labeled occupancy-resolved model or explicit configuration family.

Crystallographic occupancy is an ensemble/site statistic, not a GCTS t-weight.
GCTS t-values describe additive coverage by overlapping placed tiles. They must
be inferred and verified from the chosen actual configuration and occurrences.
Never set t equal to crystallographic occupancy to bypass configuration choice.

Discover geometry, correspondences and shared t/m-values without B12/B2 labels,
bond definitions, force fields or prescribed coordination. Compare discovered
motifs to published descriptions only as an evaluation. A disjoint partition
into familiar clusters can cover the atoms while failing to expose a fractional
frontier; inter-cluster connections or other weighted supports must be learned.
Recovering the named clusters alone is not a successful growth model.

Mandatory gates: verified t/m agreement on the full periodic observation;
nondegenerate positive-overlap connectivity; known-position replay with exact
rollback; then coordinate-blind placement with explicit continuous-pose limits.
Compare marked/unmarked search on the same base library and candidate model.
Report failures and distinguish finite exact coverage from physical plausibility.

Input runner: `boron-input-audit.py OUTPUT_DIRECTORY` retrieves the six original
CIFs, checks repository MD5 plus records SHA256, compares ASE expansion against
explicit Gemmi symmetry-operation expansion, checks occupancy and counts, and
checks periodic minimum distances independently. Runtime: Python with ASE,
Gemmi and NumPy. It does not infer marks or run growth.

Next gates must report independently for each model: learned support dictionary,
exact shared t feasibility, m equality-component collapse, held-out rotated
patch coverage, then the same finite-pool marked/unmarked search with rollback.
Growing by copying a unit cell must not be counted as a successful learned test.
