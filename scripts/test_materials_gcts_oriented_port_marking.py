#!/usr/bin/env python3

from collections import Counter

from materials_gcts_oriented_port_marking import (
    IncomingPortMarking, PortChoiceSample, score_marking)


def test_incoming_port_context_reorders_the_same_candidate_actions():
    incoming_a = (1, 2, (10,))
    incoming_b = (3, 2, (20,))
    outward_a = (2, 4, (30,))
    outward_b = (2, 5, (40,))
    global_counts = {2: Counter({outward_a: 5, outward_b: 5})}
    marking = IncomingPortMarking(
        global_counts,
        {(2, incoming_a): Counter({outward_a: 5}),
         (2, incoming_b): Counter({outward_b: 5})},
        10, 2, 3, 4, 16)
    samples = tuple(
        [PortChoiceSample((2, incoming_a), 2, outward_a)] * 5 +
        [PortChoiceSample((2, incoming_b), 2, outward_b)] * 5)
    marked = score_marking(marking, samples, use_context=True)
    unmarked = score_marking(marking, samples, use_context=False)
    assert marked.scored_choices == unmarked.scored_choices == 10
    assert marked.proposal_checks == 10
    assert marked.failed_checks == 0
    assert unmarked.failed_checks == 5


if __name__ == "__main__":
    test_incoming_port_context_reorders_the_same_candidate_actions()
    print("causal incoming oriented-port marking: passed")
