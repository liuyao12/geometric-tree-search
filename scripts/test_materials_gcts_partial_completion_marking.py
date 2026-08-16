#!/usr/bin/env python3
"""Causal and shuffled controls for target-free partial-completion marks."""

from types import SimpleNamespace

from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, IDENTITY, OrientedOverlapPort, PortAtlas)
from materials_gcts_partial_completion_marking import (
    CompletionMarkDescriptor, CompletionMarkTrace, FrozenCompletionCandidate,
    fit_completion_marking, freeze_completion_candidate,
    rank_completion_candidates, shuffle_completion_marking)
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)
from materials_gcts_port_graph_macros import BoundarySlot
from test_materials_gcts_partial_promoted_frontier import _fixture


def test_adapter_reads_only_frozen_anchor_ports_slots_and_local_support():
    program, bare_macro = _fixture()
    completion = enumerate_partial_promoted_completions(
        program, (bare_macro,)).completions[0]
    key = (11,)
    port = OrientedOverlapPort(
        0, 0, IDENTITY, (2., 0., 0.), (), (), key, 5)
    augmented = SimpleNamespace(**{
        **program.__dict__,
        "occurrences": program.occurrences + (
            ClusterOccurrence(2, 0, IDENTITY, (-2., 0., 0.)),),
        "atlas": PortAtlas((port,), 1, 0, 0, 0, 0,
                        ((2, 0, 0, 0, key),)),
        "boundary_ports": (), "boundary_relation_classes": (),
        "target_used": False})
    macro = SimpleNamespace(**{
        **bare_macro.__dict__, "boundary_slots": (
            BoundarySlot(0, "incoming", 0, (0, 0, key), 3, .75),)})
    frozen = freeze_completion_candidate(
        augmented, macro, completion,
        live_overlap_support=2, live_collision_support=0)
    assert frozen.descriptor.anchor_incoming_ports
    assert frozen.descriptor.alternative_boundary_slots
    assert frozen.descriptor.matched_witnesses == 2
    assert frozen.descriptor.training_port_evidence == 13
    assert frozen.descriptor.live_overlap_support == 2
    assert frozen.descriptor.live_collision_support == 0


def test_causal_mark_ranks_identical_candidates_better_than_constant_and_shuffles():
    port = lambda token: ("overlap", (token,), 1, 0)
    descriptors = tuple(CompletionMarkDescriptor(
        (port(token),), (("incoming", port(token), 8, 4),),
        1, 12, 2, 0) for token in ("bad-a", "bad-b", "bad-c", "good"))
    candidates = tuple(FrozenCompletionCandidate(
        f"candidate-{index}", index, 5, descriptor, (index,))
                       for index, descriptor in enumerate(descriptors))
    good = candidates[-1]
    traces = []
    for descriptor in descriptors[:-1]:
        traces.extend(CompletionMarkTrace(descriptor, False) for _ in range(8))
    traces.extend(CompletionMarkTrace(descriptors[-1], True) for _ in range(8))
    marking = fit_completion_marking(tuple(traces))
    constant = rank_completion_candidates(candidates, None)
    causal = rank_completion_candidates(candidates, marking)
    assert constant.ranked[0].candidate.candidate_id != good.candidate_id
    assert causal.ranked[0].candidate.candidate_id == good.candidate_id
    assert causal.candidate_digest == constant.candidate_digest
    shuffled_top = 0
    for seed in range(31):
        shuffled = rank_completion_candidates(
            candidates, shuffle_completion_marking(marking, seed))
        assert shuffled.candidate_digest == causal.candidate_digest
        assert shuffled.candidates_unchanged
        shuffled_top += (shuffled.ranked[0].candidate.candidate_id ==
                         good.candidate_id)
    assert shuffled_top < 16
    assert causal.candidates_unchanged and not causal.target_used


if __name__ == "__main__":
    test_adapter_reads_only_frozen_anchor_ports_slots_and_local_support()
    test_causal_mark_ranks_identical_candidates_better_than_constant_and_shuffles()
    print("partial completion causal marking: passed")
