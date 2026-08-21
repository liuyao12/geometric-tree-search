#!/usr/bin/env python3
"""Learn a stage-local IQC prefix marking on consumed development nuclei.

The action geometry and every target-free feature receipt are frozen by the
companion dataset before labels exist.  A grouped nearest-neighbour marking is
selected separately at each search depth, and can only retain a child when a
selected parent prefix exists.  Thirty-one within-nucleus, within-species
site-label shuffles repeat the complete depth/model/budget selection.

This is a development gate.  Passing it can authorize integration into a new
sealed confirmation, but is not itself autonomous growth or stationarity.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import random

import numpy as np

from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_obligation_expanded_preregistration import (
    SHUFFLES, SHUFFLE_SEED)
from materials_gcts_iqc_stage_local_prefix_dataset import (
    load_default_dataset)


BRANCH_FEATURES = 31
FRONTIER_FEATURES = 3
VARIANTS = ("branch", "section", "branch-section", "coupled")
NEIGHBORS = (3, 5, 9, 19)
WEIGHTED = (False, True)
BEAM_BUDGETS = ((2, 4, 1), (4, 4, 1), (4, 8, 1), (8, 8, 1))
EXPECTED_AUDIT_DIGEST = \
    "8b2449ff42240ba4f4ba4ae2fed8b0c836d278ffb14b9703ae71cdfc0341a582"


@dataclass(frozen=True)
class PrefixMarkingSpec:
    variant: str
    neighbors: int
    weighted: bool


SPECS = tuple(PrefixMarkingSpec(variant, neighbors, weighted)
              for variant in VARIANTS for neighbors in NEIGHBORS
              for weighted in WEIGHTED)


def _hashable(value):
    if isinstance(value, list):
        return tuple(_hashable(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((key, _hashable(item))
                            for key, item in value.items()))
    return value


def _row_id(row):
    return f"{row['group']}:{row['depth']}:{row['row_index']}"


def _flatten(dataset):
    rows = []
    for group in dataset["groups"]:
        for stage in group["stages"]:
            for index, source in enumerate(stage["rows"]):
                rows.append({
                    **source,
                    "group": int(group["group"]),
                    "depth": int(stage["depth"]),
                    "row_index": index,
                    "action_key_frozen": _hashable(source["action_key"]),
                    "parent_keys_frozen": tuple(
                        _hashable(key) for key in source["parent_keys"]),
                })
    return tuple(rows)


def _variant_indices(length, variant):
    if length <= BRANCH_FEATURES + FRONTIER_FEATURES:
        raise AssertionError("stage-local feature vector is incomplete")
    section = tuple(range(BRANCH_FEATURES,
                          length - FRONTIER_FEATURES))
    if variant == "branch":
        return tuple(range(BRANCH_FEATURES))
    if variant == "section":
        return section
    if variant == "branch-section":
        return tuple(range(length - FRONTIER_FEATURES))
    if variant == "coupled":
        return tuple(range(length))
    raise ValueError(f"unknown feature variant {variant}")


def _freeze_receipts(rows):
    groups = tuple(sorted({row["group"] for row in rows}))
    receipts, records = {}, []
    for depth in (1, 2, 3):
        depth_rows = tuple(row for row in rows if row["depth"] == depth)
        lengths = {len(row["features"]) for row in depth_rows}
        if len(lengths) != 1:
            raise AssertionError("stage-local feature width drift")
        length = next(iter(lengths))
        for variant in VARIANTS:
            indices = _variant_indices(length, variant)
            vectors = np.asarray(tuple(tuple(float(row["features"][index])
                                             for index in indices)
                                       for row in depth_rows), dtype=float)
            variant_receipts = {}
            fold_records = []
            for heldout in groups:
                train_indices = np.asarray(tuple(
                    index for index, row in enumerate(depth_rows)
                    if row["group"] != heldout), dtype=int)
                test_indices = np.asarray(tuple(
                    index for index, row in enumerate(depth_rows)
                    if row["group"] == heldout), dtype=int)
                train = vectors[train_indices]
                mean = train.mean(axis=0)
                scale = np.maximum(1e-9, train.std(axis=0))
                train = (train - mean) / scale
                test = (vectors[test_indices] - mean) / scale
                distances = np.maximum(
                    0., np.sum(test * test, axis=1)[:, None] +
                    np.sum(train * train, axis=1)[None, :] -
                    2. * test @ train.T)
                for local_test, test_index in enumerate(test_indices):
                    nearest = {}
                    for local_train, train_index in enumerate(train_indices):
                        training = depth_rows[int(train_index)]
                        record = (float(distances[local_test, local_train]),
                                  _row_id(training))
                        group = int(training["group"])
                        if group not in nearest or record < nearest[group]:
                            nearest[group] = record
                    variant_receipts[_row_id(
                        depth_rows[int(test_index)])] = tuple(
                            sorted(nearest.values()))
                fold_records.append((
                    heldout, tuple(map(float, mean)),
                    tuple(map(float, scale))))
            receipts[(depth, variant)] = variant_receipts
            records.append({
                "depth": depth, "variant": variant,
                "feature_indices": indices,
                "fold_normalization_digest": _digest(tuple(fold_records)),
                "receipt_digest": _digest(tuple(sorted(
                    variant_receipts.items()))),
            })
    return receipts, tuple(records), _digest(tuple(records))


def _score(receipt, labels, spec):
    nearest = receipt[:min(spec.neighbors, len(receipt))]
    if not nearest:
        return 0.
    weights = tuple(1. / (1. + math.sqrt(distance))
                    if spec.weighted else 1.
                    for distance, _row in nearest)
    return sum(weight * float(labels[row][0])
               for weight, (_distance, row) in zip(weights, nearest)) / \
        sum(weights)


def _eligible(rows, selected, depth):
    if depth == 1:
        return rows
    return tuple(row for row in rows if any(
        parent in selected.get(row["group"], set())
        for parent in row["parent_keys_frozen"]))


def _select_rows(rows, scores, budget):
    selected = {}
    for group in sorted({row["group"] for row in rows}):
        options = tuple(row for row in rows if row["group"] == group)
        ordered = sorted(options, key=lambda row: (
            -scores[_row_id(row)], repr(row["action_key_frozen"])))
        selected[group] = tuple(ordered[:budget])
    return selected


def _stage_objective(selected, labels):
    viable_groups = sum(any(labels[_row_id(row)][0] for row in group)
                        for group in selected.values())
    viable_rows = sum(labels[_row_id(row)][0]
                      for group in selected.values() for row in group)
    correct_sites = sum(labels[_row_id(row)][1]
                        for group in selected.values() for row in group)
    retained = sum(map(len, selected.values()))
    return viable_groups, viable_rows, correct_sites, -retained


def _score_tables(rows, labels, receipts):
    tables = {}
    for depth in (1, 2, 3):
        depth_rows = tuple(row for row in rows if row["depth"] == depth)
        for spec_index, spec in enumerate(SPECS):
            variant_receipts = receipts[(depth, spec.variant)]
            tables[(depth, spec_index)] = {
                _row_id(row): _score(
                    variant_receipts[_row_id(row)], labels, spec)
                for row in depth_rows}
    return tables


def _run_budget(rows, labels, score_tables, budget):
    selected_keys, stages, chosen_specs = {}, [], []
    for depth, stage_budget in enumerate(budget, start=1):
        depth_rows = tuple(row for row in rows if row["depth"] == depth)
        candidates = _eligible(depth_rows, selected_keys, depth)
        audits = []
        for spec_index, spec in enumerate(SPECS):
            table = score_tables[(depth, spec_index)]
            scores = {_row_id(row): table[_row_id(row)]
                      for row in candidates}
            selected = _select_rows(candidates, scores, stage_budget) \
                if candidates else {}
            audits.append((
                _stage_objective(selected, labels), -spec_index,
                spec, scores, selected))
        _objective, _stable, spec, scores, selected = max(
            audits, key=lambda item: (item[0], item[1]))
        selected_keys = {group: {
            row["action_key_frozen"] for row in group_rows}
                         for group, group_rows in selected.items()}
        chosen_specs.append(spec)
        stages.append({
            "depth": depth, "budget": stage_budget,
            "spec": asdict(spec), "eligible": len(candidates),
            "selected": sum(map(len, selected.values())),
            "viable_groups": _stage_objective(selected, labels)[0],
            "viable_rows": _stage_objective(selected, labels)[1],
            "correct_sites": _stage_objective(selected, labels)[2],
            "selected_ids": tuple(sorted(
                _row_id(row) for group in selected.values() for row in group)),
        })
    final = stages[-1]
    return {
        "budget": tuple(budget), "stages": tuple(stages),
        "chosen_specs": tuple(asdict(spec) for spec in chosen_specs),
        "exact_selected_groups": final["viable_groups"],
        "exact_selected_rows": final["viable_rows"],
        "selected_correct_sites": final["correct_sites"],
        "total_selected_prefixes": sum(stage["selected"]
                                       for stage in stages),
    }


def _select_policy(rows, labels, receipts):
    score_tables = _score_tables(rows, labels, receipts)
    audits = tuple(_run_budget(rows, labels, score_tables, budget)
                   for budget in BEAM_BUDGETS)
    index = max(range(len(audits)), key=lambda candidate: (
        audits[candidate]["exact_selected_groups"],
        audits[candidate]["exact_selected_rows"],
        audits[candidate]["selected_correct_sites"],
        audits[candidate]["stages"][1]["viable_groups"],
        audits[candidate]["stages"][0]["viable_groups"],
        -audits[candidate]["total_selected_prefixes"], -candidate))
    return index, audits


def _baseline(rows, labels, budget):
    selected_keys, stages = {}, []
    for depth, stage_budget in enumerate(budget, start=1):
        depth_rows = tuple(row for row in rows if row["depth"] == depth)
        candidates = _eligible(depth_rows, selected_keys, depth)
        # Cumulative log pose-port probability is frozen branch feature 1.
        scores = {_row_id(row): float(row["features"][1])
                  for row in candidates}
        selected = _select_rows(candidates, scores, stage_budget) \
            if candidates else {}
        selected_keys = {group: {
            row["action_key_frozen"] for row in group_rows}
                         for group, group_rows in selected.items()}
        objective = _stage_objective(selected, labels)
        stages.append({
            "depth": depth, "eligible": len(candidates),
            "selected": sum(map(len, selected.values())),
            "viable_groups": objective[0], "viable_rows": objective[1],
            "correct_sites": objective[2],
        })
    return {
        "budget": tuple(budget), "stages": tuple(stages),
        "exact_selected_groups": stages[-1]["viable_groups"],
        "exact_selected_rows": stages[-1]["viable_rows"],
        "selected_correct_sites": stages[-1]["correct_sites"],
    }


def _real_labels(rows):
    return {_row_id(row): (bool(row["viable_prefix"]),
                           int(row["correct_sites"])) for row in rows}


def _site_label_maps(rows):
    maps = {}
    for row in rows:
        group = row["group"]
        target = maps.setdefault(group, {})
        for site, label in zip(row["action_key_frozen"],
                               row["site_correct"]):
            prior = target.setdefault(site, bool(label))
            if prior != bool(label):
                raise AssertionError("site truth changes across prefixes")
    return maps


def _shuffle_labels(rows, trial):
    rng = random.Random(f"{SHUFFLE_SEED}:stage-local-prefix:{trial}")
    shuffled = {}
    for group, source in _site_label_maps(rows).items():
        target = dict(source)
        colors = sorted({site[1] for site in source})
        for color in colors:
            sites = sorted((site for site in source if site[1] == color),
                           key=repr)
            values = [source[site] for site in sites]
            rng.shuffle(values)
            target.update(zip(sites, values))
        shuffled[group] = target
    return {_row_id(row): (
        all(shuffled[row["group"]][site]
            for site in row["action_key_frozen"]),
        sum(shuffled[row["group"]][site]
            for site in row["action_key_frozen"])) for row in rows}


def evaluate():
    dataset = load_default_dataset()
    rows = _flatten(dataset)
    receipts, receipt_records, receipt_digest = _freeze_receipts(rows)
    labels = _real_labels(rows)
    selected_index, audits = _select_policy(rows, labels, receipts)
    selected = audits[selected_index]
    baseline = _baseline(rows, labels, selected["budget"])
    nulls, null_policy_indices = [], []
    for trial in range(SHUFFLES):
        index, trial_audits = _select_policy(
            rows, _shuffle_labels(rows, trial), receipts)
        nulls.append(trial_audits[index])
        null_policy_indices.append(index)
    null_groups = tuple(row["exact_selected_groups"] for row in nulls)
    null_rows = tuple(row["exact_selected_rows"] for row in nulls)
    group_p = (1 + sum(value >= selected["exact_selected_groups"]
                       for value in null_groups)) / (SHUFFLES + 1)
    row_p = (1 + sum(value >= selected["exact_selected_rows"]
                     for value in null_rows)) / (SHUFFLES + 1)
    exact_supply_groups = sum(any(
        row["viable_prefix"] for row in rows
        if row["group"] == group and row["depth"] == 3)
        for group in sorted({row["group"] for row in rows}))
    body = {
        "schema_version": 1,
        "development_dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["consumed_development_groups"],
        "rows_by_depth": tuple(sum(row["depth"] == depth for row in rows)
                               for depth in (1, 2, 3)),
        "exact_terminal_supply_groups": exact_supply_groups,
        "feature_variants": VARIANTS,
        "candidate_specs": tuple(asdict(spec) for spec in SPECS),
        "beam_budgets": BEAM_BUDGETS,
        "geometry_receipt_records": receipt_records,
        "geometry_receipt_digest_before_labels": receipt_digest,
        "selected_policy_index": selected_index,
        "selected_result": selected,
        "all_budget_results": audits,
        "matched_current_pose_port_baseline": baseline,
        "shuffle_trials": SHUFFLES,
        "fully_reselected_shuffle_policy_indices": tuple(
            null_policy_indices),
        "shuffle_exact_group_counts": null_groups,
        "shuffle_exact_row_counts": null_rows,
        "shuffle_exact_group_median": sorted(null_groups)[SHUFFLES // 2],
        "shuffle_exact_group_maximum": max(null_groups),
        "shuffle_exact_row_median": sorted(null_rows)[SHUFFLES // 2],
        "shuffle_exact_row_maximum": max(null_rows),
        "shuffle_group_upper_tail_p": group_p,
        "shuffle_row_upper_tail_p": row_p,
        "within_group_species_stratified_site_shuffles": True,
        "prefix_consistency_preserved_in_nulls": True,
        "targets_used_for_features_or_receipts": False,
        "candidate_geometry_changed": False,
        "consumed_development_only": True,
        "fresh_confirmation_opened": False,
        "integrated_as_default_marking": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["stage_local_gate_passed"] = bool(
        exact_supply_groups > 0 and
        selected["exact_selected_groups"] >
        baseline["exact_selected_groups"] and
        selected["exact_selected_groups"] > max(null_groups) and
        selected["exact_selected_rows"] > max(null_rows) and
        group_p <= .05 and row_p <= .05)
    return {**body, "audit_digest": _digest(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    if EXPECTED_AUDIT_DIGEST and report["audit_digest"] != \
            EXPECTED_AUDIT_DIGEST:
        raise AssertionError("stage-local prefix marking audit drift")
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else
          ("stage-local prefix marking gate passes" if
           report["stage_local_gate_passed"] else
           "stage-local prefix marking gate remains red"))


if __name__ == "__main__":
    main()
