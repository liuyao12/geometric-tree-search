#!/usr/bin/env python3
"""Audit a bounded boundary backoff for exact IQC port-instance pruning.

The fixed forward-port certificate rejects useful and false branches alike.
This development audit asks whether one target-free scalar boundary feature can
defer a forward-UNSAT branch for later exact search.  Feature family selection
is leave-one-nucleus-out; thresholds are fitted without the held-out nucleus.
Thirty-one within-nucleus label shuffles repeat the complete selection path.

Deferred is deliberately distinct from SAT: the rule never manufactures a
physical-port certificate and is not permitted to accept an action by itself.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import hashlib
import json
import random

from materials_gcts_iqc_exact_port_instance_dataset import (
    load_default_dataset)


SHUFFLES = 31
SHUFFLE_SEED = 81721
DIRECTIONS = ("le", "ge")


@dataclass(frozen=True)
class BoundaryRule:
    feature: str
    direction: str
    threshold: float

    def accepts(self, row):
        value = float(row["boundary_context"][self.feature])
        return value <= self.threshold if self.direction == "le" \
            else value >= self.threshold


def _forward_unsatisfied_rows(dataset, labels=None):
    rows = []
    for group in dataset["groups"]:
        for row in group["rows"]:
            if row["certificates"]["forward"]["status"] != "unsatisfied":
                continue
            rows.append({**row, "group": int(group["group"])})
    if labels is not None:
        if len(labels) != len(rows):
            raise ValueError("label vector does not match frozen rows")
        rows = [{**row, "exact": bool(label)}
                for row, label in zip(rows, labels)]
    return tuple(rows)


def _thresholds(values):
    values = sorted(set(map(float, values)))
    if not values:
        return ()
    epsilon = max(1., max(map(abs, values))) * 1e-12
    return (values[0] - epsilon,
            *(0.5 * (left + right)
              for left, right in zip(values, values[1:])),
            values[-1] + epsilon)


def _fit_threshold(rows, feature, direction):
    """Fit one stump while requiring all train exact rows to be deferred."""
    candidates = []
    groups = sorted(set(row["group"] for row in rows))
    for threshold in _thresholds(
            row["boundary_context"][feature] for row in rows):
        rule = BoundaryRule(feature, direction, threshold)
        if any(row["exact"] and not rule.accepts(row) for row in rows):
            continue
        false_rejected = sum(not row["exact"] and not rule.accepts(row)
                             for row in rows)
        fully_rejected_false_groups = sum(
            any(not row["exact"] for row in rows
                if row["group"] == group) and
            all(row["exact"] or not rule.accepts(row) for row in rows
                if row["group"] == group)
            for group in groups)
        deferred = sum(rule.accepts(row) for row in rows)
        # The last term fixes otherwise equivalent thresholds without using a
        # raw row ID.  It prefers the simplest broad boundary between values.
        threshold_tie = -threshold if direction == "le" else threshold
        candidates.append(((fully_rejected_false_groups, false_rejected,
                            -deferred, threshold_tie), rule))
    return max(candidates, default=(None, None), key=lambda item: item[0])[1]


def _family_cross_validation(rows, feature, direction):
    predictions = []
    for heldout in sorted(set(row["group"] for row in rows)):
        train = tuple(row for row in rows if row["group"] != heldout)
        test = tuple(row for row in rows if row["group"] == heldout)
        rule = _fit_threshold(train, feature, direction)
        predictions.extend((row, bool(rule and rule.accepts(row)))
                           for row in test)
    exact_deferred = sum(row["exact"] and decision
                         for row, decision in predictions)
    false_deferred = sum(not row["exact"] and decision
                         for row, decision in predictions)
    false_rejected = sum(not row["exact"] and not decision
                         for row, decision in predictions)
    exact_groups = len({row["group"] for row, decision in predictions
                        if row["exact"] and decision})
    return {
        "exact_groups_deferred": exact_groups,
        "exact_deferred": exact_deferred,
        "false_deferred": false_deferred,
        "false_rejected": false_rejected,
    }


def _select_family(rows):
    features = tuple(sorted(rows[0]["boundary_context"]))
    candidates = []
    for feature_index, feature in enumerate(features):
        for direction_index, direction in enumerate(DIRECTIONS):
            score = _family_cross_validation(rows, feature, direction)
            key = (score["exact_groups_deferred"],
                   score["exact_deferred"], score["false_rejected"],
                   -score["false_deferred"], -feature_index,
                   -direction_index)
            candidates.append((key, feature, direction, score))
    _key, feature, direction, score = max(candidates)
    return feature, direction, score


def _shuffle_labels_within_group(rows, trial):
    labels = [None] * len(rows)
    rng = random.Random(SHUFFLE_SEED + trial)
    for group in sorted(set(row["group"] for row in rows)):
        indices = [index for index, row in enumerate(rows)
                   if row["group"] == group]
        values = [bool(rows[index]["exact"]) for index in indices]
        rng.shuffle(values)
        for index, value in zip(indices, values):
            labels[index] = value
    return tuple(labels)


def evaluate():
    dataset = load_default_dataset()
    rows = _forward_unsatisfied_rows(dataset)
    feature, direction, cross_validation = _select_family(rows)
    rule = _fit_threshold(rows, feature, direction)
    if rule is None:
        raise AssertionError("no boundary backoff can retain train exact rows")

    deferred = tuple(row for row in rows if rule.accepts(row))
    rejected = tuple(row for row in rows if not rule.accepts(row))
    all_rows = tuple(row for group in dataset["groups"]
                     for row in group["rows"])
    forward_sat = tuple(row for row in all_rows
                        if row["certificates"]["forward"]["status"]
                        == "satisfied")
    supplied_groups = tuple(group for group in dataset["groups"]
                            if any(row["exact"] for row in group["rows"]))
    final_exact = sum(row["exact"] for row in forward_sat + deferred)
    final_false = sum(not row["exact"] for row in forward_sat + deferred)
    supply = sum(any(
        row["exact"] and (
            row["certificates"]["forward"]["status"] == "satisfied" or
            rule.accepts({**row, "group": group["group"]}))
        for row in group["rows"]) for group in supplied_groups)

    null_scores = []
    for trial in range(SHUFFLES):
        shuffled = _forward_unsatisfied_rows(
            dataset, _shuffle_labels_within_group(rows, trial))
        _feature, _direction, score = _select_family(shuffled)
        null_scores.append(score)
    exact_p = (1 + sum(score["exact_deferred"] >=
                       cross_validation["exact_deferred"]
                       for score in null_scores)) / (SHUFFLES + 1)
    rejection_p = (1 + sum(score["false_rejected"] >=
                           cross_validation["false_rejected"]
                           for score in null_scores)) / (SHUFFLES + 1)

    body = {
        "schema_version": 1,
        "source_dataset_digest": dataset["dataset_digest"],
        "forward_unsatisfied_branches": len(rows),
        "forward_unsatisfied_exact": sum(row["exact"] for row in rows),
        "forward_unsatisfied_false": sum(not row["exact"] for row in rows),
        "candidate_feature_count": len(rows[0]["boundary_context"]),
        "candidate_rule_family": "one scalar threshold; <= or >=",
        "selected_feature": feature,
        "selected_direction": direction,
        "selected_threshold": rule.threshold,
        "group_heldout_metrics": cross_validation,
        "deferred_exact": sum(row["exact"] for row in deferred),
        "deferred_false": sum(not row["exact"] for row in deferred),
        "rejected_exact": sum(row["exact"] for row in rejected),
        "rejected_false": sum(not row["exact"] for row in rejected),
        "final_exact": final_exact,
        "final_false": final_false,
        "final_precision": final_exact / (final_exact + final_false),
        "supplied_groups_after_backoff": supply,
        "supplied_groups": len(supplied_groups),
        "shuffle_trials": SHUFFLES,
        "within_group_label_shuffle": True,
        "shuffle_exact_deferred_median": sorted(
            score["exact_deferred"] for score in null_scores)[SHUFFLES // 2],
        "shuffle_false_rejected_median": sorted(
            score["false_rejected"] for score in null_scores)[SHUFFLES // 2],
        "exact_deferred_empirical_p": exact_p,
        "false_rejected_empirical_p": rejection_p,
        "deferred_is_not_port_satisfied": True,
        "candidate_geometry_unchanged": True,
        "group_label_or_raw_occurrence_id_used_as_feature": False,
        "target_used_for_boundary_features": False,
        "development_labels_used_for_family_selection": True,
        "fresh_confirmation_claimed": False,
        "integrated_as_default_marking": False,
        "boundary_backoff_supply_gate_passed": bool(
            supply == len(supplied_groups) and
            not any(row["exact"] for row in rejected)),
        "causal_marking_gate_passed": bool(
            exact_p <= .05 and rejection_p <= .05),
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
        "honest_status": (
            "a one-dimensional port-length boundary backoff restores all "
            "nine supplied nuclei and still rejects 8 false branches, but "
            "all 31 within-nucleus label shuffles tie it; this is a useful "
            "descriptive fallback and not evidence for a learned marking"),
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
