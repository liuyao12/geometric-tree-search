# From junction types to the geometry of their connection

The new representation learns which **joint arrangements of two neighboring
junctions** occur in the training decompositions. A single proper rotation must
fit both neighborhoods together. Independently fitting the two junctions does
not establish this: their relative twist can be different.

## Family and training scope

The dictionary and original t/m values use all six acquired boron coordinate
models. Junction learning uses the six original decompositions and twelve
generated alternative records. Only four of those alternatives are genuinely
different decompositions; periodic repetitions and duplicate records are not
independent observations. These are not held-out materials or a verified
same-temperature/pressure ensemble. No energies, forces, chemical coordination
rules or formation histories enter the learner.

## Representation

The previous junction library describes connector stars at points that have no
incident larger face motif. First, a class-only learner records 3,784 directed
relations between neighboring star classes, indexed by the connecting pair type.
Reversing a pair is admitted only when its two endpoint t/m decorations agree.

The next learner places both endpoint stars in the first root's frame. Its
distinguished vector connects the two roots. Each arm carries its existing pair
type and endpoint t/m decorations, plus a side label distinguishing the two roots.
Arbitrary arm numbering is not a matching feature: correspondence is enumerated
within those labels. The second star is translated by the connecting vector, and
one proper rotation fits the combined geometry, with maximum residual 0.03 Å.
Mirrors are not silently treated as rotations.

Training yields 3,876 joint templates. Target states can have multiple witnessed
junction-class assignments; a joint fit from any admitted class pair suffices.
Witnesses need not agree on a single global latent frame or class assignment.
Approximate fitting is not a complete continuous-rotation feasibility oracle:
failure of the fitting procedure is a learned rejection, not an impossibility
certificate. No transitive closure of approximate geometric equivalence is used.

| Input | Class-only admissible state pairs | Joint-geometry admissible pairs | Additional rejected combinations |
|---|---:|---:|---:|
| β-B106 | 49,464 | 47,025 | 2,439 |
| τ-B106 | 18,792 | 18,369 | 423 |

The other four inputs have no edges joining two pair-only junctions; this layer
does not change their models. Fewer combinations alone do not demonstrate faster
search or better material reconstruction.

The recorded accepted fits include just 54 β-B106 and 207 τ-B106 combinations
whose joint template also has a source in another configuration. These are
template-mediated geometric witnesses, not an independent holdout test or a
complete census of all possible cross-configuration matches. Each source and
target is fitted to its template within 0.03 Å; a direct source-to-target fit
within that same tolerance is not asserted. Most recorded joint arrangements
remain configuration-specific. This limits the present evidence for a reusable
family-wide connection library and motivates broader sample coverage.

## Ordinary scalar marking realization

Each local junction state labels an added scalar m-channel at its root point.
A base pair placement has a marked variant for each admitted endpoint-state
combination. The joint-geometry restriction removes variants with unobserved
joint arrangements. The remaining variants use the original exact integer t
contributions and scalar marking agreement; the kernel needs no new geometric
legality primitive. β-B106 has 48,348 explicit variants; τ-B106 has 21,663.

These scalar state labels are compiled for each fixed target. They are not yet
a portable marking assigned once to a geometric motif and transported to new
positions. A next requirement is a shared, rotation-covariant representation of
the endpoint neighborhoods, rather than target-local state indices. The present
compiler establishes a finite GCTS encoding, not that stronger learned-growth
capability.

The search keeps these label domains implicit and propagates their binary
compatibility through the existing frontier graph. Both the selected and absent
states of a shared candidate participate in propagation. Domains are rebuilt
after rollback. Global dead ends, degree-one moves and earliest-generation
branching are retained; the declared required-connection preference only breaks
generation ties. The full observed base pool is retained before learned filtering.
All required points are active roots. This is finite reconstruction at supplied
poses, not seed-driven growth or complete enumeration of continuous placements.

## Independent checks

- The independent geometry checker reconstructs 42,332 directed training
  source fits and 65,394 accepted target fits. Maximum checked residual is
  0.02999134561 Å. Counts include periodic and repeated training observations.
- Every retained target state pair belongs to the previous class-only model.
  Every selected training connection remains admitted. This verifies positive
  witnesses and training preservation, not completeness of rejected matches.
- All eighteen training records lift to explicit scalar markings and pass the
  native point-value verifier with exact integer capacity arithmetic.
- One hundred proper-rotation and arm-permutation controls pass. A synthetic
  independent-star twist passes separate-star matching but fails joint matching;
  a chiral reflection also fails proper-rotation matching.
- The shared connection filter passes 150 exhaustive small-model tests covering
  16,832 subsets, 92 restricted solutions, graph consistency, priority and exact
  rollback, plus a 35-state BigInt-domain control.
- Repeating joint-template learning produces identical artifact bytes. One local
  replay takes 7.58 seconds (7.40 user CPU seconds), excluding upstream motif,
  t/m, junction and class-relation training. This is not end-to-end learning cost.

## Search interpretation

No additional reconstruction or speedup was demonstrated. β-B106 remains
unresolved at 100 seconds in both lanes. τ-B106 completes in both lanes, with
5,400 placements covering all 5,724 supplied positions and one connected
positive-support component. The joint lane's 4,266 selected coupled connections
and its explicit scalar marking lift are independently checked.

| Input | Independent junction states | Joint geometry |
|---|---|---|
| β-B106 | Unknown; 19,863 advances, 100.05 s | Unknown; 15,101 advances, 100.04 s |
| τ-B106 | Complete; 5,401 advances, 49.19 s | Complete; 5,401 advances, 53.04 s |

The τ joint run uses 2,560 degree-one moves and 2,840 branch choices, with zero
backtracks; 2,476 choices receive the within-generation required-connection
preference. The valid but incomplete β prefix is not certified extendible.

Search results and independent final-state checks accompany the report. The
100-second / 1,000,000-advance controls use the same bitset implementation and
generation-tie policy, comparing independent junction states with joint-compatible
states. The runner's historical `learned-connections` label identifies the supplied
connection table; its hash identifies whether that table is class-only or joint
geometry. Timings are exploratory single-machine measurements, not statistical
or end-to-end speedup estimates. Short validation and learning-replay work also
ran during part of the experiment.

All restrictions remain learned hypotheses. Preserving training decompositions
does not prove that every valid unseen decomposition survives. In particular,
reconstruction of a known coordinate set must not be described as a prediction
of a new atomic structure. Independent condition-matched family tests and growth
beyond supplied coordinates remain open.

## Reproduction

Run `boron-junction-connections.py` and `verify-junction-connections.py` on the
existing input, learned t/m, alternative-cover and junction artifacts. Then run:

```
python boron-junction-joined.py INPUT LEARNED ALTERNATIVES JUNCTIONS CLASS_CONNECTIONS JOINED
python verify-junction-joined.py INPUT LEARNED ALTERNATIVES JUNCTIONS CLASS_CONNECTIONS JOINED CHECK
python test-junction-joined.py
node test-junction-connection-filter.mjs KERNEL
node boron-junction-connection-search.mjs COMPILED KERNEL SEARCH_FOLDER JUNCTIONS JOINED
python verify-junction-connection-search.py INPUT LEARNED JUNCTIONS JOINED SEARCH_FOLDER KERNEL SEARCH_CHECK
node compile-junction-connections.mjs COMPILED JUNCTIONS ALTERNATIVES KERNEL EXPANDED_FOLDER JOINED SEARCH_FOLDER
```

Python geometry scripts require NumPy. Output paths must be new. Raw coordinate
artifacts are not republished with this update; source provenance and upstream
construction scripts are documented in the earlier boron reports. Check files
bind the local training artifacts and results by SHA-256. Thus the download set
is audit evidence and source code, not a self-contained raw-data reproduction
bundle.
