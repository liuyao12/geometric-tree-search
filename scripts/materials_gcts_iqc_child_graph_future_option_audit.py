#!/usr/bin/env python3
"""Group-heldout clusters-squared option audit on consumed IQC nuclei.

Each six-action terminal is treated as a parent cluster state.  Its already
frozen child-frontier graph supplies at most eight child options.  Two marking
channels are learned from nine development nuclei at a time (order-one and
order-two typed port graphs); two further channels are fixed local option
statistics.  The held-out target label is consulted only after the immutable
four-parent beam has been selected.

This is a development audit, not a fresh confirmation.  In particular, the
child nodes have no individual correctness labels: the result tests retention
of an exact *parent* when bounded future options are visible.  It must not be
reported as proof that a third-block child is correct or as autonomous growth.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_child_frontier_graph_value import (
    ChildFrontierGraphExample, ChildFrontierGraphValueSpec,
    fit_child_frontier_graph_value, score_child_frontier_graph_value)
from materials_gcts_clusters2_future_option import (
    ChildOption, FrozenFutureOptionSpec, ParentOption, score_future_options,
    select_future_options)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_post_self_fed_child_graph_dataset import (
    EXPECTED_DATASET_DIGEST,
    EXPECTED_FIXTURE_SHA256 as EXPECTED_SOURCE_FIXTURE_SHA256,
    graph_from_json, load_graph_fixture, validate_dataset)


CHANNELS = ("typed-ports-order1", "typed-ports-order2",
            "local-port-mass", "live-continuation")
TOP_K = 4
BEAM_WIDTH = 4
SHUFFLES = 31
SPECS = (
    ChildFrontierGraphValueSpec(1, 2, 10., 100, .16),
    ChildFrontierGraphValueSpec(2, 2, 10., 100, .16),
)
ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_child_graph_future_option_audit_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "f8acad24fad1137200003211d04940f8efda123e7876acf7ff904e1f20aaf8d9"
EXPECTED_AUDIT_DIGEST = \
    "920ad7aa4e31ff219ac27556b1682eca5223a94d05aeb38c28bd5b4b15106372"


@dataclass(frozen=True)
class Row:
    group: int
    stable_index: int
    graph: object
    exact: bool
    correct_sites: int


@dataclass(frozen=True)
class Fold:
    heldout_group: int
    parent_candidates: int
    exact_parent_supply: int
    selected_parent_ids: tuple[int, ...]
    selected_exact_parents: int
    retained_exact_parent: bool
    mean_option_first_exact_rank: int | None
    order2_first_exact_rank: int | None
    order2_top_parent_exact: bool
    retained_child_options: int
    candidate_digest: str
    model_digests: tuple[str, ...]


def _load_rows():
    raw, payload = load_graph_fixture()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SOURCE_FIXTURE_SHA256:
        raise AssertionError("child-graph fixture byte drift")
    dataset = validate_dataset(payload)
    if dataset["dataset_digest"] != EXPECTED_DATASET_DIGEST:
        raise AssertionError("child-graph dataset drift")
    rows = tuple(Row(
        int(item["group"]), int(item["stable_index"]),
        graph_from_json(item["graph"]), bool(item["exact"]),
        int(item["correct_sites"]))
        for group in dataset["groups"] for item in group["rows"])
    return rows, dataset


def _fit(rows, spec):
    return fit_child_frontier_graph_value(tuple(
        ChildFrontierGraphExample(row.group, row.graph, row.exact)
        for row in rows), spec)


def _local_child_scores(graph):
    compatible = [0] * len(graph.nodes)
    witnessed = [0] * len(graph.nodes)
    for edge in graph.edges:
        if edge.compatible:
            compatible[edge.left_index] += 1
            compatible[edge.right_index] += 1
        if edge.connection_witnessed:
            witnessed[edge.left_index] += 1
            witnessed[edge.right_index] += 1
    denominator = max(1, len(graph.nodes) - 1)
    return tuple((
        min(1., (node.incoming_mass_bin + node.outgoing_mass_bin) / 32.),
        (2. * (not node.dead_end)
         + compatible[index] / denominator
         + witnessed[index] / denominator) / 4.,
    ) for index, node in enumerate(graph.nodes))


def _parents(rows, models):
    parents = []
    for row in rows:
        graph_scores = tuple(score_child_frontier_graph_value(
            model, row.graph) for model in models)
        local = _local_child_scores(row.graph)
        children = tuple(ChildOption(
            (row.graph.canonical_digest, index),
            graph_scores + local_score)
            for index, local_score in enumerate(local))
        parents.append(ParentOption(row.stable_index, children))
    return tuple(parents)


def _select_values(parent_ids, values, width):
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
        for index in sorted(range(len(parent_ids)), key=lambda index: (
                -sum(values[index]) / len(values[index]),
                parent_ids[index])):
            if parent_ids[index] not in selected:
                selected.append(parent_ids[index])
            if len(selected) == width:
                break
    return tuple(selected)


def _rank(parent_ids, values, exact_ids):
    order = tuple(parent_ids[index] for index in sorted(
        range(len(parent_ids)), key=lambda index: (
            -sum(values[index]) / len(values[index]), parent_ids[index])))
    return next((rank for rank, parent_id in enumerate(order, 1)
                 if parent_id in exact_ids), None)


def evaluate():
    rows, dataset = _load_rows()
    spec = FrozenFutureOptionSpec(CHANNELS, TOP_K, BEAM_WIDTH)
    folds = []
    control_retention = [0] * SHUFFLES
    control_rank_sums = [0] * SHUFFLES
    every_marginal_preserved = True
    for heldout in range(dataset["development_groups"]):
        training = tuple(row for row in rows if row.group != heldout)
        held = tuple(row for row in rows if row.group == heldout)
        models = tuple(_fit(training, model_spec) for model_spec in SPECS)
        parents = _parents(held, models)
        selection = select_future_options(parents, spec)
        scored = tuple(sorted(selection.scored,
                              key=lambda row: row.parent_id))
        parent_ids = tuple(int(row.parent_id) for row in scored)
        values = tuple(tuple(map(float, row.channel_values)) for row in scored)
        exact_ids = {row.stable_index for row in held if row.exact}
        selected = set(map(int, selection.selected_parent_ids))
        mean_rank = _rank(parent_ids, values, exact_ids) if exact_ids else None
        order2_order = tuple(parent_ids[index] for index in sorted(
            range(len(parent_ids)), key=lambda index: (
                -values[index][1], parent_ids[index])))
        order2_rank = next((rank for rank, parent_id in
                            enumerate(order2_order, 1)
                            if parent_id in exact_ids), None)
        folds.append(Fold(
            heldout, len(held), len(exact_ids),
            tuple(map(int, selection.selected_parent_ids)),
            len(selected & exact_ids), bool(selected & exact_ids), mean_rank,
            order2_rank, bool(order2_order and order2_order[0] in exact_ids),
            sum(len(children) for _parent, children in
                selection.selected_child_ids_by_parent),
            selection.candidate_digest,
            tuple(model.model_digest for model in models)))

        if not exact_ids:
            continue
        original = tuple(tuple(sorted(row[channel] for row in values))
                         for channel in range(len(CHANNELS)))
        for shuffle in range(SHUFFLES):
            rng = random.Random(
                f"iqc-child-graph-option-null-{heldout}-{shuffle}")
            columns = []
            for channel in range(len(CHANNELS)):
                column = [row[channel] for row in values]
                rng.shuffle(column)
                columns.append(column)
            shuffled = tuple(tuple(columns[channel][parent]
                             for channel in range(len(CHANNELS)))
                             for parent in range(len(parent_ids)))
            every_marginal_preserved = every_marginal_preserved and tuple(
                tuple(sorted(row[channel] for row in shuffled))
                for channel in range(len(CHANNELS))) == original
            selected_null = set(_select_values(
                parent_ids, shuffled, BEAM_WIDTH))
            control_retention[shuffle] += int(bool(
                exact_ids & selected_null))
            control_rank_sums[shuffle] += _rank(
                parent_ids, shuffled, exact_ids) or 0

    supplied = tuple(fold for fold in folds if fold.exact_parent_supply)
    retained = sum(fold.retained_exact_parent for fold in supplied)
    rank_sum = sum(fold.mean_option_first_exact_rank or 0 for fold in supplied)
    order2_exact = sum(fold.order2_top_parent_exact for fold in supplied)
    retention_p = (1 + sum(value >= retained
                           for value in control_retention)) / (SHUFFLES + 1)
    rank_p = (1 + sum(value <= rank_sum
                      for value in control_rank_sums)) / (SHUFFLES + 1)
    gate = (retained > order2_exact and retention_p <= .05
            and rank_p <= .05)
    body = {
        "schema_version": 1,
        "source_dataset_digest": dataset["dataset_digest"],
        "development_groups": dataset["development_groups"],
        "parent_examples": len(rows),
        "exact_parent_examples": sum(row.exact for row in rows),
        "channels": CHANNELS,
        "top_k_child_options": TOP_K,
        "parent_beam_width": BEAM_WIDTH,
        "folds": [asdict(fold) for fold in folds],
        "supplied_heldout_groups": len(supplied),
        "future_option_retained_groups": retained,
        "order2_top_parent_exact_groups": order2_exact,
        "mean_option_first_exact_rank_sum": rank_sum,
        "shuffles": SHUFFLES,
        "shuffle_retained_groups": tuple(control_retention),
        "shuffle_first_exact_rank_sums": tuple(control_rank_sums),
        "retention_p_value": retention_p,
        "rank_p_value": rank_p,
        "every_channel_marginal_preserved": every_marginal_preserved,
        "candidate_geometry_unchanged": True,
        "children_individually_labeled": False,
        "parent_labels_opened_only_after_selection": True,
        "target_used_for_child_graph_or_ranking": False,
        "targets_consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "third_block_child_correctness_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
        "causal_superiority_gate_passed": gate,
        "honest_status": (
            "group-heldout parent retention only; individual third-block "
            "child outcomes remain unobserved"),
    }
    return {**body, "audit_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("audit_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest
            or body["schema_version"] != 1
            or body["source_dataset_digest"] != EXPECTED_DATASET_DIGEST
            or body["development_groups"] != 10
            or body["parent_examples"] != 1278
            or body["exact_parent_examples"] != 142
            or tuple(body["channels"]) != CHANNELS
            or body["top_k_child_options"] != TOP_K
            or body["parent_beam_width"] != BEAM_WIDTH
            or not body["every_channel_marginal_preserved"]
            or not body["candidate_geometry_unchanged"]
            or body["children_individually_labeled"]
            or not body["parent_labels_opened_only_after_selection"]
            or body["target_used_for_child_graph_or_ranking"]
            or not body["targets_consumed_development_only"]
            or body["fresh_confirmation_claimed"]
            or body["third_block_child_correctness_claimed"]
            or body["autonomous_growth_claimed"]
            or body["stationary_or_exponential_claimed"]):
        raise AssertionError("IQC child-graph future-option audit drift")
    if EXPECTED_AUDIT_DIGEST and digest != EXPECTED_AUDIT_DIGEST:
        raise AssertionError("IQC child-graph future-option digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("IQC child-graph option fixture byte drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    row = evaluate()
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
