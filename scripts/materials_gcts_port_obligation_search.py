#!/usr/bin/env python3
"""Target-free carried-port obligation features for GCTS lookahead."""

from __future__ import annotations

import math

from materials_gcts_frontier_band_marking import BAND_FEATURE_NAMES


PORT_OBLIGATION_FEATURE_NAMES = (
    "log_frontier_candidates",
    "log_total_connection_votes",
    "mean_vote_multiplicity",
    "consensus_site_fraction",
    "singleton_site_fraction",
    "mean_source_color_purity",
    "mean_target_role_purity",
    "mean_state_multiplicity",
    "mean_state_purity",
    "mean_state_entropy",
    "mean_parent_multiplicity",
    "mean_parent_purity",
    "train_recurrent_state_fraction",
    "mean_train_state_purity",
)

LOOKAHEAD_BAND_FEATURE_NAMES = BAND_FEATURE_NAMES + tuple(
    f"future_{name}" for name in PORT_OBLIGATION_FEATURE_NAMES) + tuple(
    f"delta_{name}" for name in PORT_OBLIGATION_FEATURE_NAMES)


def _purity(counter):
    total = sum(counter.values())
    return max(counter.values(), default=0) / total if total else 0.


def _entropy(counter):
    total = sum(counter.values())
    if not total:
        return 0.
    return -sum((count / total) * math.log(count / total)
                for count in counter.values() if count)


def describe_port_obligations(proposals, marking=None):
    """Summarize a frozen frontier without coordinates, IDs, or target data."""
    points = tuple(sorted(proposals.votes))
    if not points:
        return (0.,) * len(PORT_OBLIGATION_FEATURE_NAMES)
    votes = tuple(proposals.votes[point] for point in points)
    states = tuple(proposals.state_votes.get(point, {}) for point in points)
    parents = tuple(proposals.parent_votes.get(point, {}) for point in points)
    sources = tuple(proposals.color_votes.get(point, {}) for point in points)
    targets = tuple(proposals.target_color_votes.get(point, {})
                    for point in points)

    def mean(rows, function):
        return sum(function(row) for row in rows) / len(rows)

    state_rows = tuple((state, count) for row in states
                       for state, count in row.items())
    evidence = getattr(marking, "evidence", {}) if marking is not None else {}
    recurrent = getattr(marking, "accepted_states", ()) \
        if marking is not None else ()
    recurrent_mass = sum(count for state, count in state_rows
                         if state in recurrent)
    total_state_mass = sum(count for _state, count in state_rows)
    evidence_mass = sum(count for state, count in state_rows
                        if state in evidence)
    weighted_purity = sum(
        count * evidence[state].positive / max(1, evidence[state].total)
        for state, count in state_rows if state in evidence)
    return (
        math.log1p(len(points)),
        math.log1p(sum(votes)),
        sum(votes) / len(votes),
        sum(value >= 2 for value in votes) / len(votes),
        sum(value == 1 for value in votes) / len(votes),
        mean(sources, _purity),
        mean(targets, _purity),
        mean(states, lambda row: sum(row.values())),
        mean(states, _purity),
        mean(states, _entropy),
        mean(parents, lambda row: sum(row.values())),
        mean(parents, _purity),
        recurrent_mass / total_state_mass if total_state_mass else 0.,
        weighted_purity / evidence_mass if evidence_mass else 0.,
    )


def lookahead_band_features(base_features, before, after, marking=None):
    """Attach the carried frontier and change in unresolved port obligations."""
    base = tuple(float(value) for value in base_features)
    if len(base) != len(BAND_FEATURE_NAMES):
        raise ValueError("lookahead requires the frozen base band schema")
    previous = describe_port_obligations(before, marking)
    future = describe_port_obligations(after, marking)
    delta = tuple(right - left for left, right in zip(previous, future))
    result = base + future + delta
    if len(result) != len(LOOKAHEAD_BAND_FEATURE_NAMES) or any(
            not math.isfinite(value) for value in result):
        raise ValueError("lookahead obligation features must be finite")
    return result
