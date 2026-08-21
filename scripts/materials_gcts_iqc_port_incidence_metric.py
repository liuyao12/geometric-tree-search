#!/usr/bin/env python3
"""Bounded continuous metric over the shared GCTS port-incidence graph.

Exact semantic identity is sparse across IQC nuclei.  This model retains the
same immutable action graphs but compares finite proper-motion-invariant
statistics of their action geometry, witnessed ports, and directed endpoint
incidence.  Nearest-neighbor votes are reduced to at most one vote per training
nucleus so symmetry/candidate multiplicity cannot inflate evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math

from materials_gcts_iqc_port_incidence_quotient import development_rows


COLORS = ("X", "Y", "Z")
DIRECTED_PAIRS = tuple(left + right for left in COLORS for right in COLORS)
UNDIRECTED_PAIRS = ("XX", "XY", "XZ", "YY", "YZ", "ZZ")
RELATIONS = ("same_parent", "same_source",
             "left_source_is_right_parent",
             "right_source_is_left_parent", "touch")
FEATURE_VARIANTS = (
    "geometry", "roles", "pose", "environment", "incidence",
    "roles+pose", "roles+incidence", "pose+incidence",
    "roles+pose+incidence", "ports", "all",
)
K_VALUES = (3, 5, 9, 13)
WEIGHTED = (False, True)
ADMISSION_THRESHOLDS = (.5, .6, .7, .8, .9)
PRECISION_FLOOR = .95
_STANDARDIZER_CACHE = {}
_NEIGHBOR_RECEIPT_CACHE = {}


@dataclass(frozen=True)
class PortGraphMetricSpec:
    feature_variant: str
    neighbors: int
    weighted: bool
    admission_threshold: float


@dataclass(frozen=True)
class PortGraphMetricSelection:
    spec: PortGraphMetricSpec
    supplied_groups: int
    selected_exact_groups: int
    selected_groups: int
    selected_precision: float
    supplied_recall: float
    correct_sites: int
    maximum_correct_sites: int


@dataclass(frozen=True)
class FrozenPortGraphMetric:
    spec: PortGraphMetricSpec
    feature_indices: tuple[int, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    training_rows: tuple[dict, ...]
    model_digest: str


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _symbol(value):
    return str(value).strip("'\"")


def _stats(values):
    values = tuple(map(float, values))
    if not values:
        return (0., 0., 0.)
    return (min(values), sum(values) / len(values), max(values))


def _determinant(vectors):
    first, second, third = vectors
    cross = (second[1] * third[2] - second[2] * third[1],
             second[2] * third[0] - second[0] * third[2],
             second[0] * third[1] - second[1] * third[0])
    return sum(left * right for left, right in zip(first, cross))


def graph_features(graph):
    nodes = tuple(graph["nodes"])
    edges = tuple(graph["edges"])
    center = tuple(map(float, graph["center_local_nn"]))

    node_colors = tuple(_symbol(node["species"]) for node in nodes)
    radial = tuple(float(node["center_distance_nn"]) for node in nodes)
    edge_by_pair = {pair: [] for pair in UNDIRECTED_PAIRS}
    for edge in edges:
        left, right = edge["nodes"]
        pair = "".join(sorted((node_colors[left], node_colors[right])))
        edge_by_pair[pair].append(float(edge["distance_nn"]))
    vectors = tuple(tuple(float(node["local_nn"][axis]) - center[axis]
                          for axis in range(3)) for node in nodes)
    volume = _determinant(vectors)
    geometry = (
        tuple(float(node_colors.count(color)) for color in COLORS) +
        _stats(radial) +
        tuple(float(len(edge_by_pair[pair])) for pair in UNDIRECTED_PAIRS) +
        tuple(_stats(edge_by_pair[pair])[1] for pair in UNDIRECTED_PAIRS) +
        _stats(edge["distance_nn"] for edge in edges) +
        (math.log1p(abs(volume)),
         float((volume > 1e-8) - (volume < -1e-8)))
    )

    ports = tuple(port for node in nodes for port in node["incoming_ports"])
    node_port_counts = tuple(len(node["incoming_ports"]) for node in nodes)
    state_pairs = tuple(_symbol(port["state"]["parent_species"]) +
                        _symbol(port["state"]["source_species"])
                        for port in ports)
    endpoint_pairs = tuple(_symbol(port["parent_species"]) +
                           _symbol(port["source_species"]) for port in ports)
    separations = tuple(float(port["state"]["separation_bin"])
                        for port in ports)
    port_geometry = [[] for _ in range(5)]
    parent_last, source_last, parent_total, source_total = [], [], [], []
    for node in nodes:
        action = tuple(map(float, node["local_nn"]))
        for port in node["incoming_ports"]:
            parent = tuple(map(float, port["parent_local_nn"]))
            source = tuple(map(float, port["source_local_nn"]))
            values = (math.dist(action, parent), math.dist(action, source),
                      math.dist(parent, source), math.dist(center, parent),
                      math.dist(center, source))
            for bucket, value in zip(port_geometry, values):
                bucket.append(value)
            parent_counts = tuple(map(float,
                port["state"]["parent_radial_counts"]))
            source_counts = tuple(map(float,
                port["state"]["source_radial_counts"]))
            parent_last.append(parent_counts[-1]); source_last.append(source_counts[-1])
            parent_total.append(sum(parent_counts)); source_total.append(sum(source_counts))
    role_features = (
        (float(len(ports)),) + _stats(node_port_counts) +
        tuple(float(state_pairs.count(pair)) for pair in DIRECTED_PAIRS) +
        tuple(float(endpoint_pairs.count(pair)) for pair in DIRECTED_PAIRS)
    )
    pose_features = (
        _stats(separations) +
        tuple(value for bucket in port_geometry for value in _stats(bucket))
    )
    environment_features = (
        _stats(parent_last) + _stats(source_last) +
        _stats(parent_total) + _stats(source_total)
    )

    relation_counts = {relation: 0 for relation in RELATIONS}
    relation_metric = {relation: [] for relation in RELATIONS}
    cross_distances, pairs_per_edge, touched_edges = [], [], 0
    for edge in edges:
        pairs_per_edge.append(len(edge["port_pair_relations"]))
        edge_touched = False
        for row in edge["port_pair_relations"]:
            distances = tuple(map(float, row["endpoint_distances_nn"]))
            cross_distances.extend(distances)
            for relation in row["relations"]:
                relation_counts[relation] += 1
                relation_metric[relation].append(sum(distances) / 4.)
                edge_touched = True
        touched_edges += int(edge_touched)
    incidence = (
        tuple(float(relation_counts[relation]) for relation in RELATIONS) +
        tuple(_stats(relation_metric[relation])[1] for relation in RELATIONS) +
        _stats(cross_distances) + _stats(pairs_per_edge) +
        (float(touched_edges),)
    )
    groups = {"geometry": geometry, "roles": role_features,
              "pose": pose_features, "environment": environment_features,
              "incidence": incidence}
    names, values, ranges, cursor = [], [], {}, 0
    for group in ("geometry", "roles", "pose", "environment", "incidence"):
        group_values = tuple(map(float, groups[group]))
        ranges[group] = tuple(range(cursor, cursor + len(group_values)))
        names.extend(f"{group}-{index}" for index in range(len(group_values)))
        values.extend(group_values)
        cursor += len(group_values)
    return tuple(names), tuple(values), ranges


def metric_rows(labels=None):
    rows = []
    for source in development_rows():
        names, features, ranges = graph_features(source["graph"])
        rows.append({**source, "features": features,
                     "feature_names": names, "feature_ranges": ranges,
                     "correct_sites": 3 if source["exact"] else 0})
    if labels is not None:
        if len(labels) != len(rows):
            raise ValueError("metric labels do not align")
        for row, label in zip(rows, labels):
            row["fit_label"] = bool(label)
    return tuple(rows)


def feature_indices(row, variant):
    groups = ("roles", "pose", "environment") if variant == "ports" else \
        (("geometry", "roles", "pose", "environment", "incidence")
         if variant == "all" else tuple(variant.split("+")))
    return tuple(index for group in groups
                 for index in row["feature_ranges"][group])


def _standardizer(rows, indices):
    means = tuple(sum(row["features"][index] for row in rows) / len(rows)
                  for index in indices)
    scales = tuple(max(1e-9, math.sqrt(sum(
        (row["features"][index] - mean) ** 2 for row in rows) / len(rows)))
                   for index, mean in zip(indices, means))
    return means, scales


def _geometry_signature(rows):
    return tuple((str(row["candidate_id"]),
                  str(row["graph"]["canonical_digest"])) for row in rows)


def _neighbor_receipt(rows, heldout_group, test_row, feature_variant,
                      neighbors, weighted):
    signature = _geometry_signature(rows)
    cache_key = (signature, int(heldout_group), str(test_row["candidate_id"]),
                 feature_variant, int(neighbors), bool(weighted))
    if cache_key in _NEIGHBOR_RECEIPT_CACHE:
        return _NEIGHBOR_RECEIPT_CACHE[cache_key]
    indices = feature_indices(rows[0], feature_variant)
    standardizer_key = (signature, int(heldout_group), feature_variant)
    if standardizer_key not in _STANDARDIZER_CACHE:
        training = tuple(row for row in rows
                         if row["group"] != heldout_group)
        _STANDARDIZER_CACHE[standardizer_key] = _standardizer(
            training, indices)
    _means, scales = _STANDARDIZER_CACHE[standardizer_key]
    values = tuple(test_row["features"][index] for index in indices)
    nearest_by_group = {}
    for candidate in rows:
        if candidate["group"] == heldout_group:
            continue
        candidate_values = tuple(candidate["features"][index]
                                 for index in indices)
        distance = sum(((left - right) / scale) ** 2
                       for left, right, scale in zip(
                           candidate_values, values, scales))
        record = (distance, str(candidate["candidate_id"]))
        prior = nearest_by_group.get(candidate["group"])
        if prior is None or record < prior:
            nearest_by_group[candidate["group"]] = record
    nearest = sorted(nearest_by_group.values())[:neighbors]
    receipt = tuple((candidate_id,
                     1. / (1. + math.sqrt(distance)) if weighted else 1.)
                    for distance, candidate_id in nearest)
    _NEIGHBOR_RECEIPT_CACHE[cache_key] = receipt
    return receipt


def fit_metric(rows, spec):
    indices = feature_indices(rows[0], spec.feature_variant)
    means, scales = _standardizer(rows, indices)
    detached = tuple({
        "group": int(row["group"]),
        "candidate_id": str(row["candidate_id"]),
        "fit_label": bool(row["fit_label"]),
        "features": tuple(row["features"][index] for index in indices),
    } for row in rows)
    body = {"spec": asdict(spec), "indices": indices, "means": means,
            "scales": scales, "training": detached}
    return FrozenPortGraphMetric(
        spec, indices, means, scales, detached, _digest(body))


def score(model, row):
    values = tuple(row["features"][index] for index in model.feature_indices)
    nearest_by_group = {}
    for candidate in model.training_rows:
        distance = sum(((left - right) / scale) ** 2
                       for left, right, scale in zip(
                           candidate["features"], values, model.scales))
        record = (distance, candidate["candidate_id"],
                  float(candidate["fit_label"]))
        prior = nearest_by_group.get(candidate["group"])
        if prior is None or record[:2] < prior[:2]:
            nearest_by_group[candidate["group"]] = record
    nearest = sorted(nearest_by_group.values())[:model.spec.neighbors]
    if not nearest:
        return 0.
    weights = tuple(1. / (1. + math.sqrt(distance))
                    if model.spec.weighted else 1. for distance, _id, _label
                    in nearest)
    return sum(weight * row[-1] for weight, row in zip(weights, nearest)) / \
        sum(weights)


def all_specs():
    return tuple(PortGraphMetricSpec(*values) for values in itertools.product(
        FEATURE_VARIANTS, K_VALUES, WEIGHTED, ADMISSION_THRESHOLDS))


def cross_validate(rows, spec):
    selected = []
    for heldout in sorted({row["group"] for row in rows}):
        testing = tuple(row for row in rows if row["group"] == heldout)
        if not testing:
            continue
        training = tuple(row for row in rows if row["group"] != heldout)
        model = fit_metric(training, spec)
        ranked = tuple(sorted(((score(model, row), row) for row in testing),
                              key=lambda pair: (-pair[0],
                                                pair[1]["candidate_id"])))
        if ranked and ranked[0][0] >= spec.admission_threshold:
            selected.append(ranked[0][1])
    supplied = sum(any(row["exact"] for row in rows if row["group"] == group)
                   for group in {row["group"] for row in rows})
    exact = sum(row["exact"] for row in selected)
    return PortGraphMetricSelection(
        spec, supplied, exact, len(selected),
        exact / len(selected) if selected else 0.,
        exact / supplied if supplied else 0.,
        sum(row["correct_sites"] for row in selected), supplied * 3)


def _ranked_loocv(rows, feature_variant, neighbors, weighted):
    labels = {str(row["candidate_id"]): float(row["fit_label"])
              for row in rows}
    ranked = []
    for heldout in sorted({row["group"] for row in rows}):
        testing = tuple(row for row in rows if row["group"] == heldout)
        if not testing:
            continue
        scored = []
        for row in testing:
            receipt = _neighbor_receipt(
                rows, heldout, row, feature_variant, neighbors, weighted)
            value = sum(weight * labels[candidate_id]
                        for candidate_id, weight in receipt) / sum(
                            weight for _candidate_id, weight in receipt)
            scored.append((value, row))
        order = tuple(sorted(scored,
                             key=lambda pair: (-pair[0],
                                               pair[1]["candidate_id"])))
        ranked.append((heldout, order[0][0], order[0][1]))
    return tuple(ranked)


def _selection_from_ranked(rows, spec, ranked):
    selected = tuple(row for _group, value, row in ranked
                     if value >= spec.admission_threshold)
    supplied = sum(any(row["exact"] for row in rows if row["group"] == group)
                   for group in {row["group"] for row in rows})
    exact = sum(row["exact"] for row in selected)
    return PortGraphMetricSelection(
        spec, supplied, exact, len(selected),
        exact / len(selected) if selected else 0.,
        exact / supplied if supplied else 0.,
        sum(row["correct_sites"] for row in selected), supplied * 3)


def select_spec(rows):
    audits = []
    for feature_variant, neighbors, weighted in itertools.product(
            FEATURE_VARIANTS, K_VALUES, WEIGHTED):
        ranked = _ranked_loocv(rows, feature_variant, neighbors, weighted)
        for threshold in ADMISSION_THRESHOLDS:
            spec = PortGraphMetricSpec(
                feature_variant, neighbors, weighted, threshold)
            audits.append(_selection_from_ranked(rows, spec, ranked))
    audits = tuple(audits)
    precise = tuple(row for row in audits if row.selected_groups
                    and row.selected_precision >= PRECISION_FLOOR)
    pool = precise or audits
    selected = max(pool, key=lambda row: (
        row.selected_exact_groups, row.correct_sites,
        row.selected_precision, -row.selected_groups,
        -len(feature_indices(rows[0], row.spec.feature_variant)),
        -row.spec.neighbors, not row.spec.weighted,
        row.spec.admission_threshold, row.spec.feature_variant))
    return selected, audits


__all__ = [
    "ADMISSION_THRESHOLDS", "FEATURE_VARIANTS", "K_VALUES", "PRECISION_FLOOR",
    "PortGraphMetricSelection", "PortGraphMetricSpec", "FrozenPortGraphMetric",
    "all_specs", "cross_validate", "feature_indices", "fit_metric",
    "graph_features", "metric_rows", "score", "select_spec",
]
