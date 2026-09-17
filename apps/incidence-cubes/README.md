# Incidence cubes

An interactive exposition and an independent Lean 4 project for Penrose's conic cube, Fomin–Pylyavskyy's surface cancellation, and the Veronese coefficient-space bridge.

[Live exposition](https://liuyao12.github.io/geometric-tree-search/apps/incidence-cubes/) · [Lean CI](https://github.com/liuyao12/geometric-tree-search/actions/workflows/incidence-cubes.yml) · [Blueprint](BLUEPRINT.md)

The page follows the reading-plus-floating-demo arrangement of `GCTS-I.html`. Its panel is sticky, draggable and horizontally resizable on desktop, and stacked above the text on mobile. “Follow text” selects the corresponding experiment while reading; using a control turns automatic following off. The reset-position button restores the panel.

## Four experiments

**Conics:** seven conics in a symmetric-matrix normal form; reveal the eighth; select cube edges for contact chords, points and tangents; select faces for concurrency. Drag the hollow seed-chord handles, change matrix couplings, pan with empty-space drag and zoom with Shift-wheel.

**Incidences:** a point/line cube built from perspective triangles. Drag O or vary the three point positions. Reveal the line containing the three side-intersection points. The face ratios are numerical diagnostics, not proof evidence.

**Cancellation:** arbitrary nonzero integer edge values on the oriented cube. Ratios and their total product use exact BigInt fractions. Doubling one edge changes two face ratios reciprocally. An arbitrary edge assignment is not claimed to be geometrically realizable.

**Bridge:** a conic pencil q(t)=q0−tℓ² and all six coefficient coordinates. The double-line vector remains constrained to the Veronese surface; no reduction of Penrose's theorem to the Fomin–Pylyavskyy master theorem is asserted.

## Formal project

```
formal/
  lean-toolchain                # Lean 4.19.0
  lakefile.lean
  lake-manifest.json            # exact dependency commits
  IncidenceCubes.lean           # imports every implemented module
  Audit.lean                    # all 17 public theorem dependencies
  IncidenceCubes/
    Penrose/Algebra.lean
    Fomin/Surface.lean
    Fomin/Coherence.lean
    Connection/Veronese.lean
```

From this directory:

```sh
cd formal
lake exe cache get
lake build
lake env lean Audit.lean
```

The build record is in `verification.json`. The GitHub workflow builds the root library, runs the axiom audit, rejects `sorryAx`, `Lean.ofReduceBool` and `Lean.trustCompiler` in the audited dependency lists, and uploads the audit and lockfile. It does not rely on browser or CAS outputs.

**Implemented scope:** the polynomial contact identities and algebraic eighth expression; face-pencil and polarization identities; general finite edge cancellation and its last-face consequence; a concrete finite cube certificate; coordinate cross-ratio/incidence equivalence; double-line evaluation, scaling, nonvanishing and the coefficient-pencil relation.

**Not yet a full formalization of both geometric theorems:** arbitrary-input normal-form existence, projective contact geometry, full completion/uniqueness, complete conics and a theorem comparing the two frameworks remain development targets. The general cancellation certificate records algebraic pairing data, not a topological manifold structure. See the blueprint for the precise boundary.

## Software tests and local preview

```sh
node test.cjs
python -m http.server 8000
```

Then open `http://localhost:8000/`. The engine and page have no external runtime dependencies. `test.cjs` runs 1,000 deterministic configurations, including all twelve contact identities and all six face conditions, exact edge-product cancellation, non-incidence and coefficient identities. `test-results.json` records the output. These are software tests, not replacements for Lean proofs.

Export data saves the current numerical configuration, explicitly marked as not a Lean certificate. No accounts, tracking, browser storage or user-data uploads are used.

## References

- Arnold, Chern, Eide, Gunn, Neukirchner and Penrose, [Penrose's eight-conic theorem](https://arxiv.org/html/2409.17150v8), especially §§6–7.
- Fomin and Pylyavskyy, [Incidences and tilings](https://arxiv.org/abs/2305.07728), Proposition 2.5, Theorem 2.6 and Proposition 9.1.
- [Chern's Penrose project page](https://cseweb.ucsd.edu/~alchern/projects/Penrose/).
