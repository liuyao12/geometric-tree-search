#!/usr/bin/env python3
"""Build a geometry-complete recurrent IQC macro-branch corpus.

The earlier recurrent-value fixture retained nine scalar branch features but
not the colored proper-SE(3) geometry or the finite port witnesses that made
each action possible.  Those labels cannot safely be retrofitted onto a newly
generated geometry.  This module therefore constructs a new corpus from
scratch from seventeen atom-domain-disjoint development nuclei.  Those nuclei
fit the primitive cluster vocabulary, connection marking, pose-port state
scorer, and later macro quotient under grouped cross-validation.  All seventeen
domains are disjoint from the unchanged ten wide fallback domains used only by
the external transfer audit.

Candidate branches are frozen before a group's target labels are joined.  A
branch carries a canonical right-handed local frame, all three colored action
sites, and every exact parent/source port witness expressed in the same frame.
No raw occurrence index, global frame, material label, lift, or target
coordinate is serialized as a model-facing field.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_iqc_expanded_development_preregistration import (
    EXPANDED_DEVELOPMENT_CENTERS, PRIOR_DEVELOPMENT_CENTERS)
from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS as WIDE_DEVELOPMENT_CENTERS,
    SAFETY_MARGIN as WIDE_SAFETY_MARGIN)
from materials_gcts_iqc_incidence_token_preflight import (
    _CandidateSource, _key, _minimum_distance)
from materials_gcts_iqc_pose_port_state_audit import (
    MINIMUM_STATE_GROUPS, MINIMUM_STATE_SUPPORT, TOKEN_SHRINKAGE,
    UPSTREAM_ANGULAR_BIN_WIDTH, _advance, _descriptors, _exact, _examples)
from materials_gcts_iqc_recurrent_prototype_connection_audit import _bounded
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_SEED_RADIUS, EVALUATION_TARGET_RADIUS, _crop)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch_fast
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)
from materials_gcts_pose_port_state_marking import (
    fit_pose_port_state_marking, pose_port_state_marking_digest,
    score_pose_port_state)
from materials_gcts_recursive_connections import (
    learn_recurrent_cluster_prototypes, learn_recursive_connection_marking,
    local_cluster_types, map_to_prototypes,
    merge_recursive_connection_markings)


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_recurrent_macro_geometry_dataset_v1.json.gz"
SCHEMA_VERSION = 1
BEAM_WIDTH = 4
ACTION_REACH = 4
SEARCH_DEPTH = 3
ORACLE_LIFT_BOUND = 24
TOKEN_SUPPORT = 4
TOKEN_GROUPS = 2
STATE_BIN_WIDTH = 1.0

# Group 9, (0,0,-50), is deliberately removed: its closed target ball can
# intersect a wide benchmark domain once that domain's larger audit radius is
# respected.  The first nine prior nuclei and all eight expansion nuclei are
# retained in their already-committed order.
EXCLUDED_PRIOR_INDEX = 9
DEVELOPMENT_CENTERS = (
    PRIOR_DEVELOPMENT_CENTERS[:EXCLUDED_PRIOR_INDEX] +
    EXPANDED_DEVELOPMENT_CENTERS)
UPSTREAM_FIT_GROUPS = len(DEVELOPMENT_CENTERS)


@dataclass(frozen=True)
class _SearchState:
    positions: tuple[tuple[float, float, float], ...]
    species: tuple[str, ...]
    proposals: object
    actions: tuple[tuple[tuple[float, float, float], str], ...]
    probabilities: tuple[float, ...]
    votes: tuple[int, ...]
    witnesses: tuple[tuple[object, ...], ...]
    cumulative_log_probability: float


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _sha(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _state_code(state):
    return {
        "parent": {
            "species": str(state.parent_type.color_key),
            "radial_counts": tuple(state.parent_type.cumulative_neighbor_counts),
        },
        "source": {
            "species": str(state.source_type.color_key),
            "radial_counts": tuple(state.source_type.cumulative_neighbor_counts),
        },
        "separation_bin": int(state.normalized_separation_bin),
    }


def _action_witnesses(state: _SearchState, point):
    """Detach exact occurrence witnesses before the action is applied."""
    pair_actions = state.proposals.pair_actions
    if pair_actions is None:
        raise AssertionError("candidate frontier lost exact pair provenance")
    rows = []
    for action in pair_actions.get(point, ()):
        rows.append({
            "state": _state_code(action.state),
            "parent_position": tuple(state.positions[action.parent_index]),
            "parent_species": str(state.species[action.parent_index]),
            "source_position": tuple(state.positions[action.source_index]),
            "source_species": str(state.species[action.source_index]),
        })
    if not rows:
        raise AssertionError("candidate action has no exact port witness")
    return tuple(rows)


def _normalize(vector):
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 1e-10:
        raise ValueError("cannot normalize a zero vector")
    return tuple(value / norm for value in vector)


def _subtract(left, right):
    return tuple(left[axis] - right[axis] for axis in range(3))


def _dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def _cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _frame(points):
    """Return a proper intrinsic frame from an ordered non-collinear triple."""
    first = _subtract(points[1], points[0])
    second = _subtract(points[2], points[0])
    e1 = _normalize(first)
    transverse = tuple(second[axis] - _dot(second, e1) * e1[axis]
                       for axis in range(3))
    e2 = _normalize(transverse)
    e3 = _normalize(_cross(e1, e2))
    if _dot(_cross(e1, e2), e3) < 1. - 1e-8:
        raise AssertionError("intrinsic frame is not right handed")
    return points[0], (e1, e2, e3)


def _in_frame(point, origin, frame, scale):
    vector = _subtract(point, origin)
    return tuple(round(_dot(vector, axis) / scale, 6) for axis in frame)


def _canonical_macro_geometry(center, actions, witness_rows,
                              minimum_distance):
    """Quotient global translation/proper rotation and action insertion order.

    Reflections are not admitted: every candidate frame is explicitly
    right-handed.  Port endpoints use the same frame as the three emitted
    sites, so the payload can later reconstruct complete local macro geometry.
    """
    if len(actions) != SEARCH_DEPTH or len(witness_rows) != SEARCH_DEPTH:
        raise ValueError("macro geometry requires a complete three-action branch")
    candidates = []
    for permutation in itertools.permutations(range(SEARCH_DEPTH)):
        ordered_points = tuple(actions[index][0] for index in permutation)
        try:
            origin, frame = _frame(ordered_points)
        except ValueError:
            continue
        nodes = []
        for canonical_index, source_index in enumerate(permutation):
            point, color = actions[source_index]
            witnesses = []
            for witness in witness_rows[source_index]:
                witnesses.append({
                    "state": witness["state"],
                    "parent_species": witness["parent_species"],
                    "source_species": witness["source_species"],
                    "parent_local_nn": _in_frame(
                        witness["parent_position"], origin, frame,
                        minimum_distance),
                    "source_local_nn": _in_frame(
                        witness["source_position"], origin, frame,
                        minimum_distance),
                })
            nodes.append({
                "node": canonical_index,
                "species": str(color),
                "local_nn": _in_frame(point, origin, frame, minimum_distance),
                "center_distance_nn": round(
                    math.dist(point, center) / minimum_distance, 6),
                "port_witnesses": tuple(sorted(
                    witnesses, key=lambda row: _canonical_json(row))),
            })
        payload = {
            "nodes": tuple(nodes),
            "center_local_nn": _in_frame(
                center, origin, frame, minimum_distance),
            "proper_frame_determinant": 1,
        }
        candidates.append((_canonical_json(payload), payload))
    if not candidates:
        raise ValueError("three emitted sites do not define a finite proper frame")
    payload = min(candidates, key=lambda row: row[0])[1]
    payload["canonical_digest"] = _sha(payload)
    return payload


def _branch_features(actions, probabilities, votes):
    distances = tuple(math.dist(actions[left][0], actions[right][0])
                      for left in range(len(actions))
                      for right in range(left + 1, len(actions)))
    return (
        sum(math.log(max(value, 1e-15)) for value in probabilities),
        min(probabilities), sum(probabilities), float(sum(votes)),
        float(max(votes)), float(len({color for _point, color in actions})),
        min(distances), sum(distances) / len(distances), max(distances),
    )


def _configuration_key(actions):
    return tuple(sorted((tuple(point), str(color)) for point, color in actions))


def _freeze_group_candidates(source, state_model, connection):
    """Generate immutable terminal branches without reading ``source.truth``."""
    public = SimpleNamespace(
        group=source.group, seed_positions=tuple(source.seed_positions),
        seed_species=tuple(source.seed_species))
    proposals = _bounded(connection, public, local_cluster_types(
        public.seed_positions, public.seed_species, CLUSTER_EDGES))
    states = (_SearchState(
        public.seed_positions, public.seed_species, proposals,
        (), (), (), (), 0.),)
    depth_candidate_counts = []
    retained_counts = []
    for depth in range(1, SEARCH_DEPTH + 1):
        children = {}
        candidates = 0
        for state in states:
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
                -score_pose_port_state(state_model, descriptors[point]),
                -state.proposals.votes[point], point)))[:ACTION_REACH]
            for point in ordered:
                candidates += 1
                color = str(_dominant_source_color(state.proposals, point))
                probability = score_pose_port_state(
                    state_model, descriptors[point])
                vote = int(state.proposals.votes[point])
                witnesses = _action_witnesses(state, point)
                positions, species, future = advance_frontier_configuration(
                    connection, state.proposals, state.positions,
                    state.species, (point,), (color,), CLUSTER_EDGES,
                    source.group, EVALUATION_TARGET_RADIUS)
                actions = state.actions + ((tuple(point), color),)
                cumulative = state.cumulative_log_probability + math.log(
                    max(probability, 1e-15))
                child = _SearchState(
                    positions, species, future, actions,
                    state.probabilities + (probability,),
                    state.votes + (vote,), state.witnesses + (witnesses,),
                    cumulative)
                key = _configuration_key(actions)
                prior = children.get(key)
                if prior is None or (cumulative, actions) > (
                        prior.cumulative_log_probability, prior.actions):
                    children[key] = child
        depth_candidate_counts.append(candidates)
        ordered_children = tuple(sorted(children.values(), key=lambda row: (
            -row.cumulative_log_probability,
            _configuration_key(row.actions))))
        states = (ordered_children if depth == SEARCH_DEPTH else
                  ordered_children[:BEAM_WIDTH])
        retained_counts.append(len(states))
        if not states:
            break

    minimum = source.minimum_distance
    raw_rows = []
    for state in states:
        if len(state.actions) != SEARCH_DEPTH:
            continue
        geometry = _canonical_macro_geometry(
            source.group, state.actions, state.witnesses, minimum)
        occurrence_key = tuple(sorted(
            ((tuple(round(value, 8) for value in point), str(color))
             for point, color in state.actions)))
        raw_rows.append({
            # Opaque execution identity only.  The global coordinates used to
            # create it never enter a learned descriptor.
            "candidate_id": _sha({
                "group": source.group, "actions": occurrence_key}),
            "production_alternative_id": geometry["canonical_digest"],
            "geometry": geometry,
            "scalar_features": _branch_features(
                state.actions, state.probabilities, state.votes),
            "action_colors": tuple(color for _point, color in state.actions),
            "action_probabilities": tuple(state.probabilities),
            "action_votes": tuple(state.votes),
            # Private generation-time payload.  It is excluded from both the
            # candidate digest and serialized fixture immediately after the
            # detached target labels have been joined.
            "_world_actions": tuple(state.actions),
        })
    # Search order is not occurrence identity.  Distinct insertion histories
    # that replay the same world occurrence are retained as alternative
    # derivations.  Conversely, proper-motion-equivalent occurrences remain
    # separate candidate actions while sharing production-alternative IDs.
    grouped = {}
    for row in raw_rows:
        grouped.setdefault(row["candidate_id"], []).append(row)
    rows = []
    for candidate_id, alternatives in sorted(grouped.items()):
        first = alternatives[0]
        if any(_configuration_key(row["_world_actions"]) !=
               _configuration_key(first["_world_actions"])
               for row in alternatives[1:]):
            raise AssertionError("opaque macro occurrence collision")
        derivations = tuple(sorted(({
            "production_alternative_id": row[
                "production_alternative_id"],
            "geometry": row["geometry"],
            "scalar_features": row["scalar_features"],
            "action_colors": row["action_colors"],
            "action_probabilities": row["action_probabilities"],
            "action_votes": row["action_votes"],
        } for row in alternatives), key=lambda row: _canonical_json(row)))
        primary = max(alternatives, key=lambda row: (
            sum(math.log(max(value, 1e-15))
                for value in row["action_probabilities"]),
            row["scalar_features"]))
        rows.append({
            "candidate_id": candidate_id,
            "production_alternative_ids": tuple(sorted({
                row["production_alternative_id"]
                for row in alternatives})),
            "geometry": first["geometry"],
            "scalar_features": primary["scalar_features"],
            "action_colors": primary["action_colors"],
            "action_probabilities": primary["action_probabilities"],
            "action_votes": primary["action_votes"],
            "derivation_count": len(derivations),
            "derivations": derivations,
            "_world_actions": first["_world_actions"],
        })
    rows = tuple(rows)
    return rows, tuple(depth_candidate_counts), tuple(retained_counts)


def _attach_labels(rows, truth):
    """Join colored target labels only after immutable candidates exist."""
    labeled = []
    for row in rows:
        actions = tuple((node["local_nn"], node["species"])
                        for node in row["geometry"]["nodes"])
        # Exact labels must use world coordinates, which are intentionally not
        # serialized.  Recover them from the detached candidate's witness-free
        # canonical ID is impossible by design; caller supplies a parallel
        # private action lookup produced before serialization.
        if "_world_actions" not in row:
            raise AssertionError("private world action lookup is unavailable")
        exact_sites = tuple(
            truth.get(_key(point)) == color
            for point, color in row["_world_actions"])
        public = {key: value for key, value in row.items()
                  if not key.startswith("_")}
        public["exact_sites"] = sum(exact_sites)
        public["exact"] = all(exact_sites)
        labeled.append(public)
    return tuple(labeled)


def _source(center, seed, target, connection):
    public = SimpleNamespace(
        group=center, seed_positions=tuple(seed.positions),
        seed_species=tuple(seed.species))
    proposals = _bounded(connection, public, local_cluster_types(
        public.seed_positions, public.seed_species, CLUSTER_EDGES))
    return _CandidateSource(
        center, proposals, tuple(seed.positions), tuple(seed.species),
        {_key(point): color for point, color in zip(
            target.positions, target.species)},
        _minimum_distance(seed.positions))


def _fit_program(sources):
    """Fit one recurrent primitive/port program on all development nuclei."""
    raw = tuple(local_cluster_types(
        source.seed_positions, source.seed_species, CLUSTER_EDGES)
        for source in sources)
    prototypes = learn_recurrent_cluster_prototypes(raw, minimum_groups=2)
    markings = tuple(learn_recursive_connection_marking(
        source.seed_positions, map_to_prototypes(types, prototypes),
        tuple(source.truth), HIDDEN_UNIT, minimum_positive_support=1,
        minimum_purity=1e-9, target_colors=tuple(source.truth.values()))
        for source, types in zip(sources, raw))
    positives = tuple(tuple(state for state, row in marking.evidence.items()
                             if row.positive > 0) for marking in markings)
    connection = merge_recursive_connection_markings(
        markings, minimum_positive_support=2,
        minimum_positive_groups=2, minimum_purity=.5,
        positive_states_by_marking=positives)
    return prototypes, connection


def _all_training_corpora(sources, connection):
    """Fit state evidence on every development group, never the wide set."""
    corpora = []
    for source in sources:
        positions = tuple(source.seed_positions)
        species = tuple(source.seed_species)
        proposals = _bounded(connection, source, local_cluster_types(
            positions, species, CLUSTER_EDGES))
        stages = []
        for _wave in range(3):
            labels = {point: _exact(source, proposals, point)
                      for point in proposals.votes}
            descriptors = _descriptors(
                positions, species, proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            points = tuple(sorted(proposals.votes))
            stages.append(tuple(
                (descriptors[point], labels[point]) for point in points))
            exact = tuple(sorted(
                (point for point in proposals.votes if labels[point]),
                key=lambda point: (-proposals.votes[point], point))[:64])
            if not exact:
                break
            positions, species, proposals = _advance(
                source, connection, positions, species, proposals, exact)
        corpora.append(tuple(stages))
    return tuple(corpora)


def _build_crops():
    physical_radius = math.ceil(max(math.dist((0., 0., 0.), center)
                                    for center in DEVELOPMENT_CENTERS) +
                                EVALUATION_TARGET_RADIUS)
    oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND, physical_radius)
    check, _ = oracle_patch_fast(ORACLE_LIFT_BOUND + 1, physical_radius)
    crops = []
    for center in DEVELOPMENT_CENTERS:
        seed = _crop(oracle, center, EVALUATION_SEED_RADIUS,
                     "IQC-recurrent-macro-seed")
        target = _crop(oracle, center, EVALUATION_TARGET_RADIUS,
                       "IQC-recurrent-macro-target")
        check_seed = _crop(check, center, EVALUATION_SEED_RADIUS,
                           "IQC-recurrent-macro-seed-check")
        check_target = _crop(check, center, EVALUATION_TARGET_RADIUS,
                             "IQC-recurrent-macro-target-check")
        if (tuple(seed.positions), tuple(seed.species),
                tuple(target.positions), tuple(target.species)) != (
                tuple(check_seed.positions), tuple(check_seed.species),
                tuple(check_target.positions), tuple(check_target.species)):
            raise AssertionError("development crop changes at bound plus one")
        crops.append((seed, target))
    return tuple(crops), physical_radius


def _domain_audit():
    pairwise = min(math.dist(left, right)
                   for index, left in enumerate(DEVELOPMENT_CENTERS)
                   for right in DEVELOPMENT_CENTERS[index + 1:])
    wide_required = (EVALUATION_TARGET_RADIUS * 2 + WIDE_SAFETY_MARGIN)
    wide_separation = min(math.dist(left, right)
                          for left in DEVELOPMENT_CENTERS
                          for right in WIDE_DEVELOPMENT_CENTERS)
    return pairwise, wide_required, wide_separation


def build_dataset():
    crops, physical_radius = _build_crops()

    # The entire development corpus is training data relative to the sealed,
    # atom-domain-disjoint wide benchmark.  Later quotient selection remains
    # grouped by nucleus; no wide atom or label enters this fit.
    seed_sources = tuple(_CandidateSource(
        center, None, tuple(seed.positions), tuple(seed.species),
        {_key(point): color for point, color in zip(
            target.positions, target.species)},
        _minimum_distance(seed.positions))
        for center, (seed, target) in zip(DEVELOPMENT_CENTERS, crops))
    prototypes, connection = _fit_program(seed_sources)
    sources = tuple(_source(center, seed, target, connection)
                    for center, (seed, target) in zip(
                        DEVELOPMENT_CENTERS, crops))

    training = _all_training_corpora(sources, connection)
    state_model = fit_pose_port_state_marking(
        _examples(training), minimum_token_support=TOKEN_SUPPORT,
        minimum_token_groups=TOKEN_GROUPS,
        token_shrinkage=TOKEN_SHRINKAGE,
        state_bin_width=STATE_BIN_WIDTH,
        minimum_state_support=MINIMUM_STATE_SUPPORT,
        minimum_state_groups=MINIMUM_STATE_GROUPS)

    groups = []
    candidate_freeze = []
    for group, source in enumerate(sources):
        rows, depth_counts, retained = _freeze_group_candidates(
            source, state_model, connection)
        # Keep world actions private only until labels are joined.  The frozen
        # candidate digest below excludes them and all target information.
        # Reconstruct the mapping from the canonical ID using a second local
        # enumeration is deliberately avoided; `_freeze_group_candidates`
        # attaches this private field before returning.
        candidate_freeze.extend((group, row["candidate_id"],
                                 row["production_alternative_ids"],
                                 row["derivations"])
                                for row in rows)
        labeled = _attach_labels(rows, source.truth)
        groups.append({
            "group": group,
            "role": "development-fit",
            "center": source.group,
            "seed_atoms": len(source.seed_positions),
            "target_atoms": len(source.truth),
            "depth_candidate_counts": depth_counts,
            "retained_configurations": retained,
            "rows": labeled,
        })

    pairwise, wide_required, wide_separation = _domain_audit()
    body = {
        "schema_version": SCHEMA_VERSION,
        "description": "geometry-complete three-action recurrent IQC macro corpus",
        "development_centers": DEVELOPMENT_CENTERS,
        "excluded_prior_center": PRIOR_DEVELOPMENT_CENTERS[
            EXCLUDED_PRIOR_INDEX],
        "excluded_prior_reason": "closed domain can intersect wide benchmark",
        "upstream_fit_groups": UPSTREAM_FIT_GROUPS,
        "upstream_heldout_groups": len(DEVELOPMENT_CENTERS) -
            UPSTREAM_FIT_GROUPS,
        "seed_radius": EVALUATION_SEED_RADIUS,
        "target_radius": EVALUATION_TARGET_RADIUS,
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "oracle_physical_radius": physical_radius,
        "oracle_bound_plus_one_stable": True,
        "minimum_development_center_separation": pairwise,
        "required_development_separation": 2 * EVALUATION_TARGET_RADIUS,
        "minimum_wide_center_separation": wide_separation,
        "required_wide_separation": wide_required,
        "development_domains_pairwise_disjoint": pairwise >
            2 * EVALUATION_TARGET_RADIUS,
        "wide_domains_disjoint_by_closed_ball_certificate":
            wide_separation > wide_required,
        "primitive_prototypes": len(prototypes),
        "accepted_connection_states": len(connection.accepted_states),
        "connection_digest": hashlib.sha256(
            repr((prototypes, connection)).encode()).hexdigest(),
        "state_model_digest": pose_port_state_marking_digest(state_model),
        "state_model_fit_groups": tuple(range(UPSTREAM_FIT_GROUPS)),
        "state_model_target_groups_used": tuple(range(UPSTREAM_FIT_GROUPS)),
        "development_targets_used_for_upstream_fit": True,
        "candidate_generation_reads_target_after_upstream_fit": False,
        "labels_joined_after_candidate_freeze": True,
        "proper_se3_canonical_geometry": True,
        "raw_occurrence_ids_serialized": False,
        "global_frame_used_as_model_feature": False,
        "wide_atoms_or_labels_used": False,
        "candidate_digest": _sha(candidate_freeze),
        "groups": tuple(groups),
    }
    body["dataset_digest"] = _sha(body)
    return body


def write_fixture(path=DEFAULT_FIXTURE):
    dataset = build_dataset()
    raw = _canonical_json(dataset)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(path, "wb", mtime=0) as handle:
        handle.write(raw)
    return dataset


def load_fixture(path=DEFAULT_FIXTURE):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    digest = payload.pop("dataset_digest")
    if _sha(payload) != digest:
        raise AssertionError("recurrent macro geometry fixture digest drift")
    payload["dataset_digest"] = digest
    return payload


def validate_dataset(payload):
    if payload["schema_version"] != SCHEMA_VERSION:
        raise AssertionError("unexpected recurrent macro geometry schema")
    if not payload["development_domains_pairwise_disjoint"] or \
            not payload["wide_domains_disjoint_by_closed_ball_certificate"]:
        raise AssertionError("macro corpus domains are not disjoint")
    if payload["upstream_fit_groups"] != UPSTREAM_FIT_GROUPS:
        raise AssertionError("upstream split drift")
    if not payload["labels_joined_after_candidate_freeze"] or \
            not payload["proper_se3_canonical_geometry"]:
        raise AssertionError("candidate freeze or proper geometry missing")
    rows = tuple(row for group in payload["groups"] for row in group["rows"])
    if not rows:
        raise AssertionError("macro corpus contains no terminal branches")
    if any(len(row["geometry"]["nodes"]) != SEARCH_DEPTH
           for row in rows):
        raise AssertionError("incomplete macro branch geometry")
    if any(not all(node["port_witnesses"]
                   for node in row["geometry"]["nodes"])
           for row in rows):
        raise AssertionError("macro branch lost port incidence")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-fixture", action="store_true")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = write_fixture(args.fixture) if args.write_fixture else \
        load_fixture(args.fixture)
    validate_dataset(payload)
    summary = {
        "dataset_digest": payload["dataset_digest"],
        "groups": len(payload["groups"]),
        "terminal_branches": sum(len(group["rows"])
                                 for group in payload["groups"]),
        "exact_branches": sum(row["exact"] for group in payload["groups"]
                              for row in group["rows"]),
        "upstream_fit_groups": payload["upstream_fit_groups"],
        "upstream_heldout_groups": payload["upstream_heldout_groups"],
        "state_model_digest": payload["state_model_digest"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True)
          if args.json else summary)


if __name__ == "__main__":
    main()
