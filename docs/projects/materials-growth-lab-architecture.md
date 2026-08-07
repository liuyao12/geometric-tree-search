# Materials Growth Lab: architecture and realism audit

## Scientific contract

The lab is a structural continuation experiment, not molecular dynamics. Its
input is one finite, element-labelled point set (optionally with a periodic
cell); its output is an explicit covering assembled from cluster environments
observed in that input. The growth engine does not integrate forces, conserve
energy, predict kinetics, or replace atomistic dynamics outside the learned
structural distribution. A useful result must therefore report reconstruction
fidelity, held-out overlap consistency, growth validity, and search work—not
only the number of displayed atoms.

The current pipeline is:

1. Parse and validate Cartesian positions, species, cell, periodicity,
   occupancy, format, and provenance.
2. Compute element-resolved radial and angular local descriptors with a bounded
   metric neighborhood and general-cell minimum images.
3. Cluster every atom-centred environment by deterministic k-medoids; the
   assignments cover the complete known configuration and medoids are the
   displayed cluster symbols.
4. Register overlapping occurrences as relative SE(3) transforms and
   deduplicate them into a finite directed attachment grammar.
5. Fit a bounded, cluster-local GCTS section whose directional ports encode
   observed connections and transported shared-support consistency. This is a
   geometric marking, not a physical potential.
6. Seed one learned occurrence and branch over transported grammar rules.
   Species-aware merging, hard-core exclusion, confinement, shared support,
   and the learned marking rank or prune candidate coverings.
7. Compare live RDF and coordination evidence with the known input and report
   an emergent structural classification only when confidence is adequate.

## Current implementation

GitHub Pages serves a browser-only ES module application. Import and learning
are local and reproducible; there is no server receiving a structure. Supported
formats are CIF, POSCAR/CONTCAR/VASP, XYZ/extXYZ, and the documented JSON atom
schema. CIF atom sites are expanded with algebraic crystallographic symmetry
operations. General triclinic cells and independent periodic axes are retained.

The browser rejects invalid coordinates, singular periodic cells, duplicate
sites closer than 0.1 Å, files over 8 MB, and configurations over 1,200 atoms.
It reports composition, atom count, periodic axes, median nearest-neighbour
distance, cell volume, and validation warnings. Partial occupancy is not
silently converted into a fully occupied configuration.

The learned-section trainer uses one full initial audit followed by incremental
incident-overlap losses. It no longer scans the complete overlap graph after
every training sample. Live RDF, coordination, and order inference use a
contiguous central window of at most 256 atoms so visualization cost does not
grow quadratically without bound.

## Measured end-to-end fixture

The repository includes a 64-atom, 2×2×2 NaCl conventional-cell extXYZ fixture.
The current deterministic browser run parses 32 Na and 32 Cl atoms at a median
nearest-neighbour distance of 2.82 Å, recovers two zero-spread coordination-six
environment clusters, learns 112 retained SE(3) rules from 1,344 directed
overlap observations, and reaches 162 explicit atoms after about three seconds
at the 60-event/s UI setting. In that run, learned marking reuse resolves 30%
of 207 tree decisions. These numbers are a regression fixture, not a claim of
speedup over molecular dynamics.

## Known gaps exposed by that fixture

- Symmetric environments admit several equally valid local frames. The current
  frame choice consequently proliferates equivalent NaCl rules. The next
  engine milestone is quotienting transforms by each cluster's learned point
  stabilizer and reporting raw versus symmetry-reduced grammar size.
- A finite growing crystallite has a large under-coordinated surface, whereas a
  periodic reference does not. RDF/coordination-only prototype matching is
  consequently conservative. Reliable classification needs bulk/interior
  selection, a structure factor or bond-order invariants, and independent
  crystallographic verification before assigning a space group.
- CIF disorder assemblies, magnetic symmetry, modulated/superspace structures,
  and trajectory frames are not resolved. Partial occupancy is only reported.
- Descriptor, validation, and overlap graph construction remain O(N²) in the
  learning-window size. A thousand atoms is an upper browser guardrail, not a
  performance promise.
- The current search is a geometric covering model. There is no relaxation or
  energy model after placement, and no uncertainty calibration for extrapolated
  regions.

## Production backend boundary

Small single configurations should continue to parse locally for privacy and
fast iteration. A production service should add four separable components:

1. **Ingestion workers:** streamed CIF/trajectory parsing, disorder policies,
   unit normalization, provenance hashes, and adapters for Materials Project,
   NOMAD, COD, OQMD, or user object storage. Database identifiers must resolve
   server-side or through an explicitly user-provided API token; the static page
   should not embed credentials.
2. **Scientific workers:** cell-aware spatial neighbour lists, descriptor and
   clustering jobs, symmetry/stabilizer discovery, held-out splits by spatial
   region or trajectory frame, and versioned grammar/marking artifacts.
3. **Search workers:** resumable deterministic jobs with node/time/memory
   budgets, checkpoints, complete event traces, policy ablations, and compact
   streamed geometry updates rather than millions of browser objects.
4. **Artifact API:** immutable input, model, run, metric, and provenance records
   whose schemas are versioned. The UI should consume this API without changing
   the scientific engine.

The next meaningful benchmark is not “render one million atoms.” It is to train
on spatially separated windows from real crystal, quasicrystal approximant, and
amorphous datasets; reconstruct held-out regions; and compare geometry-only,
direct-rule, and GCTS-marked search on fidelity, invalid-placement rate, nodes,
wall time, memory, and marking reuse. Only after that ablation should hierarchical
clusters-of-clusters be judged by extension rate and error accumulation.
