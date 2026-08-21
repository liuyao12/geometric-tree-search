#!/usr/bin/env python3
"""Canonical colored action/port incidence graphs for generic GCTS macros.

The graph is deliberately smaller than a material model and richer than a
cluster shape.  Its nodes are simultaneous colored placements.  Each node
carries every witnessed incoming parent->source port, and each pair of nodes
carries the exact equality/incidence relations among those port endpoints.
Only proper frames are used, so arbitrary translation and proper rotation are
quotiented while chirality remains observable.  Raw occurrence identifiers,
global coordinates, lattice indices, family labels, and targets are not part
of the public representation.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math


SCHEMA_VERSION = 1
ENDPOINT_RELATIONS = (
    "same_parent", "same_source", "left_source_is_right_parent",
    "right_source_is_left_parent", "touch",
)


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _subtract(left, right):
    return tuple(float(left[axis]) - float(right[axis]) for axis in range(3))


def _dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def _cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _normalize(vector):
    norm = math.sqrt(_dot(vector, vector))
    if norm <= 1e-10:
        raise ValueError("proper intrinsic frame is degenerate")
    return tuple(value / norm for value in vector)


def _frame(points):
    first = _subtract(points[1], points[0])
    second = _subtract(points[2], points[0])
    e1 = _normalize(first)
    transverse = tuple(second[axis] - _dot(second, e1) * e1[axis]
                       for axis in range(3))
    e2 = _normalize(transverse)
    e3 = _normalize(_cross(e1, e2))
    if _dot(_cross(e1, e2), e3) < 1. - 1e-8:
        raise AssertionError("intrinsic frame is not proper")
    return tuple(map(float, points[0])), (e1, e2, e3)


def _in_frame(point, origin, frame, scale):
    vector = _subtract(point, origin)
    return tuple(round(_dot(vector, axis) / scale, 6) for axis in frame)


def _state_code(value):
    """Detach a finite port-state value without depending on its Python type."""
    if isinstance(value, dict):
        parent = value["parent"]
        source = value["source"]
        return {
            "parent_species": str(parent.get("species")),
            "parent_radial_counts": tuple(map(int, parent["radial_counts"])),
            "source_species": str(source.get("species")),
            "source_radial_counts": tuple(map(int, source["radial_counts"])),
            "separation_bin": int(value["separation_bin"]),
        }
    if len(value) != 5:
        raise ValueError("port state must have five roles")
    return {
        "parent_species": str(value[0]),
        "parent_radial_counts": tuple(map(int, value[1])),
        "source_species": str(value[2]),
        "source_radial_counts": tuple(map(int, value[3])),
        "separation_bin": int(value[4]),
    }


def _near(left, right, tolerance):
    return math.dist(left, right) <= tolerance


def _relation_code(left, right, scale, tolerance):
    lp, ls = left["parent_position"], left["source_position"]
    rp, rs = right["parent_position"], right["source_position"]
    flags = {
        "same_parent": _near(lp, rp, tolerance),
        "same_source": _near(ls, rs, tolerance),
        "left_source_is_right_parent": _near(ls, rp, tolerance),
        "right_source_is_left_parent": _near(rs, lp, tolerance),
    }
    flags["touch"] = any(flags.values())
    return {
        "relations": tuple(name for name in ENDPOINT_RELATIONS
                           if flags[name]),
        "endpoint_distances_nn": tuple(round(math.dist(a, b) / scale, 6)
            for a in (lp, ls) for b in (rp, rs)),
    }


def canonical_port_incidence_graph(center, actions, scale, *,
                                   equality_tolerance=1e-6):
    """Return an ID-free proper-SE(3)-canonical graph.

    ``actions`` is an iterable of mappings with ``point``, ``species``, and
    ``port_witnesses``.  Every witness supplies a finite ``state`` plus ordered
    parent/source positions and species.  Exactly three actions are currently
    required because this is the bounded branch macro used by the benchmark;
    the schema itself does not encode a lattice or material family.
    """
    actions = tuple(actions)
    if len(actions) != 3:
        raise ValueError("bounded macro graph currently requires three actions")
    if not math.isfinite(scale) or scale <= 0.:
        raise ValueError("normalization scale must be finite and positive")
    tolerance = equality_tolerance * scale
    if tolerance <= 0.:
        raise ValueError("equality tolerance must be positive")
    for action in actions:
        if not action.get("port_witnesses"):
            raise ValueError("every action needs at least one witnessed port")

    candidates = []
    for order in itertools.permutations(range(3)):
        ordered = tuple(actions[index] for index in order)
        points = tuple(action["point"] for action in ordered)
        try:
            origin, frame = _frame(points)
        except ValueError:
            continue
        nodes = []
        raw_ports = []
        for index, action in enumerate(ordered):
            ports, raw = [], []
            for witness in action["port_witnesses"]:
                detached = {
                    "state": _state_code(witness["state"]),
                    "parent_species": str(witness["parent_species"]),
                    "source_species": str(witness["source_species"]),
                    "parent_local_nn": _in_frame(
                        witness["parent_position"], origin, frame, scale),
                    "source_local_nn": _in_frame(
                        witness["source_position"], origin, frame, scale),
                }
                ports.append(detached)
                raw.append(witness)
            sorted_pairs = sorted(zip(ports, raw),
                                  key=lambda pair: _canonical_json(pair[0]))
            ports = tuple(pair[0] for pair in sorted_pairs)
            raw = tuple(pair[1] for pair in sorted_pairs)
            raw_ports.append(raw)
            nodes.append({
                "node": index,
                "species": str(action["species"]),
                "local_nn": _in_frame(action["point"], origin, frame, scale),
                "center_distance_nn": round(
                    math.dist(action["point"], center) / scale, 6),
                "incoming_ports": ports,
            })
        edges = []
        for left in range(3):
            for right in range(left + 1, 3):
                relations = tuple(sorted((
                    _relation_code(lp, rp, scale, tolerance)
                    for lp in raw_ports[left] for rp in raw_ports[right]),
                    key=_canonical_json))
                edges.append({
                    "nodes": (left, right),
                    "distance_nn": round(math.dist(
                        ordered[left]["point"], ordered[right]["point"]
                    ) / scale, 6),
                    "port_pair_relations": relations,
                })
        payload = {
            "schema_version": SCHEMA_VERSION,
            "nodes": tuple(nodes),
            "edges": tuple(edges),
            "center_local_nn": _in_frame(center, origin, frame, scale),
            "proper_frame_determinant": 1,
            "raw_occurrence_ids_serialized": False,
            "global_frame_semantic": False,
        }
        candidates.append((_canonical_json(payload), payload))
    if not candidates:
        raise ValueError("action geometry has no finite proper frame")
    result = min(candidates, key=lambda pair: pair[0])[1]
    result["canonical_digest"] = _digest(result)
    return result


def development_geometry_to_incidence_graph(geometry):
    """Adapt the frozen development fixture to the shared graph contract."""
    actions = []
    for node in geometry["nodes"]:
        witnesses = tuple({
            "state": row["state"],
            "parent_position": tuple(row["parent_local_nn"]),
            "parent_species": row["parent_species"],
            "source_position": tuple(row["source_local_nn"]),
            "source_species": row["source_species"],
        } for row in node["port_witnesses"])
        actions.append({
            "point": tuple(node["local_nn"]),
            "species": node["species"],
            "port_witnesses": witnesses,
        })
    return canonical_port_incidence_graph(
        tuple(geometry["center_local_nn"]), actions, 1.)


__all__ = [
    "ENDPOINT_RELATIONS", "SCHEMA_VERSION",
    "canonical_port_incidence_graph", "development_geometry_to_incidence_graph",
]
