#!/usr/bin/env python3
"""Lossless JSON payloads for frozen finite pose-port markings.

The marking token vocabulary contains nested tuples and ``PortRole`` values.
This module encodes that finite vocabulary explicitly; it never serializes
Python object code and never uses ``pickle`` or ``eval``.  Loading a payload
therefore reconstructs only the admitted immutable marking dataclasses.
"""

from __future__ import annotations

from typing import Any, Mapping

from materials_gcts_incidence_token_marking import (
    FrozenIncidenceTokenMarking, TokenEvidence)
from materials_gcts_port_incidence_search import PortRole
from materials_gcts_pose_port_state_marking import (
    FrozenPosePortStateMarking, PosePortStateEvidence)


FORMAT = "gcts-finite-pose-port-state-v1"


def _encode(value: Any):
    if isinstance(value, PortRole):
        return {"port_role": [
            value.parent_color, list(value.parent_neighbors),
            value.source_color, list(value.source_neighbors),
            value.separation_bin,
        ]}
    if isinstance(value, tuple):
        return {"tuple": [_encode(item) for item in value]}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"unsupported frozen marking value: {type(value)!r}")


def _decode(value: Any):
    if isinstance(value, dict):
        if set(value) == {"tuple"} and isinstance(value["tuple"], list):
            return tuple(_decode(item) for item in value["tuple"])
        if set(value) == {"port_role"}:
            fields = value["port_role"]
            if not isinstance(fields, list) or len(fields) != 5:
                raise ValueError("invalid frozen port role")
            return PortRole(
                str(fields[0]), tuple(map(int, fields[1])),
                str(fields[2]), tuple(map(int, fields[3])), int(fields[4]))
        raise ValueError("unknown frozen marking object")
    if isinstance(value, list):
        raise ValueError("untyped list in frozen marking")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise ValueError("invalid frozen marking scalar")


def pose_port_state_marking_payload(
        marking: FrozenPosePortStateMarking) -> dict[str, Any]:
    """Return a canonical-data payload suitable for deterministic JSON."""
    token_weights = sorted(
        marking.token_marking.token_weights.items(), key=lambda row: repr(row[0]))
    token_evidence = sorted(
        marking.token_marking.token_evidence.items(), key=lambda row: repr(row[0]))
    return {
        "format": FORMAT,
        "token_marking": {
            "intercept": marking.token_marking.intercept,
            "minimum_support": marking.token_marking.minimum_support,
            "minimum_groups": marking.token_marking.minimum_groups,
            "shrinkage": marking.token_marking.shrinkage,
            "weights": [[_encode(token), weight]
                        for token, weight in token_weights],
            "evidence": [[_encode(token), row.positive, row.total,
                          row.independent_groups]
                         for token, row in token_evidence],
        },
        "channel_families": [list(channel)
                             for channel in marking.channel_families],
        "state_bin_width": marking.state_bin_width,
        "state_probabilities": [[list(state), probability]
                                for state, probability in sorted(
                                    marking.state_probabilities.items())],
        "state_evidence": [[list(state), row.positive, row.total,
                            row.independent_groups]
                           for state, row in sorted(
                               marking.state_evidence.items())],
        "prior_probability": marking.prior_probability,
        "minimum_state_support": marking.minimum_state_support,
        "minimum_state_groups": marking.minimum_state_groups,
        "smoothing": marking.smoothing,
    }


def pose_port_state_marking_from_payload(
        payload: Mapping[str, Any]) -> FrozenPosePortStateMarking:
    """Validate and reconstruct one frozen finite pose-port marking."""
    if payload.get("format") != FORMAT:
        raise ValueError("unsupported frozen pose-port marking format")
    token = payload.get("token_marking")
    if not isinstance(token, Mapping):
        raise ValueError("missing frozen token marking")
    weights = {_decode(row[0]): float(row[1])
               for row in token.get("weights", ())}
    evidence = {
        _decode(row[0]): TokenEvidence(int(row[1]), int(row[2]), int(row[3]))
        for row in token.get("evidence", ())}
    if (len(weights) != len(token.get("weights", ())) or
            len(evidence) != len(token.get("evidence", ()))):
        raise ValueError("duplicate frozen token key")
    token_marking = FrozenIncidenceTokenMarking(
        float(token["intercept"]), weights, evidence,
        int(token["minimum_support"]), int(token["minimum_groups"]),
        float(token["shrinkage"]))
    probabilities = {tuple(map(int, row[0])): float(row[1])
                     for row in payload.get("state_probabilities", ())}
    state_evidence = {
        tuple(map(int, row[0])):
            PosePortStateEvidence(int(row[1]), int(row[2]), int(row[3]))
        for row in payload.get("state_evidence", ())}
    if (len(probabilities) != len(payload.get("state_probabilities", ())) or
            len(state_evidence) != len(payload.get("state_evidence", ()))):
        raise ValueError("duplicate frozen recurrent state")
    return FrozenPosePortStateMarking(
        token_marking,
        tuple(tuple(map(str, channel))
              for channel in payload["channel_families"]),
        float(payload["state_bin_width"]), probabilities, state_evidence,
        float(payload["prior_probability"]),
        int(payload["minimum_state_support"]),
        int(payload["minimum_state_groups"]), float(payload["smoothing"]))
