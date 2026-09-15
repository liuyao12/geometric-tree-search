# Portable geometric markings: a common value rather than a target-local ID

The learned catalog now has an intrinsic export: 16 base motifs with their
learned t-values and scalar markings, and 3,876 pair variants decorated with
geometric endpoint markings. Motif values contain relative anchor coordinates,
opaque connector labels and displacement vectors—not configuration IDs, atom
IDs or target-state indices. Provenance hashes are separate from motif values.

This closes a representation gap, not the entire growth pipeline. The existing
search experiments still use the earlier fixed-target compilation. The portable
cloud representation has not yet been integrated into that search or validated
on an independent ice or boron configuration.

## What the marking means

At a motif endpoint, m is a colored set of displacement vectors describing the
learned neighboring connector arrangement. Translating a placement moves its
anchor; a proper rotation rotates every vector in its marking. Comparisons of
overlapping assignments do **not** fit an additional independent rotation, which
would erase the relative-orientation constraint. Vector order is irrelevant;
correspondence must preserve the opaque labels learned in the existing model.
No physical potentials, chemical coordination formulas or history labels are
introduced.

To accommodate positional error, an assigned cloud represents the set of clouds
within a specified radius under a color-preserving bijection. Several assignments
agree only if their sets have a **single common cloud value**. The implementation
checks such a value against every assignment. It does not replace agreement by
a chain of nearby values, or by independent pairwise-overlap checks.

The anchor-registration tolerance remains 0.03 Å. The displacement-marking
radius is 0.06 Å: subtracting two independently registered positions can add
their error bounds. This is an explicit uncertainty enlargement, not a claim
that the portable model has exactly the same solution set as the earlier scalar
encoding. Distances are numerically checked with a 1e-10 Å membership guard;
the implementation is not an exact-real geometric certificate. Integer t-values
and the base scalar m-values are retained unchanged.

## Checks on the recorded training decompositions

| Input | Endpoint assignments | Common-value groups | Values found without target-cloud input |
|---|---:|---:|---:|
| β-B106 | 16,624 | 4,050 | 4,050 |
| τ-B106 | 25,708 | 6,156 | 6,156 |

These are three training records per input, including periodic copies. Counts
are not independent material samples. The other four structures have no selected
pair-only junction-to-junction edges, so this particular check is vacuous for
them; their 16-type base catalog is exported and checked, not newly reconstructed.

All 42,332 endpoint assignments contain their supplied training-neighborhood
witness. The maximum observed marking residual is 0.038502484 Å; the maximum
anchor-registration residual is 0.023361242 Å. All 10,206 common-value groups
also pass after a proper rotation.

Separately, a consensus proposer aligns assignments by color-preserving
correspondences, tries their mean and the assigned clouds, and verifies each
proposed value against all assignments. It finds a valid value for every tested
group **without receiving the original neighborhood as the answer**. Placement
poses still come from known-coordinate registrations; this is not blind growth.

Two hundred randomized small-cloud cases agree with independent exhaustive
permutation enumeration, including rotated controls. Adversarial tests reject
unallowed reflections and implicit extra rotation, demonstrate that pairwise
intersection can fail to give a common value, and include a feasible case that
the proposer misses. Therefore a failed proposal returns unknown, never a
sound dead-end or pruning certificate. The proposer is deliberately not presented
as a complete intersection solver.

## What remains before use in growth

1. Specify where the learned cloud decoration applies in a new configuration.
   The base catalog is a reference, not permission to bypass markings by selecting
   undecorated pair variants.
2. Generate registered candidates without reusing the supplied target's local
   state tables. Account explicitly for continuous rotations and positional
   uncertainty; an unexhausted sampled pool cannot establish degree zero or one.
3. Maintain common-value constraints, dependencies and exact rollback through
   the reference frontier graph. Only a justified contradiction may prune;
   failure of the current witness proposer must trigger refinement or stay unknown.
4. Recheck full t coverage and marking witnesses on completed reconstructions,
   then compare with the same unmarked model, candidate universe and budget.
5. Test frozen, reusable motif libraries on other family configurations and on
   verified condition-matched ice samples. Neither cohort independence nor
   same-condition provenance is established by these boron checks.

No new reconstruction, speedup, physical validity or independent generalization
is claimed in this update. The concrete advance is a checked, rotation-covariant
marking value that can be transported independently of target-state numbering.

## Reproduction

```
python export-portable-junctions.py INPUT LEARNED JOINED PORTABLE
python test-portable-cloud-markings.py
python verify-portable-junctions.py INPUT LEARNED ALTERNATIVES JUNCTIONS JOINED PORTABLE CHECK
```

Python requires NumPy. The export output must be a new path. The check artifact
records input/export identities and source hashes. Raw coordinate-derived
libraries are not included in this publication update; obtaining the underlying
data and rebuilding the earlier artifacts is still required for full reproduction.
