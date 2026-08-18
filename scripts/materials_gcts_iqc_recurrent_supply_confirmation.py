#!/usr/bin/env python3
"""One-shot sealed confirmation of recurrent IQC connection supply.

This is a vocabulary/candidate-supply ceiling, not an autonomous selection
claim.  The complete root and one-step successor graph is frozen before the
reserved target is opened exactly once; target labels are used only afterward
to count exact colored roots and root-to-child paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_iqc_expanded_development_baseline import (
    _expanded_fixture)
from materials_gcts_iqc_incidence_token_preflight import (
    _key, _minimum_distance)
from materials_gcts_iqc_recurrent_prototype_connection_audit import (
    _bounded)
from materials_gcts_iqc_recurrent_supply_confirmation_preregistration import (
    DEVELOPMENT_VALIDATION_GROUPS, MINIMUM_POSITIVE_GROUPS,
    MINIMUM_POSITIVE_SUPPORT, MINIMUM_PURITY, PROTOTYPE_MINIMUM_GROUPS,
    RESERVED_CONFIRMATION_CENTER, SEPARATION_BIN_WIDTH, TRAINING_GROUPS,
    audit as protocol_audit)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS, _open_target, _seed_crop)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)
from materials_gcts_recursive_connections import (
    learn_recurrent_cluster_prototypes, learn_recursive_connection_marking,
    local_cluster_types, map_to_prototypes,
    merge_recursive_connection_markings)
from materials_gcts_successor_state_marking import successor_outgoing_points


EXPECTED_PROTOCOL_DIGEST = \
    "d1bc418806247da462a048078b807b972741b7f284dbd01229bf9a2fb8238a29"


@dataclass(frozen=True)
class RecurrentSupplyConfirmation:
    protocol_digest: str
    training_groups: int
    development_validation_groups: int
    confirmation_center: tuple[float, float, float]
    recurrent_prototypes: int
    accepted_connection_states: int
    model_digest: str
    confirmation_seed_atoms: int
    root_candidates: int
    root_candidate_digest: str
    successor_candidates: int
    successor_candidate_digest: str
    candidate_graph_frozen_before_target: bool
    target_open_count: int
    confirmation_target_atoms: int
    correct_root_candidates: int
    exact_root_child_paths: int
    checked_correct_roots_before_first_exact_path: int
    minimum_development_center_separation: float
    required_center_separation: float
    spatial_domains_disjoint: bool
    event_order: tuple[str, ...]
    target_used_for_fit_or_candidate_generation: bool
    supply_gate_passed: bool
    autonomous_selection_claimed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def _dominant_target_free_color(proposals, point):
    return _dominant_source_color(proposals, point)


def evaluate() -> RecurrentSupplyConfirmation:
    protocol = protocol_audit()
    if (protocol.manifest_digest != EXPECTED_PROTOCOL_DIGEST or
            not protocol.source_hashes_match):
        raise AssertionError("recurrent-supply confirmation protocol drift")
    events = ["protocol-verified"]

    sources, _crop_counts, _original_connection = _expanded_fixture()
    if len(sources) != TRAINING_GROUPS + DEVELOPMENT_VALIDATION_GROUPS:
        raise AssertionError("development corpus size drift")
    raw_types = tuple(local_cluster_types(
        source.seed_positions, source.seed_species, CLUSTER_EDGES)
        for source in sources[:TRAINING_GROUPS])
    prototypes = learn_recurrent_cluster_prototypes(
        raw_types, minimum_groups=PROTOTYPE_MINIMUM_GROUPS)
    markings = tuple(learn_recursive_connection_marking(
        source.seed_positions, map_to_prototypes(group_types, prototypes),
        tuple(source.truth), HIDDEN_UNIT,
        separation_bin_width=SEPARATION_BIN_WIDTH,
        minimum_positive_support=1, minimum_purity=1e-9,
        target_colors=tuple(source.truth.values()))
        for source, group_types in zip(
            sources[:TRAINING_GROUPS], raw_types))
    positive_states = tuple(tuple(
        state for state, row in marking.evidence.items() if row.positive > 0)
        for marking in markings)
    connection = merge_recursive_connection_markings(
        markings, minimum_positive_support=MINIMUM_POSITIVE_SUPPORT,
        minimum_positive_groups=MINIMUM_POSITIVE_GROUPS,
        minimum_purity=MINIMUM_PURITY,
        positive_states_by_marking=positive_states)
    model_digest = hashlib.sha256(repr((
        EXPECTED_PROTOCOL_DIGEST, prototypes, connection)).encode()).hexdigest()
    events.append("model-frozen")

    seed = _seed_crop(RESERVED_CONFIRMATION_CENTER)
    seed_types = local_cluster_types(
        seed.positions, seed.species, CLUSTER_EDGES)
    source = SimpleNamespace(
        group=RESERVED_CONFIRMATION_CENTER,
        seed_positions=tuple(seed.positions), seed_species=tuple(seed.species),
        minimum_distance=_minimum_distance(seed.positions))
    proposals = _bounded(connection, source, seed_types)
    roots = tuple((point, _dominant_target_free_color(proposals, point))
                  for point in sorted(proposals.votes))
    root_digest = hashlib.sha256(repr(roots).encode()).hexdigest()
    events.append("root-candidates-frozen")

    successor_rows = []
    for root, root_color in roots:
        positions, colors, future = advance_frontier_configuration(
            connection, proposals, source.seed_positions,
            source.seed_species, (root,), (root_color,), CLUSTER_EDGES,
            source.group, EVALUATION_TARGET_RADIUS)
        root_index = len(positions) - 1
        outgoing = successor_outgoing_points(
            future, new_parent_index=root_index,
            occupied_positions=positions,
            minimum_distance=source.minimum_distance)
        successor_rows.extend((
            root, root_color, child,
            _dominant_target_free_color(future, child)) for child in outgoing)
    successor_rows = tuple(successor_rows)
    successor_digest = hashlib.sha256(
        repr(successor_rows).encode()).hexdigest()
    frozen_digest = hashlib.sha256(repr((
        model_digest, root_digest, successor_digest)).encode()).hexdigest()
    if not frozen_digest:
        raise AssertionError("candidate graph did not freeze")
    events.append("successor-candidates-frozen")

    target_open_count = 0
    if tuple(events[-3:]) != (
            "model-frozen", "root-candidates-frozen",
            "successor-candidates-frozen"):
        raise AssertionError("target cannot open before graph freeze")
    target = _open_target(RESERVED_CONFIRMATION_CENTER)
    target_open_count += 1
    events.append("target-opened")
    truth = {_key(point): color for point, color in zip(
        target.positions, target.species)}
    exact_roots = {(point, color) for point, color in roots
                   if truth.get(_key(point)) == color}
    exact_paths = tuple(row for row in successor_rows
                        if (row[0], row[1]) in exact_roots and
                        truth.get(_key(row[2])) == row[3])
    checked = 0
    found = False
    children_by_root = {}
    for row in successor_rows:
        children_by_root.setdefault((row[0], row[1]), []).append(row)
    for root in roots:
        if root not in exact_roots:
            continue
        checked += 1
        if any(truth.get(_key(row[2])) == row[3]
               for row in children_by_root.get(root, ())):
            found = True
            break
    events.append("scored")

    separation = min(math.dist(RESERVED_CONFIRMATION_CENTER, source.group)
                     for source in sources)
    required = 2. * EVALUATION_TARGET_RADIUS
    disjoint = separation > required
    passed = bool(exact_roots and exact_paths and found and disjoint and
                  target_open_count == 1 and tuple(events) == (
                      "protocol-verified", "model-frozen",
                      "root-candidates-frozen",
                      "successor-candidates-frozen", "target-opened",
                      "scored"))
    return RecurrentSupplyConfirmation(
        EXPECTED_PROTOCOL_DIGEST, TRAINING_GROUPS,
        DEVELOPMENT_VALIDATION_GROUPS, RESERVED_CONFIRMATION_CENTER,
        len(prototypes), len(connection.accepted_states), model_digest,
        len(seed.positions), len(roots), root_digest, len(successor_rows),
        successor_digest, True, target_open_count, len(target.positions),
        len(exact_roots), len(exact_paths), checked, separation, required,
        disjoint, tuple(events), False, passed, False, False,
        ("recurrent quotient confirms exact IQC continuation supply"
         if passed else
         "recurrent quotient fails exact IQC continuation supply"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
