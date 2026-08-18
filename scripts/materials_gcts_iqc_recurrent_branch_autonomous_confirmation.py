#!/usr/bin/env python3
"""Execute the preregistered recurrent-branch IQC confirmation once.

The candidate tree, finite pose/port marking, recurrent branch value, selected
terminal branch, and trace hashes are immutable before ``_open_target_once``
is called.  The target is accepted only by the final pure scorer.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import _dominant_source_color
from materials_gcts_iqc_expanded_development_baseline import _expanded_fixture
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_pose_port_state_audit import _descriptors, _program
from materials_gcts_iqc_recurrent_branch_autonomous_preregistration import (
    ACTION_REACH_PER_CONFIGURATION, BEAM_WIDTH, BRANCH_NEIGHBORS,
    CONFIRMATION_CENTER, ORACLE_LIFT_BOUND, SEARCH_DEPTH, SEED_RADIUS,
    TARGET_RADIUS, UPSTREAM_ANGULAR_BIN_WIDTH,
    audit as preregistration_audit)
from materials_gcts_iqc_recurrent_branch_value_audit import (
    EXPECTED_MODEL_DIGEST as EXPECTED_BRANCH_MODEL_DIGEST,
    _load as load_branch_training)
from materials_gcts_iqc_recurrent_prototype_connection_audit import _bounded
from materials_gcts_iqc_spatial_beam_transfer_benchmark import CLUSTER_EDGES, _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_persistent_frontier_beam import advance_frontier_configuration
from materials_gcts_pose_port_state_marking import score_pose_port_state
from materials_gcts_pose_port_state_serialization import (
    pose_port_state_marking_from_payload)
from materials_gcts_recurrent_branch_value import (
    fit_grouped_recurrent_branch_value, recurrent_branch_value_digest,
    score_recurrent_branch)
from materials_gcts_recursive_connections import local_cluster_types


EXPECTED_PREREGISTRATION_DIGEST = \
    "6099d968bb0cef9cd73d3ea2dc17e117471b4daffd021f03e05e469ebf3b936e"
STATE_MODEL_FIXTURE = Path(__file__).resolve().parent / \
    "fixtures/iqc_recurrent_pose_port_state_model.json.bz2"
EXPECTED_STATE_FIXTURE_SHA256 = \
    "0048b66abccc7789ffd6767fe94d5c5b4b40550af3d4c6bd4064eeea9ae9354c"
EXPECTED_STATE_PAYLOAD_SHA256 = \
    "51a05fb88ee5691a8bf9c2b693329ebd30e046144bfeb826fc457342ce085c11"
EXPECTED_STATE_RUNTIME_DIGEST = \
    "ebeeac4a317044526e22b49e11a7b8977e888bc852a9a520cdb6ae7d3bda324e"
BRANCH_FEATURE_NAMES = (
    "sum_log_state_probability", "minimum_state_probability",
    "sum_state_probability", "sum_state_votes", "maximum_state_votes",
    "emitted_species_count", "minimum_action_separation",
    "mean_action_separation", "maximum_action_separation")


@dataclass(frozen=True)
class FrozenActionCandidate:
    depth: int
    parent_actions: tuple[tuple[tuple[float, float, float], str], ...]
    point: tuple[float, float, float]
    species: str
    state_probability: float
    vote_count: int


@dataclass(frozen=True)
class FrozenTerminalBranch:
    actions: tuple[tuple[tuple[float, float, float], str], ...]
    action_probabilities: tuple[float, ...]
    action_votes: tuple[int, ...]
    features: tuple[float, ...]
    branch_value: float


@dataclass(frozen=True)
class _SearchState:
    positions: tuple[tuple[float, float, float], ...]
    species: tuple[str, ...]
    proposals: object
    actions: tuple[tuple[tuple[float, float, float], str], ...]
    probabilities: tuple[float, ...]
    votes: tuple[int, ...]
    cumulative_log_probability: float


@dataclass(frozen=True)
class FrozenConfirmationExecution:
    seed_atoms: int
    state_runtime_digest: str
    branch_model_digest: str
    candidate_counts_by_depth: tuple[int, ...]
    retained_configurations_by_depth: tuple[int, ...]
    candidate_digest: str
    terminal_digest: str
    trace_digest: str
    terminals: tuple[FrozenTerminalBranch, ...]
    selected_terminal: int


@dataclass(frozen=True)
class IQCRecurrentBranchAutonomousConfirmation:
    preregistration_digest: str
    confirmation_center: tuple[float, float, float]
    seed_radius: float
    target_radius: float
    seed_atoms: int
    target_atoms: int
    oracle_lift_bound: int
    target_bound_plus_one_stable: bool
    state_model_fixture_sha256: str
    state_runtime_model_digest: str
    branch_model_digest: str
    branch_neighbors: int
    frozen_recurrent_states: int
    beam_width: int
    action_reach_per_configuration: int
    search_depth: int
    candidate_counts_by_depth: tuple[int, ...]
    retained_configurations_by_depth: tuple[int, ...]
    terminal_configurations: int
    exact_terminal_configurations: int
    selected_terminal_index: int
    selected_branch_value: float
    first_exact_recurrent_rank: int | None
    candidate_digest: str
    terminal_digest: str
    trace_digest_before_target_open: str
    selected_actions: tuple[tuple[tuple[float, float, float], str], ...]
    selected_action_probabilities: tuple[float, ...]
    emitted_sites: int
    correct_sites: int
    false_sites: int
    precision: float
    target_open_count: int
    target_materialized_after_execution: bool
    target_used_for_state_or_branch_fit: bool
    target_used_for_candidate_or_feature_generation: bool
    target_used_for_ranking_or_execution: bool
    exact_candidate_geometry_changed: bool
    self_fed_depth: int
    autonomous_top1_gate_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _load_state_model():
    compressed = STATE_MODEL_FIXTURE.read_bytes()
    if hashlib.sha256(compressed).hexdigest() != EXPECTED_STATE_FIXTURE_SHA256:
        raise AssertionError("frozen pose-port state fixture drift")
    raw = bz2.decompress(compressed)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_STATE_PAYLOAD_SHA256:
        raise AssertionError("frozen pose-port state payload drift")
    payload = json.loads(raw)
    runtime_digest = payload.pop("runtime_model_digest")
    if hashlib.sha256(_canonical_json(payload)).hexdigest() != runtime_digest:
        raise AssertionError("frozen pose-port runtime digest drift")
    if runtime_digest != EXPECTED_STATE_RUNTIME_DIGEST:
        raise AssertionError("unexpected frozen pose-port runtime model")
    if payload.pop("training_groups") != 30 or \
            payload.pop("training_candidates") != 63811:
        raise AssertionError("frozen pose-port training-accounting drift")
    model = pose_port_state_marking_from_payload(payload)
    if model.token_marking.token_evidence or model.state_evidence:
        raise AssertionError("runtime marking contains unnecessary labels")
    return model, runtime_digest


def _load_branch_model():
    payload, examples = load_branch_training()
    if tuple(payload["feature_names"]) != BRANCH_FEATURE_NAMES:
        raise AssertionError("branch feature schema drift")
    model, audit = fit_grouped_recurrent_branch_value(
        examples, feature_names=BRANCH_FEATURE_NAMES,
        color_keys=tuple(payload["color_keys"]),
        candidate_neighbors=tuple(payload["candidate_neighbors"]),
        beta_prior=float(payload["beta_prior"]))
    if audit.selected_neighbors != BRANCH_NEIGHBORS or \
            recurrent_branch_value_digest(model) != EXPECTED_BRANCH_MODEL_DIGEST:
        raise AssertionError("frozen recurrent branch model drift")
    return model


def _configuration_key(actions):
    return tuple(sorted(actions))


def _branch_features(actions, probabilities, votes):
    if len(actions) != SEARCH_DEPTH or len(probabilities) != len(actions) or \
            len(votes) != len(actions):
        raise ValueError("incomplete terminal branch")
    distances = tuple(math.dist(actions[left][0], actions[right][0])
                      for left in range(len(actions))
                      for right in range(left + 1, len(actions)))
    return (
        sum(math.log(max(value, 1e-15)) for value in probabilities),
        min(probabilities), sum(probabilities), float(sum(votes)),
        float(max(votes)), float(len({color for _point, color in actions})),
        min(distances), sum(distances) / len(distances), max(distances))


def _seed_crop_at_frozen_bound():
    physical_radius = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + SEED_RADIUS)
    oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND, physical_radius)
    return _crop(oracle, CONFIRMATION_CENTER, SEED_RADIUS,
                 "IQC-recurrent-branch-autonomous-seed")


def _open_target_once():
    physical_radius = math.ceil(math.dist(
        (0., 0., 0.), CONFIRMATION_CENTER) + TARGET_RADIUS)
    oracle, _ = oracle_patch_fast(ORACLE_LIFT_BOUND, physical_radius)
    check, _ = oracle_patch_fast(ORACLE_LIFT_BOUND + 1, physical_radius)
    target = _crop(oracle, CONFIRMATION_CENTER, TARGET_RADIUS,
                   "IQC-recurrent-branch-autonomous-target")
    target_check = _crop(check, CONFIRMATION_CENTER, TARGET_RADIUS,
                         "IQC-recurrent-branch-autonomous-target-check")
    stable = (tuple(target.positions), tuple(target.species)) == (
        tuple(target_check.positions), tuple(target_check.species))
    if not stable:
        raise AssertionError("confirmation crop changes at bound plus one")
    return target, stable


def _execute_target_blind(state_model, branch_model, connection, seed):
    source = SimpleNamespace(
        group=CONFIRMATION_CENTER,
        seed_positions=tuple(seed.positions), seed_species=tuple(seed.species))
    proposals = _bounded(connection, source, local_cluster_types(
        source.seed_positions, source.seed_species, CLUSTER_EDGES))
    states = (_SearchState(
        source.seed_positions, source.seed_species, proposals, (), (), (), 0.),)
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
                -score_pose_port_state(state_model, descriptors[point]),
                -state.proposals.votes[point], point)))[
                    :ACTION_REACH_PER_CONFIGURATION]
            for point in ordered:
                color = str(_dominant_source_color(state.proposals, point))
                probability = score_pose_port_state(
                    state_model, descriptors[point])
                vote = int(state.proposals.votes[point])
                action = (tuple(point), color)
                depth_rows.append(FrozenActionCandidate(
                    depth, _configuration_key(state.actions), tuple(point),
                    color, probability, vote))
                positions, species, future = advance_frontier_configuration(
                    connection, state.proposals, state.positions,
                    state.species, (point,), (color,), CLUSTER_EDGES,
                    CONFIRMATION_CENTER, TARGET_RADIUS)
                actions = state.actions + (action,)
                cumulative = state.cumulative_log_probability + math.log(
                    max(probability, 1e-15))
                child = _SearchState(
                    positions, species, future, actions,
                    state.probabilities + (probability,),
                    state.votes + (vote,), cumulative)
                key = _configuration_key(actions)
                prior = children.get(key)
                if prior is None or (cumulative, actions) > (
                        prior.cumulative_log_probability, prior.actions):
                    children[key] = child
        snapshots.append(tuple(sorted(depth_rows, key=repr)))
        candidate_counts.append(len(depth_rows))
        states = tuple(sorted(children.values(), key=lambda state: (
            -state.cumulative_log_probability,
            _configuration_key(state.actions)))[:BEAM_WIDTH])
        retained_counts.append(len(states))
        if not states:
            break
    terminals = []
    for state in states:
        features = _branch_features(
            state.actions, state.probabilities, state.votes)
        value = score_recurrent_branch(
            branch_model, features,
            tuple(color for _point, color in state.actions))
        terminals.append(FrozenTerminalBranch(
            state.actions, state.probabilities, state.votes, features, value))
    terminals = tuple(sorted(terminals, key=lambda row: (
        -row.branch_value, row.features,
        tuple(color for _point, color in row.actions), row.actions)))
    if not terminals:
        raise AssertionError("frozen autonomous search produced no terminal")
    candidate_digest = hashlib.sha256(repr(tuple(snapshots)).encode()).hexdigest()
    terminal_digest = hashlib.sha256(repr(terminals).encode()).hexdigest()
    trace = (
        candidate_digest, terminal_digest, tuple(candidate_counts),
        tuple(retained_counts), terminals[0].actions, terminals[0].branch_value)
    trace_digest = hashlib.sha256(repr(trace).encode()).hexdigest()
    return tuple(candidate_counts), tuple(retained_counts), candidate_digest, \
        terminal_digest, trace_digest, terminals


def prepare_target_blind_execution() -> FrozenConfirmationExecution:
    """Freeze the complete selected execution without opening the target."""
    protocol = preregistration_audit()
    if protocol.manifest_digest != EXPECTED_PREREGISTRATION_DIGEST or \
            not protocol.source_hashes_match or not protocol.domains_disjoint:
        raise AssertionError("recurrent branch preregistration drift")
    state_model, state_digest = _load_state_model()
    branch_model = _load_branch_model()
    sources, _counts, _connection = _expanded_fixture()
    _prototypes, connection = _program(sources)
    seed = _seed_crop_at_frozen_bound()
    if not seed.positions:
        raise AssertionError("frozen confirmation seed is empty")
    (candidate_counts, retained_counts, candidate_digest, terminal_digest,
     trace_digest, terminals) = _execute_target_blind(
        state_model, branch_model, connection, seed)
    return FrozenConfirmationExecution(
        len(seed.positions), state_digest,
        recurrent_branch_value_digest(branch_model), candidate_counts,
        retained_counts, candidate_digest, terminal_digest, trace_digest,
        terminals, 0)


def evaluate() -> IQCRecurrentBranchAutonomousConfirmation:
    frozen = prepare_target_blind_execution()
    immutable_before_target = frozen
    target_open_count = 0
    target, target_stable = _open_target_once()
    target_open_count += 1
    truth = {_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    exact = tuple(all(truth.get(_key(point)) == color
                      for point, color in row.actions)
                  for row in frozen.terminals)
    selected = frozen.terminals[frozen.selected_terminal]
    selected_correct = sum(truth.get(_key(point)) == color
                           for point, color in selected.actions)
    if frozen != immutable_before_target:
        raise AssertionError("frozen execution mutated after target open")
    emitted = len(selected.actions)
    false = emitted - selected_correct
    first_exact = next((rank for rank, value in enumerate(exact, 1) if value),
                       None)
    passed = bool(
        target_stable and target_open_count == 1 and
        emitted == SEARCH_DEPTH and selected_correct == emitted and false == 0)
    return IQCRecurrentBranchAutonomousConfirmation(
        EXPECTED_PREREGISTRATION_DIGEST, CONFIRMATION_CENTER, SEED_RADIUS,
        TARGET_RADIUS, frozen.seed_atoms, len(target.positions),
        ORACLE_LIFT_BOUND, target_stable, EXPECTED_STATE_FIXTURE_SHA256,
        frozen.state_runtime_digest, frozen.branch_model_digest,
        BRANCH_NEIGHBORS, 876, BEAM_WIDTH, ACTION_REACH_PER_CONFIGURATION,
        SEARCH_DEPTH, frozen.candidate_counts_by_depth,
        frozen.retained_configurations_by_depth, len(frozen.terminals),
        sum(exact), frozen.selected_terminal, selected.branch_value,
        first_exact, frozen.candidate_digest, frozen.terminal_digest,
        frozen.trace_digest, selected.actions, selected.action_probabilities,
        emitted, selected_correct, false,
        selected_correct / emitted if emitted else 0., target_open_count,
        True, False, False, False, False, len(selected.actions), passed, False,
        ("recurrent branch value selects an exact target-blind depth-three "
         "IQC continuation" if passed else
         "recurrent branch value fails the sealed autonomous IQC confirmation"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
