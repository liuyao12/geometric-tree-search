# GCTS + RL renewal

Fresh research beginning October 8, 2026. The turtle learner imports only the
vertices and angle units of the article. It starts with no marking, zero policy
weights, no saved model, no known tiling, and no supplied substitution. Historical
experiments elsewhere in the repository are comparison context only.

The report is at [the existing GitHub Pages destination](https://liuyao12.github.io/geometric-tree-search/docs/research/gcts-rl-renewal/).

Run a cold iteration and the semantic conformance checks:

```sh
python3 research/gcts-rl-renewal/run.py
python3 -m unittest discover -s research/gcts-rl-renewal -p test_research.py -v
python3 research/gcts-rl-renewal/audit_geometry.py
```

The runner is standard-library only, with Python 3.10 or newer recommended.
Each run recomputes the complete pair catalog, verifies failure certificates,
synthesizes a marking, trains policies, mines inspectable sequences from its own
searched patches, evaluates on disjoint seeds, and runs two limited inflation
controls. Checkpoints are written after completed stages. Training and solver
construction costs are included in the report. Saved JSON is inspection evidence;
the runner never reads it as a starting model or as a tiling witness.

Evaluation uses several fixed pair starts, with identical starts in all lanes.
Policy training and donor search start from one tile; their random seeds are
disjoint. Evaluation pairs may appear as subpatches of donor trajectories, so
this does not claim strict patch-disjoint policy generalization. GCTS uses every
resolved pair label, as required by the shared learning contract.

## Goals and success criteria

1. **Exact unmarked turtle baseline.** Complete candidate incidence; global
   dead ends and forced propagation before generation-first branching; exact
   occupancy, marking comparison, rollback, and independent witness replay.
2. **Geometric failure encoding.** Every negative has a complete replayable
   exhaustion certificate. Learn point-value agreement data from all resolved
   contacts. Give the support and symmetry assumptions of any redundancy claim.
   Extended-support restrictions stay hypotheses until mark-only contacts are
   covered by an additional proof.
3. **RL sequences.** Learn irregular cluster proposals, expose all constituent
   placements, validate them, obey the scheduler during execution, retain every
   base move, and evaluate on disjoint seeds with construction costs reported.
4. **Substitution discovery.** Infer several metatile types from patches, propose
   exact expansion maps, and export rules as lists of base placements. Repeated
   motifs alone do not pass. Check coverage, interfaces, and at least three
   recursion levels before calling a rule an experimental substitution.
5. **Plane construction, if attainable.** An exact substitution needs compatible
   collars and an expanding nested construction or an equivalent coverage proof.
   Finite growth, a visually plausible patch, and a spectral radius alone do not
   pass. Aperiodicity is a further independent assertion.
6. **Penrose over \(\mathbb Z[\zeta_5]\).** Exact rank-four arithmetic first.
   Declare a faithful point model and admissible translations before transferring
   the learner; the physical module is dense, so polygon interiors cannot simply
   be represented by finitely many lattice samples. No supplied arrows or rule
   may enter the discovery lane. Unmarked rhombs also permit periodic tilings;
   finding a Penrose-compatible subsystem is not redundant pruning of all rhomb
   tilings.
7. **Checkable computational proof search.** Embed Wang edge agreement as point
   markings. Establish finite accepting computation certificates for a general
   transition compiler. Next connect a trusted, total proof checker for an
   explicitly chosen recursively axiomatized theory, enumerate proof programs,
   and search accepting rectangles. Turing completeness is expressiveness, not
   a guarantee of deciding every statement or terminating on unprovable inputs.

## Conformance evidence and gaps

The domain is \(A_2=\{(x,y,z)\in\mathbb Z^3:x+y+z=0\}\), with twelve signed
coordinate permutations and integer capacity \(12\). A tile has 28 positive
point values; the only geometric calculation authors those values by an exact
rational polygon membership test. Search does not add polygon intersection
checks. Faithfulness to conventional polygon tilings has not been independently
proved. Distinct orientations remain distinct inventory identities.

`Graph` maintains forward and reverse shared incidence. All positive support
alignments are enumerated. Dependency changes at occupancy and marking-only
points update every incident domain while preserving unaffected domains.
`State.copy` and `Graph.copy` restore all semantic branch data exactly. Interned
placements are immutable, append-only caches; they contain no branch exclusions.
Rules are frozen within a run; a new rule creates a new model and replays seeds.

The tests compare incremental domains with independent enumeration, check
zero-valued obligations, shared fractional candidates, remote marking-only
disagreements including assigned zero, generation precedence, exact snapshots,
symmetry closure, independently checked failure proofs, budget-as-unknown, and
rejected tampered computation certificates. The catalog proof trees use the
independent enumerator at every node; positive witnesses use an independent
integer replay and frontier viability check.

Growth activates newly occupied support, but does not yet activate a fair
exhaustion of all untouched points. Results are consistent finite point patches,
never plane tilings. Sequence proposals have bounded lengths, with base fallback
preserving the complete search universe; hierarchical composition remains open.
Finite inflation controls declare fixed exterior point contributions and a
single-shape integer dilation, so their failures do not rule out a metatile
substitution. Memory is process peak resident memory, not per-lane allocation.

## Soundness boundary for the smallest marking

The complete rooted contact catalog contains every legal pair with shared
positive occupancy. All twelve orientations are closed under composition and
inverse. The marking is scalar under that action and its assigned support is a
subset of the positive occupancy support. Independent checks establish that
every rejected contact belongs to the certified negative set, including all
transformed contacts.

Suppose a complete unmarked point-model tiling had disagreeing marking values.
The two tiles carrying those values share positive occupancy and can be moved
to a catalog representative. Its negative proof tree exhausts every possible
continuation, yet the complete tiling supplies a legal continuation at every
frontier decision, contradicting a dead leaf. Thus every complete unmarked
point-model tiling satisfies the smallest marking. This is a redundancy lemma,
not an existence proof and not a claim that every legal finite prefix survives.

## Next research iteration

Mine spatial connected clusters and their point interfaces, rather than just
chronological sequences. Fit a multi-type grammar with exact coordinate
transforms. Penalize boundary mismatch and uncovered obligations. Search
inflation matrices without providing a known scalar, and try hierarchical
composition; preserve single-tile fallback. Certify exclusions of larger motifs
before adding further marking channels. Transfer to Penrose only after closing
its point-model gap. For logic, compile an actual proof checker before comparing
learned policies with conventional proof enumeration.
