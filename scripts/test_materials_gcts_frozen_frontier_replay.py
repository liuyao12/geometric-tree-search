#!/usr/bin/env python3

import math

from materials_gcts_frozen_frontier_replay import (
    FrontierSeed, RadialBoundary, enumerate_frontier,
    fit_frozen_frontier_program, replay_frontier, score_replay)
from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_periodic_growth import replicate


def test_nacl_replay_is_frozen_target_blind_and_boundary_audited():
    training = next(item for item in benchmark_systems()
                    if item.name == "NaCl-rocksalt")
    learned = compile_irregular_port_program(
        training.species, training.positions)
    program = fit_frozen_frontier_program(learned)
    assert program.productions
    assert not program.target_artifacts_stored
    assert not program.family_label_used
    assert not program.lattice_used
    assert not program.physical_potential_used

    seed = (learned.occurrences[0],)
    frontier = enumerate_frontier(program, seed)
    assert frontier.candidates
    # A gap atom has no invented orientation and proposes no action, but it is
    # part of compatibility: putting an unlike gap on the best novel site
    # removes that action as a geometric conflict.
    blocker = (("explicit-gap", frontier.candidates[0].novel_sites[0][1]),)
    blocked = enumerate_frontier(
        program, seed, explicit_gap_sites=blocker)
    assert blocked.conflicting_placements > frontier.conflicting_placements
    assert len(blocked.candidates) < len(frontier.candidates)

    center = seed[0].translation
    seed_radius = max(math.dist(point, center)
                      for _, point in frontier.candidates[0].rendered_sites)
    bounded = enumerate_frontier(
        program, seed,
        boundary=RadialBoundary(center, seed_radius * .25))
    assert bounded.outside_boundary > 0
    assert len(bounded.candidates) < len(frontier.candidates)

    # Ranking is a hook over the already frozen candidate set. It receives
    # incoming/outgoing port state but cannot add a target-derived action.
    default = replay_frontier(program, seed, maximum_steps=1)
    reranked = replay_frontier(
        program, seed, maximum_steps=1,
        ranker=lambda candidate: (-candidate.production_id,
                                  candidate.outgoing_port))
    assert default.accepted_productions
    assert reranked.accepted_productions
    assert default.attempted_poses == reranked.attempted_poses
    assert not default.target_used_for_proposals
    assert not reranked.target_used_for_proposals
    seen_incoming = []
    replay_frontier(
        program, seed, maximum_steps=2,
        ranker=lambda candidate: (
            seen_incoming.append(candidate.incoming_port) or
            (candidate.incoming_port is None, candidate.production_id)))
    assert any(port is not None for port in seen_incoming)

    target = replicate(training)
    score = score_replay(
        default, target.species, target.positions)
    assert score.proposed_novel_atoms > 0
    assert score.correct_novel_atoms == score.proposed_novel_atoms
    assert score.precision == 1.0
    assert not score.target_used_for_proposals

    with_gap = replay_frontier(
        program, FrontierSeed(seed, blocker), maximum_steps=0)
    assert with_gap.explicit_seed_gap_sites == 1
    assert with_gap.initial_oriented_sites + 1 == len(with_gap.initial_sites)


if __name__ == "__main__":
    test_nacl_replay_is_frozen_target_blind_and_boundary_audited()
    print("frozen target-blind frontier production replay: passed")
