#!/usr/bin/env python3
"""Execute the preregistered autonomous IQC pose-port confirmation once."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import _dominant_source_color
from materials_gcts_iqc_expanded_development_baseline import _expanded_fixture
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_pose_port_autonomous_preregistration_v2 import (
    ACTION_REACH_PER_CONFIGURATION, BEAM_WIDTH, CONFIRMATION_CENTER,
    EXPECTED_MODEL_DIGEST, MINIMUM_STATE_GROUPS, MINIMUM_STATE_SUPPORT,
    MINIMUM_TOKEN_GROUPS, MINIMUM_TOKEN_SUPPORT, ORACLE_LIFT_BOUND,
    SEARCH_DEPTH, SEED_RADIUS,
    STATE_BIN_WIDTH, TARGET_RADIUS, TOKEN_SHRINKAGE,
    UPSTREAM_ANGULAR_BIN_WIDTH, audit as preregistration_audit)
from materials_gcts_iqc_pose_port_state_audit import (
    _descriptors, _examples, _program, _training_corpora)
from materials_gcts_iqc_recurrent_prototype_connection_audit import _bounded
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, _crop)
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_persistent_frontier_beam import advance_frontier_configuration
from materials_gcts_pose_port_state_marking import (
    fit_pose_port_state_marking, pose_port_state_marking_digest,
    score_pose_port_state)
from materials_gcts_recursive_connections import local_cluster_types


EXPECTED_PREREGISTRATION_DIGEST = \
    "39ad50d65f18b30a3d7f8b85abd5349de3e56f3edbc412460596378b0a99bb24"


@dataclass(frozen=True)
class FrozenBeamCandidate:
    depth: int
    parent_configuration: tuple[tuple[tuple[float, float, float], str], ...]
    point: tuple[float, float, float]
    species: str
    state_probability: float
    vote_count: int


@dataclass(frozen=True)
class _Configuration:
    positions: tuple[tuple[float, float, float], ...]
    species: tuple[str, ...]
    proposals: object
    actions: tuple[tuple[tuple[float, float, float], str], ...]
    cumulative_log_probability: float


@dataclass(frozen=True)
class IQCPosePortAutonomousConfirmation:
    preregistration_digest: str
    confirmation_center: tuple[float, float, float]
    seed_radius: float
    target_radius: float
    seed_atoms: int
    target_atoms: int
    oracle_lift_bound: int
    target_bound_plus_one_stable: bool
    model_digest: str
    model_matches_preregistration: bool
    frozen_recurrent_states: int
    beam_width: int
    action_reach_per_configuration: int
    search_depth: int
    candidate_counts_by_depth: tuple[int, ...]
    retained_configurations_by_depth: tuple[int, ...]
    candidate_digest: str
    trace_digest_before_target_open: str
    selected_actions: tuple[tuple[tuple[float, float, float], str], ...]
    selected_action_probabilities: tuple[float, ...]
    emitted_sites: int
    correct_sites: int
    false_sites: int
    precision: float
    target_open_count: int
    target_materialized_after_execution: bool
    target_used_for_candidate_generation: bool
    target_used_for_model_fit: bool
    exact_candidate_geometry_changed: bool
    self_fed_depth: int
    autonomous_top1_gate_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def _configuration_key(actions):
    return tuple(sorted(actions))


def _seed_crop_at_frozen_bound():
    physical_radius = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SEED_RADIUS)
    oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND, physical_radius)
    return _crop(oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "IQC-pose-port-autonomous-seed")


def _open_target_once():
    physical_radius = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + TARGET_RADIUS)
    oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND, physical_radius)
    check, _ = oracle_patch_fast(ORACLE_LIFT_BOUND + 1, physical_radius)
    target = _crop(oracle, CONFIRMATION_CENTER, TARGET_RADIUS,
                   "IQC-pose-port-autonomous-target")
    target_check = _crop(check, CONFIRMATION_CENTER, TARGET_RADIUS,
                         "IQC-pose-port-autonomous-target-check")
    stable = (tuple(target.positions), tuple(target.species)) == (
        tuple(target_check.positions), tuple(target_check.species))
    if not stable:
        raise AssertionError("confirmation crop changes at bound plus one")
    return target, stable


def _execute(model, connection, seed):
    source = SimpleNamespace(
        group=CONFIRMATION_CENTER,
        seed_positions=tuple(seed.positions),
        seed_species=tuple(seed.species))
    proposals = _bounded(connection, source, local_cluster_types(
        source.seed_positions, source.seed_species, CLUSTER_EDGES))
    states = (_Configuration(
        source.seed_positions, source.seed_species, proposals, (), 0.),)
    snapshots = []
    candidate_counts = []
    retained_counts = []
    for depth in range(1, SEARCH_DEPTH + 1):
        children = {}
        depth_rows = []
        for state in states:
            descriptors = _descriptors(
                state.positions, state.species, state.proposals,
                UPSTREAM_ANGULAR_BIN_WIDTH)
            ordered = tuple(sorted(state.proposals.votes, key=lambda point: (
                -score_pose_port_state(model, descriptors[point]),
                -state.proposals.votes[point], point)))[
                    :ACTION_REACH_PER_CONFIGURATION]
            for point in ordered:
                color = str(_dominant_source_color(state.proposals, point))
                probability = score_pose_port_state(
                    model, descriptors[point])
                row = FrozenBeamCandidate(
                    depth, _configuration_key(state.actions), tuple(point),
                    color, probability, int(state.proposals.votes[point]))
                depth_rows.append(row)
                positions, species, proposals = advance_frontier_configuration(
                    connection, state.proposals, state.positions,
                    state.species, (point,), (color,), CLUSTER_EDGES,
                    CONFIRMATION_CENTER, TARGET_RADIUS)
                actions = state.actions + ((tuple(point), color),)
                child = _Configuration(
                    positions, species, proposals, actions,
                    state.cumulative_log_probability + math.log(
                        max(probability, 1e-15)))
                key = _configuration_key(actions)
                prior = children.get(key)
                if prior is None or (
                        child.cumulative_log_probability,
                        tuple(child.actions)) > (
                            prior.cumulative_log_probability,
                            tuple(prior.actions)):
                    children[key] = child
        snapshots.append(tuple(sorted(depth_rows, key=repr)))
        candidate_counts.append(len(depth_rows))
        states = tuple(sorted(children.values(), key=lambda state: (
            -state.cumulative_log_probability,
            _configuration_key(state.actions)))[:BEAM_WIDTH])
        retained_counts.append(len(states))
        if not states:
            break
    selected = states[0] if states else _Configuration(
        source.seed_positions, source.seed_species, proposals, (), 0.)
    candidate_digest = hashlib.sha256(
        repr(tuple(snapshots)).encode()).hexdigest()
    trace_payload = (
        candidate_digest, tuple(candidate_counts), tuple(retained_counts),
        tuple((_configuration_key(state.actions),
               state.cumulative_log_probability) for state in states),
        selected.actions)
    trace_digest = hashlib.sha256(repr(trace_payload).encode()).hexdigest()
    selected_probabilities = []
    prefix = ()
    for action in selected.actions:
        match = next(row for rows in snapshots for row in rows
                     if row.parent_configuration == _configuration_key(prefix)
                     and (row.point, row.species) == action)
        selected_probabilities.append(match.state_probability)
        prefix += (action,)
    return (tuple(snapshots), tuple(candidate_counts), tuple(retained_counts),
            candidate_digest, trace_digest, selected,
            tuple(selected_probabilities))


def evaluate() -> IQCPosePortAutonomousConfirmation:
    protocol = preregistration_audit()
    if protocol.manifest_digest != EXPECTED_PREREGISTRATION_DIGEST:
        raise AssertionError("autonomous pose-port protocol drift")
    if not protocol.source_hashes_match or not protocol.domains_disjoint:
        raise AssertionError("autonomous pose-port preregistration invalid")

    sources, _counts, _origin = _expanded_fixture()
    _prototypes, connection = _program(sources)
    training = _training_corpora(sources, connection)
    model = fit_pose_port_state_marking(
        _examples(training),
        minimum_token_support=MINIMUM_TOKEN_SUPPORT,
        minimum_token_groups=MINIMUM_TOKEN_GROUPS,
        token_shrinkage=TOKEN_SHRINKAGE,
        state_bin_width=STATE_BIN_WIDTH,
        minimum_state_support=MINIMUM_STATE_SUPPORT,
        minimum_state_groups=MINIMUM_STATE_GROUPS)
    model_digest = pose_port_state_marking_digest(model)
    if model_digest != EXPECTED_MODEL_DIGEST:
        raise AssertionError("frozen pose-port model drift")

    seed = _seed_crop_at_frozen_bound()
    if not seed.positions:
        raise AssertionError("frozen confirmation seed is empty")
    (snapshots, candidate_counts, retained_counts, candidate_digest,
     trace_digest, selected, probabilities) = _execute(
        model, connection, seed)
    frozen_execution = (
        snapshots, candidate_counts, retained_counts, candidate_digest,
        trace_digest, selected.actions, probabilities)

    target_open_count = 0
    target, target_stable = _open_target_once()
    target_open_count += 1
    truth = {_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    correct = sum(truth.get(_key(point)) == color
                  for point, color in selected.actions)
    if frozen_execution != (
            snapshots, candidate_counts, retained_counts, candidate_digest,
            trace_digest, selected.actions, probabilities):
        raise AssertionError("execution mutated after target open")
    emitted = len(selected.actions)
    false = emitted - correct
    passed = emitted == SEARCH_DEPTH and correct == emitted
    return IQCPosePortAutonomousConfirmation(
        EXPECTED_PREREGISTRATION_DIGEST, CONFIRMATION_CENTER, SEED_RADIUS,
        TARGET_RADIUS, len(seed.positions), len(target.positions),
        ORACLE_LIFT_BOUND, target_stable,
        model_digest, model_digest == EXPECTED_MODEL_DIGEST,
        len(model.state_probabilities), BEAM_WIDTH,
        ACTION_REACH_PER_CONFIGURATION, SEARCH_DEPTH, candidate_counts,
        retained_counts, candidate_digest, trace_digest, selected.actions,
        probabilities, emitted, correct, false,
        correct / emitted if emitted else 0., target_open_count, True,
        False, False, False, len(selected.actions), passed, False,
        ("autonomous finite pose-port tree selects an exact depth-three IQC "
         "continuation" if passed else
         "autonomous finite pose-port tree fails the sealed IQC confirmation"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
