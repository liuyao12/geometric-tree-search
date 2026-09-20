# Frozen interface transfer with continuous pose feasibility

19 September 2026. Follow-up to [OFFATOM.md](OFFATOM.md).

## Question

Does choosing one atom-only least-squares registration hide valid connections
under the same learned interface? We freeze the complete interface model,
dictionary identities, endpoint roles, source coordinates and all tolerances.
No evaluation data changes the learned parameters.

## Two controls

1. Enumerate color-preserving point correspondences under necessary distance
   bounds, visiting at most 20,000 backtracking nodes per motif. Each map
   produces one proper Kabsch pose that must fit every atom within 0.15 Å.
   Include the original poses explicitly; do not deduplicate decorated maps.
2. For previously failed pairs, jointly optimize each endpoint's rotation and
   translation against atom positions, anchor coincidence and transported
   vector values. Use SLSQP to minimize maximum constraint violation. Keep
   at most 12 initializations ranked by initial interface mismatch, at most
   120 iterations each, with a two-second per-pair callback budget. Rotational
   increments use rotation vectors with components in [-π,π]; translation
   increments are bounded to ±0.3 Å per axis. These are declared numerical
   search limits, not proof of exhaustive feasibility.

Atomic fit tolerance stays 0.15 Å. Anchor and vector pair-separation tolerances
stay 0.30 Å, with the original 0.30 Å vector-to-displacement target prior.
Witnesses are accepted only by directly replaying all constraints, regardless
of optimizer success status. Independent replay uses numerical slack 10^-9 Å;
the largest checked atomic residual is 0.150000000007 Å. This is a floating-point
positive witness, not an exact-arithmetic geometric certificate.

## Results

| Method | α pairs / 99 | β pairs / 49 | Total / 148 |
|---|---:|---:|---:|
| Original poses | 2 | 15 | 17 |
| Additional correspondences | 3 | 15 | 18 |
| Joint continuous pose fit | 22 | 32 | 54 |

The correspondence control registered 276 motif occurrences, with at most
three entries per occurrence including the original pose. No correspondence
node budget was reached. Six templates are collinear and retain unsampled
continuous freedom; all other templates have numerical rank three.

Joint fitting adds 36 positive witnesses beyond the correspondence control,
37 beyond the original-pose baseline. No two-second budget stops were recorded;
iteration and initialization limits still apply. Failures remain unknown.
Every proposed pair has an individual witness in 3/44 α frames and 29/44 β
frames. This does **not** establish simultaneous frame feasibility: a motif
shared by two pairs can receive two incompatible poses. The pair proposal
graph can also be disconnected and is not the full GCTS frontier graph.

## Verification

Independent replay reads the source atoms, checks proper rotations and
species-preserving bijections, reconstructs periodic images, and evaluates
the transported anchors and vector values using the frozen model. Controls
reject omitted pairs, changed translations, nonproper matrices, nonbijective
maps and false residuals. Enumerator tests recover all 24 proper octahedral
maps, agree with exhaustive 720-map enumeration on six clouds, reject a
labeled reflection and explicitly report budget stops and collinear rank.

The result identifies a registration limitation; it does not resolve missing
connection types, anchor locality, t-support learning, shared-pose consistency,
condition-matched data, or growth. In particular, missed marking overlaps are
still unconstrained rather than forbidden. There is no search-speedup claim.

## Reproduce

After preparing `cohort`, `nested.json`, and `interfaces.json` as in the earlier
notes, place the supplied scripts in one directory and run:

```sh
python test-enumerate-rigid-proposals.py
python refit-offatom-interface-poses.py cohort/coordinates.json cohort/metadata.json nested.json interfaces.json reposed.json
python verify-reposed-interfaces.py cohort/coordinates.json cohort/metadata.json nested.json interfaces.json reposed.json reposed-check.json
python optimize-interface-poses.py cohort/coordinates.json cohort/metadata.json nested.json interfaces.json reposed.json continuous.json
python verify-reposed-interfaces.py cohort/coordinates.json cohort/metadata.json nested.json interfaces.json continuous.json continuous-check.json
python test-reposed-interface-check.py cohort/coordinates.json cohort/metadata.json nested.json interfaces.json continuous.json
```

The checker also requires `verify-offatom-interfaces.py` for independent
periodic-image enumeration. Receipts bind the original model and result hashes;
full coordinate-bearing pose witnesses are regenerated rather than bundled.
Time-bounded optimization can produce different counts on other machines.
