# Real-coordinate ice-family admission and geometric component test

14 September 2026. This is a first-layer geometric result, not a GCTS growth result.

## Dataset and separation

We acquired all eight 400-frame training / 100-frame validation files for ice Ih,
II, VI and VIII from the [authors' repository](https://github.com/venkatkapil24/fine-tuning-MLPs-ice-polymorphs),
pinned at `c9a4bb534b35bfc8f467d7388f3056325bd2dd4e`. The associated paper is
[Kaur et al., DOI 10.1039/D4FD00107A](https://doi.org/10.1039/D4FD00107A).
Nested smaller training files were not pooled. The corpus contains 2,000 frames,
552,000 atom instances, and no exact source-ordered geometry duplicates.
An independent text parser checked every exported atom, cell, species and source hash.

The learner receives only opaque IDs, shuffled atom positions, element labels,
periodic cells and PBC. It does not receive forces, energies, stress, phase or
formation history. Grouping uses distances only; composition is evaluated afterwards.

The author's validation split is **not an independent-trajectory holdout**.
Absence of exact duplicates does not establish absence of temporal correlation,
permutation-equivalent duplicates or leakage from shared trajectories. File-level
temperature, imposed pressure and trajectory identifiers are missing. The paper's
dataset-sampling methods explicitly state NPT at 100 K / 1 bar, providing
paper-level evidence for a shared sampling protocol, not merely evaluation
conditions. File-level provenance and trajectory independence still need checking
before admission as a verified same-condition ensemble. The released VIII frames
contain 64 molecules; reconciling released-file details with the manuscript is
part of that audit.

## Frozen geometric rule

A prespecified 200-frame pilot used the first 25 frames per phase and split.
We then ran the unchanged component procedure on the complete corpus, fitting
its distance scale and threshold afresh on all 1,600 training frames only.
The median nearest-neighbor distance defines a scale. The largest gap in training
pair distances below 2.5 times that scale defines a threshold: **1.256587 Å**,
between **1.094335 and 1.418840 Å**. Periodic pairs closer than that threshold form
an undirected graph; its connected components are the proposed clusters.
No O–H cutoff, molecular formula, valence or coordination count is prescribed.

| Phase | Train / validation frames | Train components | Validation components | OHH composition after grouping |
| --- | --- | --- | --- | --- |
| Ih | 400 / 100 | 51,200 | 12,800 | 100% |
| II | 400 / 100 | 38,400 | 9,600 | 100% |
| VI | 400 / 100 | 32,000 | 8,000 | 100% |
| VIII | 400 / 100 | 25,600 | 6,400 | 100% |

An independent verifier uses explicit periodic images, a KD-tree and union-find,
rather than ASE's minimum-image distance matrix and SciPy's graph components.
It reproduces all 184,000 components at the frozen threshold. This checks the
component partition, not independent optimality of the threshold selection.

## What remains unsolved

These disjoint components cover atom identities, not interstitial space or a
connected weighted tiling. They do not specify relative molecular orientations
or distinguish the four crystal arrangements. No anchors, t-values or m-values
for overlapping larger motifs have been learned in this experiment. There is no
tree-search reconstruction, blind growth, comparative speedup or condition-matched
generalization claim here. The distance-gap proposal is restricted, not a general
solution to motif discovery.

The next experiment must build overlapping multi-component motifs, fit their
geometric tolerance on training data, and test t-sums and m-agreement on supplied
configurations before the reference tree-search test. Failure must remain visible;
passing molecular decomposition is not a substitute for that test.

## Reproduction

Python dependencies: NumPy, ASE and SciPy. Run in a fresh output directory:

```
python ice-dft-corpus.py ice-dft-data
python verify-ice-dft-corpus.py ice-dft-data ice-dft-data/verification.json
python ice-geometric-components.py ice-dft-data/coordinates.json ice-dft-data/provenance.json ice-dft-data/components.json
python verify-ice-components.py ice-dft-data ice-dft-data/component-verification.json
```

The repository license was not identified during admission; source coordinates
are therefore linked, not republished. Published evidence contains aggregate
checks and executable procedures, not the raw coordinate files.
