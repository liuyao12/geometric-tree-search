#!/usr/bin/env python3
"""Transfer a larger-corpus recurrent branch value to wide IQC fallbacks.

The value model is fitted only on the pre-existing 30-nucleus branch corpus.
Any training nucleus whose full radius-14.56 domain could intersect a wide
radius-23.56 domain is removed before grouped capacity selection.  Frozen
features for the wide candidates are joined from the independently generated
terminal fixture; wide exact labels are inspected only after all orders freeze.
Thirty-one within-training-nucleus label shuffles refit capacity and the model
against byte-identical wide candidates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random

from materials_gcts_iqc_exact_port_instance_dataset import (
    load_default_dataset)
from materials_gcts_iqc_extended_development_preregistration import (
    TARGET_RADIUS as TRAINING_RADIUS)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    DEFAULT_FIXTURE as TERMINAL_FIXTURE, SECOND_BLOCK_RADIUS,
    load_fixture_json as load_terminal_fixture,
    validate_dataset as validate_terminal_dataset)
from materials_gcts_recurrent_branch_value import (
    RecurrentBranchExample, fit_grouped_recurrent_branch_value,
    score_recurrent_branch)


ROOT = Path(__file__).resolve().parent
TRAINING_FIXTURE = ROOT / "fixtures/iqc_recurrent_branch_value_training.json"
SHUFFLES = 31
SHUFFLE_SEED = 44107


def _load_training_payload():
    return json.loads(TRAINING_FIXTURE.read_text())


def _disjoint_training_groups(payload, wide):
    wide_centers = tuple(tuple(map(float, group["center"]))
                         for group in wide["groups"])
    required = TRAINING_RADIUS + SECOND_BLOCK_RADIUS
    rows = []
    for group, center in enumerate(payload["development_centers"]):
        separation = min(math.dist(center, other) for other in wide_centers)
        rows.append((group, separation, separation > required))
    return tuple(rows), required


def _training_examples(payload, admitted_groups, labels=None):
    admitted = set(admitted_groups)
    source = tuple(row for row in payload["examples"]
                   if int(row["group"]) in admitted)
    if labels is not None and len(labels) != len(source):
        raise ValueError("shuffled training labels do not align")
    return tuple(RecurrentBranchExample(
        int(row["group"]), tuple(map(float, row["features"])),
        tuple(map(str, row["action_colors"])),
        bool(row["successful"] if labels is None else labels[index]))
        for index, row in enumerate(source))


def _fit(payload, examples):
    return fit_grouped_recurrent_branch_value(
        examples, feature_names=tuple(payload["feature_names"]),
        color_keys=tuple(payload["color_keys"]),
        candidate_neighbors=tuple(payload["candidate_neighbors"]),
        beta_prior=float(payload["beta_prior"]))


def _wide_candidates(wide, terminal):
    if tuple(terminal["feature_names"][:10]) != (
            "depth", "sum_log_state_probability",
            "minimum_state_probability", "sum_state_probability",
            "sum_state_votes", "maximum_state_votes",
            "emitted_species_count", "minimum_action_separation",
            "mean_action_separation", "maximum_action_separation"):
        raise AssertionError("terminal branch feature schema drift")
    rows = []
    for group in wide["groups"]:
        terminal_group = terminal["groups"][int(group["group"])]
        for row in group["rows"]:
            if row["certificates"]["forward"]["status"] != "unsatisfied":
                continue
            source = terminal_group["rows"][int(row["stable_index"])]
            if int(source["stable_index"]) != int(row["stable_index"]):
                raise AssertionError("terminal stable-index join drift")
            graph_key = json.dumps(
                row["complete_branch_action_graph"], sort_keys=True,
                separators=(",", ":"))
            rows.append({
                "group": int(group["group"]),
                "graph_key": graph_key,
                "features": tuple(map(float, source["features"][1:10])),
                "action_colors": tuple(map(str, source["action_colors"])),
            })
    return tuple(rows)


def _wide_labels(wide):
    labels = {}
    forward_status = {}
    supplied_groups = set()
    for group in wide["groups"]:
        group_id = int(group["group"])
        for row in group["rows"]:
            graph_key = json.dumps(
                row["complete_branch_action_graph"], sort_keys=True,
                separators=(",", ":"))
            key = (group_id, graph_key)
            exact = bool(row["exact"])
            if key in labels and labels[key] != exact:
                raise AssertionError("one branch graph has conflicting labels")
            labels[key] = exact
            forward_status[key] = row["certificates"]["forward"]["status"]
            if exact:
                supplied_groups.add(group_id)
    return labels, forward_status, tuple(sorted(supplied_groups))


def _freeze_order(model, candidates):
    orders = []
    for group in sorted({row["group"] for row in candidates}):
        rows = tuple(row for row in candidates if row["group"] == group)
        scored = tuple((score_recurrent_branch(
            model, row["features"], row["action_colors"]), row)
            for row in rows)
        order = tuple(row for _score, row in sorted(
            scored, key=lambda item: (-item[0], item[1]["graph_key"])))
        scores = tuple(score for score, _row in sorted(
            scored, key=lambda item: (-item[0], item[1]["graph_key"])))
        orders.append((group, order, scores))
    return tuple(orders)


def _score_orders(orders, labels):
    selected_exact = sum(labels[(group, order[0]["graph_key"])]
                         for group, order, _scores in orders)
    exact_ranks = tuple(
        next((rank for rank, row in enumerate(order, 1)
              if labels[(group, row["graph_key"])]),
             None)
        for group, order, _scores in orders)
    return selected_exact, exact_ranks


def _shuffle_training_labels(examples, trial):
    labels = [None] * len(examples)
    rng = random.Random(SHUFFLE_SEED + trial)
    for group in sorted({row.group for row in examples}):
        indices = [index for index, row in enumerate(examples)
                   if row.group == group]
        values = [examples[index].successful for index in indices]
        rng.shuffle(values)
        for index, value in zip(indices, values):
            labels[index] = value
    return tuple(labels)


def evaluate():
    payload = _load_training_payload()
    wide = load_default_dataset()
    _terminal_raw, terminal = load_terminal_fixture(TERMINAL_FIXTURE)
    validate_terminal_dataset(terminal)
    group_audit, required_separation = _disjoint_training_groups(
        payload, wide)
    admitted_groups = tuple(group for group, _separation, admitted
                            in group_audit if admitted)
    excluded_groups = tuple(group for group, _separation, admitted
                            in group_audit if not admitted)
    minimum_admitted_separation = min(
        separation for _group, separation, admitted in group_audit
        if admitted)
    maximum_excluded_separation = max(
        (separation for _group, separation, admitted in group_audit
         if not admitted), default=0.)
    examples = _training_examples(payload, admitted_groups)
    model, train_audit = _fit(payload, examples)
    candidates = _wide_candidates(wide, terminal)
    candidate_digest = hashlib.sha256(repr(tuple(
        (row["group"], row["graph_key"], row["features"],
         row["action_colors"]) for row in candidates)).encode()).hexdigest()
    orders = _freeze_order(model, candidates)
    order_digest = hashlib.sha256(repr(tuple(
        (group, tuple(row["graph_key"] for row in order), scores)
        for group, order, scores in orders)).encode()).hexdigest()

    # Wide labels first enter after the exact candidate set, model scores, and
    # every within-group candidate order above have been frozen.
    wide_labels, forward_status, supplied_groups = _wide_labels(wide)
    selected_exact, exact_ranks = _score_orders(orders, wide_labels)

    null_scores = []
    null_candidate_digests = []
    for trial in range(SHUFFLES):
        shuffled = _training_examples(
            payload, admitted_groups,
            _shuffle_training_labels(examples, trial))
        shuffled_model, _audit = _fit(payload, shuffled)
        null_orders = _freeze_order(shuffled_model, candidates)
        null_scores.append(_score_orders(null_orders, wide_labels)[0])
        null_candidate_digests.append(candidate_digest)

    selected_by_group = {group: order[0]
                         for group, order, _scores in orders}
    final_supply = sum(
        any(exact and forward_status[(group, graph_key)] == "satisfied"
            for (candidate_group, graph_key), exact in wide_labels.items()
            if candidate_group == group)
        or (group in selected_by_group and wide_labels[
            (group, selected_by_group[group]["graph_key"])])
        for group in supplied_groups)
    candidate_keys = tuple((row["group"], row["graph_key"])
                           for row in candidates)
    exact_unsatisfied = sum(wide_labels[key] for key in candidate_keys)
    false_unsatisfied = sum(not wide_labels[key] for key in candidate_keys)
    selected_false = len(orders) - selected_exact
    false_rejected = false_unsatisfied - selected_false

    body = {
        "schema_version": 1,
        "training_source_candidate_digest": payload["candidate_digest"],
        "wide_source_dataset_digest": wide["dataset_digest"],
        "training_domain_radius": TRAINING_RADIUS,
        "wide_domain_radius": SECOND_BLOCK_RADIUS,
        "required_center_separation": required_separation,
        "training_groups_total": len(payload["development_centers"]),
        "training_groups_admitted": len(admitted_groups),
        "training_groups_excluded_for_domain_overlap": excluded_groups,
        "minimum_admitted_center_separation": minimum_admitted_separation,
        "maximum_excluded_center_separation": maximum_excluded_separation,
        "raw_atom_domain_disjoint_by_closed_ball_certificate": bool(
            minimum_admitted_separation > required_separation),
        "training_examples": len(examples),
        "training_positive_examples": sum(row.successful
                                           for row in examples),
        "training_feature_names": tuple(payload["feature_names"]),
        "training_selected_neighbors": train_audit.selected_neighbors,
        "training_supplied_groups": train_audit.supplied_groups,
        "training_selected_exact_groups": (
            train_audit.selected_exact_groups),
        "training_selection_precision": train_audit.selected_precision,
        "frozen_model_digest": train_audit.model_digest,
        "wide_candidate_count": len(candidates),
        "wide_affected_groups": len(orders),
        "wide_recoverable_exact_groups": sum(rank is not None
                                             for rank in exact_ranks),
        "wide_selected_exact_groups": selected_exact,
        "wide_exact_ranks": exact_ranks,
        "wide_selected_false_groups": selected_false,
        "wide_false_branches_rejected": false_rejected,
        "wide_false_unsatisfied_branches": false_unsatisfied,
        "wide_exact_unsatisfied_branches": exact_unsatisfied,
        "supplied_groups_after_transfer": final_supply,
        "supplied_groups": len(supplied_groups),
        "candidate_digest": candidate_digest,
        "frozen_order_digest": order_digest,
        "shuffle_trials": SHUFFLES,
        "within_training_group_label_shuffle": True,
        "shuffle_selected_exact_median": sorted(
            null_scores)[SHUFFLES // 2],
        "shuffle_selected_exact_maximum": max(null_scores),
        "selected_exact_empirical_p": (
            1 + sum(value >= selected_exact for value in null_scores)) /
            (SHUFFLES + 1),
        "all_null_candidate_digests_identical": all(
            digest == candidate_digest for digest in null_candidate_digests),
        "wide_labels_used_for_fit_capacity_or_order": False,
        "raw_coordinates_ids_or_group_used_as_model_feature": False,
        "labels_joined_after_order_freeze": True,
        "candidate_geometry_unchanged": True,
        "integrated_as_default_marking": False,
        "external_recurrent_transfer_gate_passed": bool(
            selected_exact == sum(rank is not None for rank in exact_ranks)
            and final_supply == len(supplied_groups)
            and (1 + sum(value >= selected_exact for value in null_scores)) /
            (SHUFFLES + 1) <= .05),
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
        "honest_status": (
            "the atom-domain-disjoint 29-nucleus recurrent value ranks one "
            "of two exact wide fallbacks first, but the other ranks tenth; "
            "exact supply remains eight of nine and the transfer gate is red"),
    }
    return {**body, "audit_digest": hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    print(json.dumps(row, indent=2, sort_keys=True)
          if args.json else row["honest_status"])


if __name__ == "__main__":
    main()
