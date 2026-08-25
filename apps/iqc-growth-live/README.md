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

The selectable inputs include an exact NaCl rocksalt positive control, a Cu-Zr
metallic-glass negative control, an Al-Cu-Fe icosahedral-approximant surrogate,
the published Cd5.7Yb icosahedral-quasicrystal model, a 30° twisted hBN bilayer,
and a silicon BC8-like network. The hBN fixture is two
intrinsically 2D sheets embedded in 3D, not a thin 3D periodic box.
Element-dependent colors and radii are presentation
encodings, not electron densities or physical potentials.

The live Cd5.7Yb option is a deterministic 506-atom off-centre radius-14 Å
restriction of Feuerbacher's V1.5 published model (article DOI
`10.1107/S2053273326006601`, immutable Zenodo record
`10.5281/zenodo.21470195`, CC-BY-4.0). Its off-centre origin avoids presenting
global icosahedral shell rotations as independent translated motifs. The
browser receives only Cd/Yb species and physical-space Cartesian positions;
source-site names, empty-centre markers, six-dimensional coordinates, and
occupation domains are absent. The receipt pins the article, archive, generator
and normalized 506-atom digest. Selecting this saved example does not provide
its phase label to clustering, marking, or growth.

### Occupational disorder and partial sites

CIF and JSON imports preserve a crystallographic site as one geometric position
with a finite set of element fractions and, when the total occupancy is below
one, an explicit vacancy fraction. Co-located rows such as `Ta 0.6` and `V 0.4`
are merged into one `Ta 60% / V 40%` site after symmetry expansion; they are not
turned into two colliding atoms and are not collapsed to whichever element
appears first. Composite labels without explicit fractions are retained as
equal alternatives and visibly flagged as inferred.

The scene uses the occupancy-weighted element color and adds an orbital ring in
the secondary-element color (or a pale vacancy ring). The legend gives the
fractions explicitly. More importantly, the full canonical occupancy vector is
the colored-site token used by irregular support discovery, port learning,
marking compatibility, structure digests, and weighted-composition receipts.
The finite-molecule hypothesis fails closed on mixed sites because a virtual
occupancy channel has no single covalent radius or valence; those materials use
the generic irregular-cover route instead of silently choosing a species.

Ordinary CIF `_atom_site_U_iso_or_equiv` / `_atom_site_B_iso_or_equiv` columns
and full `_atom_site_aniso_U_ij` / `_atom_site_aniso_B_ij` loops are preserved,
using `B = 8π²U`. Crystallographic tensors are converted through the supplied
cell metric into Cartesian covariance tensors, transported by every symmetry
operation, checked for positive semidefiniteness, and diagonalized into a
right-handed principal-axis frame. A translucent violet wire ellipsoid displays
the two-sigma displacement halo around the arbitrary element glyph; the halo's
axis excess beyond the glyph is the measured 2σ displacement. The isometry tolerance is the largest of the selected
nominal tolerance, the measured one-sigma U/B pair-distance uncertainty
`sqrt(2)·median(sqrt(U))`, and any fixed-topology snapshot pair-distance floor;
the UI and receipt show every source. This broadens
only the comparison of noisy measured geometry. It is not a temperature,
phonon trajectory, force field, Debye–Waller intensity model, or dynamical
growth clock. Modulated/superspace CIFs remain unsupported and must not be
approximated by this ordinary-cell tensor path.

### Recorded measurement conditions

For ordinary CIF input, the lab preserves IUCr core measurement metadata when
present: `_diffrn_ambient_temperature` in kelvins,
`_diffrn_ambient_pressure` in kilopascals, and
`_diffrn_ambient_environment` as text. Deprecated
`_cell_measurement_temperature` and `_cell_measurement_pressure` values are
accepted only as visibly flagged fallbacks. The exact source tag accompanies
each value in the experiment receipt.

These fields label the conditions under which the supplied diffraction or cell
measurement was made. They are provenance, not synthesis conditions, an
equilibrium-state reconstruction, a temperature-dependent potential, pressure
control, elapsed physical time, or an MD thermostat/barostat. The browser shows
them as read-only chips and never feeds them into cluster admission, marking,
tree-search ranking, or growth.

### Fixed-topology snapshot ensembles

Multi-frame extended XYZ and JSON inputs retain up to 64 configurations (and
24,000 total atom presentations in the browser) when
atom count, atom order, species, occupancy, and supplied formal charge remain
identical. The displayed/growth frame is chosen explicitly. A separate control
can pool every retained frame when learning colored pair-distance,
coordination-capacity, and three-body angle envelopes. Distances and angles are
formed only within a frame—frames are never concatenated into one point cloud,
and no cross-frame atom pair exists. Variable cells and per-frame periodic
wrapping are preserved.

For atom pairs lying inside the selected frame's local descriptor cutoff, the
lab also measures each pair distance in every frame. The 90th percentile of
their per-pair sample standard deviations becomes an empirical one-sigma floor
for metric-isometry matching, alongside any supplied U/B displacement floor.
Because this statistic uses only distances, global translation and proper
rotation cannot masquerade as disorder; changing cells and genuine local
deformation remain visible. The floor, cutoff, pair count, and distribution
summary are shown in the clustering control and serialized in the receipt.

The cluster cover, pose atlas, port grammar, GCTS marking, and growth nucleus
still come from the one selected frame. This keeps later snapshots from leaking
candidate placements or becoming simultaneous atoms while allowing thermal or
relaxed configurations to broaden the geometric evidence used by hard
admission and soft strain ranking. The receipt records every frame digest, the
selected index, pooled frame and atom-presentation counts, and this exact
boundary.

This path does not read velocities or forces, integrate equations of motion,
infer elapsed time, or treat correlated frames as statistically independent.
It is ensemble-informed structural geometry, not molecular dynamics or a
kinetic growth-rate model. Reactions, changing atom identity, and trajectories
requiring atom remapping fail closed for now.

## Reproducible experiment receipts

The left rail can download or copy a stage-aware JSON receipt at any point in
an investigation. It records the input provenance and composition, periodic
geometry, inferred translation support, proper-pose atlas, complete cluster
cover, marking configuration and learned coefficients, selected search policy,
clusters² setting, decision counts, and the current explicit-output digest.
Receipts taken before a stage is entered say so rather than serializing stale
state from a later stage.

Atomic coordinates and hidden scoring targets are never embedded in a receipt.
The input and explicit output are represented by order-independent SHA-256
digests; public-database identifiers and cell vectors remain as reproducibility
metadata. `experimentStateSha256` excludes the generation timestamp, so two
exports of an unchanged state have the same experiment identity, while
`receiptSha256` authenticates the complete timestamped record.

The same rail contains a bounded, local **experiment notebook** for rapid
comparison. “Save current run” derives a compact coordinate-free summary from
the full receipt; saving the same `experimentStateSha256` twice selects the
existing entry instead of fabricating a replicate. Up to eight runs may be kept
locally. Selecting two produces a field-by-field comparison of material and
composition, geometry hypothesis, complete cover, marking and representation,
hierarchy/depth, explicit output, branch work, posthoc classification, and claim
boundary. The notebook never restores or executes a run, never stores atom
coordinates, and never substitutes for the downloadable receipt. Clearing it is
a two-click action and does not affect downloaded files or the marking library.

The receipt also carries a machine-readable claim boundary. Finite structural
continuation is not relabelled as a physical potential, elapsed time, growth
rate, stationary production, or generic exponential GCTS result. In
particular, the ice receipt records the executed frozen-anchor waves and safe
fixed point while keeping unresolved proton orientations and stationary growth
explicitly false.

## Environment discovery

The cluster stage exposes the **translation geometry** explicitly. **Auto** tests
translation closure from the positions, **periodic lattice** applies periodic
translations, **aperiodic module** assumes a discrete but non-periodic
pose/translation atlas (the natural model-set or quasicrystal hypothesis), and
**general point set / free SE(3)** makes no discrete translation assumption.
The latter two apply no periodic wrapping. Curated fixtures declare whether their supplied window
is periodically closed; imported structures use their PBC flags. Auto still reports a lattice only
when translation closure is recovered from the positions. This setting changes the displacement geometry used by
descriptors and the complete cover; it is not a preassigned crystal or
quasicrystal label.

The browser still computes boundary-aware radial/angular descriptors for local
diagnostics and order classification, but those atom labels no longer define
the cluster cover. The cover learner receives only species, metric distances,
and the nearest-neighbour scale. It mines two candidate families: recurring
coordination supports and **centre-free bond-lens supports** constructed around
short pairs. A complete coloured pair-distance signature, quantized at `2.5%`
of the measured nearest-neighbour scale, quotients translation, atom order, and
proper rigid isometry. A canonically role-ordered signed-volume token keeps
enantiomorphic supports distinct; symmetric or coplanar cases are reported as
chirality-unresolved instead of receiving an arbitrary hand. Recurring coordination classes are used first; centre-free
classes enter when they are needed to cover atoms that the elementary supports
cannot represent. The tolerance and minimum two-occurrence admission rule are
written into every experiment receipt.

A deterministic set-cover pass selects admitted support occurrences and retains a
second observation of every selected recurring class. Any remaining connected
region is partitioned into bounded explicit gap clusters, grouped only when its
full coloured metric set is isometric. Thus the cover is always audited against
every supplied atom, while a glass or unfamiliar boundary is allowed to remain
literal instead of being forced into a false repeating motif.

Cluster identification is presented as a process over the complete 3D
configuration, not only as a final gallery. Tentative teal connections appear,
locally inconsistent or non-recurrent connections are removed in red, and
family-coloured edges settle into the accepted overlapping cover. A reversible
process timeline is indexed by the frozen decision trace: dragging it rewinds
the connections, coverage, rejection count, captions, and metrics together,
and Play resumes from the selected decision step. It never consults a target
structure or fabricates a dynamical trajectory.

Four clickable evidence tiles explain the selected audit step: newly admitted
hypotheses, accepted versus removed edges, newly covered sites, and one
species/normalized-distance representative. Their detail panel states the
important limitation explicitly: the cover learner is computed first and this
timeline replays its competing edges in a deterministic visual order. It is
not an online optimizer, molecular dynamics, or physical time.

Cover completeness and rigid replay connectivity are audited separately. The
learner first adds recurring Steiner occurrences from already admitted support
classes. If a nearby component still lacks a two-site rigid overlap, it may add
a bounded explicit replay connector, which is removed after known-window
reconstruction and can never become a continuation rule. Components farther
than `2.5a` remain disconnected; the browser does not invent a long nonphysical
edge merely to make the search graph connected.

Every displayed prototype is the actual coloured support selected by that
cover, centred only for rendering. It may be an atomic coordination polyhedron,
an irregular bond-lens polyhedron, a molecule, or an explicit gap terminal.
Each admitted metric-isometry class has its own independently rotating canvas card;
repeated placements do not create duplicate cards and no card is reconstructed
as radial spokes from an artificial central point.

The gallery is also an interactive cover proof. Selecting a card reports the
union of observed atoms covered by that exact class, its occurrence and support
counts, how many covered atoms participate in overlaps, the symmetry-quotiented
proper-pose orbit count, chirality status, connection-port rank, and derived
marking-channel rank. Recurrent supports, reusable gap/void boundary constraints,
and literal residual terminals are visually and semantically separated; a
terminal can certify complete replay but is never silently promoted into a
generative rule.

An expandable **heterogeneous-geometry audit** keeps three roles distinct.
Recurring material supports may become growth actions; recurring gap/void
boundaries may constrain a connection but emit no atoms; literal residuals
close the observed cover and can never become growth rules. The same audit
reports species-local coordination outliers using a median/MAD rule, spatial
contacts between unlike local proper-pose orbits, and explicitly supplied
occupational/vacancy alternatives. These are candidates for inspection, not
automatic vacancy, dislocation, grain, or grain-boundary labels: a finite crop,
surface, molecule orientation, strain, or truncation can generate the same
signals. No defect formation energy, relaxation, mobility, or thermodynamic
preference is inferred. The experiment receipt records the counts, thresholds,
and all of these non-claims without embedding atom coordinates. An interactive
XY/XZ/YZ projection uses the supplied positions only for visualization: mint
sites belong to recurring material supports, amber rings mark reusable void
boundaries, red sites remain literal, blue rings mark unlike-pose contacts,
violet halos flag robust coordination candidates, and diamonds preserve
occupational/vacancy alternatives. Changing the projection cannot alter a
cluster, marking, candidate, or tree-search decision.

The same stage reports how many symmetry-inequivalent orientations of every
cluster are actually needed to cover the observation. It constructs intrinsic
right-handed frames from the complete element-coloured cluster geometry and
retains every tied frame as a proper-symmetry gauge. Pose distance is minimized
over those gauges, so a translation or arbitrary common proper rotation of the
whole sample cannot change the orbit count; reflections are never included in
the quotient. Proper self-symmetries of a cluster therefore collapse: the Na and Cl
octahedra in periodic rocksalt each require one physical pose, even though one
may write many equivalent local frames for an octahedron. Removing periodic
wrapping exposes boundary environment types and their larger pose atlas. If
the sampled orientations do not close into a stable finite atlas, the UI marks
that cluster type as equivariant `SO(2)` / `SO(3)` (or as an axial stabilizer
for a collinear support) and reports the number sampled rather than
pretending those samples are a finite set of allowed rotations. A finite pose
orbit is called *required* only when every symmetry-quotiented pose has at
least two observed occurrences; sparse one-off poses are shown as unresolved
and reserve model capacity without becoming a geometric law.

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
For molecular covers, the port rank includes the dependency-ordered observed
replay graph as well as reusable continuation rules. Ice therefore inherits
the actual H2O, water-dimer, and O6 void-boundary pose/port atlas rather than
falling back to atom-centred oxygen environments.

## Chemistry encoded as hard geometry

The live executor no longer applies one universal collision radius to H–O,
Na–Cl, Cu–Zr, and like-species pairs. Before clustering, it learns one colored
distance envelope for every observed unordered species pair. Each atom
contributes its nearest neighbor of the requested species; the lower contact
tail and median are retained for audit, while the hard exclusion is chosen
strictly below the shortest supplied contact. The original configuration is
therefore admissible by construction. Unknown pairs fail back to the declared
generic exclusion rather than receiving an invented chemical bond.

These pair envelopes are used both when a cluster is attached to the occupied
frontier and when several commuting cluster actions are considered in one
antichain. Same-species sites merge only inside the much tighter positional
tolerance; a different species at the same position is always a conflict.
Internal bond lengths and angles are transported exactly with each learned
rigid cluster prototype, so accepted growth must satisfy both the whole-cluster
shape and its colored exterior exclusions. The input-stage inspector lists the
observed contact and learned hard limit in ångströms, and the complete table and
fit fractions are serialized in the experiment receipt.

The same contacts define **ordered coordination capacities**. O→H and H→O are
separate statistics, so an H2O sample can learn two covalent hydrogens around
oxygen while allowing only one covalent oxygen around each hydrogen; rocksalt
likewise learns six unlike first-shell neighbors. The executor enforces only
the maximum coordination observed anywhere in training. It never requires a
frontier atom to have reached its final lower coordination, because later
cluster actions may legitimately complete that shell. A simultaneous batch is
checked as a union before commitment, making saturation independent of the
permutation in which its commuting placements are displayed.

The third layer is a **colored three-body angular envelope**. For every central
species and unordered pair of contact-neighbor species, the input supplies the
observed angle modes. Separated modes remain separate: rocksalt can retain its
90° and 180° octahedral bands without silently admitting every angle between
them, while bent H-O-H, tetrahedral O-O-O, and planar sp2 environments receive
their own colored bands. Every observed band is padded by a declared tolerance,
so the supplied structure remains admissible. During growth the rule is tested
only when both neighbors are already present; an incomplete frontier is never
rejected for a missing angle. Whole commuting batches are checked together, so
two individually plausible attachments cannot jointly create an impossible
three-body arrangement.

Hard admissibility still leaves several legal frontier actions. The executor
therefore computes a dimensionless **geometric strain** from the same frozen
colored contact and angle statistics and uses it only as a small, target-blind
ranking term over the already enumerated exact actions. The score reports
distance and angle components separately in the live decision inspector and
receipt. It cannot create a pose, rescue a hard violation, or reject an action;
candidate identity and the collision/coordination/angle certificates are
unchanged. This deliberately encodes the preference for familiar low-distortion
local geometry without calling the score an energy, force, probability, or
elapsed-time model. Stage 4 exposes an explicit off/strain selector and weak,
balanced, and strong weights. Changing it restarts the same frozen search
experiment, so marking-only and strain-assisted orderings can be compared
without changing the cluster or port vocabulary.

For multicomponent growth, the sample also defines a reduced **composition
reservoir** with no binary-system assumption. Each candidate reports how its
unique new sites change the total-variation distance between the live and
observed element fractions. A soft Stage-4 selector can favor actions that
reduce that drift, or it can be disabled while retaining the diagnostic. The
term is size-scaled so it remains visible as the solid grows, but it is never a
hard constraint: a finite surface, nucleus, defect, or temporarily incomplete
frontier may depart from bulk stoichiometry. No chemical potential or elemental
feed rate is inferred.

When an imported CIF or JSON structure explicitly supplies oxidation states,
the browser preserves them per occupational alternative: Fe2+ and Fe3+ remain
distinct colored chemistry channels, and a mixed-valence site retains its
occupancy-weighted formal charge. A separate optional **formal-charge reservoir**
reports whether an unchanged candidate action moves the frontier's
mean supplied formal charge toward or away from the reference configuration.
It is soft ranking only and fails closed at zero weight unless every occupied
site has a resolved charge. The app never guesses common oxidation states from
element names. This bookkeeping is not charge density, Coulomb or Madelung
energy, dielectric screening, redox chemistry, electron transfer, a potential,
or a chemical potential; charged surfaces and intermediate fronts remain
admissible.

A separate optional **surface-completion** term measures the remaining ordered
species coordination deficit relative to the sample median. For each proposed
whole-cluster action it compares already occupied frontier centers before and
after attachment, then combines the coordination healed on those centers with
the residual deficit introduced by the new sites. Lower is preferred. This is
the geometric analogue of favoring fewer dangling or unsatisfied contacts, but
it is deliberately not called bond energy or surface energy: there are no bond
orders, inferred oxidation states, electronic chemical potentials, or energetic
units.
It never rejects an undercoordinated surface and can be disabled independently.
Balanced and strong modes rank the same frozen candidate set; the live
inspector and receipt report new-site deficit, healed existing deficit, weight,
and accepted/rejected means.

All pair, capacity, angle, and strain evaluations are compiled to the exact
finite-reach neighborhood affected by the proposed fresh sites. The live
spatial index finds existing centers touched by the action and then gathers
their complete learned contact neighborhoods; no atom outside the maximum
learned contact reach can contribute to these local terms. This changes the
work from a whole-solid scan per candidate to a bounded local query without
sampling or changing the result. Receipts report evaluation count, mean and
maximum projected neighborhood size, full live size, and physical reach.

This is chemistry-as-geometry, not a pair potential: it has no attractive
well, angular energy, charge, bond order, temperature, pressure, or kinetics. Those effects
can constrain which clusters and ports are observed in the sample, but the
browser leapfrogs their dynamical trajectories and preserves only the learned
geometric admissibility envelope.

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

GCTS learning deliberately changes the visual grammar. Each learned cluster or
gap class receives its own rotating 3D scene, and its local connection/failure
level sets morph from the random initialization toward the fitted section. The
same reversible timeline is now indexed by processed section samples, so a
materials scientist can compare intermediate halos across cluster classes,
rewind to any fit state, and resume training from that sample count. The
timeline state is included in the coordinate-free experiment receipt.
At every sample the synchronized evidence tiles distinguish fit from held-out
occurrences, name the affected cluster section, report the coordinate-free
coefficient update norm, and show the held-out-loss change. Clicking a tile
expands its interpretation and repeats the non-potential, non-dynamics claim
boundary.

The representation selector now changes the mathematical readout, not only its
label. Port vectors compare the two directed endpoint sections. Site-resolved
sections emphasize the least compatible colored site; local halos blend the
endpoint and support mean; whole-action readout emphasizes the mean over the
entire frozen child template. The chiral halo adds a learned connection-class
preference for a colored pseudoscalar constructed from the parent translation
and canonically tokenized child-site pairs. That pseudoscalar is invariant under
translation, proper rotation, and atom insertion order, and changes sign under a
mirror. Symmetry-degenerate equal-token pairs contribute nothing. These
readouts rank the same frozen rigid candidates and never authorize new geometry.
Their definition and learned chiral class means are included in receipts and
saved marking-library entries.

The molecular path uses one section sample per cover occurrence. In ice Ih
that means `72` H2O, `144` bridge, and `180` void-boundary samples (`396`
total). Stage three renders those same three Stage-two prototypes with their
connection/failure halos; it does not reintroduce the radial spoke view or a
whole-crystal scene. The observed gap-boundary port incidence raises the
automatic shared tensor from three to six channels while unused channels stay
masked on the lower-rank molecule and bridge types.

A completed fit can be frozen into the browser's marking library. Each entry
retains its material, geometric-support hypothesis, configuration,
coefficients, sample count, and held-out loss. A lattice-trained marking is not
offered under the aperiodic-module or free-`SE(3)` hypotheses. The growth stage
can select any compatible saved marking, the unmarked
colored-action baseline, or the exact-local-oracle diagnostic ceiling. “Train a
different marking” returns to stage three without deleting earlier entries.
Compatibility is stricter than a material-name match: a versioned fingerprint
must agree on reduced composition, resolved translation support, invariant
prototype geometry, proper-pose status, and pose-by-port rank. This prevents a
saved section from being silently applied after the cluster vocabulary changes
while still allowing multiple independently trained sections for the same
frozen geometry.

## Off-lattice search

### External geometry as a hard public boundary

The input rail distinguishes six target-independent growth experiments: a
finite bulk window, spherical nucleus, cylindrical nanowire/pore, free-standing
slab, film above an impenetrable support plane, and a constricted pore/neck.
One shared analytic domain definition drives both the wireframe rendering and
the candidate-admission test, so the picture cannot silently disagree with the
tree search. Dimensions are serialized in scene units and ångströms.

These boundaries can study morphology and frontier accessibility, but they do
not invent wall atoms or interactions. In particular, the supported-film mode
models only excluded geometry: it supplies no epitaxial registry, adhesion,
surface or interface energy, pressure field, periodic image, or substrate
chemistry. The receipt records those claim boundaries alongside the exact
domain parameters.

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

Every live tree decision now carries a geometry-as-physics ledger. Hard
admission rows report colored minimum-distance exclusion, whole-cluster shared
support, novel-site emission, public-domain containment, species-resolved
coordination capacity, colored angular envelopes, and transported GCTS-marking
compatibility. Elastic mismatch, composition-reservoir balance, and surface
completion are shown separately as ranking terms with their active weights;
when disabled they remain diagnostic and explicitly cannot authorize geometry.
Rejected stack rows say `prune` and the failed row turns red—for example, a
geometrically coincident proposal fails `novel colored sites` as a duplicate
cover even when every other constraint passes. This makes the physics proxy,
search logic, and claim boundary inspectable action by action.

Each ledger tile is interactive. Its expanded record separates four things a
materials scientist should not have to infer from a color alone: the observed
position/species evidence, the frozen geometric surrogate, whether it is a hard
admission gate or a soft ordering term, and the physical claim boundary. Thus a
coordination cap exposes its center-observation count and species channel,
whereas the elastic proxy explicitly reports that its dimensionless residual is
not a modulus, stress, force, or phonon calculation. Formal-charge bookkeeping
fails closed when oxidation-state coverage is incomplete. The selected record
updates with each tree decision without turning any diagnostic into an energy.

The growth controls also display a counterfactual frontier table computed from
the same already-enumerated, hard-admitted candidate set. It reports the top
action under marking/recurrence alone, balanced elastic mismatch, composition
balance, surface completion, and the currently active combined policy. The
candidate count and number of distinct winners expose whether the soft physics
proxies actually change the next action. During reconstruction the table says
`target-aware replay`; after the one-to-one known-window certificate it says
`target-blind frontier`. The specialized ice executor instead states that its
orientation-domain rule is used and the generic rankers are not.

Each policy row is also an interactive counterfactual: clicking it previews the
winning whole-cluster pose in the 3D scene without executing the action or
changing the atoms, frontier, or search state. A bounded history strip records
how often recent frozen frontiers produce more than one winner and lets the user
revisit any disagreement. The experiment receipt serializes only candidate-set
and selected-candidate digests, policy labels, actions, and scores—never preview
coordinates. Candidate enumeration is always target-free; the receipt separately
records whether the ranking itself still used known-window reconstruction evidence.

The right-hand inspector adds a live **multiscale geometry passport**. Its five
interactive levels report the measured nearest-neighbour distance and colored
contact evidence; learned cluster/void support diameters; GCTS channel count and
neighborhood reach; current frontier size, hierarchy mode, and causal depth; and
the thermodynamic/kinetic boundary. Each level uses the same four-part audit as
the constraint ledger—observed evidence, geometric encoding, role in search, and
claim boundary—and updates with the selected material and pipeline stage. The
receipt preserves the passport without atom or preview coordinates. Recorded
temperature, pressure, or environment metadata appears only in the open kinetics
level and is never promoted into an uncalibrated simulation control.

The live **growth certificate** keeps four layers separate while the animation
runs: exact replay of the supplied window, outside-window structural output,
causal self-feed / hierarchy depth, and the strongest claim actually supported.
For generic output, “target-blind structural site” means the frozen geometry and
collision certificates passed; it does not mean an unopened physical target
was matched. Ice reports its sealed backend parity and finite fixed point, but
keeps proton orientations and stationary recurrence open. A separately green
NaCl stationary benchmark is likewise not relabelled as physical elapsed time
in the viewport. The same structured certificate is embedded in experiment
receipts.

The adjacent **structural leap certificate** explains what one visible update
actually means. It records the explicit atom/cluster state before the update,
the immutable whole-cluster candidate batch, shared and proposed-new colored
sites, the hard geometric tests applied before commitment, and the explicit
state afterward. Recent leap cards are selectable, and the same target-free
records are serialized into the experiment receipt. A commuting update is one
order-independent antichain over the underlying tree; it is not a
molecular-dynamics time step. Every record therefore freezes `targetUsed=false`,
`dynamicsIntegrated=false`, and `physicalTimeModeled=false`, with a material-
specific statement of the omitted relaxation, diffusion, barrier, entropy, or
rate claim. A frontier exhaustion is reported as a finite structural fixed
point—not equilibrium.

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

Tree-search scheduling is an explicit growth-stage ablation. The default visual
update is a maximal greedy **commuting frontier set**, not one search move or an
arbitrary fixed-size animation batch. Candidates are drawn from the same
frontier snapshot. A placement joins the displayed set only when every
cross-placement site is either safely separated or a coincident atom of the
same species, and every placement retains at least one new site not supplied by
another member. These monotone local checks make all permutations of the
displayed placements admissible. Serial best-first mode instead executes one
ranked branch decision per update, making branch order directly inspectable.
Both modes use the identical rigid candidate geometry and dependency-ordered
tree; scheduling changes execution/display order, not what actions exist. The
selected mode and this no-geometry-change invariant are serialized in the
experiment receipt.

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

The real/reciprocal-space and coordination-number charts compare the known
configuration with the explicit atoms produced by search. The RDF is dimension aware: planar
materials use annular area normalization and three-dimensional systems use
spherical shells. Periodic windows use minimum-image distances only inside the
inscribed half-cell radius; open windows use a translation edge correction.
The element-pair selector exposes total and partial distributions such as
Cu–Cu, Cu–Zr, and Zr–Zr. Its tail readout reports both mean `g(r)` and RMS
departure from unity. An amorphous solid is therefore expected to have strong
short-range peaks and approach `g(r)=1` at long range—not to be flat at every
radius. Beyond 216 atoms, the live chart uses a contiguous 216-atom central
window. Coordination bins remain interactive and highlight every matching
center, all current neighbors, and their connecting segments.

The same card can switch to a finite-observation geometric powder structure
factor. It evaluates the Debye pair sum with `sin(qr)/(qr)` in 3D and the
correct `J0(qr)` orientational kernel for intrinsically 2D materials. The
2D distance is projected into a proper intrinsic plane inferred from the point
cloud, so a rigid embedding in 3D does not change the curve. The wave-number
axis is normalized as `qa`, using the measured nearest-neighbour
scale. Unit scattering weights make this a species-neutral geometry audit:
there are no X-ray form factors, neutron scattering lengths, occupancies,
Debye–Waller factors, or instrument broadening, so the curve must not be read
as an experimental diffraction intensity. The glass control has a broad first
maximum and returns toward `S(q)=1` at high q; periodic and quasiperiodic
fixtures retain sharper reciprocal peaks. Numerical regression compares an
equal-size hard-core glass with 3D cubic and 2D hexagonal positive controls.

The deterministic Cu₆₄Zr₃₆ control no longer starts from a jittered cubic grid.
It begins from continuous random positions in a periodic box and applies only
species-dependent hard-core relaxation before rescaling the measured median
nearest-neighbour distance to 2.72 Å. The generator uses neither a target RDF
nor lattice sites; its seed, composition, minimum distance, cell length, and
negative provenance flags are exported in the experiment receipt. It is still
a structural packing surrogate rather than a quenched MD trajectory.

The live order panel stays explicitly unclassified throughout input, cluster
identification, and GCTS learning. Only after Material Growth begins does it
classify the generated geometry, without feeding a structure label back to
growth. It compares RDF, coordination, and geometric powder
`S(q)` evidence against a
small prototype library and reports a provisional crystal, quasicrystal, or
amorphous interpretation. This remains a posthoc prototype match, not an
independent phase determination. A publishable evaluator still needs `spglib`
or a fully certified translation analysis for crystals, indexed reciprocal
modules and experimental diffraction for quasicrystals, and chemically
weighted scattering plus local-motif tests for glasses.

The order card now keeps the inference auditable as growth proceeds. It plots
confidence against the live atom count, shows the contiguous analysis-window
size, the evidence margin between the best and second-best prototypes, and the
independently computed translation-closure score. The 58% provisional decision
threshold, 32-atom minimum, RDF/coordination/geometric-`S(q)` weights, component
errors, prototype-library self-reference flag, and the complete bounded
confidence history are written to the experiment receipt. The receipt also
states mechanically that classification is posthoc, embeds no coordinates,
and is used by neither candidate admission nor branch ranking. In particular,
a curated fixture may also appear in the diagnostic prototype library; this is
reported rather than hidden and prevents the panel from being mistaken for an
independent phase determination. Translation closure may establish a periodic
crystal before the local prototype scores separate, but it then reports the
point group and prototype as unresolved: a tied or under-supported numerical
leader is never promoted into a material name.

Finite nuclei are compared fairly rather than against full-cell statistics.
For every read, the browser selects a translation-invariant window around the
point-cloud centroid, truncates every prototype to the same atom count, and
uses one shared RDF cutoff in nearest-neighbour units. Intrinsic 2D versus 3D
normalization is inferred from the global and median local covariance spectra
of the positions, so a finite multilayer remains locally 2D without pretending
that its total thickness is zero; the curated material dimension is not
consulted. A fourth readout repeats the
ranking after removing the selected fixture from the prototype library. This
leave-one-out value is a transfer diagnostic, not a second vote secretly used
to change the displayed classification. All window, dimension, cutoff, and
leave-one-out fields are preserved in the receipt.

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
its element-labelled coordinates to the learner. The browser no longer carries
a hidden `molecularCover: water` switch: it first infers a valence-bounded
covalent graph from standard element radii, requires repeated finite connected
components, and rejects extended covalent networks back to the irregular-cover
learner. Only after the recurring colored metric formula emerges as H2O does
the water-specific connection/void topology run. Stage 2 displays this
hypothesis audit for every material: accepted component counts/formulas and
zero-label provenance, an extended-network rejection, or the exact missing
chemistry metadata that caused a safe irregular-cover fallback. A new generic ice audit uses
standard covalent radii and bounded ordinary valences to infer finite connected
components, without receiving an ice label, H2O formula, coordination number,
or ring size. It discovers one H2O type in both polytypes, constructs the
nearest-shell component graph, and promotes its locally shortest chordless
cycles to oxygen-ring gap boundaries. The live
gallery renders the H2O bent molecular face, the complete water-dimer
connection polyhedron, and the ordered six-oxygen void-boundary polyhedron;
it never substitutes radial centre-to-neighbor spokes for cluster topology.
The browser's strict colored complete-metric gallery shows every class in the
observed periodic window: `1 / 3 / 33` H2O / bridge / O6-boundary classes for
Ih and `1 / 2 / 39` for Ic. GCTS marking deliberately compresses those cards
back to three connection families (molecule, bridge, ring boundary), so proton
decoration does not become dozens of arbitrary channels. The gallery toolbar
filters those families without merging or renumbering the
underlying isometry classes. Every card reports its colored support size,
occurrence multiplicity, observed proper-pose count, connection-port rank, and
cover role. The toolbar also carries a three-layer cover ledger. Its molecular layer
states the literal atom accounting (`72 H2O → 216 / 216 atoms` for Ih); its
bridge and void layers state connection and empty-region boundary accounting
separately. Clicking a layer filters the exact cards. This avoids implying
that the auxiliary polyhedra repair missing atoms: H2O already closes the atom
cover, while the auxiliary clusters close the geometry needed for attachment
and traversal.

Two published diffraction controls now make the occupancy boundary explicit.
COD 1566658 is proton-ordered ice VIII: its fully occupied O/D coordinates
must rediscover one D2O molecular class, water-pair connections, and O6
empty-region boundaries. COD 1567346 is proton-disordered ice VI: the `2×2×2`
average structure contains 80 fully occupied O sites and 320 candidate D sites
at occupancy one half, or 240 occupancy-weighted atoms. Those 400 average sites
are rendered with D/vacancy rings and enter the irregular colored-support
learner without being collapsed to D. The fully occupied oxygen framework also
supplies 80 shortest chordless O4 empty-region boundaries in two exact metric
classes. Because the average coordinates do not select two D sites around each
oxygen, the finite-molecule hypothesis, tree search, and post-growth phase
classification fail closed. This is an occupancy-ambiguity control, not a
claim that D2O ceases to be the physical local molecule.

Ice VI also exposes an explicit opt-in realization step. From geometry alone,
the browser pairs the two half-occupied D alternatives on every O--O bond,
builds the measured four-connected oxygen graph, and orients each closed Euler
circuit. Selecting the donor-side D on every oriented edge yields exactly one
D per O--O bond and two covalent D per oxygen: 80 O + 160 D = 240 realized
atoms on two interpenetrating networks. A seed makes the choice reproducible;
another click samples a different valid orientation. Only after this choice
does the ordinary molecular pipeline rediscover one D2O topology (with six
measured metric conformers retained as pose subtypes), hydrogen-bond connection
polyhedra, and the two O4 gap classes. It does not retain the generic O6 family
alongside those shortest Ice-VI voids, so the gallery does not double-count
empty space.
The receipt records the seed, method, both ice-rule checks, and that neither an
energy nor a target score selected the microstate. This is one valid
instantaneous realization, not a claim that diffraction determined it or that
all occupational states are equiprobable.

A separate sealed cross-microstate audit now tests what that geometry can
actually continue. One 123-molecule training crop learns five recurring D2O
metric conformers and 84 directed proper-SE(3) ports. Three training-side
microstates select a minimum of two independent parent-port witnesses at
23/24 precision (95.8%). The frozen grammar then receives a spatially disjoint
23-molecule nucleus from a fifth microstate; only after its candidate traces
are frozen is the 134-molecule outer crop opened. It emits `4 → 3 → 1` oxygen
anchors in three self-fed waves, all `8/8` exact. Every associated D2O pose
remains a mutually exclusive hypothesis, and forcing whole molecules yields
18 correct plus 3 wrong atomic sites. This is finite oxygen-framework
continuation—not occupational prediction, kinetics, stationarity, or an
exponential ice rule.

Cluster identification now exposes its colored metric-isometry tolerance as a
stage-local scientific control: strict `1.0%`, balanced `2.5%`, or thermally
broadened `5.0%` of the observed nearest-neighbor distance. The selected value
is applied consistently to finite-molecule signatures, intermolecular
connection and void classes, and generic irregular-support signatures. It does
not change hard-core exclusion or authorize an unseen pose. Changing it reruns
clustering and the downstream pose/port atlas, so the scientist can inspect
whether a vocabulary fragments under strict matching or collapses only under a
broadened experimental tolerance. Receipts store the named mode, dimensionless
fraction, and resulting ångström tolerance.

The same front end now has a non-water molecular-crystal control: a saved
`3×3×3` low-pressure cubic CO2-I (`Pa-3`) window containing 108 linear CO2
molecules and 324 atoms. The fixture supplies only C/O positions and species.
The generic learner rediscovers 108 finite CO2 components, then constructs a
nearest-component connection graph and promotes locally shortest chordless
cycles as void-boundary clusters. In the current deterministic window that is
`1 / 1 / 1` molecule / connection / void class with complete `324 / 324` atom
cover. No CO2 formula, expected ring size, material name, or space-group label
enters clustering. This control demonstrates that the molecule–connection–void
ledger is not an ice-only branch; autonomous dry-ice continuation remains an
open gate. The fixture geometry follows the phase-I body-diagonal molecular
model and reported `a = 5.578 Å` and `C–O = 1.168 Å` measurements.

The browser control also traverses this generic cover end to end. From one
three-atom CO2 seed, 94 deterministic tree decisions produce 95 rigid
placements at causal depth 14 and reconstruct `324 / 324` known colored sites
with no missing, duplicate, or extraneous atoms. The learned observed frontier
then reaches a fixed point without emitting an outside-window site. The live
certificate labels this as target-aware known-window replay: it proves that the
generic molecular grammar is executable and self-feeding within the observed
periodic sample, but it is not autonomous continuation or a growth-rate claim.

The complementary generic headless gate finds one transferable
six-member void family. Its underlying
tree actions reconstruct 216/216 and 192/192 sites in six visible commuting
waves with zero backtracking. The narrower directional hydrogen-bond cover is
retained as a visualization/control ablation. The executable regressions are
`scripts/test_materials_gcts_generic_ice_benchmark.py` and
`scripts/test_materials_gcts_ice_cover.py`. These certify reconstruction of
the known windows.

The next sealed gate now separates molecular placement from proton decoration.
A physically valid fixture first enforces both Bernal–Fowler rules: every
oxygen has two covalent hydrogens and every tetrahedral O–O connection carries
exactly one proton. An 8-port proper-SE(3) grammar is then learned on one finite Ih window. Before the
outer target is opened, a disjoint nine-molecule seed emits one factored oxygen
frontier: all 16 anchors are exact. Applying the same frozen grammar to cubic
ice gives 12/12 exact anchors without refitting. Whole-H2O execution commits an
orientation too early (65.8% atom precision on Ih), while keeping orientations
as mutually exclusive alternatives preserves the exact first scaffold. At the
second self-fed wave those alternatives are still unresolved: Ih is 52/77 and
Ic is 36/64 correct oxygen anchors. Therefore the app reports exact blind
first-frontier transfer. A stricter branch-domain rule now requires a proposed
anchor to be generated by every surviving orientation of at least one parent.
On Ih that rule keeps the 16/16 first wave, adds a second 8/8 exact wave, then
stops at a safe fixed point; on Ic it keeps 12/12 and rejects all unsupported
depth-two anchors. This proves two exact unseen anchor levels on Ih without
turning unresolved proton alternatives into simultaneous atoms. Full H2O,
stationary, cluster-of-clusters, and exponential ice growth remain red. The
remaining object is a bounded local proton-orientation connection marking
obeying the already learned ports.

The live Stage 4 now executes that finite certificate rather than replaying
hard-coded output coordinates. It loads a target-free artifact containing the
learned H2O prototype, two proper self-symmetries, eight recurrent ports, and
disjoint seed poses; the browser independently recomputes `16 -> 8 -> 0` for
Ih and `12 -> 0` for Ih-to-Ic transfer. Only shared oxygen atoms are drawn.
Hydrogen orientations remain mutually exclusive symbolic branches, target
calls stay at zero, and clusters-of-clusters is disabled because no stationary
ice production has been certified.

The interactive Evidence Atlas now treats molecular ice as a first-class
benchmark beside NaCl, ideal IQC, Cd-Yb, and glass. Its plotted frontier counts
are produced by executing the same frozen browser artifact rather than by
reading the artifact's expected-count audit fields. The system card separates
complete molecular cover, target-free port fitting, exact finite anchor
transfer, and the unresolved proton/stationarity boundary. Buttons link the
evidence directly to the 37-card Ih cluster gallery, the Ih anchor trace, and
the Ih-to-Ic transfer trace.

A dedicated Physics Map makes the structural-surrogate assumption auditable.
Five interactive layers trace bonding and coordination, orientation and
chirality, long-range order, voids and defects, and thermodynamics/kinetics
from physical content through its geometric encoding to its actual effect on
tree search. Each layer ends with an explicit non-claim and compares NaCl,
ice, ideal IQC, published Cd-Yb, and glass. In particular, the map distinguishes
an exact ice-rule-compatible oxygen scaffold from unresolved proton barriers
and orientational entropy, and distinguishes symbolic action compression from
physical elapsed time, phase stability, or a growth-rate prediction.

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

That first port control is now explicit rather than inferred from scalar
completion. The exact matcher retains the occupied atom set supporting each
candidate-centred partial cluster, then exposes only permutation-invariant
pair summaries: minimum/mean/maximum shared occupied atoms and the number of
connected action pairs. The value model never receives those atom indices.
Nested selection uses the incidence representation in two folds, but remains
`17 / 20` exact and falls to `54 / 60` correct moves. Hence a count of shared
support is also insufficient; the next useful object must retain the typed,
oriented port-incidence graph rather than collapsing it to four scalars.

That graph is now implemented. Nodes retain recurrent irregular-support type,
action chemistry, partial coverage, and independent-nucleus support. Edges
retain the colored shared-site multiset, normalized action separation, both
endpoint-to-interface distance profiles, and a signed local volume only when
the endpoint and shared-site roles resolve its symmetry. Canonicalization is
invariant to atom/action permutation and arbitrary proper SE(3), while a
reflection flips the certified chirality bit. A finite value table backs off
from exact graph to typed nodes, then port geometry, then the train prior.
Despite retaining the desired GCTS object, grouped inner selection chooses it
in zero of five folds: best exact-group counts are
`23 / 25`, `24 / 26`, `16 / 25`, `20 / 26`, and `24 / 25`. Exact categorical
graph identity is too sparse. The next justified value is a continuous graph
kernel or bounded message-passing section over these same certified nodes and
edges—not another looser geometry generator.

That continuous control is now measured. It uses optimal assignment between
the certified typed nodes and ports, with support-type weights `0 / .25 / 1`,
node/edge weights `(1,.5) / (1,1) / (.5,1)`, and neighbors
`1 / 3 / 5 / 9 / 15 / 25` selected strictly inside each outer fold. The
continuous kernel is preferred over both scalar completion and categorical
port tables in folds 1 and 2, demonstrating transferable similarity beyond
exact graph identity. On the sealed outer groups, however, the combined
selector remains `17 / 20` exact and `54 / 60` correct from `18 / 20` supply.
The proper-SE(3) graph representation is retained as a research control, not
promoted into the default marking library, and the reserved confirmation
nucleus remains unopened.

A bounded message-passing section is the next stricter control. Initial node
states contain action chemistry, partial-support completion, support size, and
independent-nucleus evidence; certified ports transport shared chemistry,
normalized separation/profile moments, and symmetry-resolved chirality for at
most two rounds. Node and edge order, global pose, coordinates, action IDs,
and target labels are absent. Nested choices cover depths `1 / 2`, support-ID
weights `0 / .25 / 1`, and the same six neighbor counts. All five folds select
one round, with inner exact counts `23 / 25`, `24 / 26`, `22 / 25`, `22 / 26`,
and `24 / 25`. It is strictly preferred in zero folds, so the outer result and
red confirmation gate are unchanged. This rejects the present fixed encoder;
it does not reject a train-learned equivariant message function.

That learned readout has now been tested. A class-balanced ridge-logistic head
fits the sparse one- or two-round node/port messages, with depth, support-type
weight, and ridge strength selected only inside each outer fold. It may replace
the established terminal value only after a strict inner exact-path win. Every
fold selects one round; folds 1 and 2 admit the learned head. The replacement
then falls from the established `17 / 20` to `16 / 20` exact terminals while
remaining at `54 / 60` correct moves. The learned head alone is `15 / 20` and
`53 / 60`; against 31 within-nucleus label shuffles its integrated exact-path
plus-one p-value is `.375`. Candidate geometry and certificates are unchanged,
and no new value-model confirmation is opened. This rules out a scalar linear
readout of the present bounded messages; a useful learned section must update
the equivariant messages themselves or preserve a higher-order graph object.

The higher-order graph is now explicit. Every action pair is represented in a
canonical complete incidence graph: observed overlap/connection edges retain
their shared colored geometry, while absent connections remain typed failure
edges rather than disappearing. A group-balanced pairwise ridge model learns
invariant source × port × neighbor interactions on that graph. It cannot
replace candidate geometry or the established value; inside each immutable
candidate set its percentile rank is only a bounded correction to the scalar
section. Representation, scalar neighbor count, and graph weight are selected
by true leave-one-nucleus-out fits inside each outer fold. Folds 0–2 pass the
strict inner replacement rule. The sealed development aggregate reaches
`18 / 20` exact terminals and `56 / 60` correct moves from the same `18 / 20`
supply, passing the predeclared performance threshold. However, 2 of 31
within-nucleus graph-label shuffles also reach `18 / 20` (`p = .09375`;
correct-move `p = .21875`). This is the best generic terminal value so far,
but the causal marking gate remains red and no fresh confirmation is opened.

That policy has now been tested unchanged on a preregistered extension rather
than tuned again on the original 20 cases. Before any new seed was generated,
the exact recursive connection table, 53-support irregular vocabulary,
pose/port state model, four portfolio branch heads, scalar section, and
equivariant graph weights were migrated from temporary checkpoints into a
2.4 MB explicit compressed-JSON artifact. The artifact reproduces model digest
`505b6548…`, rejects mutation, and loads under both Python 3.9 and 3.12. A
second published manifest froze ten mutually disjoint centres and all source
hashes. After seed-only execution, a third published receipt fixed eight
terminal branches and the scalar/fusion order for every centre before any
outer crop was opened.

The one-shot radius-9 → radius-14.5623 result is `6 / 10` exact selected
terminals and `23 / 30` correct sites for both scalar and fused values. Fusion
changes the selected terminal on five nuclei but changes no correctness
outcome. More importantly, the immutable candidate set contains no exact
terminal in four nuclei; the six supplied nuclei are all ranked correctly at
one. Thus the larger batch validates transfer of the frozen policy but gives
no incremental fusion advantage. Candidate supply—generating a correct
three-action branch in all local environments—is now the measured bottleneck.
This is additional development evidence, not a fresh confirmation, sustained
growth, stationarity, or an exponential certificate.

A complete-frontier audit now separates the missing geometry from value
selection. It keeps the frozen pose/port grammar and marking unchanged, removes
beam truncation one stage at a time, and freezes every candidate and both
orders before reopening the already-consumed targets. Keeping all final states
or all second-depth states leaves exact supply at `6 / 10`; keeping every root
state raises it to `9 / 10`. The complete bounded `8 -> 8 -> 8` tree contains
an exact three-action terminal in `10 / 10` nuclei, among `120–136` terminals
per nucleus. Exact scalar ranks are at most nine and exact fusion ranks at most
fifteen. A generic target-free dual-rank portfolio therefore retains the first
nine states from each order—at most eighteen unique terminals—and preserves
complete supply. Top-one selection is not solved: scalar chooses `2 / 10`
exact terminals and fusion `6 / 10` (`22 / 30` versus `23 / 30` correct
sites). This consumed-development result fixes the candidate-supply diagnosis;
it does not constitute a new confirmation, transferable value win,
stationarity, or exponential growth.

That widened policy has now passed a fresh spatial confirmation. Before any new
atom was generated, a geometry-only manifest fixed centre
`(-110, -10, -10)`, lift bound 60, the complete `8 -> 8 -> 8` search, source
hashes, dual budget nine, and one target-open rule. A separately committed
zero-target receipt then froze a 473-atom seed, candidate counts
`8 -> 37 -> 128`, every terminal action and both rank orders, and eighteen
rollback states. The radius-14.5623 target was opened once afterward and is
identical at lift bounds 60 and 61. It contains 2,048 atoms, 1,575 outside the
seed. Posthoc, `90 / 128` terminal branches are exact; scalar rank one and
fusion rank one are both exact `3 / 3`, and the dual portfolio contains exact
branches. This confirms finite candidate supply and portfolio retention on a
new atom-domain-disjoint nucleus. One finite three-action confirmation is not
sustained continuation, stationarity, or exponential IQC growth.

The confirmed fusion top-one branch was then used exactly as selected—without
consulting its target—to seed a second complete block at the same nucleus. A
published manifest fixed the enlarged public radius to
`14.5623 + 9 = 23.5623`; a second zero-target receipt reconstructed the unique
three-action branch, froze its 476-atom colored configuration, and serialized
another `8 -> 37 -> 128` tree plus an eleven-state dual portfolio. Only then
was the 8,684-atom outer target opened once at lift bounds 72 and 73. The crops
agree. Candidate geometry is not the limitation: `62 / 128` second-block
terminals are exactly color-correct. Transfer of terminal value is red:
scalar and fusion first-exact ranks are 13 and 16, neither top-one terminal is
exact (`2 / 3` sites each), and the frozen portfolio misses every exact state.
Thus the generic grammar supplies a valid continuation after self-feed, but it
does not autonomously choose six exact actions. Stationarity and exponential
IQC growth remain unclaimed.

A post-self-feed value is now trained only on second complete blocks from the
ten already-consumed development nuclei. Each of 1,278 terminal states keeps
the existing local-section features, the complete canonical order-three port
incidence graph, and sixteen target-free successor-frontier summaries. Nine
nuclei contain an exact terminal. Fully nested whole-nucleus selection chooses
an exact top-one terminal in `7 / 9` supplied groups and `26 / 30` colored
sites, below the frozen `8 / 9` and 27-site gate, so no new nucleus is opened.
The two supplied failures have first-exact ranks 14 and 10; consequently a
development-selected width-16 tree beam retains exact states in all `9 / 9`.
On the already-consumed second-block confirmation, the frozen value still
misranks top one (`2 / 3` sites), but rank 10 is exact and six of the first 16
states are exact. This is evidence for bounded rollback supply, not a fresh
confirmation or a branch-commit rule. The next gate must learn to choose among
those retained configurations from downstream consequences.

That downstream-consequence gate is now measured explicitly. Every one of the
1,278 complete terminals is advanced through at most eight child actions with
the unchanged frozen GCTS transition. Before any copied development label is
read, the builder records 685 proper-motion-invariant fields: child count and
color balance, the highest-ranked child section, and mean/maximum summaries of
the child local sections and successor frontiers. The deterministic compressed
fixture is 1.1 MB and is linked to the source terminal digest.

The fully nested whole-nucleus value selects only `3 / 9` exact terminals and
`18 / 30` correct colored sites, versus `7 / 9` and `26 / 30` for the prior
scalar/port-graph fusion. Its frozen `8 / 9` and 27-site gate is therefore
decisively red; no fresh nucleus is opened. This rejects pooled immediate-child
statistics as the missing commit value. The next implementation should retain
the typed child-frontier incidence graph and explicit failure/rollback edges,
rather than compressing downstream geometry into scalar moments.

That typed graph is now executable evidence, not a design placeholder. The
eight strongest target-free child attachments become colored nodes carrying
their symmetry-quotiented pose/port channels, incoming connection roles, and
outgoing obligations. Pair edges carry invariant distance, shared ports and
future sites, witnessed connections, and color conflicts. The corpus contains
1,016 canonical graphs, 995 witnessed child-child relations, and 638 dead-end
child nodes. All 35,784 pairs are locally compatible, showing that the hard
decision is future port survival rather than immediate collision pruning.

A fixed pairwise graph value, nested by whole nucleus, improves exact top-one
selection from `7 / 9` to `8 / 9` supplied nuclei. It reaches only `25 / 30`
correct colored sites, down from `26 / 30`, so the unchanged joint gate of
`>=8 / 9` and `>=27 / 30` remains red. Typed pose/port topology is useful, but
the present exactness objective undervalues how much correct material a branch
grows. No fresh target, stationarity, or exponential claim follows.

The two complementary values are therefore kept as a bounded marking
portfolio rather than averaged. One head ranks typed child topology; the other
combines the established local section with a group-balanced ordinal graph
value trained on 0/1/2/3 correct-site levels. Each outer model excludes its
held-out nucleus and both heads rank the identical candidates. Retaining one
candidate per head—at most two—contains an exact terminal in all `9 / 9`
supplied nuclei and a posthoc best `28 / 30` sites. Only 19 states are retained
across ten nuclei, reducing the previous rollback width from 16 to 2.

This is a green bounded-supply result and a red autonomous-commit result. The
target-free search still lacks a certified detector that tells it when to
discard the first locally valid state and try the second. The consumed labels
are consulted only after the two orders freeze; no fresh target is opened.

The first explicit rollback detector audit advances all 19 retained states for
the same 16 target-free child placements inside one additional public shell.
The rollout never constructs a target crop, and every per-step frontier count,
vote mass, selected port probability, and chosen color is frozen before labels
are joined. None of the 19 traces reaches a fixed point, so hard exhaustion is
unavailable. A train grid over five aggregate discharge statistics and seven
horizons finds a 12-step frontier-vote rule with `9 / 9` exact supplied groups
and `28 / 30` sites when fitted on all consumed development data. Whole-nucleus
holdout falls to `8 / 9` and `26 / 30`, while 31 within-nucleus label shuffles
give `p = .3125`. The endpoint advantage is development overfit, not a causal
rollback certificate; aggregate frontier volume is rejected in favor of a
future typed-obligation/discharge representation.

That rule was nevertheless frozen for a genuine one-shot spatial audit rather
than tuned further. Commit `18e45c9` preregisters a geometry-only maximin center
at `(-70, 10, 70)`, 66.33 units from every recorded prior IQC center and beyond
two second-block radii; the public harness and all model/rule digests were
published before seed generation. From a 491-atom seed, the frozen first tree
has candidate counts `4 → 7 → 29`, and its selected state is self-fed into 133
second-block terminals. The topology and ordinal-yield markings retain states
21 and 19, then both receive the same 12-step target-free rollout and score
`1232`. Their complete receipt is hashed before the radius-23.56 target opens
exactly once.

The fresh result is red. The first block places `2 / 3` correct actions; the
two second-block alternatives place `2 / 3` and `1 / 3`, so neither supplies
an exact state, and the stable tie selects the latter. End-to-end correctness
is `3 / 6`. Reranking only those two retained states cannot fix the path:
exact width-two portfolio supply is absent and the selected upstream first
block is inexact. The autonomous finite-commit, stationary, and exponential
IQC gates remain red.

A complete-tree follow-up now separates missing geometry from destructive
pruning. Delaying the first prune gives `8 → 37 → 128` terminals, including 16
exact states; the frozen fusion value places its first exact state at rank 8.
Self-feeding that exact state gives `8 → 36 → 127` second terminals with four
exact continuations (stable IDs 86, 87, 89, and 123). Thus an exact two-block
path exists in the unchanged candidate geometry. The current topology and
ordinal-yield heads still bury their best exact action at ranks 62 and 98, so
top-one-per-head retention loses the path. The preregistered step-12 frontier
vote mass improves the best exact rank only to 19.

Integrated frontier vote mass at horizon 12 ranks exact second action 89 first,
but it is not a universal greedy rule: applied to the complete first tree it
selects inexact state 115, with its best exact first state again only rank 8.
This is consumed-development evidence chosen after scoring, not a fresh
confirmation. It justifies an explicit bounded tree beam across blocks, not a
new top-one commit claim. Candidate supply is now green in the complete tree;
bounded transferable selection, runtime, autonomous commitment, stationarity,
and exponential IQC growth remain red.

The branch-local executor is now run end to end. It retains the eight
complete-tree fusion parents, independently builds each full second tree
(`126–141` terminals), rolls every terminal for twelve target-free steps, and
keeps one integrated-vote child per parent. All eight branch receipts and the
global score order freeze before the consumed target opens. Exactly one beam
path is exact: first-parent rank 8 and its selected second child, stable state
89. Thus the branch-local `8 × 1` beam preserves the exact six-action path.
However, comparing the eight integrated scores globally selects parent rank 3,
whose first and second blocks are both inexact. The exhaustive audit takes
about forty minutes on four workers. Parent context must remain in the value
state, and this explicit beam is a correctness ceiling rather than a practical
growth engine.

A literal clusters-of-clusters geometry is tested next. For each consumed
development nucleus, the exact inherited three-action parent and every
three-action child become a six-action colored macro. Its 62-component
descriptor contains within-parent, within-child, and cross-block distances,
colored connection counts, centroid/radius statistics, and a proper-SE(3)-
invariant mirror-sensitive triple product. The frozen corpus has 1,278 macros,
142 exact, across ten nuclei. A group-balanced linear value reaches 6 / 9 exact
supplied groups in-sample and beats all 31 within-group label shuffles
(`p = .03125`), but whole-nucleus holdout collapses to 1 / 9 and 14 / 30 sites.
On the consumed confirmation beam it ranks the sole exact macro fourth and
selects parent 2. Raw macro shape overfits; reusable clusters-of-clusters need
typed boundary obligations and carried GCTS ports, not geometry alone.

That proposed correction has now been tested explicitly. A second frozen
dataset augments every six-action macro with 23 ID-free parent-port graph
statistics, the same 23 child-port statistics, and their 23 signed changes.
The fields count typed incoming and outgoing obligations, witnessed edges,
components, degrees, and boundary load; candidate coordinates and colors are
unchanged and no raw support-type ID enters the value. Coupling these 69 fields
to the 62 macro fields raises nested whole-nucleus selection from 1 / 9 to
3 / 9 supplied nuclei and from 14 / 30 to 20 / 30 sites, but it does not beat
the 31 within-nucleus label shuffles (`p = .1875`). On the consumed eight-parent
beam the only exact six-action path falls from rank four to rank five and the
selected parent is still false. Aggregate port-transition summaries are
therefore rejected as the default marking. The next value must retain the
identity and incidence of obligations that are discharged or carried, not
merely their graph totals.

The identity-preserving version is now operational. It constructs one
canonical six-node transition graph from the three parent actions and three
child actions. All 15 within/cross edges retain normalized separation, shared
colored support, support-geometry equality, proper chirality, and whether a
parent action participates in a child's matched support. Parent/child roles
are node colors; canonicalization enumerates only the `3! × 3!` block-local
permutations. Translation, global proper rotation, action order, and raw
support-type IDs are absent. The 1,278 terminals form 1,120 unique graphs.

A fixed order-three source × port × neighbor value reaches 7 / 9 exact
supplied nuclei and 26 / 30 sites under whole-nucleus holdout. All 31
within-nucleus label shuffles do worse (`p = .03125`). On the consumed
eight-parent beam, the only exact six-action path rises to rank two, although
the top-ranked path remains false. Equal percentile fusion with the existing
successor child-frontier graph reaches 8 / 9 exact supplied nuclei but remains
at 26 / 30 sites; weights from .5 through 2 share the same accuracy plateau.
The unchanged development gate requires both 8 / 9 and 27 sites, so the
incidence value enters the marking library as an experimental option rather
than becoming the autonomous default. Exact graph-embedding caching reduces a
full 42-fit audit from about an hour to a few minutes without changing model
digests or scores.

The same identity-preserving value is then tested in the narrower role it was
designed for: ordering only the already-frozen two-marking rollback portfolio.
That portfolio contains 19 states across ten nuclei and never more than two in
one nucleus. Whole-nucleus outer models choose an exact retained state in all
`9 / 9` supplied nuclei and total `28 / 30` correct colored sites. This passes
the deterministic development threshold, but not the causal control.

The corrected null repeats the complete model fit separately for each held-out
nucleus after every one of 31 within-nucleus label shuffles. Eleven shuffled
fits also reach `9 / 9`, giving the plus-one upper-tail result `p = .375`.
Thus the earlier pooled-null advantage cannot justify autonomous rollback. On
the consumed six-action receipt the exact state is present at incidence rank
two, while the first-ranked state is false. The benchmark therefore keeps the
two-state supply result green and the failure-detector, fresh-confirmation,
stationary, and exponential gates red.

The follow-up now preserves discharge *identity* through the rollout rather
than reducing the frontier to total vote mass. The same 19 immutable retained
states are each advanced for 16 target-free placements. Across 304 transitions,
406 selected-role transitions retain 131 symmetry-quotiented semantic port
identities and record whether each selected obligation disappears, persists,
or is selected again. No candidate, atom ID, absolute coordinate, lattice axis,
or target atom enters this representation.

An eight-step selected-role-persistence rule fitted outside each nucleus picks
an exact state in all `9 / 9` supplied nuclei and totals `27 / 30` correct
colored sites; fitting all consumed development nuclei yields `28 / 30`.
That apparent result is statistically underpowered. Only three nuclei have
nonidentical `(exact, correct-sites)` label tuples, and only two can change the
exact-selection result. Exhaustively refitting every outer fold for all eight
distinct within-nucleus assignments gives `p = .25`, which is also the minimum
attainable exact-test resolution of this 19-state corpus. Typed discharge enters
the marking library as an interpretable experimental channel, while autonomous
rollback remains red. The next decisive audit needs more independently
ambiguous nuclei or a wider target-free retained portfolio.

That wider stress test is now complete. The same two target-free orderings keep
their first eight candidates, restoring the historical maximum rollback width
of 16 after deduplication. The result contains 120 states, preserves exact
supply in all `9 / 9` supplied nuclei, and gives seven independently mixed
exact/inexact nuclei. Its conditional random-selector exact probability is
`.0006686`, so the earlier resolution problem is genuinely removed.

Every state is replayed for the unchanged 16-step horizon. The frozen corpus
contains 1,920 transitions, 2,581 selected-role events, and 135 semantic role
identities; the original 19 trajectories are byte-for-byte equal after JSON
decoding. On this harder supply, scalar frontier evidence selects `7 / 9` exact
nuclei and `24 / 30` sites, while aggregate typed persistence falls to `5 / 9`
and `24 / 30` (`p = .71875`). A nested identity-specific model then chooses
among 120 exact/coarse/chemistry role-channel specifications with independent-
nucleus support. Its final 50-weight coarse role-status table reaches only
`5 / 9` and `23 / 30`; all hyperparameters and every null are refitted inside
their outer folds, again giving `p = .71875`.

The wide portfolio is retained as the statistically meaningful rollback
benchmark, but independent obligation weights are rejected. The next GCTS
marking must represent relations among simultaneous discharged, surviving,
and newly exposed ports—or an explicit contradiction certificate—rather than
assigning value to each port identity separately.

The next audit adds those relations without serializing the hundreds of
background role identities. At every accepted attachment it transiently scans
the complete before/after semantic-role multiset and records seven bounded,
proper-motion-invariant counters for each selected port: reciprocal connection,
forward and backward continuation, equal parent/source endpoint, and parent or
source touch. Five explicit contradiction flags record missing or depleted
continuations. A parity test proves all 120 scalar and typed trajectories are
unchanged.

A deliberately low-capacity grid of 120 metric/horizon/direction rules selects
“minimize the number of forward continuations after two steps.” Whole-nucleus
holdout reaches `7 / 9` exact supplied nuclei and `26 / 30` colored sites—two
more sites than scalar discharge and three more than independent role weights,
but still below the `9 / 9`, `27`-site gate. Six of 31 fully refitted label
shuffles match or exceed seven exact nuclei, giving `p = .1875`. Relational
closure is useful but not causally sufficient. The remaining implementation
target is a branch-level consistency graph or explicit certificate that some
carried port obligation can no longer be satisfied.

That branch-level solver is now implemented with a strict three-valued result.
It returns `satisfied` only with an explicit conflict-free action cover,
`unsatisfied` only after complete candidate enumeration and exhaustive search,
and `unknown` whenever either side is truncated. Only `unsatisfied` is a legal
rollback certificate. A synthetic adversarial control proves the difference
from the former marginal check: actions exist for every role separately, yet
their pair conflict makes the joint branch exhaustively impossible.

The real width-16 audit rebuilds the complete successor frontier for all 120
retained IQC branches, freezes exact pair-collision constraints, hashes each
candidate set and certificate, and joins consumed development labels only
after each group's geometry is frozen. All 120 searches complete. The result
is deliberately red: all 59 exact and all 61 false branches are `satisfied`.
Forty-one branches have no persisting selected role; the remaining 79 reduce
to at most one distinct semantic role, 137 relevant child actions in total,
and zero pair conflicts. The simultaneous solver is no longer the weakness.
The role quotient erased the finite port-instance incidence needed to expose a
contradiction. The next graph must carry exact symmetry-quotiented port
instances while keeping candidate geometry and target ordering unchanged.

That finite-instance path is now live. `MarkedProposalResult` preserves the
exact ordered parent→source occurrence witness for each aggregated proposal
through filtering and merged frontiers. These indices are execution provenance
only. The benchmark converts them into endpoint-equality relations and a
colored normalized distance matrix before serialization; raw indices, global
coordinates, and lattice axes never become marking keys. Rigid-motion and
atom-permutation controls preserve the resulting scientific relation.

Every one of the 120 selected wide actions has exactly one ordered pair
witness. The complete successor frontier is tested under seven fixed instance
relations matching the earlier semantic vocabulary. The forward-continuation
certificate retains `57 / 59` exact branches and rejects `26 / 61` false
branches. Its retained precision is `57 / 92 = 61.96%`, versus `59 / 120 =
49.17%` before filtering. This is a real contradiction signal created solely
by restoring finite incidence. It is not yet safe to deploy: two exact
branches are rejected, and one of nine nuclei with exact supply loses its only
exact branch. Backward continuation recovers all exact branches but rejects
only one false branch, so simply unioning relations destroys the gain. The
next marking must learn a train-only local boundary condition for when absent
forward continuation is acceptable.

That bounded follow-up is now measured rather than assumed. Before labels are
joined, every selected exact port records six invariant scalars: public-boundary
margins for the target and both endpoints, ordered port length, outward cosine,
and current frontier fraction. A leave-one-nucleus-out sweep over one scalar and
one threshold direction selects normalized ordered port length. Treating the
selected forward-UNSAT branches as **deferred**, never as port-satisfied,
restores `59 / 59` exact branches and exact supply in all `9 / 9` nuclei while
still rejecting `8 / 61` false branches; retained precision is `59 / 112 =
52.68%`. This recovery is not causal marking evidence. Thirty-one
within-nucleus label shuffles repeat feature selection and threshold fitting,
and every null ties the observed two exact recoveries and eight false
rejections (`p = 1` for both). The rule remains out of the active marking. It
separates boundary regimes but cannot distinguish exact from false actions
inside either exact-bearing regime, so the next representation must retain the
joint endpoint metric graph rather than add scalar boundary capacity.

The endpoint graph itself is also now falsified as sufficient. The selected
target, parent, source, and public center give only three graph classes among
the 28 forward-UNSAT rows; in both exact-bearing classes the exact row collides
with false rows. The fixture therefore adds the full three-action branch as an
unordered colored proper-metric graph: three center distances, three internal
edge lengths, node colors, and a signed normalized volume. Raw occurrence IDs
and action insertion order are absent. This makes every one of the 28 difficult
branches locally distinct with zero exact/false graph collisions.

Local identity does not transfer. The 120 branches contain 119 exact graph
classes; only one class repeats across nuclei, covering two exact rows. A
nested grouped nearest-recurrent section over 30 invariant graph aggregates
selects `0 / 2` recoverable exact forward-UNSAT nuclei. A separate train-only
colored-edge vocabulary, with edge-width selected inside each outer fold, also
selects `0 / 2`. Thirty-one within-nucleus shuffled-label refits have median
zero and maximum one exact selection for both arms (`p = 1`). Neither section
is deployed. The next justified step is to learn a recurrent
cluster-of-clusters quotient across a larger independent nucleus corpus before
fitting branch value; increasing capacity over 119 nearly unique graphs would
only memorize development geometry.

The pre-existing 30-nucleus recurrent branch corpus supplies the next
independent transfer audit without generating or tuning on another wide target.
Its complete local domains have radius `14.5623`; the wide benchmark domains
have radius `23.5623`. One training nucleus is excluded because its nearest
wide-center separation is `37.4166`, below the required sum `38.1246`. The
remaining 29 nuclei have minimum separation `40.0`, so their closed atom
domains are disjoint from every wide case. They contain 338 branches, 195
exact, and 20 nuclei with exact supply.

The existing grouped capacity search selects a nine-neighbor value and chooses
the exact branch in `19 / 20` supplied training nuclei. Frozen features for the
28 wide forward-UNSAT candidates are then joined from the independent terminal
fixture; candidate geometry and order are fixed before wide labels are scored.
On the two recoverable exact wide nuclei, the exact ranks are `1` and `10`; the
third affected nucleus has no exact branch. Top-one selection rejects `24 / 26`
false alternatives but recovers only `1 / 2` exact fallbacks, leaving complete
supply at `8 / 9` nuclei. Thirty-one within-training-nucleus label shuffles
repeat capacity selection and model fitting against the byte-identical wide
candidates. Every null also selects one exact fallback (`p = 1`).

The external recurrent value is therefore not integrated. Its larger corpus
improves the earlier graph sections from `0 / 2` to `1 / 2`, but the result is
neither causally distinct from shuffled labels nor supply preserving. The
missing representation is still a recurrent oriented cluster-of-clusters
quotient with transported port semantics, not a higher-capacity value over the
nine aggregate scalar branch features.

On the consumed development set, candidate supply is no longer the immediate
uncertainty. A second train-only audit keeps
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

### Geometry-complete recurrent macro quotient

The next IQC audit makes the clusters-of-clusters candidate itself explicit
rather than reducing it to scalar branch statistics. Seventeen development
nuclei are closed-ball disjoint from the unchanged ten-nucleus wide audit. They
freeze 168 three-action macro occurrences, including 72 exact occurrences and
158 exact port-derivation alternatives. Each occurrence stores colored nodes,
a right-handed intrinsic frame, symmetry-quotiented endpoint geometry, and the
parent/source connection witnesses. Raw occurrence indices, action order, and
a global coordinate frame are not semantic fields. Different search histories
that realize one geometry remain exact derivation alternatives rather than
being silently collapsed.

The train-only quotient searches fixed distance widths and independent-nucleus
support thresholds. Its selected width is 4.0, producing 33 semantic geometry
types and 54 exact action alternatives. Leave-one-nucleus-out evaluation finds
7 of 9 supplied exact nuclei, but selects 11 branches at only 63.6% precision;
31 within-nucleus label shuffles give `p = .4375`. The exact unbinned quotient
is perfectly precise but reaches only 4 of 9 supplied nuclei.

Frozen on the unchanged wide forward-UNSAT set, the quotient selects two false
branches and none of the two recoverable exact branches. The earlier scalar
fallback selects one exact and two false branches. This is an informative red
result: cluster shape is not a transferable GCTS marking by itself. The next
implementation step is one common canonical port-incidence graph schema for
both development and wide branches—node geometry, ordered connection state,
endpoint witnesses, and bounded successor incidence—followed by the same
grouped-shuffle and external-transfer gates. No autonomous, stationary, or
exponential IQC claim follows from this audit.

### Shared port-incidence graph and exact-vocabulary transfer

That common schema is now executable rather than aspirational. A generic
serializer accepts three colored placements and all incoming parent→source
port witnesses. It emits three canonical nodes and three action-pair edges.
Nodes retain the finite cluster-state colors and endpoint geometry; edges
retain directed endpoint equality/touch relations and normalized endpoint
distances. Exhaustive node permutation removes action insertion order. Only
right-handed intrinsic frames are admitted, so translation and proper rotation
are quotiented while reflections remain distinguishable. Synthetic controls
cover permutation, arbitrary proper motion, chirality, missing ports, and
continuous-frame degeneracy.

The unchanged wide branches are replayed from their colored seeds to obtain
authentic internal witnesses. Receipt-constrained replay advances only prefixes
that can still match one of the pre-existing target-blind action graphs; every
final action digest must reproduce exactly. The resulting 57 KB companion
fixture contains all ten groups and all 120 branches (59 exact). Second-block
targets and row labels are absent from graph workers and join only after all
ten graph digests freeze. Development and wide records now have byte-for-byte
the same public graph fields.

A bounded quotient independently ablates action metric, port metric, state
separation, endpoint metric, and repeated-witness multiplicity while preserving
directed incidence and chirality. Under leave-one-nucleus-out selection with a
95% precision floor, the selected recurrent type reaches 4 / 9 supplied
development nuclei with 4 / 4 selections correct. Frozen on the unchanged 28
forward-UNSAT candidates, it recognizes only one candidate, recognizes neither
recoverable exact branch, and selects nothing. Both exact and false external
shuffle p-values are 1. The fail-closed behavior is correct, but exact semantic
identity is too sparse to be the GCTS marking. The next benchmark learns a
bounded graph metric/message quotient on this shared representation; it may
rank existing exact alternatives but cannot authorize new geometry. No
autonomous, stationary, or exponential IQC claim follows.

### Continuous port-graph metric

Exact recurrent type identity is then relaxed only at the marking layer. Each
common graph produces 92 fixed proper-motion-invariant measurements, separated
into action geometry, port-role chemistry, port pose, radial environment, and
directed endpoint incidence. Nearest examples are reduced to one vote per
training nucleus before weighting, so a large symmetry orbit or a nucleus with
many similar branches cannot dominate. Candidate geometry, exact production
alternatives, ports, and collision certificates remain unchanged.

Whole-nucleus development selection searches eleven predeclared feature
families, 3/5/9/13 group-neighbor counts, weighted/unweighted votes, and five
admission thresholds. A 95% precision floor applies before coverage. The
minimum-description winner uses only pose+incidence, thirteen weighted group
neighbors, and threshold 0.7. It selects 6 / 9 supplied nuclei with 6 / 6
exact branches, improving the exact vocabulary's 4 / 9. However, 31 complete
within-nucleus label shuffles have median five and maximum seven exact nuclei,
giving `p = .46875`.

Frozen on the unchanged wide set, no branch reaches 0.7. The two exact branches
rank fifth and second in their groups; no false branch is admitted. The
external exact p-value is 1. The metric therefore supplies a useful continuous
ordering and safer fail-closed behavior, but neither causal evidence nor an
action-commit rule. It remains an experimental marking-library option. The next
step is a finite relational message quotient whose learned node/edge updates
must beat the same grouped nulls and unchanged-wide transfer before recursive
growth is attempted.

### Finite relational port-message quotient

The shared three-action graph now supports one bounded, train-fitted message
quotient. Its 216 proper-motion-invariant measurements are attached to the
three canonical action nodes and three pairwise incidence edges; raw IDs,
global coordinates, targets, lattice data, and family labels are excluded.
Training-nucleus balancing prevents a repeated orbit from supplying extra
votes. Exact action terminals and collision certificates remain unchanged.

The selected rule uses node messages, three bins, support in four independent
training nuclei, eight retained tokens, and threshold 0.55. It compresses the
training graph measurements into 362 finite recurrent states and selects 4 / 9
supplied development nuclei with 4 / 4 exact branches. This is weaker than the
continuous metric's 6 / 9, and 31 full grouped-label refits give `p = .96875`.
On the unchanged wide audit, exact branches move from ranks 5 and 2 to ranks 3
and 1, but neither clears the frozen threshold. The representation therefore
improves ordering without validating commitment. It is retained only as a
diagnostic marking-library option; tree-search deployment, recursive
promotion, autonomous growth, stationarity, and exponential growth stay red.

### Sequential port-obligation automaton

The static relational quotient is now followed by an explicitly temporal
marking. Every exact frozen branch is replayed for sixteen target-free steps.
At each step, concrete port identities are removed and replaced by a bounded
canonical state containing selected-role discharge and production, relation
gain/loss/retention, contradiction flags, and simultaneous selected-pair
incidence. Counts saturate at four. A training nucleus contributes at most one
mean label to a state, and the branch score is the mean posterior of its four
weakest recognized states. The resulting automaton contains 102 states and
cannot alter or authorize candidate geometry.

Under leave-one-nucleus-out replay, the automaton selects exact branches for
8 / 9 supplied nuclei and retains 27 / 28 available correct colored sites. The prior
single relational contradiction rule reached 7 / 9. Thirty-one within-nucleus
label shuffles reach a median of five and a maximum of seven, giving the fixed
automaton `p = .03125`.

This is a meaningful branch-consistency signal, not yet a deployment result.
The automaton specification was developed on this consumed corpus rather than
preregistered, 47 / 102 states have support in only one training nucleus, and
one supplied nucleus still chooses a false branch. It is
therefore frozen only as a future disjoint-confirmation candidate. Default
tree-search commitment, clusters-of-clusters promotion, autonomous growth,
stationarity, and exponential growth remain disabled.

### Fresh obligation-automaton confirmation

The automaton was then frozen and preregistered before touching a new nucleus.
A geometry-only maximin rule selected `(-110, -70, -70)`, with 87.18 units of
separation from every consumed 32.56-radius rollout domain. The colored R9
seed contains 480 atoms. Complete `8 × 8 × 8` frontier enumeration supplies
152 three-action terminals; the unchanged scalar/fusion portfolio retains 13.
All sixteen-step trajectories, automaton scores, action IDs, and receipt hashes
freeze before one target-factory call. Bounds 72 and 73 reproduce the same
2,066-atom R14.56 target exactly.

The portfolio contains two exact branches, so candidate supply passes. The
automaton ranks the first exact branch fifth and selects a branch with two
correct sites and one false site. Recognized transition-state coverage is only
6.25–18.75%. The one-shot gate is therefore red. This is a transfer failure of
the obligation vocabulary, not a missing-candidate failure; the target is now
consumed and will not be retried. Default search commitment, autonomous growth,
recursive promotion, stationarity, and exponential claims remain disabled.

### Obligation backoff and soft temporal metrics

A target-free companion fixture reconstructs the consumed confirmation's
`8 → 40 → 152` candidate tree, 13 retained sixteen-step trajectories, and
published candidate/portfolio/receipt hashes without importing or constructing
the target. New marking representations rank this fixture first; only then is
the already-published partial ordering joined.

An exact→role-shape→aggregate backoff improves recognized-state coverage on
the published-known exact branch from `12.5%` to `75%`, but grouped selection
has `p = .1875` and the branch moves from rank 5 to rank 8. A 270-coordinate
colored role metric and a 1,620-coordinate order-sensitive metric then replace
state equality with bounded proper-motion-invariant discharge, contradiction,
relation, and timing channels:

| obligation representation | heldout AUC | exact top actions | top-action p | consumed known-exact rank |
| --- | ---: | ---: | ---: | ---: |
| pooled role channels | `.8637` | 8 / 10 | `.50` | 13 |
| ordered temporal bins | `.7498` | 8 / 10 | `.50` | 8 |

For both models the AUC and log-loss plus-one p-values are `.03125`, showing
that the coordinates contain a real ranking signal. They nevertheless fail
the discrete decision the executor needs: top-action selection is reproduced
by shuffled labels, and known false actions outrank the known exact action in
the consumed spatial transfer. Neither model is installed, no target is
reopened, and no fresh confirmation, autonomous, stationary, or exponential
claim is made. The next dataset must add independently ambiguous nuclei rather
than tune more capacity on this consumed ten-group corpus.

### Twenty-nucleus disjoint obligation corpus

A published maximin grid fixes twenty new nuclei whose complete
32.5623-radius rollout domains are mutually disjoint and disjoint from every
consumed nucleus. Each colored R9 seed enumerates its complete three-action
tree, retains the union of two target-free ranker heads, and rolls every
retained branch for sixteen relational steps. All 303 trajectory records and
their hashes freeze before any R14.5623 target is constructed. Bounds 84 and
85 reproduce every seed and target crop exactly.

The full 162-spec role/temporal grid, including two bounded frontier-dynamics
channels, is reselected by whole-nucleus holdout. Every one of 31 null trials
shuffles `(exact, correct-sites)` together inside each nucleus and repeats the
full selection. The selected temporal model yields 41 correct sites, exceeding
the shuffle maximum of 40 (`p=.03125`). It nevertheless selects exact whole
branches in only 7 of the 8 nuclei that supply one; a shuffle reaches eight
(`p=.125`). Thus the enlarged corpus validates a transferable site-section
signal but rejects exact action commitment. It is consumed development data,
not a confirmation; default marking, autonomous growth, recursive promotion,
stationarity, and exponential claims remain disabled.

### Site-resolved obligation actions and consumed confirmation

The 303 fixed branch geometries are next expanded into 909 emitted-site rows:
462 supported sites and 447 unsupported sites. The action is not split or
repaired. Each site receives a bounded temporal obligation section, frontier
trace measurements, and proper-motion-invariant colored triangle geometry;
the three site scores are then aggregated back onto the original certified
three-site terminal. Grouped outer folds select a weighted seven-neighbor
model with mean aggregation. It chooses an exact action in all eight nuclei
that supply one and yields 45 correct selected sites. Thirty-one complete
within-nucleus label shuffles reach at most seven exact actions and 39 sites,
so both plus-one p-values are `.03125`. This is the first exact-action green
development gate for this obligation corpus.

The model and a new maximin centre `(0,-120,-160)` were then published before
any confirmation atom was generated. Its complete rollout domain is 118.322
units from the nearest consumed domain. Three self-fed waves freeze candidate
counts `8→40→157`, `8→39→144`, and `8→38→136`, retaining portfolios of 14,
15, and 15 actions. Only after all site scores and selected successor clouds
are immutable does one target factory construct the 2,031-atom R14.5623 crop;
lift bounds 108 and 109 agree exactly.

The one-shot result is red. The first frozen portfolio contains no exact
three-site action. The second and third each contain one, but the learned mark
selects neither: selected correctness is `0/3`, `2/3`, and `0/3`, or `2/9`
sites total. This separates an upstream portfolio-supply failure at wave one
from a marking-transfer failure at waves two and three. The target is consumed
and is not retried. Default commitment, autonomous finite growth, recursive
promotion, stationary recurrence, and exponential IQC claims remain disabled.

The consumed first wave has now been exhaustively diagnosed. All 157 terminals
of the original `8→8→8` tree were rolled out and scored before reconstructing
the already-consumed target; none is exact, so no portfolio width or marking
can rescue that tree. A fixed reach audit then freezes six alternative trees
before posthoc scoring. The smallest repair is `12→4→8`: it contains one exact
terminal while reducing proposal checks from 392 to 356. `16→4→8` supplies two
and `24→4→8` supplies four, at 504 and 800 checks. The repaired exact terminal
still ranks only 107th by fusion and 114th by the scalar head. The next target
is therefore an earlier, cheaper connection section—not a 107-candidate
portfolio. This is consumed diagnostic evidence, not a replayed confirmation.

### Stage-local rollout value

The repaired `12→4→8` tree is next scored before terminal fusion rather than
asking a late scalar head to recover a rank-107 action. Twenty disjoint
development nuclei contribute 320 target-free training candidates; the
execution portfolio remains eight candidates per nucleus, or 160 total. A
bounded 16-step, four-time-bin section records connection discharge,
contradiction, and separation channels and changes only the ordering of those
same exact actions.

| stage-local development | result |
| --- | ---: |
| development nuclei / exact-supply nuclei | 20 / 19 |
| training / execution candidates | 320 / 160 |
| selected section | temporal-61 · horizon 16 · 4 bins · k=7 weighted |
| selected exact / colored sites | 19 / 19 · 59 |
| connection-only exact / colored sites | 19 / 19 · 57 |
| 31-shuffle maxima exact / sites | 18 / 58 |
| plus-one exact / site p | `.03125 / .03125` |

Every null trial shuffles the complete sixteen-candidate label vector inside
each nucleus and repeats the 162-model selection. The result validates a local
connection-value signal on consumed development data; it does not validate a
search policy, autonomous growth, recursive stationarity, or exponential IQC
growth.

### Preregistered rollout-ranked confirmation

The temporal-61 model, the complete `12→4→8` geometry, the `(4→8→8)` retained
portfolio, a three-block self-fed protocol, and the geometry-only maximin
centre `(120,-40,-220)` were frozen before the new nucleus was generated. The
476-atom seed drives three target-free blocks. All candidate IDs, rollout
features, rankings, and selected successor clouds freeze before one target
factory call creates the 2,069-atom reference.

| confirmation block | marked | stable-prefix baseline |
| ---: | ---: | ---: |
| 1 | 2 / 3 | **3 / 3 exact** |
| 2 | 2 / 3 | 2 / 3 |
| 3 | 2 / 3 | 1 / 3 |
| total | 6 / 9 · 0 exact blocks | 6 / 9 · 1 exact block |

The significant development model therefore fails spatial transfer: it
displaces a correct first baseline action and does not produce one exact
three-site block. The one-shot target is consumed and is not retuned. The
first-block, sustained-continuation, autonomous, stationary, and exponential
gates all remain red.

### Shared marking-library tree

The tree executor now separates candidate geometry from marking value. The
connection and rollout markings rank the same immutable eight-action frontier,
and a round-robin shared beam retains states proposed by both without expanding
the geometry twice. On the consumed confirmation this preserves the exact
connection head at index 0 alongside the rollout head at index 7; the learned
rollout score can no longer delete the known-stronger baseline action.

The three-block width-two receipt expands `8 → 16 → 16` physical candidates
and retains two states at every block. Both final paths recover `6 / 9` colored
sites and neither is exact. The generic portfolio therefore passes its limited
candidate-supply invariant—same actions, both marking heads retained, no target
input—but does not select a winner or establish autonomous, stationary, or
exponential IQC growth.

### Prefix channel portfolio and bounded reach

The generic portfolio now supports depth-dependent beam schedules, global or
parent-balanced allocation, additive or stage-local replacement scores, and a
finite state channel for every marking. Channel allocation covers distinct
local-section and pose/port cells before using another slot in the same cell.
Crystal-equivalent actions still deduplicate to one physical state, and an
empty amorphous frontier still terminates without a growth rule.

The consumed IQC diagnosis separates reach from value. A lineage-balanced
`2→4→8` outer beam keeps eight terminal paths but none is exact; the best has
`7/9` colored sites. With learned prefix pruning removed, the bounded
`12→8→16` exposed-port reach contains a target-guided exact block at all three
self-fed stages. After one exact two-site prefix, the first correct final port
is rank 14 among 740 exposed ports, explaining why reach eight fails.

That geometric availability does not transfer into an autonomous decision.
The frozen channel-diverse `8→16→32` prefix portfolio retains two exact first
blocks, then zero exact second blocks among 64 retained terminals. The target
is used only in this already-consumed diagnostic to identify exact prefixes;
candidate generation itself remains target-free. The next gate is a
transferable clusters²/port-incidence value that retains the bounded exact
lineage, not another wider brute-force tree.

### Clusters² future-option portfolio

Parent selection now looks one complete cluster block ahead. The base,
colored, port, and coupled frozen markings all score the same `126–141` child
terminals under each of eight parents, and each channel contributes a parent
to a shared width-four beam. The only exact parent moves from source rank eight
to port-option rank one and mean-option rank three. Its union-of-top-eight
child portfolio contains one exact continuation, yielding the retained
six-action path `parent 8 → child 123`; none of the four greedy top children is
exact.

This is a supply result, not a selection claim. Fifteen of 31
marginal-preserving score shuffles also retain the exact parent (`p=.50`), and
the exact mean rank is not significant (`p=.40625`). The consumed target is
opened only after the tree, scores, channel orders, and selected IDs are
hashed. A group-heldout parent-option corpus and a third self-fed block are
still required before autonomous, stationary, or exponential IQC growth can
turn green.

That group-heldout audit now exists. It contains 1,278 six-action parents
across ten consumed development nuclei, 142 exact parents, and a frozen graph
of at most eight target-free child actions below every parent. Order-one and
order-two typed-port values are fitted leave-one-nucleus-out; local port-mass
and live-continuation channels are fixed. A width-four option beam retains an
exact parent in `8 / 9` supplied held-out nuclei with mean first-exact rank sum
`30`. Thirty-one marginal-preserving controls give `p=.03125` for retention
and rank. The strongest order-two graph value is itself `8 / 9`, however, so
the option portfolio has not yet improved causal retention. Individual child
nodes have no correctness labels; this is parent supply, not a third-block or
autonomous-growth result.

The retained parents have now been executed at a genuinely larger radius.
Forty parent configurations produce 5,091 immutable three-action terminals;
the four marking channels retain 160 before one consumed target open. Exact
parents survive in eight nuclei. The bounded top-8 terminal trees contain 90
exact end-to-end paths across six nuclei, but the retained portfolios contain
only six paths across three. Three failures are portfolio pruning failures
(first-exact ranks reach 109), while two occur at the hard per-step reach
cutoff.

A consumed-target reach diagnostic resolves the latter ambiguity without
changing the grammar or deployable policy. For all four exact parents in those
two nuclei, a lexicographic uniform-cost search over the full frozen frontier
finds an exact three-action path. Every minimum bottleneck rank is `12` (rank
sums `21` or `23`), whereas reach `8` supplies none. Thus connection geometry
is present; a train-only adaptive or channel-diverse reach policy is missing.
Because the diagnostic follows correct prefixes using an already-consumed
target, it does **not** authorize setting reach to twelve.

A separate nested group-heldout value test rejects the simplest proposed
fix. Proper-SE(3)-invariant terminal scores, triangle geometry, radii, and
parent/terminal cross-distances retain exact paths in only `2 / 6` supplied
nuclei, versus `3 / 6` for the incumbent. Thirty-one within-parent label
shuffles give retention `p=.4375` and rank `p=.21875`. The model, candidate
geometry, and four-per-parent budget are frozen, but this terminal geometry is
not a transferable GCTS marking. These results are self-fed third-block
diagnosis, not autonomous commitment or a stationary/exponential IQC rule.

The first compute-matched reach repair is now positive on the consumed
development corpus. The generic pose/port marking exposes its five continuous
train-frozen channel responses. At every state, a new selector spends the
unchanged budget of eight child constructions on three scalar leaders plus
one previously unseen leader from each channel. It does not increase the
frontier, use coordinates as features, refit the marking, or inspect a target.
On the four parents hidden by scalar top-8, it restores `11`, `10`, `11`, and
`10` exact terminal paths. On all fifteen exact parents, it preserves every
previously supplied nucleus and improves:

| consumed third-block supply | scalar top-8 | 3 scalar + 5 channels |
| --- | ---: | ---: |
| exact parents supplied | `11 / 15` | `15 / 15` |
| eligible nuclei supplied | `6 / 8` | `8 / 8` |
| exact terminal paths | `90` | `472` |
| child-expansion budget per state | `8` | `8` |

This selector was proposed after the two reach failures were consumed. The
six other nuclei are a preservation/transfer screen, not a genuinely fresh
confirmation, and no path winner is committed. The production executor
therefore keeps its prior default until a disjoint preregistered nucleus passes
the same frozen policy. Autonomous, stationary, and exponential IQC gates
remain red.

### Fresh bounded joint-action confirmation

The complete second frontier, the whole-child proper-SE(3)-invariant marking,
the per-parent `joint top-1 + base top-5` schedule, exact unordered-action
geometry memoization, source hashes, and maximin centre `(160,-180,-140)` were
committed before the fourth fresh nucleus was generated. Its full radius-32.56
domain is 161.25 units from every one of 89 prior centres. The R9 seed contains
474 atoms. Candidate generation, ranking, memo telemetry, and the complete
receipt freeze before the target is opened exactly once.

| fresh bounded clusters² receipt | result |
| --- | ---: |
| scheduled / eager child prefixes | `47 / 168` |
| naive / unique geometry advances | `17,240 / 8,207` |
| memoized duplicate advances | `9,033` |
| immutable nine-action lineages | `6,099` |
| exact parent→child prefixes after scoring | `34` |
| exact nine-action lineages after scoring | `410` |
| parents with exact supply | `8 / 8` |
| measured execution / preregistered limit | `1,119.19 s / 1,200 s` |

Both the exact-supply and bounded-compute gates are green. This confirms that
the generic clusters² tree can preserve exact three-block alternatives on a
new disjoint IQC nucleus without target access and without eagerly expanding
the entire marking library. It does **not** choose one of those alternatives,
commit an autonomous antichain, identify a stationary production, or establish
exponential IQC growth. Those remain the next gates.

### Commuting closure and child-transfer boundary

The first frontier now has a stricter order-independence certificate. A bounded
subset dynamic program accepts a three-action closure only when every one of
its six permutations replays to the same colored state. A group-heldout
incidence marking retains exact closure supply in all four development nuclei;
the consumed top-eight audit contains two exact parents. This is the contract
used by the UI when it displays several simultaneous frontier flashes.

The corresponding second-frontier value remains red. Its immutable training
corpus contains `3,994` candidates and `95` exact labels. Conditional
four-nucleus holdout keeps all `14 / 14` exact parent branches inside a
per-parent top `16`, but a fifth consumed geometry places its only two exact
six-action continuations at ranks `132` and `133`. Neither is selected. The
model and the failure receipt are byte-pinned so this negative transfer cannot
be hidden by downstream tree breadth or target-guided retuning. The next
representation must transfer the parent-to-child obligation change; no fresh
confirmation is eligible yet.

A fixed feature ablation confirms that this is not just excessive section
dimension. All six arms rank the identical `1,220` consumed candidates under
the same top-`16` budget. Removing nearest-neighbor slots, radial bins, or all
`408` site coordinates still supplies neither exact child. The four legacy
connection scores are best among these coarse controls, but the exact actions
remain ranks `95` and `96`. Coarsening loses development supply before it gains
transfer. A new marking must represent which typed parent obligations are
discharged and created by the child, rather than summarize either endpoint in
isolation.

That identity-preserving transition has now been tested directly. Every
candidate becomes a canonical six-node graph with three typed parent
obligations, three typed child obligations, and all proper-SE(3)-invariant
within/cross incidences (shared colored support, endpoint ownership, distance
profiles, and chirality). The order-two value supplies `12 / 14` exact
development branches and moves the fifth-geometry exact ranks to `69` and
`71`; order three supplies `9 / 14` and reaches ranks `78` and `80`. Both miss
the unchanged top-`16` gate. Explicit obligation correspondence is therefore
directionally useful but insufficient, and neither model is exposed as a
selectable autonomous marking.

Serve the repository root and open `/iqc-growth-live/`.
### Fourth-block IQC replay and marking transfer

The generic lineage executor previously canonicalized all nine stored actions
at once before splitting them into three public-radius blocks.  That global
sort could move an action into the wrong radius and falsely reject an exact
lineage.  Canonicalization is now block-local.  On the corrected development
receipt, all `64 / 64` retained parents replay and reach eight produces `8,872`
fourth-block successors.  A consumed-target reach audit proves that the frozen
geometry contains an exact continuation at proposal ranks `7 → 9 → 9`; reach
eight therefore tops out at `11 / 12` correct actions, while reach nine exposes
exact supply.

A new bounded pose/port marking keeps the same five invariant channel families
and is trained only on consumed nuclei 0 and 1 (`10,721` causal candidate
descriptors, `1,044` positives).  On untouched nucleus 2 it is frozen before
the target is opened and runs at the cheaper reach-eight budget.  All `64`
parents replay, yielding `8,382` successors.  Post-hoc scoring finds `82` exact
twelve-action continuations, distributed across all `14 / 14` exact parents in
the beam.  This is a green fourth-block **marked proposal-supply** result.

A subsequent same-nucleus ablation freezes both reach-eight receipts on
untouched nucleus 3 before opening its target. The unmarked arm produces `96`
exact successors from `10,868` unique geometry expansions; the marked arm
produces `100` exact successors from `11,078`. Both cover all `16 / 16` exact
parents. The `1.0417×` exact-supply gain costs `1.0193×` geometry work, below
the predeclared `1.05×` cap, so the causal marked-supply gate is green.

The next one-shot autonomous test freezes a causal 32-branch shortlist and a
fifth-block rollout before opening untouched nucleus 4. It is honestly red:
the shortlist contains `0` exact branches. Post-hoc scoring of the unchanged
full receipt finds `96 / 8,649` exact successors under only two parents; their
first exact global rank is `116`, but the first exact child is rank `2` within
each parent. A parent-balanced width-two beam would retain both exact parents
in `128` branches. The next fresh confirmation therefore preserves parent
diversity instead of applying another global cutoff.

No retry is claimed on consumed nucleus 4. Autonomous, stationary, and
exponential IQC growth remain red.

### Fresh parent-balanced fourth-block confirmation

The post-hoc width-two observation was not used as the final policy. A
train-only cross-nucleus audit found that width eight per parent preserves all
exact-parent groups on both development folds (`14 / 14` and `16 / 16`). The
fresh executor therefore keeps eight nine-action parents under each of eight
first-block parents, then eight marked fourth-block children under each of
those 64 parents. Candidate identity, geometry, scores, and parent assignment
freeze before a fresh target is opened.

The first maximin nucleus `(280,220,0)` produced a valid 512-candidate receipt,
but its confirmation harness compared six-decimal frozen actions to target
coordinates with exact eight-decimal dictionary lookup. Its reported `0 / 512`
is preserved as a **scorer-harness failure**, not interpreted as scientific
transfer, and that target is not reopened or retried.

A second geometry-only maximin centre `(-280,160,-160)` adds the failed domain
to the exclusion set, uses the established species-aware `10⁻⁵` matcher, and
stores the opened target sites for independent audit. This corrected one-shot
is scientifically valid and red:

| fresh parent-balanced receipt | measured |
| --- | ---: |
| seed / target atoms | `483 / 47,526` |
| complete nine-action lineages before selection | `1,114` |
| retained nine-action parents | `64` |
| retained fourth-block candidates | `512` |
| exact fourth-block terminal triples | `8` |
| exact retained nine-action parents | `0` |
| exact complete twelve-action paths | `0` |
| best complete path | `11 / 12` |
| target-blind execution time | `1,721.03 s` |

Thus fourth-block connection geometry still transfers—the receipt contains
eight exact terminal triples—but the selected nine-action parents are all
inexact. Because the receipt did not serialize the other 1,050 unretained
nine-action lineages, this run cannot distinguish raw parent-supply failure
from selector loss without prohibited re-execution. The next executor must
serialize the full parent antichain, record per-stage timings, and cache shared
fourth-frontier prefixes. Autonomous, stationary, and exponential IQC growth
remain red.

The auditable V3 executor now closes that instrumentation gap on the already
consumed development nucleus `(-70,10,70)`. It freezes all `1,102` raw
nine-action lineages before post-hoc scoring. Three raw lineages under one
parent are exact, and all three survive the 64-lineage parent-balanced
selection. The following 512 fourth-block candidates contain `21` exact full
twelve-action paths and `476` exact terminal triples. Thus, on this consumed
nucleus, the selector preserves the available exact parent; it is not the
failure boundary.

This remains diagnostic evidence, not a new fresh confirmation. Runtime is
also red at `2,179.18 s` against the fixed `600 s` engineering gate. The
measured stages are `383.44 s` for first/second frontiers, `169.53 s` for
scheduled third frontiers, `208.02 s` for transported port graphs, `44.38 s`
for fitting/selection, and `1,373.81 s` for chunked fourth frontiers. The last
stage accounts for 63.0% of execution time and is now the primary optimization
target. Normal regressions load the pinned 50 KB receipt fixture rather than
rerunning this 36.3-minute audit.

Profiling one frozen fourth-stage parent attributes most remaining work to
repeated nearest-prototype assignment: the uncached path performs tens of
millions of identical local-color comparisons. A new target-free cache reuses
the mapping from each exact local cluster color to the frozen prototype table.
On that parent it preserves the identical `8 → 38 → 143` state sequence and
action digest while reducing `43.97 s` to `18.85 s` (`2.33×`). Incremental
local-cluster typing, exact anchored-support indexing, single-pass port-channel
responses, and bounded memoization of finite semantic port roles then remove
the other repeated inner-loop work.

The complete target-free construction has now been replayed with every frozen
scientific output identical: second-branch receipt, scheduled prefix, lineage
model, all `1,102` raw lineages, the same 64 selected indices, all 512 fourth
candidates, and the final deterministic receipt. Runtime falls from
`2,179.18 s` to `436.36 s` (`4.99×`), passing the fixed `600 s` engineering
gate. The stages are now `83.92 / 74.42 / 18.97 / 44.47 / 214.58 s`; the last
number is fourth-frontier generation. This turns only the consumed-audit
runtime gate green. It does not turn the fresh disjoint result, autonomous IQC
growth, stationary recursion, or exponential growth green.

The same auditable executor was then frozen before a third fresh confirmation
at the geometry-only maximin center `(-180,-80,-300)`, `231.52` units from the
nearest recorded nucleus. Its target-free receipt contains all `1,087` raw
nine-action lineages, 64 selected lineages, and 512 complete twelve-action
candidates before the 47,530-atom target is opened once. Post-hoc scoring finds
zero exact raw nine-action lineages, zero exact complete paths, but 197 exact
terminal fourth blocks. Six candidates reach `11 / 12`; all share the same one
incorrect upstream action. Runtime is `534.84 s`, so the engineering gate
transfers to the fresh domain. Scientifically, this localizes failure to
upstream parent supply—not selector loss or fourth-block connection geometry.
No retry or fallback was run.

An experimental V4 upstream policy now keeps every joint prefix and adds at
most four alternatives only when they remove an action shared by all eight
joint parents. Across four consumed development cases it retains all six known
exact child groups with `40` prefixes total (`10` per case on average), versus
`189` for the full frozen schedule. When no universal action exists it adds no
fallback and reproduces the V3 `1,102`-lineage digest exactly. A wider
16-prefix development run still gets its three exact nine-action lineages from
the original joint tier and zero from the fallbacks, so V4 remains an
experimental coverage hedge—not a demonstrated scientific improvement or a
reason to consume another fresh target yet.
