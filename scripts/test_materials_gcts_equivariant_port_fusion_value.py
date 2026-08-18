#!/usr/bin/env python3

from dataclasses import replace

from materials_gcts_equivariant_port_fusion_value import (
    EquivariantPortFusionCandidate, EquivariantPortFusionExample,
    EquivariantPortFusionSpec, fit_grouped_equivariant_port_fusion,
    percentile_ranks, select_equivariant_port_fusion)
from materials_gcts_irregular_supports import _species_key
from materials_gcts_learned_equivariant_port_value import (
    LearnedEquivariantPortSpec)
from materials_gcts_partial_irregular_port_graph import (
    PartialIncidenceEdge, PartialIrregularPortGraph, PartialPortNode)
from materials_gcts_portfolio_terminal_value import TerminalRepresentation


def _graph(label):
    nodes = (
        PartialPortNode(0, _species_key("A"), 3, 5, 4),
        PartialPortNode(1, _species_key("B"), 4, 6, 3))
    edge = PartialIncidenceEdge(
        0, 1, ((_species_key("X"), 1),), 5,
        ((_species_key("X"), (2, 3)),), 1 if label else -1,
        connection_witnessed=label)
    return PartialIrregularPortGraph(
        nodes, (), 0, ("a" if label else "b") * 64,
        incidence_edges=(edge,))


def test_rank_fusion_is_group_sealed_and_candidate_preserving():
    rows = tuple(EquivariantPortFusionExample(
        group, (0.,), ("X",), _graph(label), label)
        for group in range(5) for label in (False, True))
    spec = EquivariantPortFusionSpec(
        graph=LearnedEquivariantPortSpec(
            interaction_order=3, ridge=.1, minimum_feature_groups=2,
            steps=140, objective="pairwise"),
        neighbors=(1,), graph_rank_weights=(0., 1.))
    first, audit = fit_grouped_equivariant_port_fusion(
        rows, feature_names=("scalar",), color_keys=("X",),
        representations=(TerminalRepresentation("all", (0,)),), spec=spec)
    second, _ = fit_grouped_equivariant_port_fusion(
        tuple(reversed(rows)), feature_names=("scalar",), color_keys=("X",),
        representations=(TerminalRepresentation("all", (0,)),), spec=spec)
    assert first.model_digest == second.model_digest
    assert audit.groups == 5 and audit.selected_exact_groups == 5
    assert audit.selected_graph_rank_weight == 1.
    assert audit.candidate_geometry_unchanged and not audit.target_used
    candidates = (
        EquivariantPortFusionCandidate((0.,), ("X",), _graph(False), "bad"),
        EquivariantPortFusionCandidate((0.,), ("X",), _graph(True), "good"))
    selected = select_equivariant_port_fusion(first, candidates)
    assert selected.stable_index == 1
    assert selected.top_indices == (1,)
    assert percentile_ranks((4., 4., 8.)) == (0., 0., 1.)


def test_target_taint_fails_closed():
    rows = tuple(EquivariantPortFusionExample(
        group, (float(label),), ("X",),
        replace(_graph(label), target_used=(group == 0 and label)), label)
        for group in range(3) for label in (False, True))
    try:
        fit_grouped_equivariant_port_fusion(
            rows, feature_names=("scalar",), color_keys=("X",),
            representations=(TerminalRepresentation("all", (0,)),))
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted graph entered rank fusion")


if __name__ == "__main__":
    test_rank_fusion_is_group_sealed_and_candidate_preserving()
    test_target_taint_fails_closed()
    print("equivariant port-fusion tests passed")
