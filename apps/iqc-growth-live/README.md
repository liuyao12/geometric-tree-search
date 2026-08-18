# Materials Growth Lab: off-lattice GCTS covering

A static GitHub Pages visualization of a multi-element, dimension-aware
materials-GCTS pipeline. It begins with element-labelled atomic positions and
runs four visible stages:

1. ingest Cartesian positions in ångströms with no cluster labels;
2. discover a complete irregular cluster cover, including explicit residuals;
3. register finite proper-`SE(3)` connections and train bounded GCTS markings;
4. grow an explicit off-lattice covering and recursively promote clusters of clusters.

The **Evidence Atlas** in the top bar is the materials-science presentation of
the backend research program. It separates complete representation, held-out
continuation, hierarchical compression, and stationary/exponential growth into
distinct claims. Interactive system cards compare NaCl, an ideal icosahedral
quasicrystal, the published Cd–Yb quasicrystal model, and an amorphous control;
the GCTS anatomy view explains covers, oriented ports, markings, search, and
promotion; and the claim ledger keeps proved, measured, and open results visibly
separate. Its numbers are frozen benchmark results, not recomputed browser demos.

The selectable inputs are an exact NaCl rocksalt positive control, a Cu-Zr
metallic-glass surrogate, an Al-Cu-Fe icosahedral-approximant surrogate, a 30°
twisted hBN bilayer, and a silicon BC8-like network. The hBN fixture is two
intrinsically 2D sheets embedded in 3D, not a thin 3D periodic box.
Element-dependent colors and radii are presentation
encodings, not electron densities or physical potentials.

## Environment discovery

The cluster stage exposes the geometry domain explicitly. **Auto** tests
translation closure from the positions, **periodic lattice** applies periodic
translations, **aperiodic module** assumes a discrete but non-periodic
pose/translation atlas (the natural model-set or quasicrystal hypothesis), and
**non-lattice point set / free SE(3)** makes no discrete translation assumption.
The latter two apply no periodic wrapping. This setting changes the displacement geometry used by
descriptors and the complete cover; it is not a preassigned crystal or
quasicrystal label.

For every atom the browser builds a periodic, rotation-invariant descriptor
containing central and neighbor element channels, Gaussian radial functions
through `1.9a`, a first-shell angular histogram, and coordination terms.
Standardized features are grouped by deterministic k-medoids. A bounded
farthest-medoid elbow test chooses the vocabulary size and collapses exactly
regular low-rank inputs early. A separate greedy set-cover pass then chooses
atom-centred occurrences on the periodic quotient and audits their union
against every supplied atom. Any uncovered atom is promoted to an explicit
residual cluster type, so incomplete coverage cannot be hidden by a label
assignment.

Every displayed prototype is an actual medoid point-cloud patch with its
measured, element-labelled first shell. The visualization does not substitute a
fixed catalogue of demonstration polyhedra. Each approximate isometry class has
its own independently rotating canvas card; repeated placements do not create
duplicate cards.

The same stage reports how many symmetry-inequivalent orientations of every
cluster are actually needed to cover the observation. It compares centered,
element-coloured directional neighborhoods in the laboratory frame. Proper
self-symmetries of a cluster therefore collapse automatically: the Na and Cl
octahedra in periodic rocksalt each require one physical pose, even though one
may write many equivalent local frames for an octahedron. Removing periodic
wrapping exposes boundary environment types and their larger finite pose atlas.

The pose atlas is learned before the GCTS marking. Each cluster card reports
its observed symmetry-inequivalent pose count, outgoing connection-port rank,
and an automatic channel recommendation. The browser builds the observed
pose-by-port incidence matrix for that cluster and uses its numerical rank plus
two compatibility/failure fields, capped at twelve. It is deliberately not one
channel per rotation: proper-symmetry-equivalent frames share equivariant
fields, and poses that induce the same connection behavior share the same
basis direction. Chemistry, successful connection, and failure information can
still require more than one field when a cluster has only one physical pose.
The marking stage retains a manual override for controlled ablations.
The clustering controls summarize that dependency explicitly as
`translation support × required pose orbits → pose/port channel basis`, with a
per-cluster audit underneath rather than a single unexplained channel slider.

## Finite rigid overlap grammar

The encoding stage assigns a deterministic local orthonormal frame to every
cluster occurrence. For each pair of overlapping occurrences it computes the
relative rigid transform `(R,t)` in the source cluster's coordinates and
records the shared atomic support. Nearby transforms are clustered in `SE(3)`.

Directed self-rules `Cᵢ→Cᵢ` and cross-rules `Cᵢ→Cⱼ` are both retained. Every
rule stores an arbitrary quaternion, translation, observation frequency, mean
shared support, fit/held-out counts, and a representative observed destination
patch. The catalogue is finite, but rotations are not restricted to lattice
angles. The stage-three inspector reports rule counts, rotation angles,
translation lengths, recurrence, and held-out support.

The encoder keeps two deliberately separate products. Recurring pose classes
form the compressed grammar used for continuation. The complete observed
occurrence-overlap graph is serialized as one-off residual edges used only to
audit reconstruction of the supplied window. The encode-stage **replay graph**
metric reports how many known occurrence centers are reachable from the chosen
seed before search starts. Those residual edges are removed as soon as exact
reconstruction is certified, so they cannot leak into continuation.

## GCTS connection sections and experiment library

The marking stage is separate from both cluster discovery and rule extraction.
Its stage-local controls choose an automatically derived channel rank or a
manual 1, 3, 6, or 12 channels; one-, two-, or three-shell neighborhood reach;
and a site-resolved, connection-port, or whole-cluster action representation.
The automatic rank is derived from the observed incidence of
symmetry-inequivalent pose classes with outgoing port roles. It is not the raw
number of rotations: a symmetry quotient may need one pose while chemistry,
connection, and failure remain distinct channels. These choices rebuild the learned section model
rather than merely relabeling the display. Strong observed overlaps label
compatible directional ports; directions without evidence supply
unsupported/failed-port examples. On shared atoms the loss penalizes
disagreement between the two transported sections.

Sections are expressed in cluster-local frames, so their lobes rotate with each
rigid placement. They are connection markings, not physical or interatomic
potentials. Training starts from deterministic random directional coefficients;
the live fit and held-out curves combine signed-port mismatch with
shared-support disagreement.

A completed fit can be frozen into the browser's marking library. Each entry
retains its material, geometric-support hypothesis, configuration,
coefficients, sample count, and held-out loss. A lattice-trained marking is not
offered under the aperiodic-module or free-`SE(3)` hypotheses. The growth stage
can select any compatible saved marking, the unmarked
colored-action baseline, or the exact-local-oracle diagnostic ceiling. “Train a
different marking” returns to stage three without deleting earlier entries.

## Off-lattice search

Search begins from one observed cluster occurrence. There is no separate
reconstruction and continuation algorithm. Every frontier item is generated by
composing a placed pose with a learned `(R,t)` rule:

`T_child = T_parent · (R_rule, t_rule)`.

The growth-stage hierarchy switch is also operational. With clusters² enabled,
accepted clusters expose their frozen ports and recursively seed the next
frontier. In primitive-only mode the initial cluster frontier is still searched,
but accepted placements cannot spawn another generation. In both modes the
selected marking ranks the same exact rigid candidate geometries; it does not
invent coordinates.

The representative destination patch is transformed into world coordinates.
A cell-list spatial index merges coincident same-species atoms and detects
hard-core or species conflicts without scanning the whole structure. A
candidate must:

- share at least two existing atoms;
- introduce at least one new atom;
- remain inside the selected confinement;
- avoid hard-core and element-identity conflicts;
- pass the transported GCTS section test when the marked policy is active.

During the known-window audit, every proposed site is mapped by species and
minimum-image distance to a stable reference index. Accepted sites are snapped
to that representative, and already represented indices are treated as shared
support rather than fresh atoms. Every simultaneous placement must own a
distinct missing reference index. Reconstruction passes only at exact
one-to-one equality: 216 unique species-labelled sites, 216 explicit atoms,
zero duplicate reference indices, and zero extraneous quotient sites. The
known positions validate or rank learned actions; they never manufacture a
placement. A marking false negative is counted and bypassed during this audit,
which separates grammar reachability from marking quality and autonomous
search quality.

Accepted placements generate new frontier branches. Failed placements are
pruned while other branches remain available. A soft cost for radius, search
depth, and overrepresented angular sectors prevents one frequent attachment
direction from starving the rest of the frontier.

One visual update is a maximal greedy **commuting frontier set**, not one search
move or an arbitrary fixed-size animation batch. Candidates are drawn from the
same frontier snapshot. A placement joins the displayed set only when every
cross-placement site is either safely separated or a coincident atom of the
same species, and every placement retains at least one new site not supplied by
another member. These monotone local checks make all permutations of the
displayed placements admissible. The engine materializes them in a
deterministic order internally, but that order does not select the result.

Red markers are also batched, but only for failures that are invariant under
those permutations: hard-core/species conflict, confinement failure, duplicate
covering, or a failed frozen marking. An under-supported candidate is deferred
because an independent placement could supply its missing overlap; it is not
misreported as a rejection. Thus several independently pruned branches produce
several simultaneous red flashes.

With the marked policy, recurring overlap rules preload bounded section
intervals and can avoid repeated local compatibility evaluation. Selecting the
exact-oracle or colored-action policy restarts the same geometric search without
that section ranking/cache, providing direct ablations.

The audited IQC panel now reports the persistent-symbol promotion gate rather
than treating raw proposal amplification as successful growth. From two
observed exact-control patches (507 and 1,969 atoms), 122 rigid templates form
18 symbolic productions with 165 relative-pose ports. Typed poses survive two
unseen compositions without atom re-clustering, but outward fidelity changes
from 932 correct / 0 false (3.27% shell recall) to 1,340 correct / 2,580 false
(34.18% precision, 1.14% recall). A frozen normalized port marking retains five
symbols and then none. The UI therefore marks mechanical recursion as achieved
and exponential-quality GCTS growth as failed.

## Live validation

The RDF and coordination-number charts compare the known configuration with
the explicit atoms produced by search. Beyond 216 atoms, the live chart uses a
contiguous 216-atom central window. Coordination bins remain interactive and
highlight every matching center, all current neighbors, and their connecting
segments.

The live order panel classifies the generated geometry rather than feeding a
structure label to growth. It compares RDF and coordination evidence against a
small prototype library and reports a provisional crystal, quasicrystal, or
amorphous interpretation. A publishable evaluator still needs `spglib` or
translation closure for crystals, reciprocal-module and diffraction tests for
quasicrystals, and structure-factor plus local-motif tests for glasses.

For a periodic input, a translation-consensus pass searches same-species
displacements for three recurrent independent vectors. During search it draws
the resulting parallelepiped as a candidate unit cell; once the live order
audit calls the grown structure crystalline, the badge changes from candidate
to detected. Quasicrystal and amorphous classifications suppress the cell.

Growth has no preset atom target. The one- and two-minute controls run as many
explicit rigid-overlap decisions as browser performance and the geometric
frontier permit, then pause without discarding state.

## Scientific status

This is now the intended off-lattice construction rather than a cubic-site
animation: arbitrary rigid transforms, cluster-local frames, overlapping
point-cloud patches, spatial conflict checks, a persistent branch frontier,
and transported GCTS markings participate in each placement. It is still a
browser-scale research prototype. Scientific use requires symmetry-quotiented
registration, robust Kabsch/RANSAC alignment, pose relaxation, richer
equivariant fibres, learned negative examples, and held-out DFT/MD evaluation.

The audited IQC card now also reports the first family-blind recursive
similarity-cover benchmark. Pair-distance recurrence discovers the inflation
scale, 21 contracted copies cover all 507 known sites, and a bounded colored
section is fitted on inner/annular examples before it is frozen on the unseen
outer shell. The displayed 4.236x factor is latent hierarchy compression; the
explicit first-level result (713 correct sites at 53.5% precision) is reported
separately and is not presented as exact exponential growth. With every map
and setting frozen, correct proposals grow 829 to 2,747 on the next level
(3.314x). The atom halo loses its precision advantage there, while a finite
scale- and SO(3)-invariant Gram section over agreeing macro maps raises
precision from 49.27% to 55.51% at 4.02% recall.

Relative rotations are proposed from scale-matched local triangle frames. The
same family-blind procedure recovers a 31-site map between two randomly
oriented crystal grains and finds 31 leading nonidentity IQC rotations with the
same 70-site overlap as the identity action. These rotations are an audited
proposal set. They now participate in one greedy self-cover: 47 selected maps,
33 nonidentity, cover all 514 bicrystal atoms, while 52 identity-only maps stop
at 502. The IQC remains completely covered by 21 symmetry-representative maps.
An all-nonidentity 21-map IQC representative is now propagated with every
rotation and translation frozen through 507 -> 1,969 -> 8,603 atoms. Correct
proposals grow 829 -> 2,747 (3.314x); the cross-fitted Gram backoff retains
2,488 correct second-level parents at 37.5% recall. This is verified recursive
subset growth, not complete full-patch generation.

The latest marking is genuinely hierarchical rather than another geometric
halo. Frozen similarity actions form a directed cluster-connection graph; one
message-passing round assigns each source a finite recursive address from its
incoming and outgoing action types. A fine address table accepts 241/243
second-level proposals (99.2% precision), while a coarse backoff accepts
2,304/4,169 (55.3% precision, 34.7% recall). Their union retains 2,374 correct
attachments and reduces false branches from 2,871 to 1,865. All addresses are
trained inside the original 507-atom patch; rotations, translations, and
thresholds remain frozen at the second inflation.

On the experimental Sc-Zn parent holdout, the recursive address is now an
additional search tier rather than a decorative label. The automatic local
atomic section gives 120/159 correct proposals (75.5% precision); intersecting
it with the action address gives a first tier of 70/82 correct (85.4%) and
reduces false branches from 39 to 12. Test-origin actions are excluded from the
address graph. The unsupported address-only forced core transfers no actions
and is not claimed as a rewrite.

An oracle-filtered reachability audit now separates marking error from action
vocabulary error on the ideal IQC. The 21-map minimum cover reaches only 44.0%
of the next patch and a pooled support vocabulary reaches 94.2%. All 386
remaining atoms share the minority learned color. Counting translation votes
within each input color and retaining one map for each of 1,000 observed
supports reaches all 6,634 new atoms: 6,568 in the first wave and 66 in the
second. The maps are selected from the 507-atom input only; the oracle measures
reachability. This proves complete representation, not autonomous selection:
the first wave still contains 12,332 false proposals. Direct phi-squared macro
maps recover none of the residual and remain a negative ablation.

The first autonomous mark is trained on placements inside radius 6 of the
507-atom input, tuned on the disjoint radius 6–9 annulus, and frozen for the
larger frontier. At the same 8,172-expansion budget as validation-selected
vote consensus, learned action marks select 3,631 correct sites instead of
3,416: 215 more correct and 215 fewer false branches, raising precision from
41.8% to 44.4%. This is a causal marking gain at fixed cost, but it retains
only 54.7% of the reachable first wave; autonomous complete emission remains
the next gate.

Four direct cluster-of-actions ablations are now recorded at the same budget.
Pair identities select 3,554 correct sites, smoothed pair reliability 3,492,
scale-invariant geometric pairs 3,446, and a regularized 34-dimensional
continuous cluster section 3,540. The individual action mark remains best at
3,631. The geometric categorical model creates 67,109 states from only 801
inner examples, exposing the sample-complexity problem rather than concealing
it. The next model will retain individual marks and learn only a compact
residual consensus correction.

The sample selector now separates saved benchmark families from
composition-first NOMAD search. Saved families include graphene, aligned and
30-degree hBN, and proton-ordered ice Ih/Ic; choosing a fixture supplies only
its element-labelled coordinates to the learner. The ice path uses a
molecular overlap cover rather than atom-centred shells: one H2O type,
water-dimer connection clusters, and oxygen-ring gap boundaries. The live
strict replay search recovers 216/216 Ih sites in 35 decisions and 192/192 Ic
sites in 30 decisions. The independent Python headless gate records the
water-only ablation and full-cover result in
`scripts/test_materials_gcts_ice_cover.py`. This certifies reconstruction of
the known windows; larger blind ice continuation remains open.

A common recursive-program gate now prevents the crystal and quasicrystal
cards from using incomparable meanings of "action." NaCl, the icosahedral
model set, the Fibonacci-product control, and rotated 30-degree hBN must each
exactly materialize two unseen levels before their symbolic million-site curve
is admitted. All four reach at least one million represented sites in five or
six recursive promotions, with minimum per-action factors from 3.884x to 8x
and flat-cluster action reductions from 33,221x to 176,942x. The shared
selector receives positions and species only and rejects the amorphous
control. A second production gate now compiles NaCl, the Fibonacci product,
the 30-degree hBN pose/address atlas, and the ideal icosahedral section into
the same typed parent/child/address/section contract. Three finite graphs use
the same counter rewrite; the IQC uses a
rank-6 address generator gated by its learned bounded 3D internal section.
All match their two-level certificates and symbolic million-site counts, and
survive tested rigid motions. The planar row distinguishes its
square address envelope from the exact circular atom crop. Geometry discovery
front ends remain specialized and are the next unification target.

Model selection no longer means “try families in order and stop at the first
success.” The planar and three 3D hypotheses are all proposed before a common
fit-plus-description-and-seed-mismatch score is minimized. The Fibonacci
control is the first competing-hypothesis gate: its exact substitution program
scores 0.0192 while an inexact translation quotient scores 1.5607, independent
of proposal order. NaCl, ideal IQC, and 30-degree hBN select their expected
programs with exact seed replay, while the amorphous control produces no
admitted proposal.

The integrated selector now has a perturbation gate. With 0.005 Angstrom
Gaussian coordinate noise, NaCl, the ideal IQC, and the Fibonacci product all
retain the correct production and reconstruct the clean first growth level at
100% position recall and precision. A 30-degree hBN seed with 0.006 Angstrom
noise and 3.5% vacancies retains its planar production and reaches 100%
precision / 99.20% recall on the clean continuation. A noisy 1%-vacancy IQC
now recovers its module origin from repeated antipodal-pair midpoints and
reconstructs the clean first level at 100% precision and recall. Bounded
lift-complexity preflight prevents expensive invalid rank-6 enumeration. More
severe and nonuniform 3D damage remains open.

A 12-case finite-window gate repeats discovery at three sizes per family.
NaCl keeps its primitive 8-atom quotient from 64 to 512 observed atoms; the
ideal IQC keeps phi, window 1.5, and shell fractions 0.5/0.75 from 345 to 919;
Fibonacci keeps `A -> AB, B -> A` from 216 to 1,728; and twisted hBN keeps the
same two-pose atlas from 470 to 1,130 atoms. Every next-window continuation is
exact. This gate fixed a minimum-description bug where the largest NaCl crop
preferred a redundant 2x supercell despite exact primitive-cell evidence.

The end-to-end timing gate reports learning, explicit emission, compact
counting, and exact counting separately. In the recorded Python run, learning
takes 0.34–3.37 seconds and exact two-level emission takes 0.03–0.26 seconds.
Finite production graphs count a million-scale representation exactly in
roughly 10–73 microseconds. The IQC cut-and-project density estimate takes 106
microseconds and differs by 0.084% from an exact 2.49-second enumeration of
2,791,097 sites. These measurements support representation and macro-action
compression only; they are not a claim to beat molecular dynamics or to emit
explicit coordinates sublinearly.

A matched-quality marking ablation now measures actual search work rather than
comparing unlike recall levels. Compiled full-recall sections reduce proposal
work by 56.2x for Fibonacci substitution and 717x for the ideal IQC, eliminating
invalid branches after filtering. On the harder learned-local-section test,
the IQC halo is trained on 507 -> 1,969 and frozen on 1,969 -> 8,603. Reaching
the same 252 correct moves needs 392 checks and 140 failed branches with GCTS,
versus an expected 526 checks and 274 failures under unmarked random ordering:
1.34x proposal and 1.96x backtrack reductions. This is a causal but still
moderate learned-marking gain, not a claim that the local marker solves the
complete IQC frontier.

The first geometry-bearing generic cover grammar is now exercised separately
from the family-specific growth backends. It stores rigid child poses, overlap
identities, and coordinate-bearing gap terminals for each modal
cluster-of-clusters production. Recursive expansion replays all 68 stored NaCl
and all 48 stored IQC prototypes exactly; the amorphous null yields no
production. This is deliberately still a red benchmark: the modal production
currently describes only 33% of NaCl occurrences and 30% of IQC occurrences.
Context-marked alternatives and held-out geometric continuation are required
before this generic grammar can inherit the million-site claim.

The follow-up frozen occurrence split makes that requirement executable rather
than rhetorical. A 2:1 spatial ordering split learns 70 finite NaCl and 59
finite IQC right-hand-side alternatives; these vocabularies contain the true
held-out alternative for 100% and 99.60% of cases. However, both the original
bounded halo and the first child-port section choose exactly the same modal
production as the parent type alone: 90.0% held-out accuracy for NaCl and
88.49% for IQC, with zero marking gain. The negative control is committed as a
red test. It prevents merely storing alternatives from being reported as
GCTS: the next marking must use already-placed connection/overlap context and
beat this frozen modal baseline before an unseen-window claim is allowed.

The acceptance split is now fixed before the encoder refactor. Two recursive
NaCl replications provide 13,824 atoms; the independent IQC level provides
8,603. At hierarchy levels 1--3, a fixed irrational-direction half-space and a
guard equal to the *sum* of all recursive body radii plus the marking halo
leave 785 / 785 NaCl centres at level 3 and 532 / 532 IQC centres at level 2.
The 8,603-site IQC patch leaves no level-three centres under this cumulative
guard, so only two IQC levels are certified and level 3 remains red. At every
certified level, projected separation exceeds twice the raw dependency radius,
so train and held-out local domains cannot share atoms.

The new spatially indexed frozen encoder now performs that transform. It fits
the nearest-neighbour scale, species map, three signature dictionaries,
promoted-color maps, and unknown sentinels on training centres only. Across
the disjoint guard, 100% of held-out centre signatures occur in the frozen
dictionaries across three NaCl and two IQC levels, with no held-out refit. The
original top-four bottleneck retained as little as 24.48% of NaCl and 15.39%
of IQC context. It is now replaced by the smallest train-only prefix of
recurring colors covering 95% of training centres, capped at 64. The learned
budgets are 4/6/16 colors for NaCl and 51/30 for IQC; frozen held-out promotion
coverage is at least 95.29% and 95.59%, respectively. This passes
hierarchy-state transfer, but not yet production selection or continuation.

A causal deepest-certified-level ablation then restricts the marking to the
inward half of the halo—the side representing already-grown material. IQC uses
certified level 2; NaCl uses level 3. With the cumulative guard and improved
colors, every parent type has exactly one right-hand side: 16/16 for NaCl and
30/30 for IQC. Both modal searches therefore have zero decomposition
backtracks, and a marking cannot improve them. The gate remains red. This negative
result moves the causal GCTS question to the correct interface: ranking which
neighboring macro placement to attempt at the frontier, not decomposing a
parent whose full colored geometry is already known.

That live-frontier gate is now implemented on the real regenerative IQC
proposal set. A marker is trained on 507 -> 1,969 atoms and frozen on the
1,969 -> 8,603 frontier. The learned marker, overlap-vote baseline, and 30
within-training-label shuffled refits receive the identical 66,110 candidate
points and stop after the same 120 correct novel sites. Learned incoming GCTS
ordering checks exactly 120 proposals with zero failed branches; overlap votes
check 232 with 112 failures, a 1.93x work reduction. Shuffles require a median
4,608 checks (38.40x learned work), and the best requires 404. The learned
marker beats every shuffle; no held-out label is used in training. This is a
causal role for GCTS at the correct interface, though 120 sites are one forced
frontier macro rather than exponential continuation.

The first temporal-window macro audit correctly rejected a tempting false
positive: its four-site candidates all came from one time window. The successor
is order-independent. It partitions the accumulated exact frontier into eight
guarded spatial domains and runs one generic colored-point cover learner. On
296 off-boundary sites, every level is an exact cover and recurrent supports
grow `3 → 11 → 37`, or `3.67x` then `3.36x`. This certifies three spatial
levels—including clusters of clusters—without lattice metadata, phase labels,
or construction order. Extrapolating the smaller measured factor suggests nine
additional promotions to one million represented sites, but that number is
explicitly unverified until those unseen productions replay.

A sealed spatial grammar test then fits the distance scale, type vocabularies,
and parent-to-child productions on four negative-x sectors (148 atoms) and
replays them on the four positive-x sectors (148 atoms). The frozen `4 / 3 / 1`
type dictionaries and eight productions obtain 100% held-out occurrence, atom,
and production coverage at all three levels, with no held-out geometry used for
fitting. All eight parent types have one RHS in this symmetric fixture, so the
GCTS marking result remains the separate causal frontier-ranking ablation.

The cumulative-guard benchmark is now large enough to test three recursive
levels without reusing raw-atom domains. A new exact meet-in-the-middle 6D
oracle is bit-for-bit equivalent to the original enumerator on reference
patches and produces the converged 155,097-site radius-61.69 IQC in roughly
2.5 seconds. A bounded coordination-plus-angular GCTS color encoder is fit on
28,211 inner atoms. It has 23,919 / 16,587 / 6,953 guarded training centers and
is frozen on 106,162 / 70,458 / 4,260 held-out centers; bounded-color coverage
is 100% at all three levels. A matched-density, three-species amorphous null is
accepted at only 42.6% on level 1 and 24.1% on level 3, so it fails the shared
gate. Exact signature coverage intentionally remains a diagnostic and falls to
zero at higher levels: this result proves transferable bounded GCTS colors,
not exact geometry generation or million-atom continuation.

The first exact-production recognition audit is intentionally red. A frozen
atlas retains every sampled species-labelled child-distance graph for each
bounded parent color, rather than selecting a modal RHS. On 1,024 training and
1,024 held-out parents per level, parent colors are known for 98.7% / 97.9% /
100% of held-out cases. Exact child geometry matches only 67.4% / 0% / 0%.
Level 1 contains as many as five alternatives per parent color; levels 2 and 3
had one sampled training alternative but encounter unseen held-out geometry.
This demonstrates why the transferable color must be augmented by a bounded
incoming-port GCTS marking. Production execution is separately red because
recognizing a distance graph does not recover a proper pose or materialize it.

A first causal incoming-port ablation now separates the already-grown side of
the frontier from the proposed outward production. The marking contains only
the species/type and quantized center distance of smaller-radius neighbors; it
cannot inspect future atoms. Of 2,048 held-out level-1 parents, 285 have a
training-supported `(parent color, incoming marking)`. The learned marking
selects 104 exact outward productions on this matched subset, versus 31 for the
parent-only modal rule and at most 44 across 30 within-parent label-shuffled
refits. The effect is therefore not explained by parent-class frequency, but
13.9% context coverage is too low and exact contexts do not transfer at levels
2–3. This is a positive ablation, not a passed growth benchmark.

The recursive centre-connection path also no longer receives the hidden
inflation factor. A seed-only estimator builds the recurrent pair-distance
spectrum and scores every candidate ratio by closure at both `s` and `s²`.
This rejects a stronger one-level accidental ratio near 1.902. A generic set
of low-degree integer-polynomial roots is admitted under the same score, and
the 507-atom IQC selects `1.618033988749895`, with 51.2% and 55.8% weighted
distance closure. The existing frozen connection marking then produces the
same held-out result using this inferred scale.

A stricter sealed protocol reveals that the earlier connection table still
learned labels from the first inflation. The replacement trains only on 93
inner parents whose inferred-scale images remain inside the 507-atom seed.
Both the 1,969-atom state and 8,603-atom target are evaluation-only. Applied at
the outer frontier, the frozen table proposes 3,404 novel sites, 500 correct:
14.7% precision and 7.5% held-out recall. Vote thresholds do not recover a
high-quality operating point, and a naive radial-coordination distance to
training clusters is anti-informative on the incomplete frontier. The sealed
generic gate is therefore red; the next marking must use overlap-port
incidence among already placed clusters.

The first symmetry-quotiented motif-centre port atlas now supplies a positive
answer at limited recall. A port stores the two frozen local motif types and
their exact separation, then divides that separation by the current recursive
level scale before lookup. It is invariant to translation, arbitrary rotation,
atom order, and inflation level. Proposals outside the finite seed are censored
rather than treated as negative; 73 of 544 observable seed-only port classes
are accepted. On the unseen frontier they generate 860 distinct sites; all 860
occur in the target, for 100% precision and 12.96% recall. The otherwise
identical 0.5-wide separation-bin marking produces 3,404 sites at 14.69%
precision, so the metric port improves precision 6.81x. The next target is to
increase port coverage without sacrificing this exactness, then iterate the
accepted sites as an actual growth state.

That iteration is now explicit. The 860 predicted species-labelled atoms are
inserted using only the atlas's train-only color votes, growing the state from
1,969 to 2,829 atoms with 100% correctness. Retyping and admitting every
train-supported single port produces 13,020 wave-2 sites, all false. The
regenerative gate rejects this exponential error branch: single-port support
is insufficient.

Promoting the action-incidence graph does uncover two genuine overlapping
superclusters: accepted sites are connected when their supporting port actions
share a parent or source motif centre. The exact 860-site patch has two large
components of 500 and 240 sites plus 32 smaller components. They are
conflict-free parallel macro actions. They are different isometry classes, and
scaling either component does not generate its successor. This is meaningful
clusters-of-clusters action compression, not yet an exponential production.

A higher-order section now learns 271 unordered pairs of metric ports that
co-support the same observed endpoint inside the seed. Requiring a learned
pair—not merely one valid port—is applied within a 6.155 Å frontier halo
derived from the longest train-supported normalized port. It gives three
held-out waves of `260 → 192 → 60` sites. All 512 inserted positions and
predicted species are exact, and the state grows from 1,969 to 2,481 without
oracle insertion before stalling. This is the first regenerative generic
GCTS trajectory. It is not exponential: wave sizes do not amplify, so the
long-term gate remains red.

There is now also a stricter exponential-style scale test. The smallest
pair-supported endpoint inside the seed has 11 underlying port actions. The
frozen consensus rule requires `ceil(11 / scale^level)` actions at later
levels—seven at the first unseen inflation and five at the second. It accepts
80/80 exact sites on the 1,969 → 8,603 frontier and 480/480 exact sites on the
8,603 → 37,073 frontier: a measured 6x batch amplification across two unseen
scales. No held-out geometry chooses the thresholds. This is a genuine
clusters-of-clusters exponential-style certificate, but it is sparse (1.21%
and 1.69% novel recall) and is not yet a generic million-site rollout.

A cross-family selector now prevents that result from being mistaken for a
universal marking. A fixed-anchor similarity section learned on the 729-site
3-D Fibonacci product emits 2,090 and then 7,222 exact novel sites at two
unseen scales. The IQC port-pair section and this anchor section are both
successful. A shared seed-only recurrence test selects the anchor hypothesis
when at least 25% of seed sites have an exact similarity image; otherwise it
selects the overlap section. It chooses the IQC pair section from 61/507 anchor
support and the Fibonacci anchor from 216/729, without phase labels or held-out
targets, then passes both unseen scales for both controls.

The same competition includes the translation-quotient hypothesis and selects
it for the NaCl crystal from its colored point geometry. It emits 1,728 and
13,824 exact sites over two unseen levels. Thus crystal, icosahedral, and
substitution-quasiperiodic controls now enter one family-blind hypothesis
interface. Their selected markings are compiled to the shared interpreter
described next.

That executor caveat is now narrowed. Translation cover, fixed-anchor
similarity, and overlap-port consensus compile to three opcodes in one geometry
VM. Every opcode consumes a colored point cloud and emits a set of new colored
sites. Through that same interpreter, NaCl emits 1,512 and 12,096 exact novel
sites; IQC emits 80 and 1,254; Fibonacci emits 2,090 and 7,222. All six outputs
have 100% position/species precision. The IQC opcode evaluates chemical labels
with the learned bounded internal section; reusing the old port-majority color
would have mislabeled 20/80 and 480/480 sites and is explicitly rejected.

The remaining opcode distinction is now data, not control flow. Each selected
instruction compiles to a `PortCoverGraph` node with the same fields: binding
domain, affine output, coincident-proposal grouping, connection section, color
section, and child-node references. Translation binds integer cover cells,
anchor similarity binds one typed site, and overlap consensus binds two motif
centres. All three graphs have a self-edge representing the recursive
cluster-of-clusters rewrite. One relational evaluator reproduces the same six
exact colored-site batches without inspecting an opcode or material family.

The graph is now tested causally rather than only on complete held-out states.
Starting from the 1,969-site IQC cloud, each emitted colored site is inserted
and becomes the sole input to the next graph evaluation. Four level-1 waves
add `260, 192, 120, 80`; two level-2 waves add `792, 204`; three level-3 waves
add `360, 240, 120`. All 2,368 inserted sites have exact positions and species,
and the partial cloud reaches 4,337 atoms without any held-out atom or oracle
color entering state. Totals by recursive level are `652 → 996 → 720`, so this
passes self-fed multiscale regeneration but not exponential amplification.

A complementary gap node now gives the learned level set a causal accept/reject
role. A single metric port proposes a missing site; the IQC internal section accepts
or rejects that connection before insertion and supplies its chemical color.
It rejects 420 invalid endpoints and self-feeds six recursive levels with exact
totals `3,304 → 1,332 → 300 → 2,520 → 780 → 120`. Across 20 nonempty waves it
adds 8,356 / 8,356 correct colored sites, growing 1,969 → 10,325. The hidden
model is used only by the independent scorer. The level-4 resurgence does not
persist through levels 5–6, so exponential growth remains explicitly false.
This is a section-assisted ceiling: the global superspace coordinate is learned
from the seed, but it is stronger than the intended bounded local cluster halo.
Replacing it with finite local marking data remains a genericity requirement.

The companion regenerative scaling audit makes the remaining gap quantitative.
Extending the same frozen policy to 16 waves adds
`12, 104, 12, 4, 36, 24, 24, 12, 8, 24, 24, 24, 24, 12, 12, 12` sites for
368/368 correct continuation sites, and the available frontier grows while
proposals are consumed. The largest forced macro is 104 sites. But four-wave
supermacros shrink `132 → 96 → 80 → 60`; geometric mean wave growth is 1.0
and log cumulative sites versus wave has R² 0.605. The exponential gate
explicitly fails. The next algorithmic target is to promote recurrent
*frontier wave states* whose support grows, not simply bundle more exact local
waves.

That target is now executable. A material-blind frontier-state compiler builds
an adaptive nearest-neighbour graph independently on every exact wave,
enumerates connected colored subgraphs through five sites, and canonicalizes
them modulo translation, positive scale, and proper 3-D rotation. Five
recurring normalized types cover 336 of the 368 emitted sites; the remaining
32 sites are explicit residual terminals, so the cover is complete. Ninety-two
occurrences have independently fitted finite proper poses. This is a genuine
structural promotion beyond the old count-only `132 -> 96 -> 80 -> 60` wave
bundles.

The stricter exponential gate remains red for a newly precise reason. One
two-site state repeats the golden-ratio scale over waves 7--9, but its unique
support shrinks `24 -> 12 -> 8`. It also has a continuous rotational
stabilizer, so it cannot define a finite oriented GCTS port state. The proper
three-site state recurring over waves 14--16 has constant 12-site support and
unequal learned scale ratios. A synthetic expanding triangle control learns
`3 -> 6 -> 12` support with scale `1 -> 2 -> 4` and passes, while a colored
chiral reflection and amorphous clouds stay separate/red. The remaining task
is therefore a transition grammar between frontier-state types, not another
larger fixed window of exact local waves.

That transition grammar and its executor now exist. For every consecutive
wave, atom-disjoint finite proper state occurrences are fitted, target states
are assigned to their nearest compatible parent, and the complete child set is
expressed in the parent frame. Canonicalization jointly quotients the parent
proper symmetry and every child symmetry while retaining learned relative
scale, rotation, translation, chemistry, and child multiplicity. A rule is
stationary only if the identical multi-child production has at least two
independent parents on each of two consecutive transitions.

On the real IQC trace, three finite proper state types yield 30 packed
occurrences and eight complete parent-production observations. They form five
exact rules. Four rules are genuine heterogeneous multi-child productions,
with as many as three children of three distinct types; this fixes the earlier
compiler artifact that split a mixed right-hand side into unrelated unary
rules. None of the five rules appears on multiple transitions, however, and
none saves description length. The target-free executor is therefore available
but has no stationary IQC rule to run. Its generic expanding control does: two
colored triangle parents learn the same two-child rule twice, replay the next
two explicit waves exactly, and reach 1,572,864 represented sites after 18
symbolic actions. A second synthetic control exactly replays a mixed two-type
right-hand side; it is intentionally excluded from the scalar symbolic counter
because heterogeneous recurrence needs a vector substitution matrix. This
proves the machinery can execute both homogeneous and heterogeneous
cluster-of-clusters rules without granting an exponential claim to the real
IQC trace.

The next correction makes child ownership global across the entire typed
frontier. A next-wave occurrence is assigned to exactly one nearest previous
occurrence, rather than being copied once into every possible parent type. On
a sealed two-state algebra/control, the generic learner now recovers the closed
rules `A -> AB` and `B -> A`, including their proper relative poses and common
learned scale 2. The inferred substitution matrix is
`[[1,1],[1,0]]`; its measured Perron growth is 1.6180339887. Two observed
levels replay exactly and the frozen grammar predicts a sealed 48-site fourth
wave exactly. The complete grammar has positive description saving, and 24
symbolic vector actions represent 1,178,508 colored sites. Permuting the
input and applying a generic proper rigid motion preserves the frozen program
digest. This is an executable multi-state exponential capability control, not
a claim that the ideal IQC trace has passed: its five real rules still contain
no closed production system recurring across transitions.

An untuned 24-wave extension identifies the next tree-search failure precisely.
Waves 1--16 remain 368/368 exact. At wave 17 the greedy maximum-score band
contains 60/60 wrong but locally collision-free sites; the immediately adjacent
rank-2 band contains 48/48 exact sites, and ranks 3--4 are also exact. The
score gap is only 0.0001877. Lift bounds 6, 7, and 8 all give the same 8,603-site
oracle crop, so this is not target truncation. Internal recurring-cluster cover
and hard-core checks do not separate the branches. Candidate generation is
therefore sufficient; the open task is a target-free cluster-of-clusters
lookahead marking with rollback across locally legal phason alternatives.

That lookahead now runs on the frozen top-two fork. Expanding each branch once
without target access gives future boundary scores 0.9997197 for greedy rank 1
and 0.9997951 for rank 2. A leaf-consistency-first beam therefore rolls back
the 60-site error and selects the 48/48 exact sibling. Summing immediate and
future scores would still choose incorrectly, so the implementation keeps
search value distinct from the local marking. This is an exploratory recovery
on the diagnosed trace, not yet an independent confirmatory growth gate.

Executing that width-two rule rather than stopping at the attractive example is
decisive: waves 18--24 contain only 40 correct versus 72 false selected sites.
A width-four leaf-score beam recovers waves 17--18, but its held-forward suffix
still contains 36 correct and 68 false sites. The first exact bands remain in
the top four; the scalar leaf score is the failure, not candidate generation.

The replacement tree value asks how many frozen, compatible frontier actions
survive after a provisional branch. This is a target-free option-preservation
measure, not an oracle similarity. Within width four it selects exact ranks
2, 4, and 4 on the three exploratory forks. Frozen before wave 20, it then
selects ranks 2, 3, 1, 4, and 4 and adds 120/120 exact held-forward sites with
four real rollbacks. The full 24-wave trace is 572/572 exact while candidate
supply grows from 63,890 to 67,806. This passes the same-trace temporal search
gate. Spatially disjoint confirmation, a recurring production, and exponential
IQC growth remain open and are reported separately.

The first spatial confirmation is now recorded rather than silently widening
the beam until it works. Training uses only the concentric 507 → 1,969 atom
origin crops. At the disjoint centre `(30, 0, 0)`, width four fails and the
first exact colored score band is rank five, so width five is frozen. A second
centre `(18, 25, 14)` is then used once; its complete radius-14.562 target ball
is disjoint from both the training ball and the first diagnostic ball, and its
different centre norm excludes an origin-fixing rotation between the two
tests. Before the second target is opened, the frozen grammar proposes 5,616
bounded sites, 431 of which later prove color-correct. Nevertheless the five
retained option-preserving branches are all false; the first correct and first
pure-correct bands are both rank seven. Spatial confirmation therefore stays
red. This isolates the next problem to a transferable, target-free branch
value or adaptive breadth rule—not missing candidate geometry.

The next feedback-loop iteration trains one rigid-motion-invariant attachment
marker jointly on the origin and those two completed diagnostic nuclei. The
three radius-14.562 training balls are mutually disjoint and contribute 15,830
candidate examples with 3,171 positives. On a fourth mutually disjoint centre
`(-20, 20, 20)`, the correct 2-site action moves into the frozen width-four
beam at rank four. That is real improvement in marking transfer. The current
one-step option-supply value nevertheless chooses the false rank-two action
(three wrong sites). The benchmark therefore remains red and specifies the
next implementation precisely: retain alternative configurations across
multiple tree depths, then roll back a branch when its future frontier fails,
rather than committing after one-step lookahead.

That persistent search substrate now exists. It retains four complete
atom/cluster/port states, expands each through three tree depths, regenerates
the local marking and collision state on every branch, and only then commits
the first action. A robust companion marking takes the minimum probability
over three leave-one-nucleus-out models, penalizing a connection that is
supported by only one local environment. On the fourth (now diagnostic)
nucleus, the combined policy evaluates 36 branches and recovers an exact
3-site path `4 → 3 → 3`. Frozen exactly as-is, it is then tested once at a
fifth centre `(20, -25, 20)`, whose full target ball is disjoint from all three
training balls and the fourth diagnostic ball. The exact 1-site action is again
inside the top four at rank four, but frontier-count value selects path
`2 → 3 → 2` and emits one false site. The fifth-nucleus gate is red. This
repeatedly falsifies frontier cardinality as a value function while validating
the persistent beam as the substrate on which a learned connection value must
now operate.

A first learned value replaces that falsified scalar without changing the
candidate grammar or beam. The two completed diagnostics supply exact-action
counts by root rank `(0, 0, 1, 2)` out of two observations each. A fixed
Beta(1,1) posterior gives finite values `(0.25, 0.25, 0.50, 0.75)`; no target
coordinate, material label, or global direction is a feature. The model is
frozen and applied once at a sixth centre `(-20, -20, -25)`, whose target ball
is at least 37.749 Å in centre separation from every earlier ball. The exact
1-site action is rank four; the value-guided three-depth beam selects path
`4 → 2 → 2` and emits that site exactly after 36 target-free branch
expansions. This is the first green spatial confirmation of learned IQC branch
selection. It certifies one action only—sustained autonomous growth,
stationarity, and exponential amplification remain red.

Executing the frozen policy for two self-fed waves on that now-diagnostic sixth
nucleus separates value failure from channel coverage. Wave one remains exact.
At wave two, none of the four actively expanded root channels is correct, so
the executor emits one false site. A target-free snapshot of the first twelve
immutable score bands—without expanding the extra branches—shows exact 1-site
actions at ranks six and twelve. Candidate geometry is therefore still
present; the learned action representation is too narrow for this frontier.
The benchmark now records active branching width and diagnostic channel reach
separately. The next channel count must be selected from training recurrence or
pose/port coverage, then frozen before another spatial nucleus; this diagnostic
cannot justify silently widening the live search.

Channel selection is then made explicit. Across four completed frontier
observations, exact alternatives occurred at ranks `{3, 4, 6, 7, 12}`; keeping
all observed exact channels therefore learns reach 12. Per-rank Beta-smoothed
values use their actual support counts (four observations for ranks 1–4, two
for ranks 5–12), while the configuration beam remains width four. The first
predeclared seventh-nucleus process lost its result at the execution transport
boundary and is recorded as consumed/unknown—not rerun. With the policy still
unchanged, a new eighth centre `(-25, 20, -20)` is tested, disjoint from every
prior ball. The target-free search evaluates 108 branches, selects path
`4 → 12 → 11`, and posthoc emits the exact 1 / 1 colored site. This is a green
one-action channel/value confirmation. It does not yet certify a second
self-fed action, stationary recurrence, or exponential growth.

The repeated sixth/eighth second-wave pattern supplies the missing bounded
GCTS context. Initial-frontier observations make rank four the dominant
channel (`5/6` after smoothing). After arriving through rank four, two
independent diagnostic nuclei both place exact next actions at ranks six and
twelve, so the carried-context table assigns each `3/4`. This order-one finite
marking is frozen—no coordinate, material label, or target atom is a key—and
tested for two waves at a ninth centre `(-25, -20, 20)`, disjoint from every
prior ball. The persistent beam evaluates 108 branches per wave and commits
paths `4 → 12 → 11` then `12 → 9 → 10`. Posthoc scoring is 2 / 2 exact colored
sites with zero false placements. This is the first green spatial confirmation
of multiwave, self-fed generic IQC tree search. Wave size is still one and no
stationary production or amplification is certified, so exponential growth
remains red.

Extending the ordinal context one more step exposes its limit. After the
confirmed `4 → 12` prefix, three independent diagnostic nuclei all place the
next exact action at rank six, so a third state values rank six at `4/5`.
Frozen for three waves on a tenth disjoint nucleus `(30, -25, -20)`, however,
the exact initial action has moved to rank eleven. The rank-context policy
selects rank four and all three committed sites are false. Exact candidates
remain in the twelve-channel snapshots, but their ordinal ranks drift across
nuclei. Therefore score rank is not a physical GCTS channel. The next marking
must key on the symmetry-quotiented parent/source cluster and connection-port
semantics; rank remains only an executor-local ordering.

The semantic-key audit then prevents overcorrecting with another brittle table.
Across five completed nuclei, exact evidence keys, full structural port keys,
and coarse colored parent/source/port keys each have 0% coverage on the tenth
nucleus. A chemistry-only backoff covers 25% of its twelve candidates but does
not recognize its one exact action. The failure is not leakage—the candidate
sites, colors, and keys freeze before each target opens—and coarsening only
affects ranking, never geometric admission. The result rules out a categorical
lookup at these resolutions. The next marking is a continuous local section
fit across spatial nuclei, with the exact port and collision layers retained as
hard certificates.

That replacement now passes its first spatial confirmation. Nine previously
completed, mutually separated nuclei provide 49,716 frozen candidate examples,
including 3,695 exact coordinate-and-species positives. Unlike the earlier
geometry-only fit, a candidate at the right coordinate with the wrong element
is a negative. A rigid-motion-invariant continuous section is fitted without a
nucleus ID, global direction, phase label, or target coordinate. Eight of nine
leave-one-nucleus-out folds contain an exact action within the predeclared
twelve-channel reach, although only two rank it first.

The model is then frozen (SHA-256 `bb891f2c...d980697`) before a new centre
`(0, 0, -50)` is opened. Its target ball is separated from every training ball
by at least 37.749, versus 29.125 required for disjointness. The target-free
three-depth beam selects path `1 -> 5 -> 12`; posthoc scoring gives 4 / 4 exact
colored sites and zero false sites. This validates continuous local-section
transfer and replaces ordinal rank as the marking representation. It is still
one committed action: sustained growth, clusters-of-clusters amplification,
stationarity, and exponential IQC growth remain red.

The unchanged model is then tested for two waves at another unopened centre,
`(0, 50, 0)`. Its SHA-256 matches exactly and both waves retain twelve frozen
candidate bands. Wave one again selects rank one and emits 4 / 4 exact colored
sites. After those sites self-feed, an exact second action is present at rank
five, but the seed-trained section selects rank one and emits 0 / 4 correct.
The two-wave gate is therefore red at 4 / 8 overall. This localizes the next
problem: candidate geometry and reach are sufficient, while the continuous
section has not been trained on post-commit frontier neighborhoods. The next
model must add self-fed training states from known nuclei rather than widen the
beam or revive ordinal rank as state.

That controlled intervention is also tested. Eight training nuclei provide an
exact teacher-forced first action; their post-commit frontiers contain 44,439
candidates and 3,205 exact colored positives. A second continuous section is
fit only on those states and staged after the first commit. On a new disjoint
centre `(-50, 0, 0)`, wave one is again 4 / 4. At wave two the exact action is
present at rank four, but the self-fed section still selects rank one and emits
0 / 4. Thus exposure to post-commit states alone is insufficient. The current
descriptor is radial/color/vote based and does not continuously encode the
parent/source port-state distribution; that missing connection geometry is the
next justified feature, not more rank channels.

Adding that feature closes the two-wave gate on a new nucleus. The
`port-state-v2` descriptor augments the bounded radial section with continuous
invariants of its exact connection evidence: separation-bin moments,
parent/source neighborhood sizes, same-color and same-shape fractions,
state/parent diversity and purity, and color entropy. It contains no type ID,
coordinate, global axis, phase label, or target atom. All nine training nuclei
now provide a teacher-forced post-commit state, yielding 50,065 examples with
3,677 exact colored positives.

Both marking artifacts are frozen before the new disjoint centre
`(0, -50, 0)` is opened. The twelve-band, width-four, depth-three search ranks
the exact action first at both waves, selects paths `1 -> 6 -> 8` and
`1 -> 7 -> 6`, and emits 4 / 4 then 4 / 4 exact colored sites. The 8 / 8 result
has zero false sites and no ordinal rank state. This is a green spatial
confirmation of a self-fed continuous GCTS connection section. Wave size is
still four and no promoted stationary production or amplification is present,
so the generic exponential IQC gate remains red.

The learned-program benchmark now also has an explicit output certificate.
From a 216-atom NaCl seed, five quotient actions stream 7,077,888
species-labelled positions in 16.2 seconds. From a 507-atom IQC seed, the
locally propagated three-component GCTS mark is promoted into a rank-six
address macro; six actions stream 2,791,097 positions in 9.7 seconds. A
729-atom Fibonacci-product seed learns its substitution and streams 1,061,208
positions in five actions (2.6 seconds). All three
streams are checked with order-independent 256-bit coordinate/species digests
against structurally independent oracles (a rocksalt half-grid, sealed
cut-and-project constants, and a hidden substitution word). The output clouds
are not retained. This proves
exponential representation/action compression and linear coordinate emission.
The IQC emitter does not lift output coordinates or refit the model. Translation,
substitution, and marked-address expansion still remain distinct production
kinds behind the common API, so the strict single-production gate stays red.

The first published real-material model transfer is now sealed as well. A
provenance-pinned offline port of the Cd5.7Yb generator supplies nested 506,
1,056, and 1,672-atom windows around the fixed off-centre point
`(3.1, 5.7, 8.2) Angstrom`. Only the 506 positions and species enter the
learner. The offset is important: a crop centred at the model's global
icosahedral origin made rotational shell orbits look like independently
reusable local clusters.

The cell-free learner now merges touching adaptive-shell seeds into irregular
supports, distinguishes colored metric graphs up to proper rigid motion, and
adds an explicit residual class for complete cover. Repeated supports cover
99.4% of the seed and the frozen dictionary covers 77.1% of the first unseen
annulus. Learned proper-SE(3) overlap ports transfer 31.2% of held-out witnessed
relations on a greedy target cover. These are representation and connection
transfer results, not autonomous growth: the common recursive selector still
emits no held-out atoms. A causal incoming-port marking reduces proposal work
slightly, but does not beat shuffled-label controls for either quasicrystal.
Continuation, hierarchy depth, and meaningful marking speedup therefore remain
explicitly red.

The next architectural boundary is now executable rather than aspirational.
`materials_gcts_frozen_frontier_replay.py` detaches prototypes and admitted
proper-SE(3) ports from training, then generates frontier candidates solely by
composition with already placed occurrences. Held-out atoms are accepted only
by a separate scorer after replay. A public radial boundary rejects and counts
out-of-domain placements; unoriented residual atoms remain explicit and take
part in compatibility checks. In the one-step gate, greedy replay emits one
correct NaCl atom and three correct Cd--Yb atoms. Post-hoc oracle scoring of the
same sealed candidates finds a six-atom NaCl action and a nineteen-atom Cd--Yb
action. The ideal IQC has no exterior candidate, cleanly separating a grammar
failure from a ranking failure.

A second bounded marking replaces prototype IDs with local support-size and
species histograms, overlap chemistry, normalized translation and rotation,
and incoming-to-outgoing angle bins. It reduces raw port classes from
1,424/896/11,870 to 468/411/4,183 static action states for NaCl/IQC/Cd--Yb,
but frozen-target gains remain only 1.009x, 1.060x, and 1.000x over the
unmarked arm; IQC ties shuffled labels and Cd--Yb has zero context coverage.
This remains a red causal marking result.

The original action-history route is now retained as a negative baseline, not
the main hierarchy result. Its invariant proper-SE(3) canonicalizer admits 11
action-submacro types, every one with maximum dense occurrence multiplicity two,
and the recursion reaches only two positive levels. This diagnoses limited
independent evidence as well as representation loss; the earlier
action-history figures are no longer the canonical result.

The stronger route forgets action history and re-clusters the grown colored
point clouds. Across six patches it processes 2,064 atoms, identifies 78
repeated irregular support types with 1,122 occurrences, and adds explicit gap
clusters so the atomic configuration is completely covered. The unchanged
boundary-aware reducer, exact proper-SE(3) miner, quotient, and promoter produce
quotient counts `73 -> 17 -> 5 -> 3 -> 2 -> 1 -> 0`. A derivation-aware version
that keeps mutually exclusive exact right-hand-side alternatives separate gives
`73 -> 17 -> 6 -> 3 -> 2 -> 1 -> 0`. Neither route has a common normalized
chemistry/chirality/port production across three consecutive levels, so strict
stationarity and generic exponential growth remain red.

Train compression is not presented as transfer. In a sealed split, five
predeclared grown patches fit the primitive vocabulary and three raw-ID-disjoint
patches are held out. Frozen primitive supports cover all 1,248 / 1,248 held-out
atoms. The original width-three audit replayed 256 of 259 first-level quotient
types. The missing IDs `184 / 185 / 252` all require the same 23-atom primitive
type 49, observed only twice in training, both in patch 2 near its public crop
boundary, and never in heldout. Their required ports consequently have no
heldout witness. Trying every train-fitted exact semantic derivation remains at
256 / 259 with zero ambiguity; this is a patch-local boundary artifact, not an
alternative-derivation repair.

The corrected executable policy selects a recurrent core using training
namespaces only: an exact macro must occur in a strict majority of the five
training patches. Original macro IDs and exact action terminals are retained;
atoms outside the core remain explicit colored residual terminals. At width
five the frozen heldout **re-encoding** has raw/selected exact type counts
`520 / 148`, `53 / 10`, `16 / 4`, and `3 / 1`, with
`1,495 -> 85 -> 29 -> 9` occurrences.
Exact core atom coverage is `1,220 -> 1,033 -> 925 -> 870` of 1,248, paired
with `28 -> 215 -> 323 -> 378` residual atoms; coordinate/species SHA
certificates verify a complete representation at every level. Minimum heldout
namespace support is `2 / 3 / 3 / 3`, and maximum exact support size is
`78 / 78 / 110 / 111` atoms.

This audit observes the complete heldout positions before matching; only the
learned vocabulary—including supports, ports, quotient alternatives, and the
recurrence rule—is frozen. It therefore measures transfer of a representation,
not continuation or growth.
There is no greater-than-three recursive amplification, no normalized
stationary key common to three levels, and both autonomous-growth and
exponential gates remain red.

The first target-blind recurrent-macro executor is now separate from that
re-encoding audit. Five mutually disjoint **raw** IQC radius-11 windows train
the support, port, and strict-majority macro vocabulary (`322 -> 141` exact
first-level types). A sixth raw-ID-disjoint radius-7 seed contains 226 atoms
and two recognized recurrent macro poses. With no target argument, the
executor composes frozen overlap and witnessed non-overlap boundary ports,
commits whole proper-SE(3) macros with exact colored collision and inclusion
certificates, and feeds accepted placements into the next wave. Under a public
radius-11 boundary it accepts `16 -> 8 -> 0` placements and emits
`92 -> 56 -> 0` atoms. Only after execution is frozen does scoring expose the
873-atom target: 136 of 148 emitted atoms match, giving 91.9% precision and
21.0% recall outside the seed. This is autonomous clusters-of-clusters
continuation, but it is a finite depth-two continuation: lowering the batch
cap changes the display to three nonempty waves without changing the final
148-atom union, and the reachable frontier then reaches a fixed point. It
contains 12 wrong atoms and has no stationary amplification.

A candidate-level marking audit trains on all 718 eligible actions from five
train-only frontiers (693 valid, 25 invalid) and runs every arm before opening
the target. Exact ID-based contexts transfer 0 / 62. An ID-free port-pose →
overlap-chemistry → port-kind hierarchy instead covers all 62, creates five
first-wave scores and 112 rank inversions, and cuts matched exact-action work
from 71 to 51. It still reconstructs the same 136 / 148 atoms and reaches only
`p = 0.25` against 31 label shuffles. A 35-feature continuous proper-SE(3)
mark, now including live proposal-witness and site-consensus invariants, has
strong train-only validation loss (0.0186 versus 0.1511 global) and 362
first-wave inversions, but neither ranking nor a frozen high-precision
threshold removes the 12 wrong atoms. The threshold yields 134 correct and 12
wrong. The marking gate remains red because training calibration still does
not transfer to exterior correctness. Uniformly shifting the five training
nuclei is rejected too: it grows 718 candidates to 3,119 but adds only five
failures and still covers 0 / 62 exterior parent roles. The next sampler must
seek train-only role and failure diversity rather than duplicate easy
positives.

The role-diversity audit now selects a boundary-exposed occurrence of every
one of the 141 learned macro types from the five training windows. This rules
out the earlier zero-role-coverage explanation: all 48 incorrect evaluation
actions use exact parent/production rules that were observed as correct in
training. The residual is chiefly colored decoration, not placement geometry.
Of the final 12 wrong atoms, eight occupy exact target coordinates with the
wrong species and four are unsupported terminals. A causal local site section
fit on four windows and calibrated on the fifth sees 3,047 terminal records,
but only ten are recolor/absence examples. Its wider transferable margin makes
four recolors and ten removals on the unopened window, reducing the result to
124 correct / 16 wrong (88.6% precision). It remains a red diagnostic and is
not integrated into the executor.

The replacement representation now learns geometry before chemistry. With
species hidden, 35 irregular support types transfer to the disjoint window and
cover 841 / 873 atoms. Their 275 train-observed proper-rotation decoration
alternatives cover 795 atoms; a naive colored expansion would require 49,735
port classes instead of 7,731 factored geometry classes (6.43x). A bounded
two-incoming-port section improves decoration accuracy over one port and the
modal alternative, but loses to within-geometry label shuffles (`p = 0.875`).
Optional overlap propagation from 226 known seed species then infers 279 outer
labels, 267 correctly (95.7% precision, 41.3% recall), while outer species
remain scorer-only. This is a stronger reconstruction baseline; it is still
below the 99% / 90% gate and is not autonomous coordinate growth.

The alternatives now feed a bounded overlap tree search. All arms see the same
55,483 frozen occurrence-decoration actions. With six shared atoms and a 99%
train-posterior threshold, the GCTS ranking/admission policy infers 354 / 415 labels correctly
(85.3% precision, 54.7% recall), versus 116 / 140 for the modal ordering. All
31 within-geometry shuffles fall back to the modal result, giving
`p = 0.03125`; marking now has a significant role in search, although 61 wrong
labels keep reconstruction red.

Naively coloring promoted geometry does not solve that residual. The first
uncolored clusters-of-clusters level retains 457 geometry types and 18,660
train occurrences, but none of 13 transferred heldout macro occurrences has a
train-seen whole-macro decoration. Macro type plus child role improves the same
27 child samples from 2 to 5 correct, yet loses to shuffle controls
(`p = 0.1875`). Chemistry must therefore remain a finite child alternative;
the next mark should quotient macro boundary context rather than memorize an
entire colored macro.

The lower-cardinality boundary follow-up remains red on ideal IQC. A
train-selected ID-free macro-boundary descriptor predicts 5 / 27 child
decorations (`p = 0.125`); consensus over unique children gives 3 / 19
(`p = 0.21875`). Only 9 / 27 role samples have their correct full decoration
anywhere in training. Unary/pair partial sections can generate unseen whole
decorations, but improve heldout site accuracy only from 68.68% to 69.78%; none
of 811 unseen predictions is exactly correct.

The published Cd5.7Yb model is a much stronger positive case. Two disjoint
radius-14 crops provide 969 train atoms and a third disjoint crop provides 478
evaluation atoms. Frozen geometry covers 449 / 478 atoms. From a 59-atom
colored inner seed, every search arm sees the same 1,385 exact actions. GCTS
reconstructs 378 / 378 novel atoms (100% precision, 90.21% outer recall), while
modal and all 31 within-geometry shuffles stop at 377 / 377 (89.98% recall).
The extra correct reach at unchanged perfect precision gives `p = 0.03125`.
This turns the fixed quasicrystal reconstruction and GCTS-ablation gates green
on a published real-material model. Positions are supplied and the frontier
reaches a finite fixed point, so autonomous and exponential gates remain red.

The same split now has a genuinely autonomous coordinate-emission test. A
colored irregular-support grammar is frozen from the two training crops, and a
consensus threshold is selected only by radius-7 to radius-14 reconstruction
inside those training domains. The selected threshold, 0.6, is then applied to
the disjoint 59-atom seed with only a public radius-14 boundary. Before the
478-atom target is opened, five self-fed waves accept `3 -> 18 -> 9 -> 35 -> 7`
whole clusters and emit 179 coordinates. The sealed scorer finds 177 correct
and 2 wrong: 98.88% precision and 42.24% recall over the 419-atom outer region.
The unfiltered arm reaches 68.26% recall but only 78.14% precision; strict
consensus is exact but reaches only 4.53%. The accepted antichains are promoted
target-free into exactly certified colored action macros, but no normalized
macro signature recurs across three waves. Finite autonomous Cd--Yb
continuation is therefore green; sustained/stationary and exponential growth
remain red.

A bounded local GCTS section now resolves the finite-growth precision failure
without using a material label or global coordinate. On the two training
frontiers, the accepted candidate distances have a learned gap at 2.118
nearest-neighbor units. Proposals on the close side must have at least five
independent frozen cluster-connection witnesses. The rule sees only already
placed atoms and the candidate's overlap witnesses. On two mutually disjoint
evaluation nuclei it emits 178 / 178 and 117 / 117 correct atoms; the unmarked
executions emit 193 / 220 and 168 / 224. Across both nuclei that is 295 / 295
for the section versus 361 / 444 unmarked. Thirty-one controls preserve each
wave's candidates and witness-count multiset but permute which placement owns
which count; none matches the learned zero-error reach (`p = 0.03125`). This is
the first causal GCTS-marking win during autonomous growth of the published
quasicrystal model. Both marked runs still reach finite fixed points, and their
promoted action macros have no three-wave recurrence, so sustained and
exponential growth remain red.

The history-free hierarchy now has a deeper real-material test. Five disjoint
radius-14 Cd--Yb windows contain 2,385 atoms and learn a complete irregular
cover. Exact macro quotienting produces nine positive levels,
`80 -> 36 -> 22 -> 15 -> 8 -> 6 -> 4 -> 2 -> 1`, while the largest colored
support grows from 67 to 472 atoms. Every support stays inside its packed crop
namespace. At level one, 79 / 80 retained types have proof occurrences in at
least two disjoint windows; every later retained type does. The five windows
are distinct configurations, although disjointness alone is not statistical
independence. The strict stationary audit nevertheless finds no three-level
common production, with child-count/topology already failing.

Two reserved windows provide an honest frozen-transfer boundary. Without
refitting or renumbering, the entire frozen vocabulary remains available while
types absent from the finite region stay dormant. Exact active
types/occurrences continue through four levels:
`53/92 -> 20/26 -> 8/8 -> 2/2`, covering respectively
`560 -> 445 -> 314 -> 170` of 959 observed atoms. Level five has no active
occurrence and stops. Every attempted level retains frozen IDs and ports, exact
proper-SE(3) replay, and complete representation through explicit residuals.

Simple filtering does not manufacture this result: all 27 absent first-level
types have the same two-window training prevalence as 50 / 53 active types; a
strict-majority core covers only 13.56%. Predeclared semantic descriptors find
no recurrent port-consistent class and exact derivation alternatives recover
no absent type. Since heldout coordinates are supplied for matching, the four
levels are exact re-encoding, not autonomous growth. Transferable vocabulary
closure, stationary recurrence, and exponential Cd--Yb growth remain red.

The hierarchy now has a seed-only execution gate. A predeclared 478-atom
radius-14 Cd--Yb seed is spatially disjoint from all five training windows and
the radius-25 target remains unopened during execution. It recognizes 276
primitive occurrences but zero complete level-one macros, so the exact frozen
hierarchy cannot start. A NaCl control executes its recognized macro exactly.

The generic fallback recognizes a promoted macro from a finite partial RHS.
It enumerates proper symmetry gauges, requires a train-admitted port from the
observed anchor to a missing child, and rejects collision, boundary, or parent
ambiguity. One-child recognition produces 82 target-blind candidates; only six
are exact posthoc. A GCTS mark trained on five radius-7 to radius-14 frontiers
selects one exact action among its top five and emits 16 correct / 18 wrong
sites, versus constant ordering's 13 / 24. All 31 within-parent label shuffles
tie it (`p = 1`). The partial macro search machinery is now present, but
transferable ranking and autonomous hierarchical growth remain red.

A second, publicly preregistered Cd--Yb nucleus now tests whether a continuous
ID-free section fixes that transfer failure. The complete model, 28-row
training corpus, source hashes, top-five policy, 31 within-window shuffled
refits, and centre `(35, 35, -35)` were committed before the target opened.
The common first frontier has 36 candidates and no completely exact macro
action. The marked top five emit 27 / 56 correct sites versus stable and
frequency ordering's 10 / 41, but all 31 shuffled models reproduce the marked
result (`p = 1`), so the causal marking gate is red. Target-blind execution does
self-feed through seven nonempty waves over four hierarchy levels and reaches
247 / 2,217 outer-shell atoms (11.14% recall), but the preregistered primary and
sustained-growth gates both fail. The sole target opening and result are now
sealed in a hash-checked, non-rerunnable fixture.

The next train-only section moves the mark inside the macro. Across the same
five training windows, three predeclared seed radii and fixed nearest-neighbor
shifts supply 123 macro candidates and 1,245 emitted-site examples: 871
supported and 374 unsupported. The ten-feature local proper-SE(3) section
reaches grouped site AUC 0.8864 and whole-action AUC 1.0; every one of 31
within-window label shuffles is lower for both (`p = 0.03125`). A train-selected
zero-error logit safety margin of 1.5 gives 97.73% fixed-margin held-window
precision, and its final threshold selects 70 / 70 cross-window sites. That is
not yet permission to open another target: when margin selection itself is
fully nested, precision is 94.48%, below the fixed 95% deployment gate. A
structural atomic peel is also rejected: it preserves the
complete cover through explicit residual subclusters but lowers train precision
from 110 / 148 to 62 / 90. The generic executor therefore keeps exact
port-connected components, scores their sites, accepts compatible high-score
sections, and keeps every deferred obligation as an exact residual terminal.
A partial mask never becomes a cluster occurrence; a child appears only after
its full colored support is present, and a parent appears only after all
children and frozen ports are independently reverified. Synthetic controls and
the NaCl control pass (48 / 48 emitted sites correct), but Cd--Yb deployment is
disabled until fully nested train-only high-precision calibration succeeds.

For the ideal IQC parallel-action gate, the backend now carries the port
incidences themselves instead of only their aggregate moments. A role is the
symmetry-quotiented parent/source local type plus normalized separation; each
action state keeps at most eight roles. A child must consume a carried role,
and bounded search backtracks a branch whose explicit obligations have no
frozen continuation. On a 504-action nine-nucleus audit, 97.4% of held-out role
mass is train-seen. The search finds connected two-action paths on eight of
nine nuclei, but posthoc all 16 selected actions are false (120 false sites).
Individual roles and order-two same-site role patterns are not transferable
success labels. The reserved confirmation nucleus remains unopened: the next
marking needs joint incidence geometry, while the exact action/collision layer
stays fixed.

The marking has therefore moved from whole equal-score bands to individual
candidate cluster centres. The finite descriptor contains semantic port roles,
order-two incidences, proposal-neighbour distances, and the colored distance
shell to already occupied atoms; it contains no origin, global frame, raw
occurrence ID, target atom, or material label. Adding the colored metric graph
of the nearest occupied neighbors supplies the missing angular invariant.
Across 44,602 collision-free candidates and nine leave-one-nucleus-out folds,
the calibrated complete score level admits 25 / 26 compatible placements
(96.15% precision). It covers only four of nine nuclei, below the predeclared
all-nucleus gate, so the reserved confirmation remains sealed.

The user-visible geometry settings are also audited rather than treated as
cosmetic knobs. A bounded grid crosses one-, two-, and three-shell reach with
coarse/fine distance quantization. For each outer held-out nucleus, a nested
leave-one-nucleus-out loop on the remaining eight selects both geometry and a
complete-score threshold. Those absolute thresholds drift when the final
training fold is added and achieve only 41 / 65 correct actions (63.08%). A
fixed top-two rank is more stable: it selects 16 / 16 exact actions on the
eight generic nuclei, but two false actions on the sole symmetry-centred
nucleus, hence 16 / 18 overall (88.89%). Increasing the section to 32 nearest
neighbors moves the first exact centred action only from rank 189 to 121 and
does not change the top-two failure. Thus neither wider reach nor nested
parameter selection passes the unchanged all-nucleus gate.

A symmetry-orbit channel projection then prevents a large family of equivalent
rotation or metric-edge tokens from receiving extra weight merely because it
has more representatives. A label-free selector chooses between the detailed
and channel scores by the size of their exact top-score equality orbit. Fixed
at three-shell reach, 0.25 distance bins, eight neighbors, and two actions per
nucleus, it reaches 18 / 18 exact placements on the nine development nuclei.
The rule and candidate/model digests were committed before the reserved centre
was imported. The one-shot spatially disjoint confirmation is red: detailed
and channel top bands contain four and two actions respectively, the frozen
rule chooses detailed, and both selected actions are false (0 / 2). The target
was constructed once after the selection digest was frozen. Orbit multiplicity
is therefore rejected as a transferable value function even though
symmetry-quotiented pose channels remain the correct representation.

The consumed nucleus then joins development for a stricter follow-up. Choosing
the channel view whenever detailed and channel orbit cardinalities disagree
reaches 18 / 20 group-heldout actions. A nested candidate-level linear section
cross-fits the base token model again for every meta-training nucleus, then
uses 15 invariant score, rank, orbit-size, token-family, and evidence-coverage
features. Fixed ridge strengths 0.1, 1, and 10 each select 0 / 20 exact
actions. Candidate positions and colors are identical throughout, and the next
disjoint centre remains unopened. This rejects scalar score stacking as the
missing marking: the next model must operate on the joint incidence graph.

That graph is now explicit. The primary symmetry-quotiented connection role is
coupled to every occupied colored shell and every pairwise metric edge, giving
6,140 role--shell and 19,837 role--edge types without changing any candidate.
Across ten held-out nuclei, 97.66% of descriptor tokens receive a train-frozen
weight. The best fixed fit nevertheless selects only 15 / 20 exact actions;
support/group floors of 16/3 or 32/3 give 14 / 20, and the strongest 64/5
regularization gives 8 / 20. The remaining failure is therefore topological:
independent edge weights cannot represent the arrangement of a local incidence
graph. The next section must use finite canonical subgraphs or bounded message
passing while retaining the same exact placement layer.

A bounded message-passing control retains that topology explicitly. Occupied
nodes begin with species and candidate-relative radial shell, then exchange
their complete pair-distance-labelled neighbor multisets for one or two rounds;
the primary port conditions every node and whole-graph color. Both depths score
14 / 20 exact group-heldout actions. Exact message hashes create 80,323
one-round and 161,768 two-round role-conditioned node colors, respectively, so
recurrence fragments instead of improving. These hashes only rank already
certified candidates and never authorize geometry. The next section must learn
a train-only finite quotient of message colors before applying the marking.

The first finite-quotient audit is now complete and remains red. Coarsening
message distances by factors two, four, or eight and replacing full port roles
with parent/source color roles reduces the exact one-round vocabulary as far as
12,954 node and 5,787 graph colors, but all exact-hash variants remain at
14 / 20. A stronger additive quotient records bounded colored node-state and
metric-edge multiplicities instead of hashing the whole neighborhood. It uses
only 457 node and 976 graph types and reaches 15 / 20. Finally, a positive
prototype is admitted to a finite codebook only when its graph view recurs in
at least two or three independent nuclei. The selected three-nucleus codebook
contains 356--358 prototypes per fold but falls to 11 / 20. Candidate geometry,
collision certificates, and the two-action antichain are identical in every
arm; the next disjoint centre remains unopened. This rejects vocabulary size
and nearest recurring graph prototype as sufficient GCTS value functions.

To distinguish small-sample instability from the wrong model class, eight new
development centres were frozen in commit `fc80434` before any corresponding
seed or target was generated. Their radius-14.562 domains are mutually
disjoint and remain at least 37.417 from every prior, consumed-confirmation,
and reserved-confirmation domain. A common model-set crop at coefficient bound
24 has identical per-centre seed/target counts at bound 25: 476--496 seed atoms
and 2,028--2,064 target atoms. On those stable crops the previously frozen
457-state quotient selects 14 / 16 new actions and 30 / 36 across all eighteen
nuclei. Stricter support/group floors fall to 28, 24, or 27 / 36.

A finite conditional-state model then learns complete node/edge/graph-state
purity and backs off deterministically through node/graph, graph/port, and
coarse port/color/occupancy states. It reaches 29 / 36, below the additive
baseline, despite thousands of independently supported fine states. Thus the
expanded corpus rejects both "more recurrence support" and "whole-state
lookup" as sufficient explanations. Candidate geometry is unchanged and the
reserved centre `(0, 50, 0)` remains unopened.

The marking now also retains the orientation that a frozen port presents to
the occupied neighborhood. Candidate-to-parent axes are compared with nearby
occupied directions by dot products; signed scalar triple products preserve
handedness. These features quotient arbitrary proper rotation and translation
and require no lattice axis. Angular widths 0.125 / 0.25 / 0.5 create 9,580 /
6,501 / 4,414 finite orientation tokens. The coarsest arm ties the 30 / 36
unoriented result, while finer arms select 28--29 / 36.

An order-independent search control then enumerates all 120 compatible
unordered pairs in each 16-action shortlist. Every one of the eighteen nuclei
contains an exact pair (at least six per shortlist), and pair fitting is nested
so an outer nucleus influences neither its candidate shortlist nor its pair
marking. The selected pair model remains at 30 / 36. Thus candidate supply,
attachment rotations, and greedy action order have been separated from the
remaining transferable-value failure. The reserved confirmation is still
sealed.

The first causal value improvement comes from the state after an action. For
each fold, only its frozen top-16 candidates are placed hypothetically. Local
cluster types and connection proposals are recomputed, and the marking sees
the count, vote mass, chemistry, finite port roles, and order-two incidences of
the newly exposed frontier. It never sees the target during rollout. The
strongest independently supported successor section improves selection from
30 / 36 to 32 / 36 once both causal endpoints of every affine connection are
carried. A bounded second successor step evaluates 76--184 child branches per
nucleus and reaches 33 / 36 with 16 / 18 exact nuclei. The informative object
is therefore not another unordered frontier shell alone; it is the obligation
carried along a particular root-to-child path.

Retaining that path produces the strongest expanded result so far. Each
descriptor binds the root successor, the incoming child-port roles and
order-two patterns, and the child successor into one directed record. Geometry
is frozen before labels enter; a path is positive only when both placements
are correct. Scoring each root by its best supported four-child continuation
reaches 33 / 36 at width four. Widening the exact tree from four to sixteen
children supplies at least two exact paths in every nucleus and raises
selection to 34 / 36, with 16 / 18 exact nuclei. Candidate supply is complete
at this bounded depth; the two remaining failures are ranking errors among
present alternatives.

Pooling connection markings before quotienting cluster identity fails. The new
generic merger requires pooled purity, positive support, and positive evidence
from independent configurations, and retains chemistry evidence. Yet exact raw
local types include crop-boundary variants: the loosest fold-frozen merge
supplies correct root candidates in only 14 / 18 nuclei and exact root→child
continuations in 7 / 18. Therefore expanded configurations must first be
mapped to a shared recurrent cluster vocabulary; a union of raw markings is
not a valid shortcut.

That ordering now has a direct held-out audit. Ten training nuclei learn 455
local pose classes that recur in at least two independent configurations;
only then are their connection states pooled. On eight expanded validation
nuclei the frozen quotient supplies at least one correct first action in all
eight and an exact root-to-child continuation in all eight. The formerly
missing continuation exposed a causal bookkeeping error rather than a missing
port: an affine action depends on both its ordered parent and source, but the
successor search had retained only the parent index. The engine now carries a
separate causal-endpoint map while preserving the geometric parent role used
by marking features. No evidence threshold was relaxed, and the reserved
confirmation remains unopened until this exact rule is committed.

The rule was then committed and separately preregistered before the reserved
nucleus at `(0, 50, 0)` was opened exactly once. Its complete target-free graph
contains 672 root candidates and 1,104 causal successors; the model and both
candidate layers were SHA-serialized before target access. Posthoc scoring
finds 38 exact colored roots and four exact root-to-child paths, with the first
path reached after eight correct roots. The domains are spatially disjoint and
no target atom entered fitting or candidate generation. This confirms
transferable candidate supply, not autonomous selection, stationary
recurrence, or exponential IQC growth.

The corresponding recurrent-path value audit keeps geometry and labels in the
right order. It first freezes a 256-root by 16-child target-free tree, which
contains exact two-step paths in all eight development nuclei with counts
`13 / 2 / 8 / 8 / 1 / 14 / 13 / 13`. Only afterward does each group-heldout
fold label its frozen paths and fit a bounded incidence-token section on the
other seven groups. The selected support-24 / five-group marking ranks an exact
path first in `7 / 8` nuclei. The failed nucleus still contains one exact path
among 293 candidates, so supply is green while autonomous path selection stays
red. No new reserved nucleus is opened for a selector that has not passed its
development gate.

A first behind-the-scenes clusters-of-clusters value now evaluates each
tentative root→child pair against the frozen recurrent cluster vocabulary. The
incremental calculation has exact parity with full reclustering: it records
the two inserted-cluster residuals, the residual induced on affected existing
clusters, and an invariant frontier angle estimated from the nearest eight
occupied sites. A group-heldout linear section keeps the seven easy nuclei at
rank one and moves the rare nucleus's sole exact path from rank 101 to rank 21,
a `4.81×` pruning gain. Because it still does not select that path first,
clusters-of-clusters pruning is reported separately from autonomous selection.

The next audit corrects an overly restrictive search interpretation. A prior
third-step check required every new action to be causally attached to the most
recently inserted cluster. That is a valid directed-path diagnostic, but it is
not the intended order-independent covering search: after a commit, any
exposed frozen port on the whole configuration may act next. Ten authorized
training nuclei now provide 20,716 candidate descriptors and 1,151 exact
actions over three self-fed stages. A stage-aware leave-one-nucleus-out grid
selects a support-4 / two-group / 0.5-shrinkage finite incidence marking.
Conditional on a known-exact two-action prefix, every one of the eight heldout
configurations contains 57--75 exact global frontier actions. The previous
clusters² compatibility ranks `3 / 3 / 4 / 4 / 1 / 9 / 9 / 9`; the new
post-commit marking gives `3 / 4 / 3 / 3 / 1 / 1 / 1 / 1`. Thus width four
has complete conditional supply, while top-one selection remains only `4 / 8`.
Heldout truth constructs the exact prefix and scores the frozen frontier, so
this explicitly does **not** certify autonomous, sustained, stationary, or
exponential IQC growth.

An orientation-capacity ablation then asks whether the missing value is simply
the cluster rotation channel requested by the UI. Candidate attachment axes
are expressed only through dot products and signed triple products relative to
the occupied neighborhood, so global proper rotation and translation are
quotiented while chirality is retained. Angular widths 0.125 / 0.25 / 0.5 and
additive versus one-vote-per-channel scoring are selected strictly by grouped
training stages. The train winner uses width 0.125 and channel scoring, reaches
`23 / 28` eligible stages, and retains 28,558 weighted tokens. On the eight
conditional heldout frontiers, however, first-exact ranks worsen to
`5 / 1 / 7 / 6 / 1 / 3 / 3 / 3` and top-one falls from `4 / 8` to `2 / 8`.
This is why the interface reports observed symmetry-inequivalent poses but
derives Auto capacity from recurrent pose × connection-port rank: one channel
per observed rotation is a high-cardinality overfit, not a GCTS principle.

The cluster-identification stage therefore exposes the translation support as
an explicit hypothesis: a periodic lattice, a finite-rank aperiodic module, or
an observed/generated non-regular point set with free proper-SE(3) placement.
It also freezes a separate proper-pose atlas for every cluster isometry class.
Only after that atlas and its connection ports are known does the marking stage
derive its per-cluster channel rank. The UI allocates the largest required rank
as a shared tensor width and masks unused channels for lower-rank clusters;
manual channel counts are capacity ablations, not alternative rotation atlases.

The replacement now respects the pipeline boundary explicitly. Clustering
freezes the 0.125-radian proper-pose atlas first; marking learning is not
allowed to refit that geometry. It pools the frozen descriptor evidence into
five invariant channels—connection role, proposal multiplicity, occupied
shell, neighboring incidence, and pose/chirality—and train-selects a bounded
quantization of their normalized responses. The chosen support-4 / two-group /
state-width-1 model contains 437 recurrent states. On the same eight
conditional heldout frontiers it ranks an exact action first in `8 / 8`,
improving the unquotiented `4 / 8` result with identical candidates. This is a
green conditional branch-selection gate. Heldout truth still supplies the
two-action prefix, so autonomous, sustained, stationary, and exponential IQC
growth remain unclaimed pending a newly sealed self-fed confirmation.

That confirmation is now consumed. The first preregistered centre was retired
unscored when lift bounds 24 and 25 produced different target crops. A second
centre at `(-50, 50, -10)` was committed 40.31 units from every prior domain,
with bound-32 / bound-33 stability required. Before one target-open call, the
frozen 437-state model built a width-four, reach-four, depth-three
configuration tree with candidate counts `4 / 16 / 16` and retained four
configurations at every depth. Its selected self-fed branch emitted three
colored sites. Posthoc only `1 / 3` was exact. Thus the conditional `8 / 8`
gate remains useful evidence for the marking representation, but the first
autonomous top-one gate is red; no sustained or exponential claim follows.
Post-confirmation diagnosis finds one all-exact path in the frozen tree, with
within-parent ranks `1 -> 4 -> 4`, but cumulative pose-port probability ranks
it 10th of 10 distinct terminal configurations. The selected path is
`exact -> false -> false`. Merely widening the retained beam from 4 to 16
does not repair grouped training supply; some held-out correct actions occur at
ranks 17, 28, and 847. The next gate is therefore a transferable recurrent
branch value at bounded reach, not a cosmetically enormous beam.

That value now clears a development gate. Twelve additional nuclei are chosen
by a geometry-only maximin rule, at least 47.17 units from the prior centres
and 44.72 units from one another, and all are retained regardless of their
labels. Across the resulting 30 spatial groups, the fixed reach-four /
beam-four / depth-three search produces 354 terminal branches, 211 exact, with
exact alternatives in 21 groups. The cumulative pose-port product selects an
exact branch in 17 / 21. A group-heldout nearest-recurrent value appends only
the order-independent action-color population to nine invariant branch
statistics; train-only capacity selection chooses `k = 9` and reaches 20 / 21
(`95.24%`) with identical candidates. The frozen model digest is
`dcaae79dc2a8c3edf1caec7fc32b05054077c125e8b1e5ad93c11e8097be56ce`.

On the already-consumed diagnostic tree, this model moves the sole exact
terminal configuration from rank 10 to rank 1. When the upstream finite
pose-port state model is also refit on all 30 groups, the same target-free tree
contains 12 / 12 exact terminal configurations and the recurrent value selects
one. These are post-development diagnostics, not another confirmation.

The new maximin, atom-domain-disjoint confirmation at `(40, -40, -80)` is now
consumed and honestly red. The 30-group state model was serialized before any
seed access as a typed, compressed finite vocabulary with 148,729 token
weights and 876 recurrent states. The branch model, reach four, beam four, and
depth three were committed before materialization. The target-free execution
froze `4 / 16 / 16` action candidates and four terminal configurations, with
candidate digest `9ef36560339e20e6b384a6a85199e5e277b5213a3e9845ef81b07526fd1cda48`.
Bounds 44 and 45 agree, and the target opened exactly once after the execution
trace froze. Posthoc, none of the four terminals is all-exact; the selected
branch places `2 / 3` colored sites correctly. This converts the next problem
from value-only ranking to transferable candidate supply and beam retention.
It does not justify widening the beam after seeing this target, and sustained,
stationary, and exponential IQC growth remain red.

The next implementation moves value estimation to the point where the failure
occurs. A target-free diversity scheduler freezes 1,259 partial configurations
from the 30 development groups; 934 prefixes contain only exact colored moves.
Three recurrent value heads share the same invariant feature schema but select
their capacities independently while leaving out every row from one spatial
nucleus. Depths one, two, and three choose `k = 25 / 15 / 9` and select exact
prefixes in `29 / 29`, `27 / 28`, and `25 / 28` supplied stages. The aggregate
`81 / 85` (`95.29%`) passes the frozen-snapshot transfer gate with complete
score-tie handling—an unresolved mixed top-score tie never counts as success.

This does not yet solve the executor. When those heads control the self-fed
search on the already-consumed confirmation nucleus, beam widths 4, 8, and 16
all finish with zero exact terminal configurations and the selected branch
remains `2 / 3` correct. The implementation is therefore retained as a
selectable depth-conditioned marking, while the autonomous gate stays red.

The next scheduler now preserves recurrent connection-state diversity rather
than only action-color population. It normalizes each partial branch with its
train-fold head, quantizes the resulting invariant vector, and allocates a
finite quota per recurrent state. Train-only selection chooses state widths
`4 / 4 / 2`, quotas `1 / 2 / 1`, and total beam budgets `4 / 4 / 8`. This
retains an exact prefix in every one of the 85 supplied frozen snapshots.
Nevertheless the consumed closed-loop nucleus remains red: it retains
`2 / 4 / 8` configurations across the three depths, produces zero exact
terminals, and again selects `2 / 3` correct sites. Snapshot coverage is now
green; transfer of the carried state under self-fed distribution shift is the
remaining blocker.

The next audit performs exactly one group-sealed branch-value aggregation
round. For each of five folds, all rows from four heldout nuclei are excluded
from the value fit, and the pose-port state model used for the on-policy
rollouts is also refit without them. The frozen policy is rolled only on the
other 26 nuclei. This adds 4,037 invariant partial branches, including 3,224
exact prefixes. Exact duplicate rows are removed, but opposite outcomes for
the same descriptor are retained; 15 fold-local descriptor classes expose
real representation aliasing. Closed-loop exact terminal supply improves from
`16 / 20` to `18 / 20`, exact selected paths from `10 / 20` to `13 / 20`, and
correct selected moves from `44 / 60` to `51 / 60`. Two failures are therefore
candidate-supply failures and five are supplied-but-misranked failures.

This comparison is not fully nested end to end: the older broad snapshot
features were generated once using the shared upstream pose-port model, even
though their heldout rows are excluded from each branch-value fit. The result
is retained as an honest branch-value development diagnostic, not a sealed
generalization estimate. It is red regardless—the predeclared gate requires at
least `18 / 20` exact selections—so it does not authorize opening a new
confirmation nucleus.

A subsequent audit removes that caveat and tests the channel representation
directly. Each fold refits its upstream pose-port marking without the four
heldout nuclei before generating both the broad and on-policy trees. A branch
action carries five bounded proper-SE(3)-quotiented channel responses. The
responses are sorted as an action multiset so commuting order is irrelevant;
six relative-distance fields associate geometry with the `XX / XY / XZ / YY /
YZ / ZZ` color roles. Raw positions and cluster IDs never enter the value fit.

At identical search reach and beam work, the fully nested feature ablation is:

- base branch statistics: `14 / 20` exact selections, `17 / 20` terminal
  supply;
- base plus colored relative geometry: `15 / 20`, supply `17 / 20`;
- base plus pose-port channel responses: `14 / 20`, supply `16 / 20`;
- all coupled fields: `15 / 20`, supply `16 / 20`.

One on-policy refit of the coupled representation falls from `15 / 20` to
`14 / 20`; it is rejected. The result sharpens the channel rule used by the
interface: clustering may determine the pose-orbit basis and hence available
channel rank, but raw orientation/channel count is not itself predictive.
GCTS needs the connection section that couples those channels to colored local
geometry. Even the best current ablation is only 75%, below the `18 / 20` gate,
so no new confirmation target is opened.

The marking library is now tested as an executable portfolio rather than only
as four separate menu choices. Base, colored-geometry, pose-port, and coupled
markings each propose their bounded state-diverse ordering, but they share one
unchanged total beam of `4 / 4 / 8`; round-robin allocation cannot increase
search work. This raises exact-terminal supply to `18 / 20`, although the raw
portfolio order selects only `13 / 20` and `51 / 60` correct moves.

A second value head is therefore fitted only on the terminal configurations
the portfolio actually retains in each fold's 26 authorized nuclei. Inner
whole-nucleus selection chooses representation and neighbor count before the
four outer heldout executions. The five choices are
`ports:k3, base:k9, base:k5, base:k1, base:k9`. The resulting terminal value
selects `16 / 20` exact paths and `54 / 60` correct moves. All top-score ties
are either absent or uniformly exact; there are no mixed ties resolved by
candidate order. The remaining error is now sharply split into two nuclei with
no exact terminal and two with a supplied exact terminal that is misranked.

A nested ridge-logistic control is worse: `12 / 20` from broad states and
`10 / 20` after on-policy merging, so a smooth linear interaction is rejected.
The portfolio terminal value is the new development baseline, but 80% is still
below the committed 90% gate. The next sealed nucleus remains unopened.

Several fully nested pruning controls now isolate the remaining failure. Root
proposal reaches `5 / 8 / 12` all retain the same `4 / 4 / 8` committed beam;
reach 12 exposes an exact first action in all `20 / 20` nuclei, yet the direct
portfolio order selects only `13 / 20`. Independent values at the three depths
remain `16 / 20` with terminal supply `17 / 20`. A stricter label propagated
backward only through actual frozen parent edges from exact terminals falls to
`15 / 20`, supply `16 / 20`.

A bounded target-free `12 / 4 / 8` lookahead removes retention as an excuse:
7,312 proposal checks contain an exact terminal in every nucleus. A value fit
to the broad terminal distribution selects only `12 / 20`. Canonically
associating each pose/port channel with its three inter-action edge lengths
reaches `15 / 20`; none of the five inner folds selects that new representation.
A train-selected minimum-support consensus over existing valid terminal
branches reaches `13 / 20`. These are rejected controls, not menu additions.
Before unordered action sets are deduplicated, a separate audit also counts
the distinct valid placement orders reaching each three-action terminal. There
can be at most six. Correct terminals reach multiplicity six in `17 / 20`
nuclei, but false terminals also do so in `11 / 20`, and both classes do so in
the same `8 / 20`. Multiplicity-first and score-times-multiplicity select only
`14 / 20` exact paths (`52 / 60` correct moves); adding `0.1 log(multiplicity)`
merely ties the broad score at `15 / 20` (`53 / 60`). The count remains useful
for displaying commuting red flashes, but is rejected as a pruning value.
The unchanged `16 / 20` portfolio terminal value remains best among these
pruning controls: proposal supply is solved on development data, while
transferable terminal valuation is open.

A subsequent local-section value improves that baseline without changing the
portfolio states. For each proposed colored attachment, a fixed 180-component
tensor bins distances and pair angles to species-labelled atoms that are
already occupied. It is invariant under translation and proper rotation,
uses no lattice coordinates or absolute origin, and receives no future or
target atom. Whole-nucleus inner selection chooses among base, radial,
radial+base, radial+angular, and combined representations. Its five outer-fold
choices are `radial:k1`, `base+section:k3`, `base:k9`, `section:k15`, and
`base+radial:k3`. The result is `17 / 20` exact terminals and `55 / 60`
correct moves from the same `18 / 20` supply—a one-nucleus improvement, but
still below gate. Adding pairwise shared-neighbor slack/balance remains
`17 / 20` and drops to `54 / 60`; legacy atom-centred prototype-closure
features are selected in zero folds. The compact halo is exposed as an
experimental marking-library representation. Its distance/angle tensor is
also mirror-invariant. A separate 30-channel pseudoscalar extension sums
species-labelled neighbor triple products with fixed radial moments. It is
invariant under atom permutation and proper SE(3), and flips sign under
reflection. Inner folds select the chiral representation twice, but outer
selection falls to `15 / 20` exact terminals (`55 / 60` correct moves). The
chiral halo therefore remains an opt-in marking-library choice for genuinely
chiral structures, not the default IQC value.

The cluster-completion control is now genuinely non-centred. Ten geometry-only
training nuclei are fitted independently; duplicate occurrences or rotational
copies inside one nucleus contribute only one recurrence vote. Cheap colored
distance signatures are followed by exact metric-graph isomorphism, so
homometric collisions remain different classes. Requiring support in at least
three nuclei retains 53 irregular support types of 6--22 atoms. For each exact
candidate action, a bounded branch-and-bound section records the largest
species-preserving partial support containing that action and already occupied
sites; it never creates a site or reads target atoms. Whole-nucleus nested
selection uses this partial-support representation in two of five folds, but
the aggregate remains `17 / 20` exact terminals and `55 / 60` correct moves.
This rules out both atom-centred closure and full/partial irregular-cluster
completion as sufficient terminal values. It does not rule out a section over
the *ports between* those irregular supports, which is the next generic GCTS
representation to test.

Candidate supply is no longer the uncertainty. A second train-only audit keeps
the first 128 canonical local descriptor classes in every nucleus, expands
each proposed root once, and records only child actions connected through the
newly placed parent. Exact two-step pairs exist in all nine nuclei, with
positive counts `12 / 53 / 24 / 14 / 27 / 27 / 27 / 27 / 6`. The current
primary-port discharge plus bounded joint incoming→outgoing transition marking
initially selected `0 / 9` exact paths because the executor added an unrelated
raw child-vote score after the learned root→child value. Removing that double
count, while leaving every action unchanged, selects `5 / 9` exact paths. Thus
the geometry and finite tree are broad enough; four boundary environments and
transferable ranking of their existing alternatives are the next red gate. No
reserved target was imported or opened.

A bounded third-frontier control tests whether the missing value is simply
future candidate supply. The shortlist is fixed without labels by raw child
evidence at 512 paths per nucleus and contains exact alternatives in all nine.
Every path is executed one additional target-free step; the value section sees
only outgoing roles, order-two incidences, vote/parent mass, predicted colors,
and normalized child-to-frontier distances. It selects 4 / 9 exact paths,
worse than the corrected two-step section's 5 / 9. The larger immediate
frontier is therefore rejected again as a GCTS value function.

A strict finite-state substitution-cycle audit also remains red. A nontrivial
period-`p` cycle requires `2p+1` consecutive exact levels so each state and
directed transition is witnessed twice, plus equal independently learned
transition scales and exact population substitutions on heldout/self-fed
evidence. The current four-level IQC hierarchy is one level short even for
period two and has zero exact adjacent production-state intersections.

A deterministic train-only beam provides the bounded future-RL comparator. It
chooses alternative-consistent exact derivations and improves occurrence
retention from `153 -> 34 -> 10 -> 6 -> 4 -> 2` to
`324 -> 78 -> 26 -> 12 -> 8 -> 4`; its fixed-eight-level score improves from
`-63.205` to `-34.592`. Both paths still end after six positive levels and both
fail the unchanged stationary audit. The exact semantic quotient is rejected
by the train-only shuffle and perturbation controls; approximate pooling is
never relabelled as exact recursion.

The child-width implementation is not the bottleneck. The single sparse
216-atom NaCl audit is evidence-starved and admits only six size-two macros.
With two independent bounded 216-atom presentations, cached nonfactorial
partition refinement reaches maximum child width eight. The complete learned
relation graph contains 29,988 relations joining 52 cells and exports an exact
macro with 8 children, 24 directed ports, a 52-atom colored union, 2
atom-disjoint occurrences, and structural MDL saving 30. Independent replay of
the frozen relations over three learned factors yields witness totals
`1,478 / 750 / 86` and the strong contract certifies stationary scale 2.
Input permutation, global proper-SE(3), ideal-IQC, amorphous, and ternary
controls all pass.

This is a hardened crystal baseline, not a pure-port discovery result. The
radix and child-offset vocabulary still comes from the positions-only
stationary grid learner and is subsequently validated against the frozen port
relations. Learning the closure vocabulary from ports alone remains future
work. None of these stronger NaCl results changes the red stationary IQC gate.

Serve the repository root and open `/iqc-growth-live/`.
