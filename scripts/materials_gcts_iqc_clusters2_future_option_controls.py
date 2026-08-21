#!/usr/bin/env python3
"""Marginal-preserving controls for the consumed clusters² option audit.

The learned receipt is immutable.  For each of 31 deterministic controls, the
eight parent option values are permuted independently inside every marking
channel, preserving the candidate IDs and each channel's exact score
multiset.  Selection is rerun before the consumed exact-path label is used
only to score retention/rank.  This cannot serve as a fresh confirmation; it
measures how surprising the consumed supply result is under a weak null.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import asdict, dataclass

from materials_gcts_iqc_clusters2_future_option_diagnostic import (
    load_default_result)


SHUFFLES = 31


@dataclass(frozen=True)
class IQCClusters2FutureOptionControls:
    parents: int
    channels: int
    learned_selected_parents: tuple[int, ...]
    learned_exact_path_rank: int
    learned_retains_exact_path: bool
    shuffled_retained_exact_paths: int
    shuffled_exact_path_ranks: tuple[int, ...]
    retention_p_value: float
    rank_p_value: float
    identical_parent_candidate_digest: str
    every_channel_marginal_preserved: bool
    target_used_for_shuffle_or_selection: bool
    consumed_target_used_only_for_scoring: bool
    fresh_confirmation_claimed: bool
    causal_superiority_gate_passed: bool
    honest_status: str


def _select(parent_ids, values, width):
    selected = []
    for channel in range(len(values[0])):
        order = sorted(range(len(parent_ids)), key=lambda index: (
            -values[index][channel], parent_ids[index]))
        winner = next((parent_ids[index] for index in order
                       if parent_ids[index] not in selected), None)
        if winner is not None:
            selected.append(winner)
        if len(selected) == width:
            break
    if len(selected) < width:
        order = sorted(range(len(parent_ids)), key=lambda index: (
            -sum(values[index]) / len(values[index]), parent_ids[index]))
        for index in order:
            if parent_ids[index] not in selected:
                selected.append(parent_ids[index])
            if len(selected) == width:
                break
    mean_order = tuple(parent_ids[index] for index in sorted(
        range(len(parent_ids)), key=lambda index: (
            -sum(values[index]) / len(values[index]), parent_ids[index])))
    return tuple(selected), mean_order


def evaluate() -> IQCClusters2FutureOptionControls:
    result = load_default_result()
    receipt = result["receipt"]
    rows = tuple(sorted(receipt["parent_rows"],
                        key=lambda row: row["parent_id"]))
    parent_ids = tuple(int(row["parent_id"]) for row in rows)
    values = tuple(tuple(map(float, row["channel_values"])) for row in rows)
    width = int(receipt["parent_beam_width"])
    exact_ids = set(map(int, result["exact_path_parent_ids"]))
    if len(exact_ids) != 1:
        raise AssertionError("control expects one consumed exact-path parent")
    exact_id = next(iter(exact_ids))
    candidate_digest = hashlib.sha256(repr(parent_ids).encode()).hexdigest()
    original_marginals = tuple(tuple(sorted(row[channel]
        for row in values)) for channel in range(len(values[0])))
    retained = 0
    ranks = []
    preserved = True
    for index in range(SHUFFLES):
        rng = random.Random(f"iqc-clusters2-option-null-{index}")
        columns = []
        for channel in range(len(values[0])):
            column = [row[channel] for row in values]
            rng.shuffle(column)
            columns.append(column)
        shuffled = tuple(tuple(columns[channel][parent]
            for channel in range(len(columns)))
            for parent in range(len(parent_ids)))
        preserved = preserved and tuple(tuple(sorted(row[channel]
            for row in shuffled)) for channel in range(len(columns))) == \
            original_marginals
        selected, mean_order = _select(parent_ids, shuffled, width)
        retained += int(exact_id in selected)
        ranks.append(mean_order.index(exact_id) + 1)
    learned_rank = int(result["mean_option_first_exact_rank"])
    learned_retained = bool(result["future_option_retains_exact_path"])
    retention_p = (1 + sum(True >= learned_retained
                           for _ in range(retained)) +
                   sum(False >= learned_retained
                       for _ in range(SHUFFLES - retained))) / (SHUFFLES + 1)
    rank_p = (1 + sum(rank <= learned_rank for rank in ranks)) / \
        (SHUFFLES + 1)
    gate = learned_retained and rank_p <= .05 and retention_p <= .05
    return IQCClusters2FutureOptionControls(
        len(parent_ids), len(values[0]),
        tuple(receipt["selected_parent_ids"]), learned_rank,
        learned_retained, retained, tuple(ranks), retention_p, rank_p,
        candidate_digest, preserved, False, True, False, gate,
        ("clusters-squared option retains the consumed exact path, but its "
         "eight-parent null is not a causal superiority result"))


if __name__ == "__main__":
    print(asdict(evaluate()))
