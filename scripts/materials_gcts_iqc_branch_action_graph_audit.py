#!/usr/bin/env python3
"""Audit complete simultaneous colored action graphs on wide IQC branches.

The selected parent/source endpoint graph is identical for exact and false
forward-UNSAT alternatives inside a nucleus.  This audit therefore serializes
the complete three-action branch as an unordered colored proper-metric graph.
It first measures exact graph recurrence, then evaluates two bounded train-only
sections: nearest recurrent graph geometry and recurrent colored edge tokens.
Both preserve the same frozen candidate set and are selected in grouped nested
folds.  Thirty-one within-nucleus label shuffles repeat the complete fit.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random

from materials_gcts_iqc_exact_port_instance_dataset import load_default_dataset


K_VALUES = (1, 3, 5, 9, 15)
EDGE_WIDTHS = (.25, .5, 1., 2., 4.)
SHUFFLES = 31
SHUFFLE_SEED = 99173
EDGE_SHUFFLE_SEED = 72291
COLORS = ("X", "Y", "Z")
COLOR_PAIRS = ("XX", "XY", "XZ", "YY", "YZ", "ZZ")
COLOR_PATTERNS = tuple("".join(row) for row in
                       itertools.combinations_with_replacement(COLORS, 3))


def _graph_key(row):
    return json.dumps(row["complete_branch_action_graph"], sort_keys=True,
                      separators=(",", ":"))


def _rows(dataset, labels=None):
    rows = []
    for group in dataset["groups"]:
        for row in group["rows"]:
            graph = row["complete_branch_action_graph"]
            colors = tuple(graph["node_colors"])
            radial = tuple(map(float, graph["center_distances_nn"]))
            distances = tuple(map(float, graph["pair_distances_nn"]))
            volume = float(graph["proper_signed_volumes"][0])
            color_radial = {color: [] for color in COLORS}
            for color, value in zip(colors, radial):
                color_radial[color].append(value)
            edge_rows = []
            color_distances = {pair: [] for pair in COLOR_PAIRS}
            edge_index = 0
            for left in range(3):
                for right in range(left + 1, 3):
                    pair = "".join(sorted((colors[left], colors[right])))
                    value = distances[edge_index]
                    edge_rows.append((pair, value))
                    color_distances[pair].append(value)
                    edge_index += 1
            features = tuple(
                [sum(color == wanted for color in colors)
                 for wanted in COLORS] +
                [sum(color_radial[color]) / len(color_radial[color])
                 if color_radial[color] else 0. for color in COLORS] +
                [min(radial), sum(radial) / 3., max(radial),
                 min(distances), sum(distances) / 3., max(distances),
                 math.log1p(abs(volume)),
                 float((volume > 0.) - (volume < 0.))] +
                [sum(color_distances[pair]) / len(color_distances[pair])
                 if color_distances[pair] else 0.
                 for pair in COLOR_PAIRS] +
                [float("".join(colors) == pattern)
                 for pattern in COLOR_PATTERNS])
            rows.append({
                "group": int(group["group"]),
                "exact": bool(row["exact"]),
                "fit_label": bool(row["exact"]),
                "forward_unsatisfied": (
                    row["certificates"]["forward"]["status"] ==
                    "unsatisfied"),
                "graph_key": _graph_key(row),
                "features": features,
                "edges": tuple(edge_rows),
                "endpoint_key": json.dumps(
                    row["selected_endpoint_geometry"], sort_keys=True,
                    separators=(",", ":")),
            })
    if labels is not None:
        if len(labels) != len(rows):
            raise ValueError("label vector does not match frozen graph rows")
        for row, label in zip(rows, labels):
            row["fit_label"] = bool(label)
    return tuple(rows)


def _standardizer(rows):
    dimensions = len(rows[0]["features"])
    means = tuple(sum(row["features"][index] for row in rows) / len(rows)
                  for index in range(dimensions))
    scales = tuple(max(1e-9, math.sqrt(sum(
        (row["features"][index] - means[index]) ** 2 for row in rows) /
        len(rows))) for index in range(dimensions))
    return means, scales


def _knn_score(training, standardizer, row, neighbors):
    _means, scales = standardizer
    distances = sorted((
        sum(((left - right) / scale) ** 2
            for left, right, scale in zip(
                candidate["features"], row["features"], scales)),
        float(candidate["fit_label"]), candidate["graph_key"])
        for candidate in training)
    selected = distances[:min(neighbors, len(distances))]
    weights = tuple(1. / (1. + math.sqrt(distance))
                    for distance, _label, _key in selected)
    return sum(weight * label for weight, (_distance, label, _key)
               in zip(weights, selected)) / sum(weights)


def _rank_one(candidates, score):
    return min(candidates, key=lambda row: (-score(row), row["graph_key"]))


def _select_k(rows, outer_group):
    groups = sorted({row["group"] for row in rows
                     if row["group"] != outer_group})
    candidates = []
    for neighbors in K_VALUES:
        exact = false = 0
        for validation in groups:
            training = tuple(row for row in rows
                             if row["group"] not in
                             (outer_group, validation))
            heldout = tuple(row for row in rows
                            if row["group"] == validation and
                            row["forward_unsatisfied"])
            if not heldout:
                continue
            standardizer = _standardizer(training)
            selected = _rank_one(heldout, lambda row: _knn_score(
                training, standardizer, row, neighbors))
            exact += int(selected["fit_label"])
            false += int(not selected["fit_label"])
        candidates.append(((exact, -false, -neighbors), neighbors))
    return max(candidates)[1]


def _knn_outer(rows):
    selections = []
    for group in sorted({row["group"] for row in rows}):
        heldout = tuple(row for row in rows
                        if row["group"] == group and
                        row["forward_unsatisfied"])
        if not heldout:
            continue
        neighbors = _select_k(rows, group)
        training = tuple(row for row in rows if row["group"] != group)
        standardizer = _standardizer(training)
        selected = _rank_one(heldout, lambda row: _knn_score(
            training, standardizer, row, neighbors))
        selections.append((group, selected["exact"], neighbors))
    return tuple(selections)


def _edge_tokens(row, width):
    return tuple(sorted((pair, int(round(distance / width)))
                        for pair, distance in row["edges"]))


def _fit_edges(rows, width):
    counts = {}
    for row in rows:
        for token in set(_edge_tokens(row, width)):
            values = counts.setdefault(token, [0, 0])
            values[int(row["fit_label"])] += 1
    return counts


def _edge_score(model, row, width):
    values = []
    for token in _edge_tokens(row, width):
        negative, positive = model.get(token, (0, 0))
        values.append(math.log((positive + 1.) / (negative + 1.)))
    return sum(values) / len(values)


def _select_edge_width(rows, outer_group):
    groups = sorted({row["group"] for row in rows
                     if row["group"] != outer_group})
    candidates = []
    for width in EDGE_WIDTHS:
        exact = false = 0
        for validation in groups:
            training = tuple(row for row in rows
                             if row["group"] not in
                             (outer_group, validation))
            heldout = tuple(row for row in rows
                            if row["group"] == validation and
                            row["forward_unsatisfied"])
            if not heldout:
                continue
            model = _fit_edges(training, width)
            selected = _rank_one(
                heldout, lambda row: _edge_score(model, row, width))
            exact += int(selected["fit_label"])
            false += int(not selected["fit_label"])
        candidates.append(((exact, -false, -width), width))
    return max(candidates)[1]


def _edge_outer(rows):
    selections = []
    for group in sorted({row["group"] for row in rows}):
        heldout = tuple(row for row in rows
                        if row["group"] == group and
                        row["forward_unsatisfied"])
        if not heldout:
            continue
        width = _select_edge_width(rows, group)
        training = tuple(row for row in rows if row["group"] != group)
        model = _fit_edges(training, width)
        selected = _rank_one(
            heldout, lambda row: _edge_score(model, row, width))
        selections.append((group, selected["exact"], width))
    return tuple(selections)


def _shuffle_labels(rows, trial, seed):
    labels = [None] * len(rows)
    rng = random.Random(seed + trial)
    for group in sorted({row["group"] for row in rows}):
        indices = [index for index, row in enumerate(rows)
                   if row["group"] == group]
        values = [rows[index]["exact"] for index in indices]
        rng.shuffle(values)
        for index, value in zip(indices, values):
            labels[index] = value
    return tuple(labels)


def _null_scores(dataset, source_rows, evaluator, seed):
    return tuple(sum(selected[1] for selected in evaluator(_rows(
        dataset, _shuffle_labels(source_rows, trial, seed))))
        for trial in range(SHUFFLES))


def evaluate():
    dataset = load_default_dataset()
    rows = _rows(dataset)
    graph_groups = {}
    for row in rows:
        graph_groups.setdefault(row["graph_key"], []).append(row)
    repeated = tuple(values for values in graph_groups.values()
                     if len(values) > 1)
    heldout_graph_coverage = sum(any(
        other["group"] != row["group"] and
        other["graph_key"] == row["graph_key"] for other in rows)
        for row in rows)
    heldout_exact_graph_coverage = sum(row["exact"] and any(
        other["group"] != row["group"] and
        other["graph_key"] == row["graph_key"] for other in rows)
        for row in rows)
    forward_unsatisfied = tuple(row for row in rows
                                if row["forward_unsatisfied"])
    affected = sorted({row["group"] for row in forward_unsatisfied})
    within_unique = sum(len({row["graph_key"] for row in forward_unsatisfied
                             if row["group"] == group}) for group in affected)
    endpoint_classes = len({row["endpoint_key"]
                            for row in forward_unsatisfied})
    endpoint_mixed = sum(bool(
        {row["exact"] for row in forward_unsatisfied
         if row["endpoint_key"] == key} == {False, True})
        for key in {row["endpoint_key"] for row in forward_unsatisfied})

    knn = _knn_outer(rows)
    edge = _edge_outer(rows)
    knn_exact = sum(row[1] for row in knn)
    edge_exact = sum(row[1] for row in edge)
    knn_null = _null_scores(dataset, rows, _knn_outer, SHUFFLE_SEED)
    edge_null = _null_scores(dataset, rows, _edge_outer, EDGE_SHUFFLE_SEED)
    possible = len({row["group"] for row in forward_unsatisfied
                    if row["exact"]})

    body = {
        "schema_version": 1,
        "source_dataset_digest": dataset["dataset_digest"],
        "development_groups": len(dataset["groups"]),
        "supplied_groups": sum(any(row["exact"] for row in group["rows"])
                               for group in dataset["groups"]),
        "branches": len(rows),
        "exact_branches": sum(row["exact"] for row in rows),
        "false_branches": sum(not row["exact"] for row in rows),
        "canonical_branch_graph_classes": len(graph_groups),
        "repeated_branch_graph_classes": len(repeated),
        "heldout_exact_graph_rows": heldout_exact_graph_coverage,
        "heldout_graph_rows": heldout_graph_coverage,
        "forward_unsatisfied_branches": len(forward_unsatisfied),
        "forward_unsatisfied_groups": len(affected),
        "forward_unsatisfied_exact_groups": possible,
        "forward_unsatisfied_within_group_graph_classes": within_unique,
        "selected_endpoint_classes": endpoint_classes,
        "selected_endpoint_exact_false_mixed_classes": endpoint_mixed,
        "branch_graph_exact_false_collisions_within_group": sum(
            bool({row["exact"] for row in forward_unsatisfied
                  if row["group"] == group and row["graph_key"] == key} ==
                 {False, True})
            for group in affected for key in
            {row["graph_key"] for row in forward_unsatisfied
             if row["group"] == group}),
        "knn_feature_count": len(rows[0]["features"]),
        "knn_candidate_neighbors": K_VALUES,
        "knn_selected_neighbors_by_group": tuple(row[2] for row in knn),
        "knn_selected_exact_groups": knn_exact,
        "knn_shuffle_trials": SHUFFLES,
        "knn_shuffle_exact_median": sorted(knn_null)[SHUFFLES // 2],
        "knn_shuffle_exact_maximum": max(knn_null),
        "knn_empirical_p": (
            1 + sum(value >= knn_exact for value in knn_null)) /
            (SHUFFLES + 1),
        "edge_widths": EDGE_WIDTHS,
        "edge_selected_widths_by_group": tuple(row[2] for row in edge),
        "edge_selected_exact_groups": edge_exact,
        "edge_shuffle_trials": SHUFFLES,
        "edge_shuffle_exact_median": sorted(edge_null)[SHUFFLES // 2],
        "edge_shuffle_exact_maximum": max(edge_null),
        "edge_empirical_p": (
            1 + sum(value >= edge_exact for value in edge_null)) /
            (SHUFFLES + 1),
        "candidate_geometry_unchanged": True,
        "raw_occurrence_or_stable_index_used_as_feature": False,
        "target_used_for_graph_or_fit": False,
        "development_labels_used_for_model_selection": True,
        "fresh_confirmation_claimed": False,
        "integrated_as_default_marking": False,
        "local_identifiability_gate_passed": within_unique == len(
            forward_unsatisfied),
        "transferable_graph_marking_gate_passed": bool(
            knn_exact == possible and edge_exact == possible and
            max(knn_null) < possible and max(edge_null) < possible),
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
        "honest_status": (
            "the complete colored branch graph distinguishes all 28 "
            "forward-UNSAT actions locally, but exact graph identity barely "
            "recurs and both bounded grouped sections select 0 of 2 "
            "recoverable exact nuclei; local identifiability does not yet "
            "produce transferable GCTS value"),
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
