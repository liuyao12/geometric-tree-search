#!/usr/bin/env python3
"""Train-only selection and consumed-nucleus audit of obligation backoff.

The backoff specification is selected only by whole-nucleus development
holdout.  A final model then ranks the already-frozen, target-free trajectories
from the consumed confirmation nucleus.  The old confirmation fixture is
opened only after that order freezes and supplies just the published partial
ordering fact: its first four actions were false and its fifth was exact.
The target is never reconstructed, so the second exact action remains unknown.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import random

from materials_gcts_iqc_port_obligation_automaton_audit import (
    _labelled, _rows)
from materials_gcts_iqc_port_obligation_confirmation import (
    load_default_result as load_confirmation_result)
from materials_gcts_iqc_port_obligation_confirmation_trajectories import (
    load_default_dataset as load_confirmation_trajectories)
from materials_gcts_iqc_relational_port_rule import SHUFFLES, SHUFFLE_SEED
from materials_gcts_port_obligation_backoff import (
    PortObligationBackoffLevel, PortObligationBackoffSpec,
    fit_port_obligation_backoff, score_port_obligation_backoff)


def _spec(*levels, weakest):
    return PortObligationBackoffSpec(tuple(
        PortObligationBackoffLevel(kind, cap, minimum_groups)
        for kind, cap, minimum_groups in levels), weakest)


CANDIDATE_SPECS = (
    _spec(("exact", 4, 1), weakest=4),
    _spec(("exact", 4, 1), weakest=8),
    _spec(("exact", 4, 1), ("aggregate", 1, 1), weakest=4),
    _spec(("exact", 4, 1), ("aggregate", 1, 1), weakest=8),
    _spec(("exact", 4, 1), ("role_shape", 2, 1), weakest=4),
    _spec(("exact", 4, 1), ("role_shape", 2, 1), weakest=8),
    _spec(("exact", 4, 1), ("role_shape", 2, 1),
          ("aggregate", 1, 1), weakest=4),
    _spec(("exact", 4, 1), ("role_shape", 2, 1),
          ("aggregate", 1, 1), weakest=8),
)


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _action_tuple(action):
    return tuple((tuple(float(value) for value in point), str(color))
                 for point, color in action)


def _heldout(geometry, labels, spec):
    selected = []
    coverages = []
    groups = tuple(sorted({row["group"] for row in geometry}))
    for heldout in groups:
        training = tuple(row for row in geometry
                         if row["group"] != heldout)
        model = fit_port_obligation_backoff(
            _labelled(training, labels), spec)
        candidates = tuple(row for row in geometry
                           if row["group"] == heldout)
        scored = tuple((row, score_port_obligation_backoff(
            model, row["transitions"])) for row in candidates)
        ranked = tuple(sorted(scored, key=lambda item: (
            -item[1].score, item[0]["stable_index"])))
        selected.append(ranked[0][0])
        coverages.extend(item[1].recognized_fraction for item in scored)
    supplied = {group for (group, _index), (exact, _sites)
                in labels.items() if exact}
    exact = sum(bool(labels[row["group"], row["stable_index"]][0])
                for row in selected if row["group"] in supplied)
    sites = sum(int(labels[row["group"], row["stable_index"]][1])
                for row in selected)
    return {
        "selected": tuple((row["group"], row["stable_index"])
                          for row in selected),
        "exact": exact,
        "sites": sites,
        "minimum_coverage": min(coverages),
        "mean_coverage": sum(coverages) / len(coverages),
    }


def _objective(result, spec_index):
    # Exact/site fidelity is primary.  Coverage breaks scientific ties because
    # this audit addresses a measured unseen-state failure.  Complexity and a
    # stable declaration order are final tie breakers.
    return (result["exact"], result["sites"],
            result["minimum_coverage"], result["mean_coverage"],
            -len(CANDIDATE_SPECS[spec_index].levels), -spec_index)


def _select_spec(geometry, labels):
    results = tuple(_heldout(geometry, labels, spec)
                    for spec in CANDIDATE_SPECS)
    index = max(range(len(results)), key=lambda candidate:
                _objective(results[candidate], candidate))
    return index, results


def _shuffle(labels, trial):
    rng = random.Random(f"{SHUFFLE_SEED}:obligation-backoff:{trial}")
    result = dict(labels)
    for group in sorted({key[0] for key in labels}):
        keys = sorted(key for key in labels if key[0] == group)
        values = [labels[key] for key in keys]
        rng.shuffle(values)
        result.update(zip(keys, values))
    return result


def evaluate():
    development, geometry, labels, geometry_digest = _rows()
    selected_index, spec_results = _select_spec(geometry, labels)
    selected_spec = CANDIDATE_SPECS[selected_index]
    selected_result = spec_results[selected_index]
    null = []
    for trial in range(SHUFFLES):
        shuffled = _shuffle(labels, trial)
        null_index, null_results = _select_spec(geometry, shuffled)
        null.append(null_results[null_index]["exact"])
    p_value = (1 + sum(value >= selected_result["exact"]
                       for value in null)) / (SHUFFLES + 1)
    model = fit_port_obligation_backoff(
        _labelled(geometry, labels), selected_spec)

    # External geometry and its new order freeze before the consumed label
    # receipt is loaded below.
    external = load_confirmation_trajectories()
    scored = tuple((row, score_port_obligation_backoff(
        model, row["transitions"])) for row in external["geometry_rows"])
    ranked = tuple(sorted(scored, key=lambda item: (
        -item[1].score, repr(item[0]["action_key"]))))
    frozen_external_order = tuple(_action_tuple(row["action_key"])
                                  for row, _score in ranked)
    frozen_external_scores = tuple(score.score for _row, score in ranked)
    frozen_external_digest = _digest((
        frozen_external_order, frozen_external_scores,
        tuple(asdict(score) for _row, score in ranked)))

    confirmation = load_confirmation_result()
    old_order = tuple(_action_tuple(action)
                      for action in confirmation["ranked_action_keys"])
    first_exact = int(confirmation["first_exact_rank"])
    known_false = set(old_order[:first_exact - 1])
    known_exact = old_order[first_exact - 1]
    new_index = {action: index + 1 for index, action in enumerate(
        frozen_external_order)}
    known_exact_new_rank = new_index[known_exact]
    known_false_new_ranks = tuple(sorted(new_index[action]
                                         for action in known_false))
    known_exact_row = next(score for row, score in ranked
                           if _action_tuple(row["action_key"]) == known_exact)
    original_known_exact_coverage = float(
        confirmation["ranked_recognized_state_fractions"][first_exact - 1])

    level_histogram = Counter()
    for _row, score in ranked:
        for level, count in enumerate(score.level_hits):
            level_histogram[level] += count
    body = {
        "schema_version": 1,
        "development_dataset_digest": development["dataset_digest"],
        "development_geometry_digest": geometry_digest,
        "candidate_spec_count": len(CANDIDATE_SPECS),
        "selected_spec_index": selected_index,
        "selected_spec": asdict(selected_spec),
        "selected_development_result": selected_result,
        "all_development_results": tuple({
            "spec": asdict(spec), **result,
        } for spec, result in zip(CANDIDATE_SPECS, spec_results)),
        "model_digest": model.model_digest,
        "finite_state_count": len(model.states),
        "state_level_histogram": tuple(sorted(Counter(
            row.level_index for row in model.states).items())),
        "shuffle_trials": SHUFFLES,
        "fully_refit_shuffle_exact_counts": tuple(null),
        "shuffle_upper_tail_p": p_value,
        "external_target_free_dataset_digest": external["dataset_digest"],
        "external_candidate_count": len(ranked),
        "external_ranked_action_keys": frozen_external_order,
        "external_ranked_scores": frozen_external_scores,
        "external_ranked_score_records": tuple(
            asdict(score) for _row, score in ranked),
        "external_level_hit_histogram": tuple(sorted(
            level_histogram.items())),
        "external_order_digest_before_consumed_label_join":
            frozen_external_digest,
        "known_exact_old_rank": first_exact,
        "known_exact_new_rank": known_exact_new_rank,
        "known_false_new_ranks": known_false_new_ranks,
        "known_exact_original_recognized_fraction":
            original_known_exact_coverage,
        "known_exact_backoff_recognized_fraction":
            known_exact_row.recognized_fraction,
        "known_exact_outranks_all_four_published_false_actions":
            known_exact_new_rank < min(known_false_new_ranks),
        "second_exact_action_label_remains_unopened_and_unknown": True,
        "confirmation_target_reconstructed_or_reopened": False,
        "external_labels_used_for_fit_spec_or_rank": False,
        "candidate_geometry_changed": False,
        "integrated_as_default_marking": False,
        "new_confirmation_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["backoff_transfer_diagnostic_passed"] = bool(
        known_exact_row.recognized_fraction > original_known_exact_coverage and
        body["known_exact_outranks_all_four_published_false_actions"])
    return {**body, "audit_digest": _digest(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else
          ("obligation backoff transfer diagnostic passes" if
           report["backoff_transfer_diagnostic_passed"] else
           "obligation backoff remains red"))


if __name__ == "__main__":
    main()
