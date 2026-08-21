#!/usr/bin/env python3
"""Finite train-fitted quotient of a proper-SE(3) port-incidence graph.

The exact graph remains the execution identity.  This module builds only a
bounded marking representation: canonical action nodes receive messages from
their witnessed ports and canonical action-pair edges receive messages from
port-endpoint incidences.  Continuous invariant measurements are quantized by
training-only cut points.  A state is admitted only when it recurs in a fixed
number of independent training groups, and every group contributes one mean
label rather than one vote per symmetric occurrence.

No target, family, lattice coordinate, raw occurrence identifier, or absolute
frame enters the public API.  The finite quotient may rank an existing exact
candidate; it cannot authorize or alter candidate geometry.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
import math

from materials_gcts_port_incidence_graph import ENDPOINT_RELATIONS


_FEATURE_CACHE = {}
_CUTPOINT_CACHE = {}


@dataclass(frozen=True, order=True)
class RelationalMessageSpec:
    feature_domain: str
    bins: int
    minimum_groups: int
    top_tokens: int
    aggregation: str
    admission_threshold: float


@dataclass(frozen=True)
class FiniteRelationalState:
    feature_name: str
    bin_index: int
    training_groups: tuple[int, ...]
    group_positive_rates: tuple[float, ...]
    posterior: float


@dataclass(frozen=True)
class FrozenRelationalPortQuotient:
    spec: RelationalMessageSpec
    species_palette: tuple[str, ...]
    feature_names: tuple[str, ...]
    feature_domains: tuple[str, ...]
    cutpoints: tuple[tuple[float, ...], ...]
    states: tuple[FiniteRelationalState, ...]
    model_digest: str
    target_used: bool = False
    candidate_geometry_changed: bool = False


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _symbol(value) -> str:
    return str(value).strip("'\"")


def _stats(values):
    values = tuple(map(float, values))
    if not values:
        return (0., 0., 0.)
    return min(values), sum(values) / len(values), max(values)


def species_palette(graphs):
    values = set()
    for graph in graphs:
        for node in graph["nodes"]:
            values.add(_symbol(node["species"]))
            for port in node["incoming_ports"]:
                values.update((_symbol(port["state"]["parent_species"]),
                               _symbol(port["state"]["source_species"]),
                               _symbol(port["parent_species"]),
                               _symbol(port["source_species"])))
    if not values:
        raise ValueError("port graph corpus has no species roles")
    return tuple(sorted(values))


def relational_message_features(graph, palette):
    """Return an identity-preserving finite-message feature schema.

    The shared graph has three canonical action nodes.  Node messages preserve
    which canonical action owns every incoming role and pose statistic; edge
    messages preserve which canonical action pair owns each endpoint-incidence
    statistic.  This is deliberately richer than a graph-wide histogram.
    """
    nodes = tuple(graph["nodes"])
    edges = tuple(graph["edges"])
    if len(nodes) != 3 or len(edges) != 3:
        raise ValueError("bounded relational quotient requires 3 nodes/3 edges")
    center = tuple(map(float, graph["center_local_nn"]))
    directed_pairs = tuple(left + right for left in palette for right in palette)
    names, domains, values = [], [], []

    def add(name, value, domain):
        names.append(name); values.append(float(value)); domains.append(domain)

    for node_index, node in enumerate(nodes):
        prefix = f"node{node_index}"
        node_species = _symbol(node["species"])
        for role in palette:
            add(f"{prefix}.species.{role}", node_species == role, "nodes")
        ports = tuple(node["incoming_ports"])
        add(f"{prefix}.center-distance", node["center_distance_nn"], "nodes")
        add(f"{prefix}.port-count", len(ports), "nodes")
        state_pairs = tuple(_symbol(port["state"]["parent_species"]) +
                            _symbol(port["state"]["source_species"])
                            for port in ports)
        endpoint_pairs = tuple(_symbol(port["parent_species"]) +
                               _symbol(port["source_species"])
                               for port in ports)
        for pair in directed_pairs:
            add(f"{prefix}.state-role.{pair}", state_pairs.count(pair), "nodes")
        for pair in directed_pairs:
            add(f"{prefix}.endpoint-role.{pair}", endpoint_pairs.count(pair), "nodes")
        for statistic, value in zip(("min", "mean", "max"), _stats(
                port["state"]["separation_bin"] for port in ports)):
            add(f"{prefix}.separation.{statistic}", value, "nodes")

        action = tuple(map(float, node["local_nn"]))
        geometry = {name: [] for name in (
            "action-parent", "action-source", "parent-source",
            "center-parent", "center-source")}
        parent_total, source_total, parent_outer, source_outer = [], [], [], []
        for port in ports:
            parent = tuple(map(float, port["parent_local_nn"]))
            source = tuple(map(float, port["source_local_nn"]))
            for name, value in zip(geometry, (
                    math.dist(action, parent), math.dist(action, source),
                    math.dist(parent, source), math.dist(center, parent),
                    math.dist(center, source))):
                geometry[name].append(value)
            parent_counts = tuple(map(float,
                port["state"]["parent_radial_counts"]))
            source_counts = tuple(map(float,
                port["state"]["source_radial_counts"]))
            parent_total.append(sum(parent_counts)); source_total.append(sum(source_counts))
            parent_outer.append(parent_counts[-1]); source_outer.append(source_counts[-1])
        for name, bucket in geometry.items():
            for statistic, value in zip(("min", "mean", "max"), _stats(bucket)):
                add(f"{prefix}.{name}.{statistic}", value, "nodes")
        for name, bucket in (("parent-total", parent_total),
                             ("source-total", source_total),
                             ("parent-outer", parent_outer),
                             ("source-outer", source_outer)):
            for statistic, value in zip(("min", "mean", "max"), _stats(bucket)):
                add(f"{prefix}.{name}.{statistic}", value, "nodes")

    for edge in edges:
        left, right = map(int, edge["nodes"])
        prefix = f"edge{left}-{right}"
        relations = tuple(edge["port_pair_relations"])
        add(f"{prefix}.action-distance", edge["distance_nn"], "edges")
        add(f"{prefix}.port-pair-count", len(relations), "edges")
        for relation in ENDPOINT_RELATIONS:
            add(f"{prefix}.relation.{relation}", sum(
                relation in row["relations"] for row in relations), "edges")
        for endpoint in range(4):
            for statistic, value in zip(("min", "mean", "max"), _stats(
                    row["endpoint_distances_nn"][endpoint]
                    for row in relations)):
                add(f"{prefix}.endpoint{endpoint}.{statistic}", value, "edges")
    return tuple(names), tuple(values), tuple(domains)


def _cached_features(graph, palette):
    key = (str(graph.get("canonical_digest", "")), tuple(palette))
    if key[0] and key in _FEATURE_CACHE:
        return _FEATURE_CACHE[key]
    result = relational_message_features(graph, palette)
    if key[0]:
        _FEATURE_CACHE[key] = result
    return result


def _feature_indices(domains, feature_domain):
    if feature_domain not in {"nodes", "edges", "all"}:
        raise ValueError(f"unknown feature domain {feature_domain}")
    return tuple(index for index, domain in enumerate(domains)
                 if feature_domain == "all" or domain == feature_domain)


def _cutpoints(rows, indices, bins):
    if bins < 2:
        raise ValueError("finite quotient needs at least two bins")
    result = []
    for index in indices:
        ordered = sorted(float(row["features"][index]) for row in rows)
        cuts = tuple(ordered[min(len(ordered) - 1,
                                 quotient * len(ordered) // bins)]
                     for quotient in range(1, bins))
        result.append(cuts)
    return tuple(result)


def _tokens(features, indices, names, cuts):
    return tuple((names[index], sum(float(features[index]) > cut
                                    for cut in feature_cuts))
                 for index, feature_cuts in zip(indices, cuts))


def fit_relational_port_quotient(rows, spec, *, palette=None):
    rows = tuple(rows)
    if not rows:
        raise ValueError("cannot fit an empty relational corpus")
    if spec.minimum_groups < 2 or spec.top_tokens < 1:
        raise ValueError("invalid recurrence capacity")
    palette = species_palette(row["graph"] for row in rows) if palette is None else tuple(palette)
    prepared = []
    schema = None
    for row in rows:
        names, values, domains = _cached_features(row["graph"], palette)
        if schema is None:
            schema = names, domains
        elif schema != (names, domains):
            raise AssertionError("relational feature schemas do not align")
        prepared.append({**row, "features": values})
    names, domains = schema
    indices = _feature_indices(domains, spec.feature_domain)
    cut_key = (tuple(str(row["graph"].get("canonical_digest", ""))
                     for row in rows), indices, spec.bins)
    if all(cut_key[0]) and cut_key in _CUTPOINT_CACHE:
        cuts = _CUTPOINT_CACHE[cut_key]
    else:
        cuts = _cutpoints(prepared, indices, spec.bins)
        if all(cut_key[0]):
            _CUTPOINT_CACHE[cut_key] = cuts
    observations = defaultdict(lambda: defaultdict(list))
    for row in prepared:
        for token in _tokens(row["features"], indices, names, cuts):
            observations[token][int(row["group"])].append(
                float(bool(row["fit_label"])))
    states = []
    for (name, bin_index), by_group in observations.items():
        if len(by_group) < spec.minimum_groups:
            continue
        groups = tuple(sorted(by_group))
        rates = tuple(sum(by_group[group]) / len(by_group[group])
                      for group in groups)
        posterior = (1. + sum(rates)) / (2. + len(rates))
        states.append(FiniteRelationalState(
            name, bin_index, groups, rates, posterior))
    states = tuple(sorted(states, key=lambda row: (
        row.feature_name, row.bin_index)))
    full_cuts = [tuple() for _ in names]
    for index, feature_cuts in zip(indices, cuts):
        full_cuts[index] = feature_cuts
    body = {"spec": asdict(spec), "palette": palette, "names": names,
            "domains": domains, "cutpoints": tuple(full_cuts),
            "states": tuple(asdict(row) for row in states)}
    return FrozenRelationalPortQuotient(
        spec, palette, names, domains, tuple(full_cuts), states,
        _digest(body))


def score_relational_port_quotient(model, graph):
    names, values, domains = _cached_features(
        graph, model.species_palette)
    if names != model.feature_names or domains != model.feature_domains:
        raise ValueError("candidate relational schema does not match frozen model")
    state_map = {(row.feature_name, row.bin_index): row.posterior
                 for row in model.states}
    indices = _feature_indices(domains, model.spec.feature_domain)
    cuts = tuple(model.cutpoints[index] for index in indices)
    posteriors = [state_map[token] for token in _tokens(
        values, indices, names, cuts) if token in state_map]
    if not posteriors:
        return 0.
    if model.spec.aggregation == "mean":
        return sum(posteriors) / len(posteriors)
    selected = sorted(posteriors, key=lambda value: abs(value - .5),
                      reverse=True)[:model.spec.top_tokens]
    if model.spec.aggregation == "top":
        return sum(selected) / len(selected)
    if model.spec.aggregation == "logit":
        logit = sum(math.log(max(1e-9, value) /
                             max(1e-9, 1. - value))
                    for value in selected) / len(selected)
        return 1. / (1. + math.exp(-logit))
    raise ValueError(f"unknown aggregation {model.spec.aggregation}")


__all__ = [
    "FiniteRelationalState", "FrozenRelationalPortQuotient",
    "RelationalMessageSpec", "fit_relational_port_quotient",
    "relational_message_features", "score_relational_port_quotient",
    "species_palette",
]
