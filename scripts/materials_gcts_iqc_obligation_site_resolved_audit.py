#!/usr/bin/env python3
"""Site-resolved marking audit over immutable compatible IQC branches.

Each three-placement terminal remains one exact tree-search action.  The model
scores its three sites separately using only a bounded temporal obligation
section plus proper-motion-invariant colored triangle geometry, then aggregates
those scores back onto the unchanged terminal.  It cannot splice branches,
move sites, or authorize a partial cluster.  Selection and every grouped null
repeat the full neighbor/aggregation grid.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import random
import statistics

import numpy as np

from materials_gcts_iqc_obligation_expanded_dataset import (
    load_default_dataset as load_geometry_dataset)
from materials_gcts_iqc_obligation_expanded_preregistration import (
    SHUFFLES, SHUFFLE_SEED)
from materials_gcts_iqc_obligation_expanded_site_labels import (
    load_default_dataset as load_site_labels)
from materials_gcts_iqc_obligation_expanded_metric_audit import (
    _trace_features)
from materials_gcts_port_obligation_temporal_metric import (
    PortObligationTemporalMetricSpec, temporal_role_features)


BASE_TEMPORAL_SPEC = PortObligationTemporalMetricSpec(
    8, 2, False, 1, False)
NEIGHBORS = (3, 5, 7, 9, 13, 17)
WEIGHTED = (False, True)
AGGREGATIONS = ("minimum", "mean", "product")
EXPECTED_AUDIT_DIGEST = \
    "c765264cb0a2b5f1a432c3c03b5ee58fcc3d0ed9ad4565757eedbc69815c7a4c"


@dataclass(frozen=True)
class SiteResolvedSpec:
    neighbors: int
    weighted: bool
    aggregation: str


@dataclass(frozen=True)
class FrozenSiteResolvedModel:
    spec: SiteResolvedSpec
    length_scale: float
    means: tuple[float, ...]
    scales: tuple[float, ...]
    training_rows: tuple[dict, ...]
    model_digest: str
    target_used: bool = False
    candidate_geometry_changed: bool = False


SPECS = tuple(SiteResolvedSpec(neighbors, weighted, aggregation)
              for neighbors in NEIGHBORS for weighted in WEIGHTED
              for aggregation in AGGREGATIONS)


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _candidate_id(row):
    return f"{int(row['group'])}:{int(row['candidate_index'])}"


def _site_id(row, site_index):
    return f"{_candidate_id(row)}:{int(site_index)}"


def _distance(left, right):
    return math.sqrt(sum((float(a) - float(b)) ** 2
                         for a, b in zip(left, right)))


def _intrinsic_site_features(action, site_index, length_scale):
    sites = tuple((tuple(map(float, point)), str(color))
                  for point, color in action)
    point, color = sites[site_index]
    colors = ("X", "Y", "Z")
    if color not in colors:
        raise ValueError(f"unexpected IQC action color {color}")
    result = [float(color == item) for item in colors]
    others = tuple((other_point, other_color,
                    _distance(point, other_point) / length_scale)
                   for index, (other_point, other_color) in enumerate(sites)
                   if index != site_index)
    for channel in colors:
        distances = tuple(distance for _point, other_color, distance in others
                          if other_color == channel)
        result.extend((float(len(distances)), sum(distances),
                       min(distances, default=0.),
                       max(distances, default=0.)))
    pair_distances = sorted(_distance(left[0], right[0]) / length_scale
                            for index, left in enumerate(sites)
                            for right in sites[index + 1:])
    result.extend(pair_distances)
    other_points = tuple(item[0] for item in others)
    result.append(_distance(other_points[0], other_points[1]) / length_scale)
    return tuple(result)


def _row_base_features(row):
    return temporal_role_features(
        row["transitions"], BASE_TEMPORAL_SPEC, 0.) + \
        _trace_features(row["trace"])


def _fold_length_scale(geometry, train_indices):
    distances = tuple(_distance(left[0], right[0])
                      for index in train_indices
                      for left_index, left in enumerate(
                          geometry[index]["action_key"])
                      for right in geometry[index]["action_key"][
                          left_index + 1:])
    return max(1e-9, float(statistics.median(distances)))


def freeze_site_receipts(geometry):
    groups = tuple(sorted({int(row["group"]) for row in geometry}))
    base = tuple(_row_base_features(row) for row in geometry)
    receipts, scales = {}, {}
    for heldout in groups:
        train_rows = tuple(index for index, row in enumerate(geometry)
                           if int(row["group"]) != heldout)
        test_rows = tuple(index for index, row in enumerate(geometry)
                          if int(row["group"]) == heldout)
        length_scale = _fold_length_scale(geometry, train_rows)
        scales[heldout] = length_scale
        train_sites = tuple((row_index, site_index)
                            for row_index in train_rows
                            for site_index in range(3))
        test_sites = tuple((row_index, site_index)
                           for row_index in test_rows
                           for site_index in range(3))
        train = np.asarray(tuple(
            base[row_index] + _intrinsic_site_features(
                geometry[row_index]["action_key"], site_index, length_scale)
            for row_index, site_index in train_sites), dtype=float)
        test = np.asarray(tuple(
            base[row_index] + _intrinsic_site_features(
                geometry[row_index]["action_key"], site_index, length_scale)
            for row_index, site_index in test_sites), dtype=float)
        means = train.mean(axis=0)
        standard = np.maximum(1e-9, train.std(axis=0))
        train = (train - means) / standard
        test = (test - means) / standard
        distances = np.maximum(0.,
            np.sum(test * test, axis=1)[:, None] +
            np.sum(train * train, axis=1)[None, :] -
            2. * test @ train.T)
        for local_test, (test_row, test_site) in enumerate(test_sites):
            nearest = {}
            for local_train, (train_row, train_site) in enumerate(train_sites):
                row = geometry[train_row]
                record = (float(distances[local_test, local_train]),
                          _site_id(row, train_site))
                group = int(row["group"])
                if group not in nearest or record < nearest[group]:
                    nearest[group] = record
            receipts[_site_id(geometry[test_row], test_site)] = tuple(
                sorted(nearest.values()))
    body = {
        "base_temporal_spec": asdict(BASE_TEMPORAL_SPEC),
        "fold_length_scales": tuple(sorted(scales.items())),
        "receipts": tuple(sorted(receipts.items())),
    }
    return receipts, scales, _digest(body)


def _site_score(receipt, labels, spec):
    nearest = receipt[:spec.neighbors]
    weights = tuple(1. / (1. + math.sqrt(distance))
                    if spec.weighted else 1.
                    for distance, _site in nearest)
    return sum(weight * float(labels[site])
               for weight, (_distance, site) in zip(weights, nearest)) / \
        sum(weights)


def fit_site_resolved_model(geometry, labels, spec):
    indices = tuple(range(len(geometry)))
    length_scale = _fold_length_scale(geometry, indices)
    base = tuple(_row_base_features(row) for row in geometry)
    identities = tuple((row_index, site)
                       for row_index in indices for site in range(3))
    vectors = np.asarray(tuple(
        base[row_index] + _intrinsic_site_features(
            geometry[row_index]["action_key"], site, length_scale)
        for row_index, site in identities), dtype=float)
    means = vectors.mean(axis=0)
    scales = np.maximum(1e-9, vectors.std(axis=0))
    vectors = (vectors - means) / scales
    rows = tuple({
        "group": int(geometry[row_index]["group"]),
        "site_id": _site_id(geometry[row_index], site),
        "label": bool(labels[_site_id(geometry[row_index], site)]),
        "features": tuple(map(float, vector)),
    } for (row_index, site), vector in zip(identities, vectors))
    body = {
        "spec": asdict(spec), "length_scale": length_scale,
        "means": tuple(map(float, means)),
        "scales": tuple(map(float, scales)), "training_rows": rows,
    }
    return FrozenSiteResolvedModel(
        spec, length_scale, body["means"], body["scales"], rows,
        _digest(body))


def score_site_resolved_model(model, row):
    base = _row_base_features(row)
    site_scores = []
    for site in range(3):
        vector = base + _intrinsic_site_features(
            row["action_key"], site, model.length_scale)
        standardized = tuple((value - mean) / scale
                             for value, mean, scale in zip(
                                 vector, model.means, model.scales))
        nearest = {}
        for training in model.training_rows:
            distance = sum((left - right) ** 2 for left, right in zip(
                standardized, training["features"]))
            record = (distance, training["site_id"],
                      float(training["label"]))
            group = int(training["group"])
            if group not in nearest or record[:2] < nearest[group][:2]:
                nearest[group] = record
        rows = sorted(nearest.values())[:model.spec.neighbors]
        weights = tuple(1. / (1. + math.sqrt(distance))
                        if model.spec.weighted else 1.
                        for distance, _site, _label in rows)
        site_scores.append(sum(weight * item[2]
                               for weight, item in zip(weights, rows)) /
                           sum(weights))
    return tuple(site_scores), _aggregate(
        site_scores, model.spec.aggregation)


def _aggregate(values, kind):
    if kind == "minimum":
        return min(values)
    if kind == "mean":
        return sum(values) / len(values)
    if kind == "product":
        return math.prod(values)
    raise ValueError(f"unknown site aggregation {kind}")


def _auc(labels, scores):
    positive = tuple(key for key, value in labels.items() if all(value))
    negative = tuple(key for key, value in labels.items() if not all(value))
    if not positive or not negative:
        return .5
    wins = sum((scores[left] > scores[right]) +
               .5 * (scores[left] == scores[right])
               for left in positive for right in negative)
    return wins / (len(positive) * len(negative))


def _heldout(geometry, site_labels, spec, receipts):
    candidate_labels = {_candidate_id(row): tuple(
        bool(site_labels[_site_id(row, site)]) for site in range(3))
        for row in geometry}
    scores = {}
    for row in geometry:
        values = tuple(_site_score(
            receipts[_site_id(row, site)], site_labels, spec)
            for site in range(3))
        scores[_candidate_id(row)] = _aggregate(values, spec.aggregation)
    selected = []
    groups = tuple(sorted({int(row["group"]) for row in geometry}))
    for group in groups:
        rows = tuple(row for row in geometry if int(row["group"]) == group)
        selected.append(min(rows, key=lambda row: (
            -scores[_candidate_id(row)], _candidate_id(row))))
    epsilon = 1e-9
    exact_labels = {key: all(value)
                    for key, value in candidate_labels.items()}
    logloss = -sum(float(exact_labels[key]) * math.log(max(epsilon, score)) +
                   (1. - float(exact_labels[key])) * math.log(max(
                       epsilon, 1. - score))
                   for key, score in scores.items()) / len(scores)
    return {
        "selected": tuple(_candidate_id(row) for row in selected),
        "exact": sum(int(exact_labels[_candidate_id(row)])
                     for row in selected),
        "sites": sum(sum(candidate_labels[_candidate_id(row)])
                     for row in selected),
        "exact_bearing_groups": sum(any(exact_labels[_candidate_id(row)]
            for row in geometry if int(row["group"]) == group)
            for group in groups),
        "auc": _auc(candidate_labels, scores),
        "logloss": logloss,
    }


def _select(geometry, labels, receipts):
    audits = tuple(_heldout(geometry, labels, spec, receipts)
                   for spec in SPECS)
    index = max(range(len(audits)), key=lambda candidate: (
        audits[candidate]["exact"], audits[candidate]["sites"],
        -audits[candidate]["logloss"], audits[candidate]["auc"],
        -candidate))
    return index, audits


def _shuffle(label_vectors, trial):
    rng = random.Random(
        f"{SHUFFLE_SEED}:expanded-site-resolved:{trial}")
    result = dict(label_vectors)
    groups = sorted({int(key.split(":", 1)[0]) for key in label_vectors})
    for group in groups:
        candidates = sorted({":".join(key.split(":")[:2])
                             for key in label_vectors
                             if int(key.split(":", 1)[0]) == group})
        vectors = [tuple(label_vectors[f"{candidate}:{site}"]
                         for site in range(3)) for candidate in candidates]
        rng.shuffle(vectors)
        for candidate, vector in zip(candidates, vectors):
            for site, value in enumerate(vector):
                result[f"{candidate}:{site}"] = value
    return result


def evaluate():
    source = load_geometry_dataset()
    companion = load_site_labels()
    if companion["source_dataset_digest"] != source["dataset_digest"]:
        raise AssertionError("site companion/source mismatch")
    geometry = tuple({
        "group": int(group["group"]), "candidate_index": index,
        "action_key": row["action_key"],
        "transitions": row["transitions"], "trace": row["trace"],
    } for group in source["groups"]
      for index, row in enumerate(group["rows"]))
    receipts, length_scales, receipt_digest = freeze_site_receipts(geometry)
    label_vectors = {
        f"{int(group['group'])}:{int(item['candidate_index'])}:{site}":
        bool(value)
        for group in companion["groups"] for item in group["rows"]
        for site, value in enumerate(item["site_correct"])}
    selected_index, audits = _select(geometry, label_vectors, receipts)
    selected = audits[selected_index]
    model = fit_site_resolved_model(
        geometry, label_vectors, SPECS[selected_index])
    null_results, null_specs = [], []
    for trial in range(SHUFFLES):
        index, rows = _select(
            geometry, _shuffle(label_vectors, trial), receipts)
        null_results.append(rows[index])
        null_specs.append(index)
    null_exact = tuple(row["exact"] for row in null_results)
    null_sites = tuple(row["sites"] for row in null_results)
    exact_p = (1 + sum(value >= selected["exact"]
                       for value in null_exact)) / (SHUFFLES + 1)
    sites_p = (1 + sum(value >= selected["sites"]
                       for value in null_sites)) / (SHUFFLES + 1)
    body = {
        "schema_version": 1,
        "source_dataset_digest": source["dataset_digest"],
        "site_label_dataset_digest": companion["dataset_digest"],
        "development_groups": len(source["groups"]),
        "candidate_count": len(geometry),
        "site_occurrence_count": len(label_vectors),
        "geometry_receipt_digest_before_labels": receipt_digest,
        "candidate_spec_count": len(SPECS),
        "selected_spec_index": selected_index,
        "selected_spec": asdict(SPECS[selected_index]),
        "selected_result": selected,
        "frozen_model_digest": model.model_digest,
        "frozen_model_feature_count": len(model.means),
        "frozen_model_training_site_count": len(model.training_rows),
        "frozen_model_length_scale": model.length_scale,
        "all_spec_results": audits,
        "fold_length_scales": tuple(sorted(length_scales.items())),
        "shuffle_trials": SHUFFLES,
        "fully_reselected_shuffle_specs": tuple(null_specs),
        "shuffle_exact_counts": null_exact,
        "shuffle_site_counts": null_sites,
        "shuffle_exact_median": sorted(null_exact)[SHUFFLES // 2],
        "shuffle_exact_maximum": max(null_exact),
        "shuffle_exact_upper_tail_p": exact_p,
        "shuffle_sites_median": sorted(null_sites)[SHUFFLES // 2],
        "shuffle_sites_maximum": max(null_sites),
        "shuffle_sites_upper_tail_p": sites_p,
        "candidate_geometry_changed": False,
        "branches_spliced_or_sites_moved": False,
        "whole_compatible_terminal_remains_commit_unit": True,
        "targets_used_for_receipts_or_ranking": False,
        "expanded_development_consumed": True,
        "fresh_confirmation_opened": False,
        "integrated_as_default_marking": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["site_resolved_exact_action_gate_passed"] = bool(
        exact_p <= .05 and sites_p <= .05 and
        selected["exact"] > max(null_exact) and
        selected["sites"] > max(null_sites))
    return {**body, "audit_digest": _digest(body)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    print(json.dumps(row, indent=2, sort_keys=True) if args.json else
          ("site-resolved exact-action gate passes" if
           row["site_resolved_exact_action_gate_passed"] else
           "site-resolved exact-action gate remains red"))


if __name__ == "__main__":
    main()
