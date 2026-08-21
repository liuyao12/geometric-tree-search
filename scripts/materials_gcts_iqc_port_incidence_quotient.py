#!/usr/bin/env python3
"""Learn a bounded recurrent quotient of shared IQC port-incidence graphs.

Both development and wide branches use the same ID-free graph schema.  This
module learns only a semantic marking key; every exact colored geometry and
production alternative remains immutable.  Capacity is selected by complete
leave-one-nucleus-out refits and repeated under within-nucleus label shuffles.
Unknown semantic types fail closed rather than inheriting a global positive
rate.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math
import random

from materials_gcts_iqc_recurrent_macro_geometry_dataset import load_fixture
from materials_gcts_port_incidence_graph import (
    development_geometry_to_incidence_graph)


DISTANCE_WIDTHS = (1., 2., 4., 8.)
STATE_WIDTHS = (0, 4)
RADIAL_MODES = ("none",)
ACTION_GEOMETRY = (False, True)
PORT_GEOMETRY = (False, True)
METRIC_RELATIONS = (False, True)
PRESERVE_MULTIPLICITY = (False, True)
MINIMUM_GROUPS = (2, 3)
ADMISSION_POSTERIOR = .5
SHUFFLES = 31
SHUFFLE_SEED = 721_901
_SEMANTIC_KEY_CACHE = {}


@dataclass(frozen=True)
class PortIncidenceSpec:
    distance_width: float
    state_width: int
    radial_mode: str
    action_geometry: bool
    port_geometry: bool
    metric_relations: bool
    preserve_multiplicity: bool
    minimum_groups: int


@dataclass(frozen=True)
class PortIncidenceSelection:
    spec: PortIncidenceSpec
    supplied_groups: int
    selected_exact_groups: int
    selected_groups: int
    selected_precision: float
    supplied_group_recall: float
    recognized_candidates: int
    recognized_exact_candidates: int
    exact_candidates: int
    exact_candidate_coverage: float
    recognized_types: int


@dataclass(frozen=True)
class FrozenPortIncidenceType:
    type_id: str
    semantic_key: tuple
    training_groups: tuple[int, ...]
    positive_occurrences: int
    negative_occurrences: int
    posterior: float
    exact_graph_alternatives: tuple[str, ...]
    exact_derivation_alternatives: tuple[str, ...]


@dataclass(frozen=True)
class FrozenPortIncidenceQuotient:
    spec: PortIncidenceSpec
    types: tuple[FrozenPortIncidenceType, ...]
    model_digest: str


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _symbol(value):
    return str(value).strip("'\"")


def _bin(value, width):
    return int(round(float(value) / float(width)))


def _radial_code(values, mode):
    values = tuple(map(int, values))
    if mode == "none":
        return ()
    if mode == "summary":
        quarters = tuple(sum(values[index:index + 3])
                         for index in range(0, len(values), 3))
        return quarters + (values[-1], sum(values))
    raise ValueError(f"unknown radial mode {mode}")


def _port_code(node, port, center, spec):
    state = port["state"]
    action = tuple(map(float, node["local_nn"]))
    parent = tuple(map(float, port["parent_local_nn"]))
    source = tuple(map(float, port["source_local_nn"]))
    geometry = tuple(_bin(value, spec.distance_width) for value in (
        math.dist(action, parent), math.dist(action, source),
        math.dist(parent, source), math.dist(center, parent),
        math.dist(center, source))) if spec.port_geometry else ()
    return (
        _symbol(state["parent_species"]),
        _symbol(state["source_species"]),
        (int(round(int(state["separation_bin"]) / spec.state_width))
         if spec.state_width else 0),
        _radial_code(state["parent_radial_counts"], spec.radial_mode),
        _radial_code(state["source_radial_counts"], spec.radial_mode),
        _symbol(port["parent_species"]), _symbol(port["source_species"]),
        geometry,
    )


def _edge_code(edge, spec):
    relations = []
    for row in edge["port_pair_relations"]:
        role = tuple(row["relations"])
        metric = tuple(_bin(value, spec.distance_width)
                       for value in row["endpoint_distances_nn"]) \
            if spec.metric_relations else ()
        relations.append((role, metric))
    if not spec.preserve_multiplicity:
        relations = set(relations)
    return ((_bin(edge["distance_nn"], spec.distance_width)
             if spec.action_geometry else 0), tuple(sorted(relations)))


def semantic_key(graph, spec):
    """Canonical bounded port graph; chirality is retained as a sign."""
    nodes = tuple(graph["nodes"])
    center = tuple(map(float, graph["center_local_nn"]))
    edge_map = {tuple(edge["nodes"]): edge for edge in graph["edges"]}
    vectors = [tuple(float(node["local_nn"][axis]) - center[axis]
                     for axis in range(3)) for node in nodes]
    cross = (vectors[1][1] * vectors[2][2] -
             vectors[1][2] * vectors[2][1],
             vectors[1][2] * vectors[2][0] -
             vectors[1][0] * vectors[2][2],
             vectors[1][0] * vectors[2][1] -
             vectors[1][1] * vectors[2][0])
    volume = sum(left * right for left, right in zip(vectors[0], cross))
    chirality = 1 if volume > 1e-8 else -1 if volume < -1e-8 else 0
    codes = []
    for order in itertools.permutations(range(3)):
        node_codes = []
        for index in order:
            ports = tuple(_port_code(nodes[index], port, center, spec)
                          for port in nodes[index]["incoming_ports"])
            if not spec.preserve_multiplicity:
                ports = tuple(set(ports))
            node_codes.append((
                _symbol(nodes[index]["species"]),
                (_bin(nodes[index]["center_distance_nn"], spec.distance_width)
                 if spec.action_geometry else 0),
                tuple(sorted(ports)),
            ))
        node_codes = tuple(node_codes)
        edge_codes = []
        for left in range(3):
            for right in range(left + 1, 3):
                pair = tuple(sorted((order[left], order[right])))
                edge_codes.append(_edge_code(edge_map[pair], spec))
        # Odd node permutations reverse the ordered signed volume.
        inversions = sum(order[left] > order[right]
                         for left in range(3) for right in range(left + 1, 3))
        signed = chirality if inversions % 2 == 0 else -chirality
        codes.append((node_codes, tuple(edge_codes), signed))
    return min(codes)


def _cached_semantic_key(row, spec):
    cache_key = (str(row["candidate_id"]),
                 str(row["graph"]["canonical_digest"]), spec)
    if cache_key not in _SEMANTIC_KEY_CACHE:
        _SEMANTIC_KEY_CACHE[cache_key] = semantic_key(row["graph"], spec)
    return _SEMANTIC_KEY_CACHE[cache_key]


def development_rows(labels=None):
    payload = load_fixture()
    rows = []
    for group in payload["groups"]:
        for row in group["rows"]:
            rows.append({
                "group": int(group["group"]),
                "candidate_id": str(row["candidate_id"]),
                "exact": bool(row["exact"]),
                "fit_label": bool(row["exact"]),
                "graph": development_geometry_to_incidence_graph(
                    row["geometry"]),
                "derivation_alternatives": tuple(
                    row["production_alternative_ids"]),
            })
    if labels is not None:
        if len(labels) != len(rows):
            raise ValueError("shuffled labels do not align")
        for row, label in zip(rows, labels):
            row["fit_label"] = bool(label)
    return tuple(rows)


def fit_port_incidence_quotient(rows, spec, key_cache=None):
    key_cache = key_cache or {
        row["candidate_id"]: _cached_semantic_key(row, spec) for row in rows}
    grouped = defaultdict(list)
    for row in rows:
        grouped[key_cache[row["candidate_id"]]].append(row)
    types = []
    for key, occurrences in grouped.items():
        groups = tuple(sorted({row["group"] for row in occurrences}))
        if len(groups) < spec.minimum_groups:
            continue
        positive = sum(row["fit_label"] for row in occurrences)
        negative = len(occurrences) - positive
        types.append(FrozenPortIncidenceType(
            _digest(key), key, groups, positive, negative,
            (positive + 1.) / (len(occurrences) + 2.),
            tuple(sorted({row["graph"]["canonical_digest"]
                          for row in occurrences})),
            tuple(sorted({alternative for row in occurrences
                          for alternative in row["derivation_alternatives"]})),
        ))
    types = tuple(sorted(types, key=lambda row: row.type_id))
    body = {"spec": asdict(spec),
            "types": tuple(asdict(row) for row in types)}
    return FrozenPortIncidenceQuotient(spec, types, _digest(body))


def score(model, graph, key=None):
    key = semantic_key(graph, model.spec) if key is None else key
    match = next((row for row in model.types if row.semantic_key == key), None)
    return None if match is None else match.posterior


def _select_one(model, rows, key_cache=None):
    known = tuple((score(model, row["graph"],
                         None if key_cache is None else
                         key_cache[row["candidate_id"]]), row) for row in rows)
    known = tuple(pair for pair in known if pair[0] is not None)
    if not known:
        return None
    value, selected = min(known, key=lambda pair: (
        -pair[0], pair[1]["candidate_id"]))
    return selected if value >= ADMISSION_POSTERIOR else None


def cross_validate(rows, spec):
    key_cache = {row["candidate_id"]: _cached_semantic_key(row, spec)
                 for row in rows}
    groups = tuple(sorted({row["group"] for row in rows}))
    selected = []
    recognized = recognized_exact = exact = 0
    type_ids = set()
    for heldout in groups:
        training = tuple(row for row in rows if row["group"] != heldout)
        testing = tuple(row for row in rows if row["group"] == heldout)
        model = fit_port_incidence_quotient(training, spec, key_cache)
        known = {row.semantic_key: row.type_id for row in model.types}
        for row in testing:
            exact += int(row["exact"])
            key = key_cache[row["candidate_id"]]
            if key in known:
                recognized += 1
                recognized_exact += int(row["exact"])
                type_ids.add(known[key])
        choice = _select_one(model, testing, key_cache)
        if choice is not None:
            selected.append(choice)
    supplied = sum(any(row["exact"] for row in rows if row["group"] == group)
                   for group in groups)
    correct = sum(row["exact"] for row in selected)
    return PortIncidenceSelection(
        spec, supplied, correct, len(selected),
        correct / len(selected) if selected else 0.,
        correct / supplied if supplied else 0., recognized,
        recognized_exact, exact, recognized_exact / exact if exact else 0.,
        len(type_ids))


def all_specs():
    return tuple(PortIncidenceSpec(*values) for values in itertools.product(
        DISTANCE_WIDTHS, STATE_WIDTHS, RADIAL_MODES, ACTION_GEOMETRY,
        PORT_GEOMETRY, METRIC_RELATIONS, PRESERVE_MULTIPLICITY,
        MINIMUM_GROUPS))


def select_spec(rows):
    audits = tuple(cross_validate(rows, spec) for spec in all_specs())
    precise = tuple(row for row in audits if row.selected_groups
                    and row.selected_precision >= .95)
    pool = precise or audits
    selected = max(pool, key=lambda row: (
        row.selected_exact_groups, row.selected_precision,
        row.recognized_exact_candidates,
        -row.recognized_candidates + row.recognized_exact_candidates,
        row.recognized_types, -row.spec.distance_width,
        -row.spec.state_width, not row.spec.action_geometry,
        not row.spec.port_geometry,
        row.spec.radial_mode == "none",
        not row.spec.metric_relations, not row.spec.preserve_multiplicity,
        row.spec.minimum_groups))
    return selected, audits


def shuffled_labels(rows, trial):
    labels = [None] * len(rows)
    rng = random.Random(SHUFFLE_SEED + trial)
    for group in sorted({row["group"] for row in rows}):
        indices = [index for index, row in enumerate(rows)
                   if row["group"] == group]
        values = [rows[index]["fit_label"] for index in indices]
        rng.shuffle(values)
        for index, value in zip(indices, values):
            labels[index] = value
    return tuple(labels)


def evaluate():
    rows = development_rows()
    selected, audits = select_spec(rows)
    model = fit_port_incidence_quotient(rows, selected.spec)
    null = []
    for trial in range(SHUFFLES):
        labels = shuffled_labels(rows, trial)
        shuffled = tuple({**row, "fit_label": bool(label)}
                         for row, label in zip(rows, labels))
        choice, _ = select_spec(shuffled)
        null.append(choice)
    null_exact = tuple(row.selected_exact_groups for row in null)
    p_value = (1 + sum(value >= selected.selected_exact_groups
                       for value in null_exact)) / (SHUFFLES + 1)
    body = {
        "development_rows": len(rows),
        "development_groups": len({row["group"] for row in rows}),
        "selected": asdict(selected),
        "model_types": len(model.types),
        "model_digest": model.model_digest,
        "capacity_audits": len(audits),
        "shuffle_trials": SHUFFLES,
        "shuffle_exact_median": sorted(null_exact)[SHUFFLES // 2],
        "shuffle_exact_maximum": max(null_exact),
        "exact_empirical_p": p_value,
        "unknown_types_fail_closed": True,
        "same_common_schema_required_for_external_transfer": True,
        "integrated_as_default_marking": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    body["development_gate_passed"] = bool(
        selected.selected_exact_groups == selected.supplied_groups
        and selected.selected_precision >= .95 and p_value <= .05)
    body["audit_digest"] = _digest(body)
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else
          ("port-incidence quotient passes development" if
           report["development_gate_passed"] else
           "port-incidence quotient remains below development gate"))


if __name__ == "__main__":
    main()
