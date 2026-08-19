#!/usr/bin/env python3
"""Build a grouped post-self-feed IQC terminal-value development corpus.

All ten nuclei and their targets were consumed by earlier development audits.
For each nucleus this builder chooses one exact first-block terminal, uses its
complete colored state as a new seed, and enumerates a second complete block.
Features are target-free invariant summaries of the accepted actions and the
remaining frozen-port frontier.  Targets enter only after every state and
feature row for that nucleus is immutable, to attach development labels.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, ORACLE_LIFT_BOUND, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import (
    UPSTREAM_ANGULAR_BIN_WIDTH)
from materials_gcts_iqc_self_fed_complete_frontier_execution import (
    _complete_states_at_radius)
from materials_gcts_iqc_frozen_fusion_runtime import (
    COLORS, FEATURE_NAMES as FUSION_FEATURE_NAMES, _local_section, _partial,
    action_key, branch_features, load_default_runtime)
from materials_gcts_partial_irregular_port_graph import (
    PartialIncidenceEdge, PartialIrregularPortGraph, PartialPortEdge,
    PartialPortNode)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_pose_port_state_marking import score_pose_port_state


SECOND_BLOCK_RADIUS = TARGET_RADIUS + SEED_RADIUS
OUTER_ORACLE_LIFT_BOUND = 72
SUCCESSOR_FEATURE_NAMES = (
    "minimum_action_probability", "mean_action_probability",
    "minimum_action_votes", "mean_action_votes",
    "mean_action_pair_separation_over_seed_radius",
    "log_successor_count", "mean_successor_votes", "maximum_successor_votes",
    "fraction_successor_votes_ge_2", "fraction_successor_votes_ge_3",
    "mean_successor_probability", "maximum_successor_probability",
    "fraction_successor_probability_ge_half", "successor_color_entropy",
    "mean_successor_radius_fraction", "outward_successor_fraction",
)
FEATURE_NAMES = FUSION_FEATURE_NAMES + SUCCESSOR_FEATURE_NAMES
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_self_fed_terminal_dataset_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "6e9f58fcc78b46de8331e80b7bdcddc82ac7133026d349666de828930cfbd494"
EXPECTED_DATASET_DIGEST = \
    "577142be55c9cf164fedfc0f0b7c8d111b1777725b3836a84435de454b66c3c3"


@dataclass(frozen=True)
class SelfFedTerminalRow:
    group: int
    stable_index: int
    features: tuple[float, ...]
    action_colors: tuple[str, ...]
    graph: dict
    exact: bool
    correct_sites: int


@dataclass(frozen=True)
class SelfFedTerminalGroup:
    group: int
    center: tuple[float, float, float]
    seed_atoms: int
    inherited_state_atoms: int
    first_block_terminals: int
    exact_first_block_terminals: int
    inherited_action_digest: str
    second_block_counts: tuple[int, ...]
    second_block_terminals: int
    exact_second_block_terminals: int
    feature_digest: str
    target_used_for_state_or_features: bool
    rows: tuple[SelfFedTerminalRow, ...]


def _entropy(values):
    counts = {value: values.count(value) for value in set(values)}
    total = len(values)
    return -sum((count / total) * math.log(count / total)
                for count in counts.values()) if total else 0.


def terminal_successor_features(state, state_model, center, public_radius):
    descriptors = _descriptors(
        state.positions, state.species, state.proposals,
        UPSTREAM_ANGULAR_BIN_WIDTH)
    points = tuple(sorted(state.proposals.votes))
    votes = tuple(float(state.proposals.votes[point]) for point in points)
    probabilities = tuple(score_pose_port_state(
        state_model, descriptors[point]) for point in points)
    colors = tuple(str(_dominant_source_color(state.proposals, point))
                   for point in points)
    action_probabilities = tuple(map(float, state.probabilities))
    action_votes = tuple(map(float, state.votes))
    pair_distances = tuple(math.dist(first[0], second[0])
                           for index, first in enumerate(state.actions)
                           for second in state.actions[index + 1:])
    action_radius = max((math.dist(point, center)
                         for point, _color in state.actions), default=0.)
    successor_radii = tuple(math.dist(point, center) for point in points)
    count = max(1, len(points))
    return (
        min(action_probabilities, default=0.),
        sum(action_probabilities) / max(1, len(action_probabilities)),
        min(action_votes, default=0.),
        sum(action_votes) / max(1, len(action_votes)),
        (sum(pair_distances) / max(1, len(pair_distances))) / SEED_RADIUS,
        math.log1p(len(points)),
        sum(votes) / count,
        max(votes, default=0.),
        sum(value >= 2. for value in votes) / count,
        sum(value >= 3. for value in votes) / count,
        sum(probabilities) / count,
        max(probabilities, default=0.),
        sum(value >= .5 for value in probabilities) / count,
        _entropy(colors),
        (sum(successor_radii) / count) / public_radius,
        sum(radius > action_radius + 1e-8
            for radius in successor_radii) / count,
    )


def graph_from_json(row):
    def species(value):
        return tuple(value)

    def node(value):
        return PartialPortNode(
            int(value["support_type_id"]), species(value["action_species"]),
            int(value["matched_atoms"]), int(value["prototype_atoms"]),
            int(value["training_group_support"]))

    nodes = tuple(node(value) for value in row["nodes"])
    edges = tuple(PartialPortEdge(
        tuple(node(value) for value in edge["endpoint_types"]),
        tuple((species(key), int(count))
              for key, count in edge["shared_species"]),
        int(edge["separation_bin"]),
        tuple((species(key), tuple(map(int, pair)))
              for key, pair in edge["shared_distance_profiles"]),
        int(edge["chirality"])) for edge in row["edges"])
    incidence = tuple(PartialIncidenceEdge(
        int(edge["left_index"]), int(edge["right_index"]),
        tuple((species(key), int(count))
              for key, count in edge["shared_species"]),
        int(edge["separation_bin"]),
        tuple((species(key), tuple(map(int, pair)))
              for key, pair in edge["shared_distance_profiles"]),
        int(edge["chirality"]), bool(edge["connection_witnessed"]))
        for edge in row["incidence_edges"])
    return PartialIrregularPortGraph(
        nodes, edges, int(row["isolated_nodes"]), str(row["canonical_digest"]),
        bool(row["proper_se3_invariant"]),
        bool(row["lattice_coordinates_used"]), bool(row["target_used"]),
        incidence)


def _evaluate_group(payload):
    group, center, seed_positions, seed_species, first_truth, outer_truth = payload
    runtime = load_default_runtime()
    source = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    first_states, _first_counts = _complete_states_at_radius(
        source, runtime, TARGET_RADIUS)
    first_states = tuple(sorted(first_states,
                                key=lambda state: action_key(state.actions)))
    first_exact = tuple(state for state in first_states if all(
        first_truth.get(_key(point)) == color
        for point, color in state.actions))
    if not first_exact:
        raise AssertionError(f"development group {group} lacks exact first block")
    inherited = first_exact[0]
    inherited_key = action_key(inherited.actions)
    inherited_digest = hashlib.sha256(repr(inherited_key).encode()).hexdigest()
    second_source = SimpleNamespace(
        group=tuple(center), seed_positions=inherited.positions,
        seed_species=inherited.species)
    second_states, counts = _complete_states_at_radius(
        second_source, runtime, SECOND_BLOCK_RADIUS)
    second_states = tuple(sorted(second_states,
                                 key=lambda state: action_key(state.actions)))
    frozen_rows = []
    for stable_index, state in enumerate(second_states):
        partial, graph = _partial(
            second_source, state, runtime["grouped_vocabulary"])
        scalar = tuple(branch_features(state)) + _local_section(state) + partial
        successor = terminal_successor_features(
            state, runtime["state_model"], center, SECOND_BLOCK_RADIUS)
        if len(scalar) != len(FUSION_FEATURE_NAMES):
            raise AssertionError("post-self-feed scalar feature schema drift")
        frozen_rows.append((
            stable_index, scalar + successor,
            tuple(color for _point, color in state.actions), asdict(graph),
            action_key(state.actions)))
    frozen = tuple(frozen_rows)
    feature_digest = hashlib.sha256(repr(frozen).encode()).hexdigest()
    rows = tuple(SelfFedTerminalRow(
        group, stable_index, features, action_colors, graph,
        all(outer_truth.get(_key(point)) == color for point, color in actions),
        sum(outer_truth.get(_key(point)) == color for point, color in actions))
        for stable_index, features, action_colors, graph, actions in frozen)
    return SelfFedTerminalGroup(
        group, tuple(center), len(seed_positions), len(inherited.positions),
        len(first_states), len(first_exact), inherited_digest, counts,
        len(second_states), sum(row.exact for row in rows), feature_digest,
        False, rows)


def build_dataset(*, workers=1):
    physical = math.ceil(max(math.dist((0., 0., 0.), center)
                             for center in DEVELOPMENT_CENTERS)
                         + SECOND_BLOCK_RADIUS)
    oracle, _ = oracle_patch_fast(OUTER_ORACLE_LIFT_BOUND, physical)
    seeds = tuple(_crop(oracle, center, SEED_RADIUS,
                        "IQC-self-fed-value-seed")
                  for center in DEVELOPMENT_CENTERS)
    first_targets = tuple(_crop(oracle, center, TARGET_RADIUS,
                                "IQC-self-fed-value-first-target")
                          for center in DEVELOPMENT_CENTERS)
    outer_targets = tuple(_crop(oracle, center, SECOND_BLOCK_RADIUS,
                                "IQC-self-fed-value-outer-target")
                          for center in DEVELOPMENT_CENTERS)
    payloads = []
    for group, (center, seed, first, outer) in enumerate(zip(
            DEVELOPMENT_CENTERS, seeds, first_targets, outer_targets)):
        first_truth = {_key(point): str(color) for point, color in
                       zip(first.positions, first.species)}
        outer_truth = {_key(point): str(color) for point, color in
                       zip(outer.positions, outer.species)}
        payloads.append((group, center, tuple(seed.positions),
                         tuple(seed.species), first_truth, outer_truth))
    if workers == 1:
        groups = tuple(_evaluate_group(payload) for payload in payloads)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            groups = tuple(pool.map(_evaluate_group, payloads))
    body = {
        "schema_version": 1,
        "development_groups": len(groups),
        "feature_names": FEATURE_NAMES,
        "seed_radius": SEED_RADIUS,
        "first_block_radius": TARGET_RADIUS,
        "second_block_radius": SECOND_BLOCK_RADIUS,
        "outer_oracle_lift_bound": OUTER_ORACLE_LIFT_BOUND,
        "groups": [asdict(group) for group in groups],
        "target_used_for_state_or_features": False,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
    }
    digest = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {**body, "dataset_digest": digest}


def load_fixture_json(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    return raw, json.loads(gzip.decompress(raw))


def validate_dataset(row):
    body = dict(row)
    digest = body.pop("dataset_digest")
    if (hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            != digest or body["schema_version"] != 1
            or body["development_groups"] != len(DEVELOPMENT_CENTERS)
            or tuple(body["feature_names"]) != FEATURE_NAMES
            or body["target_used_for_state_or_features"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]):
        raise AssertionError("self-fed terminal dataset drift")
    for group, item in enumerate(body["groups"]):
        if (item["group"] != group or not item["rows"]
                or item["target_used_for_state_or_features"]
                or item["second_block_terminals"] != len(item["rows"])
                or item["exact_second_block_terminals"] !=
                   sum(row["exact"] for row in item["rows"])
                or any(len(row["features"]) != len(FEATURE_NAMES)
                       or len(row["action_colors"]) != 3
                       or graph_from_json(row["graph"]).target_used
                       for row in item["rows"])):
            raise AssertionError("invalid grouped self-fed terminal corpus")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.workers <= 0:
        raise SystemExit("--workers must be positive")
    row = build_dataset(workers=args.workers)
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
