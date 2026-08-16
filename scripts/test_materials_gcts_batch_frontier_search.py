#!/usr/bin/env python3
"""Whole-placement consensus and primitive replay safety tests."""

from materials_gcts_batch_frontier_search import (
    FrozenPortPairMarking, _candidate_id, run_batch_frontier_search)
from materials_gcts_frozen_frontier_replay import (
    FrozenFrontierProgram, FrozenProduction, _classify_candidate,
    _placed_sites, _site_key, enumerate_frontier,
    fit_frozen_frontier_program)
from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, IDENTITY, learn_overlap_ports)
from test_materials_gcts_oriented_overlap_ports import _octahedron


def _synthetic_frozen_program():
    sodium = _octahedron("Na", "Cl")
    chloride = _octahedron("Cl", "Na")
    directions = ((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
                  (0.0, 1.0, 0.0), (0.0, -1.0, 0.0),
                  (0.0, 0.0, 1.0), (0.0, 0.0, -1.0))
    training = (ClusterOccurrence(0, 0, IDENTITY, (0.0, 0.0, 0.0)),) + tuple(
        ClusterOccurrence(index + 1, 1, IDENTITY, direction)
        for index, direction in enumerate(directions))
    atlas = learn_overlap_ports(
        (sodium, chloride), training, minimum_overlap=2,
        allowed_type_pairs=frozenset({(0, 1)}))
    productions = tuple(FrozenProduction(
        index, port.parent_type, port.child_type, port, port.observations)
        for index, port in enumerate(atlas.ports))
    return FrozenFrontierProgram(
        (sodium, chloride), productions, .03, .45, 2, 7,
        False, False, False, False), training[0]


def test_synthetic_consensus_commits_whole_compatible_placements():
    program, seed = _synthetic_frozen_program()
    result = run_batch_frontier_search(
        program, (seed,), threshold_ratio=1.0, maximum_waves=1)
    wave = result.waves[0]
    assert wave.candidate_count == 6
    assert wave.maximum_minimum_site_support >= 1
    assert wave.accepted_candidates > 1
    assert all(item.normalized_support == 1.0 for item in wave.candidates)
    assert all(item.accepted for item in wave.candidates)
    assert len(result.symbolic_nodes) == 1 + wave.accepted_candidates
    assert not result.target_used


def test_primitive_candidate_identity_support_and_pairwise_safety():
    configuration = next(item for item in benchmark_systems()
                         if item.name == "NaCl-rocksalt")
    learned = compile_irregular_port_program(
        configuration.species, configuration.positions)
    program = fit_frozen_frontier_program(learned)
    seed = (learned.occurrences[0],)
    direct = enumerate_frontier(program, seed)
    result = run_batch_frontier_search(
        program, seed, threshold_ratio=.5, maximum_waves=1,
        maximum_accepted_per_wave=8)
    wave = result.waves[0]
    direct_by_id = {
        _candidate_id(candidate, program.overlap_tolerance): candidate
        for candidate in direct.candidates}
    assert tuple(item.candidate_id for item in wave.candidates) == tuple(
        _candidate_id(candidate, program.overlap_tolerance)
        for candidate in direct.candidates)
    support = {}
    for candidate_id, candidate in direct_by_id.items():
        for site in candidate.novel_sites:
            support.setdefault(
                _site_key(site, program.overlap_tolerance), set()).add(
                    candidate_id)
    for record in wave.candidates:
        assert record.minimum_site_support == min(
            len(support[key]) for key in record.emitted_site_keys)

    occupied = list(_placed_sites(program, seed))
    for record in sorted(
            (item for item in wave.candidates if item.accepted),
            key=lambda item: (-item.normalized_support,
                              -item.minimum_site_support,
                              item.candidate_id)):
        candidate = direct_by_id[record.candidate_id]
        _, novel, conflict = _classify_candidate(
            candidate.rendered_sites, occupied,
            program.overlap_tolerance, program.exclusion_distance)
        assert not conflict and novel
        occupied.extend(novel)
    assert result.sites == tuple(sorted(
        result.sites,
        key=lambda site: _site_key(site, program.overlap_tolerance)))


def test_bounded_port_pair_marking_fails_closed_without_changing_candidates():
    program, seed = _synthetic_frozen_program()
    baseline = run_batch_frontier_search(
        program, (seed,), threshold_ratio=1.0, maximum_waves=1)
    production_id = program.productions[0].production_id
    admitted = FrozenPortPairMarking(
        ((None, production_id, 3, 1.0),), 2, .99)
    marked = run_batch_frontier_search(
        program, (seed,), threshold_ratio=1.0, maximum_waves=1,
        marking=admitted)
    assert tuple(item.candidate_id for item in baseline.waves[0].candidates) == (
        tuple(item.candidate_id for item in marked.waves[0].candidates))
    assert marked.waves[0].accepted_candidates == 6
    assert all(item.marking_supported and item.marking_probability == 1.0
               for item in marked.waves[0].candidates)
    rejected = FrozenPortPairMarking((), 1, .5)
    closed = run_batch_frontier_search(
        program, (seed,), threshold_ratio=1.0, maximum_waves=1,
        marking=rejected)
    assert closed.waves[0].candidate_count == 6
    assert closed.waves[0].accepted_candidates == 0
    assert closed.waves[0].rejected_marking == 6
    assert all(item.rejection == "marking-rejected"
               for item in closed.waves[0].candidates)
    assert closed.bounded_port_pair_marking_used
    leaked = FrozenPortPairMarking((), 1, .5, target_used_during_fit=True)
    try:
        run_batch_frontier_search(
            program, (seed,), threshold_ratio=1.0, maximum_waves=1,
            marking=leaked)
    except ValueError as error:
        assert "target-conditioned" in str(error)
    else:
        raise AssertionError("target-conditioned marking must fail closed")


if __name__ == "__main__":
    test_synthetic_consensus_commits_whole_compatible_placements()
    test_primitive_candidate_identity_support_and_pairwise_safety()
    test_bounded_port_pair_marking_fails_closed_without_changing_candidates()
    print("whole-placement batch frontier consensus: passed")
