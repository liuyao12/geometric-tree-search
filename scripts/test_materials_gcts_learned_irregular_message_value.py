#!/usr/bin/env python3

from dataclasses import replace

from materials_gcts_irregular_supports import _species_key
from materials_gcts_learned_irregular_message_value import (
    LearnedIrregularMessageExample, LearnedIrregularMessageSpec,
    fit_learned_irregular_message_value,
    score_learned_irregular_message_value,
    shuffle_irregular_message_labels_within_groups)
from materials_gcts_partial_irregular_port_graph import (
    PartialIrregularPortGraph, PartialPortEdge, PartialPortNode)


def _graph(successful):
    first = PartialPortNode(1, _species_key("A"), 5 if successful else 2, 5, 4)
    second = PartialPortNode(2, _species_key("B"), 5, 6, 3)
    nodes = tuple(sorted((first, second)))
    edge = PartialPortEdge(
        nodes, ((_species_key("X"), 2 if successful else 1),),
        4 if successful else 10,
        ((_species_key("X"), (2, 3) if successful else (6, 8)),),
        1 if successful else -1)
    return PartialIrregularPortGraph(
        nodes, (edge,), 0, ("a" if successful else "b") * 64)


def test_grouped_learned_message_readout_scores_and_serializes():
    positive, negative = _graph(True), _graph(False)
    rows = tuple(LearnedIrregularMessageExample(group, graph, label)
                 for group in range(4)
                 for graph, label in ((positive, True), (negative, False)))
    spec = LearnedIrregularMessageSpec(ridge=.1, steps=180)
    first = fit_learned_irregular_message_value(rows, spec)
    second = fit_learned_irregular_message_value(tuple(reversed(rows)), spec)
    assert first.model_digest == second.model_digest
    assert score_learned_irregular_message_value(first, positive) > \
        score_learned_irregular_message_value(first, negative)
    assert not first.target_used


def test_label_shuffle_preserves_group_marginals_and_target_taint_fails():
    rows = tuple(LearnedIrregularMessageExample(group, _graph(label), label)
                 for group in range(3) for label in (True, False, True))
    shuffled = shuffle_irregular_message_labels_within_groups(rows, seed=17)
    for group in range(3):
        assert sum(row.successful for row in rows if row.group == group) == \
            sum(row.successful for row in shuffled if row.group == group)
    tainted = replace(_graph(True), target_used=True)
    try:
        fit_learned_irregular_message_value((
            LearnedIrregularMessageExample(0, tainted, True),
            LearnedIrregularMessageExample(1, _graph(False), False)))
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted graph entered learned value")


if __name__ == "__main__":
    test_grouped_learned_message_readout_scores_and_serializes()
    test_label_shuffle_preserves_group_marginals_and_target_taint_fails()
    print("learned irregular message-value tests passed")
