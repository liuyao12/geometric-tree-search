# Recursive GCTS benchmark for material growth

### Atomic transition-path microscope (Build 367)

Validated coordinate chains are now inspectable as actual atomic structures,
not only as scalar energy points. The selected event supplies one rotatable
CPU-projected local scene. The image slider, accessible energy-profile points,
and playback control select only indices present in the returned path; playback
does not synthesize intermediate frames.

This audit is not conditional on a kinetic model. An event selector exposes all
validated path records as soon as barriers are bound, while the HTST spectrum
continues to fail closed until complete prefactors are present. When the
spectrum is enabled, its inspected event and the path selector share the same
candidate ID.

Every dynamic site is drawn in the standard element color. Filled, outlined,
and dashed glyphs distinguish material, interface, and reservoir domains.
Invariant material context is chosen by one deterministic rule: display at
most the 180 fixed sites nearest any material- or interface-domain dynamic
coordinate anywhere in the complete validated chain. Consequently the context
set is stable across images and the
readout reports displayed versus validated fixed-site counts. Sampled trails
are projected from the exact returned coordinates and are explicitly labeled
as sample connections rather than trajectories integrated in time.

The per-image audit exposes ξ, energy relative to image zero, maximum force,
saddle status, and domain populations. The experiment receipt retains the
candidate/image selection, projection type, neighborhood cap, and negative
interpolation and target-use flags. Orbiting affects only the projection. This
viewer is evidence presentation; it neither modifies the path nor licenses a
mechanism that the external response did not contain.

### Coordinate-bearing external action paths (Build 366)

The v4 frozen-action response closes the gap between a scalar transition
barrier and the exact candidate geometry it is meant to rank. Every returned
record now includes at least three coordinate-bearing images with stable site
IDs and species, a strictly increasing reaction coordinate, energy and maximum
force per image, and an internal maximum-energy saddle. Invariant material
sites are stored once and combined with the dynamic sites during validation,
which keeps the representation proportional to the moving environment rather
than multiplying the full specimen by the image count.

For a surface hop, all sites remain in a closed, fixed-composition material
domain. Attachment, detachment, and exchange use a constant-cardinality
extended system with a hashed, described gas, solution, surface-feedstock, or
bulk reservoir boundary. The validator moves sites among material, interface,
and reservoir domains while preserving their IDs and species. This is the
appropriate open-system construction for actions whose material-domain atom
population changes; they are not mislabeled as fixed-composition NEB paths.

The first and final material multisets are reconstructed from coordinates and
checked against the frozen endpoint hashes. The profile independently
reproduces ΔE‡, optional endpoint ΔE, and the reported maximum image force. The
interactive kinetic panel draws the selected candidate's profile and exposes
its saddle, image-domain populations, reservoir condition, and adjacent-image
displacement. Response validation fails closed if a path is missing, claims a
false validation flag, changes an endpoint, changes a path-site species or ID,
or disagrees with the scalar calculation record.

This is a candidate-bound calculation handoff, not a browser-generated
reaction path. Passing the gate does not establish path uniqueness, a global
minimum-energy path, mechanism completeness, recrossing corrections, rate
theory, reservoir validity, or transferability of the external method.

### Exact local species exchange (Build 365)

The finite Stage 4 mechanism catalog now has a fourth event family. A local
species-exchange action combines an ownership-certified removable leaf with an
independent hard-admitted destination within the declared nearest-neighbor
reach. It is admitted only when the removed and emitted supports are equal in
size, nonempty, differently colored, and have an integer species delta that
sums to zero. No atom used as destination overlap may be removed by the source
half of the event.

The action-barrier contract hashes the initial configuration, every exact
removed/emitted/action site, and the derived final colored state. At commit the
browser repeats ownership, admission, feedstock, independence, count,
candidate-digest, and final-state checks before replacing the source support
and updating the species ledger as one transaction. The kinetic contract and
interactive spectrum report attachment, detachment, hop, and exchange masses
separately. A reversed exchange is recognized only through exact reversed
state hashes and opposite species deltas, not through a material label.

This closes an endpoint-level mechanism gap without pretending geometry is
chemistry. The external method must still provide a converged barrier,
uncertainty, and prefactor for every frozen action. Optional independently
supplied chemical potentials contribute reservoir work; they are not learned
from the grown structure. The result is not a transition path, transmutation,
mechanism completeness, equilibrium composition, or global detailed balance.

### Periodic pressure-and-strain relaxation (Build 364)

The mechanics handoff now has an explicitly authorized variable-cell branch
for fully periodic three-dimensional states. Its request hashes the exact
colored sites together with the reported 3×3 cell and periodic axes. The
policy is either byte-exact fixed cell or variable cell at one selected
isotropic pressure; no solver is permitted to infer that authorization from
the material label.

The v2 response binds both the initial geometry and complete initial state,
then supplies independently recomputable final geometry and final-state
digests. Variable-cell validation requires a finite nonsingular cell with the
same handedness, unchanged periodic axes, symmetric stress with explicit unit
and convention, the frozen target pressure, and a nonnegative maximum stress
residual. Fixed-cell validation rejects any changed cell entry. Atom IDs,
species, and count remain exact in both modes.

For interpretation, the portal computes `F = H_final H_initial⁻¹` and the
Green–Lagrange strain `E = (FᵀF − I)/2`, reports ΔV/V, and resolves every atomic
motion into the affine image of the original fractional coordinate plus a
minimum-image non-affine residual in the final cell. The validated cell,
periodicity, coordinates, energy/force/stress evidence, and method provenance
are adopted together into a new observation. The ordinary structure validator
and every geometric learner are then rebuilt.

This is a method-bound constant-pressure endpoint, not an in-browser barostat,
trajectory, thermal NPT ensemble, equation of state, elastic modulus, phase
boundary, or claim that the external method is valid outside its documented
domain. Partial periodicity and intrinsic-2D cells remain fail-closed until a
separate constrained-cell contract defines their admissible degrees of
freedom.

### External post-leap relaxation loop (Build 363)

The portal now implements the missing mechanics leg of the leap-frog workflow.
One explicit grown configuration is frozen as a colored, ID-bearing Cartesian
state and exported to an external fixed-composition relaxation calculation.
The request is target-free and includes an exact initial-state SHA-256, finite
boundary provenance, allowed method classes, required outputs, and a
fail-closed statement that atom count, atom IDs, species, and the cell policy
may not change.

Response validation is exact rather than label-based. It requires a bijection
over all frozen atom IDs, unchanged species, finite coordinates, a recomputed
final-state digest, converged finite total energy and residual-force metrics,
an explicit convergence criterion and iteration count, and method/settings
provenance. The resulting receipt separates the returned endpoint from the
unobserved path and records RMS/maximum displacement without treating either as
elapsed time.

Adoption is a new observation round. The returned geometry is passed through
the ordinary imported-structure validator and the complete cluster-cover,
orientation, marking, and grammar learners are rebuilt. No pre-relaxation
cluster or production is silently retained as exact. This gives a realistic
co-simulation loop in which an external solver resolves local mechanics at
selected structural checkpoints while GCTS skips the intervening dynamical
integration.

The Build 363 contract keeps a finite boundary and fixed composition/cell. It
does not infer a relaxation path, transition state, physical relaxation time,
thermal ensemble, force-field validity, atom exchange, or variable-cell
thermodynamics. Build 364 closes only the explicitly authorized fully periodic
isotropic-pressure endpoint; atom exchange and unconstrained cell protocols
remain absent rather than implicit browser behavior.

### Exact mass-conserving surface hops (Build 362)

The event-resolved growth stage now has a third finite mechanism family. Each
surface-hop candidate is the composition of an ownership-certified detachable
leaf and an independent hard-admitted attachment endpoint. The source and
destination must have the same cluster class and exactly equal colored atom
population; destination support cannot use an atom removed at the source; and
the endpoint centroids must lie inside the user-declared local reach in units
of the specimen nearest-neighbor spacing.

Execution revalidates source ownership, destination hard admission, candidate
identity, exact colored final geometry, and unchanged atom count immediately
before commit. It removes the source without returning atoms to a reservoir,
materializes the destination without consuming feedstock, and records one
atomic structural event. The candidate-resolved external calculation remains
responsible for the transition path, barrier, uncertainty, and attempt
frequency. Hop probability mass is reported separately in the interactive
frozen-event spectrum.

This closes an important mass-conserving surface-rearrangement gap while
retaining a strict claim boundary. The finite catalog is capped and local; it
does not enumerate all diffusion, exchange, concerted, reconstruction, or
bulk-defect mechanisms. Exact endpoints do not determine the intervening
trajectory. A validated inverse pair can test local balance only with explicit
thermodynamic evidence and does not establish equilibrium or a complete
kinetic model.

### Frozen-event kinetic spectrum (Build 361)

Once a complete candidate-resolved barrier/prefactor response is bound, the
portal now preserves and visualizes the entire finite kinetic competition. The
pure spectrum audit sorts the unchanged frozen action IDs by HTST rate, retains
the independently supplied barrier and prefactor uncertainty envelope, and
computes probability mass by event direction, rate span, Shannon effective
event count, nominal selected-event rank, and the set whose rate uncertainty
overlaps the nominal fastest candidate.

The SVG can switch between `log10(k / s⁻¹)` and probability within the frozen
catalog. Every attachment or ownership-certified leaf-detachment point is
keyboard/click inspectable, while the event already selected by maximum-rate
HTST or the seeded KMC draw is marked separately. The visualization changes no
candidate ID, pose, hard gate, rate, random draw, or selected event. The compact
statistics are included in the action-checkpoint receipt with explicit
`targetUsed=false`, `candidateSetChanged=false`, and
`selectedEventChanged=false` fields.

All probabilities remain conditional on the enumerated hard-admitted catalog.
The spectrum does not claim coverage of diffusion, reconstruction, concerted,
nucleation, desorption, recrossing, quantum, or other absent mechanisms, and it
does not turn a finite event catalog into an equilibrium or complete kinetic
model.

### Shared-state coherence across coupled physics (Build 360)

Coupled execution now has an explicit cross-response state contract. Spatial
interface transport `J(x,n̂)`, active orientation attachment kinetics `v(n̂)`,
and candidate-level HTST evidence each expose a 64-hex driving-state digest.
Every active channel must be validated, current for the geometry it describes,
and equal on that digest; separately supplied temperatures must agree within a
fixed numerical tolerance.

When a current state is available, the frozen action-barrier request records its
digest, optional Kelvin temperature, and the evidence channels that established
it. A kinetic response must reproduce the expected digest. If a temperature was
frozen, both kinetic and optional grand-canonical thermodynamic evidence must
match it. Response-bound temperature becomes the immutable temperature used by
the subsequent HTST/KMC competition.

The leap-frog execution gate is now ordered as follows: current target-free
geometry → current interface transport → frozen frontier → validated complete
barrier/prefactor response → explicit maximum-rate or seeded-KMC event selection
→ shared-state coherence → exact structural commit. A mismatch releases no
action and the UI identifies the offending channel or temperature.

This contract prevents accidental mixing of simulations performed under
different reservoirs, temperatures, or boundary conditions. It does not prove
that the shared state is physically complete or accurate, infer a missing state
from geometry or labels, establish equilibrium/detailed balance, or complete an
enumerated mechanism catalog.

### Catalog-conditional kinetic leap chronicle (Build 359)

Seeded HTST/KMC evidence is now accumulated as a persistent chronology rather
than disappearing with the consumed action checkpoint. For each committed
clocked leap the record retains the frozen event-catalog size, exact selected
candidate and direction, temperature, selected and total rates,
within-catalog probability, exponential waiting-time draw, conditional clock
bounds, event-count bounds, and structural atom-count change.

The chronology validator requires nonnegative finite clock values,
`clock_after = clock_before + Δt` within numerical tolerance, exactly one event
count increment per clocked leap, and continuity between successive retained
clocked events. It reports accepted structural leaps without clock evidence and
whether the retained history is truncated. The browser renders the waiting-time
spectrum on a logarithmic visual scale, supports per-event inspection, and
exports the complete conditional receipt to growth and notebook artifacts.

This does not turn GCTS scores or wall time into kinetics. An event is clocked
only after the exact frozen hard-admitted catalog has complete method-bound
barriers and converged prefactors and a seeded KMC draw chooses one action.
Unenumerated mechanisms, unclocked structural leaps, and catalog incompleteness
remain explicit. Consequently the sum is not an unconditional material clock,
bulk growth rate, integrated trajectory, or MD speedup.

### Leap-frog multiphysics refresh cycle (Build 358)

The portal now exposes the evidence lifetime around every exact GCTS state as a
six-node dependency cycle: colored geometry, persistent material evidence,
current-interface transport, frozen frontier, candidate-resolved event
evidence, and structural leap. A fingerprinted pure model decides whether the
selected coupling contract is current and names the next required action.

The contracts are deliberately nested. Structural mode retains the exact GCTS
geometry/connection/collision gates. Interface mode additionally requires a
validated `J(x,n̂)` response whose bound state digest equals the current
geometry digest. Event mode also requires a validated response bound to the
current action-frontier generation and candidate-batch digest. A voluntarily
opened event checkpoint blocks even structural execution until it is resolved,
so a user cannot silently bypass a calculation they explicitly attached.

An accepted leap increments the geometry revision and invalidates all
interface-scoped and action-scoped evidence: the spatial flux map, frozen
candidate batch, and candidate barriers/prefactors. The learned geometric
grammar and reference-bound material responses remain. This gives an explicit
external-physics → exact GCTS leap → refresh loop while preserving the existing
target-free search and exact hard certificates.

The browser does not execute the external solver, infer a missing response,
prove that a finite action catalog is complete, integrate a trajectory, or map
wall time to physical time. The cycle is an auditable co-simulation protocol,
not an additional physical model.

### Transport–attachment rate-control bridge (Build 357)

The interface audit now compares the two unit-bearing steady-state quantities
that Builds 355 and 356 kept separate. For a selected three-dimensional
periodic reference, the exact supplied cell and crystallographic occupancies
give the site number density
`ρ_site = Σ occupancy / V_cell` in atoms m⁻³. Each validated flux patch then
has a supply-equivalent velocity `v_supply = J / ρ_site`, which can be compared
with the orientation-interpolated attachment velocity `v_attach(n̂)`.

Compatibility is explicit rather than inferred from labels: both responses
must carry the same optional 64-hex `couplingStateSha256`. Missing or unequal
digests, a stale frozen interface, a nonperiodic specimen, a 2D cell without a
physical thickness, or absent oriented velocity support leaves the physical
bridge unavailable. Existing standalone J and v validation remains backward
compatible.

Classification uses uncertainty, not an arbitrary ratio cutoff. A patch is
supply-limited only when the three-sigma upper bound of `v_supply` lies below
the three-sigma lower bound of `v_attach`; attachment-limited uses the reverse
inequality; every overlap remains unresolved. The plot reports
`log10(v_supply/v_attach)`, support/abstention, and the three regime counts.

No composite search score is added. In particular the bridge does not assume
resistances in series, infer an effective interface velocity, or integrate a
clock. It flags simultaneous use of the independent J and v frontier priors as
a possible double-counting hypothesis. This makes the physical bottleneck
auditable while preserving the exact candidate set, geometry, and hard GCTS
certificates.

### Spatially resolved interface transport handoff (Build 356)

The browser now represents nonuniform material supply as a distinct external
evidence layer.  It exports an exact request bound to the colored structure,
frozen finite interface, transported species set, public growth boundary,
source provenance, and recorded conditions.  A valid response supplies a
predeclared interface quadrature with Cartesian positions, oriented outward
normals, area weights, species-resolved steady incorporation fluxes, and
one-sigma uncertainties in atoms m⁻² s⁻¹.

Validation is deliberately stronger than accepting a colored scalar field:
request, structure, interface, method, settings, and boundary-condition hashes
must agree; per-patch species fluxes must sum to the reported net flux; every
net flux must remain positive at three sigma; the solver must declare
convergence and a verified steady window; global mass-balance residual must not
exceed 10⁻³; and the declared mesh-refinement change must not exceed 5%.  A
failed field remains display-ineligible and cannot enter search.

An optional target-free rank term interpolates only among locally supported
patches using compact kernels in normalized interface position and signed
outward-normal angle.  The dimensionless score is
`tanh(log J_candidate − mean(log J_patch))`. Unsupported candidates abstain.
The exact candidate list, cluster pose, emitted atoms, GCTS marking, collision
checks, connection ports, and hard admission do not change.  The matched audit
retains support coverage, abstentions, pairwise rank inversions, leader change,
and the frozen candidate-set digest.

This closes the uniform-driving limitation of the orientation-only kinetic
habit without pretending to solve transport inside GCTS.  Source-ray
visibility is not reused as physical flux, and neither morphology, γ(n̂), nor
v(n̂) supplies J(x,n̂).  The map applies to one frozen interface and boundary
condition; it is not a concentration or chemical-potential field, inferred
diffusivity, sticking probability, moving-boundary solution, universal growth
law, or physical clock.

### Catalog-conditional HTST / KMC execution (Build 346)

Build 345 froze exact action geometry and accepted candidate-resolved barriers,
but deliberately stopped before rates.  Build 346 makes the additional
evidence requirements executable.  A kinetic response is eligible only when
every requested action has a finite positive converged attempt frequency,
log-scale prefactor uncertainty, a method/settings digest, a declared
recrossing treatment, and the exact catalog scope
`requested-hard-admitted-actions-only`.  Kinetic fields without the complete
root declaration, or any missing/invalid/unconverged candidate prefactor,
invalidate the response rather than silently falling back.

For declared temperature `T`, the browser computes
`ln k_i = ln ν_i − E_i/(k_B T)` and the frozen-catalog partition
`p_i = exp(ln k_i − logsumexp_j ln k_j)`.  Barrier and prefactor uncertainties
produce per-action lower and upper `log10(k/s^-1)` bounds.  Maximum-rate mode
chooses one deterministic action and advances no clock.  Seeded KMC mode uses
two FNV-keyed uniforms bound to the growth seed, event index, and request SHA:
one selects an action from the catalog CDF and the other gives
`Δt = −ln(u)/Σ_i k_i`.  Candidate-ID order is canonical, so input record order
cannot alter either draw.

Execution remains exact and target-free.  Kinetic mode overrides commuting
display scheduling with one serial event, but then reuses the existing whole
cluster commit path and every hard certificate.  The clock changes only after
one accepted event; failed or released checkpoints contribute no time.  Full
receipts include the method and prefactor digests, catalog size, temperature,
selected candidate, nominal/log-bounded rates, uniforms, waiting time, and
clock before/after.  The physics ledger and scale passport distinguish this
finite-catalog kinetic leap from the reduced thermal-field geometry and from
dimensionless Gumbel path exploration.

The claim is intentionally conditional: the enumerated hard-admitted frontier
is not proved to contain every physical mechanism.  The result is therefore
not an MD trajectory, transferable potential, equilibrium ensemble, complete
kinetic model, diffusion coefficient, nucleation rate, or unconditional
material clock.  This closes one bounded dynamics-to-geometry leap while
keeping missing mechanisms, recrossing, correlated events, quantum effects,
and model error explicit.

### Frozen-frontier external action barriers (Build 345)

The Stage 4 policy workbench now has a calculation checkpoint at the exact
selection boundary.  It evaluates and freezes the target-free frontier, pauses
before any branch is selected, and exports every hard-admitted action with the
initial state, emitted and complete action sites in ångströms, stable IDs,
per-action digests, and a batch SHA-256.  This action-level protocol is kept
separate from the earlier preflight evidence request because the candidate set
does not exist at preflight time.

Validation is deliberately all-or-nothing: exactly one converged path record is
required for every candidate ID, with matching request/state/batch/action
digests, declared method settings, uncertainty, independent holdout, residual
force convergence, and no-target/no-score-label/no-search-clock safeguards.
The response cannot add or remove candidates.  A robust within-batch
`tanh((median(E)-E)/(2 max(1.4826 MAD, range/4)))` coordinate makes lower
barriers favorable; the user must explicitly choose its bounded soft weight.
The term is included in the exact additive score ledger, normalization audit,
physics lineage, structural-leap certificate, and full experiment receipt.

This closes the calculation-to-exact-action handoff but not kinetics.  The
barrier is scoped to one frozen frontier and method; it is not a transferable
potential, transition probability, rate, or GCTS clock.  Candidate geometry and
all hard admission certificates remain unchanged and are checked again at
commit.  Performance or physical-time speedup is not claimed by this portal
contract alone.

### Residual-force connection marking deployment (Build 344)

Residual forces already had a proper-pose transport law and an optional capped
post-attachment projection, but they did not inform the learned connection
section.  Build 344 adds a separate explicit representation.  For a directed
port with unit axis `u`, it computes
`p_in = 1/2 (F_i − F_j)·u` and divides by the finite observation's force-vector
magnitude p90, clipping only the marking feature to `[-1,1]`.  The result is
unchanged by a common proper rotation and enters the existing pose × port
target with fixed bounded weight `0.12`.

**Force-projected ports** is disabled without a complete validated force
response on the exact observation.  Its frozen config records the response
SHA, so marking-library compatibility fails closed if that evidence is removed
or replaced.  Gold and dashed blue connections in the separate cluster cards
show positive inward and outward residual projections; receipts retain the
normalization, summary statistics, source hash, and execution boundaries.

The candidate set, exact poses, overlap/collision tests, and hard admission are
unchanged.  The feature may affect ranking only through an explicitly trained
marking.  It is not interpreted as a bond, attraction/repulsion law,
transferable force field, energy landscape, mechanical equilibrium, physical
relaxation trajectory, rate, or clock.  No performance benefit is asserted
without a later identical-candidate ablation.

### Collective trajectory marking deployment (Build 343)

Per-site covariance does not say whether neighboring environments move
together or against one another.  Build 343 therefore adds a second,
connection-local geometric statistic for validated trajectories.  After
per-frame translation removal and subtraction of each site's time-weighted
mean displacement, the browser computes the normalized cross-covariance trace
and the longitudinal correlation along every train-witnessed port.  Both are
invariant under a common proper rotation; the longitudinal term enters the
existing pose × port marking target with a fixed bounded weight of `0.14`.

Deployment is explicit and response-bound.  **Trajectory-correlated ports** is
disabled until a validated ordered path is active.  A trained library entry
stores that response SHA and becomes incompatible when the evidence changes or
is removed.  Cyan solid and pink dashed edges in the per-cluster learning cards
show positive and negative longitudinal correlation, while the receipt records
summary statistics and all causal boundaries.

This channel may reorder the unchanged candidate set only after the user
selects and trains it.  It does not create geometry, change overlap/collision
certificates, or claim a bond, energy, force constant, phonon eigenmode,
causality, equilibrium distribution, potential, barrier, rate, or mapping from
a GCTS leap to trajectory time.  No performance advantage is claimed without a
separate frozen-candidate ablation.

### Trajectory covariance deployment (Build 342)

The validated path channel now has a tensor-valued local section. With strictly
increasing physical times `t_i`, normalized trapezoidal weights integrate each
site's drift-removed displacement over the supplied window. The browser stores
the weighted mean and symmetric covariance about that mean in observation
Cartesian Å², then applies the same proper-pose tensor law used for a rigid
cluster environment: `C_world = R_cluster C_local R_cluster^T`.

The execution boundary is explicit. The empirical covariance is display-only
when first encoded; it appears as an ellipsoid in cluster cards, placed atoms,
and candidate previews without affecting the candidate set or ordering. The
user may separately choose **1σ directional clearance**, which rebuilds the
frozen local contact envelopes and admits the trajectory tensor only to the
existing hard directional-contact calculation. Reverting to display-only
relearns without that tensor. Both modes are receipt-visible.

Reported U/B covariance and empirical path covariance are not conflated. The
latter is a deterministic statistic of one request-linked trajectory after
translation removal. It assumes neither thermal equilibrium nor a phonon model,
and it does not infer a probability distribution, potential, rate, barrier, or
clock. Global rotation remains in the response geometry and is reported rather
than silently fitted away.

### Validated trajectory-to-section deployment (Build 341)

The trajectory response now has an executable but deliberately bounded
promotion path. Validation first binds it to the exact request and structure;
the local geometry route additionally requires frame zero to equal the ordered
observation within `1e-7 Å`. Per-frame center-of-configuration translation is
removed before the browser derives per-site endpoint displacement, maximum/RMS
excursion, and path length. The vector is stored in the cluster-local frame and
transported by the candidate's proper rotation. Scalar path channels follow the
same site without acquiring an orientation.

Only frame zero supplies clustering, the cover, ports, marking fit, and the
growth seed. The response frames do not pool into those structural statistics.
The transported endpoint can seed the existing capped post-attachment contact
projection only after a separate user choice; it is ignored if the initial
contact objective worsens, and the whole result rolls back if exclusion,
coordination, angle, boundary, topology, or port certificates fail. Candidate
generation, exact poses, hard admission, and branch ranking are invariant under
the binding itself.

The timestamps are real evidence for the supplied trajectory, not a clock for
GCTS. The receipt reports the physical frame count and span, response/method
hashes, drift convention, vector and path summaries, proper-pose transport,
and explicit `trajectoryIntegratedByGcts=false` and
`suppliedTimestampsUsedAsGctsClock=false` flags. Global rotation is not removed
and is reported as such; this prevents a hidden alignment claim. This route is
local geometric response reuse—not MD, a transferable kinetic model, a
minimum-energy path, a barrier, path probability, or growth-rate calibration.

### Validated force-to-geometry deployment (Build 340)

Among the six returned evidence types, site-resolved forces now have the first
executable promotion path because their transformation law under a rigid
cluster pose is explicit. A full response on the exact observation can be bound
only after request-linked validation and a separate user action. The binding
keeps site order under the validated structure digest, stores each vector on the
observed site, learns it in the cluster-local frame, and transports it by the
cluster's proper rotation. The browser reports reference, template, rule,
candidate, and placed-vector coverage plus the response hash and validation
state.

The promoted object is a vector-valued geometric hypothesis, not a potential.
Binding leaves support discovery, exact action poses, hard admission, and branch
ranking invariant. The only executable use is the pre-existing bounded
post-placement contact-residual projection, which still requires its own force
mode selection, caps displacement relative to the sample force p90, rejects a
worsening initial direction, and rolls back the whole projection on any failed
certificate. The response is cleared when the specimen or observation frame
changes. Trajectories, clocks, barriers, free energies, and probabilities remain
validated evidence only until equally explicit representation and transfer
contracts exist.

### Request-linked returned-evidence validation (Build 339)

External physics now returns through the same evidence boundary by which it
left. The request serializes an explicit response contract and both permitted
configuration digests. The browser accepts a response only when its request
hash, quantity, observation-or-seed role, structure hash, program or instrument,
settings hash, no-target safeguards, and the complete frozen validation gate
agree. Mismatches fail closed before the evidence plan or receipt changes.

Validation is quantity-specific. Trajectories require a fixed site count and
strictly increasing physical times; clocks require exposure, event, censoring,
and rate records; barriers require an explicit energy profile, endpoints, and
force convergence; free energies require uncertainty, ensemble, and
temperature; probabilities require exposure and independent trajectory counts;
and forces require one finite vector per matched site, total energy, and a valid
optional stress tensor. The resulting audit is scoped to that configuration
and method. It is evidence, not automatic authorization: candidate generation,
ranking, geometry, potential use, and physical-time use remain false. Only a
separate preregistered transfer study can promote a returned physical channel
into GCTS execution.

### Calculation-ready external-physics handoff (Build 338)

The 45-layer physics-to-geometry manifest already identifies where the browser
has direct evidence, a geometric proxy, or no physical evidence. Build 338
closes the operational gap after that diagnosis: any of the six unresolved
quantity classes—trajectory, clock, barrier, free energy, transition
probability, or force—can be serialized as a local, solver-neutral request.
The request contains exact supplied-observation and explicit-growth-seed
coordinates in Å, species and optional occupancy/charge/spin channels, cell and
periodicity, measurement conditions and provenance, suitable calculation
families, required outputs and units, and the frozen validation criterion.

This is a handoff artifact, not a hidden simulation backend. The browser sends
nothing automatically; target coordinates are absent; geometric ranking is not
an energy label; search depth is not a clock; and no kinetic, thermodynamic, or
force claim changes when the file is downloaded. The experiment receipt records
only a SHA-256, atom counts, units, and the no-submission/no-target safeguards,
so the coordinate-bearing package remains explicitly local. A later imported
result must still pass the quantity-specific validation gate before it can
support a physical interpretation.

### Live continuation-evidence ladder (Build 337)

The growth-stage controls now expose the benchmark hierarchy as an interactive
claim ladder rather than leaving it split across captions, the certificate,
and the Evidence atlas. The rungs are intentionally non-interchangeable:
complete cluster-plus-residual cover proves representation; target-free emitted
sites prove a finite structural continuation; a spatially disjoint frozen
candidate test proves an exterior transfer; and an exact production recurring
across independently verified scales is required for a stationary or
exponential representation law.

Buttons on the first three rungs select the known-window replay, fitted local
frontier, or IQC-only sealed disjoint confirmation without changing the frozen
scientific definitions. The fourth opens the full benchmark evidence. Live
state, denominators, target-use boundary, and O(N) explicit-materialization
cost are included in receipts. Consequently, a deep tree, a large represented
count, same-sample envelope crossing, or finite fixed point cannot silently
promote itself to a stronger growth claim.

### Sealed spatially disjoint IQC frontier confirmation (Build 336)

The browser now exposes the backend's preregistered fresh-nucleus confirmation
as a separate IQC evidence-library growth mode. Its initial condition is a
473-site radius-nine model-set crop from a spatial domain disjoint from every
development nucleus. The browser artifact contains that seed and the frozen
fusion top-one three-site terminal only; it contains no 2,048-site held-out
target coordinates. All 128 terminals and their ordering were serialized
before the target opened once. Posthoc scoring found 90 exact terminals, and
both scalar and fusion top-one selected an exact three-site action.

This closes a specific gap left by Build 335: the displayed sites are beyond a
small, fresh seed rather than merely filling the original 507-site observation
envelope. It does not close the sustained-growth gap. In the self-fed second
block, 62/128 terminals are exact but the first exact scalar/fusion ranks are
13/16, fusion top-one is inexact, and the frozen portfolio supplies no exact
choice. The interactive trace stops at this selection boundary. Receipts expose
protocol, candidate-set, execution, and coordinate/species digests; target-use
flags; the single sealed backend target open; and the red autonomous,
stationary, and exponential claims.

### Executable exact-IQC fitted nucleus (Build 335)

The exact ideal-IQC fixture now recommends the already-supported local fitted
nucleus for the Material growth stage. This keeps the 507-site observation as
training evidence while initializing execution from one explicit 12-site
occurrence. It is target-free: the remaining observation sites are neither
snapped to nor scored, and all candidate poses come from the frozen local port
vocabulary. The observed-window initial condition remains selectable as the
separate complete-cover closure audit. Other materials retain the generic
observed-window default.

The browser audit starts with 52 frozen actions. Its first maximal commuting
set accepts 9 placements and emits 45 novel colored sites (12 → 57 atoms,
causal depth 1); the second reaches 95 atoms and depth 2. Continued updates
reach 501 atoms and depth 10. However, the growth-domain passport records 489
novel sites inside the fitted observation envelope and zero beyond it. This is
genuine finite self-fed execution, but it is not held-out exterior transfer,
autonomous growth, stationarity, an inflation rule, or an exponential claim.

### Exact ideal-IQC browser fixture (Build 334)

The browser's ideal-IQC control now comes from the same exact six-dimensional
model-set oracle used by the backend benchmarks. The committed radius-nine,
lift-bound-three fixture contains 507 physical-space sites and maps the oracle's
three internal-radius color classes to synthetic Al/Cu/Fe display colors (63 /
150 / 294). A generator check rebuilds the artifact and a JavaScript test
verifies its coordinate/species SHA-256. Hidden lifts and internal coordinates
are not shipped to the learner.

The sample is explicitly an algorithmic cut-and-project control, not an
experimental material or an Al–Cu–Fe structure determination. Its provenance
card has no article DOI, links to the exact generator, and its receipt records
`geometryFixture.fixtureClass=algorithmic`, `materialClaim=none`, and no
`publishedModel`. The published Cd–Yb fixture remains the real-material IQC
case.

The frontend evidence improves from 2 support types / 4 occurrences / 0 direct
rules on the displaced-grid surrogate to 9 support types / 85 occurrences /
139 direct support edges / 150 rules / 56 recurrent pose classes. Every support
type has an outgoing target-free port. This does not prove autonomous or
stationary IQC growth; it makes the browser sample geometrically consistent
with the ideal-IQC backend rather than preserving a mislabeled easy surrogate.

### Terminal-bridge proper-pose readiness audit (Build 333)

Each residual-mediated support pair is now composed in a proper intrinsic frame
and quotiented by source type, target type, exact colored terminal type,
translation tolerance, and proper-rotation tolerance. Recurrence requires two
distinct terminal occurrences; several pairs routed through one terminal cannot
manufacture independent support. The browser reports directed observations,
pose-class count, recurrent class count, and maximum terminal-occurrence
support.

This remains diagnostic by construction. The artifact records
`composedTerminalEmissionCertified=false`,
`composedTerminalTransferCertified=false`, and
`composedTerminalGrowthRules=0`. A future terminal-aware executor must emit the
literal gap cluster, verify the composed attachment on a frozen held-out
window, and preserve collision/species certificates before any such class can
enter candidate supply.

Measured browser results are deliberately red: Cu–Zr has six directed
observations in six pose classes; Cd–Yb has four in four; no class is witnessed
at two independent terminals. The ideal-IQC and BC8 windows have zero complete
terminal bridges. Direct Cd–Yb/BC8 ports and the molecular ice anchor path are
unchanged.

### Molecular-anchor verdict boundary (Build 332)

Molecular covers now expose `molecular-anchor` as their atlas verdict. Their
headline reports audited molecule, connection-polyhedron, and gap/void cover
types; the zero generic-port count is retained only as a labeled ablation. This
prevents a correct H₂O molecule-plus-gap decomposition from being presented as
a failed irregular-support grammar, without counting the specialized anchor
certificate as generic GCTS port coverage.

### Cover-edge evidence decomposition (Build 331)

A zero generic-port count is no longer a single opaque failure state. The
browser audits the frozen cover occurrence graph and separately counts direct
promotable-support overlaps, support-to-terminal contacts, terminal-to-terminal
contacts, completed support→terminal→support occurrence bridges, unique bridge
type-pair topologies, recurring bridge topologies, and exact directed replay
edges. Direct rule classes are also split into one-shot and recurring relative
poses. Each quantity has an explicit denominator and can be inspected without
opening the growth target.

Only recurring direct proper-pose rules remain eligible as generic growth
supply. A repeated terminal-mediated topology is diagnostic evidence, not a
port: promotion would additionally require a train-witnessed composed proper
pose, an explicit terminal-emission certificate, collision safety, and frozen
transfer. Exact replay edges retain occurrence identity and remain target-aware.
This boundary prevents the UI from manufacturing a grammar merely to turn a red
sample green.

The current browser fixtures expose three genuinely different states. Cd–Yb
and BC8 contain direct recurrent support connections. The Cu₆₄Zr₃₆ glass has no
direct support edge but does have three terminal-mediated support pairs; it is a
representation frontier and an appropriate amorphous compression control. The
ideal IQC patch has eight support-to-terminal contacts but no completed bridge,
so its small browser window is connectivity-evidence-starved even though
backend held-out IQC continuation experiments exist. Ice is explicitly routed
to the molecular-anchor certificate: one H₂O molecule class, connection
polyhedra, and symmetry-resolved O₆ void/gap classes remain visible, while its
generic cluster-port numerator stays separate.

### Cluster-resolved continuation coverage (Build 330)

The marking stage now audits the directed frozen continuation graph at the same
type resolution as its separate 3D cluster scenes. For every cover type it
reports fitted occurrence support, incoming/outgoing rule counts and witness
mass, outgoing target/source type sets, held-out rule support, marking lobes and
unsupported sectors, channel count, proper-pose/gauge support, and exact
reconstruction degree. The scientist can select any atlas cell to open the same
cluster in the full coefficient/pose/port inspector.

Two denominators remain explicit. Type coverage is the fraction of nonterminal
cluster types with at least one outgoing continuation rule; occurrence coverage
weights those types by how often they appear in the supplied cover. Literal
residual terminals are complete-cover evidence but are never promoted. Exact
known-window edges remain target-aware replay evidence and never increase either
target-free continuation measure. A specialized molecular-anchor executor, when
available, is reported outside this generic port graph rather than conflated
with it.

### Growth-launch readiness and exact seed replay (Build 329)

Stage 4 now exposes the complete target-free launch chain as four measured
quantities: fitted occurrence support, initialized seed-type support, outgoing
frozen connection rules, and exact live frontier actions after duplicate-pose,
species, exclusion-distance, and public-boundary checks. A signed boundary
margin is reported in Å. The resulting finite state machine names the first
failed layer and links back to Cluster identification or GCTS learning instead
of collapsing every zero frontier into “change the specimen.”

The campaign planner has also been hardened. Its 864 inexpensive previews are
deduplicated by centered colored seed digest while preserving the current UI
state. Candidates with boundary failure, used/equivalent digest, or no outgoing
rule are counted and rejected. Up to 24 unique survivors are then initialized by
the real search path; only exact digest replay plus a nonempty live frontier may
register a new Baseline. If none passes, the previous experiment is rebuilt and
the failure categories remain visible. This bounded replay can establish finite
executable continuation, never physical growth arrest, kinetics, or a material
potential.

### Executable-nucleus campaign planning (Build 328)

The campaign audit now drives a target-free seed planner rather than merely
asking the scientist to change the seed manually. From the fitted occurrence
library it enumerates declared nucleation modes, ranks, requested nucleus counts,
and six finite proper-pose choices. Each preview uses only fitted support,
frozen outgoing-rule counts, the public growth boundary, and a centered colored
coordinate digest. It never reads the known-window reconstruction target or
scores a candidate against future atoms.

A preview becomes a runnable Baseline only after the actual stage initializer
reproduces its seed digest and exposes a nonempty frozen frontier. Used digests,
boundary failures, empty-frontier seeds, and preview/replay mismatches are
rejected with a visible reason. On success, the same selected evidence and the
same declared omission are restored under a fresh pair-session ID. On failure,
the planner leaves the current experiment intact and explicitly asks for another
specimen instead of manufacturing a replicate.

The proper-pose choices are controls on the same fitted geometry and public
boundary. They do not turn one observation into independent material samples,
and they are not evidence for rotational generalization unless an executable
frontier actually survives. Campaign readiness remains a descriptive
same-specimen algorithmic result, separate from population inference, kinetics,
or a causal material mechanism.

### Target-free fitted nuclei for registered replicates (Build 327)

The browser now makes the seed/target boundary explicit. In the new local-frontier
mode, one or more fitted occurrences are copied into the live state as the
declared nucleus. Their exact positions and proper poses are legitimate supplied
initial data; all other observed positions are excluded from candidate geometry,
ranking, and acceptance. Frontier actions come only from the frozen overlap/port
grammar plus species-aware live collision and boundary checks. The separate
reconstruction mode intentionally retains known-window replay and remains
target-aware until certified.

Nucleation-site modes are now usable as deterministic replicate-seed controls:
interior, surface, residual-gap, interface, and dispersed selections retain a
seed-selection label and coordinate digest in the execution receipt. Pair-session
identity still prevents cross-pairing, and the campaign still requires three
distinct seed digests. This establishes reproducible algorithmic replicates on a
single supplied configuration; it does not establish independent draws from a
materials population, kinetics, nucleation rates, or causal physical response.

### Pair-session identity and replicate readiness (Build 326)

The paired-arm protocol now freezes a unique session identifier before either
arm executes, carries it through the reset to the omission arm, and stores it in
both preflight manifests and notebook summaries. The outcome gate rejects a
missing or unequal session identifier before comparing trajectories. This
prevents repeated experiments with the same design from producing spurious
baseline×Arm-B cross-products.

A campaign audit groups receipts by session, admits only groups with exactly two
entries whose authoritative pair comparison passes, and then restricts the
replicate set to one material scenario and frozen intervention design. It reports
distinct seed count and coordinate-free domain response consistency. The initial
readiness threshold—three registered pairs on three seed digests—means only
“replicated descriptive algorithmic response.” No significance test, material
population inference, physical ensemble, or causal mechanism is implied, and
ambiguous, legacy, or failed sessions never contribute.

### Structural-response fingerprint for matched arms (Build 325)

Every comparable physics-proxy pair now produces a pure response fingerprint in
addition to its eight raw metric deltas. The fingerprint partitions the receipt
metrics into material extent (sites, clusters, lineage depth), search work
(frontier, accepted, and rejected actions), and structural order (powder
structure-factor prominence and local orientational order). Each domain retains
resolved-count coverage, a signed mean, RMS magnitude, and the dominant source
metric and provenance.

Each metric is normalized independently as `(B−A)/(|B|+|A|)` and bounded to
`[-1,1]`; zero/zero maps to zero. The display never sums domains, assigns a
favorable direction, or replaces unit-bearing values. The fingerprint is
available only after the complete paired-arm audit passes, contains no
coordinates or target information, and explicitly distinguishes an observed
algorithmic consequence from forces, energy, kinetics, physical time, and a
causal material mechanism.

### Receipt-verified paired physics workflow (Build 324)

The matched-proxy handoff now continues through an explicit four-state protocol:
register the reversible layer, execute and save Baseline, reset the supplied
structural state and execute Arm B, then open the comparison only after the
notebook gate verifies the pair. Saved runs remain separate receipt-bearing
experiments; resetting Arm B does not erase the baseline or reuse its grown
state.

The progress model is pure and target-free. It groups saved runs by the frozen
intervention plan but delegates scientific comparability to the authoritative
outcome audit, which checks the same input and seed, public boundary, exactly one
changed reversible control, identical candidate rule, target-free execution,
and a non-truncated common update horizon. It neither enumerates candidates nor
runs search, and the resulting delta remains a geometric-proxy omission response
rather than a physical force, free-energy, rate, or causal-mechanism claim.

### Evidence-to-geometry investigation handoff (Build 323)

Every omitted dynamical quantity now carries a serializable handoff in addition to its
readiness diagnosis. The handoff partitions the relevant manifest IDs into direct evidence,
geometric proxies, and unavailable inputs, then determines whether a reversible proxy is
eligible for a matched baseline/neutral comparison. The complete evidence-request mode
selects all relevant records so the physics protocol fails visibly on missing inputs. The
proxy-ablation mode retains the existing protocol and registers one explicit-neutral control
binding without applying either arm.

The preflight schema records the handoff mode, selected and requested record IDs, proposed
ablated record, and the invariants `inferenceResolved=false`, `controlValueChanged=false`,
`candidateSetInspected=false`, and `targetUsed=false`. The structural-leap and notebook
receipts retain the same record. This closes the workflow gap between “what evidence is
missing?” and “what falsifiable geometry experiment can be run now?” without relabeling the
experiment as forces, thermodynamics, kinetics, or physical time.

### Evidence acquisition for omitted dynamics (Build 322)

The six quantities deliberately left unknown by structural leap-frogging now have an
executable evidence-readiness plan. Each quantity declares its relevant physics-manifest
records, distinguishes supplied/observed evidence from soft geometric proxies, lists missing
records, states what new evidence is required, and restricts its earliest valid use. A
force-labelled state can therefore be visible as partial physical evidence while force-field
inference stays false; path clearance can be visible as a proxy while barrier and rate remain
unknown.

The plan is generated from the target-free pre-growth manifest before candidate inspection,
then frozen into each structural-leap receipt. UI routing opens the existing evidence/control
location without changing it. No readiness state authorizes admission or ranking, and all six
inferences remain explicitly unresolved until a separate model and its validation evidence
are supplied.

### Structural-leap consequence vector (Build 321)

Each retained search update now carries a pure, serializable endpoint-consequence receipt.
The full material rows remain authoritative and unit-bearing. For navigation, bounded fields
are normalized by their declared dimensionless span and adaptive fields by the larger
absolute endpoint magnitude. Five axes report their signed mean and RMS magnitude separately;
they are never summed, and no favorable direction is assigned. Clicking an axis returns to
the underlying before/after rows.

The same view lists the physical information absent from a geometric leap: intermediate
trajectory, duration/rate, transition barrier, free energy, path probability, forces,
stress, and heat flow. This makes “leap-frogging dynamics” falsifiable as an endpoint claim:
the portal can report what structural observables changed, but it cannot infer the omitted
dynamical bridge without new evidence and a separately validated physical model.

### Action-level physics provenance (Build 320)

Every retained growth-action fingerprint now contains a complete join between
the frozen physics manifest, signed score terms, and active admission gates.
The runtime rejects missing manifest IDs, rank terms whose current layer has
no rank hook, and hard gates whose current layer has no admission hook. The
result distinguishes action-bound admission, rank, labeled replay, and branch
ordering from merely available coordinate/seed hooks, evidence-only records,
and open physical gaps.

The browser exposes the same join as a filterable matrix in the selected-action
microscope. Each row routes back to the original finite evidence, geometric
encoding, current execution object, control route, and claim boundary. This is
an audit of the leap-frogging approximation: it makes missing physics visible
instead of silently assigning it a geometric score. It is not a causal
attribution, potential-energy decomposition, growth probability, or clock.

Build 320 also consumes the first cached four-copy A₂ census. Candidate 00120
exhausts 65,110 proper/reflected scale-two parent types without a substitution.
Added to the sixteen completed three-copy screens, the portal now exposes
seventeen bounded obstructions and 90,760 scale-specific parent tests. The
remaining seven four-copy screens and every global classification stay open.

### Executable score-lineage completeness (Build 319)

The live executor now compiles a candidate-level completeness certificate over
the exact signed score ledger. Every nonzero rank term except the explicitly
separated known-window replay and seeded exploration terms must map to one
manifest layer that currently declares a ranking execution object. Unmapped or
misclassified terms abort candidate construction. The certificate and its
term rows enter the retained-action fingerprint and digest.

Per-control effect overrides resolve channels with more than one role: local
geometry can reject and rank, chemistry can enforce finite inventory and rank,
scalar-spin coloring can reject overlaps only when enabled, and a frozen
external calibration can rank only after selected promotion. This is a
software/evidence-lineage invariant, not validation of the surrogate as an
energy, force, entropy, rate, or physical clock.

The same release incorporates the next exact A₂ bounded screen. The eight
focused size-seven supports each exhaust their proper/reflected three-copy
parent alphabet at scale four as well as scale three. Each scale accounts for
12,825 parent types, so the Evidence Atlas now reports 25,650 scale-specific
parent tests and sixteen bounded grammar obstructions. These remain finite
obstructions only; global tiling and aperiodicity classification are open.

### Physics execution-lineage repair (Build 318)

The portal's coordinate-free preflight previously understated four real
execution paths. With scalar-spin coloring active, incompatible supplied
labels can reject an exact overlap. The collective accepted-history graph
field, continuation multiplicity, and contact-direction constraint tensor all
contribute signed terms to the unchanged frozen candidate ranking. They are
now classified respectively as hard admission and soft ranking, not as
evidence-only diagnostics.

The lineage record names the exact execution object affected and the protocol
composer can freeze a neutral `none` arm for each of the three rank terms.
Candidate identity must remain matched for those ablations. This closes a
portal audit gap; it does not upgrade any surrogate into energy, entropy,
elasticity, magnetism, kinetics, or physical time.

The same deployed data revision completes the bounded three-copy scale-three
A₂ screen for all eight focused candidates. Together they exhaust 12,825
proper/reflected parent types without a substitution. Every obstruction
remains strictly weaker than global non-tiling or aperiodicity.

### Two-family A₂ exact-geometry explorer (Build 317)

The portal now reads both generated A₂ catalogs as distinct exact-geometry
stress tests. The established size-eight layered census retains four
exact-through-seven candidates from 4,940 inputs. The new size-seven
consecutive-layer catalog retains eight focused candidates from a 1,112-shape
census; every displayed candidate has a complete exact radius-two patch of
190–252 copies.

One interactive switch changes the support rendering, finite-screen metrics,
and clause semantics together. For the size-seven family it reports 759
radius-three failure clauses and 731 first-corona clauses, plus the declared
solver/round stop for each candidate. These clauses are sound bounded local
obstructions. They do not exhaust radius three and do not certify non-tiling,
aperiodicity, a substitution law, or a solid-growth mechanism.

The same view reports the completed candidate-00139 three-copy scale-three
cluster screen: all 1,268 reflected parent types are exhausted and no
substitution exists. This is a proved finite grammar obstruction. Other
metatile sizes, scales, decorations, global tilings, and aperiodicity remain
outside that certificate.

### Retained-leap settling robustness (Build 290)

For the currently selected material field, the portal now assembles the same
off/gentle/balanced/strong audits from every retained structural leap into an
allowance × leap map. Each cell preserves hard-gate rollback, certification,
sign, and a within-field magnitude. The history classifier reports whether
compatible virtual projections are invariant, intermittently sensitive,
consistently signed, direction-reversing, or categorical across the retained
window. Selecting a cell synchronizes the rest of the structural microscope to
that discrete search update.

The history audit is coordinate-free, target-free, saved in the receipt, and
excluded from admission and ranking. Its scale never crosses fields or units.
Sequential GCTS states are correlated outputs of one execution, so columns are
not treated as replicate materials, physical time, a relaxation trajectory,
kinetics, energy, or causal evidence.

### Field-wise settling robustness matrix (Build 289)

The same-state settling audit now presents every material fingerprint field as
a row across the off/gentle/balanced/strong allowance ladder. Numeric rows retain
their native units and are normalized only by that row's largest absolute
delta; category rows report class changes without a numerical distance. Each
row receives a transparent response classification, while the matrix separately
reports whether compatible projections form an allowance threshold or whether
the hard gates reject all or a non-nested subset of projected arms.

This is a visual robustness summary over frozen, uncommitted counterfactuals.
Rejected arms are marked as rollbacks, not retained states, and the matrix has no
route into candidate admission, marking scores, tree-search order, or subsequent
growth. It therefore makes no mixed-unit response norm, energy landscape,
kinetic pathway, probability, or physical-time claim.

### Material outcomes across settling arms (Build 288)

Each off/gentle/balanced/strong arm now receives a coordinate-free material
fingerprint evaluated on its retained virtual geometry: coordination exposure,
six-neighbor packing, local orientational order, exact-pair centrosymmetry,
unit-weight finite-window S(q) prominence, covariance size/extent/anisotropy,
dimension, and phenotype. The comparison reports named changed fields and
signed within-field deltas only; it never combines unlike units into a scalar.
Rejected arms inherit the as-placed baseline, while compatible arms are scored
without committing their coordinates.

Atom count and species inventory are asserted invariant, and the complete audit
remains downstream of search with no target, potential, force, energy, kinetics,
or clock. The live structural-statistics cache now includes the coordinate
revision as well as count/replay identity, closing a prior stale-cache path
between the as-placed and post-projection checkpoints.

### Same-as-placed settling sensitivity (Build 287)

An eligible executed leap now freezes four bounded projection arms—off,
gentle, balanced, and strong—before the selected projection can mutate the
configuration. The arms share the exact as-placed sites, the same fixed context
neighborhood sized for the strongest declared cap, identical learned
contact/angle envelopes, and identical hard exclusion and public-boundary tests.
Only cap and iteration allowance differ. The receipt retains every arm, gate,
strain reduction, displacement, and rollback reason, plus an exact selected-
preview versus committed-result parity flag.

The sensitivity ladder is counterfactual and downstream of the frozen GCTS
antichain: it does not rerun candidate enumeration, ranking, batch scheduling,
or continuation, and only the selected arm may commit. It therefore measures
dependence on the bounded geometric accommodation allowance without calling the
arms temperatures, time steps, force fields, energies, transition paths, or
physical probabilities.

### Attachment / settling decomposition (Build 286)

The executed structural-leap receipt now freezes a full coordinate-free
`asPlaced` checkpoint after the order-independent whole-cluster antichain is
committed and before the optional local constraint projection. The interactive
material-consequence panel resolves three distinct comparisons: before → final,
before → as placed, and as placed → final. The same exact observable definitions
are used for every comparison, so changes in coordination, packing, void
geometry, morphology, composition, local order, centrosymmetry, and finite-window
scattering can be attributed to the discrete attachment or to the bounded
correction without mixing their units into one score.

This decomposition is descriptive, downstream, and target-free. Projection is
restricted to newly emitted sites under an explicit displacement cap and is
accepted only after monotone contact-angle improvement plus every hard geometry
and public-boundary gate. The method does not integrate forces or time, evaluate
a physical potential or free energy, infer a transition mechanism, or turn the
discrete leap order into kinetics.

### Material-consequence decisiveness pathway (Build 285)

The frozen-frontier hypothesis audit now propagates each active score channel
through seven independently checked stages: differential score, winning pose,
commuting order, whole antichain, emitted colored sites, emitted chemistry, and
the compact virtual material fingerprint introduced in Build 284. The final
stage reports exactly which fingerprint fields change rather than combining Å,
counts, and dimensionless observables into a spurious scalar.

Material consequence is also stored per channel in the bounded retained-
frontier history and exposed as an outcome in the state-conditioned
decisiveness lens. This connects pre-decision material passports to
material-level model sensitivity across discrete structural updates. The
counterfactual remains uncommitted and target-free, and the audit explicitly
does not treat the columns as a causal chain or the retained sequence as
independent specimens, a free-energy path, kinetics, probability, rate, or
physical time.

### Channel omission to material consequence (Build 284)

The exact frozen-frontier shadow leap now carries a coordinate-free material
fingerprint for both the baseline antichain and every one-channel-omitted
antichain. It recomputes whole-configuration covariance morphology and
composition from the current explicit atoms plus the exact colored emitted-site
union. It also reports a fresh-site-count-weighted precommit coordination
completion proxy from the already frozen candidate evaluations.

The interactive microscope displays baseline → omitted atom count, covariance
phenotype, radius of gyration, maximum extent, shape anisotropy, composition
drift, and interface completion alongside the existing exact action/site/
chemistry comparison. Receipt records include rounded fingerprints, signed
omitted-minus-baseline deltas, flags, and the audit digest without coordinates.
The candidate set, hard gates, batch feasibility, and public boundary are
unchanged; neither counterfactual is committed or enumerates a downstream frontier.
No relaxation, local-order, diffraction, energy, causal effect, probability,
kinetics, rate, or physical time is inferred.

### Executed geometric growth-regime map (Build 283)

The portal now joins each accepted retained GCTS leap to a compact
before-decision material-state passport and its certified post-leap structural
response. The scientist can interactively select a geometry-only input axis
(coordination exposure, underpacking, local order, geometric S(q) prominence,
shape anisotropy, or shared-interface fraction) and an executed response axis
(the corresponding after-minus-before deltas, effective nucleus count,
interface change, or explicit emitted atoms).

Only accepted leaps with positive explicit emission enter the map. Target-used,
fixed, rejected, and unresolved rows fail closed. The receipt stores the finite
records, axes, support count, flags, and audit digest without coordinates. The
map is downstream of execution and cannot alter candidate enumeration,
admission, or ranking. Its connecting line is retained GCTS execution order,
not elapsed time; the display makes no phase-diagram, free-energy, kinetic,
causal, probability, or rate claim.

### Run-blocked material-state replication (Build 282)

The coordinate-free notebook now treats each unique saved receipt as one
replication unit for the state-conditioned channel audit. It aligns only runs
that froze the same geometry channel and structural outcome, then exposes the
eight material observables interactively. Each run contributes at most one
resolved normalized difference between its changed and stable retained
frontiers; the contributing frontier samples remain inside that run and are not
pooled into an inflated sample size.

The deterministic contract deduplicates receipt SHA-256 identities, excludes
target-tainted audits, and requires the within-run three-per-group support gate
before a run is eligible. Three eligible runs with one nonzero sign are needed
for directional replication. One shared input identity is reported only as
repeat-run consistency, whereas at least two input identities may be reported
as cross-input consistency. Mixed signs remain explicitly heterogeneous. The
card reports run/input/scenario counts, sign agreement, the median and range of
normalized within-run contrasts, and a compact audit digest. It computes no
p-value and asserts no specimen independence, causal response, physical energy,
kinetics, dynamics, or physical time.

### State-conditioned channel decisiveness (Build 281)

The portal now computes a bounded descriptive association between each frozen
material-state observable and each independent channel-omission outcome. For a
selected channel and outcome—score, leader, order, antichain, emitted atoms, or
chemistry—it partitions only retained capture-time frontiers into changed and
stable groups. Each row reports group counts and means, their signed difference,
the finite-window minimum/maximum, and a difference normalized by that row's
observed range.

Resolution requires at least three finite observations in both groups. Missing
support is displayed rather than imputed; unavailable channel/state combinations
are excluded explicitly. The receipt preserves every contributing frontier
index and candidate-set digest as well as the audit digest and claim boundary.
Because successive growth fronts share history, the portal does not assume
statistical independence, compute a p-value, or infer a causal effect. The lens
is diagnostic only and cannot alter candidate geometry, admission, ranking,
execution, energy, probability, kinetics, dynamics, or physical time.

### Linked frontier material-state passports (Build 280)

Each frozen policy frontier now carries a compact pre-decision structural
passport next to its channel-decisiveness column. The passport exports atoms,
clusters, candidate count, covariance phenotype, dimension, radius and
anisotropy, nucleus/interface summaries, plus eight independent observables:
coordination deficit, underpacked fraction, composition total variation, local
q₆ / |ψ₆|, centrosymmetry amplitude, unit-weight S(q) peak prominence,
normalized supplied-charge dipole magnitude, and sampled bond-valence RMS
mismatch.

The browser renders those observables as a row-normalized material-state ribbon
under the omission history. A state cell and its decisiveness cell navigate to
the same immutable frontier and preview, making it possible to ask whether a
channel is structurally decisive only in an exposed, disordered, charge-shaped,
or valence-mismatched local regime. The raw value, units, candidate digest, and
passport digest remain available; row color is never compared across unlike
observables and never enters search. Passports reuse the structural state frozen
before candidate evaluation, embed no coordinates, and infer no energy,
probability, reaction coordinate, kinetics, dynamics, or physical time.

### Channel decisiveness through retained frontiers (Build 279)

The selected hypothesis channel can now be followed through the bounded archive
of frozen GCTS frontiers. The interactive heatmap has one column per captured
structural update and six independent rows: differential score, winner,
commuting order, permutation-invariant antichain membership, emitted colored
sites, and species inventory. Clicking an available cell selects that immutable
frontier and restores its exact omission preview and shadow-batch comparison.

Historical cells consume the audit stored at capture, including candidate-set
and decisiveness digests; they are never recomputed from current weight controls.
The notebook receipt exports channel ID, stage counts, every per-frontier stage
value, target-use flags, and the statement that coordinates, execution, causal
hierarchy, and physical time are absent. The display therefore measures whether
a geometry-encoded hypothesis remains structurally decisive as the interface
changes, without presenting the archive as a trajectory in physical time.

### Physics-hypothesis decisiveness matrix (Build 278)

The portal now aligns the score-ledger, leave-one-channel winner audit, and
shadow-antichain audit by channel ID on one frozen candidate-set digest. Six
columns remain logically independent: nonconstant candidate contribution,
baseline-leader displacement under omission, commuting order change, sorted
antichain-set change, species-labelled emitted-site change, and emitted
species-count change. No later column is inferred from an earlier one.

For each active channel the receipt stores the minimum, maximum, and range of
its signed contribution; the baseline winner's omitted rank; action and site
Jaccard overlaps; chemistry L1 distance; the six Boolean outcomes; and a
coordinate-free audit digest. The interactive matrix uses mint cells for a
materially changed comparison and amber specifically for order-only changes.
Selecting a row synchronizes its ordinary omission winner and full shadow-leap
overlay.

The default NaCl frontier has four active geometry channels. Three vary over
the candidate set, none displaces the leader, those three reorder the commuting
placements, and zero changes the sorted 146-action antichain, its 203 emitted
sites, or the `Cl105 + Na98` emitted inventory. This is an explicit null result:
the active geometry weights are locally rank-sensitive but structurally
non-decisive at this leap. Baseline weights are frozen at capture, candidates
and hard gates remain unchanged, and no omitted arm executes. The matrix is not
a causal hierarchy, energy decomposition, probability, kinetics, dynamics, or
physical time.

### Whole-batch leave-one-channel-out shadow leap (Build 277)

Action rank sensitivity is now propagated through one complete structural
update without mutating the material. Starting from the immutable evaluated
frontier, each active soft geometry term is set to zero for every
hard-admitted candidate. The browser reranks with the production lexical tie
rule and greedily constructs a shadow commuting antichain using the same
pairwise colored-site compatibility, finite feedstock, coordination-capacity,
angular-envelope, and retained-novel-site predicates as the production
selector. Because a commuting antichain is permutation-invariant, its
coordinate-free identity digest is computed from the sorted action set; a
separate order digest records score-order changes without calling them a
structural response.

The live and shadow paths share `candidateFitsCommutingBatch`; after production
selection, the baseline shadow candidate digest must equal the accepted live
batch digest or execution throws before commit. This is stronger than a
winner-only comparison. On the default NaCl continuation, all four active
channel omissions retain the top exact pose and the same 146-action antichain.
Three alter only its score order; each emits the same 203 species-labelled
sites. The UI therefore reports zero structural-leap changes, three order-only
changes, and 100% emitted-site overlap rather than conflating a permutation of
commuting placements with a different material state.

For each channel the audit records action and emitted-site Jaccard overlap,
added/removed actions and sites, species-count L1 change, centroid shift,
radius-of-gyration change, candidate/emission digests, and baseline/live
parity. A tilted display overlays baseline-only, shared, and omission-only
sites, while exported receipts omit coordinates. Candidate enumeration,
geometry, hard admission, and boundary remain fixed; omitted batches are not
committed and do not spawn a downstream frontier. Consequently this is a
one-leap sensitivity of the declared geometric policy and scheduler, not a
physical counterfactual, causal mechanism, energy, probability, rate,
dynamics, or time.

### Action-level leave-one-channel rank sensitivity (Build 276)

The winner-only leave-one-physics-channel-out workbench has been generalized to
every retained accepted or rejected action. After the full evaluated frontier
is frozen and baseline ranks are assigned, each active physical-surrogate term
is removed from every candidate score. The remaining terms are summed exactly,
the same candidate identities are reranked with the stable candidate-key tie
break, and each action records `baselineRank`, `omittedRank`, and
`rankBenefit = omittedRank - baselineRank`.

This distinction prevents contribution magnitude from being mistaken for
decision influence. A large nearly constant term can have zero rank benefit; a
smaller varying term can move an action many places. The browser switches the
same signed bar field between contribution and rank-benefit units, reports the
strongest leave-one-channel displacement, and supports A/B comparison without
changing the matched pair. The hard-gate strip is always separate and unchanged.

The receipt stores the active term count, rank-changing count, maximum absolute
benefit, per-channel omitted score and leader digest, frozen candidate-set
digest, exact omission rule, and a sensitivity digest. It states that candidate
geometry, candidate set, and hard admission are unchanged; omitted arms are not
executed; coordinates are absent; and no causal physical effect or energy
difference is inferred. The underlying baseline may still be reference-guided
during labeled replay, which is disclosed independently.

### Branch-resolved physics → geometry attribution (Build 275)

The retained growth-event record now freezes the same exact score decomposition
used by `scoreFrontierCandidate`: grammar priority, labeled replay gain, every
declared geometric physics surrogate, and seeded exploration. Each term records
its raw value, active (possibly signed) weight, signed contribution, execution
role, and scientific claim boundary. The sum is asserted against the actual
selection score at `1e-9`; the final frontier rank, candidate count, distance
behind the leader, and a coordinate-free ledger digest are added only after the
complete immutable candidate set is sorted.

The additive ledger is not allowed to impersonate admission. Ten independently
reported predicates retain their observed value, requirement, and pass/fail
state: species/hard core, scalar-spin color, public boundary, shared support,
novel emission, known-window consistency, coordination, angles, feedstock, and
the selected GCTS marking. A rejected action can therefore be inspected as a
specific geometric failure even when some soft ordering channels are favorable.

For one selected action, the microscope displays the largest active signed
contributions around a zero axis and the complete hard-gate strip. With an A/B
pair pinned, it displays exact `A → B` contributions and sorts on their delta,
while highlighting gate transitions separately. The renderer has no candidate
evaluation, atom mutation, materialization, or search call. Receipt fields state
that the fingerprint contains no coordinates and is not itself used by search;
the underlying nonzero soft terms were already used for branch ranking. These
dimensionless geometric scores are hypotheses and ordering surrogates, not
energies, probabilities, forces, barriers, rates, dynamics, or physical time.

### Matched local-action comparison (Build 274)

The action microscope can pin one retained decision as A and compare it with a
manually selected B or the deterministically nearest opposite fate. The match
descriptor is built after decision freeze from bounded local support counts,
child/context chemistry fractions, supplied-configuration halo fractions,
proper-rotation-invariant child pair-distance and context-radius quantiles,
contact/overlap residuals, GCTS margin, and tree depth. It explicitly excludes
the outcome, gate vector, reason string, action identity, and absolute pose.
Outcome enters only as the eligibility predicate for “nearest opposite.”

The panel displays both fates and gate explanations only after selection, plus
support, chemistry, halo, clearance, residual, marking, retained-state, and the
three largest descriptor differences. A dashed gold ring retains A on the
spatial map while the ordinary white ring follows B. The selector and renderer
contain no evaluation, materialization, atom replacement, placed-cluster
replacement, or search call. Receipts explicitly state that neither the pair
nor interactive selection is serialized or used for search.

On the default NaCl action ledger, accepted A64 and redundant-cover B91 are the
nearest opposite pair at distance 0.0428 over 29 invariant components. Both
children are `Cl1 · Na6` seven-site supports; the comparison separates `6/1`
from `7/0` shared/novel sites and identifies contact clearance, depth, and
shared-support fraction as the largest descriptor differences. The explicit
material remains at 419 sites. This within-ledger pairing is descriptive and
correlated—not a physical counterfactual, causal estimate, barrier, energy,
probability, rate, or clock.

### Candidate-centred attachment geometry (Build 273)

The selected-action microscope now reconstructs a display-only local section
from the already evaluated candidate. Exact colored child sites are classified
as shared support, novel emission, or blocked proposal; occupied atoms within
the frozen neighborhood are sampled deterministically to a 48-site display
cap. Every coordinate is translated to the candidate centre and converted to
Å. Each tilted XY/XZ/YZ view adds a small third-axis depth cue while retaining
the action's current proper pose; a nearest-contact graph exposes the finite
child support rather than drawing a
radial star from one arbitrary atom.

This geometry is intentionally not a new search object. It is constructed only
inside the post-decision record path, after the candidate evaluation freezes;
its contract declares no use in enumeration, admission, or ranking. The
coordinate-free receipt destructures both `position` and `localGeometry` from
every retained event, records that the display coordinates were omitted, and
separately discloses whether a known-window display inherited target-aware
candidate provenance.

For the default target-free NaCl leap, the selected accepted event renders a
seven-site child, six coincident shared supports, one novel site, and 23 nearby
occupied context atoms. Switching projection leaves the explicit live count at
419 and changes neither the action nor its certificate. The lines are finite
nearest-contact display edges, not inferred chemical bonds, energies, forces,
transition pathways, or physical time.

### Branch-level growth decision microscope (Build 272)

The post-decision spatial event audit now retains an interactive selection over
its bounded coordinate-bearing display records while continuing to serialize
only coordinate-free evidence. Pointer selection on the XY/XZ/YZ projection,
previous/next controls, and Home/End/arrow keyboard navigation all resolve to
one immutable action record. The microscope separates action fate, local
phenotype, support change, input-derived role halo, metric conditioning,
contact/overlap residuals, GCTS section evidence, and the bounded pose audit.

The decisive gate is reconstructed from already frozen gate signals: public
boundary, colored exclusion, local topology, GCTS connection, redundant cover,
or complete hard-geometry admission. This classification occurs after the
candidate and decision freeze and never enters enumeration, scoring, admission,
or materialization. Selecting an event can synchronize the Build 271 retained-
leap evidence view, but the selector contains no candidate evaluation,
materialization, atom replacement, placed-cluster replacement, or search call.

The NaCl regression keeps the scientific execution unchanged at 216 → 419
explicit sites, 146 accepted actions, and 609 rejections. The bounded event map
stores 96/755 decisions. Its default accepted example exposes 6 shared + 1 new
site, 0.564 Å contact clearance, 0.000 Å shared-site residual, a 0.269 section
margin versus 0.020 heldout loss, and 12/12 deterministic pose-perturbation
agreement. Navigation leaves the live atom count at 419. These values are
decision diagnostics, not a physical energy, confidence, mechanism, rate, or
clock.

### Certified structural-history microscope (Build 271)

The Stage 1/3 process timeline now has a distinct Stage 4 contract. Its range
is the observed nucleus plus retained structural-leap certificates; selection
updates all coordinate-free consequence and physics-evidence panels but never
replaces the live atom array, placed clusters, frontier, or search counters.
The lower label is the observed nucleus, the upper label reports retained
states, and recent-history controls include an explicit seed button.

Each selected state summarizes exact explicit-site and placed-cluster changes,
accepted/rejected whole-cluster work, the pre-leap frozen frontier, and one
representative material fingerprint. The full existing certificate remains
available below it: composition, finite packing and void graphs, local order,
centrosymmetry, geometric S(q), supplied-charge shape, bond valence, morphology,
and every physics→geometry claim boundary. The receipt marks this as frozen
evidence replay with `liveGeometryMutated=false`, no coordinates, no target,
and no physical time. Browser regression proves the separation: selecting the
216-site NaCl nucleus leaves the live 419-site state unchanged.

### Responsive frontier microscope (Build 270)

The browser executor now exposes the finite work hidden inside one structural
leap. It first copies the frozen frontier, evaluates every candidate with the
unchanged hard geometry and soft marking/physics terms, selects the maximal
pairwise-compatible antichain, and rechecks each whole-cluster commit. All
three phases yield through animation frames after a bounded browser-work slice.
Generation tokens cancel stale work if the specimen is rebuilt; stage/reset
controls are locked while a batch is live. A timed-run pause finishes the
current immutable antichain atomically and then stops before another frontier.

The progress surface and receipt report candidate total, evaluated count,
event-loop yields, maximum scheduling-slice duration, and accepted/rejected
batch counts. Candidate and ranking target-use flags remain explicit. On the
default NaCl observed-window nucleus, the responsive path reproduces the exact
Build 269 scientific result: 1,628 frozen proposals produce 146 commuting
placements, 609 invariant rejects, 203 new sites, 419 total sites, and a 4,410-
action successor frontier. The live page remained inspectable while evaluation
and antichain selection were in progress. Scheduling duration is deliberately
not used as materials evidence, an MD comparison, a rate, or physical time.

### Target-free observed-window growth (Build 269)

Stage 4 now separates two scientifically different initial conditions. The
default `observed-window` protocol treats the supplied positions as the public
nucleus: all colored sites are installed, every frozen cover occurrence keeps
its observed proper pose, and residual sites are explicit. Candidate geometry
is generated only afterward by composing learned finite ports. The optional
`reconstruct` protocol starts from local occurrences and retains its known-
window reference-guided ranking label; it remains useful for replay audits but
is rejected by matched causal-response gates.

Receipts freeze the seed protocol, centered colored-site digest, fitted cover
count, residual count, initial frontier count, and explicit `targetUsed=false`
and `futureSitesUsed=false` declarations. The physics-arm comparator requires
equal, non-target-derived seed digests as well as its existing input, boundary,
history, intervention, and candidate-identity checks. Browser verification on
NaCl starts from 216 sites / 52 cover placements and a 1,628-action frozen
frontier. One commuting structural leap accepts 146 placements, prunes 609,
and leaves 419 explicit sites / 198 placements. A soft surface-completion
omission shares the exact first-frontier digest and gives zero response on all
reported observables. That null is preserved. The experiment remains a single
configuration, deterministic geometric omission with no force trajectory,
energy, kinetic clock, or population-level physical-causality claim.

### Matched physics-arm outcome ledger (Build 268)

The coordinate-free experiment notebook now consumes the frozen preflight
registration instead of inferring a counterfactual from two arbitrary saved
states. Manifest schema 4 adds the value of every distinct reversible physics
control before candidate enumeration. `comparePhysicsProtocolOutcomes` requires
one baseline and one arm B from the same omission plan, the same input SHA and
public boundary, verified arm values, exactly one changed control, active-layer
sets matching the registration, complete histories, and no target use. The
bounded notebook receipt now embeds this manifest as well as the full receipt,
closing a real reproducibility gap found by the browser pair test.

The comparison contract follows each layer's declared execution effect. A
ranking or branch-order intervention must retain an identical target-free
first-frontier candidate digest; an admission or candidate-geometry change may
change that digest and records it as an outcome. Initial-state interventions
remain red until an explicit seed digest is available. Passing pairs are
aligned only by common discrete structural-update count and report coordinate-
free structural deltas. No candidate search is replayed or pooled, no update is
called physical time, and the result is not an energy decomposition, removed
physical interaction, kinetic law, independent-specimen estimate, or proof of
a causal physical mechanism. The live smoke also verifies the negative gate:
a known-window reference-guided first frontier is labeled target-tainted rather
than silently admitted to the matched analysis.

The same release consumes the immutable exact-seven A₂ catalogue landed in
the shared branch. The four size-eight layer-essential survivors exhaust all
1,995 seven-copy HNF bases apiece with zero unknowns. The two harder candidates
use the complete 3+3 meet-in-the-middle fallback on 32 quotients apiece; the
exact traversals contain 29,338,463 / 74,819,710 / 74,782,180 / 29,328,075
nodes. Root-corona replay and 16 / 72 / 72 / 62 sound
GCTS obstruction clauses remain separate evidence; outer-corona exhaustion and
global non-tiling/aperiodicity classification remain open.

### Executable one-control physics arms (Build 267)

`buildPhysicsProtocolControlBinding` now compiles a selected physics row and a
live select-control snapshot into a fail-closed intervention manifest. The
frozen registry names an explicit neutral value for 28 reversible geometric
surrogates and rejects hard constraints or representations that have no honest
off state. It verifies the control ID, enumerated option values, distinct
baseline/ablation values, and the set of other selected rows affected by the
same control. The affine-load control, for example, cannot be presented as a
one-factor ablation while both affine loading and archived stress response are
selected.

Stage 4 can now apply the verified baseline or arm B before candidate
enumeration. The normal stage-reset path rebuilds the same supplied specimen;
the immutable registration is then restored with exactly one changed control
and the active protocol IDs (the omitted row is absent only from arm B). The
manifest schema is 3 and the receipt hash covers the binding, baseline and
neutral values, active arm, applied-value verification, and target-free flags.
At the first structural action, arm controls and the matched-counterfactual
selector freeze. Browser regression verifies surface completion `soft → none`,
baseline restoration, ready execution in both arms, and design-only treatment
of steric exclusion. No paired outcome is fabricated: candidate-digest and
matched-input gates remain obligations for a later two-receipt comparison.

### Matched physics counterfactual planner (Build 266)

The pre-growth protocol can now declare a one-layer baseline/omission pair.
`buildPhysicsProtocolIntervention` inspects the selected row's exact execution
flags rather than assuming every ablation has the same causal design. A pure
ranking or search-order term is eligible for a same-candidate comparison and
must reproduce the first-frontier digest. Removing hard admission or candidate
geometry makes the candidate set an outcome; removing seed logic makes the seed
digest the intervention. In all cases the input configuration, public boundary,
and every other selected protocol layer must remain unchanged.

Only selected executing rows with a real execution hook appear in the planner.
Its receipt record distinguishes a ready local control route from a design-only
omission, carries exactly one changed layer, and is frozen before candidate
enumeration with `targetUsed=false`. The result defines an auditable geometric
counterfactual; it does not identify a thermodynamic contribution, eliminate a
physical mechanism, integrate dynamics, or establish population-level cause.

### Pre-growth physics protocol composer (Build 265)

The Stage 4 preflight now supports an explicit investigation protocol. Users
select physical-manifest records before the candidate frontier exists, while
the pure protocol compiler groups the selection by readiness and reports its
coverage of hard admission, candidate geometry, initial state, ranking, and
search order. Presets expose the currently executing set and the larger locally
actionable set; individual records can be added or removed from their full
evidence→encoding→execution→response→boundary trace.

Protocol selection has no authority to change a control. Configurable,
missing-evidence, evidence-only, and external rows remain visibly distinct, and
the ready gate rejects a selection with unresolved requirements. At the first
structural action the complete selection, blockers, effect coverage, negative
claim boundary, and target-free invariants freeze inside preflight manifest
schema 2. The existing receipt hashes that manifest, so a later run cannot
silently rewrite which physical approximations were supposed to govern growth.

### Size-eight A₂ evidence frontier (Build 264)

The browser evidence view now consumes the generated layer-essential
size-eight catalogue. From 4,940 symmetry-distinct inputs, independently
replayed exact weighted quotients certify 4,529 at one copy, another 405 at two
copies, and two more at four copies. The final four candidates exhaust every
six-copy HNF basis—2,015 per candidate, with zero unknowns—and have replayed
first-corona witnesses containing 24, 29, 30, and 27 copies.

The same view reports 16 / 72 / 72 / 62 sound CEGAR/GCTS obstruction clauses
and the exact exclusion of direct scalar scales 2…8, all 49 unequal layer-scale
pairs in that range, and connected two- and three-copy metatile alphabets at
scales 2 and 3. These are bounded negative families. No outer first-corona
space is exhausted, and larger periodic domains and general substitutions are
unsearched; consequently all four global classifications remain open.

### Physics readiness planner (Build 263)

The pre-growth atlas now distinguishes five reasons for an execution state:
`executing`, `configurable`, `missingEvidence`, `evidenceOnly`, and `external`.
This prevents a disabled capillary hypothesis, a missing force-labelled archive,
a posthoc structural observable, and unresolved collective electronic/nonlocal
response from appearing as the same red omission. Readiness filters compose
with the existing physical-scale, evidence-class, and exact-effect filters.

Every manifest record carries an explicit control-route availability and label.
An unavailable calculation channel is routed to acquisition; a disabled local
geometric hypothesis is routed to its control; a pure diagnostic names its
evidence-only role; and an unimplemented nonlocal response states that an
external solver or new trainable state variable is required. Routing focuses a
control and changes no setting. `physicsExecutionReadiness` and the pure effect
matrix serialize the same coordinate-free state before candidate enumeration,
with no target or physical clock.

### Execution-effect atlas (Build 262)

The complete 43-row pre-growth physics manifest now supports a second,
orthogonal inspection axis. Each row exposes whether it can change hard
admission, bounded candidate geometry, the initial seed state, soft branch
ranking, reproducible branch order, or none of those execution objects. These
six cells form a compact rail on every process card; physical-scale, evidence,
and execution-effect filters compose, and a genuinely empty intersection is
reported rather than silently selecting a different record.

The pure `buildPhysicsEffectMatrix` contract derives every cell from the same
frozen execution lineage used by the five-step detail view and receipt. Effects
may overlap (the learned GCTS connection layer can gate and rank), while an
inactive or unresolved layer has no execution hook. The overview is
coordinate-free, target-free, pre-candidate, and carries no physical time. It
is a causal software map of what a surrogate may change, not evidence that the
surrogate is an energy, force, barrier, rate, or dynamical law.

### Physics-to-geometry execution lineage (Build 261)

The frozen pre-growth manifest now carries an execution lineage for every
physical layer. Five interactive nodes separate source evidence, geometric
encoding, direct search effect, finite structural response, and the negative
claim boundary. Independent flags state whether the row can alter hard
admission, candidate geometry, seed initialization, ranking, or branch order;
target access and physical time remain false.

The taxonomy additionally classifies calculation-stress and paired
stress–strain-response records, closing the only two unclassified manifest
IDs. A static equality contract compares all 45 current manifest IDs with all
lane assignments, while the pure module rejects duplicate IDs and keeps future
unclassified records fail-visible. This is provenance and execution semantics,
not new physics or a stronger growth claim.

### Port-resolved GCTS level sets (Build 260)

Stage 3 now preserves train-observed connection directions in intrinsic proper
cluster frames as an explicit marking-port atlas. The per-cluster renderer uses
solid compatible-port lobes and dashed unsupported training sectors; it never
turns a scalar channel into a spherical pseudo-potential. Raw direction modes,
display-resolved modes, observation counts, unsupported-sector semantics, and
the negative physical-potential/candidate-geometry flags are receipt-visible.

Executable contracts cover scalar directionality, channel-sector assignment,
proper-frame rotation covariance, and the no-spherical-fallback invariant.
Ice Ih, NaCl, and the Al–Cu–Fe IQC were exercised in the browser as distinct
cluster-card ensembles. This is a visualization and provenance correction;
it does not upgrade any continuation, stationarity, or exponential-growth gate.

### Evidence-ordered cluster discovery (Build 259)

The Stage 2 process microscope now derives its reversible event order from the
selected cover itself. Candidate relations appear by element-resolved distance;
support occurrences settle by maximum uncovered-site gain, recurring class
frequency, minimum redundant overlap, family role, and lexical support. A
rejected relation stays tentative until both endpoints have acquired selected
cover evidence. No hash or pseudorandom schedule remains in the clustering
visualization.

The trace emits explicit decision reasons and serializes its ordering audit.
This is still a deterministic replay of an already learned recurring-isometry
cover, not molecular dynamics or an online optimizer history. The distinction
is visible in the process evidence ledger and receipt. GCTS learning continues
in Stage 3 on separate rotating scenes for every molecular, bridge, support,
void, and literal residual class.

### Frozen-frontier response intervention (Build 258)

The archive-response Study Guide now performs its one-factor comparison on a
single pre-commit frontier rather than asking the reader to trust that the two
arms share geometry. Each hard-admitted candidate carries both the observed
contact/angle strain and the archive-response-transformed strain. The audit
replaces exactly that one signed score-ledger contribution, re-ranks with a
stable candidate-key tie break, and reports the unchanged frontier digest,
winner identity, rank displacement, pairwise inversions, Spearman rank
correlation, and its own deterministic digest.

This is a counterfactual soft ordering, not a second execution. Candidate
coordinates, cluster types, proper SE(3) poses, emitted sites, and hard gates
are identical by construction. The receipt records whether the frozen
snapshot was captured during labeled known-window replay or during target-free
continuation, and the UI keeps those evidentiary roles distinct.

### Guided archive-response intervention (Build 257)

The Study Guide now treats the pinned public calculation series as a complete
physics-to-geometry investigation. It reconstructs the exact NOMAD specimen,
preselects the fifth archived frame because that frame lies inside the frozen
small-strain fit domain, and registers two otherwise identical arms: a capped
response-shaped soft metric and a geometry-only control. Neither arm changes
candidate coordinates, cluster identity, finite proper-pose ports, or any hard
admission certificate.

The comparison records continuation sites, frontier work, and finite-window
geometric S(q) from executed receipts. A shareable recipe URL reconstructs the
public entry, paused stage, response arm, and declared controls without
embedding coordinates, fitted weights, or execution history. The result is an
auditable geometric intervention over one correlated archive—not a general
elastic model or a claim of favorable dynamics.

### Reproducible public worked investigation (Build 256)

The browser now exposes the known positive NOMAD response archive as a
one-click, no-text-field worked example. Exact-entry retrieval validates that
the returned entry ID matches the requested ID, then passes through the same
archive parsing, evidence profiling, supercell expansion, response fitting,
and fail-closed promotion gates as a searched specimen. The resulting URL
contains `specimen=nomad:KFBchFQ1IQAE-JEgzOS1XzZlfsTz` and reloads the exact
public investigation directly.

Receipts distinguish exact-entry retrieval from randomized page sampling and
retain the entry ID, source URL, and share token. The worked example is a
reproducible code-path audit: its apparent K* and G* remain correlated
within-archive response scales, not transferable material constants.

### Mechanical-response evidence receipt (Build 255)

The response fit now serializes as a SHA-256-addressed experiment artifact.
It includes the precise frame subset, fixed small-strain domain, excluded-pair
count, compliance channels, held-frame residuals, response-scale summaries,
selected frame, selected deformation gradient, and explicit false flags for
candidate-geometry changes, hard-admission changes, target coordinates, growth
outcomes, physical time, independent validation, and a general elastic-tensor
claim. The physics preflight mirrors the same state before an action executes.

The live positive-path audit uses public NOMAD entry
`KFBchFQ1IQAE-JEgzOS1XzZlfsTz` (Cl₂Na₂; 144-site browser supercell). Of nine
source-to-final pairs, five satisfy the predeclared `||E||F <= 0.15` domain;
four are excluded before fitting. The fixed promotion gate passes with
leave-one-frame-out skill 0.7162377, apparent K*=1.2405901 GPa, and apparent
G*=2.4440705 GPa. These numbers demonstrate the code path, not transferable
elastic constants.

### Paired archived cell–stress response (Build 254)

For public archives with at least five finite small-strain frame pairs, the UI
fits hydrostatic and deviatoric compliance independently from stress change to
final-cell Green–Lagrange strain. The admissible domain is fixed at
`||E||F <= 0.15`; larger deformations are excluded before fitting and reported.
Promotion additionally requires same-sign channels, leave-one-frame-out skill
of at least 0.2, and apparent bulk/shear scales within 0.1–2000 GPa. When all
gates pass, a user-selected archived frame can supply a capped 1–4% affine
metric for soft frontier ordering. It never changes the exact candidate set or
a hard geometric gate.

The displayed K* and G* are within-archive apparent response scales, not
material elastic constants. Archive order is not elapsed time, the final cell
is an input reference, and no energy, force field, equilibrium, or kinetic
claim follows from this fit.

## Claim under test

From at most 1,000 species-labelled Cartesian positions, learn a bounded,
rotation-invariant hierarchy of overlapping clusters and local boundary
markings.  Use that hierarchy to continue a crystal or quasicrystal with fewer
search decisions than an atom-by-atom search, without being given a lattice,
unit cell, space group, cut-and-project coordinates, or generator labels.

“Exponential growth” applies to the implicit hierarchy: if the median support
amplification is `b > 1`, a level-`L` accepted macro placement represents
approximately `b^L` atoms.  Materializing or exporting `N` atomic coordinates
still has an unavoidable `O(N)` cost and must be reported separately.

### Archived stress-shape metric (Build 253)

The public-data path now retains finite NOMAD
`run/calculation/stress/total/value` tensors. NOMAD's built-in Metainfo uses SI
units, so the browser converts Pa to GPa after symmetrizing parser-level numeric
asymmetry. The receipt records the full tensor plus trace, hydrostatic,
deviatoric-Frobenius, and total-Frobenius summaries and its exact archive path.

Stress may optionally cross the observation/search boundary only as a declared
normalized metric hypothesis. The existing contact-and-angle strain term is
re-evaluated under `F = I ± m σ / ||σ||F`, where `m` remains a small prescribed
dimensionless amplitude. The plus arm preserves archive sign and the minus arm
is an explicit sign-reversal ablation. Candidate coordinates, candidate IDs,
and all hard geometric certificates are identical; missing, malformed, zero,
or non-finite tensors disable both arms. The normalization deliberately removes
stress magnitude. It is not a learned compliance, elastic tensor, modulus,
Hooke-law prediction, strain energy, force balance, mechanical equilibrium,
relaxation trajectory, kinetics, or time.

### Proper-pose residual-force seeds (Build 252)

The browser's site-resolved external residual-force channel can now cross the
GCTS representation boundary without becoming a force integrator. Each vector
is converted once to eV/Å, stored in the supporting cluster's local proper
frame, and transported to a candidate as `Fworld = Rcluster Flocal`. In the
explicit force-seed ablation, its direction and its magnitude relative to the
frozen reference-sample p90 define a proposed offset
`cap min(1, |F|/F90) unit(Fworld)`. The cap remains 5% of `dnn` and below half
the exact merge tolerance. Multiple commuting placements that predict the same
new site contribute through an order-independent vector mean. A worsening seed
is discarded before generic projection; exclusion, coordination, angle,
boundary, exact topology, and proper-port checks can still roll back the whole
placement.

Receipts separately count reference, local-template, frozen-rule, live-
candidate, and placed force vectors; record the p90 scale, seed use, and whether
the last seed survived; and state that no target entered. Cluster cards, live
candidates, and accepted descendants expose the same transported direction.
This is a bounded rigid-environment hypothesis over one method-dependent
calculation snapshot. It does not infer a transferable force field, Hessian,
energy surface, mass, time step, optimizer path, MD trajectory, rate, or
physical time. The unseeded bounded geometric projection remains the direct
control.

### Proper-pose observed relaxation seeds (Build 251)

The browser can now use a fixed-topology selected→final archive pair to
leapfrog one local relaxation hypothesis. It decomposes variable-cell motion
into affine cell deformation and minimum-image non-affine site displacement,
stores each non-affine vector in the learned cluster's local proper frame, and
transports it to a new candidate as `Δrworld = Rcluster Δrlocal`. An explicit
post-attachment mode supplies these vectors as initial offsets to the bounded
contact-residual projection. The total displacement remains capped at 5% of
`dnn` and below half the exact merge tolerance. A seed that worsens the bounded
contact+tether objective is discarded; any failed exclusion, coordination,
angle, public-boundary, exact-cluster, or port certificate rolls back the whole
projection. Receipts distinguish supplied, local-template, candidate,
transported, retained, and rejected vectors.

This is an observed geometric-difference reuse, not learned dynamics. The two
frames do not establish a force law, velocity, physical time step, optimizer
clock, minimum-energy path, barrier, transition probability, diffusion event,
or growth rate. The copied vector is valid only as a declared rigid local-
environment hypothesis, and the unchanged generic projection remains the
control.

### Collinear scalar spin as an exact site color (Build 250)

When a source calculation supplies per-site signed collinear spin populations,
the browser can now preserve their polarity as part of the finite GCTS marking
alphabet. The cluster cover itself is unchanged. Each local template stores its
observed scalar; a proper-SE(3) placement transports the label without rotating
it; and coincident same-species sites merge only when the two supplied scalar
colors agree. Missing labels do not become guessed zeros. An explicit
chemistry-only ablation disables this gate while retaining the same geometric
candidate construction, and receipts report reference/template/rule/candidate
coverage, overlap checks, and compatibility prunes.

This is a discrete geometric compatibility hypothesis, not a magnetic model.
The source API supplies neither a three-dimensional quantization axis nor a
guaranteed magnetic-moment unit, and the browser infers no vector moment,
exchange coupling, Hamiltonian, energy, domain wall, ordering temperature,
force, relaxation trajectory, kinetics, or physical time.

### Transported displacement ellipsoids (Build 249)

The browser now renders the covariance that the growth engine actually uses.
Every accepted generated site reconstructs the ordered eigensystem of its
transported Cartesian U tensor; live frontier candidates and committed sites
therefore carry oriented 2σ wire ellipsoids. The separate rotating cluster
scenes used during GCTS learning project the same rotated covariance into a 2D
ellipse, making anisotropy and orientation transport inspectable per cluster.
A layer toggle hides these glyphs without modifying candidates, markings, or
admission. This is one matrix shown in several views, not an added physical
field or a claim of correlated dynamics.

### Proper-pose displacement transport (Build 248)

Reported Uiso/Uij no longer stops at the training-time pair table. Each cluster
template stores the full covariance in its local proper frame; every candidate
rotates it into the live Cartesian frame as `Uworld = R Ulocal Rᵀ`. Candidate
admission, commuting-antichain compatibility, swept-arrival clearance,
robustness margins, and the post-attachment hard recheck resolve the pair width
again along the current connecting direction. Newly committed sites retain
that transported tensor, so the hypothesis remains self-consistent across
later generations. A missing pair of live tensors falls back byte-for-byte to
the frozen scalar exclusion.

This closes a covariance-lineage gap but does not turn crystallographic ADPs
into dynamics. Replicating an observed tensor with a rigid cluster is an
explicit geometric-template assumption. The model still assumes independent
site covariance and does not infer correlated atomic motion, phonons,
temperature, contact probability, a potential, force, barrier, collision
trajectory, kinetics, or physical time.

### Directional Uij contact geometry (Build 247)

The browser now transports reported Cartesian Uiso/Uij into the colored local
contact model. Each observed pair uses its connecting direction `n` to compute
`σpair = √(nᵀ(Ui+Uj)n)` under an explicit independent-site covariance
assumption. The one-sigma lower contact support is stored alongside the mean
contact, broadens the soft contact-strain scale, and can lower the hard
exclusion enough to preserve that reported ellipsoidal support. Missing tensors
contribute zero. Receipt fields separate the original mean-position exclusion,
the adjusted exclusion, directional observation counts, and sigma summaries.
The scalar metric-isometry floor remains separately reported; the cover learner
does not pretend that overlapping pair intervals form an exact equivalence
relation. This is uncertainty-aware geometry, not a correlated-displacement or
phonon model, contact probability, potential, force, dynamics, or physical time.

### Full anisotropic displacement powder quadrature (Build 246)

The reciprocal-space inspector now offers a second reported-displacement view
that retains the complete intrinsic-space Uij covariance rather than reducing
it to Ueq. For each deterministic powder direction it evaluates the attenuated
coherent amplitude in O(N), restores every exact unit self term, and averages
over 96 directions. This is equivalent to attenuating all coherent i<j terms
but avoids a directional O(N²) expansion. Fully isotropic tensors use the exact
analytic Ueq kernel, providing a strict compatibility check with Build 245.

Scientific regressions require the zero-tensor curve to equal the mean-position
curve exactly, the isotropic curve to equal the Ueq curve exactly, anisotropy to
respond to its orientation relative to pair geometry, joint proper rotations
to agree within the declared quadrature error, invalid covariance to fail
closed, and a 400-site calculation to remain interactive. The receipt records
the quadrature, direction count, anisotropic weighted-site count, and unchanged
boundaries: no diffuse redistribution, q-dependent form factor, instrument
response, refinement, temperature inference, phonon dynamics, or growth input.

### Reported-displacement reciprocal-space view (Build 245)

The finite-observation powder inspector can now apply coherent pair attenuation
from the intrinsic-dimensional isotropic equivalent of reported Cartesian
Uiso/Uij tensors. The mean-position curve remains available beside it. The
self term is retained, unknown tensors use zero attenuation, and missing
diffuse redistribution is stated explicitly; this is not a refinement,
temperature inference, phonon model, force field, or dynamical trajectory.

### Reported crystallographic displacement envelopes (Build 244)

The interstitial network now optionally subtracts directional
`k√(nᵀUn)` support at 1σ, 2σ, or 3σ from imported Cartesian Uiso/Uij tensors.
The topology and empty-simplex witnesses are unchanged; only node and throat
clearances change. Missing tensors are counted and contribute zero support.
This is a coordinate-free structural ellipsoid hypothesis, not temperature,
dynamics, probability, a trajectory, or a physical-time integration.

### Sample-fitted multicomponent contact envelopes (Build 243)

The interstitial pathway now offers a third framework hypothesis between point
sites and a fixed element table. From the already train-only colored distance
envelopes, it identifies the leading nearest-contact shell and fits one
nonnegative additive envelope radius per supported species. The fit is weighted
by the number of nearest observations. Cordero covalent radii enter only through
a shared scale and ridge ratio prior, which makes an underdetermined cross-only
binary system solvable without silently treating equal radii as known physics.

Every result exposes the selected and excluded species pairs, support count,
RMS and maximum residual, data-matrix rank, parameter count, and number of
prior-dependent degrees of freedom. The browser uses the fitted radii in the
same empty centers and shared-face throats as the point and covalent views, for
both finite growth windows and periodic input quotients. Candidate topology is
therefore identical across models. A fitted value is explicitly a geometric
contact envelope conditioned on the supplied sample, not an inferred ionic,
metallic, van-der-Waals, oxidation-state, energy, or force-field radius. It is
not used to train or accept growth actions.

### Periodic input-quotient interstitial network (Build 242)

For a supplied three-dimensional periodic cell, the interstitial audit may now
construct a separate periodic reference quotient. It creates neighboring cell
images, resolves empty tetrahedral circumspheres without the finite view's
unnecessary inside-simplex restriction, and quotients coincident centers back
into the reported cell. Two quotient nodes are adjacent only when lifted
tetrahedra share an exact three-site face. Every edge stores the integer image
translation needed to lift its child center.

A component is called geometrically periodic only when a closed graph walk
accumulates a nonzero integer cell translation. The certificate reports the
independent winding rank, lattice axes touched by winding cycles, thresholded
winding rank, wrapped-edge count, and widest point- or covalent-envelope
winding bottleneck. A simple-cubic regression gives 64 quotient centers, 192
face-witnessed edges, 48 wrapped edges, rank-three winding, and an exact
point-site bottleneck of `sqrt(1/2)` nearest-neighbor units; the certificate is
invariant under translation, proper rotation, and atom permutation.

This mode is intentionally restricted to the supplied input quotient. The live
grown cloud remains a finite explicit structure and atoms beyond the observed
cell are never folded back into it. Cell winding is a topological/geometric
statement, not accessible porosity, probe transport, hopping, a migration
barrier, permeability, diffusion, a rate, or elapsed time.

### Species-resolved steric-envelope hypothesis (Build 241)

The interstitial pathway now preserves two explicitly separate geometries. The
exact point-site graph remains the baseline. An opt-in hard-envelope view assigns
each supported displayed species its element-only covalent radius from Cordero
et al., [Dalton Transactions 2008, DOI 10.1039/B801115J](https://doi.org/10.1039/B801115J).
At every empty center it records the minimum atom-center distance minus that
atom's radius; along every shared-face edge it records the minimum distance from
the complete straight segment to every radius envelope. The browser can switch
models without rebuilding or changing the candidate graph. A finite preset
library—point probe, current displayed species, and common light/mobile
elements—sets the effective spherical-probe threshold without a text field;
manual slider changes become an explicitly labelled custom threshold.

The portal fails closed when a displayed species lacks an explicit radius. It
records the radius source, selected model, selected probe, and threshold in the
receipt, and exposes the widest core-to-front covalent-envelope bottleneck as a
separate consequence channel. Covalent radii are a deliberately visible proxy:
they do not encode oxidation state, coordination number, spin state, anisotropic
electron density, bonding environment, solvation, or thermal motion. Therefore
this view is not an ionic-radius calculation, accessible porosity, a migration
barrier, permeability, diffusion coefficient, rate, or physical time, and it
does not rank or admit growth actions.

### Witnessed interstitial bottlenecks (Build 240)

The face-adjacency graph now carries a finite geometric capacity on every edge.
For two adjacent empty centers, the browser evaluates the minimum distance from
every explicit point site to the complete straight segment joining the centers;
the smallest value is the witnessed throat clearance, normalized by the
supplied median nearest-neighbor distance. Node clearance and edge throat
clearance jointly define a thresholded subgraph. The interactive threshold
recomputes open centers, open throats, components, isolation, and components
touching both the declared inner-core and growth-front radial bands. A widest-
path calculation separately reports the maximum bottleneck attainable between
those bands, and the material-consequence matrix retains that value without
mixing it with component fraction or empty-center size.

This is an exact result for straight segments among sampled, locally witnessed
point-site centers. It supplies no atomic/ionic radius, probe radius, curved
path, continuous void boundary, periodic image, energy landscape, hopping
model, or thermal sampling. The threshold is an exploratory geometric cutoff,
not a particle radius. Therefore the result is not accessible porosity,
physical transport connectivity, a migration barrier, permeability, a
diffusion coefficient, a rate, or physical time, and it remains excluded from
growth candidate generation, marking, ranking, and admission.

### Witnessed interstitial connectivity graph (Build 239)

Each retained empty center now carries all locally witnessed defining
simplices. The browser joins two centers only if at least one simplex pair shares
a complete edge in 2D or triangular face in 3D. This produces a finite exact
face-adjacency graph over the sampled empty-center vocabulary. The radial
clearance plot renders the graph and can filter all nodes, the largest
component, components touching both declared core and growth-front radial
bands, or isolated cages. Receipts and leap snapshots retain node/edge counts,
components, isolated fraction, mean degree, graph cycle rank, largest-component
fraction, and the number of core-to-front components. The consequence matrix
uses only the largest-component fraction and does not merge it with clearance.

The graph says that witnessed simplices share explicit sites. It has no atomic
or probe radii, continuous void boundary, throat cross-section, energetic
barrier, hopping rule, or rate. Consequently it is not accessible porosity, a
physical diffusion path, permeability, migration kinetics, or a transport
coefficient, and it remains excluded from candidate generation and ranking.

### Finite interstitial-clearance pathway (Build 238)

Explicit gap clusters now have a quantitative, dimension-aware companion. From
an invariant radial sample of explicit sites and complete nearest-distance ties,
the browser forms locally witnessed triangles in 2D or tetrahedra in 3D. A
circumcenter is retained only when the simplex is nondegenerate, the center lies
inside it, and no explicit site lies inside the corresponding circle or sphere.
Clearance is normalized by the supplied configuration's median nearest-neighbor
distance. The interactive view compares before/after distributions, maps
clearance against normalized centroid radius, and traces median, p90, maximum,
or growth-front clearance across certified structural states. The same p90
channel appears independently in the material-consequence matrix.

This is a finite point-site empty-region audit. It supplies no atomic or ionic
radius, periodic image, probe radius, surface reconstruction, or connectivity
between empty centers. It therefore cannot establish porosity, pore volume,
accessible free volume, vacancy/interstitial identity, a diffusion channel,
migration barrier, pressure, free energy, rate, or physical time. It is not used
to generate, admit, or rank growth actions.

### Core-to-growth-front material profile (Build 237)

The finite packing pathway now resolves spatial heterogeneity instead of
reporting only global, core, and surface summaries. It partitions the explicit
structure into eight fixed bins of centroid radius normalized by the maximum
explicit-site radius. For each finite shell it retains the median sixth-neighbor
number-density ratio and exact fractions of every displayed site species. The
interactive plot compares the selected structural state with the supplied
configuration and offers one standard-color channel for every element, with no
binary-system assumption. The material-consequence matrix also records the
largest positive outer-shell fraction excess relative to the complete current
configuration.

The radius normalization and local-density ratio are invariant to translation,
proper rotation, atom order, and a common scale change. This is a finite radial
site audit: it neither infers equilibrium segregation nor labels a surface
phase, chemical potential, diffusion process, surface/interfacial energy,
porosity, pressure, growth rate, or elapsed time. Occupationally disordered
sites remain displayed-site counts here; their full alternative chemistry
continues to live in the separate occupancy geometry and receipt.

### Finite local packing-density pathway (Build 236)

The browser now records a finite local-density distribution in every retained
structural state. At radially stratified centers it estimates number density
from the radius to the sixth neighbor, using the dimension-aware ball measure,
and normalizes it to the median density of the inner half of the supplied
configuration. The interactive view separates all sampled centers, the inner
core, the outer radial quarter, and the inverse relative-local-volume proxy;
the leap consequence matrix uses the identical retained snapshot.

This is a geometric finite-observation estimator. It is invariant to
translation, proper rotation, atom order, and a common rescaling of both the
observed and supplied configurations. It does not create periodic images or
infer a unit cell. It must not be reported as mass density, packing fraction,
porosity, thermodynamic free volume, pressure, free energy, a bulk limit,
kinetics, or elapsed physical time, and it is not used to rank or authorize
growth actions.

### Species-resolved stoichiometry pathway (Build 235)

The browser now unfolds the scalar composition-deviation channel into an
interactive multicomponent history. The vocabulary is derived from the union of
species recorded in the retained structural states, so ternary and higher-order
systems use the same code path as binary examples. For each certified state the
view preserves exact integer counts, normalized fractions, a stacked
standard-element-color bar, total-variation deviation from the supplied
configuration, and species-specific finite/open reservoir accounting. A
selected species is plotted over structural-leap index against its dashed
supplied-fraction reference; selecting a state routes to the identical leap
certificate rather than reconstructing or relabelling it.

The supplied composition is a bookkeeping reference, not a target phase label.
No chemical potential, activity, phase equilibrium, segregation energy,
diffusion, flux, growth rate, or elapsed time is inferred. The pathway is not a
new action score and does not change the candidate set, hard gates, marking,
search order, or emitted geometry. Its receipt manifest records those negative
claims together with the exact species vocabulary and state source.

### Leap-resolved material consequences (Build 234)

The live structural-leap certificate now consolidates its previously separate
local, mesoscale, chemistry, and reciprocal-space snapshots into one interactive
before/after fingerprint. It reports exact site inventory; total-variation
composition deviation from the observed input fractions; finite reservoir
inventory; colored coordination shortfall; q6 or |psi6|; exact-pair
centrosymmetry; covariance radius and anisotropy; shared multi-nucleus interface
fraction; and unit-weight finite-window S(q) peak prominence. The new composition
snapshot retains counts, fractions, the observed target ratio, and explicit
negative inference flags in every leap receipt.

The display does not rank the channels or treat positive/negative changes as
favorable. Every row is independently scaled, links to a channel-specific
definition and limitation, and is aligned only by discrete GCTS search update.
It therefore makes the material consequence of a geometric leap inspectable
without relabelling the sequence as physical time, a trajectory, free energy,
phase transition, rate, probability, or experimental scattering.

### Bounded notebook snapshots (Build 231)

Saving a run in the browser no longer executes the full downloadable receipt
pipeline. A dedicated bounded snapshot retains the observed-input digest,
intervention settings, first and latest frozen-frontier identity, retained
structural leaps, marking-to-cover-family lineage, exact notebook outcomes, and
claim boundary. Its SHA-256 is a snapshot digest, not a claim that the full
receipt was built. Creation-response blocked surrogates are explicitly deferred
to full receipt export; this keeps the notebook interactive without replacing
or weakening the complete scientific artifact.

Build 232 adds an explicit **Compute response atlas** action. It freezes the
current explicit-site digest, the last 256 eligible placement ledgers, leap
count, and bounded-projection counters before fitting the existing grouped and
chronologically blocked response analyses. The cached artifact is reused by a
notebook snapshot or full receipt only when that state SHA-256 still matches;
resetting the specimen or recording another structural leap invalidates it.
The blocked surrogate and horizon grid runs in a module worker and reports each
outcome/phase without blocking the rendering thread. This separates interactive
capture from deliberate statistical analysis while
preserving the same no-target, no-atom-pseudoreplication, and no-physical-time
claim boundary.

### Exact corona-marking presentation (Build 233)

The browser Evidence Atlas now includes the A₂ layered lattice-function census
as a geometry stress test alongside, but explicitly distinct from, atomic
material systems. Of 1,119 size-seven non-product candidates, exact weighted
quotient certificates remove 910 at two copies and another 98 at four copies;
111 exhaust all 399 determinant-14 HNF bases. Every survivor has a replayed
root corona. For eight focused candidates, exact-model CEGAR turns independently
replayed UNSAT cores into sound family-obstruction clauses. Greedy reduction
finds one replayed 3–12-placement core per candidate; seeding those cores into a
strengthened continuation yields 1,113 retained clauses (130–156 per candidate).
The interactive atlas renders the underlying seven-cell supports, reduced-core
sizes, and clause counts directly from the generated catalogue.

This result is a concrete model of a GCTS marking: a bounded local obstruction
generalizes to a finite family of incompatible connections. It is not a growth
curve or physical potential. Because no focused outer first-corona space is
exhausted and no radius-two witness has been found, every candidate remains
unresolved; neither non-tiling nor aperiodicity is claimed. Excluding scalar
single-shape substitutions at scales 2–6 and 336 cellular anisotropic cases
also leaves decorated, multi-metatile, and other substitution grammars open.

### Browser presentation boundary (Build 223)

The cluster-identification stage now presents its molecular-cover accounting as
a live four-part decomposition: finite molecules, connection clusters,
gap/void clusters, and total observed-site coverage. Counts advance only when
the corresponding cover placements settle in the reversible discovery trace.
For H2O the finite three-site component is therefore visible before the
hydrogen-bond and O-ring supports that interpolate the periodic configuration.
This is a visualization of the learned cover, not a new classifier: formula
metadata is not an input, molecular bonds remain distinct from inter-molecular
supports, and no atom-centred radial shell is substituted for the molecule.

Build 224 adds a display-only decomposition microscope to the same ribbon.
Selecting molecule, connection, or void isolates settled edges belonging to
that exact cover family; selecting complete cover restores all tentative,
rejected, and accepted relations. Shared edges use their complete learned
family incidence rather than a display-priority color. The interaction changes
no cover membership, type, pose, marking, candidate, or benchmark statistic.

Build 225 carries that display focus into GCTS learning. A molecule, connection,
or void selection becomes the initial filter over the separate three-dimensional
marking scenes, where the corresponding proper-pose, symmetry-gauge, port-rank,
and channel-allocation evidence is already reported per class. Gallery filters
update the same focus in reverse. The handoff survives pipeline-stage rebuilds
for one specimen but resets on the input stage, and it remains absent from the
learned artifact and search state.

Build 226 conditions the visible GCTS mismatch curve on that same display
focus. Per-family fit and held-out losses are evaluated from the immutable
coefficient state at every training step and the original index-based split;
the training algorithm, sample order, coefficients, active channels, and global
loss remain unchanged. This provides family-resolved diagnostics for molecular,
connection, and void sections without turning display selection or held-out
mismatch into a fit input, growth score, energy, or physical potential.

Build 227 makes that cover-family provenance auditable at material-growth time.
The candidate constraint ledger maps each frozen parent→child rule back to its
molecule, connection, gap/void, residual, or recurring-support families, and
accepted placement evidence retains the same mapping. The current family focus
is reported only as an inside/outside display diagnostic and is explicitly
excluded from ranking. The specialized ice oxygen-anchor trace is identified as
a separate molecular primitive-port continuation, not as evidence that the
generic promoted-macro executor ran.

Build 228 adds a clickable cover-propagation history beside the live tree-search
stack. It aggregates accepted and rejected decisions by cover-family transition,
reports their causal-depth span and exact emitted-site count, and keeps the
specialized molecular trace visually and semantically separate. The downloadable
receipt now includes grouped lineage totals, a coordinate-free digest over all
accepted generic lineage records, and up to the latest 256 records; no
coordinates, target sites, energies, or physical mechanisms enter this audit.

Build 229 freezes marking provenance at every growth decision. The record names
the exact single or portfolio-selected library source and retains its channel
capacity, bounded neighborhood reach, representation/readout, score, threshold,
and gate role. The lineage inspector therefore shows which learned connection
section governed each propagated cover family within that run; changing or
retraining the marking starts a new run, while the exported receipt keeps the
old provenance for an explicit comparison. The ice molecular-port unanimity
trace has an explicitly separate provenance schema and is not counted as a
generic GCTS library intervention.

Build 230 carries that provenance into the compact experiment notebook. A saved
run retains the active marking, every executed marking-source group, its finite
score range and threshold, and the coordinate-free cover-family transitions it
propagated. Selecting two runs renders the complete
marking→family-attachment→emission pathway on both sides. The existing
registered saved-marking gate remains authoritative: causal wording is allowed
only for identical observed-input SHA-256, unchanged non-marking controls,
identical first target-free candidate/hard-admitted sets, complementary frozen
artifacts, and a matched registered leap horizon or paired terminal fixed point.
All other lineage differences are labeled descriptive; no potential, kinetics,
physical time, or independent-specimen effect is inferred.

## Benchmark ladder

All learners receive only positions and species.  Hidden construction metadata
is available only to the evaluator.

1. A randomly rotated binary crystal, to establish the easy periodic control.
2. A three-species icosahedral cut-and-project point set, to establish a true
   three-dimensional nonperiodic control with finite local complexity.
3. A composition-matched hard-core amorphous point set, as the null control.
4. Noisy and defected versions of 1–3.
5. Experimental or DFT structures with provenance and held-out spatial regions.

The algorithm must be shared across the suite.  A model-set lift, a recovered
translation lattice, or a Fibonacci-axis grammar may be reported as a competing
specialized baseline, but not as generic GCTS.

## Gates

### G0 — recursive representation

- At least three learned cluster levels beyond atoms.
- Every level has a finite, explicitly reported marking domain.
- Median support amplification at least 2 over two consecutive transitions.
- Identical hierarchy statistics after an arbitrary rigid motion.
- The amorphous null must not pass merely because a large ball contains atoms;
  its promoted recurring cluster types must vanish or pay their dictionary cost.

### G1 — blind continuation

Train on a radial core of 300–1,000 atoms and hide an outer annulus.  Place the
annulus without inspecting its atoms.  Score species/position precision and
recall after optimal rigid registration, minimum-distance violations, RDF and
coordination error, and structural-class agreement.  Passing requires at least
0.95 precision and recall on clean controls and zero hard-core violations.

### G2 — search advantage

Run atomic moves and recursive macro moves with identical compatibility rules,
frontier, timeout, and random seeds.  Report candidate evaluations, expanded
nodes, backtracks, accepted atoms per decision, wall time, peak memory, and
explicit-output time.  The target is a 10× reduction in expanded nodes at
10,000 represented atoms and increasing advantage at larger implicit sizes.

### G3 — marking causality

Compare learned markings with no markings, shuffled markings, radius-only
markings, and an oracle compatibility table while holding the cluster dictionary
and proposal order fixed.  A marking matters only if it reduces nodes/backtracks
or improves held-out validity.  The target is a 2× node reduction or a 10-point
success-rate improvement on at least one ambiguous quasicrystal/defect task.

### G4 — scaling

Report 10×, 1,000×, and 100,000× implicit continuation.  Separately materialize
fixed prefixes to establish linear output throughput.  A million-atom label is
not allowed unless one million coordinates are actually emitted or the result
is explicitly labelled an implicit representation.

## Current measured baseline

`scripts/materials_recursive_gcts.py` implements G0 as a generic colored-point
algorithm.  It learns an overlapping ball at each center, recursively colors
those centers with a bounded evidence-ranked vocabulary, expands the marking
domain geometrically, and learns the modal colored annular section for every
cluster type.

On the deterministic current fixtures:

| system | atoms | largest recurring supports by level | support ratios | top-level atoms / greedy macro decision | G0 |
|---|---:|---|---|---:|---|
| binary crystal | 515 | 7, 27, 203, 515 | 3.86, 7.52, 2.54 | 515 | pass |
| icosahedral model set | 507 | 14, 49, 270, 507 | 3.50, 5.51, 1.88 | 507 | pass |
| amorphous hard-core null | 507 | 0, 0, 0, 0 | 0, 0, 0 | 0 | reject |

These numbers establish recursive representation only.  They do not establish
G1 continuation, G2 search advantage, or G3 marking causality.  In particular,
the final level approaching the finite sample size is saturation, not evidence
of unlimited growth.

### First blind-frontier result

`scripts/materials_gcts_blind_continuation.py` trains on the 507-atom
icosahedral core and cannot inspect the 1,722 hidden atoms.  Three matching
colored atoms determine an arbitrary rigid orientation of a learned cluster.
The GCTS section is the bounded set of species-labelled pair distances learned
in the core; a proposed connection absent from that section rejects the patch.

| ablation | candidate patches | proposed sites | correct sites | precision | hidden recall |
|---|---:|---:|---:|---:|---:|
| cluster overlap, no marking | 16,340 | 24,288 | 84 | 0.0035 | 0.0488 |
| learned bounded marking | 60 | 180 | 180 | 1.0000 | 0.1045 |

This is a causal G3 result with the cluster dictionary, seed, confinement, and
alignment procedure held fixed: the marking removes every false-positive site
in the first wave and improves precision by 289×.  It is also partial G1
evidence, but not a G1 pass—the one-wave recall remains only 10.45%.  Iterated
frontier waves must preserve precision and reach at least 95% recall.

The initial iterative ablation exposed two further limits.  Independent
pair-distance sections reached 35.8% recall after four greedy waves but
precision fell to 81.7%.  Treating a mixed patch as an all-or-nothing decision
also stalled: at the ambiguous second wave a cluster could contain both a
forced site and an unresolved alternative.

The current implementation therefore lets a marking *improve* a proposal.
Clusters propose sites; a larger bounded section retains only the supported
part.  At level 2 the section is colored by learned level-1 cluster types, not
only atomic species:

| wave | action / marking | candidate patches | added hidden sites | cumulative hidden recall | precision |
|---|---|---:|---:|---:|---:|
| 1 | level-1 clusters + radius-2.25 section | 60 | 180 | 0.1045 | 1.0000 |
| 2 | level-1 proposals + radius-3 refinement | 8,100 | 60 | 0.1394 | 1.0000 |
| 3 | level-2 macros + level-1 colored section | 1,620 | 120 | 0.2091 | 1.0000 |

Thus clusters of clusters now make a successful blind continuation step: 360
of 1,722 hidden sites are reconstructed with no false atoms.  An exploratory
level-3 macro plus level-2 colored section of radius 4 selects another 80/80
correct sites (25.55% cumulative recall), but its current explicit 270-atom
candidate expansion is too slow for the regular test path.

The same generic local learner and marked-growth engine completely solve the
periodic control.  A 515-atom spherical core hides 904 atoms of the larger
crystal.  Four marked waves add 284, 366, 246, and 8 atoms respectively, ending
with all 1,419 oracle sites, 1.000 precision, and 1.000 hidden recall.  No unit
cell, lattice indices, translation vectors, or space-group label are supplied
to the learner; the hidden lattice coordinates are used only for evaluation.

| blind benchmark | training | hidden | final precision | hidden recall | status |
|---|---:|---:|---:|---:|---|
| binary crystal | 515 | 904 | 1.0000 | 1.0000 | G1 pass |
| icosahedral model set, tested path | 507 | 1,722 | 1.0000 | 0.2091 | partial |
| icosahedral model set, exploratory level 3 | 507 | 1,722 | 1.0000 | 0.2555 | partial |

These results also show that large supports alone are not hierarchical GCTS.
Unmarked level-2/level-3 macros have poor precision; the recursively colored
section is the component that makes their useful subset identifiable.

### Exact transform DAG

`scripts/materials_gcts_transform_dag.py` now converts exact, rotation-only
cluster types into a reusable DAG.  A parent stores child type IDs, proper rigid
transforms, and residual atoms not covered by complete children.  Provisional
fingerprint types are split by full colored congruence before reuse, including
a chirality split: mirror-related occurrences are distinct unless a proper
rotation maps them.

| system | recurring support sizes | root entries | represented atoms | root compression | level-3 dictionary: explicit / DAG |
|---|---|---:|---:|---:|---:|
| binary crystal | 7 → 57 → 474 | 36 | 474 | 13.17× | 8,531 / 777 |
| icosahedral model set | 14 → 55 → 471 | 30 | 471 | 15.70× | 4,451 / 441 |

Expansion reproduces the representative species and Cartesian coordinates
exactly, and every stored child transform has determinant +1.  Support grows by
3.93–8.56× per level on these finite controls.  This passes the implicit
representation portion of the exponential-growth benchmark: one accepted root
reference can stand for hundreds of atoms.  It does not remove the unavoidable
linear cost of emitting those coordinates.

### DAG parent search versus atomic search

`scripts/materials_gcts_dag_search_benchmark.py` tests the DAG as an actual
search action.  It generates 2,048 adversarial proper-rotation candidates; each
decoy is translated so at least one child of the correct type agrees with the
known level-2 configuration.  Atomic search transforms and scores every leaf of
every candidate.  DAG-GCTS scores the recursively colored child ports, accepts
one parent, and expands its atoms once.

| system | atomic leaves / DAG child marks | operation reduction | measured wall speedup | selected parent |
|---|---:|---:|---:|---|
| binary crystal | 474 / 24 | 19.56× | 19.73× | exact |
| icosahedral model set | 471 / 22 | 21.19× | 21.08× | exact |

This passes the 10× G2 search-advantage target for parent recognition and makes
the “exponential” distinction operational: the accepted action count is one
parent rather than 471–474 atomic leaves.  It assumes the child-cluster layer
has already been inferred; blind quasicrystal frontier completion remains the
harder unfinished benchmark.

### Blind DAG frontier experiment

`scripts/materials_gcts_dag_blind_frontier.py` now carries the learned DAG into
the blind icosahedral frontier rather than benchmarking preidentified parents.
It indexes rare, rotation-defining connector marks, keeps a bounded
frontier-diverse beam, composes exact SO(3) child/parent frames, proposes
level-3 parents from partial level-2 children, and separates a sparse expansion
DAG from a dense overlapping marking.  The latter retains every typed,
oriented level-2 port centered in the learned parent support, including ports
discarded by the nonoverlapping compression cover.  Ground truth is excluded
from the policy and used only after selection for scoring.

Starting from the proven three-wave state (507 training atoms plus 360 correct
continuations), the current beam has 500 level-1 and 500 level-2 hypotheses.
It finds 8,477 frontier parent poses.  The sparse-cover score alone has 138
top poses with three agreeing children.  Atomic section filtering improves a
selected proposal from 55.7% raw precision to 72.0%.  Rescoring with the full
overlapping level-2 port marking raises the best score to 11, leaves 68 top
poses, and selects 46 new sites, 40 of which match the held-out model set:
87.0% precision and 2.32% additional hidden recall.  This is the first measured
gain specifically from a cluster-of-clusters GCTS marking, but it is not yet an
acceptable growth action.

A bounded exterior halo was then learned from repeated occurrences in each
parent's canonical SO(3) frame.  The training set supplies 1,681 recurring
exterior ports across 13 of 14 level-3 types.  None are directly observed at
the blind frontier—as expected for a genuinely exterior section—but one-step
lookahead asks which ports become partially supported after a provisional
action.  It reduces the 68-way internal tie to 20 poses.  Feeding that future
support back to individual sites retains 21 atoms, 19 correct: **90.5%
precision** and 1.10% additional hidden recall.  This improves the action but
still does not meet the no-error recursive-growth requirement.

| blind level-3 policy | selected sites | correct | precision |
|---|---:|---:|---:|
| raw parent expansion | 149 | 83 | 55.7% |
| atomic section | 50 | 36 | 72.0% |
| internal overlapping level-2 ports | 46 | 40 | 87.0% |
| exterior one-step site lookahead | 21 | 19 | **90.5%** |
| lookahead + inferred module latent | 19 | 19 | **100%** |

Two negative ablations locate the remaining problem.  Requiring at least three
observed atomic neighbors changes nothing, so the six errors are not weakly
attached sites.  Voting across overlapping parent proposals also fails because
correlated pose variants vote together (392/554, 70.8%).  Full child-frame
matching rejects positionally coincident orientation decoys in a focused test,
but does not change this frontier result.  The surviving ambiguity therefore
requires a larger *hierarchical* context or tree-search lookahead, not a larger
atomic section or a missing rotation check.

Requiring each lookahead site to participate in two exterior ports is also
counterproductive (13/15, 86.7%).  Greedily displaying all mutually compatible
top branches accepts four macro actions and 60 unique sites, but only 52 are
oracle sites (86.7%).  Parallel display must therefore preserve the four branch
identities for rollback; compatibility alone is not evidence that every branch
is correct.

The current pure-Python end-to-end benchmark fell from 218 seconds to 148
seconds after caching type expansions, sharing SO(3) registrations, and
inverting dense port scoring.  An aggressive beam that retained only the 138
maximum sparse-cover poses was faster (134 seconds) but selected a different,
77.4%-precision action; it is rejected.  Sparse cover score is not a valid
upper bound on the denser overlapping marking.

Depth-2 branch evaluation also leaves all 20 branches tied: every branch
supports a distinct second parent with 21 internal port matches.  A
species-resolved pair marking over the full learned level-3 radius (9.94 local
length units) likewise leaves all 20 tied at score 0.9984.  Applying that
nonlocal section as a hard per-site filter is harmful (15/17, 88.2%).  The two
oracle mismatches therefore remain geometrically supported through two macro
depths and across the complete bounded marking domain.  Choosing the particular
held-out model-set realization now requires either a learned global/phason
state, external boundary information, or accepting multiple valid branches;
more static local thresholds are not justified by these ablations.

The input point cloud does, however, admit a zero-residual low-rank module
reconstruction.  A gated latent marking infers the quadratic unit, integer
six-dimensional lifts, internal acceptance window, and chemical shells from
the 507 known positions.  It activates only below a (10^{-5}) reconstruction
residual.  Applied after GCTS lookahead, it removes exactly the two false sites
and retains 19/19 correct atoms.  This is the first safe recursive IQC action
and a clean causal use case for a nonlocal marking.  It is not yet a generic
solution for arbitrary quasicrystals: the current module-family search is the
icosahedral quadratic control already implemented in
`materials_gcts_icosahedral_modelset.py`.

That learned model-set implementation is the current target baseline: it grows
507 atoms to 2,229 (4.40×) with 100% lift precision/recall, species accuracy,
and position accuracy.  Recursive GCTS must repeat its now-safe macro action to
match that result before the benchmark radius is increased toward million-atom
implicit representation.

`scripts/materials_gcts_dag_iterated_growth.py` remaps both hierarchy layers
after every accepted batch and backtracks through descending score strata when
the best stratum contains no new latent-valid sites.  Four measured waves add
70, 12, 1, and 14 atoms, all correct.  The state grows from the 867-atom
three-wave baseline to 964 atoms at 100% precision and 26.54% cumulative hidden
recall.  Waves 3 and 4 require three and twelve score strata respectively,
showing that rollback is operational.  This remains well below the 95% gate
and is not exponential growth yet.

An eight-wave run adds 103/103 correct atoms and reaches 970 total atoms at
100% precision, but hidden recall is only 26.89%.  The wave sizes are
70, 12, 1, 14, 1, 1, 2, and 2 atoms, and the run takes 426 seconds.  This is a
clear failure of the exponential-growth benchmark: after the first macro wave,
the frontier proposal mechanism degenerates into nearly atomic progress even
though the latent validator remains exact.

## Latent-directed rigid-parent ablation

`scripts/materials_gcts_latent_macro_growth.py` places complete learned level-3
DAG parents at centers proposed by the inferred internal-space marking.  A
ranked four-section marking and the unpruned fourteen-section atlas produce the
same result: 777 exact legal placements, of which a greedy overlapping cover
selects 90 and adds 210 atoms at 100% precision.  The largest marginal gain is
only five atoms.  This rules out overaggressive marking as the cause of the
plateau.  Rigid translated/rotated parents are primarily reconstruction
patches; by themselves they do not encode the quasicrystal inflation law.

## Recursive marked cluster rule

`scripts/materials_gcts_recursive_marked_growth.py` adds a distinct parametric
node to the transform hierarchy: `patch(R) -> patch(unit * R)`.  Its support is
not a copied finite atom list.  The learned six-dimensional acceptance section
is the GCTS marking that decides which module sites and chemical shells belong
to the enlarged parent.  From the same 507-atom input, the learner recovers
`unit = 1.618033988749895` with zero residual.  The first marked parent at
radius 14.562 contains 1,969 atoms; extending the requested envelope to radius
15 contains 2,229 atoms.  One recursive rewrite generates all 1,722 new atoms.
Held-out oracle evaluation reports 100% position and species precision and
recall, giving 1,722x action compression relative to atomwise placement.

This passes the exponential-style gate for the quadratic icosahedral control,
and it makes the role of the marking causal: removing the internal acceptance
section leaves the dense six-dimensional projection ill-defined.  It is not a
generic quasicrystal result.  The current module-family detector is specialized
to this control and must remain gated by its reconstruction residual.

## Generic translated-parent connection marking

`scripts/materials_gcts_recursive_connections.py` now tests a less specialized
route to the same hierarchy.  Every atom is the centre of a bounded local
colored cluster.  A cluster-of-clusters action connects a parent cluster to a
source cluster and proposes

`parent + scale * (source - parent)`.

The learned GCTS marking is a finite table over the parent local type, source
local type, and binned separation.  Separation is divided by the known level
scale before the marking is reused, so the same connection state can recur at
the next inflation level.  Local types use only colored radial neighbor counts;
the rule is invariant under rigid motion and has no lattice coordinates,
physical potential, cut-and-project lift, or material-specific labels.

On the ideal icosahedral control, the complete translated-parent action family
covers every target site in both 507→1,969 and 1,969→8,603.  This establishes
that translated copies of higher-order parents can be a complete generator,
not merely the origin-centred subset measured by the earlier iterated-marking
test.  The marking is learned only on the first transition (1,558 observed
connection states, 171 accepted) and then frozen.  The 1,969 already-known
sites are removed before scoring continuation; the target is the 6,634 genuinely
new sites:

| held-out consensus | proposed sites | correct | precision | target coverage |
|---|---:|---:|---:|---:|
| at least 1 overlapping action | 55,990 | 6,454 | 11.5% | **97.3%** |
| at least 2 | 35,626 | 6,034 | 16.9% | **91.0%** |
| at least 4 | 15,726 | 3,934 | 25.0% | 59.3% |
| at least 8 | 3,358 | 1,732 | **51.6%** | 26.1% |
| at least 16 | 504 | 332 | 65.9% | 5.0% |

This result identifies two distinct jobs that had previously been conflated.
The finite connection marking transfers almost the entire next patch, while
overlap agreement ranks confidence among its sites.  A high threshold is a
safe forced-move policy; a low threshold supplies a broad candidate frontier
for tree search.  No operating point yet meets 95% precision and recall at
once, so this is a useful generic GCTS benchmark rather than a solved growth
algorithm.  The next step is to learn a bounded marking on the *consensus
neighborhood itself*—a second-order cluster type—then search only the residual
ambiguous frontier.

### Second-order consensus-neighborhood marking

`scripts/materials_gcts_consensus_neighborhood.py` now promotes the overlap
field itself into another cluster level.  A proposed site's bounded descriptor
contains its action multiplicity, agreement of predicted colors, diversity of
parent/source connection states, and radial counts of neighboring proposals.
Both a continuous logistic section and a finite binned likelihood section are
learned.  These remain rigid-motion invariant and contain no physical energy,
lattice direction, or held-out oracle coordinate.

To prevent the first transition from labelling its own proposals, five spatial
parent folds are used.  Each fold's connection table is learned on the other
four folds and applied only to the excluded parents.  Known sites are removed.
The resulting 3,832 out-of-fold continuation proposals contain 1,462 positives
and 2,370 genuine negative
examples.  The second-order marking is fitted there, frozen, and applied to
66,110 novel-site proposals on the 1,969→8,603 transition.

The atom-growth factor learned from the training transition is 3.8836.  It
predicts 7,647 total next-level sites, hence a budget of 5,678 *new* sites after
the 1,969 known sites are merged, without inspecting the 8,603-site target.  At
fixed multiples of that continuation budget, the second-order marking causally
improves multiplicity-only ranking:

| next-level site budget | selected second-order policy | second-order P / R | vote-only P / R |
|---:|---|---:|---:|
| 2,839 (0.5×) | continuous section | **70.87% / 30.33%** | 53.89% / 23.06% |
| 5,678 (1×) | equal-rank section ensemble | **48.47% / 41.48%** | 43.64% / 37.35% |
| 11,356 (2×) | finite binned section | **32.69% / 55.95%** | 29.48% / 50.47% |

This is the first leakage-controlled gain from an explicit cluster of
connection proposals rather than from raw overlap multiplicity.  It is not a
G1 pass.  Absolute score thresholds calibrated on 507→1,969 transfer poorly
because candidate density and class prevalence change sharply at the next
level.  The current recursively stable policy therefore ranks the atom budget
predicted by the learned growth factor.  The next marking must model that
density transformation explicitly or learn a higher-order sparse cover so an
absolute forced-move decision remains calibrated across levels.

### Frontier attachment and third-order marking

`scripts/materials_gcts_frontier_attachment.py` adds the accepted
configuration to the marking domain.  For each recursive proposal it records
bounded colored neighbor counts and nearest distances to already accepted
atoms, together with source-color and learned target-color connection votes.
The latter is retained as a separate hypothesis: using the learned
state-to-color mode directly is a negative result (40.7% held-out species
accuracy versus 56.0% for the source-carried color).  The higher-order marker
may use their agreement, but does not replace the better color rule.

The frontier marker is trained on the same 3,832 cross-fitted continuation
proposals and frozen.  On the 66,110 held-out novel-site candidates it produces
a sharply purer frontier than consensus alone:

| ranked frontier budget | correct | precision | novel recall |
|---:|---:|---:|---:|
| 250 | 238 | 95.2% | 3.59% |
| 500 | 488 | **97.6%** | 7.36% |
| 1,000 | 868 | 86.8% | 13.08% |
| 2,000 | 1,530 | 76.5% | 23.06% |

An explicit third level then forms a broad provisional covering (twice the
learned novel-site budget), treats its colored proposal neighborhood as the
new marking domain, and fits another bounded section.  It improves the full
5,678-site operating point from 48.5% precision / 41.5% recall to **53.3% /
45.6%**.  Its diagnostic top 250 sites are 250/250 correct, but there is no
unlabelled score gap at rank 250, so that number is not used as a policy.

The operational policy accepts only the current maximum-score symmetry
plateau, merges it into the known configuration, and recomputes both frontier
levels.  Eight frozen-policy waves add:

`10 → 2 → 120 → 36 → 24 → 8 → 4 → 4`

All 208 proposed sites are correct, for 100% precision and 3.14% novel recall.
The 120-site third wave is a verified macro action selected as a cluster of
proposal clusters, not 120 atomwise oracle decisions.  Later plateaus shrink,
so this is safe hierarchical progress rather than exponential continuation.

The first implementation re-ranked a fixed proposal family.  The current
regenerative search now recomputes local cluster types after every accepted
macro and evaluates only incremental connection pairs involving a new parent or
source.  Its radial envelope is also learned rather than read from the held-out
target: the finite-sample extent ratio is 1.6629 and gives a 24.010 continuation
radius.  Eight regenerated waves add:

`12 → 104 → 12 → 4 → 36 → 24 → 24 → 12`

They contain **228/228 correct novel sites** (3.44% recall).  More importantly,
the available frontier grows from 63,890 to 66,254 candidates while accepted
sites are removed.  New actions therefore outpace consumption; this is actual
continuation from newly created clusters, not replay of a precomputed list.
The plateau sizes still do not amplify monotonically, so the exponential gate
remains open.

Two calibration ablations remain negative.  Scaling a training-pure prefix by
the expected surface factor selects 3,828 sites at only 60.2% precision, while
an absolute 99%-training-precision score threshold transfers at about 17%
precision.  Minimum-separation pruning changes no result because the false
branches are locally valid, non-colliding alternatives.  Maximum-score plateau
iteration is the only currently verified self-calibrating forced-move policy.

## Next implementation target

Continue the exact plateau search with new recursive connection proposals after
each accepted macro, and learn a branch-level lookahead marking when the top
plateau ceases to be pure.  Learn the transformation of proposal density and
class prevalence between hierarchy levels, or replace dense pair proposals
with a learned sparse parent cover.  Generalize the parametric recursive-node
interface so crystals learn a
translation quotient, substitution quasicrystals learn an inflation or
superspace section, and amorphous controls decline the deterministic rule.  Add
held-out perturbations and non-icosahedral model sets so a module-specific
success cannot masquerade as generic GCTS.  The generic G1 gate remains 95%
hidden recall with exact species and position validation.

## Generic parametric dispatcher and million-atom curve

> **Scoreboard correction.** This section is the specialized algorithmic
> ceiling, not the final generic GCTS pass. The shared dispatcher selects among
> translation quotient, internal section, substitution product, and planar
> address encoders. Its exact growth is valuable evidence and a target for the
> generic cluster/port grammar, but `family_specific_backends_remain = true`
> now forces the common research gate to stay red. Only unseen recursive
> execution by one frozen cluster/port grammar can turn that gate green.

`scripts/materials_gcts_parametric_recursive.py` now exposes one discovery
contract over an unlabeled colored point cloud.  The local recursive hierarchy
is learned first and gates all later rules.  The NaCl control learns supports
of 7, 27, and 164 atoms, then discovers three composable species-preserving
translations directly from the finite cloud; removing its supplied periodic
cell does not change the generated 2x2x2 continuation.  The IQC learns supports
of 14, 49, and 270 atoms, registers its ten shortest-bond axes to a canonical
icosahedral frame, and activates the internal-section rule only at low lift
residual.  An arbitrary SO(3) rotation plus translation is inverted before
learning and restored after growth.  The amorphous control has supports
0, 0, and 0 and declines deterministic continuation.

The dispatcher also recognizes a second, non-icosahedral quasiperiodic family.
For the 729-atom three-dimensional Fibonacci-product control, it recovers three
orthogonal shortest-bond axes, two gap clusters, the minimum-description
substitution `A -> AB, B -> A`, and an eight-entry species decoration marking.
Its recursive supports are 4, 17, and 81 atoms.  One held-out rewrite produces
3,375 exact positions and species.  A rotated and translated input produces the
same transformed continuation, including when axis reversal selects the
conjugate word presentation.

The internal-section enumerator no longer scans a six-dimensional coefficient
box.  It writes each Cartesian coordinate as `a + b*unit`, filters the physical
and conjugate internal intervals, enforces the three lift parity constraints,
and combines only surviving coordinate sections.  The learned IQC rule's
second inflation contains 8,603 atoms and matches an independent hidden-window
and species certificate.  `scripts/materials_gcts_recursive_scaling_benchmark.py`
measures the complete implicit curves:

| action | NaCl atoms | icosahedral IQC atoms | Fibonacci-product atoms |
|---:|---:|---:|---:|
| 0 | 216 | 507 | 729 |
| 1 | 1,728 | 1,969 | 3,375 |
| 2 | 13,824 | 8,603 | 13,824 |
| 3 | 110,592 | 37,073 | 59,319 |
| 4 | 884,736 | 155,097 | 250,047 |
| 5 | 7,077,888 | 657,057 | 1,061,208 |
| 6 | — | 2,791,097 | — |

On the development machine, count-only IQC enumeration through action 6 takes
2.72 seconds for the last level and about 39 MB peak process memory.  A separate
materializing run produced 1,007,649 atoms at radius 115 in 2.32 seconds, with
about 400 MB peak memory.  These are algorithm/runtime benchmarks, not MD
equivalence: no dynamics, defects, stresses, or thermodynamics are inferred.

`scripts/materials_gcts_million_emission_benchmark.py` replaces that earlier
ad-hoc materialization note with a reproducible explicit certificate. The
learned 216-atom NaCl quotient streams 7,077,888 species-labelled positions in
five macro actions (16.2 seconds in the current recorded Python run). The
507-atom IQC first learns the same three-component GCTS mark used by local
port growth, then promotes it to a rank-six address macro and streams 2,791,097
positions in six actions (9.7 seconds). The learned Fibonacci-product
substitution streams 1,061,208 sites in five actions (2.6 seconds).
Neither output cloud is retained. Instead, an order-independent 256-bit sum of
per-site cryptographic hashes is compared with a structurally independent
oracle: direct rocksalt half-grid parity for NaCl, sealed unit/window/shell
constants for the IQC, and an independently generated hidden substitution
word for the Fibonacci product. All three digests and species counts match
exactly. The observed geometric means are 8.000, 4.202, and 4.292 sites per
recursive action. This closes the **explicit million-site emission** benchmark
for one crystal and two quasicrystal controls. IQC emission performs no
coordinate lifting, model refit, target
lookup, or physical-potential call; a regression makes coordinate lifting
raise during macro inference. This gives GCTS a concrete multiscale role:
local port search validates and propagates the marking through 66,935 exact
sites, then the same mark becomes the fast clusters-of-clusters address
production. Writing coordinates remains O(N), and the stricter requirement
that crystal, substitution, and IQC use one production kind remains red.

The inference artifacts are now physically separated from their trainers.
The local `PortCoverGraph` retains the 789 promoted typed-distance ports,
frontier width, origin, and carried mark, but drops all 13,111 fitting-only
port pairs and the global section. The promoted million-site artifact is
smaller still: `MarkedAddressMacro` contains only the learned algebraic unit,
window radius, species thresholds, origin, and rigid frame. It contains no
port atlas, seed marks, target sites, or fitting model. Structural regressions
enforce both exclusions, so the cost comparison no longer counts discarded
training evidence as required inference state.

## Perturbation gate

`scripts/materials_gcts_noise_robustness_benchmark.py` adds independent Gaussian
coordinate noise before discovery and removes the crystal's periodic metadata.
At sigma 0.005 in the control length units, all three deterministic families
retain a rule: NaCl learns supports 7, 27, 137 and grows to 1,728 atoms; the
icosahedral control learns 14, 49, 270 and grows to 1,969; the Fibonacci product
learns 4, 11, 51 and grows to 3,375.  Four independently seeded 507-atom
hard-core amorphous controls produce zero deterministic false positives.

At sigma 0.01, the IQC and Fibonacci controls lose their level-3 recurring
support and the dispatcher returns `none`.  This is the intended conservative
failure mode.  The noise path currently recovers and snaps an underlying ideal
topology.  It does not extrapolate phonons, thermal displacement correlations,
defects, stress fields, or time evolution; those require a residual/displacement
field model layered on top of the recursive structural rule.

## Multi-species crystal and local-defect suite

`scripts/materials_gcts_real_crystal_benchmark.py` applies the same unlabeled,
cell-free discovery path to six crystallographic prototypes: NiAl B2, Cu3Au
L1_2, GaAs zinc blende, NaCl rock salt, SrTiO3 perovskite, and the 168-atom
Cd6Yb 1/1 approximant cell.  The first five inputs contain 128--320 atoms.  The
Cd6Yb case uses an observed 2x2x2 crop (1,344 atoms), because one isolated unit
cell contains no repeated translation from which a cell-free learner could
infer its quotient.  All six learn three translations and a consensus colored
motif, then produce the exact held-out 2x2x2 continuation: 8x as many atoms,
with exact position and species sets.

The quotient learner scores candidate translation bases by how completely a
small colored motif explains the observed finite box.  This matters when the
input contains a non-repeating residual.  In
`scripts/materials_gcts_defect_locality_benchmark.py`, a 3x3x3 NaCl crop is
modified by one vacancy, one Na-to-K substitution, or one Xe interstitial.  A
single quotient action produces 1,727, 1,728, and 1,729 atoms respectively,
matching the clean 6x6x6 continuation with exactly the original one-off defect.
The defect is not multiplied into the seven synthesized blocks.

This is the first operational separation between a learned cluster-of-clusters
and its residual field: consensus structure receives the recursive rewrite;
unexplained local state is carried once.  It is still a static ideal-geometry
test.  The next gate is to learn smooth displacement/strain residuals and to
test defects near a growth frontier; the current code does not predict defect
energetics, kinetics, or finite-temperature dynamics.

## Explicit recursive application and marking ablation

The earlier scaling table used exact count recurrences, but the one-step IQC
and substitution materializers did not retain the enlarged parent envelope.
Calling them twice therefore regenerated the first child.  This is now an
explicit regression gate rather than an implicit projection.
`apply_rule_actions` keeps the original training cloud as the marking witness
and advances the parent state by an arbitrary number of recursive actions.
`scripts/materials_gcts_explicit_recursive_benchmark.py` materializes two
levels and independently checks every colored site:

| family | input | action 1 | action 2 | atomwise placements / macro action |
|---|---:|---:|---:|---:|
| NaCl translation quotient | 216 | 1,728 | 13,824 | 6,804.0 |
| icosahedral internal section | 507 | 1,969 | 8,603 | 4,048.0 |
| Fibonacci-product substitution | 729 | 3,375 | 13,824 | 6,547.5 |

Thus the same learned node now acts on a cluster, then on the resulting
cluster-of-clusters.  These ratios measure discrete placement decisions, not
wall-clock speedups over MD.

`scripts/materials_gcts_recursive_marking_ablation.py` makes the role of the
marking causal.  For the second IQC inflation, the learned integer module,
physical-radius bound, and lift-parity connections admit 6,171,443 candidate
sites if its bounded internal section is removed.  The section retains 8,603,
rejecting 99.86% of algebraically connected but incompatible candidates.  For
the Fibonacci product, there are 392 bounded two-symbol child grammars before
observed parent sections are enforced and six remain consistent; the learned
minimum-description marking selects `A -> AB, B -> A`.  For NaCl, quotient
geometry without a species-preserving marking leaves `2^56` possible binary
decorations across the seven new images, while the colored connection marking
selects one.

The ablation deliberately removes only the section/connection marking while
retaining the learned geometry.  It therefore measures GCTS information rather
than comparing against a completely uninformed random generator.

## Markings on non-ideal parent geometry

`scripts/materials_gcts_hierarchical_residual.py` adds a synthetic but fully
held-out displacement benchmark.  Its input is a 1,024-atom NiAl B2 point cloud
with no cell or axes.  The atomic coordinates contain a bounded displacement
decoration generated at three nested binary parent levels.  The learner first
recovers a short same-species translation frame and the two-atom colored
quotient.  It then fits seven possible octant sections at each observed level
and tests whether the section vectors themselves follow a low-residual scalar
recurrence.  This is a marking on a cluster-of-clusters, rather than another
atom type or a physical interatomic potential.

The hidden recurrence ratio is 0.58; the learner obtains
0.5799999999999651.  Both the coordinate fit and the between-level recurrence
have relative error below `6e-13`.  Extrapolating the next two parent markings
materializes 1,024 -> 8,192 -> 65,536 atoms with exact colored position sets,
or 32,256 atomwise placements per macro action.  A flat ablation copies the
observed 8x8x8 displacement block but omits its new parent section.  It retains
the chemical quotient while missing held-out coordinates by 0.00620 angstrom
RMS; the marked rule is accurate to `5e-14` angstrom RMS.  A rotated and
translated input gives the correspondingly transformed output.

An IID displacement field on the identical B2 geometry is a negative control.
It is rejected because either the finite hierarchy fit or its between-level
recurrence exceeds the 10% relative-error gate.  Thus the engine does not call
every coordinate residual a recursively growable marking.

This control establishes the interface and causal advantage, not a claim about
phonons or real strain fields.  Its octant recurrence is deliberately known to
exist, the input is dyadic, and there is no energetic relaxation.  The next
tests must mix a recurrent displacement marking with isolated frontier defects
and replace the planted recurrence with modulations measured in real material
configurations.

## Recurrent parent field with local frontier defects

`scripts/materials_gcts_frontier_defect_benchmark.py` combines the recursive
displacement marking with sparse residual handling.  A vacancy, Na-to-K-style
substitution label, or interstitial is placed on the frontier of the observed
8x8x8 B2 parent.  The structural learner excludes rare chemical labels while
fitting the quotient and parent sections, reconstructs the expected observed
parent, and records only its sparse set difference as additions or removals.
Those residual operations are carried once after every structural rewrite.

After two actions the three cases contain 65,535, 65,536, and 65,537 atoms.
Their exact held-out position/species sets contain one vacancy, one
substitution, and one interstitial respectively.  Copying the complete
observed parent at each action would instead create 64 instances.  Thus the
recursive marking applies to the consensus cluster-of-clusters while the
nonrecurring state remains local, including when it occurs at the attachment
frontier.

This test exposed a frame-identifiability issue: averaging local translation
vectors lets a missing edge atom perturb the global basis.  The learner now
jointly fits the translation frame, motif, and parent sections.  Constant and
single-bit (affine) octant modes are assigned to the quotient frame; only
pairwise and triple octant interactions are allowed in the GCTS marking.  This
gauge makes the decomposition exact with sparse missing samples and prevents a
defect from leaking into every generated coordinate.

The defect policy is intentionally conservative.  Residual additions and
removals must total at most 2% of the observed cloud, and no new defect is
predicted.  Energetic defect propagation, dislocation motion, and relaxation
remain outside the present static continuation benchmark.

## Experimental dodecagonal approximant from COD

`scripts/materials_gcts_cod_approximant_benchmark.py` vendors the measured
coordinates and symmetry operations of Crystallography Open Database entry
[1521830](https://www.crystallography.net/cod/1521830.html).  The structure is
the periodic Ta-V-Te approximant reported alongside a dodecagonal
quasicrystalline telluride.  Its P -4 21 m cell has 314 symmetry-expanded
sites.  Shared, fractionally occupied Ta/V positions are retained as a
virtual-crystal `Ta/V` point color rather than converted to an invented random
occupational realization.

From that one experimental cell, the generic bounded hierarchy learns
recurring supports of 11, 39, and 139 atoms.  Recurring clusters cover 96.82%,
99.36%, and 99.36% of the measured sites, with marking confidence 0.748,
0.842, and 0.810.  Randomly permuting the same chemical-color multiset changes
the supports to 4, 37, and 138, establishing that the first hierarchy in
particular uses measured chemical decoration rather than geometry alone.

The experimental CIF explicitly supplies a periodic cell, so the classifier
calls the resulting top parent a `periodic crystalline approximant`; it does
not infer “quasicrystal” from the publication title or chemical family.  Cell
parent actions give the exact count curve 314 -> 2,512 -> 20,096 -> 160,768 ->
1,286,144.  Two explicit actions preserve every measured coordinate and
virtual-crystal color, corresponding to 9,891 atomwise additions per macro
action.

This is the first externally sourced approximant benchmark, but it is not a
true aperiodic-coordinate dataset.  Its million-site continuation ultimately
uses the experimental periodic boundary condition.  The internal 139-atom
GCTS hierarchy makes the cell interpretable as clusters of clusters; the
translation of that complete cell is still the easy crystalline part.  A true
quasicrystal test requires an aperiodic diffraction/superspace refinement or a
large experimentally reconstructed patch with a held-out region.

## Experimental aperiodic Sc-Zn hierarchy

`scripts/materials_gcts_experimental_sczn_benchmark.py` downloads the
supplementary real-space model from the Sc-Zn icosahedral-quasicrystal
refinement and verifies its pinned SHA-256 before parsing it.  The P1 model has
41,981 atom rows and 37,531 merged point sites; coincident Sc/Zn occupational
alternatives remain the virtual color `Sc/Zn`.  This is a genuine finite
aperiodic model rather than a periodically repeated approximant cell.

Atom-centred clustering is the wrong abstraction for this input: the refined
Tsai clusters are centred in voids.  The new learner therefore ranks chemical
colors by rarity and searches for recurrent antipodal shells.  It is not given
the element name, cluster centres, or paper's cluster labels.  It selects Sc
and recovers 173 complete twelve-site shells with learned mean radius 4.9149
angstrom.  Their median 7.8-angstrom decoration contains 156 measured point
sites.  The cluster-centre graph independently has two dominant learned links,
12.0 and 13.8 angstrom.

The centre graph supplies a real clusters-of-clusters benchmark.  A bounded
radial section records counts on the two connection shells; successive levels
add their learned inflated copies.  Quantizing counts in bins of four makes the
section insensitive to the cut boundary of the finite experimental model.
Three recurring levels have largest supports 13, 38, and 98 fundamental
clusters and cover 98.84%, 97.11%, and 74.57% of detected centres.  Their next-
shell boundary markings have confidences 0.573, 0.470, and 0.481.  Thus this is
an actual hierarchy over void-centred atomic clusters, not a relabeling of
individual atoms.

A blind scale-and-origin scan learns 1.618 as the best inflation proposal,
within `3.4e-5` of the golden ratio.  One parent proposal accounts for ten
accepted fundamental-cluster placements, or 1,560 decorated atom instances,
instead of ten separate cluster decisions.  This is the first measured
supercluster action in the suite.

The unmarked proposal by itself is intentionally weak: its spatially held-out
precision is only 3/18.  A bounded GCTS section now describes the measured
7.8-angstrom atomic decoration around a `(parent centre, source centre)` pair.
It uses intrinsic radial bands and projections onto the pair axis, so a rigid
rotation and translation leave it unchanged.  A radial/axial histogram and an
independent set of even angular moments each choose their three-neighbour
threshold using training leave-one-out predictions only.  Requiring both
sections to accept gives 3/3 on the original small held-out split.  Pair
distance alone gives only 3/8; one histogram section gives 3/5.  Removing the
Sc/Zn colors does not change this split, so this gain is properly attributed to
the bounded geometric marking rather than chemistry.

`scripts/materials_gcts_section_marking.py` now contains the material-generic
algorithm used by the stronger replication.  Its inputs are an arbitrary
colored point cloud, independently learned centers, and proposed
`(parent, source)` pairs.  It contains no element names, lattice coordinates,
or quasicrystal labels.  Both finite descriptors are exactly invariant under a
common rigid motion.  Settings are selected by cross-validation that holds out
complete parent groups, preventing proposals around one parent from leaking
across the fit/validation boundary.  A periodic B2-like positive control, in
which every quotient translation is legal, correctly reduces to an
always-accept section instead of inventing false restrictions.

`scripts/materials_gcts_multi_origin_marking_benchmark.py` applies that generic
API to the measured model.  It excludes the inflation origin's trivial fixed
point, trains on 83 complete parent centres, and holds out 90 different parent
centres.  The split is a 16-angstrom spatial checkerboard of parent coordinates
and never reads a target label.
There are 2,261 training candidates and 2,441 held-out candidates.  Only 218
held-out proposals are real continuations, so accepting everything has 8.93%
precision and creates 2,223 false search branches.

The fully automatic grouped fit chooses `k=3, threshold=0.35` for the histogram
and `k=7, threshold=0.35` for the moment section.  Their conjunction accepts
159 placements, 120 of which are correct: 75.47% precision and 55.05% recall.
False branches fall from 2,223 to 39, a 57-fold reduction, and the verified
placements represent 18,720 decorated atom instances.  A separately reported
precision-first operating point freezes the earlier `k=3` thresholds 0.65 and
0.85.  It retains 84.09% precision and 33.94% recall, with 14 false branches—a
158.8-fold reduction.  This establishes a causal role for GCTS marking: the
inflation rule proposes geometry, while the bounded section controls the
precision/recall and branching of the ensuing tree search.

This still does **not** justify unrestricted experimental growth.  Recall is
deliberately low, the finite model cannot certify iterations outside its
boundary, and 14 false branches still require overlap checks or backtracking.
The remaining gates are a complete multi-parent cover of the next ideal level
and the same frozen marking on a second experimental reconstruction.

## Frozen marking reused across ideal-IQC levels

`scripts/materials_gcts_ideal_iqc_iterated_marking.py` exercises the new generic
API across successive scales instead of randomly splitting one patch.  It fits
only the 507 -> 1,969 transition, freezes the marker, then presents every
nontrivial origin-centred inflation candidate from the independently generated
1,969 -> 8,603 transition.  No label from the second transition is used during
training or setting selection.

The first transition has 222 valid mapped actions.  The next has 944, a
4.252-fold increase close to the volumetric inflation rate.  An unmarked search
would branch on all 1,968 candidates at 47.97% precision and retain 1,024 false
branches.  The high-recall histogram section retains 612 correct actions out of
1,052: 58.17% precision, 64.83% recall, and only 440 false branches.  Thus the
number of correct actions captured by the frozen marker grows 222 -> 612, a
2.757-fold recursive action factor.  The conjunctive section is more
conservative: 252/392 correct, 64.29% precision, and 140 false branches, a
7.31-fold reduction from the unmarked search.

This is the first cross-level, frozen-marking certificate.  It proves that a
bounded GCTS section learned at one inflation level can remain predictive at
the next and can carry an exponentially increasing subset of correct actions.
It does not yet generate all 8,603 atoms: the test classifies the subset reached
by origin-centred inflation, while the remaining sites require translated
parent actions or a complete substitution cover.

## Current crystal/quasicrystal scaling gates

### Common two-level exponential-action protocol

`scripts/materials_gcts_recursive_program.py` now gives the planar atlas and
the three 3D recursive learners one family-blind contract. It first uses a
rotation-invariant covariance screen plus exact seed replay to recognize an
intrinsically planar union; otherwise it calls the existing structure-blind
3D dispatcher. No crystal, quasicrystal, dimensionality, cell, or held-out
label is passed to the selector.

`scripts/materials_gcts_common_recursive_benchmark.py` applies the same gate
to every admitted program: exactly materialize two independently generated
unseen levels, then—and only then—allow a symbolic count to one million. A
flat action means placing one learned primitive cluster; a recursive action
means promoting one cluster-of-clusters program level.

| learned from positions + species | explicit certificate | minimum sites/action factor | first symbolic ≥1m | flat cluster actions / recursive actions | compression | marking ablation effect |
|---|---:|---:|---:|---:|---:|---:|
| NaCl translation quotient | 216 → 1,728 → 13,824 exact | 8.000× | action 5: 7,077,888 | 884,709 / 5 | 176,942× | rejects all but one colored quotient decoration |
| icosahedral internal section | 507 → 1,969 → 8,603 exact | 3.884× | action 6: 2,791,097 | 199,328 / 6 | 33,221× | rejects 99.86% of algebraic lift candidates |
| Fibonacci-product substitution | 729 → 3,375 → 13,824 exact | 4.096× | action 5: 1,061,208 | 265,120 / 5 | 53,024× | rejects 98.47% of bounded rewrite grammars |
| rotated 30° hBN pose/address macro | 746 → 2,954 → 11,696 exact | 4.000× | action 5: 1,048,576 | 261,958 / 5 | 52,392× | pose ablation loses 50% recall |

The common pass criteria are deliberately stronger than a million-site count:
two exact unseen levels, minimum multiplicative factor above 3, at most six
recursive actions to one million represented atoms, at least 10,000× fewer
program actions than flat primitive-cluster placement, a causal marking
ablation, and rejection of the amorphous negative control. Explicit coordinate
emission remains linear in atom count. The exponential result is compression
of represented structure per recursive action, not a claim of sublinear MD or
free materialization.

The geometric evidence extractors are still specialized (translation
residues, quadratic internal section, gap substitution, planar address atlas).
The finite recursive executor is no longer entirely specialized: the typed
transform/section compiler described below handles translation, substitution,
planar pose/address graphs, and a parametric continuous internal-section
generator through one production contract.

### First shared typed transform/section compiler

`scripts/materials_gcts_typed_productions.py` compiles discovered geometric
evidence into one finite grammar. Each parent type has transformed child
references at local addresses plus bounded section marks describing which
faces of the parent neighborhood they contact. These marks are connection
labels, not physical potentials. The executor contains no crystal-versus-
quasicrystal branch: it repeatedly applies the same type-incidence rewrite.

| point-set input | induced graph | exact count certificate | symbolic ≥1m |
|---|---:|---:|---:|
| 216-atom NaCl | 1 type, 1 production, 8 child references | 216 → 1,728 → 13,824 | action 5: 7,077,888 |
| 507-atom ideal IQC | 1 parametric production, rank-6 address domain, learned 3D section | 507 → 1,969 → 8,603 exact | action 6: 2,791,097 |
| 729-atom Fibonacci product | 8 types, 8 productions, 27 child references | 729 → 3,375 → 13,824 | action 5: 1,061,208 |
| 746-atom rotated 30° hBN | 2 pose types, 2 productions, 8 child references | exact circular crops 746 → 2,954 → 11,696; address envelopes 1,024 → 4,096 → 16,384 | action 5: 1,048,576 |

`scripts/materials_gcts_typed_production_benchmark.py` verifies that all four
graphs are unchanged by a tested proper rotation and translation, agree with
two levels of explicit atom geometry, reach one million through the same
counter rewrite, and reject the amorphous control. Planar materialization is a
circular crop of a square recursive address envelope, so both counts are
reported rather than conflated. The compiler never
reads the discovered rule's family string; it selects an adapter from which
structural evidence fields are actually present. Finite productions use one
type-incidence counter. The IQC production is necessarily parametric: it
enumerates integer rank-6 addresses in the physical envelope and accepts them
with the learned bounded 3D internal section. They share a production contract,
not one finite execution algorithm. This is a real common recursive layer, but
not yet a common geometric learner: translation residues, gap words, planar
poses, and algebraic lifts are still extracted by different front ends.

This extension also found a coordinate-frame defect in the planar selector:
its growth envelope had been centred at the ambient origin. The generic
recursive entry point now infers the observation centre from the finite sample,
so a translated and rotated input produces the same typed graph.

### Family-blind hypothesis competition

The earlier selector still tried recognizers in a hand-written order and
returned after the first successful family. That control flow has now been
removed. `discover_recursive_program_candidates` attempts the planar,
translation, product-substitution, and internal-section hypotheses without a
phase-category guard. Every admitted proposal reports normalized seed
residual, description entries, exact seed replay, recursive hierarchy support,
seed mismatch, and a common fit-plus-description score. Selection is the
minimum score and is invariant to proposal order.

`scripts/materials_gcts_model_selection_benchmark.py` provides a nontrivial
competition rather than four one-candidate demonstrations. The Fibonacci
product admits both its exact substitution grammar and an approximate finite
translation quotient. That quotient reproduces only 194 of 729 observed sites
exactly and is penalized for its seed mismatch. The common score selects
substitution at 0.019204 versus 1.560741 for the quotient, a margin of
1.541536. NaCl selects its quotient,
the ideal IQC its internal section, and rotated 30-degree hBN its planar atlas.
The amorphous control admits zero proposals. No crystal, quasicrystal, planar,
or amorphous label is provided to proposal generation or selection.

### Unified selector robustness gate

`scripts/materials_gcts_selection_robustness.py` perturbs the inputs before the
family-blind proposal stage and evaluates the selected program against a clean,
larger scaffold. This tests the integrated selector rather than invoking a
known family-specific learner directly.

| observed seed | selected production | clean grown P / R / species | registered RMS |
|---|---|---:|---:|
| NaCl + 0.005 A Gaussian noise | translation quotient | 100% / 100% / 100% | 0.0163 A |
| ideal IQC + 0.005 A Gaussian noise | internal section | 100% / 100% / 100% | 0.0244 A |
| Fibonacci product + 0.005 A Gaussian noise | substitution | 100% / 100% / 100% | 0.0108 A |
| 30-degree hBN + 0.006 A noise + 3.5% vacancies | planar pose/address | 100% / 99.20% / 100% | 0.0149 A |

A single NaCl chemical substitution retains the quotient hypothesis but is
correctly marked as an inexact seed replay. A 1%-vacancy noisy IQC initially
exposed a frame-origin failure: the arithmetic centroid moves off the
algebraic module when atoms are missing. The learner now estimates the
inversion centre from the densest cluster of antipodal-pair midpoints. With no
oracle centre or hidden lift, it selects the internal section in 1.74 seconds
and reconstructs all 1,969 clean first-level sites at 100% position/species
precision and recall. A bounded lift-complexity preflight still prevents an
invalid frame from entering a large coefficient box. Two independently seeded
amorphous controls admit zero proposals. More severe and nonuniform 3D damage
remains open.

### Finite-window and minimum-description stability

`scripts/materials_gcts_finite_window_benchmark.py` changes the observed
window before discovery. It covers cubic crystal boxes, spherical IQC crops,
Cartesian substitution products, and circular bilayer disks. For every input,
the family-blind selector is rerun, its learned parameter signature is compared
across sizes, and one clean continuation beyond the observed window is checked
by exact position/species set.

| family | observed atom range | windows | stable learned parameters | next window |
|---|---:|---:|---|---|
| NaCl quotient | 64–512 | 3 | 8-atom motif; 5.64 A orthogonal translation Gram matrix | exact |
| ideal IQC section | 345–919 | 3 | unit phi; window 1.5; shell fractions 0.5 / 0.75 | exact |
| Fibonacci substitution | 216–1,728 | 3 | `A -> AB`, `B -> A`; same eight decorations | exact |
| twisted hBN atlas | 470–1,130 | 3 | one motif class, two poses, same translation Gram matrices | exact |

The test exposed a periodic overfit: the 512-atom NaCl window initially chose
a perfectly fitting 64-atom 2x supercell motif. The old tie-breaker favored
larger determinant. It now minimizes quotient description length after fit
quality and recovers the primitive 8-atom motif at all three sizes. Parameter
stability is therefore a separate gate from exact growth: a redundant
supercell can continue exactly while failing to learn the smallest recurring
cluster-of-clusters rule.

### End-to-end cost and count semantics

`scripts/materials_gcts_end_to_end_cost.py` times discovery, exact two-level
coordinate emission, fast million-scale representation counting, and an exact
count audit separately. The recorded Python run is a reproducible algorithmic
baseline, not a comparison with a production MD code.

| system | learn | exact two-level output | fast >=1m count | exact audit | flat / recursive actions |
|---|---:|---:|---:|---:|---:|
| NaCl, 216 atoms | 0.337 s | 13,824 in 0.051 s | 7,077,888 exact in 20 us | arithmetic exact | 176,942x |
| ideal IQC, 507 atoms | 1.756 s | 8,603 in 0.264 s | 2,788,759 estimate in 106 us | 2,791,097 in 2.489 s | 33,221x |
| Fibonacci QC, 729 atoms | 2.482 s | 13,824 in 0.031 s | 1,061,208 exact in 73 us | arithmetic exact | 53,024x |
| twisted hBN, 746 atoms | 3.371 s | 11,696 in 0.214 s | 1,048,576 exact in 11 us | arithmetic exact | 52,392x |

The finite graphs have exact incidence counts. The IQC has an exact compact
radius-plus-section representation, but exact finite-window cardinality is not
constant-time: it enumerates accepted rank-6 sites. Its fast count instead
uses the learned physical-ball volume times internal-window volume divided by
the inferred rank-6 covolume. At action 6 it differs from exact enumeration by
0.0838%. Explicit coordinate output is linear for every family. Therefore the
current exponential claim is strictly about sites represented per recursive
program action and program-description compression. It is not yet evidence
that GCTS beats million-atom MD in wall time or reproduces dynamics.

### Matched-quality tree-search marking ablation

`scripts/materials_gcts_matched_search_ablation.py` holds the target,
candidate frontier, accepted-move count, and immediate conflict check fixed.
Each incompatible proposal produces one failed branch/backtrack. For an
unmarked uniformly shuffled frontier, expected inspections to obtain `k` of
`K` valid actions among `N` proposals are the exact negative-hypergeometric
order statistic `ceil(k(N+1)/(K+1))`. The marked search uses the measured
filtered frontier. This avoids comparing a high-recall unmarked run with a
lower-recall marked run.

| system / marking | matched correct moves | unmarked expected checks | marked checks | unmarked / marked false backtracks |
|---|---:|---:|---:|---:|
| NaCl compiled colored quotient | 1 | 36,028,797,018,963,968 | 1 | 36,028,797,018,963,967 / 0 |
| ideal IQC compiled internal section | 8,603 | 6,170,727 | 8,603 | 6,162,124 / 0 |
| Fibonacci compiled ordered substitution | 6 | 337 | 6 | 331 / 0 |
| frozen learned IQC local halo, unseen level | 252 | 526 | 392 | 274 / 140 |

The first three rows test the marking embedded in the learned recursive
production at full recall: proposal reductions are 3.60e16x, 717x, and 56.2x.
They prove that the sections are causal, but those sections are also part of
the compact generator. The fourth row is the stricter GCTS-learning result:
the local section is trained only on the 507 -> 1,969 transition and frozen on
1,969 -> 8,603. At the same 252 correct accepted moves it reduces proposal
checks by 1.34x and failed branches by 1.96x. It is useful but not yet a
dramatic universal tree-search win; increasing held-out recall without losing
this precision is the next marking objective.

| system | observed input | learned supports | recursive factor | million-site gate | strongest certificate |
| --- | ---: | --- | ---: | ---: | --- |
| NaCl crystal | 216 atoms | 7 -> 27 -> 164 | exactly 8x/action | action 5: 7,077,888 | exact position/species quotient |
| ideal icosahedral model set | 507 atoms | 14 -> 49 -> 270 | about 4.2x/action; frozen marked subset 2.757x | action 6: 2,791,097 | two explicit inflations, independent 6D acceptance test, and cross-level frozen marking |
| Fibonacci-product quasicrystal | 729 atoms | 4 -> 17 -> 81 | about 4.2x/action | action 5: 1,061,208 | recovered substitution grammar |
| experimental Sc-Zn IQC | 37,531 sites / 173 centres | 13 -> 38 -> 98 | learned phi proposal | not claimed | generic grouped fit: 75.47% precision / 55.05% recall; precision-first: 84.09% |
| amorphous control | 507 atoms | none beyond local | none | rejected | no deterministic macro rule |

The first three rows set the exponential-style action benchmark.  The
experimental row must match their multi-step certificate before its learned
phi action is allowed to project a million-site count.

## Geometry-bearing cluster-of-clusters gate

`scripts/materials_gcts_cover_grammar.py` closes one earlier accounting
loophole. A higher-level cluster no longer records only child counts and turns
the remainder into anonymous species counts. Each production now carries
rigid child poses, the parent-local atom identities shared by overlapping
children, coordinate-bearing gap terminals, and a full prototype replay. The
recursive executor expands lower-level productions and merges same-species
overlaps geometrically.

| finite training cloud | stored productions | exact recursive prototype replays | overlapping productions | minimum modal reuse |
| --- | ---: | ---: | ---: | ---: |
| NaCl, 216 atoms | 68 | 68 | 52 | 33.3% |
| ideal IQC, 507 atoms | 48 | 48 | 36 | 30.0% |
| hard-core amorphous null, 507 atoms | 0 | 0 | 0 | rejected |

This gate is intentionally **red**. Exact replay proves that the learned cover
is executable and that gaps retain geometry; it does not prove continuation.
One modal right-hand side does not yet explain 90% of occurrences. The next
step is to retain context-marked production alternatives, freeze them on an
inner window, and measure exact replay on unseen outer occurrences. Until that
passes, the million-site rows above remain certificates of the specialized
quotient/substitution/section/address backends—not of this generic grammar.

### Frozen alternative-selection gate

`scripts/materials_gcts_contextual_alternatives.py` now retains a finite set of
right-hand-side alternatives instead of silently discarding every non-modal
cover. It uses a deterministic two-training/one-held-out occurrence split and
freezes the rule table before scoring held-out occurrences.

| finite cloud | train / held-out occurrences | RHS alternatives | held-out RHS seen in train | parent-only modal | bounded halo / port mark |
| --- | ---: | ---: | ---: | ---: | ---: |
| NaCl | 438 / 210 | 70 | 100% | 90.0% | 90.0% |
| ideal IQC | 1,014 / 504 | 59 | 99.60% | 88.49% | 88.49% |

This is another intentional red gate. The finite vocabulary is adequate, but
the current halo is constant within each coarse parent type and the first
bounded child-port multiset adds no discriminating information. A GCTS marking
must use already-placed incoming connection/overlap ports—not atoms that the
candidate would create—and must beat both the parent-only modal rule and a
shuffled-port control. Because overlapping occurrences share atoms, this split
is diagnostic only; the acceptance benchmark will train inside one window and
test outside a guard band in larger NaCl and IQC windows.

`scripts/materials_gcts_guarded_spatial_split.py` establishes that stronger
test geometry on 13,824-site NaCl and 8,603-site IQC clouds. A fixed plane with
normal `(1,2,3)/sqrt(14)` separates training and held-out centres. At each
level the unused band is the sum of every lower-level body radius plus marking
width, and the outer boundary is eroded by the same amount. NaCl retains
785 / 785 level-three centres. IQC retains 532 / 532 level-two centres but no
level-three centres in the present 8,603-site patch. Thus three NaCl and two
IQC levels have disjoint raw-atom dependency domains; IQC level 3 remains an
explicit red gate requiring a larger patch. This fixture blocks random
overlapping-occurrence splits from becoming the acceptance result.

`scripts/materials_gcts_frozen_hierarchy.py` supplies the first train-only
encoder/transform split. A spatial index replaces the quadratic full distance
table for the 13,824/8,603-site clouds. The training half alone fixes nearest-
neighbor scale, species colors, rotation-invariant signature maps, the
promoted-color maps, and an unknown sentinel. Transforming the disjoint half
finds 100% of both NaCl and IQC signatures in the frozen dictionary at every
certified level, without regrouping or type renumbering.

That success exposed an arbitrary top-four promotion bottleneck: it retained
98.41%, 74.57%, and 24.48% of held-out NaCl centres, but only 17.94%, 15.39%,
and 33.95% of IQC centres. The encoder now selects the shortest frequency-
ordered vocabulary covering 95% of training centres, capped at 64 types. It
learns 4/6/16 promoted colors for NaCl and 51/30 for IQC. Without seeing the
held-out side, these cover 98.41%/96.81%/95.29% and 95.59%/95.68%,
respectively. The certified hierarchy-state transfer gate now
passes. Frozen production selection, incoming-port marking causality, and
actual continuation remain separate requirements.

### Causal inward-halo search ablation

`scripts/materials_gcts_incoming_port_ablation.py` prevents another possible
leak: the marking may see only the inward half of the bounded halo, standing
for atoms already grown toward the observation center. Held-out parent atoms
choose the correct answer for scoring, but never enter the ranking features.
At the deepest certified hierarchy levels (NaCl level 3, IQC level 2), the
train-selected vocabularies have one right-hand side per parent: 16/16 for
NaCl and 30/30 for IQC. Parent type therefore forces every move, and both modal
baselines have zero decomposition backtracks. Neither is a task on which a
marking can demonstrate causal value.

This negative gate is informative: when the stored parent geometry already
determines its cover decomposition, GCTS has nothing useful to choose. The
next matched-quality experiment must rank *neighboring macro placements at a
live frontier*, where several transformed clusters can genuinely compete and
incoming overlap/connection ports can exclude future conflicts.

That experiment now passes. `scripts/materials_gcts_frontier_search_ablation.py`
reuses the actual recursive IQC frontier rather than a hypothetical candidate
population. The marker is fit on the 507 -> 1,969 transition and frozen on
1,969 -> 8,603. Every arm receives the same 66,110 candidate points and stops
after finding the same 120 correct novel sites—the first pure maximum-score
macro of the existing regenerative search.

| ordering | proposal checks | immediate failed branches | precision at matched stop |
| --- | ---: | ---: | ---: |
| learned incoming GCTS marking | **120** | **0** | 100% |
| overlap-vote baseline | 232 | 112 | 51.72% |
| 30 equal-budget train-label-shuffled marker refits | median 4,608; best 404 | median 4,488 | 2.60% at median |

The learned marking cuts matched work by 1.93x versus overlap ordering and
38.40x versus the shuffle median, and beats every shuffled refit. Held-out
labels never enter fitting; shuffles preserve the proposal descriptors and
positive count while destroying their association. This is the first causal
GCTS result at the correct search interface. It does not make the exponential
gate pass: it certifies one 120-site forced macro, while sustained recursive
macro amplification and the third cumulatively guarded IQC hierarchy level
remain open.

### Order-independent spatial support hierarchy

The earlier `materials_gcts_spatial_macro_audit.py` records the colored 3D
coordinates of all 368 sites accepted exactly over 16 regenerative waves. Its
time-window analysis found 12 four-site candidates of one rigid type, but every
occurrence lay in one window. That candidate is still rejected: grouping
consecutive moves is not clusters-of-clusters evidence.

`materials_gcts_spatial_support_hierarchy.py` removes construction order from
the learner. Given only colored positions, disjoint domain labels, and bounded
radii, it makes an exact connected cover, then recursively covers the resulting
clusters with clusters. Its fast type key is the species-labelled pair-distance
multiset, so translation, rotation, reflection, point permutation, atom IDs,
lattice metadata, and phase labels do not enter. A production compiler must
still collision-resolve homometric keys by explicit congruence. Unpromoted
components remain explicit gap terminals, so each level still covers its entire
assigned domain.

`materials_gcts_spatial_sector_benchmark.py` applies this generic learner to
the accumulated exact IQC frontier. Eight octants are separated by a small
guard around their coordinate planes; 296 of 368 atoms remain. The result is:

| level | recurrent geometry types | recurrent occurrences | largest support | assigned-atom coverage |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 4 | 152 | 3 | 100% |
| 2 | 3 | 56 | 11 | 100% |
| 3 | 1 | 8 | 37 | 100% |

Support amplification is therefore `11/3 = 3.67x` and `37/11 = 3.36x`.
This passes the scoped three-level spatial hierarchy gate and gives a genuine
cluster-of-clusters certificate independent of move order. At the smaller
observed factor, nine additional symbolic promotions would exceed one million
represented sites. That is a projection, not yet a growth certificate:
unseen-level production replay, causal GCTS marking on the promoted ports, and
explicit output checks remain required.

The companion frozen test separates the eight domains by the sign of `x`.
`materials_gcts_frozen_spatial_grammar.py` fits its length unit, type
dictionaries, and production alternatives using only four negative-x domains
(148 atoms), then transforms the four positive-x domains (148 atoms) with those
objects frozen. The origin and guard width are predeclared from the known inner
configuration, rather than estimated from held-out frontier atoms.

The learned vocabularies contain `4 / 3 / 1` types and eight parent-to-child
productions. Held-out type occurrence coverage, atom coverage, and exact child
production agreement are all 100% at all three levels; there are no unseen
types or productions. This is dictionary and cover-grammar transfer across a
spatial half-space, not yet causal outward growth. Each parent has exactly one
RHS in this fixture, so a marking cannot improve decomposition; the separate
live-frontier ablation is where incoming GCTS marking has a causal choice.

### Large cumulative-guard color transfer

The prior 8,603-site IQC fixture has no level-three held-out center after the
correct cumulative dependency guard. `oracle_patch_fast` removes that sample
size bottleneck. It splits the six integer lift coordinates into two triples,
hashes one set in internal space, and joins only pairs that can enter the
bounded acceptance window. Tests require exact lift, position, and species-set
equality with the original `(2b+1)^6` enumerator. It produces a converged
155,097-site radius-61.69 fixture in about 2.5 seconds on the development host.

`materials_gcts_guarded_radial_hierarchy.py` fits only inside radius 35 and
uses cumulative dependency radii `2.054 / 5.855 / 12.885`. Held-out centers
start outside the training radius plus the corresponding dependency radius and
end inside the oracle boundary minus that radius. Therefore raw training and
held-out domains are disjoint by construction.

| level | training centers | held-out centers | exact-key coverage | bounded GCTS-color coverage |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 23,919 | 106,162 | 75.5% | 100% |
| 2 | 16,587 | 70,458 | 0% | 100% |
| 3 | 6,953 | 4,260 | 0% | 100% |

The bounded color is a coordination histogram plus an angular-incidence
histogram over a finite neighborhood. Nearest-color tolerances are derived
only from spacing among training colors: one training nearest-neighbor width
for levels 1–2 and two widths for level 3. No held-out label selects the
tolerance. A matched-density amorphous hard-core XYZ cloud is evaluated with
the same frozen encoder and reaches 42.6% / 97.2% / 24.1% coverage. The common
gate rejects it because both primitive and deepest hierarchical color transfer
must exceed 50%.

This is a positive finite-color transfer result with a meaningful negative
control. It is not yet a claim that the exact parent geometry or its outward
placement has transferred. Frozen production replay and causal frontier search
on the larger fixture remain red requirements before counting additional
symbolic promotions toward one million sites.

### Frozen exact-production recognition

`materials_gcts_guarded_production_atlas.py` retains every distinct sampled
species-labelled child-distance graph for each frozen parent color. The graph
has a distinguished center and all colored pair distances, so it tests full
relative geometry while remaining invariant to translation, rotation, and
atom ordering. No modal alternative is silently selected.

With 1,024 deterministic training and held-out parent samples per level:

| level | known held-out parent color | frozen RHS alternatives | maximum alternatives/color | exact held-out geometry |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 98.7% | 138 | 5 | 67.4% |
| 2 | 97.9% | 195 | 1 | 0% |
| 3 | 100% | 95 | 1 | 0% |

Thus bounded colors transfer but do not uniquely determine exact production
geometry. This is the expected place for GCTS marking to matter: the next rule
key must add a bounded graph of already-grown incoming ports and choose among
the compatible alternatives. Enlarging the color until it memorizes exact
held-out geometry would defeat the purpose. The execution gate also remains
red: recognizing a rigid distance graph is not equivalent to recovering a
proper SE(3) pose from frontier correspondences and emitting its children.

### Causal incoming-port ablation

The first marking test deliberately exposes only the already-grown side of a
spherical frontier. For a proposed center, its key is the bounded multiset of
species/type and quantized center distances for smaller-radius neighbors. The
outward child-distance graph is the label, never an input. Fitting uses only
the 28,211-atom inner configuration; held-out geometry is scoring-only.

At level 1, 285 of 2,048 deterministic held-out parents have a recurring frozen
incoming context. On this identical matched subset, the parent-color modal
baseline selects 31 exact outward productions, the learned marking selects
104, and 30 within-parent label-shuffled refits range from 26 to 44 (median
35.5). The learned marking therefore beats every equal-capacity shuffle in
this ablation. However, coverage is only 13.9%, and levels 2 and 3 have no
exactly recurring incoming contexts. The overall gate stays red until a
symmetry-quotiented port representation transfers at every recursive level and
drives proper-pose execution at matched output quality.

The recursive centre-connection benchmark previously received the ideal
inflation factor as an argument. It now infers that factor from the 507-atom
seed alone. Candidate ratios come from recurrent peaks in the pair-distance
spectrum plus generic positive roots of low-coefficient quadratic polynomials.
They are ranked by weighted spectral closure at both `s` and `s²`; requiring
two levels rejects a tempting one-level ratio near 1.902. The selected value is
`1.618033988749895`, with 51.24% and 55.85% closure. This inferred value—not a
hidden φ constant—now trains and applies the frozen recursive connection
marking. Target windows remain scoring-only.

That correction exposed a second leakage distinction. The older connection
table learned action labels from the complete 507 → 1,969 transition. The new
`materials_gcts_sealed_connection_benchmark.py` fits labels only for 93 inner
parents whose inferred-scale images remain inside the 507-atom seed. The
1,969-site state and 8,603-site target never enter fitting. On the outward
evaluation frontier the table proposes 3,404 distinct novel sites; 500 are
true, or 14.69% precision and 7.54% recall. Raising overlap-vote thresholds
does not produce a high-precision/high-recall operating point. Comparing a
candidate's partial radial coordination to complete training neighborhoods is
also anti-informative, confirming that the useful GCTS section is a graph of
incoming overlap ports, not a potential-like coordination score. This sealed
result is now the causal generic connection baseline and is intentionally red.

`materials_gcts_metric_port_atlas.py` makes the first useful generic
connection correction. The coarse 0.5-wide separation bin is replaced by the
motif-centre connection length itself. At application, the length is divided
by the current recursively inferred scale before matching. Thus a port class
is `(parent motif type, source motif type, normalized metric length)` and is
invariant to translation, arbitrary rotation, atom ordering, and inflation
level. No proposed coordinate or target occupancy enters the key.

Proposals leaving the observed seed are censored rather than mislabeled
negative. Across all 507 parents, 73 of 544 observable metric port classes
pass the train-only rule. Frozen on the 1,969-site frontier, they collapse to
860 distinct novel sites. All 860 are in the held-out target: 100% precision
and 12.96% recall. The matched coarse-state
ablation proposes 3,404 sites with 500 true (14.69% precision), so metric ports
give a 6.81x precision gain. This gate is green for exact transferred port
execution, while recursive full-growth recall remains red.

The executor inserts the 860 predicted species labels, producing a 2,829-site
partial cloud with 100% correctness. No oracle species or positions are
inserted. Admitting every train-supported single port then adds 13,020 sites
and every one is false. The regenerative gate rejects this branch: metric
ports transfer once, but do not reconstruct the higher-order overlap state.

The accepted port-action incidence graph is now promoted explicitly. Two sites
are in the same supercluster when a chain of accepted overlaps shares parent
or source motif centres. The 860-site exact patch has two large connected
components of 500 and 240 sites plus 32 smaller components, all available as
nonconflicting macros.
Their coordinate fingerprints are different isometry classes, and direct
inflation of either component produces no valid next sites. Accordingly this
is a real clusters-of-clusters representation and parallel-action compression,
but it is not mislabeled as recursive exponential growth.

### Regenerative port-pair section

The next GCTS section is learned one order higher: for every observed endpoint
inside the seed, it records unordered pairs of metric ports whose actions
co-support that endpoint. There are 271 train-supported port-pair classes.
Its 6.155 Å frontier width is derived from the longest train-supported port
after recursive normalization, rather than tuned on held-out performance.
Frozen on the unseen frontier, the pair section executes three nonempty waves:

| wave | sites inserted | correct | precision |
| ---: | ---: | ---: | ---: |
| 1 | 260 | 260 | 100% |
| 2 | 192 | 192 | 100% |
| 3 | 60 | 60 | 100% |

It adds 512 exact species-labelled sites, growing 1,969 → 2,481 without target
positions or oracle colors entering fitting or insertion, then stalls on wave
4. This is the first regenerative result from the generic cluster/port engine:
newly placed clusters create valid incoming contexts for later moves. It does
not pass the exponential gate because the sequence does not amplify. The next
promotion target is therefore a recurrent port-incidence component whose
support factor stays above one across unseen levels.

### Amplifying higher-order batch

A separate scale benchmark asks whether the higher-order action itself grows
with recursive level. The least-supported pair-section endpoint in the seed
has 11 underlying metric-port actions. Without inspecting held-out labels, the
frozen rule uses `ceil(11 / scale^level)` as its consensus threshold. This is
seven votes at the first unseen inflation and five at the second.

| unseen scale | state → target | pair-supported | accepted / true | precision | novel recall |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1,969 → 8,603 | 260 | 80 / 80 | 100% | 1.21% |
| 2 | 8,603 → 37,073 | 1,620 | 480 / 480 | 100% | 1.69% |

The exact accepted batch therefore amplifies by 6x across two unseen scales.
This is the first exponential-style clusters-of-clusters certificate for the
generic port grammar: the marking, scale, port vocabulary, pair vocabulary,
frontier width, and thresholds all come from the 507-atom seed. It does not
claim complete reconstruction or a generic million-site rollout; coverage is
still sparse, and those remain red gates.

The second reference window is generated by the exact meet-in-the-middle
oracle. Its 37,073-site count is unchanged for coefficient bounds 10 through
14; the smaller bound-8 crop (29,309 sites) is rejected as truncated.

### Cross-family transfer audit

The same experiment on the non-icosahedral 3-D Fibonacci-product control
identifies a different useful finite section: similarity about a recurrent
fixed anchor. Learned from the 729-site seed, it emits 2,090 / 2,090 and then
7,222 / 7,222 exact novel sites on the 3,375 → 13,824 and 13,824 → 59,319
transitions. This is substantially denser than the IQC pair batch.

The anchor section fails on the IQC, while the spherical port-pair section
fails on the Fibonacci product, so the grammar exposes both as finite marking
hypotheses. A shared seed-only selector chooses the anchor hypothesis only when
at least 25% of observed sites have an exact similarity image. IQC has 61/507
anchor support and selects port pairs; Fibonacci has 216/729 and selects the
anchor. The threshold, hypotheses, and tie-break are frozen before held-out
scoring, and no phase label enters selection. Both selected markings pass two
unseen scales, turning this cross-family selection gate green.

The competition also includes the translation-quotient hypothesis. On the
216-site NaCl cloud it is selected from colored point geometry and emits the
exact 1,728- and 13,824-site continuations. Crystal, icosahedral, and
substitution-quasiperiodic systems therefore share one hypothesis-selection
interface and all pass two unseen levels. The following geometry VM removes
the family dispatch from their coordinate/species execution.

### Generic colored-point geometry VM

The three selected hypotheses now compile to one declarative execution
contract. A `translation_cover`, `anchor_similarity`, or `overlap_section`
instruction consumes a colored point cloud and emits a set of new
species-labelled Cartesian sites. State merging, deduplication, and scoring no
longer dispatch on a material family.

| selected instruction | unseen level 1 | unseen level 2 | position/species precision |
| --- | ---: | ---: | ---: |
| NaCl translation cover | 1,512 | 12,096 | 100% / 100% |
| IQC overlap section | 80 | 1,254 | 100% / 100% |
| Fibonacci anchor similarity | 2,090 | 7,222 | 100% / 100% |

This audit exposed and fixed an important hidden failure. The earlier IQC
coordinate benchmark reused the majority species attached to a seed port; it
correctly colored only 60/80 first-scale sites and 0/480 second-scale sites.
The VM instead evaluates the learned bounded internal color section at every
accepted endpoint. No oracle species enters execution, and all 1,334 accepted
IQC sites are now chemically correct. A rigid-motion regression also verifies
that a compiled instruction moves with its cloud within the declared 1e-4
congruence tolerance.

The VM is a shared interpreter, but its three compiler adapters remain distinct
geometric hypothesis learners. The next full-genericity gate is to express
their payloads as one recursively nestable port/cover graph rather than three
opcodes.

That normalization is now implemented by `materials_gcts_port_cover_graph.py`.
Every node has exactly the same schema:

1. a finite binding domain and arity;
2. an affine output map over the bound cluster centres;
3. grouping by coincident output (the covering overlap);
4. a bounded connection/consensus section;
5. a color section; and
6. child-node references for recursive promotion.

The three controls compile to one self-recursive node each. Translation cover
uses integer-cell bindings and an always section; anchor similarity uses typed
unary bindings and its admitted-type section; IQC uses binary metric-port
bindings and its learned port-pair section. The evaluator itself has no opcode
or phase-family dispatch. Re-running the coordinate/species benchmark through
this graph produces the identical six exact outputs above. This closes the
common-interpreter gate; learning multi-node graph topology and dense generic
IQC coverage remain open.

### Self-fed multiscale graph continuation

The complete-heldout-state audit is not causal growth: missing target atoms can
provide ports even if they are never directly scored as predictions. A new
gate therefore starts from the 1,969-site state and inserts only the graph's
own species-labelled emissions before retyping and executing again.

| recursive level | successive self-fed waves | exact sites added |
| ---: | --- | ---: |
| 1 | 260 → 192 → 120 → 80 | 652 |
| 2 | 792 → 204 | 996 |
| 3 | 360 → 240 → 120 | 720 |

All nine nonempty waves are 100% correct in position and species. The graph
adds 2,368 sites and grows the partial cloud from 1,969 to 4,337 atoms. The
155,097-site converged radius-`9 phi^4` oracle is used only for scoring; no
held-out position or color enters insertion. The extra vote cutoff from the
sparse amplifying-batch audit is omitted because membership in a learned port
pair is already the finite higher-order GCTS marking.

This passes a genuine self-fed, three-scale regeneration gate. It is still not
exponential: exact sites per recursive level are `652 → 996 → 720`, so support
does not grow monotonically. Dense growth will require learning another parent
frontier state or a complementary gap-production node rather than lowering the
precision gate.

### Section-assisted gap production

Pair consensus is precise but leaves holes that eventually remove its own
frontier support. The complementary graph node binds one learned metric port,
uses its affine endpoint as a gap proposal, then evaluates the learned bounded
section as an actual connection/failure predicate. Only an accepted endpoint
is colored and inserted. This operationalizes the accept/reject surface
requested for the visual pipeline. However, this section is evaluated in the
learned global IQC superspace; it is not yet a fixed-radius local halo around a
cluster.

| recursive level | exact self-fed sites | nonempty waves |
| ---: | ---: | ---: |
| 1 | 3,304 | 8 |
| 2 | 1,332 | 4 |
| 3 | 300 | 2 |
| 4 | 2,520 | 3 |
| 5 | 780 | 2 |
| 6 | 120 | 1 |

The section rejects 420 invalid candidate endpoints. All 8,356 accepted sites
are independently certified against the hidden six-dimensional model in both
position and species, while the hidden model contributes nothing to fitting or
state. The cloud grows from 1,969 to 10,325 atoms over 20 nonempty self-fed
waves. A coordinate-magnitude-derived lift bound replaces the old fixed bound
16; without that numerical correction, valid large-level sites were
misclassified by the scorer and marking.

This greatly improves generic coverage but still fails the exponential gate:
per-level support oscillates and ends `2,520 → 780 → 120`. A successful next
production must promote the recurrent level-4 frontier state while replacing
the global internal section with a finite, bounded local cluster marking.

### Carried local section marking

`scripts/materials_gcts_propagated_marking.py` makes that replacement at
inference time. The fitted 507-atom seed gives every seed cluster a
three-component mark. A two-cluster port transports those incoming marks to a
candidate with one learned affine rule; the transported mark alone decides
connection/failure and species. The growth loop never lifts a candidate's
global coordinate and never queries the global section. A regression replaces
the lift function with an exception during inference to enforce this boundary.

| recursive level | self-fed waves | exact colored sites |
| ---: | --- | ---: |
| 1 | `582, 60` | 642 |
| 2 | `360, 180` | 540 |
| 3–6 | none | 0 |

Thus 507 atoms become 1,689 using 1,182 / 1,182 exact locally marked additions.
This is the first operational bounded connection marking rather than a global
candidate lookup. It also exposes the next obstruction cleanly: the available
port grammar exhausts after two levels, so the exponential gate remains red.
The next production therefore promotes the 1,689-site recurrent cover and
learns ports between larger-support objects.

A categorical-distillation control explains why the carried state matters. A
whitelist of the seed's ten exact port-multiset contexts has perfect acceptance
precision on only 540 of 8,356 section-accepted sites (6.46% recall) in the
six-level ceiling trace. Coarser port-pair membership reaches 13.16% recall at
97.35% precision. Moreover, one transferred context changes chemical color.
Local incident categories alone therefore do not contain the phase information
needed by the IQC; it must be carried and updated by the marking.

### Self-fed clusters-of-clusters promotion

`scripts/materials_gcts_cluster_promotion_benchmark.py` performs that loop
without introducing a held-out target. It enlarges each cluster's observation
radius by the learned recursive scale, recomputes isometry-invariant colored
support types on the 1,689 sites generated above, and fits their ports against
that generated cover only. The number of recurrent types stays finite at 30,
while average support rises from 29.70 atoms to 98.57 atoms (3.32×) and the
largest promoted cluster covers 225 atoms. This is a cluster of clusters in
the operational sense: the symbol count remains fixed while each symbol's
covered child support grows.

The promoted grammar contains 789 ports and 13,111 compatible port pairs. It is
then frozen and self-fed at three increasing port scales. Exact colored
additions are `3,234 → 8,924 → 17,674`, successive factors 2.76× and 1.98×
(geometric mean 2.34×). The cloud reaches 31,521 atoms from the 507-atom seed.
Every one of the 29,832 promoted additions is independently certified against
the hidden model, which is a post-hoc scorer only. Candidate acceptance and
chemistry use the carried three-component marks.

This clears a finite three-level exponential-style promotion gate. It is not
yet a million-atom or cross-family result: vocabulary size (789 ports) is high
enough that description length must be compared with a flat generator, and
the same promotion code must transfer to the crystal and second-quasicrystal
controls before it can satisfy the stricter single-production benchmark.

The seed compiler no longer receives the IQC's physical unit or hand-written
radial cutoffs. It discovers the inflation rule, clusters the observed
nearest-neighbor distances, selects the smallest shell with at least 5% seed
support, expresses four descriptor radii in that learned unit, and treats the
outer observation boundary as censored. This family-blind route recovers the
same compact 73-port seed atlas and 271 port-pair section.

### Executed cross-family program gate

`scripts/materials_gcts_executable_program.py` now exposes one discovery call
and one explicit-action call. The selector receives only positions and species;
it chooses a translation quotient, carried-port promotion, or substitution
production from seed evidence. `scripts/materials_gcts_common_executed_benchmark.py`
then executes and scores three materialized actions rather than accepting a
symbolic atom count:

| seed | learned production | explicitly scored atom counts | per-action total growth |
|---|---|---|---|
| 216-atom NaCl | translation quotient | `216 → 1,728 → 13,824 → 110,592` | `8.00×, 8.00×, 8.00×` |
| 507-atom IQC | carried-port promotion | `507 → 4,923 → 13,847 → 31,521` | `9.71×, 2.81×, 2.28×` |
| 729-atom Fibonacci product | substitution product | `729 → 3,375 → 13,824 → 59,319` | `4.63×, 4.10×, 4.29×` |

All 252,953 materialized output sites are exact in position and species, all
states are self-fed, and neither family labels nor held-out atoms enter growth.
This makes the cross-family execution gate green. A stricter gate remains red:
three learned production kinds still sit behind the common API. The next
unification target is to express translation and substitution as the same
carried port/cover production used by the promoted IQC, rather than hiding
their distinct executors behind a dispatcher.

The frozen IQC production also executes a fourth promoted scale: it adds
35,414 / 35,414 exact colored sites and reaches 66,935 atoms. This is another
2.00× increase in novel sites, but it exposes a computational failure in the
radial-port implementation. A volume-style neighbor scan took 609.8 s for that
wave. An exact bounding-box spherical-shell index reduces it to 440.8 s
(27.7%) while returning the identical sites. The runtime is still far from a
credible million-atom engine. The implementation now uses the faster grid on
small clouds and shell pruning above 25,000 sites; the next kernel must index
exposed promoted ports rather than repeatedly joining atom pairs.

The bounded descriptor and port scans now use exact spatial hashes. Their
runtime depends on local density and learned port radius rather than scanning
all atom pairs; a brute-force regression certifies identical local colors.

`scripts/materials_gcts_regenerative_scaling_audit.py` turns the existing
regenerative trace into an explicit red scaling gate. Extending the frozen
policy to 16 waves gives
`12,104,12,4,36,24,24,12,8,24,24,24,24,12,12,12`, totaling 368/368 correct
sites. Frontier supply increases despite accepted candidates being removed,
and the largest forced macro contains 104 sites. Yet four-wave groupings shrink
`132 → 96 → 80 → 60`; geometric mean wave growth is 1.0 and the log-cumulative
fit has R² 0.605. Thus neither local waves nor naively grouped wave states
amplify. The next hierarchy must learn a different recurrent frontier state,
rather than treating these exact local macros as exponential by fiat.

`scripts/materials_gcts_frontier_state_grammar.py` now makes that next state
search structural rather than count-based. It builds an adaptive
nearest-neighbour graph on each target-free wave, enumerates connected colored
subgraphs through five sites, and canonicalizes them modulo translation,
positive uniform scale, and proper rotation. The 16-wave IQC trace produces
2,563 candidates and 119 normalized classes. Five classes recur across
independent waves: two two-site, two three-site, and one four-site type. A
deterministic non-overlapping cover selects 156 occurrences covering 336 / 368
exact emitted sites; 32 colored sites remain explicit residual terminals. All
92 admitted non-collinear occurrences replay through fitted proper-SE(3)
poses.

This improves representation without relaxing stationarity. One two-site class
repeats the golden-ratio scale over waves 7--9, but its unique support contracts
`24 -> 12 -> 8`; as a segment it also has a continuous rotational stabilizer
and is not a finite oriented port state. The proper three-site class seen on
waves 14--16 has constant 12-site support and scale ratios 1.2217 then 0.9654.
No class therefore has both repeated expanding scale and repeated expanding
support, and the strict witness count remains zero. A synthetic
`3 -> 6 -> 12` triangle control at scales `1 -> 2 -> 4` passes the same
compiler; colored mirror and amorphous controls remain red. The next generic
step is a certified transition grammar among frontier-state types.

That transition grammar is now implemented. It packs atom-disjoint finite
proper occurrences independently by state type, assigns each next-wave state
to its nearest compatible parent, and stores the entire child set in the
parent's normalized frame. The canonical key jointly quotients the parent
proper symmetry and each child symmetry while retaining relative scale,
rotation, translation, chemistry, and multiplicity. A stationary rule needs
the identical multi-child key on two consecutive transitions with at least two
independent parent occurrences on each.

The exact IQC trace contains three finite proper types, 30 packed occurrences,
and eight complete parent-production observations. They form five exact rules.
Four are heterogeneous multi-child rules, and the largest contains three
children of three distinct state types. This corrects an earlier compiler
artifact that split each child type into a separate unary rule. The scientific
gate stays red for the stronger reason: none of those mixed rules occurs on a
second transition and none has positive description saving. No stationary rule
reaches the target-free executor. A generic expanding control does pass: two
colored triangle parents learn the same two-child rule twice, the executor
reproduces the next two explicit waves, and 18 symbolic actions represent
1,572,864 sites. A separate heterogeneous two-type control also replays two
levels exactly, but is not fed to the scalar symbolic counter; a mixed-state
recurrence requires a learned vector substitution matrix. Thus execution is no
longer the missing API. The remaining scientific blocker is cross-transition
recurrence and compression of the real IQC frontier productions.

The transition learner now also enforces global child ownership: each
next-wave state is assigned once across all typed parents. This removes a
second optimistic failure mode in which the same child could appear in several
incompatible parent rules. A dedicated positions-and-species-only control then
learns the closed two-state system `A -> AB`, `B -> A` from three explicit
waves containing 12, 18, and 30 colored sites. The common proper-similarity
scale is learned as 2, the matrix `[[1,1],[1,0]]` has spectral growth
1.6180339887, and total description saving is 3 despite the necessary unary
second row. The target-free executor reproduces both observed explicit levels
and, without receiving it during fitting, exactly predicts the 48-site fourth
wave; the vector symbolic evaluator reaches 1,178,508 represented sites in 24
actions. Its program digest is invariant under atom permutation
and a generic proper rigid motion.

This closes an important API gap for quasicrystal-like grammars: expansion is
audited for a complete finite-state substitution matrix, rather than requiring
every individual rule to branch. It remains a generic algebra/control. The
actual 16-wave IQC trace produces no recurrent closed state set, so its
multi-state exponential gate remains red.

A fixed 24-wave extension rules out a simple observation-horizon explanation.
The first 16 waves are exact; wave 17 greedily selects 60 false sites, although
the rank-2 band is 48/48 exact and ranks 3--4 are also exact. All four bands are
hard-core valid, and the wrong band has substantial recurring-state cover, so
neither collision rejection nor internal compression is a causal selector.
The score gap between ranks 1 and 2 is 0.0001877. The candidate tree already
contains the correct branch; the next generic gate is beam lookahead and
rollback using boundary connection state only. Later waves are not admitted as
exact recurrence evidence until that branch choice is repaired.

The first beam implementation freezes ranks 1--2, expands both through the
same target-free connection grammar, and ranks the leaves by future boundary
consistency before using the immediate marking as a tie-break. The wrong branch
has future score 0.9997197; the exact sibling has 0.9997951, so one rollback
recovers all 48 sites. A cumulative sum would remain wrong. This separates the
roles cleanly: the marking proposes locally plausible actions, while search
value adjudicates delayed compatibility. Because the policy was diagnosed on
this same trace, the result is exploratory and the confirmatory flag remains
false.

The implementation now executes the policy beyond that single fork. Width two
fails immediately: waves 18--24 contain 40 correct and 72 false selected sites.
Increasing to width four reaches the exact rank-4 wave-18 band, but a pure leaf
score still yields only 36 correct versus 68 false sites on waves 19--24. The
first exact continuation at waves 18 and 19 is rank 4; the correct branch is
present, but scalar score is not a transferable branch value.

A second target-free objective ranks the same four immutable bands by the
number of compatible frozen frontier actions remaining after provisional
placement, using future marking score only as a tie-break. It selects exact
ranks 2 / 4 / 4 on exploratory waves 17--19. Frozen before wave 20, it selects
ranks 2 / 3 / 1 / 4 / 4 on waves 20--24 and adds 120 / 120 exact sites with
four rollbacks. The complete option-preserving trace is 572 / 572 exact and
frontier supply rises from 63,890 to 67,806. The temporal held-forward gate is
green. The run is not spatially independent, its 24 constant-size waves do not
form a stationary substitution, and the generic exponential IQC gate remains
red.

The spatial confirmation is deliberately fail-closed. The marking and
connection grammar are fit only on the 507- and 1,969-site concentric origin
windows. At a disjoint diagnostic centre `(30, 0, 0)`, width four misses even
though the first exact colored score band is rank five; that observation
freezes width five before a second centre is evaluated. The second centre
`(18, 25, 14)` is 33.838 from the origin and 31.064 from the first centre, so
its whole radius-14.562 scoring ball overlaps neither the training domain nor
the first scoring ball. The centre norms also differ, excluding any
origin-fixing proper rotation between the nuclei.

The second run freezes 5,616 bounded candidate sites and the width-five branch
decision before constructing the target. Posthoc scoring finds 431 correct
colored candidates in that frozen universe, but all five retained score bands
are false; the first band containing any correct colored site and the first
pure-correct band are both rank seven. Thus candidate generation transfers,
while the fixed breadth/value policy does not. The one-shot spatial gate is
red and is not a stationary or exponential certificate. The next admissible
improvement must choose breadth or branch value from training/frontier state,
then face a new spatial nucleus; this target cannot be reused for tuning.

A multi-configuration learner implements that feedback loop without adding a
material or origin label. It pools the same rigid-motion-invariant local
descriptor over three mutually disjoint nuclei—the origin and the two completed
diagnostics—giving 15,830 training candidates and 3,171 positives. The marker
and width-four option-supply search are then frozen before opening a fourth
radius-14.562 nucleus at `(-20, 20, 20)`, disjoint from all three training
balls. The exact 2-site action is now present at rank four inside the retained
beam, whereas the single-origin marking placed the correct basin below its
frozen breadth. This is a genuine proposal-ranking improvement.

The one-step branch value still selects rank two, emitting three false sites.
Accordingly the multi-nucleus spatial gate remains red. Its failure is more
specific: candidate geometry transfers and the learned marking retains the
right action, but the executor collapses the beam to one configuration after
only one lookahead. The next tree-search benchmark must keep complete
alternative configurations alive for multiple depths and count actual
rollback/backtrack work before committing; widening the same one-step rule is
already falsified.

The executor now implements that persistent state explicitly. Four complete
configuration states—atoms, colors, remaining frozen proposals, regenerated
ports, and collision state—are carried through three depths; 36 branches are
evaluated before the first move is committed. A robust local marking uses the
minimum score across three leave-one-nucleus-out models. On the fourth nucleus,
this combination selects path `4 / 3 / 3` and recovers an exact 3-site first
action. This is diagnostic because the fourth target was already opened by the
preceding test.

The policy is frozen without modification and tested once at a fifth centre
`(20, -25, 20)`. Its target-ball separation from every prior centre is at least
33.541, above the required 29.125. The exact 1-site action again appears inside
the four retained roots at rank four, but the three-depth frontier-cardinality
objective selects `2 / 3 / 2` and emits one false site. Target membership is
attached only after all 36 branch expansions and the choice are immutable.
The fifth-nucleus gate is therefore red. Two independent nuclei now show the
same causal boundary: multi-nucleus marking retains the correct geometry, while
frontier size—even after real multi-depth search—is not a transferable value
function. The next admissible change is a train-only learned value over branch
connection state, using this persistent beam unchanged.

The first such value model is deliberately finite and auditable. Across the
two completed diagnostic nuclei, exact-action counts for root ranks one through
four are `(0, 0, 1, 2)` out of two each. With a frozen Beta(1,1) prior, the
rank-value channel is `(0.25, 0.25, 0.50, 0.75)`. Rank is the ordering of the
already learned local marking, not an absolute coordinate or IQC label; future
frontier cardinality remains only a tie-break. The candidate set, robust
leave-one-nucleus-out marking, width four, branching four, and depth three are
otherwise unchanged.

This model is frozen before a sixth nucleus at `(-20, -20, -25)` is opened.
Its complete scoring ball is separated from every prior ball by at least
37.749, versus 29.125 required. The four candidate roots contain one exact
1-site action at rank four. After 36 target-free branch expansions, the value
selects path `4 / 2 / 2`; posthoc scoring confirms 1 / 1 correct colored site
and zero false sites. The one-action spatial branch-selection gate is green.
This is not yet a sustained-growth result: no second confirmed action,
stationary production, amplification factor, or exponential certificate is
inferred from it.

The same sixth nucleus is then reused only diagnostically for two self-fed
waves. The first action stays exact, while the second width-four choice is
false. Crucially, a frozen snapshot of twelve score bands (the extra bands are
inspected but not expanded) contains exact 1-site actions at ranks six and
twelve; ranks one through five are all false. Thus the second-wave failure is
not missing geometry and cannot be repaired by a different value over the same
four roots. It is a learned action-channel coverage failure. Active branching
width and diagnostic snapshot reach are now separate audit fields. Any move to
six or twelve active channels must be chosen using training-side pose/port
coverage and face a new nucleus; the opened sixth target is not a tuning gate.

The finite channel learner therefore retains every rank at which an exact
alternative occurred in the completed training observations. Those ranks are
`3, 4, 6, 7, 12`, fixing channel reach at 12. The rank-value posterior is
refit with heterogeneous support: ranks 1--4 have four observations, ranks
5--12 have two. Enumeration width becomes 12, while only four complete
configuration states survive each beam layer. This ties channel count to
observed connection/pose coverage rather than to a manually selected slider.

The predeclared seventh-nucleus invocation lost its result at the execution
transport boundary. Because it may have opened the target, it is recorded as
consumed/unknown and is never rerun. The unchanged artifact is tested at an
eighth centre `(-25, 20, -20)`, separated from every prior target centre by at
least 37.749. It evaluates 108 target-free branches over three depths, selects
path `4 / 12 / 11`, and emits 1 / 1 exact colored site. The one-action learned
channel/value gate is green on this fresh nucleus. Sustained self-fed growth,
stationarity, and exponential amplification remain separate red gates.

Two completed second-wave diagnostics then justify one bounded contextual
extension. In the initial state, exact rank four appears in all four available
frontiers, giving posterior value `5/6`. Conditional on the previous committed
root being rank four, both independent observations contain exact ranks six and
twelve, giving each `3/4`; all other ranks receive `1/4`. This is an order-one
carried connection mark. It contains only the previous finite channel ID and
the candidate channel rank, never a coordinate, target site, nucleus identity,
or material-family label.

The contextual artifact is frozen and executed for two waves at a ninth centre
`(-25, -20, 20)`, whose radius-14.562 target ball is disjoint from every prior
ball by at least 37.749. Twelve root channels are enumerated, four complete
states are retained, and 108 real branches are expanded per wave. The selected
paths are `4 / 12 / 11` and, after carrying context four, `12 / 9 / 10`.
Posthoc scoring gives wave truth `(1, 1)`, falsehood `(0, 0)`: two exact
self-fed colored sites. The two-wave spatial tree-search gate is green. Its
unit wave sizes show no amplification, and no repeating production or scale is
inferred; stationary and exponential IQC gates remain red.

A third ordinal context is then trained without ambiguity: after the confirmed
`4 / 12` prefix, the sixth, eighth, and ninth diagnostic nuclei all have an
exact rank-six action, yielding posterior `4/5`. The resulting states are
`0`, `4`, and `12`. On a tenth disjoint nucleus `(30, -25, -20)`, the model is
executed for three target-free waves. It fails immediately: the exact initial
action is rank eleven, while the table selects rank four. The later frozen
snapshots likewise contain exact geometry at different ranks, but the already
wrong state makes those paths unusable. All three emitted sites are false.

This is a constructive red result: finite channel reach 12 is adequate, but
ordinal score rank is not a transferable channel identity. Rank changes when
the local candidate population changes even if the underlying port relation is
the same. Subsequent GCTS values must be indexed by symmetry-quotiented
parent/source cluster identity and connection-port semantics; rank may only be
a deterministic executor ordering and cannot carry physical state.

Four ID-free categorical quotients are evaluated next on the same frozen
candidate geometry. Exact local evidence, full parent/source radial types,
and coarse colored port types each have zero held-out channel coverage on the
tenth nucleus. Removing geometry down to connection chemistry raises overall
candidate coverage to 25%, but the one exact held-out action is still not a
train-exact chemistry class. No key sees target membership before it freezes,
and none authorizes geometry; they only rank existing certified candidates.
This falsifies a finite lookup-table marking at the tested resolutions. The
next admissible representation is a continuous rigid-motion-invariant section
learned across multiple nuclei, backed by the unchanged exact port/collision
certificates.

The continuous replacement is now measured on a fresh eleventh nucleus. Nine
completed disjoint nuclei supply 49,716 candidate rows and 3,695 exact colored
positives. The label is species-aware: correct position with incorrect species
is negative. The descriptor remains a bounded radial/color/vote section and is
invariant under common proper-SE(3); exact ports and collision checks remain the
admission layer. Leave-one-nucleus-out fitting places an exact action within
the fixed twelve-band reach in 8 / 9 nuclei (first in 2 / 9), so the training
evidence is useful but not uniformly easy.

The full model digest is
`bb891f2c5055afe529c77c2834632c4df654bb2c9c944b1a4ae888535d980697`.
It is frozen before constructing the radius-14.562 target about
`(0, 0, -50)`. Minimum separation from every training centre is 37.749, above
the 29.125 disjoint-ball requirement. The target-free width-four,
twelve-channel, depth-three search selects path `1 / 5 / 12`; the first band
is the exact action and emits 4 / 4 correct colored sites with no false site.
This is a green one-action spatial confirmation for a continuous GCTS local
section. It does not certify a second self-fed wave, a promoted macro,
stationarity, amplification, or exponential IQC growth.

The identical model is next frozen for two waves at `(0, 50, 0)`, again outside
every prior target ball. Both decisions enumerate twelve candidate bands.
Wave one selects path `1 / 5 / 12` and emits 4 / 4 exact colored sites. On the
self-fed frontier, the exact action remains available at rank five, but the
section selects path `1 / 7 / 8` and emits 0 / 4 correct sites. Overall
precision is therefore 4 / 8 and the two-wave spatial gate is red. This rules
out missing geometry and insufficient channel reach as the immediate cause.
The continuous section was trained only on seed frontiers; the justified next
step is to include target-free post-commit states from the known training
nuclei, not to carry ordinal rank or tune against this failed target.

The follow-up performs exactly that intervention without using the failed
nucleus. Eight of nine training nuclei expose an exact teacher-forced first
band. Their post-commit states supply 44,439 candidates and 3,205 exact colored
positives; a separate continuous section is fitted and selected at every depth
after the first commit. At a new disjoint centre `(-50, 0, 0)`, wave one emits
4 / 4 exactly. Wave two retains an exact action at rank four, but selects rank
one and emits 0 / 4. The gate remains red. Therefore training-state exposure
is not the only problem: the existing continuous descriptor contains bounded
radial/color/vote statistics but not a continuous summary of the actual
parent/source port states. That symmetry-invariant connection distribution is
the next representation change to test.

That representation change succeeds. `port-state-v2` adds only continuous,
rigid-motion-invariant summaries of the already frozen connection evidence:
weighted separation-bin moments, parent/source neighborhood sizes,
same-color/same-shape fractions, state and parent diversity/purity, and source
and target color entropy. It contains no raw type identifier, Cartesian
position, global direction, nucleus ID, phase label, or heldout atom. Exact
proper-SE(3) ports, species votes, and collision checks remain unchanged.

All nine training nuclei now supply an exact teacher-forced first action. Their
post-commit corpus has 50,065 candidates and 3,677 exact colored positives.
The seed and self-fed model digests are respectively `d489513f...eecbb5` and
`0629b18e...dfe0b`. Both freeze before the outer target about `(0, -50, 0)` is
constructed. The unchanged twelve-band, width-four, depth-three executor ranks
the exact action first on both frontiers, selects `1 / 6 / 8` then `1 / 7 / 6`,
and emits 4 / 4 plus 4 / 4 exact colored sites. The two-wave spatial gate is
green with no ordinal carried state. This proves self-fed finite marking
transfer; four-site wave size, no promoted recurring rule, and no amplification
leave stationary and exponential IQC growth red.

### Whole-action antichain preflight

The next experiment does not reinterpret the successful `4 + 4` sites as
parallel growth. It asks the continuous section to admit several complete
score bands that are pairwise compatible with the seed and with one another.
Such a batch is an antichain: every band remains an ordinary tree-search
action, but the accepted bands can be committed in any permutation.

The first train-only calibration uses the raw port-state probabilities. A
zero-error cutoff selects 50 / 50 seed-state sites from 49,716 rows and 24 / 24
self-fed sites from 50,065 rows. Frozen on a new disjoint centre `(0, 0, 50)`,
neither cutoff admits a band, so execution stops before wave one. This is a
score-scale transfer failure, not a collision or target-leakage result.

The replacement acts on whole bands. Its 15 rigid-motion-invariant features
contain score margin/rank, band and frontier size, vote consensus, source and
target port-role purity, state entropy, and parent multiplicity. They contain
no candidate coordinate, raw type ID, nucleus ID, phase label, or heldout
atom. The first 24 bands in each of nine nuclei give 216 seed actions with 57
pure positives and 216 self-fed actions with 48 pure positives. Ridge strength
and threshold are selected by leaving out entire nuclei. No threshold reaches
the predeclared 95% action precision for either stage, so the benchmark fails
closed before constructing the reserved `(50, 50, 0)` seed or target.

This is a stronger and more useful red result than another hand-chosen score
cutoff. The continuous section transfers as a ranking for one action, but local
scores do not yet authorize a multi-action batch. The justified next search
state must carry unresolved outgoing port obligations through bounded
lookahead/backtracking; exact geometry, collision checks, and the final sealed
site/species score remain separate gates.

A first target-free lookahead implements that search-state change at aggregate
resolution. Every candidate band is applied to the exact training frontier;
the resulting frozen proposals supply connection consensus, recurrent-state
support/purity, parent multiplicity, and unresolved singleton load. Those 28
future/delta values augment the 15 local band values. They contain neither
coordinates nor raw IDs and are rigid-motion and insertion-order invariant.

The group-heldout models now find a zero-error operating point, but only by
retaining one seed action and one self-fed action out of 216 in each table.
That is insufficient for the stated parallel-growth task. Before any new
target is opened, the preflight requires 95% precision and at least 18 retained
actions per stage—two per training nucleus in aggregate. The measured `1 / 18`
and `1 / 18` coverage therefore keep the gate red. Aggregate successor
statistics improve purity but collapse action coverage; the next justified
representation carries the actual bounded incidence multiset of unresolved
ports through backtracking rather than compressing it to moments.

That explicit state is now implemented. A semantic role contains only the
parent and source cluster colors, their cumulative neighbor-count types, and a
normalized separation bin. Whole actions carry at most eight such roles;
action IDs remain exact search identities but never enter the state. A child
must consume at least one carried role, and a branch is rolled back when an
explicit obligation has no candidate continuation. Synthetic adversarial
tests reject a higher-scoring stranded root and a disconnected child.

The nine-nucleus train-only audit builds 504 exact actions with 23 pure
coordinate-and-species positives. Leaving out whole nuclei, 97.40% of role
mass is already present in the remaining training folds, so vocabulary
novelty is not the principal failure. The explicit search explores 306 actions,
backtracks 49, and finds two-action connected paths on eight of nine folds.
Posthoc, however, all 16 selected actions are false and emit 120 false sites.
No individual role or order-two same-site role pattern reaches transferable
90% purity: apparently pure patterns occur in only one nucleus. The reserved
confirmation centre is still unopened. This rules out both marginal port
admission and topological closure as sufficient GCTS markings; the next model
must retain joint incidence geometry while exact placement and collision
certificates remain unchanged.

The next preflight changes the action resolution rather than the target. Whole
equal-score bands are split into 44,602 collision-free candidate cluster
centres (3,689 exact colored positives). Each ID-free descriptor combines the
semantic port roles and order-two incidences with proposal-neighbour distances
and the colored metric graph of the nearest occupied neighbors. Pairwise
neighbor distances supply an invariant angular surrogate that radial shells
alone cannot encode. The descriptor is
invariant under atom permutation and common proper-SE(3) motion; absolute
coordinates, the nucleus centre, target atoms, and raw occurrence IDs are not
serialized. Nine leave-one-nucleus-out models see 99.49% of heldout tokens and
assign fitted weight to 98.89%. The complete calibrated score level admits
25 / 26 exact compatible candidates (96.15% precision), but they occur in only four of nine
nuclei. The unchanged gate requires at least 18 placements and coverage of all
nine, so the reserved confirmation remains sealed.

The interface geometry controls now have a direct backend audit. The bounded
hypothesis grid is exactly one/two/three-shell reach crossed with coarse/fine
distance quantization; all six arms see the same 44,602 exact candidate
placements. In every outer fold an inner leave-one-nucleus-out loop on the
other eight chooses the descriptor geometry and a complete-score threshold.
This fully nested selection exposes calibration shift rather than curing it:
the frozen outer models select 41 / 65 correct actions (63.08%) and only six
nuclei are error-free. A fixed top-two rank removes the score-scale failure
and gives two exact actions on each of eight generic nuclei, but both actions
at the unique symmetry-centred nucleus are false (16 / 18, 88.89%). Its first
exact action is rank 189 with eight neighbors and remains rank 121 after
expanding the section to 32 neighbors. The centred stratum is therefore an
explicit out-of-distribution red control; it is not dropped or used to justify
opening the reserved confirmation nucleus.

The next fixed experiment projects the same tokens into semantic channels: all
members of one token family contribute their average evidence, so orbit size
cannot multiply a family's vote. A target-free selector uses the larger exact
top-score equality orbit to choose detailed versus channel scoring, with ties
fixed to detailed. At reach three, distance width 0.25, eight neighbors, and a
two-action antichain, leave-one-nucleus-out development is 18 / 18 exact. The
rule is frozen in commit `644d69f`; a second preregistration commit fixes the
reserved target order and protocol digest before execution. The disjoint
confirmation at `(0, 0, -50)` is 0 / 2: the detailed and channel top bands have
sizes four and two, the rule chooses detailed, and both selected placements are
false. The target is opened once after the candidate, descriptor, model, and
selection hashes are immutable. This falsifies orbit-size selection rather
than the finite pose/port representation and supplies a concrete requirement
for a learned joint role-incidence geometry section.

Post-confirmation development keeps the next disjoint centre sealed. A
deterministic disagreement selector—channel scoring whenever detailed and
channel top-orbit cardinalities differ—recovers 18 / 20 group-heldout actions,
not the required 20 / 20. A second, fully nested candidate-level learner
cross-fits the base token marking inside every outer fold and fits a 15-feature
linear section over score, rank, orbit cardinality, token-family count, and
evidence coverage. Ridge values 0.1, 1, and 10 all select 0 / 20 exact actions.
The candidate graph digest is unchanged. These controls rule out scalar
mixtures of the two sections; transferable selection must preserve joint
port-incidence geometry rather than summarize it into scores.

The first graph-valued correction couples the primary symmetry-quotiented port
role directly to each occupied colored shell and occupied-neighbor metric edge.
It adds 6,140 role--shell and 19,837 role--edge types while preserving the exact
candidate digest. In ten outer held-out folds, 97.66% of descriptor tokens have
train-frozen weights, but the best two-action result is 15 / 20. Raising the
minimum support/group evidence from 4/2 to 16/3 or 32/3 yields 14 / 20; a 64/5
floor yields 8 / 20. This is not a vocabulary-coverage problem. A marginal sum
over relational edge tokens loses graph topology, so the next bounded marking
must canonicalize finite incidence subgraphs or perform finite message passing.

The bounded message-passing control initializes occupied nodes by species and
candidate-relative radial shell and performs one or two complete-graph message
rounds with quantized pair distance as the edge label. Every resulting node and
graph color is conditioned on the primary symmetry-quotiented port. Both depths
select 14 / 20 exact heldout actions. The exact hashes produce 80,323 node
colors after one round and 161,768 after two, revealing representation
fragmentation rather than missing candidate geometry. Because these colors are
ranking features only, collisions cannot authorize a placement. The next
bounded learner must fit a finite quotient of message colors on training folds
instead of retaining exact neighborhood hashes.

That finite-quotient gate has now been run. Exact one-round colors are
coarsened by train-development distance divisors two, four, and eight and by
symmetry-reduced parent/source role projections. The smallest exact arm has
12,954 node and 5,787 graph colors, but every exact-hash arm still selects
14 / 20 actions. An additive incidence quotient replaces whole-graph hashes
with bounded colored node and metric-edge multiplicity tokens; it compresses
to 457 node and 976 graph types and improves only to 15 / 20. A separate
positive codebook then admits a prototype only when its finite graph view
occurs in at least two or three independent train nuclei. The selected
three-nucleus codebook contains 356--358 prototypes across folds and selects
11 / 20. All arms rank the same exact candidate graph, and the declared next
centre `(0, 50, 0)` is not constructed. The result is therefore a clean red
gate: finite compression is real, but neither additive bags nor nearest
recurrent graph prototypes provide the missing branch value.

The development corpus was then expanded under a separate committed protocol.
Eight radius-14.562 centres were selected geometrically and committed in
`fc80434` before any of their atoms were materialized. Their minimum separation
from prior or reserved domains is 37.417, and their mutual minimum is 44.721,
both above the required 29.125. The common model-set crop is stable between
coefficient bounds 24 and 25, with 476--496 seed and 2,028--2,064 target atoms
per new nucleus. The frozen additive quotient selects 14 / 16 new actions and
30 / 36 over all eighteen leave-one-nucleus-out folds. Increasing recurrence
support/group floors gives 28, 24, or 27 / 36 rather than an improvement.

The next train-only model treats the bounded incidence configuration as a
conditional state. It learns full node/edge/graph purity, then backs off to
node/graph, graph/port, and coarse port/color/occupancy states when evidence is
insufficient. Its best fixed floor has 4,353--4,636 supported fine states per
fold but selects only 29 / 36 actions. This falsifies whole-state lookup as the
missing GCTS value. The exact candidate graph is unchanged, all expanded
targets are development data, and the reserved `(0, 50, 0)` confirmation has
not been constructed.

The next correction restores attachment orientation rather than treating the
separation bin as a complete pose. Candidate-to-parent axes are related to the
already occupied neighborhood through dot products and signed scalar triple
products. This is invariant under global proper SE(3), retains chirality, and
does not introduce a lattice axis. Angular widths 0.125, 0.25, and 0.5 produce
9,580, 6,501, and 4,414 finite orientation tokens. Fine channels score 28--29 /
36; the coarsest exactly ties the 30 / 36 unoriented baseline.

A nested order-independent control then replaces greedy placement by one tree
node containing an unordered compatible pair. Each outer fold fits its
individual shortlist on the other seventeen nuclei; every inner pair corpus is
formed with the inner nucleus excluded as well. All 120 compatible pairs from
the top sixteen actions are scored. Every nucleus contains an exact pair in
that frozen shortlist (6--120 exact pairs per nucleus), yet all bounded pair
grids again select 30 / 36. Therefore the current six failures cannot be
attributed to missing rotations, absence of correct candidate pairs, or action
permutation order. The exact candidate graph is unchanged and the reserved
confirmation remains unopened.

The first model to improve the expanded result values the state created by an
action. For every outer fold, the additive model supplies a top-16 shortlist.
Each shortlisted action is placed hypothetically; local cluster types and
connection proposals are recomputed, and a finite descriptor records only the
new outgoing frontier's size, vote and parent mass, chemistry, port roles,
order-two incidences, and normalized distances. The development target is used
only for fold labels, never to construct the successor. Across folds, 19--46
unique candidate successors are evaluated per nucleus. With support/group
floors 16/4 and unit mixing, the corrected causal-endpoint value selects
32 / 36 rather than 30 / 36. A bounded second step then
executes the four strongest target-free outgoing children of every root. It
evaluates 76--184 child branches per nucleus and increases supported rollout
tokens substantially and reaches 33 / 36 with 16 / 18 exact nuclei. Thus
another unordered frontier shell is not sufficient; the next representation
must retain which port obligation survives
along which root-to-child path. The reserved confirmation remains sealed.

Keeping the directed path instead of pooling it is materially better. A path
descriptor joins the root successor, the incoming child-port roles and
order-two patterns, and the child successor. All path geometry is serialized
before labels are read; a training path is positive only when both root and
child have the correct species-position. The root value is the maximum over
four train-supported child continuations. This reaches 33 / 36 actions. The
same audit widened from four to sixteen children, producing 176--256 paths per
heldout nucleus and at least two exact paths in every nucleus. Selection rises
to 34 / 36 with 16 / 18 exact nuclei. Candidate supply is therefore complete
at this bounded depth; the remaining two mistakes are score-transfer failures
among present alternatives. The reserved confirmation remains unopened.

A generic multi-configuration connection merger was then tested before any
further scoring change. It pools positive and negative state counts, target
chemistry, and the number of independent configurations with a correct
connection. Directly merging exact raw local types is strongly negative:
boundary-perturbed cluster-count identities fragment the state key. At the
loosest 2-support / 2-group / 0.5-purity gate, correct root candidates exist in
14 / 18 heldout nuclei and an exact root→child continuation in only 7 / 18;
stricter recurrence floors collapse supply further. The heldout target is used
only after candidate generation to score this ceiling. Multi-configuration
evidence therefore must be learned after a shared recurrent cluster quotient,
not by unioning raw connection markings.

The recurrent-first order was then tested directly. From ten training nuclei,
the generic learner retains 455 local pose classes occurring in at least two
independent configurations, maps each raw local type to that frozen quotient,
and only afterward pools connection evidence. All eight expanded validation
nuclei contain a correct first action and an exact root-to-child continuation.
The former 7 / 8 result was caused by a directed bookkeeping defect: a newly
placed cluster may be the source endpoint of an affine connection, yet the
successor search retained only geometric-parent indices. A separate causal
endpoint map now preserves both dependencies without changing the ordered
parent/source state used by the marking. This passes the 8 / 8 development
supply gate without relaxing support or purity; the reserved confirmation crop
remains unopened until the corrected rule is committed and preregistered.

The corrected rule was committed, then separately preregistered with source
hashes and a supply-only gate before the reserved centre `(0, 50, 0)` was
opened once. The frozen model contains 455 recurrent prototypes and 21,841
admitted states. Before target access it serializes 672 root candidates and
1,104 causal one-step successors. Posthoc scoring finds 38 exact colored roots
and four exact root-to-child paths; the first appears after scanning eight
correct roots. The nearest development centre is 33.838 units away, above the
29.125 disjoint-domain requirement. This is a positive transfer confirmation
for finite GCTS candidate supply. Because target labels identify which paths
are exact and no frozen value selects one, autonomous selection remains open;
stationary and exponential claims remain red.

The follow-on recurrent-path selector keeps that supply fixed and learns only
a bounded connection value section. Its descriptor contains the candidate
action incidence, the newly placed root's causal successor state, order-two
incoming port patterns, predicted colors, and a normalized root-to-child
distance; it contains no target coordinate. The prerequisite 256-root by
16-child tree contains exact paths in all eight development nuclei, with
posthoc counts `13 / 2 / 8 / 8 / 1 / 14 / 13 / 13`. Group-heldout marking
selects an exact path first in `7 / 8`; the remaining nucleus has one exact
path among 293 frozen alternatives. Candidate supply therefore passes, while
the autonomous selector gate remains red and no new sealed confirmation is
authorized.

The first explicit clusters-of-clusters path value adds a target-free
compatibility calculation rather than another token reweighting. For every
tentative root→child insertion it incrementally recomputes the nearest frozen
prototype residual of both new clusters and every affected existing cluster.
An exact parity test compares those increments to full reclustering, while
proper rigid motion and input permutation leave the result unchanged. The
bounded section also carries the connection direction relative to a frontier
normal estimated from the nearest eight occupied sites; no global origin or
target coordinate enters. With fixed eight-to-one hard-negative sampling and
ridge `0.1`, group-heldout selection remains `7 / 8`, but the lone exact path's
rank falls from 101 to 21 (`4.81×` less branch work before reaching it).
This is a measured clusters-of-clusters pruning gain, not a passed autonomous,
stationary, or exponential gate.

The follow-on audit corrects an overly restrictive execution assumption. The
directed-path diagnostic required every third action to descend from the last
inserted cluster, although the intended GCTS covering search may next use any
exposed frozen port in the current configuration. Ten training nuclei provide
20,716 candidate descriptors and 1,151 correct actions across three self-fed
stages. A stage-aware leave-one-nucleus-out grid selects a support-4,
two-independent-group, 0.5-shrinkage finite incidence marking without reading
heldout targets. Conditional on one known-exact two-action prefix per heldout
nucleus, the complete post-commit frontiers contain 57--75 exact actions. The
clusters-of-clusters compatibility baseline reaches the first exact action at
ranks `3 / 3 / 4 / 4 / 1 / 9 / 9 / 9`; the finite post-commit marking reaches
`3 / 4 / 3 / 3 / 1 / 1 / 1 / 1`. A width-four configuration beam therefore
has complete conditional supply, but top-one selection succeeds in only four
of eight. Because heldout truth constructs the exact prefix, this is explicitly
a conditional search audit, not autonomous continuation, stationarity, or an
exponential IQC certificate.

The corresponding orientation-capacity control holds every exact candidate
fixed and augments only its marking descriptor. Attachment axes are encoded by
dot products and signed triple products in the occupied local frame, quotienting
global proper rotation and translation while preserving chirality. A grouped
training comparison over angular widths 0.125 / 0.25 / 0.5 and additive versus
one-vote-per-channel scoring selects width 0.125 with channel normalization:
it ranks an exact action first in 23 of 28 eligible training stages and retains
28,558 weighted tokens. Heldout transfer is negative. The first-exact ranks are
`5 / 1 / 7 / 6 / 1 / 3 / 3 / 3`, only two of eight top-one choices are exact,
and the required conditional beam widens from four to seven. Hence observed
cluster rotations are an input to the marking representation, but raw rotation
cardinality is not the channel count. Capacity remains admissible only when a
finite recurrent pose × port quotient improves heldout evidence.

That quotient is now implemented with the stage ownership requested by the
interactive lab. The clustering audit freezes the 0.125-radian proper-pose
atlas upstream; the marking fit cannot silently change its angular resolution.
Five invariant evidence channels pool connection role, proposal multiplicity,
occupied shell, neighboring incidence, and pose/chirality token responses.
Grouped train-only selection chooses token support 4 across two independent
nuclei and state width 1.0, yielding 437 recurrent states. The exact candidate
set is unchanged. On the eight conditional post-commit frontiers the first
exact ranks become `1 / 1 / 1 / 1 / 1 / 1 / 1 / 1`, versus
`3 / 4 / 3 / 3 / 1 / 1 / 1 / 1` before the quotient. The conditional top-one
development gate is therefore green. Its model digest is
`9b83898155f5d729499c441bcbafa6491b553196fe87de756cb6281b8b856b13` and
its candidate/descriptor digest is
`a241b449374deadd73ff32fc48f45c87412e0fa8073c6fac35848e5bc5e785b4`.
This still uses truth to construct the known-exact two-action prefix; a new
sealed self-fed nucleus is required before calling the selection autonomous.

The sealed self-fed check has now been run and fails. The first preregistered
centre `(-70, -70, 30)` is recorded consumed/unknown after bound-24 and
bound-25 target crops disagreed; no score was computed and that nucleus is not
reused. A replacement at `(-50, 50, -10)` is 40.31 units from every prior
target centre and uses a bound-32 / bound-33 stable crop. The frozen 437-state
policy constructs a target-free width-four, reach-four, depth-three tree with
`4 / 16 / 16` candidate snapshots and four retained configurations per depth.
The chosen branch is genuinely self-fed but posthoc only one of its three
colored sites is exact. Candidate digest
`028acae9f4c2105f506b06de0e2c8d6aa238bd8d6e7fb3932c8d682af148529e`
and pre-target trace digest
`d2a0290f5bf819a7234803b71ac38fcb539e8ace4409b8156e2c73aeb6f6e49d`
freeze the failure. Conditional branch selection is green; autonomous top-one,
sustained, stationary, and exponential IQC growth remain red.
Post-confirmation replay on this now-consumed development nucleus separates
supply from value. The tree contains one exact path, whose within-parent ranks
are `1 / 4 / 4`; exact-candidate counts are `1 / 7 / 7`, and the exact prefix
survives every depth. Yet cumulative state probability ranks that path 10th of
10 terminal configurations, while the selected path has truth pattern
`exact / false / false`. Group-heldout capacity controls show that beam
4 / 8 / 16 at action reach four all retain exact paths in only 6 / 10 training
nuclei and select 4 / 10; reach eight plus beam sixteen reaches only 7 / 10
supply and still 4 / 10 selection. Individual correct-action ranks reach 17,
28, and 847. Hence neither raw width nor geometry is the accepted fix: the
next gate is a learned recurrent branch value with bounded search cost.

An individual two-step port graph then separates candidate supply from marking
failure. One canonical representative of each local descriptor class is
ranked by the frozen connection score, and the first 128 per nucleus are
expanded without a target. A child is admitted to the graph only when the
newly placed root is one of its witnessed parents and exact exclusion geometry
passes. All nine known nuclei contain exact root→child pairs; their counts are
`12 / 53 / 24 / 14 / 27 / 27 / 27 / 27 / 6`. The carried obligation is one
primary symmetry-quotiented port (vote multiplicity is evidence, not extra
cardinality), while the remaining roles stay as order-two marking patterns.
The first executor nevertheless selected zero of nine exact paths because it
added an unrelated raw child-vote score after evaluating the learned joint
root→child value. Removing that double count leaves the candidate graph fixed
and raises group-heldout selection to five of nine. This is a sharper red
result: the finite exact tree already contains the answer in every nucleus,
and correct score composition exposes useful marking transfer, while four
boundary environments still require a transferable path-value section.

A fixed third-frontier control asks whether that value is simply the size or
quality of the immediately available continuation. For each nucleus, the 512
highest raw-child-evidence paths are frozen without labels; exact alternatives
remain present in every shortlist (`12 / 22 / 15 / 10 / 13 / 13 / 13 / 13 /
2`). Each path is executed one additional step without committing it. The
bounded descriptor records the outgoing semantic roles, order-two incidence
patterns, vote and parent mass, predicted color set, and normalized radial
histogram—never a target coordinate or global origin. Group-heldout selection
is only four of nine, worse than the corrected two-step section's five of nine.
Immediate frontier supply is therefore another measured negative value
function, not justification to open the reserved nucleus.

## Generic intrinsic-2D atlas gate

`scripts/materials_gcts_2d_generic_atlas.py` removes the original moire
fixture's assumptions of exactly two binary XY sheets.  From positions and
species alone it learns connected affine components, rank-two colored
translations in arbitrary 3D orientation, the complete motif modulo the
translation torus, motif isometry classes, and one finite pose marking per
component.

| control | seed -> held-out | learned motif poses | atoms per pose action | position/species |
| --- | ---: | --- | ---: | ---: |
| globally rotated graphene-like monolayer | 373 -> 1,495 | 1 x C2 | 1,122 | 100% / 100% |
| globally rotated 30-degree hBN-like bilayer | 746 -> 2,990 | 2 x BN | 1,122 | 100% / 100% |
| globally rotated 13-degree Janus MoSSe-like bilayer | 878 -> 3,578 | 2 x MoSSe | 1,350 | 100% / 100% |
| globally rotated, anisotropically strained 17-degree hBN-like bilayer | 748 -> 2,990 | 2 x BN | 1,121 | 100% / 100% |

Keeping only one pose per motif-isometry class leaves both bilayers at exactly
50% recall; restoring the learned cluster-of-clusters pose marking restores
100%.  This is a causal marking ablation with the motif dictionary fixed.

### Cross-layer registry model selection

Compact whole-structure generation does not imply that exact local interlayer
registry has a finite vocabulary. `scripts/materials_gcts_2d_registry_selection.py`
learns rotation-invariant, species-resolved cross-layer sections at increasing
radii inside the same 932-atom seed, then chooses its marking representation
before opening a 2,384-atom held-out disk.

| bilayer | local states at 5 / 10 / 15 Å | seed-local coverage on held-out registry | selected marking |
|---|---:|---:|---|
| aligned | 2 / 2 / 2 | 100% | finite local registry + pose fallback |
| commensurate 21.7868° | 10 / 10 / 10 | 99.53% | finite local registry + pose fallback |
| 30° incommensurate | 10 / 33 / 71 | 30.22% | two-state cluster-of-clusters relative pose |

The 30° local vocabulary has empirical growth exponent 0.890 and reaches 223
states in the held-out window, so the learner rejects it as an unbounded exact
local marking rather than memorizing ever more environments. Its two learned
component poses still generate the held-out structure exactly. The choice uses
only vocabulary growth inside the seed; family labels and held-out atoms are
excluded.

`scripts/materials_gcts_2d_robustness.py` deletes 3.35% of a 746-atom hBN seed
and adds 0.006 Angstrom Gaussian coordinate noise.  The learner covers the
vacancy-isolated residual atoms, recovers both BN poses with minimum translation
support 0.878, and reconstructs the clean 2,990-atom scaffold at 100% registered
position/species precision and recall with 0.0031 Angstrom RMS error.  The pose
ablation remains at 50%.  This is scaffold recovery, not prediction of future
random defects or thermal displacements.

`scripts/materials_gcts_2d_recursive_macro.py` promotes the learned two
translation ports into a cluster-of-clusters address grammar.  Each level has
four transformed references to the preceding level and therefore represents
`4^l` motif occurrences without copying atoms.  Explicit level 6 exactly
expands to the independent 2,990-atom held-out disk.  Level 9 represents
1,048,576 atoms using ten node definitions.  Starting at the 746-atom
seed-equivalent level requires five hierarchy promotions, versus 499,627 flat
motif placements, a 99,925x symbolic action-count reduction.  Explicit output
remains linear and is reported separately.

## Molecular cover gate: ice Ih and ice Ic

`scripts/materials_gcts_molecular_gap_clusters.py` tests a qualitatively
different failure mode. An ice configuration is not usefully connected by
treating each atom as the center of a fixed-radius cluster. The learner accepts
only element-labelled Cartesian positions and an optional periodic metric. A
valence-bounded covalent graph finds finite connected motifs; a nearest-shell
graph between those motifs supplies connection clusters; and locally shortest
chordless cycles become centre-free void boundaries. It receives no ice label,
H2O formula, expected coordination, or expected ring size.

The live cluster gallery uses the same supports: H2O is a bent three-site
molecular face, the bridge is a two-water connection polyhedron with covalent
and hydrogen-bond edges, and the gap is the ordered six-oxygen ring boundary.
The previous centre-to-every-member spoke drawing was only a neighbor-shell
illustration and has been removed because it misrepresented all three cluster
topologies. The gallery retains every colored complete-metric class in the
observed directional cover (`1 / 3 / 33` molecule / bridge / O6-boundary
classes for Ih and `1 / 2 / 39` for Ic), while marking learning uses the three
interpretable connection families. This separates visualization vocabulary
from marking-channel count instead of conflating proton decoration with a new
physical field.

| fixture | atoms / learned molecules | molecular classes | nearest-shell connections / classes | local-girth voids / classes | tree / visible waves | exact atom cover |
|---|---:|---:|---:|---:|---:|---:|
| proton-ordered ice Ih | 216 / 72 H2O | 1 | 144 / 9 | 180 O6 / 1 | 71 / 6 | 216/216, 0 backtracks |
| proton-ordered ice Ic | 192 / 64 H2O | 1 | 128 / 6 | 128 O6 / 1 | 63 / 6 | 192/192, 0 backtracks |

The browser also separates two published D2O cases. COD 1566658 (ice VIII)
has fully occupied O/D sites and therefore admits a unique 64-molecule D2O
cover of its 192-atom `2×2×2` observation. COD 1567346 (ice VI) is a
diffraction-average, proton-disordered structure: 80 O sites are fully occupied
and 320 candidate D sites have occupancy one half. The portal preserves all
400 average sites (240 occupancy-weighted atoms), refuses to invent a unique
D2O partition, and derives 80 O4 void boundaries in two metric-isometry classes
from the fully occupied oxygen framework alone. Its growth controls and phase
classifier remain disabled until an ice-rule microstate or an explicit
occupancy-valued ensemble grammar is supplied. Thus the ordered case tests
molecular discovery, while the disordered case tests scientifically correct
ambiguity handling.

The browser now makes the next claim boundary interactive rather than hiding
it. An optional geometry-only resolver groups the 320 half-occupied D sites
into 160 two-position O--D···O alternatives and verifies degree four at every
oxygen. A seeded Euler orientation of each of the two oxygen-network components
selects one donor-side D per bond and exactly two donor bonds per oxygen,
producing a reproducible 240-atom microstate. The unresolved average remains
the default and still withholds growth. In the opt-in realization, the generic
learner finds the D2O molecular cluster, bridge clusters, and the two O4 gap
isometry classes before enabling exploratory growth. The molecular gallery
aggregates its six measured metric conformers beneath one D2O topological
atom-cover class, while the conformer distinctions remain available to the
port grammar. The seed, graph counts,
ice-rule certificates, and absence of energy/target selection enter the
receipt.

The held-out claim boundary is now measured separately. A 123-molecule crop
from one valid microstate fits five conformer types, 84 symmetry-quotiented
ports, and 20 directed type pairs. Three additional training-side microstates
select a two-parent connection-consensus threshold at `23/24 = 95.8%`
precision. A fifth microstate supplies only a spatially disjoint 23-molecule
nucleus; its outer 134-molecule crop remains unopened until both the oxygen-
anchor and whole-molecule traces are frozen. The anchor representation emits
`4 → 3 → 1` new O sites across three self-fed waves, all `8/8` exact. It retains
eight unresolved, mutually exclusive D2O pose sets. The forced whole-molecule
arm emits 21 sites, 18 correct and 3 wrong. Thus finite oxygen-framework
continuation passes, while occupational prediction, kinetic weighting,
equilibrium sampling, stationary recurrence, and exponential growth remain
unclaimed.

The H2O colored-metric signature and the O6 void signature transfer exactly
between the two polytypes; both cubic bridge classes occur in the three-class
hexagonal atlas. Atom permutation and arbitrary proper rigid motion preserve
the scientific fingerprint. With the cell withheld, both finite point sets
still produce one H2O class, one locally inferred six-member void class, exact
atom cover, and complete graph traversal; boundary occurrence counts change,
as they should, but no lattice assumption is needed. An extended covalent carbon network is rejected
instead of being relabelled as one giant molecule, leaving it to the irregular
point-set support learner. These checks run in
`scripts/test_materials_gcts_generic_ice_benchmark.py`.

The older directional hydrogen-bond audit remains in
`scripts/materials_gcts_ice_cover.py`: it records 144/128 molecular bridges
and 180/128 ring boundaries and is the smaller subset shown by the live gallery.
Both results certify reconstruction of known periodic windows, not yet blind
continuation into a larger ice crystal, prediction of proton disorder, or an
exponential ice production.

### Sealed molecular-port continuation

`scripts/materials_gcts_molecular_port_growth.py` turns the learned H2O point
set into a proper-SE(3) prototype, quotients witnessed molecule-to-molecule
poses by its proper symmetry group, and freezes 8 recurrent ports after
verifying the Bernal–Fowler one-proton-per-O–O-link rule. The
executor has no target argument. Every wave freezes its candidate digest,
checks the public boundary and exact colored exclusion geometry, and commits a
pairwise-compatible antichain while retaining the underlying tree-action IDs.

The first whole-molecule experiment exposed a useful factorization. Candidate
oxygen anchors are much less ambiguous than their attached proton decoration.
The alternative-preserving executor therefore emits the shared oxygen site
once while keeping full H2O poses mutually exclusive; an unresolved pose is
not silently materialized as several hydrogens.

| frozen grammar → sealed seed | train / seed / target atoms | whole-H2O result | factored blind wave 1 | factored wave 2 | claim |
|---|---:|---:|---:|---:|---|
| Ih → disjoint Ih | 201 / 27 / 204 | 144/219 atoms; O: 76.7% P, 94.9% outer R | 16/16 O anchors | naive 52/77; unanimous 8/8 | two exact anchor levels; then fixed |
| Ih → disjoint Ic | 201 / 15 / 213 | 143/240 atoms; O: 82.5% P, 100% outer R | 12/12 O anchors | naive 36/64; unanimous 0 emitted | exact transfer; safe fixed point |

In both rows the seed and all candidate traces are immutable before the outer
target is constructed and opened once. No cell, family label, target atom,
potential, expected coordination, or expected frontier count enters fitting or
branch generation. The exact first wave proves that the molecular connection
geometry transfers. Treating each anchor's H2O orientations as a branch domain
adds one causal rule: an exterior anchor is admissible only if every surviving
orientation of at least one parent proposes it. The same frozen candidate
geometry then gives two exact unseen Ih levels (16 followed by 8) and rejects
all speculative third-level sites. Ic conservatively stops after its exact
12-anchor transfer wave. This is finite exact anchor continuation, not yet a
stationary or exponential molecular production: the Ih wave factor contracts,
the frontier reaches a fixed point, and no proton domain is resolved. Therefore
cluster-of-clusters promotion is still refused rather than manufacturing a
symbolic amplification factor. Executable gates:

- `scripts/test_materials_gcts_ice_blind_molecular_growth_benchmark.py`
- `scripts/test_materials_gcts_ice_cross_polytype_blind_growth_benchmark.py`

The browser consumes a frozen target-free JSON artifact containing only this
prototype, its proper symmetries, the eight ports, public boundaries, and
disjoint seed poses. Its independent JavaScript executor reproduces the sealed
accepted-anchor sequences (`16, 8, 0` and `12, 0`) before Stage 4 exposes the
atoms. It displays only O anchors, keeps proton poses symbolic, reports zero
target calls, and disables clusters-of-clusters for ice. The parity regression
is `scripts/test_materials_gcts_ice_browser_anchor_growth.mjs`; no target atoms
or precomputed emitted coordinates are stored in the artifact.

The live sample selector now exposes three complementary paths: saved curated
families (including ice and intrinsic-2D controls), composition-first random
search over NOMAD, and the existing advanced local import. Database search
does not assign a structural family before growth; curated labels are explicit
benchmark metadata and remain excluded from the learner.

## Published Cd5.7Yb nested-window transfer gate

`scripts/materials_gcts_cdyb_oracle.py` is an offline standard-library port of
the published Feuerbacher V1.5 generator. It preserves the six-dimensional
projections, V/B/E occupation domains, truncations, and physical-space shifts,
and independently matches the archived NumPy notebook at ten decimal places.
The archive DOI, CC-BY-4.0 license, MD5, and SHA-256 are pinned in the module.
Artificial `Zn` empty-centre markers are excluded from the physical Cd/Yb
configuration.

`scripts/materials_gcts_nested_transfer_benchmark.py` defines the reusable
sealed protocol. A fitter receives only an inner colored point cloud; the
frozen program and that same seed are the only inputs to marked and unmarked
growth. Two larger annuli remain scorer-only. The pass gate requires complete
seed coverage including residual/gap classes, at least 99% precision and 90%
recall on both unseen annuli, 99% species accuracy, three hierarchy levels,
and a 10x marking reduction in total and failed proposals at matched recall.
It also rejects program mutation, known-region contradictions, out-of-boundary
emissions, phase-label use, and physical-potential use.

The first real-model baseline uses converged 60 Angstrom oracle geometry and a
predeclared off-centre origin `(3.1, 5.7, 8.2) Angstrom`:

| radial window | physical Cd/Yb atoms | role |
|---:|---:|---|
| 14.0 Angstrom | 506 | learner input |
| 18.0 Angstrom | 1,056 | validation annulus |
| 21.0 Angstrom | 1,672 | test annulus |

The normalized outer fixture hash is
`166e3f4b7e1588766f8b732574675b4f4563fe13a34f5ec400cc0dfac22fe9d6`.
The offset is a methodological correction, not a favorable random choice. A
crop centred on the model's global icosahedral fixed point produced many
60-fold shell orbits but almost no transfer of their exact local vocabulary;
those are global rotations, not independent translated occurrences. The
off-centre split is now primary and the centred crop is an adversarial
symmetry-bias control.

The generic cell-free support learner now uses adaptive shells only as seeds,
merges touching seeds into irregular atom collections, distinguishes complete
colored metric graphs, and performs deterministic set cover with explicit gap
classes. On the off-centre Cd--Yb seed, repeated supports cover 99.407% of the
506 atoms and one residual class makes the cover exact. With all fitting frozen,
the same support vocabulary covers 77.091% of the 550 atoms in the first unseen
annulus (99.802% of the known inner core). This is materially stronger than the
old zero-transfer adapter, but it remains recognition rather than growth.

Each learned support is additionally fitted with a centroid-local proper
rotation. Witnessed overlaps are stored as finite, species-preserving relative
SE(3) poses, quotiented by the proper colored automorphism groups of both
supports. Improper reflections, unlike-species coincidences, and near
collisions are rejected. On a greedy frozen cover of the first unseen Cd--Yb
window, 245 of 683 held-out port classes and 31.235% of witnessed overlap
relations occur in the training atlas. Corresponding weighted relation recall
is 74.576% for NaCl and 35.294% for the ideal icosahedral model set. The target
never refits types, frames, or ports.

The first causal marking is deliberately bounded: `(middle support type,
incoming oriented port)` ranks the next outgoing port, using only a previously
placed connection. Marked and unmarked arms enumerate identical candidates;
twenty within-parent label shuffles preserve all output marginals. Proposal
check reductions are only 1.025x for NaCl, 1.012x for the ideal model set, and
1.005x for Cd--Yb. The marking beats every shuffle only for NaCl. Exact context
coverage is merely 7.62% and 5.51% on the two quasicrystal cases, so this gate
is red: the predeclared gate requires at least two systems to beat every
shuffle with at least a 2x failed-check reduction. It points to the next
generic task: learn a lower-cardinality bounded
section/backoff over oriented ports, then replay frozen productions at a live
frontier. The common recursive selector still emits zero held-out Cd--Yb sites;
no representation-transfer number here is reported as autonomous continuation.

### Target-blind frontier replay

`scripts/materials_gcts_frozen_frontier_replay.py` closes an important causal
gap between vocabulary transfer and growth. Fitting detaches only proper
cluster prototypes and train-admitted overlap ports. Replay receives that
artifact, already placed occurrences, explicit residual atoms, and an optional
public radial boundary. It cannot enumerate supports or fit poses against a
target. Candidate positions are obtained only by composing a frozen relative
SE(3) port with a placed pose; held-out atoms enter the separate scorer after
the run.

The cross-family one-step gate deliberately distinguishes three questions:

| system | frozen productions | sealed candidates | greedy novel / correct | best correct atoms among the same candidates | conclusion |
|---|---:|---:|---:|---:|---|
| NaCl, 216 -> symmetric 5,832-site scorer crop | 1,424 | 33 | 1 / 1 | 6 | grammar has an exterior action; policy is weak |
| ideal IQC, 507 -> 2,229 | 896 | 0 | 0 / 0 | 0 | missing exterior production |
| off-centre Cd--Yb, 506 -> 1,056 | 11,870 | 52 | 3 / 3 | 19 | grammar has useful actions; policy and recall are weak |

The oracle column is computed only after target-blind enumeration and never
selects the replayed action. It is a ceiling on what a marking could achieve
with the exact frozen action set. NaCl uses a symmetric explicit oracle crop;
the previous positive-octant replication incorrectly penalized a valid
outward move on the omitted side. One correct action is not a continuation
pass: Cd--Yb recall is only 0.545%, and the ideal IQC cannot move at all.

### Lower-cardinality bounded port marking

`scripts/materials_gcts_bounded_port_marking.py` removes proper-prototype IDs
from the marking state and action abstraction. Its bounded local tokens use
support size and species histogram, overlap composition/count, normalized
translation, proper-rotation angle, and the incoming-to-outgoing angle in the
shared cluster frame. Exact port IDs remain the candidate actions and stable
tie-breaks. Tables are capped at two incoming ports, 32 exact states, and 64
one-port backoff states, with minimum train support 32.

Scientific scoring uses larger frozen windows, not an interleaved occurrence
split. Target relations are admitted only when their canonical pose is already
one of the train-frozen port keys. Marked, unmarked, and shuffled-label arms
have identical candidate digests.

| system | raw ports -> abstract action states | target decisions | exact / backoff coverage | mean checks marked / unmarked / shuffle median | gain over unmarked |
|---|---:|---:|---:|---:|---:|
| NaCl | 1,424 -> 468 | 352 | 1.42% / 4.26% | 113.18 / 114.20 / 114.98 | 1.009x |
| ideal IQC | 896 -> 411 | 360 | 0% / 39.44% | 26.28 / 27.86 / 26.28 | 1.060x |
| Cd--Yb | 11,870 -> 4,183 | 258 | 0% / 0% | 132.44 / 132.44 / 132.44 | 1.000x |

The IQC improvement is exactly reproduced by shuffled labels, and Cd--Yb has
no transferred marking context. The causal gate therefore stays red. The next
generic implementation target is a sparse recurring port-graph grammar:
reduce the redundant overlapping occurrence graph, mine exact port-labelled
subgraphs with SE(3) cycle consistency, promote their boundary ports, and
admit a stationary recursive production only after the normalized rule is
observed at two adjacent learned scales. Frozen target enumeration remains
scoring-only throughout that promotion loop.

### Sparse recurring port-graph macros

`scripts/materials_gcts_sparse_occurrence_graph.py` reduces the raw overlap
hypergraph before any macro is mined. Its deterministic approximation first
chooses an overlapping cover, then adds minimum-new-node witnessed connector
paths, a maximum-overlap spanning forest, and one canonical representative of
each short cycle signature. It makes no global set-cover or Steiner optimality
claim.

| system | source occurrences / undirected edges | cover + connector occurrences | retained edges | node / edge reduction | retained components |
|---|---:|---:|---:|---:|---:|
| NaCl | 576 / 24,888 | 36 + 1 | 65 | 93.58% / 99.739% | 1 |
| ideal IQC | 780 / 26,880 | 52 + 0 | 87 | 93.33% / 99.676% | 1 |
| Cd--Yb | 623 / 39,072 | 55 + 2 | 85 | 90.85% / 99.782% | 11 |

Every repeated-support atom remains covered. The Cd--Yb source graph already
has 19 connected components, so the retained graph cannot become connected
without unsupported edges; eleven components remain.

`scripts/materials_gcts_port_graph_macros.py` mines rooted connected induced
subgraphs of this sparse graph. A cheap graph code is only a bucket: retained
classes must agree under exact directed port-labelled graph isomorphism and
under root-symmetry-canonical full colored SE(3) geometry. Observed poses also
close every internal edge composition. Evidence requires at least two macro
atom unions with at most 10% overlap and positive structural-token MDL saving.

| system | sparse directed edges | positive-MDL two-child macro types | largest atom union | largest MDL saving | maximum cycle residual |
|---|---:|---:|---:|---:|---:|
| NaCl | 130 | 3 | 18 | 2 tokens | 1.49e-15 |
| ideal IQC | 174 | 42 | 35 | 11 tokens | 4.47e-15 |
| Cd--Yb | 170 | 2 | 40 | 2 tokens | 2.28e-15 |

Each `MacroType` stores child placements, exact colored atom union, internal
ports, boundary slots with occurrence frequency, and independent occurrence
proofs. This is the first generic cluster-of-clusters representation in the
new pipeline. It is not yet recursion: macro types are not yet fed back as
nodes, structural tokens are not entropy-coded bits, and canonicalization is
currently bounded to five nodes.

### Stationary recursive-production contract

`scripts/materials_gcts_stationary_port_graph_contract.py` defines the sealed
gate for the next pass. Compilation sees only a finite colored Cartesian cloud;
execution sees only the frozen program and seed; two held-out point clouds enter
the scorer afterward. A pass requires exactly one production kind,
`recurring_port_graph_macro`, across crystal, ideal-IQC, and Cd--Yb roles, plus:

- the same normalized production and learned similarity at two adjacent
  observed promotion levels;
- complete training cover, at least 95% repeated coverage, finite oriented
  ports, carried causal marking, and self-fed execution;
- exact species/position output for the first two unseen levels and independent
  reconciliation of explicit and symbolic unique-site counts;
- strictly greater than 3x represented-site growth for three consecutive
  actions and at least one million represented sites by action seven;
- permutation/proper-SE(3) invariant program signature, equivariant output,
  clean leakage audit, and deterministic rejection of an amorphous control.

The callback-based contract has passing and deliberately failing harness tests,
but the current macro miner does not yet implement those callbacks. Therefore
the stationary/exponential gate remains explicitly red.

### Recursive macro-as-node promotion with exact support quotient

After the unchanged positive-MDL admission gate,
`scripts/materials_gcts_promoted_type_quotient.py` groups only colored atomic
supports that are exactly congruent by a proper rigid motion. It selects a
deterministic minimum-dictionary representative and retains every unique exact
training support for promotion. It does not pool duplicate derivations into
extra MDL evidence. Improper mirrors, changed chemistry, and uniform-scale-only
similarity remain distinct; the latter cannot be merged while occurrences
carry SE(3) poses without an explicit scale.

The callback order is explicitly sparse/disjoint admission, optional dense
exact matching over the frozen training graph, exact-support quotient, then
promotion. Dense deployment is disabled in the default cross-family timing
run until the IQC matcher is scalable; enabling it changes deployment support,
never the admitted types, their disjoint evidence, or their MDL scores.

`scripts/materials_gcts_macro_promotion.py` then turns each quotient `MacroType`
into the next level's ordinary oriented node. The exact colored atom union is
recentered into a prototype and its proper rotational automorphism group is
learned. Every macro occurrence is independently re-rendered from its child
poses and fitted back to the prototype; atom-index unions remain explicit.
Only training macro pairs with witnessed shared atoms enter the overlap atlas.
Cross-boundary child-port witnesses form a separate finite boundary atlas, so
non-overlapping adjacency is carried without pretending that it covers atoms.

| system | admitted types | exact quotient types | occurrence records / unique exact supports | fit failures |
|---|---:|---:|---:|---:|
| NaCl | 3 | 2 | 6 / 4 | 0 |
| ideal IQC | 75 | 32 | 198 / 87 | 0 |
| Cd--Yb | 2 | 1 | 4 / 2 | 0 |

The promoted program exposes the same prototype/occurrence/support/atlas
contract as the primitive program. `scripts/materials_gcts_recursive_port_hierarchy.py`
therefore applies the unchanged sparse reducer and exact macro miner repeatedly,
stopping when no positive-MDL macros remain:

| system | source types by level | admitted macros | quotient macros | representative MDL saving | largest support reached | termination |
|---|---:|---:|---:|---:|---:|---|
| NaCl | 7, 2 | 3, 0 | 2, 0 | 4, 0 | 18 | no positive MDL |
| ideal IQC | 13, 32, 9 | 75, 22, 0 | 32, 9, 0 | 139, 21, 0 | 94 | no positive MDL |
| Cd--Yb | 91, 1 | 2, 0 | 1, 0 | 2, 0 | 40 | no positive MDL |

Thus the exact quotient substantially removes duplicate execution dictionaries
without changing the admitted evidence or the covered training supports. The
ideal IQC still exhibits two learned compression levels; NaCl and Cd--Yb stop
after one. None is yet an exponential certificate.

`scripts/materials_gcts_stationary_production_signature.py` supplies the
strong comparison that prevents a raw pose-key coincidence from becoming a
stationary claim. It canonicalizes a connected finite-child production modulo
global proper SE(3), child order, declared proper child gauges, and one inferred
uniform translation scale. It preserves child chemistry and chirality,
relative rotations, directed port incidence, overlap chemistry, and boundary
direction/outside chemistry. Stationarity requires three consecutive observed
levels, two matching adjacent comparisons with the same learned scale,
independent low-overlap occurrences, positive MDL saving, and train-only
provenance.

Controls for a single repeated scale, disconnected copied patches, perturbed
amorphous geometry, nonuniform dilation, an improper mirror, changed chemistry
or chirality, and reversed port direction all stay red. The real adapter can
certify individual chemistry/chirality-preserving production signatures, but
the learned hierarchies do not supply three consecutive positive levels with a
single common production and equal learned adjacent scales. Consequently all
real stationary witness counts are zero and the million-site gate remains red.

### Learned stationary crystal control

`scripts/materials_gcts_crystal_stationary_benchmark.py` supplies the positive
control without receiving a unit cell, axes, a space group, a material-family
label, a radix, or a target scale. From the colored point cloud and the admitted
irregular-support occurrence graph, it finds three independent recurring
species-preserving translations. It then infers an integer radix and the
complete child-offset set only when the same nested production is witnessed at
three scales in each of two independent training configurations and improves a
two-part description length.

For NaCl, a 216-atom discovery subset and two 1,024-atom training samples yield
three generators, radix 2, eight child offsets, scale 2, and population
substitution matrix `((8,),)`. The frozen rule recursively materializes two
separate held-out configurations with one-to-one species/position equality: 16
sites at the first level and 128 at the second. Seven symbolic applications
represent 4,194,304 sites from the two-site motif. A ternary synthetic control
independently infers radix 3 and 27 children, guarding against a hidden binary
octuplication constant. The identical pipeline rejects the ideal IQC and an
amorphous cloud because neither has three independent recurring colored
translations. This closes the learned *crystal* stationary benchmark; it does
not close the generic quasicrystal benchmark.

The hardened full-relation audit asks whether that learned crystal vocabulary
is also supported by the generic oriented-port representation. A single sparse
216-atom presentation remains evidence-starved: exact width-eight search admits
only six size-two macros. The confirmatory audit therefore uses two independent
bounded 216-atom presentations. Their complete learned relation graph has
29,988 relations joining 52 cells and admits maximum child width eight. The
exported macro has 8 children, 24 directed ports, a 52-atom colored union, 2
atom-disjoint occurrences, and structural MDL saving 30.

The relation program is frozen before recursive replay. Across three learned
factors the independent witnessed-relation totals are `1,478 / 750 / 86`; the
strong chemistry, chirality, directed-incidence, exact-population, and
stationarity contract accepts the common production with learned scale 2.
Input permutation and global proper-SE(3) metamorphic tests pass, as do the
ideal-IQC, amorphous, and ternary controls.

One limitation remains explicit. The radix and child-offset vocabulary is
proposed by the positions-only stationary grid learner and then validated
against frozen port relations. A pure-port learner that discovers this closure
vocabulary without the grid proposal is future work. The certificate therefore
strengthens the separate crystal baseline without changing the red generic IQC
stationarity result.

### Sparse evidence, dense deployment, and the current marking result

`scripts/materials_gcts_dense_macro_matching.py` preserves the nearly
atom-disjoint sparse occurrences as recurrence/MDL evidence, while finding all
exact proper-SE(3) deployments of admitted macro types for execution. This
separation prevents abundant overlapping placements from manufacturing
recurrence evidence. On the 507-atom ideal-IQC training configuration, a
one-macro seed produces 16 accepted placements and 86 / 86 correct novel atoms.
Because the same configuration supplied the dense matching geometry, this is a
target-blind reconstruction test, not a held-out continuation result.

The dense NaCl reconstruction exposes genuine policy headroom. A bounded
train-frequency connection score reaches the matched correct output with fewer
proposals and higher precision than the unmarked ordering, but it does not beat
31 within-parent shuffled-label controls: its wrong-placement-plus-backtrack
work has empirical `p = 0.40625`. The causal GCTS-marking gate therefore stays
red. A future pass must fit the support grammar, dense deployments, and marking
on a genuinely disjoint training domain, enumerate the same frozen actions in
every arm, and beat both the parent-only baseline and shuffled controls on an
unseen outward frontier.

### Spatially disjoint IQC continuation and confirmatory marking

The next gate removes the fitted-geometry ambiguity. The exact IQC oracle is
used only to prepare immutable colored Cartesian crops; no lift, family label,
cell, golden-ratio value, or target site crosses into the learner. A sphere of
radius 11 about `(-16, 0, 0)` supplies 887 training atoms. A radius-7 sphere
about `(5, -17, 4)` supplies a 231-atom seed, while its radius-11 extension is
reserved for scoring. The training and scoring crops have zero raw atom IDs in
common, their centres are 27.313 units apart (greater than the sum of their
radii), and their squared norms differ, so no origin-fixing proper rotation
maps one benchmark centre to the other.

`scripts/materials_gcts_frozen_frontier_replay.py` now uses an incremental
27-cell spatial index, occupied-site map, pose set, and lazy port-orbit cache.
Exact brute-force parity covers candidate identity, action order, and replay
certificates. On the earlier exploratory disjoint patch, the frozen primitive
grammar grows target-blind from 223 atoms:

| actions | proposed atoms | correct atoms | precision | held-out recall |
|---:|---:|---:|---:|---:|
| 1 | 2 | 2 | 100% | 0.31% |
| 10 | 23 | 21 | 91.30% | 3.21% |
| 100 | 266 | 201 | 75.56% | 30.73% |

Thus the primitive irregular grammar really has unseen exterior actions, but
unmarked precision decays. The densely promoted macro grammar remains a useful
negative control: all 3,144,240 composed IQC proposals reproduce already known
poses, so it has no exterior action yet.

`scripts/materials_gcts_confirmatory_action_consensus_benchmark.py` freezes a
simple rule after that exploratory patch: rank an entire cluster placement by
the sum of normalized train-production frequency and the minimum live support
for any atom it would emit. Live support counts distinct candidate poses, so it
is a finite GCTS connection/overlap marking rather than a potential. The rule,
100-action budget, candidate geometry, and 31 degree-preserving bipartite
incidence shuffles are frozen before the confirmatory target crop is built. A
public radius-11 boundary censors unscored exterior proposals before labels.

| confirmatory arm | exact actions in first 100 | wrong emitted-site counts | work to recover the same 177 correct sites |
|---|---:|---:|---:|
| frequency + GCTS consensus | **97** | **4** | **99 proposals + 3 backtracks** |
| frequency only | 90 | 14 | 145 + 24 |
| consensus only | 95 | 6 | 240 + 44 |
| 31 degree-preserving shuffles | at most 93 | at least 9 | best total 151 |

Exact-action, wrong-site, and matched-work empirical p-values are each
`1 / 32 = 0.03125`. This is the first sealed result in this pipeline where the
GCTS marking itself significantly improves whole-cluster search ordering.
Invalid actions are scorer-labelled for the ablation; it is an ordering test,
not a claim that every wrong proposal is immediately observable online.

`scripts/materials_gcts_batch_frontier_search.py` supplies the corresponding
target-free executor. Each wave freezes the current candidates, computes
whole-placement consensus, and commits a mutually compatible antichain; only
those accepted occurrences feed the next wave. With the strict action-level
threshold ratio `15 / 21` learned on the training patch, the confirmatory run
accepts `3, 17, 4, 30, 5` clusters over five waves and emits 109 / 109 exact
novel atoms (16.62% held-out recall). Fixed diagnostic thresholds expose the
trade-off: zero threshold emits 409 / 435 correct, while 0.5 emits 312 / 320.
The exact five-wave result is genuine self-fed finite continuation. Its
nonstationary wave counts do not certify exponential growth; promotion of
these accepted action graphs is the next clusters-of-clusters gate.

`scripts/materials_gcts_action_macro_promotion.py` now performs that promotion
without a scorer. It renders every accepted occurrence, joins nodes through
exact colored overlap or a witnessed shared-parent attachment, splits connected
components, and records proper-SE(3) child poses, colored unions, overlap and
frozen-boundary certificates. On the exact five-wave confirmation, 59 accepted
placements become eight action macros with child counts
`3, 17, 3, 1, 26, 4, 4, 1`. All eight exactly cover their accepted nodes and
pass union, overlap, boundary-port, and antichain audits. Six nontrivial
components admit stationary canonicalization; each normalized key occurs in
only one wave. The three-wave recurrence count is therefore zero and no scale
law is claimed. A synthetic control accepts three translated congruent waves
and rejects a noncongruent third wave, verifying that this red IQC result is not
caused by a promoter incapable of detecting recurrence.

### Canonical IQC hierarchy: action history versus atomic re-clustering

The action-history route remains a useful negative baseline. Exact connected
subgraphs retain colored unions, directed port incidence, and
symmetry-quotiented proper-SE(3) relative poses. With the corrected invariant
canonicalizer it admits 11 types; every type has maximum dense multiplicity two,
and promotion reaches only two positive levels. Previously reported
action-history counts are superseded and must not be used as the current
recursion evidence.

The stronger history-free route re-clusters the atoms after growth instead of
requiring a repeated move history. Six patch-local clouds contain 2,064 atoms.
Seventy-eight repeated irregular support types have 1,122 occurrences; explicit
gap clusters cover the remaining atoms, giving a complete cover. No action ID,
material-family label, unit cell, or target enters discovery. Boundary-aware
recursive promotion produces:

| route | exact-support quotient types by pass | claim |
|---|---|---|
| one representative per geometry class | `73 -> 17 -> 5 -> 3 -> 2 -> 1 -> 0` | six positive train-compression levels |
| mutually exclusive exact derivations retained | `73 -> 17 -> 6 -> 3 -> 2 -> 1 -> 0` | more exact alternatives, same depth |

The strict production comparison successively audits topology/arity, species
identity and decoration chirality, directed port semantics, normalized proper-
SE(3) poses, and exact nonnegative-integer population substitution. No common
production survives the required three consecutive levels with equal learned
adjacent scales. Stationarity therefore remains red despite the deeper train
compression.

### Sealed re-encoding of the history-free hierarchy

Eight predeclared, mutually raw-ID-disjoint grown patches are split five for
training and three for heldout scoring. Frozen primitive supports cover all
1,248 / 1,248 held-out atoms, including explicit gaps. At the first promoted
level, 256 of 259 frozen quotient types replay and their exact unions still
cover every held-out atom. The three absent IDs are `184`, `185`, and `252`.
All three require primitive type 49, a 23-atom support with exactly two training
occurrences, both in patch 2 near the public crop boundary, and zero heldout
occurrences. Their associated port relations therefore have no heldout witness.
This is a rare patch-local boundary/crop artifact and insufficient independent
multiplicity. It is not a failure to try the right exact derivation: the frozen
semantic mapper tests every train-fitted alternative, preserves its exact
action-terminal identity, has zero ambiguous atom unions and exact assignment
precision 1.0, but remains at 256 / 259 types. No heldout atom is novel to the
primitive support vocabulary.

This separates three claims that should not be merged:

| claim | status |
|---|---|
| train compression on re-clustered grown atoms | green through six positive quotient levels |
| primitive heldout support/atom coverage | green, 1,248 / 1,248 |
| unfiltered promoted type map | red; 3 / 259 level-one types are patch-2-only boundary artifacts |
| strict-majority recurrent-core re-encoding | green through four exact levels, with explicit residual terminals |
| autonomous continuation and stationary/exponential growth | red; heldout positions are observed and stationary witnesses remain zero |

The production policy now fails closed on patch-local artifacts. A generic
train-only recurrent-core selector retains an exact quotient macro only when it
occurs in a strict majority of the five independent training namespaces
(`3 / 5`). Repeated occurrences inside one patch cannot satisfy the gate,
cross-patch occurrences are invalid evidence, and the original macro IDs and
exact action terminals are never renumbered. Atoms not represented by the
selected core are exported as exact `(patch, raw index, species, position)`
terminals. The core plus those terminals has a coordinate/species SHA
certificate equal to the complete atom cloud.

The main width-five audit freezes the learned training vocabulary—including
supports, ports, quotient types, and exact derivation alternatives—then
**re-encodes** the three fully observed heldout patches without refitting:

| recursive level | raw -> selected/exact types | exact occurrences | exact core atoms / 1,248 | residual atom terminals | minimum heldout namespaces | maximum support atoms |
|---|---:|---:|---:|---:|---:|---:|
| 1 | `520 -> 148` | 1,495 | 1,220 | 28 | 2 | 78 |
| 2 | `53 -> 10` | 85 | 1,033 | 215 | 3 | 78 |
| 3 | `16 -> 4` | 29 | 925 | 323 | 3 | 110 |
| 4 | `3 -> 1` | 9 | 870 | 378 | 3 | 111 |

Every selected type has at least two exact proper-SE(3) heldout occurrences,
and the residual certificate makes every level a complete representation.
However, the matcher receives all 1,248 heldout positions: heldout geometry is
observed to enumerate and match types, while only the learned vocabulary is
frozen. These numbers are therefore frozen-vocabulary representation
transfer, not target-blind proposal, continuation, or material growth.

The selected hierarchy has no action amplification above three, no normalized
stationary production key common to three consecutive levels, and no evidence
of a self-fed exterior executor. Accordingly `autonomous_growth = false` and
`exponential = false`; the IQC gate remains red. The separate learned NaCl
stationary crystal control is unchanged.

### Target-blind recurrent-macro continuation

The re-encoding result above is no longer the strongest executable IQC claim.
A separate sealed benchmark trains on five mutually raw-ID-disjoint **raw IQC**
radius-11 windows (4,405 atoms), rather than on patches produced by an earlier
growth policy. The generic width-three miner yields 322 exact first-level
macros; the train-only strict-majority gate retains 141, represented by 844
training occurrences, 5,886 overlap ports, and 5,820 witnessed boundary ports.

The evaluation window is centered at `(40, 0, 0)` and shares no raw atom ID
with the five training windows. Its radius-7 seed contains 226 atoms. Frozen
support enumeration and exact macro fitting find two placed first-level macro
occurrences; all seed atoms, including those outside those macro supports,
remain explicit collision constraints. The executor has no target or ranker
callback. It composes only frozen port orbits with the preceding placed
frontier, rejects improper poses, unlike-species coincidences, sub-minimum
collisions, insufficient overlap, and positions outside the public radius-11
boundary, then commits compatible whole macros. Every accepted placement
carries an overlap-inclusion and train-witnessed-adjacency certificate.

| wave | eligible whole macros | accepted | emitted atoms |
|---:|---:|---:|---:|
| 1 | 44 | 16 | 92 |
| 2 | 18 | 8 | 56 |
| 3 | 0 | 0 | 0 |

The 873-atom scoring crop is opened only after the proposal trace is frozen.
Of 148 proposed novel atoms, 136 are exact species/position matches and 12 are
wrong: precision is 91.89% and recall over the 647 atoms outside the seed is
21.02%. Candidate batches have immutable SHA digests, all 24 acceptances are
self-fed clusters-of-clusters actions, and target use during proposal or
ranking is false. Thus autonomous macro continuation is now implemented and
measured, but the gate remains red. A scheduling audit shows that “number of
waves” is not a scientific depth measure: lowering the per-wave batch cap from
40 to 8 changes `16 -> 8 -> 0` into `8 -> 8 -> 8 -> 0`, while producing the
identical 148-atom union. The invariant parent-child DAG has causal depth two
and reaches a finite fixed point. Precision is below 99%, recall is far below
95%, and there is no recursive amplification.

The first matched marking audit now labels every eligible proposal on five
train-only radius-7 to radius-11 frontiers, rather than fitting only accepted
connections. This supplies 718 actions (693 valid and 25 invalid) and freezes
310 bounded order-two log-odds states. All 33 evaluation arms share the same
44 first-wave candidates, and every trace is frozen before the target factory
is opened. However, all 62 evaluated commit candidates have unseen marking
contexts: exact transfer is 0, parent/production backoff transfer is 0, the
first wave has one score and zero rank inversions. Marked and unmarked both
emit 148 atoms with 136 correct; all 31 within-parent label shuffles tie and
give empirical `p = 1`. The causal macro-marking gate therefore remains red
for a precise reason: the present marking vocabulary does not transfer from
internal training frontiers to the exterior evaluation roles.

An ID-free quotient now addresses that exact failure without changing the
candidate geometry. Its hierarchy uses a symmetry-canonical port-pose key,
then `(connection kind, overlap-species set)`, then a kind-only marginal. Bin
widths are chosen by leave-one-training-patch-out log loss over nine fixed
schemas. Coverage rises from zero to all 62 evaluated candidates: 16 use the
full incident context, 14 the pose-only backoff, 30 the overlap-chemistry
backoff, and 2 the kind marginal. It creates five distinct first-wave scores
and 112 pairwise rank inversions. The final atom set is still 136 / 148, while
matched exact-action work falls from 71 to 51; with 31 label shuffles the
empirical result is only `p = 0.25`, so it is useful compression but not yet a
causal marking win.

A second, continuous mark now uses 35 ID-free proper-SE(3) invariants: prototype
composition, radial/pair moments and proper-symmetry counts; normalized port
translation/rotation and overlap chemistry; live overlap/emission fractions;
train evidence; at most two incoming-port summaries; and live proposal-witness
and emitted-site-consensus statistics. Ridge strength is
selected only by five-fold spatial training validation. Its log loss is
`0.0186` versus the global prior's `0.1511`; the unopened evaluation frontier
gets 29 distinct first-wave scores and 362 rank inversions. Yet unpruned
execution again produces 136 / 148. A threshold frozen from out-of-fold
training at 100% precision/recall prunes to 14 macro placements but produces
134 correct and the same 12 wrong atoms (91.78% precision). Some shuffled
threshold arms emit no shared correct atom, so matched work is explicitly
incomparable rather than selectively dropping those controls. This exposes a
train-to-exterior calibration shift; neither mark is integrated as the
default policy.

Uniformly jittering the five training nuclei is not the remedy. Thirty
predeclared ±1-nearest-neighbor shifts yield 25 executable frontiers and grow
the training table from 718 to 3,119 candidates, but failures rise only from
25 to 30. Evaluation parent-role coverage remains 0 / 62 and the median
standardized role distance remains 5.32. The apparent validation improvement
is positive duplication, while projected score spread contracts. This
augmentation is rejected; the next sampler must maximize train-only role and
failure diversity explicitly.

That sampler is now implemented. It enumerates 596 patch-specific
boundary-exposed representatives and selects a geometry-only cover of all 141
learned parent macro types before candidate labels exist. The result rules out
simple role omission: every one of the 48 incorrect sealed candidate actions
uses an exact `(parent type, production)` pair observed as correct in the
training windows. Ranking therefore cannot infer failure from rule identity.
Inward-prefix contexts and class balancing change work order but do not remove
the errors; a fifth-patch threshold rejects correct actions instead.

The terminal-level diagnosis is sharper. Eight of the 12 final wrong atoms
sit at exact target coordinates but carry `Y` where the sealed target carries
`Z`; four proposed `Z` sites are absent, one nearest-neighbour spacing from the
closest target site. Thus the remaining error is mostly context-dependent
chemical decoration of otherwise useful geometry. A bounded colored-site
section uses only the proposed species plus rotation-invariant local neighbour
distances. Four patches provide 3,047 deduplicated terminal records, only ten
of which are recolor/absence cases; the fifth patch freezes the alternative
margin at 100% precision and recall. Before the sixth target is opened, the
section predicts four recolors and ten absences. Posthoc scoring is worse:
124 correct and 16 wrong atoms, 88.57% precision. This is retained as an
honest red diagnostic and is not integrated into self-fed execution. The next
marking representation must learn reusable decoration alternatives at the
cluster/cluster-of-clusters level rather than postprocess isolated sites.

That geometry-first representation is now explicit. The learner hides all
species labels while fitting 35 irregular geometric support types from the
4,405-atom training corpus, then attaches the observed colored decorations
modulo each support's proper rotational symmetry. The factored vocabulary has
275 exact decoration alternatives; 29 / 35 geometry types have more than one.
On the disjoint 873-atom window, every geometry type transfers and supports
cover 841 atoms (96.33%). Train-seen decorations cover 795 atoms (91.07%),
although only 706 / 4,519 frozen occurrences have their exact decoration in
training. Expanding the alternatives naively would produce 49,735 colored port
classes, versus 7,731 factored geometry ports for the same 778,380 witnessed
relations, a 6.43-fold vocabulary penalty.

The first bounded GCTS decoration section uses one or two already-inward
overlap ports. On a common heldout causal sample, two-port composition predicts
30.37% of decorations, versus 25.79% for one port and 20.34% for the modal
geometry decoration. This apparent gain is not yet causal evidence: 31
within-geometry label shuffles have median accuracy 31.81% and give
`p = 0.875`. The marking gate therefore remains red.

An overlap-cover solver now tests the alternatives jointly. The complete
heldout positions are supplied, the radius-7 seed contributes 226 known
species, and all 647 outer species stay sealed until scoring. All 4,519 frozen
geometry occurrences are optional covering proposals. A proposal may
propagate only after overlapping an already labelled atom, and only labels
unanimous across its remaining train-observed alternatives are committed. The
solver retains geometry over 831 / 873 atoms and infers 279 outer labels: 267
are correct and 12 wrong, for 95.70% precision and 41.27% recall. It is a
reconstruction baseline, not autonomous coordinate growth; the unchanged 99%
precision / 90% recall gate remains red. The next step is bounded branch-and-
backtrack selection among exact decoration alternatives, with marking used to
order identical candidate sets.

That bounded search is now executable. It freezes 55,483 exact actions—one
geometric occurrence, one train-observed decoration, and one proper rotational
gauge—and exposes no target-species argument. A beam state stores only seed or
committed species and selected occurrences; unlike-species overlap prunes the
branch. Every arm receives the identical candidate SHA. With a predeclared
six-atom overlap and 99% train-posterior threshold, the GCTS connection policy
finds 354 correct labels among 415 inferred outer atoms (85.30% precision,
54.71% recall). The modal arm finds only 116 / 140 (82.86% precision, 17.93%
recall). All 31 within-geometry label shuffles collapse to the modal result, so
both precision and correct-atom comparisons give `p = 0.03125`. This is the
first significant evidence that learned GCTS ranking/admission improves the covering
search over identical cluster alternatives. It is not a reconstruction pass:
61 labels remain wrong and the 99% / 90% gate stays red.

The first geometry-first cluster-of-clusters decoration audit also prevents a
misleading shortcut. Width-three mining admits 1,263 macros and exact geometry
quotienting retains 457 types with 18,660 dense train occurrences and 15–55
atoms per support. On a deterministic sparse heldout primitive cover, only 12
macro geometry types / 13 occurrences transfer, covering 254 atoms. The train
vocabulary contains 1,229 whole-macro decoration alternatives, but none of the
13 heldout macro decorations is train-seen. Treating a whole macro's chemistry
as its identity therefore increases memorization rather than transfer.

Using macro geometry only as a bounded mark on each primitive child is better
but still red. `(macro type, child role)` covers all 27 transferred child
samples and predicts 5 / 27 decorations, versus 2 / 27 for the primitive modal
baseline. Thirty-one within-primitive-type shuffles reach as high as 6 / 27;
the learned result has `p = 0.1875`. The next hierarchy representation must
retain exact child decoration alternatives while quotienting the macro boundary
mark more coarsely than exact macro type/role. Full promoted-atlas construction
was also removed from this audit: an atom-inverted exact overlap index and
lightweight prototype/pose deployment avoid an unnecessary multi-gigabyte
all-pairs port expansion.

A train-selected lower-cardinality macro-boundary key does not rescue the
ideal-IQC chemistry. Leave-one-patch-out selects a `boundary_fine` descriptor
from child geometry, macro arity, graph degree, boundary incidence/direction,
normalized radial role, and support-size ratios; it contains no macro or
occurrence ID and no world pose. It still predicts only 5 / 27 heldout child
decorations (`p = 0.125` against 31 within-child-type shuffles). Combining all
boundary marks per unique child gives 3 / 19 (`p = 0.21875`). The exact
alternative ceiling explains much of the failure: only 9 / 27 role samples and
7 / 19 unique children have their correct full decoration anywhere in train.

Factorizing a decoration into a maximum-information tree of unary and pairwise
site sections can emit unseen combinations, but unconstrained composition is
also insufficient. On ideal IQC it raises heldout exact occurrence accuracy
only from 4.96% to 5.44% and site accuracy from 68.68% to 69.78%; 811 predicted
whole decorations are unseen in train and none is exactly correct. The partial
section is retained as an honest red generator, not added to search.

### Published Cd--Yb disjoint reconstruction

The same generic geometry/decoration pipeline now has a stronger real-material
test. Two predeclared, mutually disjoint radius-14 crops of the published
Cd5.7Yb model provide 969 train atoms; a third radius-14 crop, at least 30.55
angstrom from either train centre, provides 478 evaluation atoms. The learner
receives positions/species only—no cut-and-project coordinates, source-site
labels, family name, cell, or physical potential. With species hidden during
geometry fitting, 166 support types and 713 frozen evaluation occurrences
cover 449 / 478 atoms (93.93%). This is a large improvement over the earlier
single 506-atom crop's 277 / 478 (57.95%) coverage. Whole-decoration modal and
pair-factor models both reach 66.20% exact occurrence and 94.57% site accuracy;
the remaining 29 explicit singleton gap clusters are only 27 / 29 correct
under a bounded radial/nearby-cluster KNN mark.

Joint covering search resolves that ambiguity much more strongly than
independent classification. A radius-7 colored seed contains 59 atoms. Every
arm then receives the same 1,385 exact actions formed from 713 frozen geometry
occurrences and 174 train-observed decoration alternatives. With a five-atom
overlap and 99% train-posterior threshold, GCTS reconstructs 378 / 378 novel
atoms exactly: 100% precision and 90.21% recall over the 419-atom outer region.
The modal arm and all 31 within-geometry label shuffles reconstruct 377 / 377,
for 89.98% recall. Precision is at 100% for every arm; the meaningful causal
comparison is extra correct reach at no precision loss, where GCTS gives
`p = 0.03125`. Thus the unchanged 99%-precision / 90%-recall reconstruction
gate and the matched-quality GCTS marking gate are green on a published
icosahedral material model. Coordinates are supplied and the search reaches a
finite fixed point, so autonomous continuation, stationary recurrence, and
exponential growth remain red.

### Published Cd--Yb autonomous frontier continuation

Reconstruction no longer supplies the outer coordinates in this follow-up.
The two 969-atom training crops fit 175 colored irregular cluster types, 804
occurrences, and 14,595 finite proper-SE(3) overlap ports. Six candidate
consensus thresholds are evaluated only on radius-7 to radius-14 training
reconstructions. Threshold 0.6 is the highest-reach choice for which both
training windows retain at least 99% precision (both are in fact exact).

The frozen grammar then sees only the disjoint 59-atom colored seed and a
public radius-14 boundary. Six recognized clusters cover 49 seed atoms; ten
explicit singleton gap clusters complete the seed. All evaluation executions
finish and their candidate/action/site digests are frozen before the 478-atom
target factory is called. Five self-fed waves accept
`3 -> 18 -> 9 -> 35 -> 7` complete clusters and emit 179 novel coordinates;
the scorer finds 177 correct and 2 wrong, or 98.88% precision and 42.24% recall
over the 419 outer atoms. An unfiltered diagnostic emits 366 atoms and reaches
68.26% recall at 78.14% precision, while strict consensus emits 19 / 19 at
only 4.53% recall. This makes the bounded finite-autonomous continuation gate
green without hiding its precision/coverage trade-off.

The selected target-free trace also feeds the cluster-of-clusters loop.
Commuting wave placements become colored action macros with exact node cover,
proper poses, colored unions, overlap intersections, frozen incoming ports,
and antichain certificates. No normalized action-macro production recurs over
three waves. Continuing the same threshold past the calibrated five waves also
accumulates errors. The result is therefore finite autonomous real-material
continuation, not sustained stationarity or exponential symbolic growth.

### Bounded local section and causal growth ablation

The first autonomous errors are locally valid port applications, so raw
production identity and prototype-size envelopes do not transfer reliably.
The improved marking uses the local frontier itself. For every candidate it
measures the closest proposed-site distance to the already placed cloud in the
training-derived nearest-neighbor unit and counts distinct frozen
cluster-connection witnesses for the same pose. Among the 390 train-selected
candidate samples, the distance distribution has a train-fitted gap at 2.118
nearest-neighbor units. On its close side, the minimum witnessed correct action
has five independent connections. The frozen section therefore rejects a close
proposal with fewer than five witnesses. It neither generates coordinates nor
uses absolute position, direction, family, cell, potential, source-site label,
or evaluation target.

The original evaluation nucleus now executes
`3 -> 18 -> 9 -> 35 -> 5 -> 1 -> 0` placements and emits 178 / 178 correct
atoms (100% precision, 42.48% outer recall). A second predeclared radius-14
nucleus at `(-15, 10, -15)`, disjoint from both training crops and the first
evaluation crop, executes `2 -> 12 -> 6 -> 4 -> 10 -> 14 -> 0` and emits
117 / 117 (100% precision, 27.73% recall). The corresponding unmarked runs
emit 193 / 220 and 168 / 224, for 83 false atoms in aggregate.

The causal null preserves every frozen candidate and, separately within each
wave, the complete witness-count multiset, but permutes witness counts among
placements before the scorer is opened. All 31 shuffled policies run their
full self-fed consequences on both nuclei. None reaches the learned section's
295 correct atoms at zero error (`p = 0.03125`). Thus finite autonomous
continuation, transfer across two nuclei, and the matched GCTS-marking gate are
green on the published Cd--Yb model. Target-free promotion certifies the
resulting action macros, but no normalized production recurs across three
waves; sustained stationary and exponential quasicrystal growth remain red.

An extended radius-25 diagnostic from the same first-wave candidate batch emits
416 atoms over three waves and matches 374 (89.90% precision), but 39 scoring
atoms overlap a training window. It is retained only as a depth diagnostic and
is not a sealed result.

### Deep Cd--Yb hierarchy and frozen transfer boundary

The history-free cluster-of-clusters loop now has a substantially larger
real-material corpus. Five mutually disjoint radius-14 crops of the published
Cd5.7Yb model contain 2,385 atoms. Each crop is recentered and packed into a
separate 80-angstrom namespace before learning, which prevents a support or
port from joining nearly touching crop boundaries. The positions/species-only
cover is complete: 2,360 atoms belong to recurring irregular supports and 25
are explicit gap terminals. It learns 274 primitive support types, 1,697
occurrences, and 21,056 finite proper-SE(3) ports.

Exact macro mining, derivation quotienting, and promotion then produce nine
positive levels:

`80 -> 36 -> 22 -> 15 -> 8 -> 6 -> 4 -> 2 -> 1 -> 0`.

The largest exact colored support rises from 67 to 472 atoms. Every admitted
macro has at least two low-overlap proof occurrences and every occurrence is
confined to one crop namespace. At level one, 79 / 80 retained quotient types
are witnessed in at least two disjoint windows; the remaining type is confined
to one. Every retained type at the later positive levels has two-window
evidence. The five windows are distinct exact configurations, although
disjoint atom domains alone do not imply statistical independence. The loop
terminates at evidence exhaustion. This is genuine deep clusters-of-clusters
compression, not a visible extra pipeline stage. The exact nine-level depth is
deterministic on this packed corpus; robustness to resampling and positional
perturbation has not yet been established.

The unchanged strict stationarity audit remains red. No production key is
shared across three consecutive levels; the first failing field is already
child-count/topology, before chemistry, directed ports, normalized proper pose,
scale, or population substitution can rescue it. Declining support-growth
ratios and eventual crop saturation are not labelled exponential growth.

A separate frozen audit observes two reserved, mutually disjoint radius-14
windows containing 959 atoms. It does not refit or renumber the training
grammar. A finite region need not instantiate every symbol in a grammar, so
the corrected deployment keeps the complete frozen type/port vocabulary while
allowing absent types to remain dormant. Only exact active occurrences can
seed the next level; dormant symbols are never counted as transferred.

| level | frozen types | active types | dormant types | active occurrences | covered atoms |
|---:|---:|---:|---:|---:|---:|
| 1 | 80 | 53 | 27 | 92 | 560 / 959 |
| 2 | 36 | 20 | 16 | 26 | 445 / 959 |
| 3 | 22 | 8 | 14 | 8 | 314 / 959 |
| 4 | 15 | 2 | 13 | 2 | 170 / 959 |
| 5 | 8 | 0 | 8 | 0 | 0 / 959 |

Thus the frozen hierarchy has four positive heldout re-encoding levels rather
than one. Every attempted level preserves frozen IDs, all frozen overlap and
boundary ports, exact proper-SE(3) replay, train-admitted relations, and a
complete coordinate/species representation through explicit residual
terminals. Each active type has only one-window/one-independent-occurrence
minimum evidence in this small heldout corpus, and level five stops when no
exact active occurrence remains.

The negative controls explain why this cannot be turned green by a convenient
filter. Every one of the 27 absent first-level types occurs in two of five
training windows, as do 50 / 53 active types; a strict-majority core retains
only two types and covers 13.56% of heldout atoms. Four predeclared
chemistry/chirality/proper-geometry descriptors produce 80, 80, 79, and 77
classes, but none forms a port-consistent semantic class recurrent across
three training namespaces, and exact derivation alternatives recover zero
absent types. Heldout-tuned pooling is therefore rejected.

Because the heldout coordinates are observed for matching, this is exact
four-level re-encoding—not autonomous emission. The nine-level train hierarchy
and four-level frozen deployment are stronger clusters-of-clusters evidence,
while transferable vocabulary closure, stationary recurrence, and exponential
Cd--Yb growth remain red.

### From hierarchy re-encoding to seed-only macro execution

The next benchmark asks whether the frozen higher levels can actually emit
coordinates. It uses the same five training crops and a predeclared evaluation
centre `(35, 30, 20)` in a wider published-model crop. The learner receives a
478-atom radius-14 seed and a public radius-25 boundary. The 2,696-atom scoring
target is at least 49.244 angstrom from every training centre—greater than the
39-angstrom sum of train and target radii—and is opened only after every
candidate trace is immutable.

The seed contains 276 frozen primitive occurrences and 500 train-admitted
primitive relations, but no complete level-one promoted macro. Consequently,
the exact hierarchy executor cannot start any of its nine frozen levels. A
NaCl control recognizes and executes its frozen level-one macro with exact
certificates, so this is a Cd--Yb vocabulary/recognition failure rather than a
missing executor API.

GCTS can recognize a partial macro instead. The generic matcher anchors a
frozen RHS on already observed child clusters, enumerates every finite proper
symmetry gauge, requires a train-admitted internal or boundary port from the
anchor to a missing child, and rejects collisions, public-boundary violations,
and cross-parent ambiguity. Two-child recognition remains empty. Allowing one
finite child witness over all 181 exact derivation alternatives produces 82
target-blind completion candidates and 333 unique proposed atoms. Posthoc only
6 / 82 complete actions are exact; the other 76 show why completion must be a
tree-search decision rather than an unconditional macro copy.

A bounded GCTS mark is fitted only on five radius-7 to radius-14 training
frontiers. Those contain 14 completion candidates—8 positive and 6 negative.
Five-fold leave-one-patch-out freezes threshold 0.25 and a top-five budget.
On the sealed radius-14 to radius-25 frontier, the marked top five contain one
exact and four wrong actions, emitting 16 correct and 18 wrong sites. Constant
ordering also finds one exact action (13 correct / 24 wrong sites); a
frequency baseline finds none. All 31 within-parent train-label shuffles tie
the marked result, giving `p = 1`.

Thus partial promoted completion is now finite, target-blind, proper-SE(3),
port-witnessed, and executable in principle, but its current marking does not
transfer. The next algorithmic target is a lower-cardinality or learned
continuous local section trained on a more diverse set of train-only frontier
failures, followed by a newly predeclared confirmatory nucleus. No autonomous
hierarchical or exponential claim is made from this red result.

### Publicly preregistered second nucleus

The next test was frozen in two public commits before its target was accessed.
The geometry manifest fixes centre `(35, 35, -35)`, radius-14 seed, radius-25
public boundary, and an atom-domain separation above 55 angstrom from every
training window and the previously opened evaluation nucleus. Protocol v2
additionally freezes the actual 28-row training-corpus digest, continuous-model
weights and digest, five source-file hashes, feature schema, top-five/no-threshold
decision rule, three waves per level, four levels, and 31 deterministic
within-window label-shuffle refits. Its one-shot guard enforces the order

`protocol -> train -> model -> seed -> candidates -> controls -> execution -> target -> score`.

One harness invocation aborted before the seed because it looked for geometry
fields on protocol v2 rather than the referenced v1 geometry manifest. The
zero-target-access abort and sole field-source correction were committed as an
erratum before proceeding. The scientific run then opened and scored the target
exactly once.

The common first wave contains 36 target-blind candidates. None is a completely
exact macro action. The continuous mark's top five emit 27 correct among 56
unique proposed sites (48.21% site precision); stable and frozen-frequency
ordering each emit 10 correct among 41 (24.39%). This numerical improvement is
not causal evidence: all 31 shuffled-label refits select the same marked result,
so exact-action, correct-site, and matched-work tests all give `p = 1`. Marked
matched work is 8 checks versus 14, a 1.75x reduction below the frozen 2x gate.

The marked executor still demonstrates real clusters-of-clusters mechanics. It
accepts `5 -> 5 -> 5` placements at level one, `5 -> 5 -> 5` at level two,
`1 -> 0` at level three, and `0` at level four. That is seven consecutive
nonempty self-fed waves. Posthoc, its frozen union contains 247 of the 2,217
outer-shell target atoms, or 11.14% recall. The primary marking gate and the
sustained-growth gate both remain red; stationarity and exponential growth are
unchanged and red. The complete result, event sequence, candidate/plan/execution
digests, and null arrays are stored as a hash-checked fixture, and the benchmark
now refuses to reopen the consumed scientific target.

### Moving the section inside a macro

The sealed failure shows why a whole promoted macro is too coarse a GCTS
decision: none of its first-wave actions is entirely exact, although 27 of the
56 marked emitted atoms are correct. The replacement section does not alter
candidate geometry or IDs. It learns a bounded score for each emitted site
from ten local proper-SE(3)-invariant quantities: chemistry, distances to the
RHS centre, seed, witnessed children and other emissions, local coordination,
overlap multiplicity, matched-child fraction, missing-child count, and frozen
port evidence.

The five authorized training windows now use three predeclared inner radii
(`5.6`, `7.0`, and `8.4` Angstrom) and the same fixed nearest-neighbor shifts.
They produce 123 macro candidates and 1,245 unique candidate-site examples, of
which 871 are supported and 374 unsupported. Nested grouped validation gives
site AUC 0.8864 and action AUC 1.0. Both exceed every one of 31 within-window
label shuffles (`p = 0.03125`). The broader corpus therefore improves both site
and whole-action ordering rather than merely duplicating easy positives.

Admission remains more stringent than ranking. A zero-observed-error threshold
is placed 1.5 logit units above the largest negative grouped-OOF score. Holding
that margin fixed gives 172 / 176 correct held-window selections (97.73%
precision, 19.75% recall), and every nonempty fold is at least 96.15% precise.
The final serialized threshold is `0.9990244124431729` and selects 70 / 70 OOF
sites (8.04% recall). But the margin was selected using all five training
windows. When margin selection is repeated inside every outer fold, it reaches
274 / 290 correct (94.48% precision), below the unchanged 95% deployment gate.
The candidate model is now nonempty and substantially better calibrated, but
the model-selection procedure remains red; no new Cd--Yb target is opened.

A separate exact-decomposition control tests whether geometry alone should cut
the action more finely. Port-connected missing children do not split these 14
training candidates. A Gabriel-graph frontier peel creates ten explicit
residual subclusters and preserves all 148 novel sites exactly, but lowers
emitted-site precision from 110 / 148 to 62 / 90 without changing the 8 exact /
6 mixed action count. It is retained as a negative control, not a growth rule.

The generic executor therefore uses exact port-connected components as the
atomic commitment boundary, applies the frozen site section within each
component, accepts a conflict-free high-score subset, and records every
unaccepted obligation as an exact species/position/owner residual. A partial
site mask never creates an occurrence. A child occurrence becomes admissible
only after its entire frozen colored support is present; a parent is promoted
only after every child is complete, every internal and boundary port is
admitted and independently reverified, and an exact proper-SE(3) prototype fit
succeeds. Synthetic controls demonstrate partial deferral, later child
completion, and exact parent promotion. The NaCl two-wave control emits 48 / 48
correct sites, while making no compression claim. Because the Cd--Yb threshold
fails closed, this machinery is not yet deployed on a new Cd--Yb target. No new
Cd--Yb target is used in fitting or these controls.

### Bounded recurrent branch value

The first autonomous pose-port confirmation fails in value rather than
geometry: its exact three-action terminal configuration is present but ranks
tenth. A geometry-only maximin expansion adds twelve development nuclei and
retains every one regardless of outcome. The resulting 30-group corpus has
354 invariant depth-three branches, 211 exact, and exact supply in 21 groups.
The cumulative state-probability product selects 17 / 21. A target-free
nearest-recurrent value uses nine proper-SE(3)-invariant branch measurements
plus the order-independent action-color population. Whole-group selection
chooses `k = 9` and selects 20 / 21 exact branches (`95.24%`) without changing
the candidate set. Its frozen model digest is
`dcaae79dc2a8c3edf1caec7fc32b05054077c125e8b1e5ad93c11e8097be56ce`.

Reusing the already-consumed failure only after fitting moves its exact branch
from rank 10 to rank 1. Refitting the upstream finite pose-port model on all 30
groups gives 12 / 12 exact terminal configurations on that diagnostic. This
is green development evidence only.

The separately committed confirmation at `(40, -40, -80)` has now run once.
Before its seed was generated, the 30-group pose-port marking was frozen as a
typed compressed vocabulary containing 148,729 token weights and 876 recurrent
states; its state and branch model digests, reach four, beam four, depth three,
target-open ordering, and exact `3 / 3` gate were preregistered. The target-free
tree froze `4 / 16 / 16` candidates, retained four configurations at each
depth, and produced four terminal branches. Only then did a single target
factory verify coefficient bounds 44 and 45 and expose 2,033 scoring atoms.
No terminal branch is all-exact; the selected branch places `2 / 3` colored
sites correctly. Candidate digest
`9ef36560339e20e6b384a6a85199e5e277b5213a3e9845ef81b07526fd1cda48`
and pre-target trace digest
`0a30b5945c7fdcc81f4f71e3e6ccbdbdcd3bcd3b88936601afa27430290fcf80`
are preserved. Thus the fresh failure is upstream candidate supply/beam
retention, not merely terminal-value ranking. Autonomous, stationary, and
exponential IQC growth remain red.

The search-value implementation now acts before terminal pruning. A fixed
target-free schedule (`4 / 4 / 8` local reach, bounded color-population
diversity) freezes 1,259 partial configurations over the same 30 development
nuclei, of which 934 have exact colored prefixes. Separate recurrent heads use
the same ten invariant branch measurements and order-independent color counts;
neighbor capacities are selected independently by leaving out whole nuclei.
Depths one through three choose `k = 25 / 15 / 9` and select exact prefixes in
`29 / 29`, `27 / 28`, and `25 / 28` supplied stages. The combined `81 / 85`
(`95.29%`) clears the frozen-snapshot gate. Score ties are evaluated as complete
equivalence classes: a mixed exact/false top tie cannot pass by insertion
order. Candidate digest is
`649fd2786f9030051bf160f6ff9dbc850c89002f25d44cc25d907e9c2769606c`.

Closed-loop execution remains red. On the consumed confirmation nucleus, the
three frozen heads produce zero exact terminal configurations at beams 4, 8,
and 16; every selected result remains `2 / 3` correct. Thus the new heads are a
real transferable marking improvement on frozen partial states, but not yet a
self-fed autonomous scheduler or an exponential-growth certificate.

A finite recurrent-state beam then replaces color-only diversity. Each
candidate is normalized by its train-fold depth head and quantized without
coordinates, IDs, material labels, or target atoms. The selected state widths
are `4 / 4 / 2`, per-state quotas `1 / 2 / 1`, and total budgets `4 / 4 / 8`.
This retains at least one exact prefix in all `29 / 29`, `28 / 28`, and
`28 / 28` supplied frozen stages—85 / 85 overall. The same fixed scheduler is
still red in the consumed closed loop: it keeps `2 / 4 / 8` configurations,
finds zero exact terminal branches, and selects `2 / 3` correct colored sites.
The remaining failure is therefore transfer under the self-fed state
distribution, not raw beam capacity or frozen-snapshot state coverage.

One group-sealed branch-value aggregation round now targets that distribution
shift directly. In each of five folds, four heldout nuclei are absent from the
value fit; the pose-port state model used by the on-policy rollouts is likewise
refit without them. The other 26 nuclei contribute 4,037 visited partial
branches (3,224 exact). The fit keeps both labels when identical invariant
descriptors have different futures rather than using candidate order to erase
the alias. The frozen closed-loop audit improves terminal exact-path supply
from `16 / 20` to `18 / 20`, top selection from `10 / 20` to `13 / 20`, and
selected correct moves from `44 / 60` to `51 / 60`. This gives a sharper
failure decomposition: two nuclei have no exact retained terminal, while five
contain an exact terminal that is misranked.

The estimate is not fully nested end to end. The older broad snapshot features
were generated once with the shared upstream pose-port model, although rows
from heldout nuclei are excluded from every branch-value fit. The 13 / 20
result is therefore a branch-value development comparison rather than a sealed
pipeline estimate. It is red even under that weaker interpretation: the gate
requires both at least 90% supply and 90% exact selection; supply is exactly
green, selection is only 65%, and a new confirmation is not authorized.

The immutable on-policy corpus digest is
`3683f5091e954c0605fa0115193365a9210a26074e61f1ee539cbbd12831d53f`;
the target-free closed-loop candidate digest is
`395eba0f5a5e66a43a4367cb5e447d48082c67aed60497c9a5631791e5d76cbd`.
These results are development cross-validation, not an autonomous-growth or
stationary-production certificate.

The follow-up fully nests the upstream marking and makes the proposed channel
semantics explicit. For every fold, the pose-port model is refit without all
four heldout nuclei before either broad or on-policy branches are generated.
Each action contributes five finite proper-SE(3)-quotiented channel responses;
the responses form an order-independent multiset, while six colored pair-
distance fields retain how connection geometry is assigned to `XX / XY / XZ /
YY / YZ / ZZ` roles. Exact coordinates remain only in candidate construction
and scoring certificates.

With the candidate reach and recurrent-state beam held fixed, the ablation is:

| branch representation | exact selected | exact terminal supplied |
|---|---:|---:|
| base aggregate statistics | 14 / 20 | 17 / 20 |
| base + colored connection geometry | 15 / 20 | 17 / 20 |
| base + five pose-port channels/action | 14 / 20 | 16 / 20 |
| coupled geometry + pose-port channels | 15 / 20 | 16 / 20 |

The one-round on-policy refit of the coupled model decreases exact selection
to `14 / 20`; it is not retained as an improvement. Raw pose-orbit/channel
identity alone therefore does not improve the value function. The modest
positive signal comes from channel-conditioned colored geometry, consistent
with treating a GCTS marking as a local connection section rather than one
scalar or one slot per observed rotation. The result is fully nested but still
red at 75%, below the 90% gate. Its corpus digest is
`8ebfa3e6cc445fd84d33089ef92c96dbe238108dc6958a73ef6e929953e7d0e3`;
its target-free closed-loop candidate digest is
`3658d67adddd8f92d07471e5681b6ce60583861bbbf655a3ed84cb0bf76871af`.

### Fixed-width marking library and terminal value

The four representations are also executed as a marking-library portfolio.
Each marking produces a state-diverse ordering, but round-robin allocation
shares the unchanged `4 / 4 / 8` total beam; this is not a fourfold beam or
proposal-budget increase. The portfolio raises exact-terminal supply from the
single coupled marking's `16 / 20` to `18 / 20`. Its raw order is deliberately
not presented as a value win: it selects only `13 / 20` exact paths and
`51 / 60` correct moves.

For each outer fold, the terminal value is fitted on the portfolio terminal
states actually visited in the other 26 nuclei. A nested whole-nucleus audit
selects both the representation and nearest-recurrent capacity from the fixed
grid. Fold choices are `ports:k3`, then `base:k9 / k5 / k1 / k9`. Frozen on the
four outer nuclei, this value selects `16 / 20` exact terminal paths and
`54 / 60` correct colored moves. Every score equality class is checked in
full; mixed exact/false top ties are zero. Relative to the portfolio, this is a
three-nucleus gain; relative to the best single marking it is a one-nucleus
gain.

The audit now separates four remaining failures: two are exact-terminal supply
failures and two are supplied-but-misranked. A fully nested ridge-logistic
control does not solve the discrete port alternatives: broad-only execution is
`12 / 20`, and merging the on-policy rows reduces it to `10 / 20`. It is
rejected rather than added as another marking option.

The portfolio terminal corpus digest is
`9625d469f8d6b1e6956cf56690aeb919fe6b465a28374b7f2d61e2067e11ed81`;
the portfolio trace digest is
`56b41e6a3d25223d844260c6c1a011d688f585794be064eb55d9e078bad8c47f`;
the terminal-value trace digest is
`3eb94332bd850eff19b1612ca3d833b15bdcd7044240a5226381731495afee37`.
The exact-selection rate is 80%, still below the committed 90% development
gate, so no new one-shot confirmation is authorized.

The subsequent pruning audit deliberately holds the benchmark gate fixed.
Increasing root proposal reach to 12 makes a correct first action available in
all 20 nuclei, but the unchanged `4 -> 4 -> 8` beam ends with only 17 exact
terminals and selects 13. Independent depth values select 16 with supply 17;
backward descendant-viability labels, propagated only along frozen tree edges,
select 15 with supply 16.

A target-free `12 -> 4 -> 8` lookahead evaluates 7,312 proposals and contains
an exact terminal in all 20 nuclei. This is a supply ceiling, not a value win:
a broad-distribution terminal model selects 12. A canonical feature binding
each symmetry-quotiented pose/port response to its inter-action edge geometry
selects 15, and all five inner folds reject the new edge representation. A
group-heldout action-consensus policy chooses support widths `1 / 1 / 3 / 9 /
5` but selects only 13. None beats the fixed portfolio terminal baseline of
16, so the uncertainty has moved from proposal reach to transferable terminal
valuation. The `18 / 20` confirmation gate remains red and no new target is
opened.

The executor's unordered branch deduplication does not erase whether the same
compatible three-action set could have been assembled in several orders. A
fixed audit counts those parent/order derivations first (maximum `3! = 6`) and
then applies four target-blind terminal rankings. Correct terminals have full
six-order support in `17 / 20` nuclei, but false terminals also have it in
`11 / 20`; both occur in the same `8 / 20`. Multiplicity-first and
score-times-multiplicity fall to `14 / 20` exact selections and `52 / 60`
correct moves. Adding `0.1 log(multiplicity)` only ties the unmodified broad
score at `15 / 20` and `53 / 60`. Order multiplicity is therefore retained as
a truthful visualization of commuting moves, not promoted to a GCTS value
channel.

The next value is a genuine local section rather than another branch-score
transform. A fixed 180-component tensor records species-resolved radial and
pair-angle histograms between the three proposed colored attachments and atoms
already occupied by the search. It is invariant under proper SE(3), contains
no lattice coordinates or absolute origin, and cannot alter the frozen action
geometry. Nested whole-nucleus selection chooses representations
`radial / base+section / base / section / base+radial` with neighbor counts
`1 / 3 / 9 / 15 / 3`. On the same 20 outer nuclei it selects `17 / 20` exact
terminals and `55 / 60` correct moves from `18 / 20` terminal supply, improving
the fixed portfolio by one exact nucleus but remaining below the `18 / 20`
gate. A larger joint-support tensor stays at 17 and loses one correct move;
legacy atom-centred prototype-closure scalars are chosen in zero folds. Only
the compact halo enters the experimental marking library. Because radial and
pair-angle invariants also quotient reflection, this version reports
`chirality_preserved=false`. A separate 30-channel pseudoscalar extension sums
species-labelled ordered neighbor triple products with fixed radial moments.
It is invariant under atom permutation and proper SE(3), changes sign under
reflection, and reports `chirality_preserved=true`. The inner selector chooses
it in two folds, but outer transfer falls to `15 / 20` exact terminals while
remaining at `55 / 60` correct moves. It is therefore exposed only as an
opt-in chiral-material marking; the nonchiral 180-channel halo remains the IQC
default.

The follow-on cluster section removes the atom-centred assumption. Ten
geometry-only nuclei are fitted independently, and exact colored metric-graph
isomorphism retains 53 irregular support classes recurring in at least three
nuclei. Scalar partial completion reaches `17 / 20` exact and `55 / 60`
correct; pair-incidence summaries remain `17 / 20` and fall to `54 / 60`.
An exact typed port graph preserves support identity, shared-species distance
profiles, and symmetry-resolved chirality, but sparse categorical backoffs are
selected in zero folds.

The continuous graph-kernel control therefore compares those same certified
nodes and ports by optimal assignment. Every capacity choice is nested inside
the corresponding outer fold: support-type weights are `0 / .25 / 1`,
node/edge weights are `(1,.5) / (1,1) / (.5,1)`, and neighbor counts are
`1 / 3 / 5 / 9 / 15 / 25`. Inner selection prefers the kernel in folds 1 and
2, showing useful similarity beyond exact graph identity. The sealed aggregate
nevertheless remains `17 / 20` exact and `54 / 60` correct from `18 / 20`
supplied terminals. No target label is available before selection. Continuous
port-graph similarity is therefore retained as an honest research control,
not promoted to the default marking, and the reserved confirmation target
remains unopened.

A bounded message-passing control then transports action chemistry,
partial-support completion, independent-nucleus evidence, shared-interface
chemistry, normalized separation/profile moments, and certified chirality
through the same ports for at most two rounds. It contains no coordinates,
global frame, lattice index, action ID, or target label. The fully nested
selector chooses one round in every fold; inner exact-group counts are
`23 / 25`, `24 / 26`, `22 / 25`, `22 / 26`, and `24 / 25`. It is strictly
preferred over the existing scalar, categorical, and assignment-kernel values
in zero folds. The fixed message encoder is therefore rejected without
changing the `17 / 20` outer result or opening confirmation. A future learned
message map would require its own grouped regularization and shuffled-label
control rather than inheriting credit from this negative.

The grouped learned-readout control is now complete. A class-balanced
ridge-logistic head receives the sparse one- or two-round certified message
embedding. Five group-sealed inner folds choose message depth, support-type
weight, and ridge strength; an outer fold replaces the established value only
when its inner exact-path count is strictly larger. All five folds choose depth
one and folds 1 and 2 pass that replacement rule. On their sealed outer groups,
however, the integrated result is `16 / 20` exact terminals and `54 / 60`
correct moves, versus `17 / 20` and `54 / 60` before replacement. The learned
head alone reaches `15 / 20` and `53 / 60`. Thirty-one within-nucleus label
shuffles give an integrated exact-path plus-one p-value of `.375`. The target
is unavailable to feature fitting, capacity selection, and shuffles; the next
reserved confirmation remains unopened. A learned scalar head is therefore
rejected, while train-learned equivariant message updates remain an open model
class.

That equivariant interaction class is now tested without changing search
geometry. The action representation is a complete canonical incidence graph:
witnessed overlaps/connections preserve shared colored geometry and every
non-connection remains an explicit typed failure edge. A group-balanced
pairwise ridge model learns proper-SE(3)-invariant source × port × neighbor
interactions. Its score may only supply a within-candidate percentile-rank
correction to the established scalar local section. Representation, scalar
neighbor count, and correction weight are selected by true
leave-one-nucleus-out fits inside each outer fold; replacement requires a
strict inner exact-path win. Folds 0, 1, and 2 replace the incumbent. The
fixed outer result is `3 / 4`, `4 / 4`, `3 / 4`, `4 / 4`, `4 / 4`, or
`18 / 20` exact terminals, with `56 / 60` correct moves from unchanged
`18 / 20` terminal supply. This passes the predeclared development-performance
gate. It does not yet prove learned causal value: 2 of 31 within-nucleus label
shuffles also reach 18 exact groups, for a conditional plus-one `p = .09375`
(`p = .21875` for at least 56 correct moves). The causal gate therefore
remains red and no fresh confirmation is opened.

The same fold-one policy is now frozen as an executable artifact rather than
left in process-local experiment caches. Its recursive connection marking,
53-class grouped irregular-support vocabulary, pose/port state table, four
portfolio branch heads, scalar terminal section, and learned equivariant graph
weights are serialized as inert, schema-checked compressed JSON. The 2.4 MB
artifact reproduces the selected model digest
`505b65481e3fe2cc25a284ba8dc175e3a794465c2c7bd726f5448c1fac6bbef5`
and contains neither new-development atoms nor target sites. A published
execution manifest then fixes source hashes, the `4 -> 4 -> 8` proposal reach,
the `4 -> 4 -> 8` diverse-beam budgets, the scalar/fusion capacity, and ten new
mutually disjoint development centres. Seed-only execution produces a second
published receipt containing all 80 terminal action sets and both immutable
orders; its target-open count is zero.

Opening all ten radius-14.5623 targets once gives the following exact result:

| frozen arm | exact-terminal supply | exact selected nuclei | correct selected sites |
| --- | ---: | ---: | ---: |
| scalar local section | 6 / 10 | 6 / 10 | 23 / 30 |
| scalar + equivariant graph rank | 6 / 10 | 6 / 10 | 23 / 30 |

Fusion changes the selected terminal on five nuclei but changes no correctness
outcome. Every supplied exact terminal has rank one in both arms. The other
four nuclei have no exact terminal among their eight frozen branches, so this
batch turns candidate supply into a measured failure rather than attributing
it to the value model. The unchanged policy therefore passes the predeclared
noninferiority transfer check but does not demonstrate an incremental graph
advantage. This batch is additional development evidence, not a fresh
confirmation, and it provides no sustained, stationary, or exponential IQC
claim.

The missing branches were then localized without changing the frozen geometry,
marking, or target-order contract. Removing only final-depth truncation expands
the eight retained terminals to `22–29` but leaves exact supply at `6 / 10`.
Removing second-depth truncation expands them to `26–60` and still leaves
`6 / 10`. Retaining the complete root frontier produces `60–68` terminals and
raises supply to `9 / 10`, proving that first-depth pruning destroyed three of
the four missing paths. Doubling only root action reach does not recover the
last path. On the failed nucleus, a four-schedule ladder frozen before one
target-open call finds the first exact branch at reach `8 -> 8 -> 8`; its scalar
rank is one and fusion rank fifteen.

The corresponding complete ten-nucleus `8 -> 8 -> 8` audit freezes `120–136`
terminals per nucleus and contains an exact three-action terminal in all
`10 / 10`. Exact scalar ranks are
`1 / 9 / 9 / 1 / 5 / 4 / 5 / 3 / 3 / 2`; exact fusion ranks are
`1 / 15 / 15 / 15 / 1 / 10 / 1 / 1 / 1 / 1`. Consequently a generic
target-free portfolio retaining the first nine terminals from each immutable
order preserves complete supply in at most eighteen unique states. It is a
tree-search/rollback portfolio, not a winning value model: scalar top-one is
exact on `2 / 10`, fusion top-one on `6 / 10`, and fusion selects `23 / 30`
correct sites. The result uses the consumed development targets and is neither
fresh spatial confirmation nor stationary/exponential evidence. The frozen
result receipt is `9031bc59…514a5`; the compact result fixture is checked by
SHA-256 in ordinary regression tests.

The widened search and dual portfolio were then frozen for a true spatial
confirmation. Commit `e2ff810` preregistered the first geometry-only expanded-
grid centre `(-110, -10, -10)`, its 40-unit minimum separation from every prior
centre, lift bound 60 with a bound+1 check, exact source hashes, schedule
`8 -> 8 -> 8`, dual budget nine, and a single target-open rule. Before target
access, receipt `b4e7d872…f1ae` froze a 473-atom seed, candidate counts
`8 -> 37 -> 128`, every losslessly compressed terminal action, scalar/fusion
orders, and eighteen rollback states; its target-open count is zero.

The radius-14.5623 target was then opened once at lift bounds 60 and 61. The
crops agree exactly and contain 2,048 atoms, 1,575 outside the seed. Posthoc,
`90 / 128` terminals are fully color-correct. Scalar first exact rank is one,
fusion first exact rank is one, both selected branches place `3 / 3` correct
sites, and the dual portfolio contains exact alternatives. Candidate bytes and
orders remain unchanged after scoring. This is a fresh spatial confirmation of
finite candidate supply and rollback-portfolio retention. It is not evidence
of self-fed sustained growth, a common three-scale production, or exponential
IQC growth.

The next gate self-feeds that *already frozen* fusion top-one state instead of
choosing a posthoc exact alternative. Commit `5f7b409` fixes the same centre,
the inherited action digest, and a larger public radius
`R2 = 14.5623 + 9 = 23.5623`. Receipt `c0a67515…4a1f8`, published before the
outer target, reconstructs the first branch uniquely, records its 476-atom
state, and freezes a second `8 -> 37 -> 128` tree with eleven dual-portfolio
states.

The radius-23.5623 target was opened once at lift bounds 72 and 73; both crops
contain the same 8,684 colored sites. The result separates supply from value:

| second self-fed block | result |
|---|---:|
| exact terminals / complete terminals | `62 / 128` |
| scalar first exact rank | `13` |
| fusion first exact rank | `16` |
| exact terminal in 11-state portfolio | no |
| scalar / fusion top-one correct sites | `2 / 3`, `2 / 3` |
| autonomous six-action gate | red |

The learned cluster/port geometry therefore remains capable of continuation
after self-feed; the transferred terminal value and fixed rollback allocation
do not. The next implementation target is a generic post-self-feed terminal
value trained on consumed blocks, followed by a new sealed confirmation. This
result is not stationary or exponential evidence.

That generic post-self-feed value is now measured. For each of the ten
already-consumed development nuclei, one exact first-block terminal is chosen
from development truth, self-fed as a complete colored configuration, and used
to enumerate a second complete block. Candidate state and features freeze
before its already-consumed outer target attaches labels. The resulting corpus
contains 1,278 terminals, 142 exact, with exact second-block supply in nine of
ten nuclei. Every row carries 236 target-free invariant fields: the existing
scalar section, a complete canonical order-three port-incidence graph, and 16
successor-frontier summaries.

The whole-nucleus nested result is:

| post-self-feed development gate | result |
|---|---:|
| nuclei with exact terminal supply | `9 / 10` |
| exact top-one selections among supplied nuclei | `7 / 9` |
| correct sites selected | `26 / 30` |
| all-exact top bands | `7 / 9` |
| two failed supplied first-exact ranks | `14`, `10` |
| frozen top-one gate | `>=8 / 9` and `>=27 / 30` |
| gate | red |

The final train-only capacity is the incidence representation with one scalar
neighbor and graph-percentile weight 0.25. The two supplied failures motivate
a bounded tree interpretation rather than an unbounded rescue: width 16 is
the smallest power-of-two ceiling above the maximum development first-exact
rank, and it retains an exact terminal in all nine supplied groups.

The already-consumed second-block confirmation is then reused diagnostically
with the model and width frozen. All 128 exact candidate geometries reproduce
the published receipt before the target is regenerated. Top one remains false
at `2 / 3` sites, the first exact terminal is rank 10, and six of the first 16
are exact. Thus bounded rollback supply transfers, but the commit value does
not. Because the preregistered top-one development gate failed, no fresh
nucleus is opened and this is not a new confirmation, stationarity result, or
exponential-growth certificate.

The proposed downstream-value step is also now tested rather than assumed.
Each of the 1,278 complete terminals is advanced through at most eight
target-free child actions under the identical frozen GCTS transition. A
deterministic 1.1 MB compressed fixture stores 685 proper-motion-invariant
measurements per terminal: child count/color balance, the highest-ranked child
local section, and mean/maximum summaries of every child local section and
successor frontier. Source candidate counts, action colors, inherited-action
hashes, and invariant feature slices must replay before the existing consumed
labels may be copied.

| downstream-consequence development gate | prior fusion | consequence value |
|---|---:|---:|
| exact top-one / 9 supplied nuclei | `7 / 9` | `3 / 9` |
| correct colored sites / 30 | `26 / 30` | `18 / 30` |
| required | `>=8 / 9`, `>=27 / 30` | red |

The consequence model is selected inside each outer whole-nucleus fold; no
candidate-random split or fresh target is used. Immediate child-frontier
moments therefore do not resolve the ranks 14 and 10 failure and are rejected
as a commit value. The next value representation must preserve the typed
child-frontier incidence graph, explicit incompatibility edges, and rollback
obligations rather than pooling the downstream state into scalar summaries.
This negative result changes neither the stationary nor exponential IQC gate.

The typed representation has now been implemented and tested as well. Each
terminal keeps its eight strongest target-free child attachments as nodes
colored by cluster species, symmetry-quotiented pose/port channel response,
incoming connection roles, and outgoing obligations. Pair edges retain
proper-motion-invariant separation, shared incoming ports, shared future
sites, witnessed connections, and color conflicts. Across the 1,278
terminals this produces 1,016 distinct canonical graphs, 995 witnessed
child-child relations, and 638 dead-end child nodes. All 35,784 pair edges are
locally compatible, so local collision pruning cannot explain the remaining
ranking error; the signal is whether a legal child preserves a useful future
frontier.

With one fixed pairwise graph capacity and whole-nucleus nesting, the graph
value selects an exact terminal in `8 / 9` supplied nuclei, improving the
prior fusion's `7 / 9`. It selects `25 / 30` correct colored sites, however,
versus the prior `26 / 30`, and therefore still misses the unchanged joint
gate of `>=8 / 9` and `>=27 / 30`. This is evidence that typed pose/port
incidence carries transferable information, but exact/non-exact ranking alone
underweights productive branches. The next value must represent multi-step
port discharge or rollback cost without discarding the number of correct sites
grown. No fresh target is opened and no stationary or exponential claim is
made.

The complementary views are now exposed as a bounded marking library instead
of being averaged into one score. Head one is the typed child-topology value.
Head two combines the established local-section/port value with a new
group-balanced ordinal graph value trained on `0 / 1 / 2 / 3` correct-site
levels. Every outer model excludes its held-out nucleus, both heads rank the
identical frozen candidates, and the portfolio retains only the top candidate
from each head. Across the nine nuclei with exact supply, this at-most-two-state
portfolio contains an exact terminal in `9 / 9`; the posthoc best retained
choices total `28 / 30` correct sites. Nineteen candidates are retained across
all ten nuclei, versus the previous width-16 rollback ceiling.

This passes a **bounded rollback-supply** gate, not autonomous commitment. The
only complementary failure needs the topology state first and the ordinal
state second, so posthoc exact rank is at most two. No target-free detector has
yet proved when the first state is contradictory, and the consumed labels are
used only after both immutable orders and the portfolio are frozen. Therefore
the UI may offer this as a marking-library tree-search option, while the
automatic commit, stationary-production, and exponential IQC gates remain
red.

The retained portfolio is also executed beyond its terminal boundary rather
than judged only by its immediate child graph. Every one of the 19 states gets
the same 16 greedy pose/port-marked child placements inside a public radius one
seed shell beyond the second block. The generator never constructs an oracle
crop at that rollout radius, and freezes each complete trace before copying the
already-consumed label. No trace exhausts its frontier. A deliberately small
grid of five aggregate statistics and horizons `0 / 1 / 2 / 4 / 8 / 12 / 16`
selects final frontier vote mass at horizon 12 on the complete development
corpus, where it obtains `9 / 9` exact supplied nuclei and `28 / 30` correct
sites. Proper whole-nucleus holdout selects only `8 / 9` and `26 / 30`; a
31-shuffle within-nucleus control gives an exact-count upper-tail
`p = .3125`. Therefore neither hard exhaustion nor aggregate surviving port
mass is a validated target-free rollback detector. The negative audit narrows
the next representation to typed obligation identity and discharge history,
not another scalar measure of frontier size.

A fresh two-block confirmation then freezes the imperfect development rule
instead of selecting another retrospective statistic. Public preregistration
commit `18e45c9` fixes a geometry-only maximin center `(-70, 10, 70)`, the
source/model/audit digests, the width-two marking portfolio, frontier-vote mass
at horizon 12, and a single target-open call. The center's minimum separation
from all 30 recorded development and confirmation centers is `66.3325`, larger
than two second-block radii (`47.1246`). The execution harness is also
published before it generates the 491-atom seed.

The target-blind first tree has candidate counts `4 → 7 → 29` and retained
widths `2 → 4 → 8`; its selected state is replayed uniquely and becomes the
source for 133 second-block terminals. The typed-topology and ordinal-yield
heads retain stable states 21 and 19. Both complete 16-step traces are frozen;
the preregistered step-12 vote masses tie at `1232`, so the stable rule selects
19. Only after receipt hashing does the 8,671-atom radius-23.56 target open,
once, with lift-bound-plus-one equality.

Posthoc scoring is unambiguously red: the selected first block is `2 / 3`
correct, retained state 21 is `2 / 3`, retained state 19 is `1 / 3`, neither
second-block state is exact, and the selected end-to-end path is `3 / 6`.
Thus the missing capability precedes rollback: the fresh first-block value and
width-two portfolio lose exact supply. No autonomous finite-commit,
stationary-production, or exponential IQC claim is made.

The follow-up exhausts the same consumed branch before pruning. The complete
first tree grows `8 → 37 → 128`; 16 terminals are exact, while the frozen
fusion order reaches its first exact state only at rank 8. Feeding precisely
that state into the unchanged second block gives `8 → 36 → 127` terminals and
four exact continuations, stable IDs `86 / 87 / 89 / 123`. Therefore unchanged
candidate geometry contains an exact two-block path. The original typed-
topology and local-section-plus-ordinal-yield values place their best exact
second action at ranks 62 and 98. Retaining 124 actions merely to recover one
is not a useful GCTS remedy.

Every one of those 127 states is then rolled forward for the same 16
target-free steps before the consumed target is reconstructed. The frozen
step-12 frontier-vote rule improves the best exact rank to 19 but remains
outside top 16. A statistic already present in the predeclared grid—integrated
frontier vote mass at horizon 12—ranks exact stable state 89 first. On the
original retained development corpus it has the same `9 / 9` exact supplied
groups as the selected frontier endpoint, with `27 / 30` rather than `28 / 30`
correct sites. Yet repeating that rule on the complete first tree selects
inexact state 115; its best exact first state is rank 8. The statistic is a
useful conditional value, not a stage-independent greedy marking.

All candidate orders and traces are hashed before either consumed target is
opened, but the integrated rule was identified after those labels were scored.
Accordingly this is a development diagnostic only. It moves the immediate red
gate from geometric supply to bounded cross-block beam retention: an exact
path survives in a width-eight first beam and a top-one integrated continuation
of its exact node, but no target-free rule yet chooses that node globally.
Runtime is also material—complete enumeration and 127×16 rollout work take
minutes per nucleus. Autonomous commitment, fresh transfer, stationary
production, and exponential IQC growth remain red.

The branch-local policy is also executed rather than inferred from the one
exact source. Each of the eight fusion-ranked first parents independently
enumerates its full second tree (`126–141` terminals), rolls every terminal for
twelve target-free steps, and retains one integrated-vote child. All branch
candidate digests, trace digests, chosen children, and the global parent order
are frozen before the consumed radius-23.56 target is reconstructed. The beam
contains exactly one exact end-to-end path: first-parent rank 8 followed by
stable child 89. This makes bounded branch-local supply green at width `8 × 1`.

Global scalar comparison is still red. The eight winning child scores order
the parents `3 / 7 / 1 / 4 / 5 / 6 / 8 / 2`; parent 3 is selected and both of
its blocks are inexact. The exact parent is only seventh by the cross-parent
score. This proves the integrated statistic is meaningful only conditional on
its parent context and should not be normalized into a universal state value.
The complete audit takes roughly forty minutes with four workers, so it is an
explicit correctness ceiling, not a computational win. The next marking must
encode parent→child obligation change or promote shared branch subtrees into
clusters-of-clusters before any fresh autonomous confirmation is justified.

The first explicit clusters-of-clusters value uses the six accepted actions as
one colored macro: three parent actions plus three child actions. A
62-component descriptor records colored populations, sorted within-block and
cross-block distances, centroid/radius and nearest-parent statistics,
connection fractions, colored cross-distance summaries, and a proper-SE(3)-
invariant pseudoscalar that preserves chirality. It is translation invariant
and permutation invariant within each block. Geometry for all 1,278 examples
freezes before the 142 consumed exact labels are copied from the prior corpus.

This geometric macro value is not transferable. The final cross-geometry head
selects 6 / 9 supplied nuclei and 25 / 30 sites in-sample, exceeding all 31
within-nucleus label shuffles (`p = .03125`), but nested whole-nucleus selection
falls to only 1 / 9 and 14 / 30. Applied target-free to the eight confirmation
beam paths, it orders parents `2 / 4 / 3 / 8 / 7 / 5 / 1 / 6`; the sole exact
path is rank 4 and the selected path is wrong. The gap between apparent
in-sample significance and failed spatial transfer is precisely why raw macro
geometry is rejected. The next recursive marking must preserve typed incoming,
discharged, and remaining boundary ports across the parent→child transition.

That boundary-obligation hypothesis is tested without changing the candidate
geometry. For every one of the same 1,278 terminals, a frozen 69-component
port-transition descriptor concatenates 23 ID-free statistics of the parent
graph, 23 of the child graph, and their signed difference. The statistics
cover typed incoming/outgoing obligations, witnessed edges, connected
components, degree moments, and boundary load; raw prototype/support IDs are
excluded. Nested whole-nucleus model selection over the port-only and
geometry-plus-port views reaches 3 / 9 supplied exact terminals and 20 / 30
correct sites. That is better than raw macro geometry's 1 / 9 and 14 / 30,
but the within-nucleus shuffle result is not significant (`p = .1875`).

The consumed branch-local receipt supplies an independent diagnostic of the
same failure mode. The target-free model orders the eight parents
`4 / 2 / 3 / 7 / 8 / 1 / 6 / 5`; the sole exact six-action path is rank five
and the selected parent is false. Thus scalar summaries of port-graph change
do not transfer as a cluster-of-clusters value. Subsequent work must preserve
the typed incidence matching—exactly which obligation is discharged and which
is carried—rather than compressing that graph to counts.

The identity-preserving alternative is implemented as a canonical six-node
transition graph. Three nodes are parent obligations and three are child
obligations. Every one of the 15 within/cross edges retains normalized
separation, shared colored support and distance profiles, support-geometry
equality, proper chirality, and explicit parent-action participation in a
child's matched support. Parent/child role is part of node color; the graph is
quotiented over only `3! × 3!` block-local permutations. Raw support IDs,
action order, translation, global proper rotation, lattice coordinates, and
targets are excluded. The 1,278 examples yield 1,120 unique canonical graphs.

With one fixed order-three source × port × neighbor model—no hyperparameter
search—the identity-preserving graph reaches 7 / 9 exact supplied nuclei and
26 / 30 correct sites under whole-nucleus holdout. All 31 within-nucleus label
shuffles do worse (`p = .03125`). On the consumed eight-parent receipt it
orders the sole exact six-action path second, compared with ranks four and
five for raw macro geometry and aggregate port transition, but still selects
a false path. An explicitly exploratory equal-rank fusion with the established
successor child graph reaches 8 / 9 exact supplied nuclei and 26 / 30 sites;
weights `.5 / 1 / 2` share that plateau. The frozen joint gate remains
`8 / 9` and 27 sites, so autonomous commit is still red.

The exact geometry colors initially made the 42-fit nested/null audit take
about one hour because every fit rebuilt identical sparse graph embeddings.
A graph-digest/specification cache is numerically exact: cached and uncached
model digests, weights, and scores agree, while the same audit completes in a
few minutes. This changes training cost only; online scoring was already one
pass over six nodes and 15 edges.

### Fully nested incidence-ranked rollback control

The identity-preserving graph is also evaluated as a bounded rollback value,
not as a new candidate generator. The input is the existing two-marking
portfolio: 19 immutable retained states across ten nuclei, with at most two
states in any nucleus. For each outer fold, the incidence model is fitted on
the other nine nuclei and is allowed only to reorder those retained states.
It selects an exact state in all `9 / 9` nuclei with exact supply and totals
`28 / 30` correct colored sites.

That apparent perfect supplied-nucleus selection is not causally significant
under the rigorous null. For each of 31 within-nucleus label shuffles, ten new
models are fitted, and every shuffled model excludes the nucleus it ranks.
Eleven shuffles also select `9 / 9`, giving the plus-one upper-tail result
`p = .375`. The previous pooled shuffle was therefore optimistic for this
specific two-state decision. Candidate geometry, portfolio membership, and
the retained-state limit are identical in every arm.

The already-consumed six-action confirmation provides a boundary diagnostic:
the exact continuation is inside the incidence-ranked top two, but the first
state is false. The result preserves a green bounded rollback-*supply* claim
and rejects the incidence value as an autonomous rollback trigger. A fresh
confirmation is not opened, and autonomous commitment, stationary recurrence,
and exponential IQC growth remain red.

### Identity-preserving obligation-discharge history

The next audit retains the semantic identity of obligations through time rather
than summarizing the successor frontier into total vote mass. It replays the
same 19 immutable retained states for the same 16 target-free child placements.
For each accepted attachment it records every selected semantic port role—its
colored parent and source cluster signatures plus normalized separation—and
whether that role is discharged, persists, or is selected again. The causal
cohort is untruncated: the 304 transitions contain 406 selected-role transitions
over 131 proper-motion-quotiented identities. Background frontier mass is kept
only for audit accounting and is not used for ranking.

Whole-nucleus outer fitting selects an eight-step persistence rule. It chooses
an exact state in all `9 / 9` nuclei with exact supply and totals `27 / 30`
correct colored sites; the model fitted on all consumed development nuclei gives
`28 / 30`. Candidate geometry, the two-state bound, and every rollout remain
unchanged.

This corpus cannot establish a 5% causal result. Only groups 0, 3, and 5 have
nonidentical `(exact, correct-sites)` tuples, and only groups 0 and 5 can change
exact/non-exact selection. The audit therefore enumerates all eight distinct
within-nucleus label assignments and refits all ten outer folds for every one.
Two assignments reach the observed `9 / 9`, giving an exact upper-tail
`p = .25`; four unique exact-label assignments make `.25` the minimum attainable
exact-test resolution. Typed discharge is retained as an interpretable marking
channel, but failure detection, autonomous commitment, fresh confirmation,
stationary recurrence, and exponential IQC growth remain red. The next
statistically meaningful benchmark must increase the number of independently
ambiguous nuclei or retain a broader target-free portfolio.

### Wide typed-discharge stress test

The broader portfolio is fixed at eight candidates from each of the same two
outer-fold marking orders. Deduplication yields 120 states total and 10–16 per
nucleus, never exceeding the earlier width-16 rollback ceiling. Exact supply
remains `9 / 9`; seven nuclei now contain both exact and inexact alternatives.
The conditional probability that independent uniform selection happens to pick
an exact retained state in every mixed nucleus is `.0006685714`, versus `.25`
for the narrow portfolio. Thus the wide corpus removes the randomization-
resolution objection without changing any exact terminal geometry.

Every retained state receives the same 16-step target-free rollout. The sealed
artifact contains 1,920 transitions, 2,581 selected-role transitions, and 135
semantic role identities. A regression check proves that all 19 trajectories
from the narrow corpus—including scalar traces, typed transitions, and copied
labels—are identical inside the wide artifact. No fixed point occurs.

The harder evaluation overturns the narrow-corpus persistence result. Nested
scalar rollout rules select `7 / 9` exact supplied nuclei and `24 / 30` sites.
Nested aggregate typed rules select `5 / 9` and `24 / 30`; 31 fully refitted
within-nucleus shuffles give `p = .71875`. An identity-specific model then tests
120 train-selected specifications: 4/8/16-step horizons; exact, coarse, and
chemistry role quotients; independent-group support 2/3; two shrinkages; and
mean or square-root-normalized aggregation. All hyperparameters are selected
inside every outer fold, and the entire process is repeated inside every null.
The final 50-weight coarse role-status model reaches only `5 / 9` and `23 / 30`,
again with `p = .71875`.

This is a useful negative benchmark. Widening solved candidate ambiguity and
statistical resolution; coarsening solved much of the channel-coverage shift;
neither solved branch value. Independent role weights are rejected as the
autonomous default. The next representation must retain relational
contradictions among simultaneous discharged, persistent, and newly exposed
ports, or prove a branch-local unsatisfied-obligation certificate. Fresh
confirmation, autonomous commitment, stationary IQC recurrence, and
exponential IQC growth remain red.

### Relational discharge contradiction

The selected-role cohort alone cannot reconstruct its causal context from the
stored top-16 background roles: only 116 of 2,581 selected-role events occur in
that truncated set. A new sealed replay therefore scans the complete semantic
role multiset transiently at every step while serializing only seven fixed
proper-motion-invariant relation families: exact reciprocal connection,
forward/backward continuation, common parent/source endpoint, and parent/source
touch. For each selected role it records before, after, lost, retained, and
gained multiplicity plus five missing/depletion flags. Raw background role IDs,
coordinates, and candidate identities are not features.

The relational artifact is parity-checked against all 120 published wide
trajectories after stripping the new fields. Across 2,581 selected-role events
it observes 51 reciprocal losses, 64 forward-continuation losses, 2,581 source-
touch losses, 13 forward gains, and 151 new parent-touch relations. This is real
connection structure that the independent-role model did not contain.

A low-capacity nested rule grid tests 12 relation metrics, five horizons, and
both directions. Outer fitting chooses “minimize forward continuations after
two steps” in nine folds except for one one-step reciprocal control. The result
is `7 / 9` exact supplied nuclei and `26 / 30` colored sites. It improves site
yield over scalar discharge (`24 / 30`) and independent-role value (`23 / 30`),
but does not improve the exact-nucleus count. Six of 31 within-nucleus label
shuffles, with the complete rule fit repeated in every outer fold, reach at
least seven exact nuclei, giving `p = .1875`.

Relational discharge is therefore retained as a useful experimental channel,
not an autonomous rollback policy. The next representation must enforce
branch-level simultaneous consistency or produce an explicit unsatisfied-port
certificate; independent relation totals still conflate locally identical
alternatives in the two difficult boundary environments. Fresh confirmation,
autonomous commitment, stationary IQC recurrence, and exponential IQC growth
remain red.

### Simultaneous semantic port-cover certificate

The replacement search no longer equates marginal availability with joint
consistency. Given a finite carried multiset and frozen exact actions, it
enumerates mutually compatible action sets and reports one of three states:

- `satisfied`: an explicit compatible set covers every carried duty;
- `unsatisfied`: complete candidate enumeration and exhaustive search prove no
  cover exists;
- `unknown`: either the candidate enumeration or bounded search was truncated.

Only `unsatisfied` authorizes rollback. An adversarial regression has two
carried roles and one action for each; both roles are marginally available, but
the actions conflict. The old stranded-role check accepts it, while the new
solver returns an exhaustive inconsistency certificate. The same problem with
an incomplete candidate list returns `unknown`, never a fabricated rejection.

The real audit reconstructs the complete successor frontier for each of the
120 branches in the frozen width-16 IQC portfolio. Candidate geometry is
unchanged, exact inter-candidate minimum-distance conflicts are frozen, and
labels from the consumed development set are joined only after each group's
candidate sets and certificates are hashed. All successor enumerations and all
searches complete: 257 search nodes over 137 role-relevant actions.

The stronger result is nevertheless red. Every branch is satisfiable: all 59
exact and all 61 false branches pass. Forty-one branches carry no persistent
selected role. The other 79 contain at most one distinct semantic role, at
most three relevant successor actions per branch, and zero pair conflicts.
Thus simultaneous search is implemented and verified, but the semantic role
quotient has erased the joint structure it was meant to constrain. The next
certificate must preserve exact finite symmetry-quotiented port instances and
their incidence; increasing scalar capacity or reweighting the same role
classes cannot repair this loss. No physical valence, mandatory port occupancy,
autonomous growth, stationary IQC rule, or exponential claim follows.

### Exact finite port-instance incidence

The proposal engine previously discarded the ordered occurrence pair after it
incremented an aggregate vote. It now carries an exact `parent_index →
source_index` witness alongside each proposal through frontier subsetting and
merging. The indices are never learned features. They are used transiently to
ask whether a successor action shares the same parent/source occurrence; the
serialized action class contains only the fixed relation name, colored local
types, and the complete normalized pair-distance signature of selected and
successor endpoints. This is invariant to atom permutation, translation, and
proper rotation, while exact candidate geometry remains independently frozen.

All 120 selected actions in the width-16 portfolio have exactly one ordered
pair witness. For each action the complete successor frontier is scanned under
the seven fixed relations used by the earlier semantic audit: reverse,
forward/backward continuation, same parent/source, and parent/source touch.
Every certificate search and every successor enumeration completes before
consumed labels are joined.

The fixed forward relation is the strongest low-loss discriminator:

| finite-instance relation | exact SAT | false SAT | exact UNSAT | false UNSAT |
| --- | ---: | ---: | ---: | ---: |
| reverse | 43 | 22 | 16 | 39 |
| forward | 57 | 35 | 2 | 26 |
| backward | 59 | 60 | 0 | 1 |
| same parent | 59 | 61 | 0 | 0 |
| same source | 56 | 41 | 3 | 20 |
| touch parent | 59 | 61 | 0 | 0 |
| touch source | 57 | 43 | 2 | 18 |

Forward continuation therefore retains `96.61%` of exact branches, rejects
`42.62%` of false branches, and raises retained precision from `49.17%` to
`61.96%`. The semantic-role cover rejected zero false branches, so restoring
finite incidence is a material improvement rather than a wider scalar model.

The deployment gate remains red. The two rejected exact branches include the
only exact branch in one supplied nucleus, reducing exact supply from nine to
eight nuclei. The permissive backward relation restores all exact branches but
rejects only one false branch; an unconditional union would erase nearly all
the gain.

The bounded local backoff experiment is now complete. Each selected action
serializes six target-free scalars before consumed labels are joined: target,
parent, and source margins to the public boundary; ordered port length in
nearest-neighbor units; port/outward cosine; and current frontier fraction.
Candidate geometry and exact finite-port certificates are unchanged. A
leave-one-nucleus-out selection over one feature, one direction, and one
threshold chooses `ordered_port_length_nn >= 9.3709435`. The threshold itself
is refit without each held-out nucleus.

| boundary-backoff result | exact | false |
| --- | ---: | ---: |
| forward SAT | 57 | 35 |
| forward UNSAT deferred | 2 | 18 |
| forward UNSAT rejected | 0 | 8 |

The backoff therefore restores `59 / 59` exact branches, all nine supplied
nuclei, and retains eight false rejections. Its final precision is `59 / 112 =
52.68%`. Deferred is a separate state—not SAT—and cannot accept an action by
itself.

The causal gate is red. Thirty-one deterministic within-nucleus label shuffles
preserve each nucleus's class marginal and repeat the complete feature-family
selection plus threshold fit. Every shuffle also defers both exact-labelled
rows and rejects eight false-labelled rows, giving `p = 1` for exact recovery
and false rejection. The scalar recognizes three boundary/port-length regimes,
but exact and false actions inside the two exact-bearing regimes remain
indistinguishable. It is not integrated as the learned marking and no fresh
confirmation is claimed. The next experiment must retain their joint endpoint
metric graph or simultaneous incidence, not add another scalar boundary
channel. No physical valence, mandatory port occupancy, autonomous growth,
stationary IQC recurrence, or exponential growth follows.

### Complete simultaneous branch-action graph

The scalar result leaves two possible explanations: either the selected port
attachment lacks sufficient geometry, or the rest of the simultaneous branch
contains the missing relation. The dataset now freezes both representations
before labels are joined.

The selected endpoint descriptor is the ordered colored proper-metric graph of
public center, proposed target, parent occurrence, and source occurrence: six
normalized distances plus signed normalized volume. It has only three classes
among the 28 forward-UNSAT branches. Both classes containing an exact row also
contain false rows, so selected-port geometry cannot distinguish the action.

The complete branch descriptor instead uses all three colored placements in
the terminal state. It enumerates their six action orders, takes the canonical
colored distance code, and retains a signed volume so improper mirrors do not
collapse unless the colored metric set has the corresponding proper symmetry.
The resulting code is invariant to insertion order, atom permutation,
translation, and proper rotation. Candidate geometry and all seven finite-port
certificates are unchanged.

This solves local identifiability but not transfer:

| branch-graph audit | result |
| --- | ---: |
| branches / exact / false | 120 / 59 / 61 |
| canonical complete graph classes | 119 |
| exact graph rows recognized outside their nucleus | 2 / 59 |
| forward-UNSAT graph classes within nuclei | 28 / 28 |
| within-nucleus exact/false graph collisions | 0 |
| nested nearest-recurrent graph recovery | 0 / 2 exact nuclei |
| nested colored-edge token recovery | 0 / 2 exact nuclei |

The nearest-recurrent arm uses 30 fixed ID-free aggregates and selects
`k ∈ {1,3,5,9,15}` only inside each outer nucleus fold. The edge arm retains
the three colored internal edges and selects a normalized distance width from
`{0.25,0.5,1,2,4}` in the same nested manner. Each arm ranks exactly one of
the unchanged forward-UNSAT alternatives in each affected nucleus. Both select
zero of the two recoverable exact nuclei. Across 31 within-nucleus label
shuffles, each null family has median zero and maximum one exact selection, so
both observed plus-one upper-tail values are `p = 1`.

Neither graph section is integrated. The exact graph is almost an occurrence
identifier, while its bounded recurrent quotients have no transported value.
The next representation step must learn a recurrent cluster-of-clusters
quotient from more independent nuclei before fitting the branch marking. A
higher-capacity classifier over 119 nearly unique development graphs would not
be evidence of generic GCTS. No fresh confirmation, autonomous growth,
stationary recurrence, or exponential IQC claim follows.

### External recurrent branch-value transfer

The independent 30-nucleus recurrent branch corpus tests whether repeated
scalar frontier state can supply that quotient without fitting a larger graph
classifier. The audit first certifies spatial independence. Training domains
have radius `14.5623059`, wide benchmark domains have radius `23.5623059`, and
their required center separation is therefore `38.1246118`. Training nucleus 9
is excluded because its nearest wide center lies at `37.4165739`. Every other
training nucleus is at least `40.0` away, leaving 29 closed-ball-disjoint
nuclei, 338 branches, 195 exact branches, and 20 groups with exact supply.

The existing grouped recurrent-value learner selects `k = 9` using only these
training groups. It selects exact branches in `19 / 20` supplied groups. The
wide branch candidates retain their frozen geometry and use the matching nine
target-free scalar fields from the independent terminal fixture. Candidate
and order digests are frozen before the exact wide labels are joined.

| external recurrent-value transfer | result |
| --- | ---: |
| admitted training nuclei / examples | 29 / 338 |
| training exact examples | 195 |
| training supplied nuclei selected exact | 19 / 20 |
| wide forward-UNSAT candidates | 28 |
| recoverable exact wide nuclei selected | 1 / 2 |
| exact ranks in affected nuclei | 1 / none / 10 |
| false wide alternatives rejected | 24 / 26 |
| exact supply after transfer | 8 / 9 nuclei |
| 31 grouped-shuffle median / maximum | 1 / 1 exact nucleus |
| plus-one upper-tail value | `p = 1` |

This is a useful negative transfer result. The larger corpus improves the two
bounded graph arms from `0 / 2` to `1 / 2`, but does not preserve exact supply
and is indistinguishable from grouped shuffled labels. It is not integrated as
the GCTS marking. The missing operation remains a recurrent oriented
cluster-of-clusters quotient whose states transport finite port semantics;
aggregate branch probability, vote, color, and separation fields are not a
substitute. No new autonomous, stationary, or exponential claim follows.

The initial pairwise graph implementation also exposed an accidental
computational bottleneck: it rebuilt a sparse feature-difference dictionary
for every positive-negative pair at every gradient step. The replacement
computes the identical logistic pair coefficient per pair, accumulates one
coefficient per endpoint, and makes one sparse pass over the examples. It
matches the reference weights to `1e-12`; a full 1,278-row graph fit falls to
about 26 seconds, and the complete 56-fit nested graph cache plus scalar sweep
finishes in about 13 minutes rather than running for hours.

### Finite-state substitution cycles

Stationarity is not broadened informally to rescue the IQC result. A strict
finite-state alternative permits a period-`p` sequence of exact production
states only after `2p+1` consecutive observations, so every state and directed
transition is seen twice. State identity preserves canonical chemistry,
chirality, proper geometry, directed overlap/boundary ports, and overlap
chemistry. Repeated transitions must have equal independently learned scales
and identical exact population-substitution matrices, and the entire cycle
must recur on heldout or self-fed evidence. A synthetic two-state cycle passes;
short prefixes, shuffled states, chemistry/population mutations, and replayed
rather than independently observed heldout scales fail.

The current IQC hierarchy has four positive levels, while the smallest
nontrivial period-two cycle needs five. Its exact adjacent-state intersections
are `0, 0, 0`, its exact three-level intersections are `0, 0`, and heldout
levels merely re-encode frozen geometry rather than independently observe a
scale. Finite-state recurrence therefore remains red alongside stationary
recurrence.

### Train-only hierarchy selection and semantic controls

`scripts/materials_gcts_hierarchy_selection_environment.py` exposes a bounded
future-RL interface: state is the current exact promoted program plus retained
derivation alternatives; actions choose a train-admitted quotient subset or
derivation policy; reward combines exact cover, MDL saving, and future witnessed
port connectivity. Stationarity is an external gate, never a branch label.

A deterministic width-three beam over a fixed eight-level horizon chooses the
alternative-consistent policy. Relative to the all-representative greedy path,
it changes promoted occurrence retention from
`153 -> 34 -> 10 -> 6 -> 4 -> 2` to
`324 -> 78 -> 26 -> 12 -> 8 -> 4` and improves the fixed-horizon score from
`-63.205` to `-34.592`. It still reaches only six positive levels and produces
no stationary witness. The result is therefore improved hierarchy selection,
not avoidance of evidence exhaustion. This beam is a train-compression
comparator rather than the executable transfer policy; promoted heldout
matching is supplied by the strict-majority re-encoding above.

The guarded semantic-quotient experiment preserves every exact proper-SE(3)
terminal as a replay alternative, but the exact quotient is rejected by the
train-only shuffle and perturbation controls.
Approximate connection grammars are labelled approximate and cannot satisfy the
strict exact-recursion gate.

### Width-eight search and the hardened NaCl relation certificate

Cached partition refinement removes factorial child-order enumeration while
preserving exact permutation and proper-SE(3) invariance. The apparent earlier
negative was an evidence issue: one sparse 216-atom audit finds only six
size-two macros. With two independent bounded presentations and all 29,988
learned relations retained, the search admits child width eight and exports the
`8 children / 24 directed ports / 52 atoms / 2 atom-disjoint occurrences /
MDL 30` production summarized in the crystal section above. Frozen-relation
replay supplies `1,478 / 750 / 86` witnesses over three learned factors and the
strong stationary signature recurs at scale 2.

This does not erase the discovery boundary: the positions-only grid learner
still proposes radix and offsets before the port graph validates them. Pure-
port closure learning remains open, and the IQC stationary result remains red.

### Geometry-complete recurrent IQC macro quotient

The scalar external-value failure motivates a geometry-complete intermediate
benchmark. Seventeen development nuclei are closed-ball disjoint from the
unchanged ten wide audit domains. Their target-blind branch generator freezes
168 three-action cluster-of-clusters occurrences before labels are joined: 72
are exact, and 158 symmetry-quotiented port derivations retain alternative
search histories. The 47 KB normalized fixture stores colored nodes in an
intrinsic right-handed frame, exact parent/source endpoint metric geometry,
chirality, and witnessed connections. It stores neither raw occurrence IDs nor
global poses as semantic features. The upstream primitive pose/port learner is
fit on development atoms; candidate generation does not reread target atoms
after that fit. The wide audit remains completely excluded.

| geometry-complete quotient | result |
| --- | ---: |
| development nuclei / macro occurrences | 17 / 168 |
| exact macro occurrences | 72 |
| exact port-derivation types | 158 |
| selected distance width / minimum groups | 4.0 / 2 |
| semantic geometry types | 33 |
| exact action / derivation alternatives | 54 / 86 |
| held-out supplied nuclei selected exact | 7 / 9 |
| selected branch precision | 7 / 11 = 63.6% |
| exact candidate coverage | 47.2% |
| grouped-shuffle median / maximum | 6 / 7 exact nuclei |
| plus-one upper-tail value | `p = .4375` |
| unchanged wide recoverable exact selected | 0 / 2 |
| unchanged wide false selected | 2 |
| autonomous / stationary / exponential | false / false / false |

The unbinned exact geometry class is precise but covers only 4 / 9 supplied
nuclei. Coarsening raises transfer coverage by merging exact alternatives whose
connection consequences differ. On the unchanged wide set the selected
geometry quotient is worse than the prior scalar fallback (`0 / 2` rather than
`1 / 2` exact, with two false selections in both cases). It is therefore not
integrated as a marking-library default.

This failure is narrower and more useful than another classifier result. The
training fixture already retains the exact parent/source port witnesses, while
the wide branch fixture retains selected port state, endpoint geometry,
boundary context, and successor candidate classes. They are not yet expressed
in one canonical incidence schema, so a cross-corpus join would be artificial.
The next benchmark will first align both sides on the same bounded directed
port graph—canonical colored node geometry, ordered connection state, endpoint
witnesses, and successor incidence—then learn the quotient and repeat grouped
shuffles plus unchanged-wide transfer. Only a transferred rule may enter a
self-fed recurrence or stationarity audit.

### Shared proper-SE(3) port-incidence representation

The schema mismatch identified above is now removed. The generic serializer
represents a three-action macro as three colored action nodes plus three
pairwise edges. Every node carries all exact incoming parent→source witnesses:
finite parent/source cluster-state colors, ordered endpoint species, and local
endpoint geometry. Every edge carries directed endpoint-equality/touch roles
and the normalized four-distance endpoint cross metric. Exhaustive node
permutation removes historical insertion order. An intrinsic right-handed
frame removes global translation and proper rotation while retaining
chirality. Raw occurrence IDs, lattice coordinates, material labels, targets,
and global poses are absent.

The development fixture adapts directly to this contract. The unchanged wide
fixture required authentic internal witnesses, so each frozen terminal branch
was replayed from its colored seed. A receipt-constrained executor preserves
the original top-`8 -> 37 -> 128` proposal order but advances only prefixes
whose colors, center radii, and pair distances can still match one of the
already-frozen target-blind branch graphs. Every final source-action digest is
checked. The companion fixture is 57,220 compressed bytes and contains all 10
wide groups, all 120 branches, and all 59 existing exact labels. Graph workers
receive no second-block target sites or exact/false labels; labels join only
after every group graph digest freezes.

| shared port-incidence quotient | result |
| --- | ---: |
| development / wide branch graphs | 168 / 120 |
| unchanged wide forward-UNSAT candidates | 28 |
| selected development precision | 4 / 4 = 100% |
| supplied development nuclei reached | 4 / 9 |
| recognized development exact candidates | 20 / 72 |
| frozen recurrent semantic types | 26 |
| recognized wide candidates | 1 / 28 |
| recoverable exact wide candidates recognized | 0 / 2 |
| selected wide exact / false | 0 / 0 |
| external exact / false shuffle p-values | 1 / 1 |
| autonomous / stationary / exponential | false / false / false |

The strict selector enforces a 95% development precision floor. A coarser
role-only code reaches 6 of 9 supplied nuclei but is only 60% precise and is
therefore rejected: a growth marking cannot purchase recall with false atoms.
The strict recurrent vocabulary fails closed on the wide set because exact
port types shift across nuclei. This is no longer a data-contract ambiguity.
The next justified algorithm is a bounded graph metric or learned finite
message quotient over the common representation, selected entirely on grouped
development folds and then transferred unchanged. Exact action terminals,
ports, and collision certificates remain immutable, and no recurrence audit is
eligible until that transfer gate passes.

### Continuous common-graph metric

The exact-vocabulary failure is followed by a bounded metric, without changing
the candidate set. Ninety-two fixed invariant measurements are partitioned
into five independently selectable channels:

- colored action geometry and chirality;
- incoming port-role chemistry and multiplicity;
- normalized action/parent/source pose geometry;
- radial environment summaries; and
- directed endpoint-incidence counts and cross distances.

Nearest training branches are reduced to one nearest representative per
nucleus before voting. This prevents repeated symmetry-related candidates from
acting as independent evidence. The capacity grid contains eleven fixed feature
families, neighbor counts `3 / 5 / 9 / 13`, weighted and unweighted votes, and
admission thresholds `.5 / .6 / .7 / .8 / .9`. All are selected by complete
whole-nucleus development refits with a 95% precision floor. Geometry receipts
are cached across label shuffles; only label-dependent votes and capacity
selection are refit.

| continuous port-graph metric | result |
| --- | ---: |
| selected channels | pose + endpoint incidence |
| group neighbors / weighted | 13 / yes |
| admission threshold | 0.7 |
| development exact selections | 6 / 6 |
| supplied development nuclei reached | 6 / 9 |
| shuffle median / maximum | 5 / 7 |
| development plus-one p-value | `.46875` |
| wide exact ranks | 5 / 2 |
| wide selected exact / false | 0 / 0 |
| external exact / false p-values | `1 / .53125` |
| autonomous / stationary / exponential | false / false / false |

The metric improves strict development coverage from 4 / 9 to 6 / 9 and
correctly rejects absolute action shape and radial-environment channels. The
gain is reproducible under shuffled labels and does not produce a wide commit,
so it is not deployed. Exact branches appearing at ranks five and two show that
continuous incidence geometry contains ordering signal, but not a validated
decision boundary. The next gate is a learned finite relational message
quotient on the same graph, with unchanged grouped shuffles and wide transfer.

### Finite relational port-message quotient

The next gate is now implemented. A generic quotient assigns bounded messages
to the three canonical action nodes and three pairwise incidence edges of the
shared port graph. It exposes 216 fixed proper-SE(3)-invariant measurements
(159 node and 57 edge), admits states only after recurrence in independent
training nuclei, and computes group-balanced positive rates. It cannot add,
remove, or alter an exact candidate.

| finite relational quotient | result |
| --- | ---: |
| selected domain / bins | nodes / 3 |
| independent-group support / retained tokens | 4 / 8 |
| frozen admission threshold | 0.55 |
| finite recurrent states | 362 |
| development exact selections | 4 / 4 |
| supplied development nuclei reached | 4 / 9 |
| grouped-shuffle median / maximum | 4 / 5 |
| development plus-one p-value | `.96875` |
| wide exact ranks | 3 / 1 |
| wide selected exact / false | 0 / 0 |
| autonomous / stationary / exponential | false / false / false |

The exact wide branches move closer to the front, so relational messages do
capture useful ordering structure. The selected development rule is not better
than shuffled labels and its frozen threshold admits neither wide branch.
Accordingly it remains a diagnostic library entry, not a tree-search policy.
No promoted hierarchy or recursive growth run is licensed by this result.

### Sequential port-obligation automaton

The next representation uses branch dynamics rather than a larger static
message vocabulary. Each existing exact candidate is replayed for sixteen
target-free steps. Every step becomes one canonical finite state containing
only bounded role discharge/production, relation loss/gain/retention,
contradiction flags, and simultaneous selected-pair incidence. Counts saturate
at four; raw role identities, atom coordinates, targets, and material labels
are absent. One training nucleus supplies one balanced mean per state.

| finite obligation automaton | result |
| --- | ---: |
| trajectory candidates / groups | 120 / 10 |
| supplied groups | 9 |
| frozen finite states | 102 |
| state support histogram (groups → states) | 1→47 · 2→38 · 3→9 · 4→3 · 5→1 · 7→4 |
| branch value | mean of four weakest recognized states |
| heldout exact supplied groups | 8 / 9 |
| heldout correct colored sites | 27 / 28 available |
| prior relational rule | 7 / 9 |
| shuffle median / maximum | 5 / 7 |
| plus-one grouped-shuffle p-value | `.03125` |
| autonomous / stationary / exponential | false / false / false |

The result demonstrates that persistent weak obligations carry information
which the static quotient discards. It is nevertheless exploratory: the fixed
state form was developed on this consumed corpus, 47 states have only one-group
support, and one supplied nucleus still fails. The model is frozen as a future
disjoint-confirmation candidate,
not installed as the default GCTS marking. A new target-blind confirmation must
reproduce the gain before this score may commit branches or feed recursive
promotion.

### Fresh disjoint obligation confirmation

The exploratory automaton was frozen into a geometry-only preregistration
before any confirmation atom was generated. The maximin grid rule selects
`(-110,-70,-70)`. Its complete 32.5623-radius rollout domain is 87.178 units
from every consumed domain, exceeding the frozen 71.125-unit requirement.

| one-shot obligation confirmation | result |
| --- | ---: |
| seed / target atoms | 480 / 2,066 |
| complete terminal counts | 8 → 40 → 152 |
| frozen dual-ranker portfolio | 13 |
| exact candidates supplied | 2 |
| first exact automaton rank | 5 |
| selected correct / false sites | 2 / 1 |
| recognized state fraction | 6.25–18.75% |
| selected target-free rollout | 16 steps |
| target opens / bound stability | 1 / bounds 72=73 |
| confirmation gate | **red** |

Every candidate, trajectory, automaton score, and receipt hash froze before
the single target call. The target was used only for final scoring. Candidate
supply is therefore not the blocker: the finite state vocabulary shifts too
strongly to the disjoint nucleus. The target is consumed, no retry or posthoc
threshold is allowed, and the automaton is rejected as a default GCTS policy.

### Obligation backoff and order-sensitive value audit

The consumed confirmation now has a separate target-free trajectory receipt.
It reproduces candidate counts `8 → 40 → 152`, all 13 retained trajectories,
and the original candidate, portfolio, and execution hashes without rebuilding
the target. New models freeze their complete ordering against this receipt;
only then is the published partial label ordering joined.

The first train-only repair is a finite exact→role-shape→aggregate backoff. It
raises recognized-state coverage for the published-known exact branch from
`.125` to `.75`, but fails the causal selection control (`p=.1875`) and moves
the branch from rank 5 to rank 8. Two softer ID-free metrics were then audited:

| grouped obligation audit | pooled role | ordered temporal |
| --- | ---: | ---: |
| selected feature count | 270 | 1,620 |
| heldout AUC | `.863712` | `.749792` |
| heldout log-loss | `.501003` | `.551357` |
| AUC / log-loss shuffle p | `.03125 / .03125` | `.03125 / .03125` |
| exact top actions | 8 / 10 | 8 / 10 |
| top-action shuffle median / p | `7 / .50` | `7 / .50` |
| consumed known-exact rank | 13 | 8 |

The distinction matters: both coordinate systems contain statistically real
group-heldout discrimination, but neither validates the discrete branch choice
that growth requires. Candidate geometry and exact certificates remain fixed,
the consumed target is not reconstructed or reopened, and neither score is
deployed. More independent ambiguous nuclei—not posthoc retuning on the same
ten groups—are required before another confirmation or clusters-of-clusters
growth claim is eligible.

### Preregistered twenty-nucleus obligation transfer corpus

The next development batch is fixed before atom access. Twenty maximin grid
centres have complete radius-32.5623 rollout domains separated by more than
71.1246 units from each other and every consumed nucleus. Workers receive only
colored R9 seeds. They freeze complete `8 × 8 × 8` three-action trees, a union
of the first eight scalar and first eight fusion branches, and sixteen-step
relational obligation trajectories. Only after all twenty geometry digests
exist are R14.5623 labels constructed. Oracle lift bounds 84 and 85 reproduce
all crops exactly.

| expanded obligation development | result |
| --- | ---: |
| disjoint nuclei / retained branches | 20 / 303 |
| nuclei supplying an exact branch | 8 |
| bounded model specs / geometry representations | 162 / 22 |
| selected representation | 8-step, 2-bin temporal · 9 unweighted groups |
| selected exact nuclei | 7 / 8 |
| selected correct sites | 41 |
| shuffle maximum exact / sites | 8 / 40 |
| exact-action / site-yield p | `.125 / .03125` |
| exact-action / site-yield gate | **red / green** |

All 31 null trials shuffle the paired `(exact, correct-sites)` label inside
each nucleus and repeat the full 162-spec selection. The site result therefore
is not a fixed-model comparison against an underfit null: 41 correct selected
sites exceeds every refitted shuffle. But exact whole-branch choice does not
beat the null. The corpus is consumed development evidence and the model is
not installed. The next implementation step is a site-resolved cluster action
that can preserve this significant local signal while still requiring full
colored support and port certificates before promoting a child or a
cluster-of-clusters parent. No fresh confirmation is eligible yet.

### Site-resolved obligation action

The fixed branch geometries are preserved while each of their three emitted
colored sites receives its own bounded section. The section combines temporal
obligation discharge, target-free frontier evolution, and proper-SE(3)
invariants of the colored three-site terminal. It may rank a frozen action but
cannot splice branches, move sites, or promote a partial child. Whole-action
value is a predeclared aggregation of the three site scores.

| site-resolved development | result |
| --- | ---: |
| emitted-site rows | 909 |
| correct / incorrect site labels | 462 / 447 |
| selected model | k=7 weighted · mean aggregation |
| exact supplied nuclei selected | 8 / 8 |
| correct selected sites | 45 |
| 31-shuffle maxima exact / sites | 7 / 39 |
| exact / site plus-one p | `.03125 / .03125` |
| development gate | **green** |

This is a meaningful improvement over the temporal whole-action model's
`7/8` exact and 41-site result. It is still development evidence, so the model,
source hashes, geometry-only maximin centre, three-wave protocol, and strict
`9/9` exact-site gate are published before the next atom is generated.

### Preregistered site-resolved confirmation

The fresh centre `(0,-120,-160)` is 118.322 units from every consumed rollout
domain. A 480-atom R9 seed drives three target-free self-fed waves. Candidate
trees and scalar/fusion portfolios freeze before a single target opening:

| confirmation wave | complete tree | frozen portfolio | exact supplied | selected correct |
| ---: | ---: | ---: | ---: | ---: |
| 1 | `8→40→157` | 14 | 0 | 0 / 3 |
| 2 | `8→39→144` | 15 | 1 | 2 / 3 |
| 3 | `8→38→136` | 15 | 1 | 0 / 3 |

The posthoc target contains 2,031 atoms, and lift bounds 108 and 109 reproduce
it exactly. Every candidate digest, portfolio digest, rollout, site score, and
selected successor cloud was fixed before that one target factory call. The
strict confirmation is therefore **red** at `0/3` exact actions and `2/9`
correct selected sites. Wave one diagnoses missing exact supply in the frozen
portfolio; waves two and three diagnose value transfer because exact actions
exist but are not selected. The target is consumed with no retry. This result
does not authorize autonomous growth, clusters-of-clusters promotion,
stationarity, or an exponential IQC claim.

### Consumed confirmation: proposal reach versus value

The first red wave is exhaustively separated into proposal and ranking
failures. All 157 terminals in the frozen `8→8→8` tree are rolled out and
site-scored before the already-consumed target is reconstructed. Their exact
count is zero: widening the two-head portfolio cannot repair this tree.

Six target-free reach schedules are then frozen and scored posthoc:

| reach schedule | terminal counts | checks | exact terminals |
| --- | ---: | ---: | ---: |
| `8→8→8` | `8→40→157` | 392 | 0 |
| `12→4→8` | `12→37→166` | 356 | 1 |
| `12→8→8` | `12→62→216` | 604 | 1 |
| `16→4→8` | `16→53→262` | 504 | 2 |
| `16→8→8` | `16→92→360` | 880 | 2 |
| `24→4→8` | `24→85→470` | 800 | 4 |

The minimal `12→4→8` repair is strictly better on this nucleus: it restores
exact supply and uses 36 fewer proposal checks. But the sole exact terminal is
ranked 107 by fusion and 114 by the scalar head, so keeping a practical top-8
portfolio still loses it. This rules out both “just widen the portfolio” and
“just widen every level.” The next implementation must apply a transferable
connection/site section earlier in the tree, before expensive complete-terminal
fusion. The target is consumed; no confirmation or growth claim is revised.

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

All 31 null trials shuffle the complete sixteen-candidate label vector inside
each nucleus and repeat the full 162-model selection. This is strong evidence
for a bounded local connection-value representation on consumed development
data. It is not evidence for autonomous continuation or recurrence.

### Preregistered rollout-ranked confirmation

The temporal-61 model, source/fixture hashes, complete `12→4→8` geometry, the
`(4→8→8)` retained portfolio, three-block self-fed protocol, and maximin centre
`(120,-40,-220)` are committed before atom access. The 476-atom seed produces
all three target-free candidate trees, rollouts, scores, and successor clouds
before one target factory call creates the 2,069-atom reference.

| confirmation block | marked | stable-prefix baseline |
| ---: | ---: | ---: |
| 1 | 2 / 3 | **3 / 3 exact** |
| 2 | 2 / 3 | 2 / 3 |
| 3 | 2 / 3 | 1 / 3 |
| total | 6 / 9 · 0 exact blocks | 6 / 9 · 1 exact block |

The marked and baseline arms tie in aggregate site count, but the mark replaces
an exact first baseline block with an inexact one. The receipt was frozen after
one target opening and is not retried. First-block transfer, three-block
sustained continuation, autonomous finite growth, stationary recurrence, and
exponential IQC growth are all red.

### Shared marking-library tree

The search layer now expands each physical frontier once and lets multiple
frozen markings order that identical action set. A bounded round-robin beam
retains the connection head and rollout head as distinct physical states, while
deduplicating states reached by both markings. Candidate digests are invariant
to marking order, and neither the generic tree nor the IQC adapter accepts a
target API.

On the already-consumed rollout confirmation, the first immutable frontier has
eight actions: connection selects index 0, rollout selects index 7, and the
shared width-two tree retains both. Across three self-fed blocks it expands
`8 → 16 → 16` candidates and retains `2 → 2 → 2` states. Posthoc scoring gives
`6 / 9` colored sites and zero exact terminal paths for both survivors. This is
a genuine repair of candidate retention and rollback supply, but it does not
resolve value transfer or justify autonomous, stationary, or exponential IQC
growth.

### Prefix channel portfolio and bounded-reach failure boundary

The shared portfolio API now supports a depth-dependent beam schedule,
parent-balanced or global allocation, additive or stage-local replacement
scores, and finite marking channels. Each ranking covers distinct channel
cells before taking a second state from one cell. The IQC adapter uses frozen
standardized local-section cells and proper pose/port channel codes; neither
contains target coordinates or labels.

On the consumed rollout nucleus, outer lineage retention `2→4→8` expands
`8→16→32` candidates and preserves eight terminal paths, but exact supply is
zero and the best path is `7/9`. A posthoc oracle prefix trace then removes
learned pruning while keeping finite proposal reach. At `12→8→16`, exact
prefix counts are `7→21→56`, `5→10→25`, and `3→3→5` across the three blocks;
an exact three-block path therefore exists in the frozen geometry. The first
correct final port after an exact two-site prefix is ranked 14 among 740
exposed ports, outside the former final reach of eight.

The autonomous channel portfolio remains red. With reach `12→8→16` and beam
`8→16→32`, it retains two exact first blocks, expands 64 second-block terminal
states, and retains zero exact second blocks. A complete bounded block-two
audit finds 25 exact terminals among 600; the best frozen local-section rank is
19 and the pose/port rank is 135. Thus bounded geometry is available, but the
current marking does not preserve the correct lineage. These are consumed
diagnostics only; no fresh confirmation, autonomous continuation, stationary
production, or exponential IQC claim follows.

### Clusters² future-option portfolio

The tree now assigns a parent an explicit downstream option value instead of
ranking it only by the three placements it has already made. Every one of the
eight frozen first-block parents receives its complete second-block tree
(`126–141` terminals). Four train-frozen recurrent heads—base, colored
geometry, ports, and coupled pose/port—score exactly those same child IDs. For
each channel the parent value is the mean of its best eight children; the
four-parent beam first admits one parent per channel and then deduplicates
physical states. No target, material family, lattice coordinate, or candidate
ID enters a marking score.

| consumed two-block audit | result |
| --- | ---: |
| exact parent in the eight-parent source beam | rank `8` |
| exact parent by base / colored / ports / coupled option | `5 / 5 / 1 / 2` |
| exact parent by mean option | `3` |
| selected parent IDs | `7 / 1 / 8 / 5` |
| selected child portfolio under exact parent | `20` distinct terminals |
| retained exact parent→child path | `8 → 123` |
| any channel's greedy best child exact | no |
| marginal-preserving shuffle retention | `15 / 31` |
| retention / mean-rank plus-one p | `.50 / .40625` |

This closes the specific pruning failure found by the prefix audit: the exact
first parent and one exact child are now simultaneously present in a bounded,
target-free clusters-of-clusters portfolio. It does **not** prove that the
learned value identifies the path—half the weak nulls also retain it, and no
greedy child is exact. The next gate is a group-heldout parent-option corpus
followed by a third-block self-fed execution from the retained six-action
states. Autonomous commitment, stationary recurrence, and exponential IQC
growth remain red.

The group-heldout parent-option corpus is now frozen and audited. It contains
`1,278` six-action parents from ten consumed development nuclei, `142` exact
parent labels, and a proper-SE(3)-invariant child-frontier graph of at most
eight target-free actions under every parent. In each fold, order-one and
order-two typed-port graph values fit only the other nine nuclei; fixed local
port-mass and live-continuation channels score the identical child IDs.

| leave-one-nucleus-out option audit | result |
| --- | ---: |
| supplied held-out nuclei | `9 / 10` |
| exact parent retained by width-four option beam | `8 / 9` |
| exact parent selected by order-two top-one | `8 / 9` |
| mean first-exact rank sum | `30` |
| marginal-preserving retention / rank p | `.03125 / .03125` |
| individually labelled child actions | no |

Thus the option values are transferable and sharply non-random, but the
portfolio ties rather than beats the strongest existing graph head. This
closes the proposed group-heldout *parent-supply* gate while leaving the
incremental causal-superiority gate red. The next admissible experiment must
reconstruct the retained parent states, freeze executable child actions, and
open a later annulus only afterward; parent correctness cannot be recycled as
a child label.

The executable later-annulus audit is also complete. Each of the forty
retained parents becomes a new colored seed at
`R3 = R2 + Rseed = 32.562305898749054`; the unchanged `8×8×8` bounded search
enumerates `5,091` third-block terminals. All actions and four frozen marking
scores are serialized before the larger consumed targets open once. The
library keeps four terminals per parent (`160` total).

| executable third-block audit | complete tree | retained library |
| --- | ---: | ---: |
| exact-parent nuclei | `8` | `8` |
| nuclei with an exact third-block path | `6` | `3` |
| exact end-to-end third-block paths | `90` | `6` |
| terminal states | `5,091` | `160` |

The feedback loop initially identifies two apparent blockers. In two nuclei
an exact parent has no exact third-block terminal under the bounded top-8
candidate reach. In three other nuclei exact terminals exist but the marking
drops them; first-exact channel ranks range as high as `109`.

The two reach failures are now resolved diagnostically. For their four exact
parents, a lexicographic uniform-cost search follows only target-correct
prefixes through the unchanged, untruncated frozen frontier. It quotients
commuting action orders by the resulting colored cloud and minimizes
`(maximum local rank, rank sum)`. All four parents have an exact three-action
path. Their minimum bottleneck rank is uniformly `12`, with minimum rank sums
`21` or `23`; the deployed reach `8` supplies zero of four. The grammar does
not lack these poses. This is an already-consumed-target diagnostic, however,
so it cannot tune or deploy a top-12 rule. It specifies the next causal gate:
learn reach or channel diversity on training nuclei, freeze it, and test it on
a disjoint target.

The first terminal-value attempt is also frozen and rejected. A nested
group-heldout ridge selects among score-only, geometry-only, and combined
proper-SE(3)-invariant representations of all `5,091` terminals. With the same
four-per-parent budget it retains exact paths in `2 / 6` supplied groups and
four paths total, versus `3 / 6` and six paths for the incumbent portfolio.
Thirty-one within-parent label shuffles yield retention `p=.4375` and first
rank-sum `p=.21875`. Terminal triangle/radius/cross-distance geometry is
therefore not promoted as a marking. Candidate geometry stays immutable and
targets never enter generation, but autonomous, stationary, and exponential
IQC claims remain ineligible.

The next repair changes *which* eight children are represented, not how many
are rendered. `pose_port_channel_responses` exposes the five continuous
train-frozen connection responses already quantized by the recurrent state
model. The generic `select_pose_port_channel_diverse` policy retains three
leaders under the scalar state probability, one previously unseen leader per
connection channel, then fills any duplicate slots from the scalar order. The
exact candidate geometry, child budget, collision rules, and target boundary
are unchanged.

On the four consumed parents that required bottleneck rank twelve, this fixed
`3 + 5` allocation recovers `11`, `10`, `11`, and `10` exact three-action
paths. The all-development audit then reuses those immutable receipts and
generates eleven other exact-parent trees before one target open:

| consumed exact-parent supply | scalar top-8 | channel-diverse top-8 |
| --- | ---: | ---: |
| parents with an exact path | `11 / 15` | `15 / 15` |
| eligible nuclei with an exact path | `6 / 8` | `8 / 8` |
| exact paths | `90` | `472` |
| child constructions per state | `8` | `8` |

All six previously supplied transfer nuclei remain supplied, while design
nuclei one and two are recovered. This passes the consumed-development
preservation gate and turns the rank-twelve diagnosis into a generic GCTS
implementation improvement. It is not fresh confirmation: the `3 + 5`
allocation was proposed after those two failures were inspected. The scalar
production default is therefore not silently replaced, causal-superiority is
not claimed, and the next gate is a preregistered disjoint nucleus followed by
winner selection and exact cluster-of-clusters promotion.

### Fresh bounded joint-action supply confirmation

The successor keeps each three-site child action intact. Its 502
proper-SE(3)-invariant features contain no candidate ID, global frame, lattice
address, family label, or target value. Grouped consumed-nucleus selection
freezes a fair schedule of one joint-ranked child plus five base-channel
fallbacks under each of all eight parents. That schedule supplies all `6 / 6`
known exact parent groups and their exact third blocks while reducing
development prefix expansions from `635` to `191`.

The implementation memoizes only the geometry of equivalent unordered action
sets. Path-dependent marking probabilities and cumulative scores remain
separate. A consumed-prefix parity audit produces identical 132 terminal
states with and without the memo, reduces unique geometry advances from `368`
to `177`, and measures a `1.70×` speedup.

The rule, source hashes, a 48-prefix ceiling, a 1,200-second wall-time gate,
and the geometry-only maximin centre `(160,-180,-140)` were committed before
the fresh nucleus was generated. The radius-32.56 domain is 161.25 units from
all 89 prior centres. The target is opened once only after the candidate queue,
selected prefixes, 6,099 lineages, memo telemetry, and receipt digest freeze.

| one-shot fresh receipt | measured |
| --- | ---: |
| seed / target atoms | `474 / 22,867` |
| scheduled / eager prefixes | `47 / 168` |
| naive / unique geometry advances | `17,240 / 8,207` |
| saved geometry advances | `9,033` |
| wall time / fixed limit | `1,119.19 s / 1,200 s` |
| exact first / second prefixes | `8 / 34` |
| exact nine-action lineages | `410 / 6,099` |
| parents with exact supply | `8 / 8` |

This passes the preregistered fresh candidate-supply and bounded-compute gates.
It is stronger than a target-guided existence diagnostic because every branch
and score is frozen first, but it remains a *supply* result. No winner is
selected or committed, so autonomous continuation, recurring cluster-of-
clusters stationarity, and exponential IQC growth remain explicitly red.
### Corrected fourth-block replay and bounded marking transfer

The depth-independent lineage worker had a serialization defect: it globally
sorted nine actions and only then divided them into three radius blocks.  The
correct contract canonicalizes each unordered three-action block separately.
After this correction, both audited shards replay all `64 / 64` retained
parents with zero replay contradictions.

The corrected width-eight development control emits `8,872` successors from
`11,794` unique geometry expansions (`23,888` naïve).  Its best successor is
`11 / 12` correct and no exact fourth block is supplied.  A consumed-target
uniform-cost reach audit locates an exact path at ranks `7, 9, 9` (rank sum
`25`), proving that proposal geometry is present but the width-eight policy
mechanically excludes it.  A disjoint reach-nine receipt emits `12,861`
successors from `16,524` unique expansions (`33,543` naïve); after candidate
freeze, `61` successors are exact and all three exact nine-action parents
survive replay.

To recover that supply without uniformly widening the tree, a frozen
five-channel pose/port marking is fit on consumed nuclei 0 and 1.  Its corpus
contains `10,721` causal candidate descriptors and `1,044` correct actions;
the representation contains no raw IDs, absolute frame, target positions, or
new candidate geometry.  On untouched nucleus 2, the marking is applied at
reach eight before the target is opened.  It emits `8,382` successors from
`11,260` unique expansions (`23,536` naïve).  Post-hoc scoring finds `82` exact
twelve-action successors spanning every one of the `14` exact parents.

This passes a marked fourth-block **proposal-supply** gate at the original
local budget. A later same-nucleus ablation freezes both arms on untouched
nucleus 3 before opening the target. The unmarked arm has `96` exact
twelve-action successors from `10,868` unique geometry expansions; the marked
arm has `100` from `11,078`. Both span all `16 / 16` exact parents. Thus the
mark supplies `1.0417×` as many exact continuations for `1.0193×` unique
geometry work, below the predeclared `1.05×` work cap. The causal marked-supply
gate is green.

The subsequent one-shot autonomous selector freezes a 32-branch causal
shortlist, runs one target-blind fifth-block lookahead, freezes 31 shuffled
control orders, and only then opens untouched nucleus 4. It is red: all 32
branches are inexact. The failure is not missing full-beam supply. Post-hoc
scoring of the unchanged `8,649`-candidate receipt finds `96` exact successors
under two parents, with first global rank `116`. Within each exact parent,
however, the first exact child is rank `2`. The global cutoff erased parent
diversity; a width-two-per-parent beam retains one exact child from each exact
parent in `128` branches.

Nucleus 4 is not retried. Parent-balanced continuation must be frozen and
tested on a new disjoint nucleus. Autonomous selection, stationary recurrence,
and exponential IQC growth remain unclaimed.

### Disjoint parent-balanced fourth-block result

Width eight per parent—not the post-hoc width-two minimum—is the frozen policy:
it preserves every exact-parent group in two train-heldout development folds
(`14 / 14`, `16 / 16`). The executor first retains eight nine-action lineages
under each of eight first parents, then eight marked fourth-block children
under each of the resulting 64 parents. The full 512-candidate receipt freezes
before target construction.

The first preregistered target at `(280,220,0)` was consumed by a scorer bug:
frozen six-decimal actions were checked by exact eight-decimal dictionary
lookup rather than the project-wide species-aware `10⁻⁵` matcher. Its `0 / 512`
result is mechanically retained but scientifically uninterpretable; the target
was neither reopened nor rescored.

The corrected second preregistration selects the next geometry-only maximin
centre `(-280,160,-160)`, includes the failed domain in the spatial exclusion
set, hashes the tolerant scorer, and serializes the post-open target sites.
Its one-shot outcome is valid and red:

| quantity | result |
| --- | ---: |
| seed / target atoms | `483 / 47,526` |
| raw complete nine-action lineages | `1,114` |
| retained nine-action parents | `64` |
| retained twelve-action candidates | `512` |
| exact terminal fourth blocks | `8` |
| exact retained nine-action parents | `0` |
| exact complete paths | `0` |
| best complete path | `11 / 12` |
| execution / scoring time | `1,721.03 s / 0.083 s` |

The eight exact terminal triples show that the learned fourth-block marking
still supplies correct connection geometry on a disjoint nucleus. Failure is
at or before the nine-action parent-balanced selection. The receipt did not
retain the other 1,050 raw nine-action geometries, so it cannot separate an
upstream supply failure from selector pruning after the fact; no re-execution
is permitted. This instrumentation gap and the 28.7-minute runtime are both
benchmark failures. The next implementation must serialize the full parent
antichain, expose stage timings, and share fourth-frontier prefix caches before
another autonomous confirmation is justified.

### Full-width consumed-lineage audit

The V3 executor implements the missing auditability without reopening either
fresh confirmation. On the already-consumed development nucleus
`(-70,10,70)`, it serializes every raw nine-action lineage, its parent class,
the selected raw indices, deterministic receipt digest, and per-stage wall
times before constructing the known scoring cloud. The species-aware
`10⁻⁵` scorer is attached only afterward.

| consumed V3 quantity | result |
| --- | ---: |
| raw nine-action lineages | `1,102` |
| exact raw lineages / parent classes | `3 / 1` |
| selected lineages | `64` |
| exact selected lineages / parent classes | `3 / 1` |
| exact-parent retention | `all retained` |
| fourth-block candidates | `512` |
| exact full twelve-action paths | `21` |
| exact terminal triples | `476` |
| total execution time | `2,179.18 s` |
| fixed `600 s` runtime gate | `fail` |

The selector is therefore not the loss mechanism on this consumed nucleus:
it retains every exact raw parent supplied to it. This does **not** repair or
reinterpret the disjoint fresh result, whose unselected raw lineages were not
stored. It only resolves the selector-versus-supply ambiguity where a complete
raw receipt now exists.

Timing identifies the current engineering bottleneck. First/second frontiers
take `383.44 s`, scheduled third frontiers `169.53 s`, transported port graphs
`208.02 s`, lineage fitting/selection `44.38 s`, and chunked fourth frontiers
`1,373.81 s`. Fourth-frontier generation is 63.0% of the total even after
worker-level runtime reuse. The next optimization must eliminate repeated
frontier/graph work across sibling parents rather than tune the inexpensive
selector. This is consumed diagnostic evidence only; autonomous, stationary,
and exponential IQC growth remain red.

A target-free single-parent profile isolates the largest inner-loop cost:
nearest-prototype assignment repeatedly compares the same local cluster color
against the same frozen table. Bounded reuse of that exact map leaves the
`8 → 38 → 143` frontier states and action digest
`707a39934736f64001c7da255e444edb0051a4c967465472f6f9dc2e3b65a10e`
unchanged, while the measured parent drops from `43.97 s` to `18.85 s`
(`2.33×`). The cache key contains only the local cluster color and frozen
prototype vocabulary—never a target, family label, or lattice coordinate.
Incremental local-cluster typing, exact anchored-support indexing, single-pass
port-channel evidence, and bounded memoization of the finite semantic port
role remove the remaining repeated inner-loop work.

The full target-free consumed audit has now been revalidated. All seven frozen
outputs are exactly identical: the second-branch receipt, scheduled prefix,
lineage model, raw-lineage antichain, selected indices, 512-candidate receipt,
and deterministic execution receipt. The result is pinned at:

| optimized consumed V3 quantity | result |
| --- | ---: |
| first/second frontiers | `83.92 s` |
| scheduled third frontiers | `74.42 s` |
| transported port graphs | `18.97 s` |
| lineage fitting/selection | `44.47 s` |
| chunked fourth frontiers | `214.58 s` |
| total | `436.36 s` |
| speedup over original audit | `4.99×` |
| fixed `600 s` runtime gate | `pass` |
| frozen-output parity | `7 / 7 exact` |

This is an engineering result on an already-consumed diagnostic nucleus. It
does not alter the scientific interpretation: the disjoint fresh audit still
has zero exact complete paths with a best result of `11 / 12`, and generic
autonomous, stationary, and exponential IQC growth remain red.

### Fresh full-width confirmation after optimization

Before opening another target, a third full-width protocol froze the current
source hashes, four-worker schedule, width-eight parent balance, exact colored
`10⁻⁵` scorer, `600 s` runtime ceiling, and the geometry-only maximin center
`(-180,-80,-300)`. That center is `231.52` units from the nearest recorded
nucleus, versus the required `107.12`-unit domain guard. The seed is opened at
radius 9; every raw and selected lineage is serialized before the radius
`41.5623` target is constructed once.

| fresh auditable quantity | result |
| --- | ---: |
| seed / target atoms | `491 / 47,530` |
| raw nine-action lineages | `1,087` |
| exact raw nine-action lineages | `0` |
| selected nine-action lineages | `64` |
| exact selected lineages | `0` |
| fourth candidates | `512` |
| exact terminal fourth blocks | `197` |
| exact complete twelve-action paths | `0` |
| best complete path | `11 / 12` |
| target-free execution | `534.84 s` |
| fixed runtime gate | `pass` |

This resolves the failure boundary on a genuinely disjoint nucleus. Correct
fourth-block connection geometry is abundant, but none of the 1,087 upstream
nine-action parents is exact. Six best candidates differ only in their fourth
continuation and all inherit the same single false upstream action at
`(-190.532889,-78.631190,-303.052622)`, color `Y`. Therefore widening or
retuning the downstream selector cannot repair this result: the next generic
improvement must make upstream GCTS propose or preserve an alternative to that
incorrect attachment using only causal local connection evidence. The result
is red for exact fresh continuation, autonomous growth, stationarity, and
exponential IQC growth; it was not retried.

The immediate upstream experiment is deliberately compute bounded. V4 always
retains the eight joint prefixes and adds at most four fallbacks, but only when
a fallback removes an action present in every joint prefix. On the four
consumed development cases this selects `8 / 12 / 11 / 9` prefixes, preserves
all six known exact child groups, and averages 10 prefixes instead of the full
schedule's 47.25. On the no-saturation consumed nucleus it adds zero fallbacks
and reproduces the exact V3 raw-lineage digest
`b349bc646d7a420822cf6754018ec21a4445cdf598a1df87d9391d2f35d2b74a`.

This is not yet a positive supply result. In the wider 16-prefix development
audit, all three exact nine-action lineages still come from the original joint
tier and none from the structural fallbacks. V4 therefore remains
experimental while its expanded receipt serializes every second-frontier
alternative and channel score before any future target. Another fresh nucleus
should be consumed only after the upstream policy shows positive grouped
evidence beyond merely preserving existing paths.

### Local bond-valence satisfaction channel

The browser laboratory now has an opt-in local bond-valence-sum residual for
candidate ordering. It uses exact supplied oxidation states and checked
`bvparm2020` cation-anion parameter ranges in physical angstrom coordinates,
computes `s = exp((R0 - R) / B)`, and compares the total absolute valence-sum
residual on the sites changed by an exact attachment. Unsupported pairs,
occupational alternatives, and missing charge labels fail closed. The frozen
candidate set, exact proper-SE(3) poses, collision gates, and hard admission are
unchanged; only an explicitly enabled soft score can alter ordering. The work
ledger and receipt retain parameter provenance, local before/after residuals,
unsupported pairs, score contribution, and exact evaluation counts. This
finite local descriptor is not an energy, electron-density or charge-transfer
model, force calculation, relaxation, rate, or physical clock.

### Directional bond-valence coordination balance

The same frozen frontier now also evaluates the proper-rotation-invariant bond
valence vector resultant `V_i = Σ_j s_ij r̂_ij` for each affected local site,
following Harvey *et al.* (2006),
[doi:10.1107/S0108768106026553](https://doi.org/10.1107/S0108768106026553).
An unresolved affected or emitted ion receives its supplied oxidation-state
magnitude as the explicit baseline burden; a resolved site contributes the
magnitude of its vector resultant. The selected soft score can be scalar,
vector, or the equal mean of both, without changing the exact candidate set,
proper-SE(3) pose, collision tests, or hard admission. A live two-axis portrait
shows every candidate's scalar and vector score and retains all resultants,
parameter rows, work counts, and provenance in the receipt. Near-zero balance
is expected only under the spherical-ion coordination hypothesis. Lone-pair,
electronic, and steric anisotropy are explicitly unmodeled and may make a
nonzero vector physical; no force, torque, energy, relaxation, or time is
inferred.

### Bond-valence state across structural leaps

The structural-leap audit now freezes a bounded full-state coordination
snapshot before and after each retained GCTS update. Up to 96 centers with
complete supplied oxidation states are chosen by deterministic radial
stratification. For every sampled center, all charged neighbors inside the
largest checked bond-valence cutoff are obtained from the exact spatial index;
the center's scalar mismatch and vector resultant are then evaluated in
angstrom coordinates. The aggregate reports RMS scalar mismatch, mean absolute
mismatch, mean and RMS vector magnitude, normalized vector imbalance, resolved
and unresolved centers, checked/missing pair types, context-site presentations,
and exact distance evaluations.

The browser renders these discrete states as an interactive scalar-versus-vector
path. The state index is a structural search leap, not elapsed time, and the
connected line is visual correspondence rather than an interpolated physical
trajectory. The observation is finite and does not synthesize periodic images.
It uses only supplied oxidation states, does not infer an energy or relaxation
direction, and does not alter candidate geometry, ranking, or hard admission.
The directional axis retains the same spherical-ion caveat: electronic,
lone-pair, or steric anisotropy may make a nonzero resultant physically
meaningful.

### Spatial bond-valence defect microscope

The current structure can now be inspected without replacing standard element
colors. Scalar mode surrounds up to 320 deterministically stratified charged
centers with a diverging wire halo: blue is underbonded, mint is near scalar
balance, and coral is overbonded. Directional mode colors the same halos by
bond-valence-vector magnitude and adds an arrow in the resultant direction.
The display scale is the sampled 90th percentile, bounded below by 0.1 valence
units so one outlier cannot collapse the visible range. The eight strongest
sampled sites can be selected to focus the 3D camera target.

For each center the map queries the exact spatial index through the largest
checked bond-valence cutoff and evaluates only explicitly supplied charged ion
pairs in angstrom coordinates. The receipt records the mode, sample and
resolution counts, cutoff, p90 display scale, context-site presentations, and
distance work without storing coordinates. This is an analysis overlay: arrows
are not forces, energy gradients, torques, or prescribed relaxation directions;
the finite crop receives no invented periodic images, and the map cannot alter
candidate geometry, ranking, hard admission, or search history.
## Build 164: scalar-spin geometry is now a preserved observation channel

The browser portal now retains explicit per-atom collinear spin scalars from NOMAD `calculation.charges[].spins` and lossless JSON inputs. It analyzes only the supplied scalar field: signed-site counts, normalized net signed population, and finite-crop distance-binned pair correlation `Σsᵢsⱼ/Σ|sᵢsⱼ|`. The 3D microscope adds polarity or local-correlation halos without replacing standard element colors. The experiment receipt hashes the ordered scalar records, records the NOMAD archive path and analysis method when present, and explicitly denies use in fitting or execution.

This closes a data/provenance and geometric-observation gap, not the magnetic-physics gate. The upstream schema defines a scalar `n_atoms` quantity and does not guarantee a vector axis or unit, so the portal does not label it μB and draws no spin arrows. No exchange model, magnetic Hamiltonian, periodic spin sum, domain structure, ordering temperature, spin dynamics, force, or growth preference is inferred. Collective magnetism remains in the open long-range/electronic-response row. Primary source: [NOMAD schema source](https://github.com/nomad-coe/nomad-schema-plugin-run/blob/0f1000184032b742da8b7f0421b5605a5b086918/runschema/calculation.py).
## Build 165: local centrosymmetry is now an interactive defect-sensitive observable

The portal now exposes the Kelchner–Plimpton–Hamilton centrosymmetry parameter as an inspection channel. For a selected even nearest-neighbor shell it solves the opposite-neighbor pairing exactly, reports both the raw sum of squared pair-vector residuals and a bounded scale-normalized amplitude, and records the selected atom pairs. Automatic shell selection is restricted to dimension-appropriate complete-shell candidates; centers without enough neighbors remain explicitly unresolved.

The distribution and three-dimensional halo are linked: a histogram bin isolates the corresponding local shells, and the spatial map preserves element-colored cores while adding a mint-to-coral inversion-asymmetry halo. The observable is translation-, proper-rotation-, atom-permutation-, and uniform-scale-invariant. It is post-hoc geometric evidence only; it does not infer a named defect, energy, kinetics, or thermodynamic phase.

## Build 166: centrosymmetry is now a certified structural-leap pathway

The reference configuration now freezes one dimension-appropriate complete-shell choice for every growth-state comparison. Each retained before/after state carries the same exact-pairing centrosymmetry histogram and aggregate statistics; the leap certificate derives a Jensen–Shannon distance, mean and p90 changes, high-asymmetry-fraction change, and resolved-shell accounting. This makes the display reproducible across leap-frogged structural states without treating the discrete search index as elapsed time.

Receipts, compact notebook trajectories, the interactive leap inspector, and the geometry-as-physics ledger all carry this evidence. The pathway remains a post-hoc validation channel and is never exposed to the growth ranker. A change in centrosymmetry is defect-sensitive evidence, but it is not a vacancy, interstitial, antisite, stacking-fault, dislocation, grain-boundary, stress, energy, temperature, transition-rate, or phase-transition assignment.

## Build 167: coherent local deformation is separated from non-affine motion

The imported fixed-topology ensemble now retains the complete per-site
least-squares deformation audit rather than only its residual. Twelve paired
minimum-image neighbor vectors determine the best local `F`; the portal derives
`E=(FᵀF−I)/2`, the equivalent deviatoric invariant
`sqrt(2 Edev:Edev / 3)`, signed volume change `det(F)−1`, physical and
scale-normalized `√D²min`, and selected/final nearest-neighbor identity change.
The best-affine residual is traced to Falk and Langer,
[doi:10.1103/PhysRevE.57.7192](https://doi.org/10.1103/PhysRevE.57.7192).

An interactive four-mode halo renders residual motion, coherent shear, signed
dilation, or cage exchange on the atom scene. The receipt hashes the complete
fitted local records, reports full-rank and withheld cages separately, and does
not embed coordinates or tensors. An unregularized source-moment rank test is
mandatory: regularization may stabilize `D²min` for planar data, but it may not
authorize a three-dimensional strain value.

This closes a geometric-observation gap only. No constitutive law converts the
invariants into stress, energy, modulus, plasticity, defect identity, barrier,
mobility, trajectory, growth rate, or physical time. The analysis is excluded
from clustering, marking learning, candidate generation, ranking, and hard
admission.

## Build 168: sample-relative local mismatch survives into the grown state

The live portal now projects its frozen colored contact, coordination, and
three-body angle envelopes back onto the current explicit solid. Each inspected
center retains the contact-length residual, separated angle-mode residual,
their established 0.55/0.45 ranking combination, and the ordered coordination
shortfall as distinct values. A spatial-index neighbor callback makes the
definition identical for small and large observations without an all-pairs
scan. Up to 1,200 deterministic centers are displayed and the receipt records
both coverage and sampling policy.

This diagnostic requires no atom correspondence between structural states, so
it remains available during leap-frogged growth where new atoms have no prior
identity. It does not feed its post-commit values back into the search. In
particular, coordination shortfall is not silently treated as strain: a free
surface, finite crop, unfilled frontier, and bulk defect can produce the same
signal. The map therefore makes geometric incompatibility inspectable while
explicitly withholding stress, force, elastic/frustration energy, bond order,
defect identity, kinetics, and physical time.

## Build 169: chemistry-resolved finite Debye scattering

The structural-observable card now supports arbitrary real site weights in its
dimension-aware finite Debye average. The normalization is
`I(q)/Σᵢwᵢ² = 1 + 2Σᵢ<ⱼwᵢwⱼK_d(qrᵢⱼ)/Σᵢwᵢ²`, with the same `sin(qr)/(qr)`
three-dimensional kernel and `J₀(qr)` intrinsic-two-dimensional kernel used by
the unit-weight control. Tests prove unit-weight parity, invariance to common
weight rescaling, non-negativity, and sensitivity of signed chemical contrast
to alternating multicomponent order.

The interactive channels are all-site unit density, per-chemistry-token
sublattice density, constant atomic-number weighting, and composition-centered
atomic-number contrast. The last two are intentionally called proxies: no
q-dependent atomic X-ray form factor or neutron coherent scattering length is
present. Refined occupancy amplitudes, anomalous terms, Debye–Waller factors,
instrument resolution, absorption, preferred orientation, and intensity
calibration remain outside the model. The receipt hashes the selected curve and
records every omitted channel. Retained structural-leap comparisons stay on
the immutable unit-weight basis, and no scattering value enters GCTS learning
or execution.

## Build 170: a geometric descriptor is checked against archived calculations

For an imported fixed-topology relaxation archive with at least three frames,
the browser fits colored contact-length, coordination, and angular envelopes
to the final archived geometry only. It evaluates the same deterministic set
of at most 256 atom-index-quantile centers in every frame using periodic
minimum-image vectors, then pairs mean contact-plus-angle mismatch with
same-run relative energy per primitive atom and residual-force RMS. An
interactive scatter plot reports paired counts, Pearson correlation, Spearman
rank correlation, and an ordinary least-squares guide; its points select the
corresponding archived structures.

The receipt hashes the per-frame geometric/calculation records and explicitly
records that energy and force never fit the geometry or rank growth. This is a
descriptive final-frame-referenced association within one correlated archive,
not independent validation, prediction, causal evidence, an energy model,
force field, reaction coordinate, physical trajectory, kinetics, or time.

## Build 171: geometry-reference sensitivity is explicit

The archived-calculation inspector now repeats its mismatch analysis with
three label-free geometric references: the final frame, the first frame, and
the pooled fixed-topology ensemble. Each mode learns distance, coordination,
and angular envelopes through the same code path and evaluates the same
deterministic centers. The interactive control makes reference dependence
visible while the receipt freezes the selected mode and all three energy/force
Pearson and Spearman summaries.

Neither energy nor residual force selects the reference or fits an envelope.
This is still a within-archive sensitivity study: frames are correlated, pooled
evaluation is descriptive rather than held out, and frame order is not elapsed
time. Reference robustness therefore does not establish prediction, causality,
an interatomic potential, force field, reaction coordinate, growth rank,
kinetics, or thermodynamic validity.

## Build 172: a compact geometric state faces a predictive preflight

Each archived frame now supplies three aggregate geometric features under the
selected final/first/pooled reference: mean contact-length mismatch, mean angle
mismatch, and mean coordination deficit. A fixed standardized ridge model
(`lambda=1`) maps those values separately to same-run relative energy and
residual-force RMS. With at least five complete pairs, every displayed
prediction is produced by a fit that excludes that frame. The portal reports
leave-one-frame-out Spearman correlation, Pearson correlation, MAE, RMSE,
`Q²`, and the full-fit standardized coefficients, and draws the prediction
residuals directly on the interactive scatter.

The experiment receipt hashes the withheld predictions and records the exact
features and fixed regularization. Calculation labels do fit this diagnostic
surrogate, while they still never fit the geometric envelopes. Because folds
belong to one correlated archive, this is not independent or transferable
validation. The model is excluded from clustering, marking, search ranking,
and admission and is not an interatomic potential, energy functional, force
field, reaction coordinate, causal mechanism, dynamics, kinetics, or time.

## Build 173: a frozen surrogate can face another calculation archive

The browser can now retain up to eight fitted geometric surrogate artifacts in
a session. Each artifact contains only its fixed three-feature normalization,
ridge coefficients, intercept, source-pair count, target quantity, and geometry
reference. A different NOMAD entry is evaluated with those numbers unchanged;
its energy or force values enter only the subsequent scoring calculation. The
same entry is explicitly rejected as a transfer target.

Cross-archive evaluation is fail-closed unless reduced occupational chemistry,
periodic axes, units, feature schema, target, reference mode, program name and
version, and the exact canonical normalized NOMAD method record all agree.
Method records are canonicalized recursively with sorted object keys; their
SHA-256 is retained while raw method JSON is omitted from the receipt. Relative
energies are still local to each archive and absolute energies are never
compared across entries.

The receipt hashes source artifacts and target predictions and records that no
refit or target-assisted prediction occurred. One compatible transfer does not
establish generalization across chemistry or electronic-structure methods and
does not create a potential, force field, reaction coordinate, causal model,
dynamics, kinetics, or time. In Build 173 the library remains diagnostic and
unavailable to cluster discovery, GCTS marking, search ranking, and admission.

## Build 174: a transferred geometric surrogate can be promoted—explicitly

The frozen cross-archive library now has a fixed promotion rule rather than an
informal visual judgment. A different exactly compatible archive must provide
at least five scored frames, no-refit Spearman prediction correlation at least
`0.80`, and predictive `Q² > 0`; target values remain post-hoc scoring labels
and never enter prediction. Failed checks are named and the control remains
disabled. A passing result merely makes an opt-in **Use as GCTS mark** action
available.

Growth candidates are evaluated with the same colored local constraint field
used for archive frames. The emitted sites supply mean distance mismatch, mean
angle mismatch, and mean coordination deficit to the frozen source model. Its
prediction is centered and scaled by the source target distribution, clipped
to a bounded dimensionless preference, and enters the existing score ledger at
fixed weight `0.18`. Enumeration and every hard geometric gate precede and
remain independent of this term; the candidate-set digest, poses, coordinates,
and admission decisions are not altered by promotion.

The receipt records eligibility, activation, thresholds, source and target
entry IDs, feature definitions, and explicit false flags for candidate
generation, hard admission, coordinate changes, physical potential use, and
kinetics. This makes external calculation evidence experimentally usable while
retaining a sharp boundary: it is a transferred rank hypothesis, not an energy
functional, force field, barrier model, trajectory, or clock.

## Build 175: deployment abstains outside frozen geometric support

The source artifact now includes per-channel minima and maxima in addition to
means, scales, coefficients, and target normalization. Support is the frozen
axis-aligned three-feature box with a predeclared `0.25` source-standard-
deviation margin. No target statistic expands this box. Cross-archive promotion
adds two independent requirements: at least five target frames must be inside
support and supported frames must comprise at least `80%` of all paired target
frames. Rank transfer and positive `Q²` remain necessary but are no longer
sufficient on their own.

Candidate-level use follows the same rule. Each emitted cluster is mapped to
the identical colored distance, angle, and coordination features, audited
against frozen source bounds, and scored only when supported. An unsupported
candidate produces a zero external term rather than an extrapolated value;
the grammar, other score channels, and exact geometric gates continue normally.
The workbench snapshot and receipt preserve supported and abstained counts,
coverage, maximum standardized excess, and target-frame support decisions.

This is a deterministic domain-of-applicability guard, not probabilistic
uncertainty quantification. It makes the calibrated hypothesis more honest by
refusing unsupported use, while still making no claim of a potential, force,
barrier, dynamics, kinetics, or generalization beyond the tested archive
domain.

## Build 176: feature-space deployment and a matched rank intervention

The calibration card now contains an interactive two-channel projection of the
three-feature deployment domain. The plot draws the frozen source-support box,
compatible target frames, and—after explicit mark activation—live candidate
clusters. Supported and abstained points have different geometry and color.
Users may choose distance–angle, distance–coordination, or angle–coordination
axes without refitting the model or changing a support decision. Calculation
labels are absent from this visualization.

For every live frontier, an exact matched audit compares the active ranking
with the same score after removing only the external-calibration term. Stable
candidate-key tie breaking is used in both arms. The portal reports candidate
count, frozen frontier digest, supported count, pairwise order inversions, and
whether the top action changes. Both rankings are previews: no alternate arm
is executed, candidate generation is shared, and hard admission is untouched.

The receipt carries the plot mode and intervention record, including whether
the ordinary known-window replay target was active. This visualization does
not promote correlation to mechanism; it makes applicability and actual policy
influence visible while preserving the existing no-potential, no-force,
no-kinetics claim boundary.

## Build 177: audit the encoded physical question before growth

Stage 4 now renders the complete physics-to-geometry manifest before any
frontier is enumerated. Its records are generated directly from the current
sample channels and experiment controls, then partitioned into
observed/learned constraints, declared soft hypotheses, and open boundaries.
Each record exposes the physical process being approximated, the exact
geometric representation, the available evidence, and the strongest claim the
representation does not support. A route button focuses the responsible
control without mutating it.

The same schema continues into every structural-leap certificate, so preflight
intent and post-event evidence can be compared without inventing a physical
clock. The experiment receipt embeds the coordinate-free preflight record and
its SHA-256 digest and explicitly records that it was frozen from current
controls before the first structural action, contains no candidate geometry,
inspected no candidate record or target, and models no physical time.

This closes a usability gap, not a physics gap: missing temperature-dependent
potentials, chemical potentials, nonlocal electronic response, barriers,
rates, and transport remain red/open records. The portal now makes those
omissions auditable before search rather than revealing them only after a
structural leap.

Build 177 also fails over cleanly when WebGL is unavailable. A non-WebGL status
canvas replaces only the 3D rendering surface; the scientific workflow,
calculations, evidence panels, plots, and receipts continue to initialize. The
receipt distinguishes interactive WebGL from the fallback and explicitly
states that the renderer choice changes no scientific calculation.

## Build 178: identify redundant geometry-encoded physics on one frontier

Build 178 adds a target-blind hypothesis-identifiability audit to the Stage 4
counterfactual workbench. It operates only after the exact hard-admitted candidate
set is frozen. For each active and nonconstant signed score term it forms one value
per candidate, then reports both Pearson contribution correlation and Spearman rank
correlation for every pair. The interactive matrix is therefore sensitive to both
linear duplication and monotone nonlinear duplication.

Known-window replay, seeded exploration, inactive terms, and frontier-constant
terms are explicitly withheld. The matrix cannot add, remove, move, rank, or execute
an action; it has no target or coordinate input. The receipt stores term ranges,
withheld reasons, all pairwise coefficients and classifications, the unchanged
candidate-set digest, and a coordinate-free audit digest. Correlation is interpreted
only as local identifiability of geometric ranking proxies on this one frontier—not
causal independence, physical independence, an energy Hessian, or parameter fitting.

## Build 179: condition identifiability on structural grammar and action size

Build 179 adds a second, default matrix mode. Before correlating two soft physics
channels it projects each signed contribution away from the frozen grammar/marking
priority and exact emitted species-labelled site count. The implementation forms a
deterministic orthonormal basis from centered controls, drops constant or collinear
axes, and residualizes without ridge tuning. Partial Spearman is computed by applying
the corresponding projection to average-ranked channels and controls.

The raw mode remains available for comparison. Both modes consume the same immutable
candidate rows, share the candidate digest, and cannot affect admission, geometry,
weights, ranking, or execution. Receipts preserve both complete matrices, control
acceptance diagnostics, raw and residual spreads, and separate coordinate-free audit
digests. The result is a local conditional-identifiability diagnostic—not proof that
the controls remove all confounding, and not causal inference or thermodynamics.

## Build 180: follow hypothesis separability through structural updates

Build 180 promotes a selected identifiability-matrix cell into a trajectory over the
retained frontier archive. Each point independently reads the immutable candidate
ledger and uses the currently selected raw or conditional contract. Missing pair
support creates a gap rather than an imputed coefficient. The summary reports
coverage, `|ρ| ≥ 0.9` counts, locally distinct counts, observed sign changes, and the
longest consecutive near-redundant run.

Historical points are navigable counterfactual records: selecting one changes the
inspected snapshot but does not regenerate candidates, replay search, mutate the
solid, or execute the historical action. Receipt records include frontier and audit
digests plus explicit false claims for physical time and mechanism persistence.
The x-axis is discrete GCTS structural-update order, never seconds or an inferred
growth rate.

## Build 181: registered-arm hypothesis contrast without frontier pooling

The compact experiment notebook now preserves the latest raw and conditioned
hypothesis-identifiability summaries plus the selected-pair trajectory. It stores
term and audit metadata, coefficients, candidate counts, receipt/frontier digests,
and claim boundaries; it does not store candidate rows or coordinates.

When both registered study arms have executed receipts, the response panel evaluates
the reference arm's preselected pair in each separately frozen arm. Comparison is
allowed only when both receipts contain that pair under the same conditioning-variable
acceptance schema. The panel reports per-arm Spearman coefficients and classifications,
the coefficient range, sign agreement, and provenance digests. Missing support or a
schema mismatch is rendered as withheld rather than replaced by another pair.

This is a descriptive registered-arm contrast. It does not pool candidate sets,
regenerate a frontier, replay search, infer a causal intervention effect, or establish
cross-material universality. Multiple configured arms can share the same source
structure and are not silently treated as statistically independent samples.

## Build 182: cross-material transfer in the general experiment notebook

The ordinary two-run notebook comparison now includes the same preselected-pair
identifiability contract used by registered arms. The first selected receipt supplies
the pair and structural-conditioning mode; the second receipt is queried only for
that exact pair. The result is unavailable if either run predates coordinate-free
identifiability summaries, the pair is absent, or conditioning acceptance differs.

For compatible runs the portal displays per-material Spearman coefficients,
classifications, candidate counts, candidate-set digests, coefficient range, sign
agreement, and a deterministic cross-run comparison digest. Candidate ledgers remain
separate and are not persisted in the notebook. No candidate is regenerated, no search
is replayed, and neither ranking nor execution is performed.

Cross-material agreement is therefore descriptive transfer evidence only. It neither
proves that the underlying physical mechanisms are universal nor treats saved runs as
independent specimens. Divergence identifies a useful next materials hypothesis—the
geometric proxy may be environment-specific—but is not itself a causal explanation.

## Build 183: from local correlation to a registered structural intervention

An off-diagonal cell in the frozen-frontier identifiability matrix can now be promoted
to a user-launched baseline / ablation experiment. The selected ordering is meaningful:
the first channel becomes the ablated channel and the second is retained as its local
comparison. The registration freezes pair labels and IDs, matrix mode, source frontier,
candidate-set and audit digests, scenario, and the current growth-control serialization.

Configuring either arm returns to supplied positions and never auto-executes. During
the ablation arm, a pure target-free transform sets only the chosen score term's weight
and signed contribution to zero. All exact candidate templates, proper-pose classes,
hard gates, scheduling, and other weights remain unchanged. The transform is independently
unit-tested for immutability, invalid-manifest failover, and target-taint rejection.

Receipts and compact notebook summaries preserve the experiment manifest. The notebook
intervention-factor ledger treats the registered arm/multiplier as an explicit search
factor and still compares every other recorded control. Outcome attribution is withheld
if the input or another control changed. This is an ablation of a geometry-encoded model
term, not a claim that a physical mechanism can literally be removed from the material.

## Build 184: fail-closed outcome attribution at a common search horizon

Build 184 adds a pure comparison contract for the registered score-channel experiment.
It accepts exactly one baseline and one ablation summary and requires the same frozen
pair, matrix mode, candidate-set digest, audit digest, scenario and structure SHA-256.
Both arms must have executed, remain target-free, retain complete histories, and differ
in exactly one recorded intervention factor: `hypothesisSeparation`. The contract is
selection-order invariant and emits a deterministic comparison digest. Failure at any
gate yields no numerical response.

The common horizon is `min(baseline structural leaps, ablation structural leaps)`, with
the seed stored at point zero. At that exact point the portal compares explicit structural
sites, cluster placements, accepted-parent lineage depth, cumulative accepted/rejected
actions, unit-weight geometric powder-S(q) peak prominence, and proper-rotation-invariant
local q6/|psi6| order. Missing optional observables stay unavailable rather than being
imputed. No candidate rows are pooled, no search is replayed, and coordinates remain
outside the notebook summary.

This produces a controlled response of one encoded scoring term under recorded browser
conditions. The horizontal alignment is a discrete GCTS update count—not seconds—and
the result does not identify a physical energy contribution, barrier, kinetic law,
causal materials mechanism, or statistical effect across independent specimens.

## Build 185: site-resolved provenance from the visible solid

Build 185 makes every rendered atom auditable. Each instanced atom mesh carries only its
live atom ID for picking; a raycast resolves that ID back to the authoritative explicit
structure. A pure site-provenance transform then computes the position in ångströms,
colored coordination and nearest distances from current sites, not from a target or a
hidden reference configuration.

The transform joins the selected atom to retained cluster placements. It reports whether
the site was supplied or emitted, its creator cluster type and exact frozen rule, parent
placement, causal depth, all overlapping cluster memberships, nucleus memberships, and
interface status. Newly emitted atoms retain a compact creation record: marking score and
gate, shared/fresh counts, contact-angle residual, composition and surface deltas, and
loop-closure witness count. The selected atom receives a separate wireframe highlight;
dragging still orbits, while a short click selects.

This inspector is deliberately ephemeral. Its absolute coordinates are not persisted in
the coordinate-free notebook or experiment receipt, and selection does not alter ranking,
admission, geometry, or search. Local provenance supports scientific debugging of the
geometric encoding; it is not a defect classifier, energy/force calculation, atomistic
mechanism assignment, or causal explanation of growth.

## Build 186: resolve learned geometric support at one visible site

Build 186 connects the site picker to the frozen colored distance, ordered coordination,
and angular envelopes. For the selected atom only, the portal evaluates the established
`coloredLocalConstraintMismatch` contract with the same current explicit neighbors and
then materializes its individual channel evidence. The aggregate therefore matches the
existing spatial mismatch field rather than introducing a second definition.

For every admitted contact the audit reports observed and typical length, learned lower
and upper contact observations, and normalized mode residual. For each ordered species
channel it reports count, observed median, hard maximum, and fractional frontier deficit.
For each contact-neighbor pair it reports the angle and its nearest learned padded band.
The view distinguishes within-mode, strained/off-mode, frontier-deficient, over-capacity,
within-band, and outside-band states. Four compact meters preserve contact, angle, and
coordination semantics, while a percentile places the site in the current deterministic
center sample without changing the fitted envelopes.

The calculation is target-free and posthoc. Contact/angle residual remains a geometric
search proxy; coordination deficit may intentionally describe an incomplete growth front.
No displayed value is an energy, force, stress, surface energy, defect identity, posterior
probability, or kinetic observable, and the inspector never feeds back into execution.

## Build 187: compare two colored local environments in the visible solid

Build 187 turns the site audit into a comparative microscope. A scientist can pin one
explicit site and select a second while retaining both highlights in the shared 3D scene.
The pure comparison contract reports center-species agreement, per-species coordination
deltas, matched and unmatched colored neighbor distances, RMS radial-shell displacement,
changes in contact/angle mismatch and coordination deficit, and supplied-versus-emitted
lineage with causal-depth and interface transitions.

The comparison intentionally discards Cartesian positions. It sorts distances separately
within every neighbor-species channel, making the result invariant to global translation,
proper rotation, and input order. This is suitable for questions such as whether an emitted
frontier site has approached the finite colored shell of a supplied bulk site. It is not a
full colored-graph congruence test: indexed radial pairing can hide angular rearrangement,
and different reaches or incomplete fronts can leave unmatched neighbors.

The comparison is ephemeral, target-free, and posthoc. Its compact digest identifies the
displayed coordinate-free result but is not persisted as a new training label. No energy,
force, defect identity, kinetic mechanism, statistical independence, or physical material
equivalence is inferred, and selecting or pinning sites never changes candidate generation,
ranking, admission, or execution.

## Build 188: add colored angular topology to the site-pair microscope

Build 188 closes a specific insufficiency in the Build 187 radial comparison. Equal colored
distance multisets need not imply equal angular geometry. The site-provenance transform now
enumerates every finite neighbor–center–neighbor angle and groups angles by the unordered
species pair on the two rays. Comparison uses minimum-cost monotone pairing within each
sorted colored channel, reporting paired count, unmatched count, and RMS angular shift.
This prevents an extra early angle from displacing every later match while retaining a
deterministic, permutation-independent calculation.

The inspector also reuses the validated `localOrientationalOrder` implementation on exactly
the same neighbor vectors. Three-dimensional sites expose Steinhardt q4, q6, and q12 through
the Legendre addition theorem; inferred two-dimensional sites expose |psi4|, |psi6|, and
|psi12| in the intrinsic plane. Unresolved centers with fewer than three 3D or two 2D
neighbors remain unavailable rather than receiving the misleading single-bond value one.

Both channels are invariant to translation and global proper rotation, but they answer
different questions. Colored angle shells remain inspectable three-body evidence, whereas
q/psi compresses angular symmetry into harmonic magnitudes. Neither establishes an exact
colored point-set isometry, neighbor correspondence, defect species, phase, crystallinity
probability, free energy, force, mechanism, rate, or physical time. The calculation is
ephemeral and target-free and never enters search decisions.

## Build 189: expose exact local centrosymmetry in the site comparison

Build 189 adds a defect-sensitive geometric channel without adding a defect label. For
both pinned sites, the portal takes the same neighbor vectors used by the validated global
centrosymmetry observable: neighbors within the fixed 1.32a structural shell. Automatic
shell selection is learned from the current reference neighbor-count population among the
dimension-appropriate 4/6 choices in 2D or 6/8/12 choices in 3D; an explicit user shell
selection is honored unchanged.

For a resolved even shell, the Kelchner parameter is computed by exact minimum-weight
perfect pairing of opposite-neighbor candidates. The normalized amplitude
`sqrt(P / (2 sum_i |r_i|^2))` removes uniform scale and is also invariant to translation,
proper rotation, and atom permutation. The site view reports shell size, resolved status,
amplitude at A and B, and the signed B-minus-A response. A center with too few current
neighbors remains explicitly unresolved; it is not assigned zero asymmetry.

Centrosymmetry is sensitive to local inversion-symmetry breaking, which can occur near
surfaces, interfaces, elastic distortions, thermal disorder, vacancies, dislocations,
stacking faults, and grain boundaries. The scalar does not distinguish those causes. The
portal therefore never converts it into a named defect, defect probability, formation
energy, stress, force, mechanism, rate, or physical time, and it remains target-free and
posthoc. The Build 188 q/psi calculation was simultaneously corrected to use this same
validated 1.32a structural shell rather than the broader 1.45a provenance-display reach.

## Build 190: bind site provenance and comparison schemas to the release

The first public Build 189 interaction exposed a cache-coherency failure rather than a
scientific-computation failure. The main application expected the new `centrosymmetry`
comparison record, but its import URL still named the earlier immutable module version.
A cached module returned the older fail-closed schema, so dereferencing the missing record
stopped A/B rendering before any value was displayed or persisted.

Build 190 advances the provenance subresource version for the angle-shell schema and the
comparison subresource version for the angular/orientational/centrosymmetry schema. Static
release contracts bind both versions to the main build marker. Public QA must exercise a
fresh A/B selection after deployment and observe the exact-shell inversion-asymmetry card;
checking only the HTML or main script version is no longer accepted as evidence.

## Build 191: expose the creation-time geometry-physics ledger per site

Build 191 connects the selected-site microscope to the actual candidate evaluator rather
than estimating an explanation after growth. When a placement is materialized, the portal
freezes every enabled physics-ranking term returned by the common score decomposition:
its raw dimensionless channel value, effective weight (including the active hypothesis
arm), signed contribution, semantic role, and claim boundary. The record also retains
zero-weight terms as explicitly diagnostic channels. Grammar priority, exploration, and
known-window reconstruction bonuses remain outside the physics subtotal so that unlike
quantities are not silently combined in the displayed number.

Admission is audited separately. The frozen receipt records species-aware hard-core and
coincidence checks, the declared public boundary, minimum shared support, nonempty novel
emission, known-window consistency where applicable, colored coordination capacity,
colored angular-envelope consistency, feedstock availability, and the chosen GCTS marking
gate or explicit known-window fallback. Because the receipt belongs to an accepted
placement, these gates should all pass; retaining them makes that assertion inspectable.

The ledger is target-free and immutable after placement. It does not infer a receipt for
supplied seed sites and it cannot alter later ranking, clustering, marking learning, or
search. Its signed subtotal is a search-ordering score, not physical energy or posterior
probability. No force, barrier, rate, trajectory, or physical time is integrated. The
feature is therefore evidence of which finite geometric surrogates and hard constraints
actually governed a leap-frogged move, not a claim that molecular dynamics was performed.

## Build 192: pair creation geometry with the current local response

Build 192 adds a true before/after structural audit for emitted atoms. After every accepted
commuting batch has been materialized but before the optional bounded contact/angle
projection, the engine freezes each new atom's colored 1.32a neighbor shell. The record
contains immutable atom IDs, species, center-relative vectors, the center position, and
the finite reach. It is session-local inspection state and is not serialized into the
scientific receipt or used by future candidate ranking.

At inspection time the current shell is paired to the creation shell by exact atom ID and
species—not by nearest-neighbor guessing. The response reports center displacement,
retained/lost/gained shell membership, RMS radial drift, and a least-squares local affine
map over persistent neighbor vectors. √D²min measures the residual after the best affine
map. When the creation cage spans three dimensions, the portal additionally reports the
Green–Lagrange equivalent shear and determinant-minus-one local volume response. Planar or
otherwise rank-deficient cages keep the residual but withhold those 3D strain invariants.

The current shell can include neighbors attached in later leaps, so the audit deliberately
does not label all change “relaxation.” It separates exact persistent-neighbor deformation
from shell gain/loss and states that the combined response may reflect both the bounded
post-attachment projection and subsequent structural completion. It is not a force
trajectory, energy relaxation, atomistic mechanism, kinetic rate, probability, or elapsed
physical time, and it remains target-free.

## Build 193: retain changed local states across structural leaps

Build 193 extends the emitted-site response from two endpoints to a bounded, interactive
local pathway. The global leap certificate does not store atomic coordinates, so it cannot
honestly reconstruct a site's past shell. Instead, the executor maintains an ephemeral set
of emitted sites affected by each newly committed batch: the new sites themselves and older
emitted sites lying within the same 1.32a structural reach. After the optional bounded
projection, those sites are reevaluated with the Build 192 exact-identity response.

Per-site histories retain at most 24 changed records. A state signature over shell identity
counts, center displacement, radial RMS, √D²min, equivalent shear, and volume response
deduplicates unchanged checks. The UI plots radial drift and affine-subtracted residual,
draws shell-gain/loss bars, and exposes keyboard-selectable leap points with exact local
readouts. Supplied atoms have no such path because no creation record exists.

The default three-dimensional NaCl runtime regression executes four genuine updates through
the known-window certificate and scans emitted sites. It finds site 15 with two retained
records: five of five creation neighbors persist, and one later neighbor enters the shell
at leap 2. No browser page errors are accepted. The index is structural search order only;
the local pathway is not elapsed time, a force/energy trajectory, a kinetic mechanism, or
a statistical sample of independent material histories.

Runtime QA also found an older JavaScript scope error in the ionic-pair/bond-valence
workbench: several renderers used a signed-number formatter defined only inside another
function. Build 193 promotes that pure formatter to shared application scope, preventing
the diagnostics from interrupting the post-leap UI update.

## Build 194: relate creation-time geometry channels to later local response

Build 194 connects the Build 191 decision ledger to the Build 192/193 response evidence at
the action-population level. The naive unit would be an emitted atom, but every atom from a
whole-cluster action shares the same creation decision; treating those atoms as independent
would multiply the apparent sample size. The portal therefore constructs exactly one record
per accepted placement. Site-level center displacement, radial drift, √D²min, shell change,
equivalent shear, and absolute local volume response are averaged within their owning action.

For each nonzero-weight creation term and selected response, the portal computes Spearman
rank correlation when at least four grouped placements contain finite values and variation
in both axes. Constant channels fail closed. The interactive plot highlights the selected
site's owning placement, and term buttons expose the strongest descriptive associations.
Only the most recent 256 eligible placements are admitted to bound interactive work; the
display reports grouped placement count separately from aggregated atom presentations.

The default four-update NaCl runtime regression reaches the 216/216 known-window certificate
without page errors. It provides 90 whole-cluster samples and 209 site-response presentations.
Non-affine residual is constant and correctly unavailable. Shell membership change varies;
the strongest displayed term is surface completion with Spearman ρ = −0.58325, followed by
composition and formal-charge balance. These values are a deterministic within-run diagnostic,
not causal effects, calibrated forecasts, independent material samples, energies, kinetics,
or statistically generalizable coefficients.

## Build 195: freeze an early-block association and test later leap blocks

Build 195 adds a temporal-order validation boundary without treating search order as physical
time. Every grouped placement record carries the `createdAtLeap` index of its emitted atoms.
The validator sorts the distinct complete leap blocks, assigns the earliest two thirds to
term selection, and reserves every later block for evaluation. All placements in one
commuting antichain remain together. The minimum support is eight grouped placements in
each split, with at least three total leap blocks.

Only earlier blocks may determine the active term: the strongest absolute Spearman
association for the selected outcome is frozen before the held-block audit is constructed.
The later result reports the same term's coefficient and whether its sign is retained.
Missing variation or insufficient support fails closed. No random split, atom-level sample,
held-block term selection, causal-effect claim, independent-material claim, or kinetic
interpretation is permitted.

The six-update default NaCl runtime regression gives an informative shell-change audit.
Leaps 1–4 contain 90 grouped placements and select surface completion at ρ = −0.59155;
leaps 5–6 contain 142 later placements and retain the negative association at ρ = −0.447.
Non-affine, radial, center-displacement, shear, and volume outcomes remain unavailable when
the early blocks lack variation. This is a sequential stability diagnostic within one
deterministic continuation, not external validation or statistical independence.

The same run identified a display error independent of the association calculation. Once
known-window replay had completed, later accepted grammar actions continued to show the
certificate text instead of their action counts. Build 195 freezes the pre-event certificate
state and now uses the certificate caption only on the transition that proves 216/216 replay;
later events report their actual compressed-grammar placements, atoms, and invariant prunes.

## Build 196: make creation-response evidence receipt-reproducible

Build 196 canonicalizes the exact grouped placement records behind the interactive
creation→response microscope. The canonical dataset is sorted by structural-leap index and
placement identity; each active physics term is sorted by stable term ID; outcomes use a
stable key order. The artifact retains at most 256 coordinate-free placement records and
reports whether truncation occurred. Its SHA-256 digest is included in the scientific
receipt alongside recomputable Spearman summaries and a blocked-validation result for each
of the six response observables.

Compact notebook entries store the digest and analysis summaries but not the record rows;
the full downloaded receipt stores those rows. This makes a saved run comparable without
turning emitted atoms into independent samples or embedding target coordinates. The artifact
explicitly records that it uses one whole-cluster placement per sample, blocks by complete
structural leaps, never selects on held blocks, uses no random split or target, and supports
no causal, kinetic, energetic, or independent-material inference.

## Build 197: inspect within-run leap heterogeneity

Build 197 adds a per-complete-leap robustness profile for each selected creation term and
response. Each bar is recomputed from only the whole-cluster placements created in that
structural leap; a bar is absent when its block has fewer than four grouped samples or no
within-block variation. The strip therefore reveals sign reversals and unavailable blocks
that the pooled coefficient and the earlier/later blocked split can obscure. These blocks
remain correlated algorithmic states of one deterministic run, not physical time points or
independent replicates.

The site microscope also exposes the canonical artifact manifest and SHA-256 prefix and can
copy the full coordinate-free grouped dataset. The copied rows, full receipt rows, receipt
digest, and compact notebook digest share the same canonical serialization. Receipts and
notebook summaries additionally record per-outcome leap profiles selected from the pooled
descriptive association. This improves auditability without allowing the target, atom IDs,
coordinates, or held-block outcomes to affect growth or the earlier-block validation rule.

## Build 198: test joint geometry-channel information on later leap blocks

Build 198 adds a fixed-ridge multichannel surrogate to the grouped placement audit. The fit
uses only the earlier complete leap blocks. Candidate score channels enter the vocabulary
when they are active in at least half of the training placements; selection is by support
and stable term ID, capped at twelve, and never reads the response. Centering, scaling,
target mean, feature removal, and coefficients are all frozen before later blocks are scored.

The held-block comparison reports model and training-mean MAE/RMSE, Spearman association of
prediction with response, and skill `1 − model SSE / training-mean SSE`. Negative skill is
retained rather than hidden. The full receipt includes every held-block prediction and the
complete standardized model; compact notebook summaries omit prediction rows while keeping
the model and scores. This is a correlated within-run explanatory diagnostic, not an energy
model, force field, kinetic law, causal estimate, confidence interval, calibrated material
forecast, or independent-material validation.

The six-leap default NaCl regression yields three supported training channels—composition,
formal-charge balance, and surface completion—from 90 earlier placements. On 142 held
placements the frozen model has MAE 1.6736 versus 1.6456 for the training-mean baseline,
skill −0.0655, and Spearman ρ +0.4542. The portal reports `no gain`; rank association alone
does not override worse squared or absolute error. This is evidence that the present channel
set is not yet a transferable multichannel response model, not a reason to tune on the held
blocks.

## Build 199: separate feature-support transfer from response error

Build 199 freezes an axis-aligned feature-support envelope from the earlier-block score
contributions. For each retained channel the receipt records training minimum, maximum,
mean, and scale. Every later placement records whether all contributions remain within the
training ranges and its maximum normalized excess. The UI reports support coverage, maximum
excess, and support-conditioned MAE alongside the standardized coefficients.

This is a covariate-support diagnostic, not a probability, confidence region, convex hull,
phase boundary, or guarantee of reliable prediction. It never changes the candidate set,
growth ordering, fit, or held-block outcome. High feature support with negative skill is
evidence against the current linear channel-to-response representation; low support instead
flags extrapolation as a competing explanation.

In the default NaCl run, feature-support coverage is 142/142 held placements and maximum
standardized excess is zero. The held-block failure from Build 198 therefore occurs entirely
inside the earlier-block axis-aligned score envelope. The frozen standardized coefficients
are −0.6966 for surface completion and approximately −0.0542 each for composition and formal
charge. This rules out simple range extrapolation as the explanation; it does not prove which
nonlinearity, omitted state variable, or leap-dependent mapping is responsible.

## Build 200: test fixed second-order coupling between geometry channels

Build 200 adds a predeclared quadratic control to the earlier-block response fit. It retains
all linear standardized channels and adds squares plus pairwise products among at most the
first six support-ranked channels. Interaction means, ridge coefficients, and target mean
are fit on earlier blocks only. The later blocks score both frozen models and the same
training-mean baseline; no winner is selected to alter the run.

The UI reports three MAEs, linear and coupled skills, both rank associations, and the largest
second-order coefficients. Receipts preserve the full basis and per-placement coupled
predictions. A second-order improvement would demonstrate useful geometric channel coupling,
not a physical many-body Hamiltonian or causal interaction; failure would rule out this
bounded polynomial explanation without justifying held-block tuning.

The default NaCl result is negative. The nine-term coupled basis has held-block MAE 1.8741,
skill −0.3648, and Spearman ρ +0.4041, worse than both the linear arm (MAE 1.6736, skill
−0.0655, ρ +0.4542) and the training-mean MAE 1.6456. The strongest interaction weights
couple surface completion to composition/formal-charge balance, but held-block performance
does not support those terms as transferable response structure. No interaction is promoted
or tuned from this result.

## Build 201: test omitted creation-time structural state

Build 201 freezes a target-free, coordinate-frame-invariant context on every accepted
placement before the commuting antichain commits. The context includes causal depth,
shared/novel support fractions, log pre-leap site/cluster/frontier counts, admitted batch
size, radius of gyration, relative shape anisotropy, coordination deficit, lineage count,
shared-interface fraction, and interface-pair count. Every action in one antichain receives
the same pre-commit global state, preventing arbitrary within-batch order from becoming a
feature.

The contextual control preserves the score-channel vocabulary and independently selects up
to twelve context fields by earlier-block support and stable ID. It uses the same fixed ridge
and is scored only on later blocks. Context coefficients and predictions are serialized in
the receipt; notebook summaries omit prediction rows. Improvement would support omitted
geometric state as an explanation, not physical time, causality, or a calibrated kinetics
model.

The current six-leap NaCl result is deliberately fail-closed. Score-only gives MAE 1.674
and held-block skill −0.065; the state-augmented arm gives MAE 1.834 and skill −0.286,
against training-mean MAE 1.646. More importantly, state-envelope coverage is 0/142 held
actions and the maximum standardized feature excess is 6.21σ. The public panel marks all
142 predictions as extrapolations and explicitly says that the reported skill is not an
interpolation test. A better experiment needs training configurations that overlap the
later frontier-state distribution; this result neither validates the state model nor rules
out structural context.

## Build 202: separate local attachment geometry from global extent

Build 202 adds a predeclared local/intensive context arm rather than selecting a convenient
subset after seeing later responses. Its five fixed channels are proposed support size,
shared support fraction, novel support fraction, local coordination deficit,
and shared-interface fraction. Extensive/global quantities—site, cluster, and frontier
counts, batch size, radius of gyration, lineage count, and interface-pair count—remain in
the all-state audit but cannot by themselves force the local arm out of range.

The same earlier-leap ridge fit and later-leap score are retained. The receipt stores the
exact context allow-list, feature envelope, supported and unsupported errors, and
supported-only skill. The UI displays five arms and separate local/all-state support bars.
No held response, held range, phase label, coordinate frame, or physical-time variable
selects the local scope. This is an interpolation audit inside one deterministic growth
trace, not evidence of transport, forces, rates, or transfer to another material.

## Build 203: machine-readable interpolation readiness

Build 203 turns feature-domain validity into an explicit gate rather than leaving it to
narrative interpretation. Each score-only, local-state, and all-state blocked model reports
one of `full-interpolation`, `mixed-domain`, or `extrapolation-only`, with supported and
unsupported held-placement counts. Aggregate skill is marked as an interpolation test only
when every held action lies inside the earlier-block axis-aligned envelope.

A mixed-domain model receives a supported-only skill only if the supported subset reaches
the fixed `minimumSamplesPerSplit` gate; otherwise the statistic is null. The readiness
object, sample threshold, interpretation, and `featureEnvelopeChosenUsingHeldout=false`
audit are serialized into the full receipt and summarized in the notebook. The new
three-tile ledger makes this boundary visible before coefficients or MAE bars are read.

## Build 204: show every blocked training horizon

Build 204 evaluates the same frozen local-state model at chronological 50/50,
ceil-two-thirds, and leave-final-leap horizons. All defined horizons are shown together;
duplicate training-block counts are collapsed only when a short trace makes two definitions
identical. No held response, skill, or envelope coverage selects an arm.

The interactive strip reports training/held leap identities, supported action counts,
readiness state, and aggregate skill. Clicking changes explanatory focus, not execution or
fit. Full receipts retain every model and prediction row, while notebook summaries remove
prediction rows but keep settings and metrics. The sweep diagnoses support acquisition as
the observed structural history grows; it is not hyperparameter selection, physical time,
or independent-material transfer.

## Build 205: compare readiness across saved material runs

The experiment notebook now renders retained local-state horizon summaries as an
interactive matrix: saved runs are rows, preregistered chronological horizons are columns,
and the response selector switches among six coordinate-free local outcomes. Tiles show
feature-envelope readiness, supported versus held placements, and frozen aggregate skill
while preserving the original run and receipt identity.

This is intentionally not a pooled validation study. Notebook summaries contain no
placement or prediction rows; the atlas does not refit, aggregate, or assume independence
between saved runs, and it marks repeated input identity. Transfer across structures,
specimens, or materials still requires a separately sealed experiment.

## Build 206: inspect the evidence behind a readiness tile

Each saved-run/horizon cell now opens a coordinate-free microscope. It reports the exact
training and held structural-leap identities, placement counts, supported-domain fraction,
model-versus-mean error, interpolation-gated skill, maximum earlier-envelope excess, and up
to eight dominant standardized coefficients from the already frozen local-state model.

The detail panel also carries the feature-scope statement, envelope definition, receipt
hash, and explicit heldout-fit and response-selection flags. Coefficients are ranking-model
diagnostics, not energies or causal physical contributions. No model is refit and no
placement or prediction rows are restored to the notebook.

## Build 207: map physical processes onto structural scales

The pre-growth physics manifest is no longer only a flat list. Its 41 current records are
classified exactly once into structural evidence, local attachment, interface/morphology,
imposed environment, or unresolved dynamics/nonlocal response. A segmented lane meter
separates observed/learned constraints from declared hypotheses and open physics; lane and
evidence-class filters compose without changing any setting.

The coordinate-free map is frozen with the preflight receipt before candidate execution.
It explicitly records that structural states are not physical time and hypotheses are not
learned physics. Classification is fail-visible: any future manifest record omitted from
the scale vocabulary enters an `unclassified` lane and makes the completeness flag false.

## Build 208: attribute measured work to pipeline stages

The live cost laboratory now records a five-stage deterministic work ledger: supplied sites,
cluster-relation decisions, processed GCTS sections, tree-search constraint checks, and
explicit colored-coordinate writes. Progress is shown for finite clustering and marking
passes; search and emission remain active counters. Clicking a card routes to the relevant
workflow stage and changes no setting.

The operation classes are retained separately and are explicitly non-additive. They are not
converted into wall time or compared numerically with force evaluations. The existing MD
rows remain a user-declared algorithmic-work reference, while symbolic recursion and O(N)
explicit materialization continue to be reported as distinct costs.

## Build 209: keep the structural scene inspectable without WebGL

The browser fallback now CPU-projects the live Three.js scene instead of replacing it with
an illustrative atom ring. Colored instanced atoms, point fields, candidate glyphs, finite
line relations, unit-cell outlines, and declared growth boundaries are projected with the
active camera; OrbitControls still provide drag and zoom. The view therefore continues to
show the full-configuration clustering process and the explicit material-growth state on
browser or capture surfaces where WebGL cannot initialize.

Projection budgets are display-only and are reported in the viewport footer. They never
truncate the scientific state, change cluster/marking/search logic, or enter a receipt as
evidence. All quantitative observables and certificates remain computed from the complete
colored coordinate and relation sets.

## Build 210: make marking capacity a scientific control

The selectable 1/3/6/12-channel marking capacity now determines the actual coefficient
dimension in both atom-environment and molecular/irregular-cover learners. A single channel
is a scalar radial section; higher capacities use a deterministic spherical code expressed
in each occurrence's learned intrinsic proper frame. No global axis enters the vocabulary.

Clustering remains upstream of marking: the observed proper-rotation support and finite
connection-port incidence determine a recommended pose×port rank for each cluster type.
The learner caps each type by the user-selected capacity, serializes the resulting active
mask and channel basis, and keeps inactive coefficients identically zero through fitting,
loss evaluation, saved-library replay, and visualization. This makes capacity ablations
real while preserving the claim boundary: channels encode bounded local compatibility and
failure evidence, not a physical potential or dynamical trajectory.

## Build 211: compare marking capacities on one frozen dataset

The marking stage now evaluates 1, 3, 6, 12, and any distinct auto-ranked channel capacity
over exactly the same cluster vocabulary, local-section samples, neighborhood reach,
representation, and deterministic modulo-five fit/holdout split. Each row reports active
parameters separately from allocated zero slots, cluster types whose pose×port rank exceeds
the capacity, fit/validation mismatch, generalization gap, rank coverage, and Pareto status.

The displayed recommendation is the smallest rank-complete model within `5% + 0.002` of the
best rank-complete held-out mismatch. That fixed rule prevents a low scalar loss from hiding
an under-capacity representation and prevents the largest tensor from winning by default.
Clicking a row performs a declared capacity intervention and restarts the same visual fit.
The complete comparison enters the marking artifact and receipt with explicit
`targetUsed=false` and `physicalEnergy=false`; it cannot inspect or choose a growth action.

## Build 212: replay every saved marking in its own learned basis

The marking library is now a collection of self-contained learned artifacts rather than a
list of coefficient arrays interpreted through the current UI model. Each entry supplies
its own deterministic spherical basis, active-channel mask, representation readout, and
chiral state to the connection scorer. Storage and compatibility validation reject malformed
bases, masks, or coefficient dimensions before they can enter search.

An interactive portfolio replay audit scores all compatible artifacts against one unchanged
frozen overlap-rule vocabulary. It reports finite coverage, active/allocated parameter count,
score summaries, and rank displacement, and serializes the same audit in the experiment
receipt. This is a representation-replay and ranking comparison only: candidate geometry is
identical across entries, target atoms are unavailable, and the audit does not certify that
the most permissive portfolio has better held-out growth precision.

## Build 213: compare saved markings on one live frontier

Each frozen growth snapshot now contains a marking-only counterfactual over its complete
hard-admitted candidate set. Every compatible marking re-scores every action using its own
serialized basis, active mask, representation, and threshold. The audit records finite
coverage, admission count, distinct-score count, top ties, winner, runner-up margin, score
digest, and mean rank displacement relative to the selected artifact. A portfolio view takes
the strongest artifact per action while retaining the winning artifact identity.

The interactive rows preview the exact winning pose but cannot execute it. The receipt stores
the full-frontier and hard-admitted-set digests plus rounded summaries, while excluding poses
and coordinates. All arms explicitly retain `candidateGeometryChanged=false`,
`hardAdmissionChanged=false`, `targetUsed=false`, and `executed=false`. This separates a
marking's causal ranking effect from every other geometric physics channel and from action
supply.

## Build 214: inspect the material consequence of each marking's winner

Each saved marking's winner is now joined back to its unchanged hard-evaluated candidate
record. The portal reports the number of shared and newly emitted sites, contact-plus-angle
mismatch, constraint margin, net signed response under the active physics ledger, and its
dominant favorable and burdening channels. Coordinate-free consequence digests enter the
receipt, while the UI preserves the exact pose preview.

The consequence audit records target use independently of the marking score: saved marking
scores remain target-free, whereas a consequence evaluated during labeled known-window
replay is explicitly marked as such. No counterfactual is executed and no physical energy,
probability, stability, kinetics, or elapsed time is inferred.

## Build 215: compare multiscale structural consequences before commitment

Every distinct saved-marking winner is now evaluated on a bounded local section: the 64
current atoms nearest the emitted-site centroid plus all newly proposed sites. The same
before/after section yields a proper-rotation-invariant q₆ change in 3D or |ψ₆| change in 2D,
and a unit-weight finite-section Debye S(q) peak-prominence and spectral-shape change.
Candidates selected by multiple markings share one cached analysis.

The receipt retains the deterministic window policy, before/after atom counts, pair-distance
work, compact order/scattering summaries, target-use state, and consequence digest without
coordinates. These observables are posthoc ranking consequences only: they do not enter the
marking score, hard admission, search, or execution and do not establish bulk order,
experimental intensity, phase stability, energy, probability, kinetics, or physical time.

## Build 216: register a two-arm saved-marking intervention

The live-frontier marking inspector now converts a selected non-active artifact into a
controlled baseline/alternative study. The registration freezes both self-contained marking
artifacts and their content digests, the common candidate and hard-admitted-set digests,
winner and consequence digests, material/vocabulary identity, scenario, and every non-marking
growth setting. Baseline and alternative buttons each reset to supplied positions and execute
nothing.

Activation revalidates the chosen artifact digest; missing or modified artifacts fail closed.
Receipts retain arm identity, registration/source-frontier digests, input/settings checks,
and confirmation that the active marking matches the requested arm. Saved-run comparison
still provides an independent identical-input/one-factor audit. The intervention tests a
learned representation's effect on finite GCTS search; it does not identify physical energy,
stability, probability, kinetics, or elapsed time.

## Build 217: certify executed saved-marking outcomes

Compact notebook summaries now retain the first target-free frozen candidate-set and
hard-admitted-set digests of an executed run. A pair carrying the saved-marking registration
is accepted only when its registration, two artifact digests, registered source frontier,
non-marking control JSON, scenario/material/vocabulary identity, supplied-position SHA-256,
and baseline/alternative arm assignment all agree. The generic notebook factor audit must
independently find exactly one changed factor, `marking`.

The design may be valid before execution, but response comparison additionally requires a
structural leap or audited fixed point in both arms and identical first candidate and hard
sets with no target use. Passing pairs expose the existing trajectory and outcome deltas;
failed pairs remain descriptive and name the failed invariant. This is an algorithmic
one-factor intervention over learned local connection geometry, not a physical-time,
free-energy, rate, or population-level causal claim.

## Build 218: freeze the saved-marking response horizon

The marking intervention adds a preregistered 1-, 4-, or 8-leap structural horizon. Its
value is serialized into the registration before either arm resets to supplied positions.
The live executor checks the horizon before every action and immediately after every frozen
structural-leap certificate, pauses Play, disables pipeline continuation, and rejects later
manual steps while the experiment remains active. Receipts separately report event count,
exact horizon attainment, overrun, and audited finite fixed points.

Notebook response certification now requires both arms at the exact registered horizon.
The only terminal exception requires both arms to reach certified finite fixed points at or
before that horizon. One early fixed point versus one censored live frontier remains
non-comparable. This removes unequal discrete search work as a confounder while preserving
the boundary that structural-leap index is not physical time, a rate, or a dynamical path.

## Build 219: keep specimen identity visible through every stage

The live workflow now separates the active observation from the composition query used to
request a future public structure. A specimen passport derives reduced formula and colored
composition directly from the current occupancy-aware atom records, alongside exact site
count, source class, dimensionality / observation geometry, and evidence label. This is a
UI provenance correction: it does not feed phase, formula, or source metadata back into
clustering, GCTS learning, or growth.

A focus-microscope view expands the scientific stage for full-configuration clustering and
the array of per-cluster marking scenes. It is presentation state only. The underlying
coordinates, learned cover, connection sections, frozen candidates, search history, and
receipts are identical before and after entering focus.

## Build 220: request calculation evidence, not merely a composition

Public NOMAD retrieval now separates chemical composition from the evidence needed for a
growth investigation. The user may require geometry, three or more fixed-topology
relaxation snapshots, at least one completely force-labelled snapshot, or five or more
calculation-paired snapshots suitable for the geometry-surrogate preflight. Searchable
geometry-optimization energy/force summaries first prefilter the exact-composition entry
population. A bounded client-side gate then inspects at most eight archives and reports
failure rather than silently falling back to a weaker evidence class.

The input receipt records the requested target and the accepted archive's frame, energy,
force, spin, and normalized-method support. Entry acceptance is the only automatic use of
this target. Calculation channels do not enter cluster identity, candidate generation, or
growth ranking unless a different compatible archive later passes the already frozen
cross-archive transfer and explicit marking-promotion gate.

## Build 221: select a public specimen family without leaking it into GCTS

The public input route now exposes three bounded NOMAD searches: 3D bulk structures,
`structural_type = 2D` layered structures, and exact H/O structures with reduced formula
`H2O`. Each remains compatible with the independently selected calculation-evidence gate.
The water filter prevents a generic two-element search from standing in for crystalline
water, while the 2D filter allows materials-science users to start from database-classified
layered configurations rather than only curated graphene / hBN examples.

The receipt records this source-family choice and explicitly records that it is not used
for cluster identity or growth. The family is an acquisition constraint, not a training
label; H₂O retrieval does not assert an ice polymorph, and NOMAD's 2D classification does
not supply a lattice, layer group, cluster cover, marking, or continuation grammar.

## Build 222: make public-source choice comparative and auditable

An exact composition / specimen-family / evidence query now returns a bounded four-entry
NOMAD tray before any archive becomes the active geometry. The tray exposes formula,
reported symmetry, indexed calculation presence, and result-window provenance. Selecting
one entry triggers the same bounded archive conversion and client-side geometry,
relaxation, force, or calibration gate used previously; failure preserves the current
specimen and does not fall back to a weaker entry.

This improves experimental design without creating label leakage. Indexed formula,
space-group metadata, and tray order are never learner inputs. The receipt records explicit
candidate selection and page provenance, while GCTS still begins from the chosen archive's
species-labelled Cartesian coordinates and permitted supplied measurement channels.
