#!/usr/bin/env python3
"""Site-resolved selector over the tie-robust stage-local IQC portfolio.

The frozen connection marking retains a ``4 -> 8 -> 8`` prefix portfolio.
This audit scores the three sites of each unchanged terminal separately using
only its target-free stage-local section and intrinsic colored triangle
geometry, then aggregates those scores back to the whole action.  Grouped
receipts freeze before labels; 31 site-consistent shuffles repeat full model
and aggregation selection.  No confirmation data is imported.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
import random
import statistics

import numpy as np

from materials_gcts_iqc_obligation_expanded_dataset import _digest
from materials_gcts_iqc_obligation_expanded_preregistration import (
    SHUFFLES, SHUFFLE_SEED)
from materials_gcts_iqc_obligation_site_resolved_audit import (
    _aggregate, _intrinsic_site_features)
from materials_gcts_iqc_stage_local_prefix_dataset import load_default_dataset
from materials_gcts_iqc_stage_local_prefix_marking_audit import (
    BRANCH_FEATURES, FRONTIER_FEATURES, PrefixMarkingSpec, _eligible,
    _flatten, _freeze_receipts, _real_labels, _row_id, _score,
    _select_rows)


PREFIX_SPECS = (
    PrefixMarkingSpec("coupled", 19, True),
    PrefixMarkingSpec("section", 19, True),
    PrefixMarkingSpec("coupled", 19, True),
)
PREFIX_BUDGET = (4, 8, 8)
SITE_VARIANTS = ("intrinsic", "branch", "section", "coupled")
SITE_NEIGHBORS = (3, 5, 9, 19)
SITE_WEIGHTED = (False, True)
AGGREGATIONS = ("minimum", "mean", "product")
EXPECTED_AUDIT_DIGEST = ""


@dataclass(frozen=True)
class SiteSelectorSpec:
    variant: str
    neighbors: int
    weighted: bool
    aggregation: str


SPECS = tuple(SiteSelectorSpec(variant, neighbors, weighted, aggregation)
              for variant in SITE_VARIANTS for neighbors in SITE_NEIGHBORS
              for weighted in SITE_WEIGHTED for aggregation in AGGREGATIONS)


def _candidate_id(row):
    return f"{row['group']}:{row['candidate_index']}"


def _site_id(row, site):
    return f"{_candidate_id(row)}:{site}"


def _shortlist(rows, labels, prefix_receipts):
    selected_keys, selected_rows = {}, None
    for depth, (spec, budget) in enumerate(zip(
            PREFIX_SPECS, PREFIX_BUDGET), start=1):
        candidates = _eligible(tuple(
            row for row in rows if row["depth"] == depth),
            selected_keys, depth)
        receipts = prefix_receipts[(depth, spec.variant)]
        scores = {_row_id(row): _score(
            receipts[_row_id(row)], labels, spec) for row in candidates}
        selected_rows = _select_rows(candidates, scores, budget)
        selected_keys = {group: {
            row["action_key_frozen"] for row in group_rows}
                         for group, group_rows in selected_rows.items()}
    result = []
    for group, group_rows in sorted(selected_rows.items()):
        for index, row in enumerate(group_rows):
            result.append({**row, "candidate_index": index})
    return tuple(result)


def _state_indices(width, variant):
    section = tuple(range(BRANCH_FEATURES,
                          width - FRONTIER_FEATURES))
    if variant == "intrinsic":
        return ()
    if variant == "branch":
        return tuple(range(BRANCH_FEATURES))
    if variant == "section":
        return section
    if variant == "coupled":
        return tuple(range(width))
    raise ValueError(f"unknown site variant {variant}")


def _length_scale(candidates, excluded_group):
    distances = tuple(math.dist(left[0], right[0])
                      for row in candidates if row["group"] != excluded_group
                      for index, left in enumerate(row["action_key_frozen"])
                      for right in row["action_key_frozen"][index + 1:])
    return max(1e-9, statistics.median(distances))


def _features(row, site, variant, length_scale):
    indices = _state_indices(len(row["features"]), variant)
    state = tuple(float(row["features"][index]) for index in indices)
    return state + _intrinsic_site_features(
        row["action_key_frozen"], site, length_scale)


def _freeze_site_receipts(candidates):
    groups = tuple(sorted({row["group"] for row in candidates}))
    result, records = {}, []
    for variant in SITE_VARIANTS:
        receipts, scales = {}, []
        for heldout in groups:
            length_scale = _length_scale(candidates, heldout)
            scales.append((heldout, length_scale))
            train_sites = tuple((row, site) for row in candidates
                                if row["group"] != heldout
                                for site in range(3))
            test_sites = tuple((row, site) for row in candidates
                               if row["group"] == heldout
                               for site in range(3))
            train = np.asarray(tuple(_features(
                row, site, variant, length_scale)
                                     for row, site in train_sites), dtype=float)
            test = np.asarray(tuple(_features(
                row, site, variant, length_scale)
                                    for row, site in test_sites), dtype=float)
            means = train.mean(axis=0)
            standard = np.maximum(1e-9, train.std(axis=0))
            train = (train - means) / standard
            test = (test - means) / standard
            distances = np.maximum(
                0., np.sum(test * test, axis=1)[:, None] +
                np.sum(train * train, axis=1)[None, :] -
                2. * test @ train.T)
            for local_test, (test_row, test_site) in enumerate(test_sites):
                nearest = {}
                for local_train, (train_row, train_site) in enumerate(
                        train_sites):
                    record = (float(distances[local_test, local_train]),
                              _site_id(train_row, train_site))
                    group = train_row["group"]
                    if group not in nearest or record < nearest[group]:
                        nearest[group] = record
                receipts[_site_id(test_row, test_site)] = tuple(
                    sorted(nearest.values()))
        result[variant] = receipts
        records.append({
            "variant": variant, "fold_length_scales": tuple(scales),
            "receipt_digest": _digest(tuple(sorted(receipts.items()))),
        })
    return result, tuple(records), _digest(tuple(records))


def _site_score(receipt, labels, spec):
    nearest = receipt[:spec.neighbors]
    weights = tuple(1. / (1. + math.sqrt(distance))
                    if spec.weighted else 1.
                    for distance, _site in nearest)
    return sum(weight * float(labels[site])
               for weight, (_distance, site) in zip(weights, nearest)) / \
        sum(weights)


def _evaluate_spec(candidates, labels, receipts, spec):
    scores, site_scores = {}, {}
    for row in candidates:
        values = tuple(_site_score(
            receipts[spec.variant][_site_id(row, site)], labels, spec)
                       for site in range(3))
        site_scores[_candidate_id(row)] = values
        scores[_candidate_id(row)] = _aggregate(values, spec.aggregation)
    selected = []
    margins, safe = [], 0
    for group in sorted({row["group"] for row in candidates}):
        rows = tuple(row for row in candidates if row["group"] == group)
        ranked = sorted(rows, key=lambda row: (
            -scores[_candidate_id(row)], _candidate_id(row)))
        selected.append(ranked[0])
        positives = tuple(scores[_candidate_id(row)] for row in rows
                          if all(labels[_site_id(row, site)]
                                 for site in range(3)))
        negatives = tuple(scores[_candidate_id(row)] for row in rows
                          if not all(labels[_site_id(row, site)]
                                     for site in range(3)))
        margins.append(max(positives, default=0.) - max(negatives, default=0.))
        top = scores[_candidate_id(ranked[0])]
        tied = tuple(row for row in rows
                     if abs(scores[_candidate_id(row)] - top) <= 1e-12)
        safe += not (any(all(labels[_site_id(row, site)] for site in range(3))
                         for row in tied) and
                     any(not all(labels[_site_id(row, site)] for site in range(3))
                         for row in tied))
    exact = sum(all(labels[_site_id(row, site)] for site in range(3))
                for row in selected)
    correct = sum(labels[_site_id(row, site)]
                  for row in selected for site in range(3))
    return {
        "spec": asdict(spec),
        "selected": tuple(_candidate_id(row) for row in selected),
        "exact_actions": exact, "correct_sites": correct,
        "tie_safe_groups": safe,
        "minimum_action_margin": min(margins),
        "sum_action_margin": sum(margins),
        "selected_site_scores": tuple((
            _candidate_id(row), site_scores[_candidate_id(row)])
            for row in selected),
    }


def _select(candidates, labels, receipts):
    audits = tuple(_evaluate_spec(candidates, labels, receipts, spec)
                   for spec in SPECS)
    index = max(range(len(audits)), key=lambda candidate: (
        audits[candidate]["exact_actions"],
        audits[candidate]["correct_sites"],
        audits[candidate]["tie_safe_groups"],
        audits[candidate]["minimum_action_margin"],
        audits[candidate]["sum_action_margin"], -candidate))
    return index, audits


def _site_map(candidates):
    result = {}
    for row in candidates:
        group = row["group"]
        target = result.setdefault(group, {})
        for site, label in zip(row["action_key_frozen"], row["site_correct"]):
            prior = target.setdefault(site, bool(label))
            if prior != bool(label):
                raise AssertionError("shortlist site label inconsistency")
    return result


def _labels(candidates, maps):
    return {_site_id(row, site): maps[row["group"]][
        row["action_key_frozen"][site]] for row in candidates
            for site in range(3)}


def _shuffle(candidates, trial):
    rng = random.Random(f"{SHUFFLE_SEED}:stage-local-site:{trial}")
    maps = _site_map(candidates)
    for group, source in maps.items():
        for color in sorted({site[1] for site in source}):
            sites = sorted((site for site in source if site[1] == color),
                           key=repr)
            values = [source[site] for site in sites]
            rng.shuffle(values)
            source.update(zip(sites, values))
    return _labels(candidates, maps)


def evaluate():
    dataset = load_default_dataset()
    rows = _flatten(dataset)
    prefix_receipts, prefix_records, prefix_digest = _freeze_receipts(rows)
    candidates = _shortlist(rows, _real_labels(rows), prefix_receipts)
    if len(candidates) != dataset["consumed_development_groups"] * 8:
        raise AssertionError("stage-local terminal shortlist drift")
    receipts, receipt_records, receipt_digest = _freeze_site_receipts(candidates)
    labels = _labels(candidates, _site_map(candidates))
    selected_index, audits = _select(candidates, labels, receipts)
    selected = audits[selected_index]
    baseline = sum(all(labels[_site_id(row, site)] for site in range(3))
                   for group in range(dataset["consumed_development_groups"])
                   for row in tuple(item for item in candidates
                                    if item["group"] == group)[:1])
    nulls, null_indices = [], []
    for trial in range(SHUFFLES):
        index, trial_audits = _select(
            candidates, _shuffle(candidates, trial), receipts)
        null_indices.append(index)
        nulls.append(trial_audits[index])
    null_exact = tuple(row["exact_actions"] for row in nulls)
    null_sites = tuple(row["correct_sites"] for row in nulls)
    exact_p = (1 + sum(value >= selected["exact_actions"]
                       for value in null_exact)) / (SHUFFLES + 1)
    sites_p = (1 + sum(value >= selected["correct_sites"]
                       for value in null_sites)) / (SHUFFLES + 1)
    body = {
        "schema_version": 1,
        "source_dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["consumed_development_groups"],
        "prefix_specs": tuple(asdict(spec) for spec in PREFIX_SPECS),
        "prefix_budget": PREFIX_BUDGET,
        "prefix_receipt_records": prefix_records,
        "prefix_receipt_digest_before_labels": prefix_digest,
        "shortlist_candidates": len(candidates),
        "shortlist_digest": _digest(tuple(
            (row["group"], row["candidate_index"], row["action_key_frozen"])
            for row in candidates)),
        "site_specs": tuple(asdict(spec) for spec in SPECS),
        "site_receipt_records": receipt_records,
        "site_receipt_digest_before_labels": receipt_digest,
        "selected_spec_index": selected_index,
        "selected_result": selected,
        "all_spec_results": audits,
        "connection_score_top_one_exact_actions": baseline,
        "shuffle_trials": SHUFFLES,
        "fully_reselected_shuffle_spec_indices": tuple(null_indices),
        "shuffle_exact_action_counts": null_exact,
        "shuffle_correct_site_counts": null_sites,
        "shuffle_exact_action_maximum": max(null_exact),
        "shuffle_correct_site_maximum": max(null_sites),
        "shuffle_exact_upper_tail_p": exact_p,
        "shuffle_sites_upper_tail_p": sites_p,
        "site_labels_shuffled_consistently_across_shared_actions": True,
        "whole_terminal_geometry_unchanged": True,
        "confirmation_data_imported_or_used": False,
        "targets_used_for_receipts_or_scores": False,
        "consumed_development_only": True,
        "fresh_confirmation_opened": False,
        "integrated_as_default_marking": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["site_selector_gate_passed"] = bool(
        selected["exact_actions"] > baseline and
        selected["exact_actions"] > max(null_exact) and
        selected["correct_sites"] > max(null_sites) and
        exact_p <= .05 and sites_p <= .05)
    return {**body, "audit_digest": _digest(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    if EXPECTED_AUDIT_DIGEST and row["audit_digest"] != \
            EXPECTED_AUDIT_DIGEST:
        raise AssertionError("stage-local site selector audit drift")
    print(json.dumps(row, indent=2, sort_keys=True) if args.json else
          ("stage-local site selector gate passes" if
           row["site_selector_gate_passed"] else
           "stage-local site selector gate remains red"))


if __name__ == "__main__":
    main()
