# Incidence Cubes: formalization blueprint

## Scope and mathematical models

Develop two independent theories and explicit comparison theorems. Do not replace the original geometric hypotheses with a parametrized family and then call that the complete theorem. Do not conflate symbolic identities, floating-point diagnostics, exact finite calculations and Lean verification.

The first layer works over commutative rings and fields. For ordinary conic tangency, start over a commutative field of characteristic different from two; either work geometrically over an algebraic closure or state when the two contact points exist over the base field. A real rendering may omit complex contact points.

The reference papers are [Penrose's eight-conic theorem, v8](https://arxiv.org/html/2409.17150v8) and [Fomin–Pylyavskyy, Incidences and tilings](https://arxiv.org/abs/2305.07728). This blueprint is an implementation plan, not a claim that all targets below are proved.

## Implemented kernel

### Penrose.Algebra

`D2`, `D3` are explicit parameter determinants. `F1`, `F2`, `F3` are explicit bordered-determinant polynomials. `L1`, `L2` are contact linear expressions.

`bottom_edge`, `middle_edge`, `top_edge` prove

    D_(S+k) F_S − D_S F_(S+k) = L_(S,k)^2.

`exists_algebraic_eighth` supplies ONE expression satisfying all three top-edge equations simultaneously. `face_pencil_identity` proves the cleared-denominator relation among the four chords of an upper face. `top_face_common_zero` extracts its common-zero consequence under a nonzero diagonal assumption. Permutations supply the other faces.

`polar_rank_one_update` and `polar_agrees_on_chord` show that the unnormalized polarization of aq+bℓ² agrees with that of aq when ℓ(x)=0. These are algebraic statements, not assertions of smoothness or two distinct real contact points.

### Fomin.Surface

`ClosedQuadrangulation` currently means an **edge-cancellation certificate**: two bijections `(Face × Fin 2) ≃ Edge`. Every edge is used once in a positive slot and once in a negative slot. There is not yet a vertex incidence map, cyclic boundary structure or a surface-realization theorem. Renaming/refining the structure when adding topology is appropriate; do not mistake its name for additional fields.

`total_product` proves cancellation in any commutative group. `last_face` forces the remaining multiplicative face relation. The finite `cube` records the exact permutations shared with `engine.js`; bijectivity is proved by kernel-evaluated `decide`, not `native_decide`. `cube_last_face` specializes the abstract theorem.

For a field, edge values live in its units. The raw field value 0 must never be silently treated as invertible.

### Fomin.Coherence

`cross_dot_identity` identifies the mixed pairing determinant with the pairing between a join and a meet. `ratio_one_iff_incident` includes nonzero denominators. Interpreting these coordinates projectively additionally requires nonzero representatives and nonzero cross products. The entire paper's geometric master theorem is not bundled into this statement yet.

### Connection.Veronese

Six coefficient coordinates are used, ordered `x²,y²,z²,xy,xz,yz`. Mixed coefficients include a factor of two for double lines. `eval_doubleLine`, `doubleLine_rescale`, `doubleLine_ne_zero` and `rank_one_pencil` prove the coordinate bridge. Nonzero quadratic coefficient vectors are distinct from their sets of rational zeros, especially over finite fields.

## Next milestone A: genuine projective contact

1. Build projective classes of nonzero linear and quadratic coefficient vectors, reusing mathlib projectivization where practical.
2. Define a conic's symmetric bilinear/polar form; prove that rescaling does not change its projective polar line. Record characteristic assumptions explicitly.
3. Define rank-one contact pencils independently of ordinary two-point tangency. Prove the appropriate equivalence when both conics are nonsingular, coefficients are nonzero and the chord meets the conic in two distinct points.
4. Track separately: nonzero equation, nonsingular conic matrix, nonzero parameter determinant, independent chord forms, distinct conics and distinct contact points. None is a synonym for the others.

## Next milestone B: arbitrary seven-conic input to normal form

Define seven projective conics indexed by subsets of {1,2,3} of size at most two, with adjacent contact data and the three completed-face concurrency conditions. The input must NOT contain a preselected matrix M or the desired normal-form conclusion.

Choose representatives q0, qi and chord forms pi so that

    qi = q0 − pi²/di,  di ≠ 0.

On each completed face, concurrence puts the other contact forms in span(pi,pj). Derive a common normalization

    qij = q0 + (pi,pj) H_ij (pi,pj)^T.

Use the two rank-one differences to prove that, under explicit exclusions,

    −H_ij^(-1) = [[di,aij],[aij,dj]].

Assemble the three aij into one symmetric M and prove all seven coefficient identities. Prove that all representative choices lead to the same projective output. This is the central missing normal-form theorem, not an omitted routine simplification.

## Next milestone C: completion and uniqueness

Instantiate the polynomial identities in a multivariable polynomial ring or coefficient-vector module. Connect the explicit `F` expressions to actual bordered principal determinants. Construct the eighth projective conic, prove it is nonzero, and establish the remaining contacts and face concurrences.

For uniqueness, formalize the three new face-concurrence points, the forced contact chords between them, and the intersection of conic pencils. State precisely the general-position hypothesis under which the points and pencils are distinct. Compare the result with the reference theorem's stronger scope before naming it a full formalization.

Only subsequently add singular parameter blocks, singular conics, coalescent contacts and complete conics retaining dual information. Polynomial specialization alone is not a proof of a limiting contact assertion.

## Next milestone D: full geometric surface theorem

Introduce a finite oriented bicolored quadrangulation with vertices, edges, faces, cyclic face boundaries and edge-reversal pairing. Map it to the existing cancellation certificate; keep topology separate from the weaker algebraic data actually needed.

Label even vertices by projective points and odd vertices by hyperplanes. Use non-incidence to assign units to edges. Prove that each faceWeight equals its representative-independent mixed cross-ratio. Then compose `last_face` with coherence to get the geometric master theorem from arbitrary admissible labels.

Prove Pappus/Desargues examples via explicit finite certificates. Separately prove the seven-to-eight existence-and-uniqueness statement of Proposition 9.1; this is not merely the all-but-one-face implication on eight already supplied labels.

## Next milestone E: meaningful comparison

First projectivize the Veronese bridge: a contact pencil gives three collinear points in P^5, one constrained to be a double line. Show that concurrent contact chords map into the Veronese conic associated to a two-dimensional covector subspace.

A proposed reduction must specify: translated vertices/edges/faces; allowed auxiliary constructions; all nonzero conditions; the precise retained Veronese constraints; and a proof that the translated conclusion recovers contact and concurrency. A common cube-shaped diagram is not such a proof. Explore degenerations to a shared Desargues configuration before attempting a general reduction.

## Engineering and verification rules

- Every implemented module is imported by the root library; no hidden unfinished modules count as completed work.
- No `sorry`, `admit`, custom theorem axioms, native computation assumptions or unchecked external certificates in accepted theorem dependencies.
- Update `Audit.lean` whenever adding a public theorem. Keep the toolchain and dependency lockfile pinned.
- `verification.json` names the exact verified commit and CI run. An older verified kernel may coexist with later UI-only commits; record that distinction.
- Keep UI tests independent of Lean. Use numerical tolerances only in rendering/tests, never in a theorem claim.
- Tests verify the browser cube's slot permutations against Lean's source. This guards encoding drift but does not certify JavaScript execution inside Lean.
- The article exposes implemented scope and pending milestones. Change its coverage ledger only when the corresponding theorem compiles and passes the dependency audit.
