#!/usr/bin/env python3
"""Synthetic and NaCl controls for component-resolved GCTS execution."""

import math
from types import SimpleNamespace

from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, IDENTITY, PortAtlas)
from materials_gcts_partial_completion_executor import (
    PartialCompletionLevel, _dynamic_program)
from materials_gcts_partial_completion_marking import freeze_completion_candidate
from materials_gcts_partial_completion_sections import (
    FrozenCompletionSectionMarking, execute_partial_completion_sections,
    freeze_completion_sections, _components)
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)
from materials_gcts_port_graph_macros import BoundarySlot, mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import ExecutionBoundary
from materials_gcts_nacl_partial_completion_execution_benchmark import (
    _key, _parent_map)
from test_materials_gcts_partial_completion_executor import _fixture, _port


def _section_fixture():
    seed_prototype, levels = _fixture()
    level = levels[0]
    first = level.frozen_lower_program.prototypes[0]
    port, key = _port(first, first, (4., 0., 0.), observations=2)
    old = level.frozen_lower_program.atlas
    level.frozen_lower_program.atlas = PortAtlas(
        old.ports + (port,), old.witnessed_relations,
        old.symmetry_orbit_collapses, old.rejected_improper_occurrences,
        old.rejected_conflicting_relations, old.discarded_rare_classes,
        old.relation_classes)
    macro = level.alternatives[0]
    macro.boundary_slots += (
        BoundarySlot(0, "outgoing", 0, (0, 0, key), 2, 1.),)
    return seed_prototype, level


def _initial_sections(seed_prototype, level):
    seed = (ClusterOccurrence(0, 0, IDENTITY, (0., 0., 0.)),)
    dynamic = _dynamic_program(level.frozen_lower_program, seed, 1e-6)
    frontier = enumerate_partial_promoted_completions(
        dynamic, level.alternatives, minimum_matched_children=1,
        explicit_seed_sites=seed_prototype.sites,
        frozen_parent_types=level.alternative_parent_types,
        pose_tolerance=1e-6)
    completion = frontier.completions[0]
    candidate = freeze_completion_candidate(
        dynamic, level.alternatives[0], completion, pose_tolerance=1e-6)
    return seed, freeze_completion_sections(
        dynamic, level.alternatives[0], completion, candidate,
        occupied_sites=seed_prototype.sites, pose_tolerance=1e-6)


def test_section_can_accept_high_evidence_component_and_defer_rest():
    seed_prototype, level = _section_fixture()
    seed, sections = _initial_sections(seed_prototype, level)
    assert len(sections) == 2 and all(item.frozen_port_witnessed
                                      for item in sections)
    ordered = sorted(sections,
                     key=lambda item: item.descriptor.training_port_evidence,
                     reverse=True)
    marking = FrozenCompletionSectionMarking(
        ((ordered[0].descriptor, .9), (ordered[1].descriptor, .1)),
        .1, 20, False)
    result = execute_partial_completion_sections(
        level, seed, explicit_seed_sites=seed_prototype.sites,
        marking=marking, minimum_marking_score=.5,
        maximum_waves=1, pose_tolerance=1e-6)
    assert result.waves[0].whole_candidates > 0
    assert result.waves[0].sections == 2
    assert result.waves[0].accepted_sections == 1
    assert result.waves[0].deferred_below_threshold == 1
    assert len(result.waves[0].accepted_section_ids) == 1
    assert len(result.waves[0].deferred_section_ids) == 1
    assert not result.promoted_occurrences
    assert result.exact_certificates and not result.target_used


def test_shared_sites_cannot_be_split_into_independent_actions():
    children = {
        1: SimpleNamespace(sites=(("A", (0., 0., 0.)),)),
        2: SimpleNamespace(sites=(("A", (0., 0., 0.)),
                                  ("B", (1., 0., 0.))))}
    assert _components(children, (), children, 1e-6) == ((1, 2),)
    children[2] = SimpleNamespace(sites=(("B", (0., 0., 0.)),))
    try:
        _components(children, (), children, 1e-6)
    except ValueError:
        pass
    else:
        raise AssertionError("colored overlap was split into separate actions")


def test_deferred_component_self_feeds_and_completes_whole_parent():
    seed_prototype, level = _section_fixture()
    seed, sections = _initial_sections(seed_prototype, level)
    marking = FrozenCompletionSectionMarking(
        tuple((item.descriptor, .9) for item in sections), .9, 20, False)
    result = execute_partial_completion_sections(
        level, seed, explicit_seed_sites=seed_prototype.sites,
        marking=marking, minimum_marking_score=.5,
        maximum_waves=2, maximum_accepted_per_wave=1,
        pose_tolerance=1e-6)
    assert tuple(item.accepted_sections for item in result.waves) == (1, 1)
    assert result.waves[1].completed_whole_macros == 1
    assert result.promoted_occurrences and result.self_fed
    assert len(result.promotion_certificates) == 1
    assert result.exact_certificates


def test_nacl_sections_remain_exact_and_target_blind_until_posthoc_score():
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    primitive = compile_irregular_port_program(nacl.species, nacl.positions)
    quotient = quotient_macro_supports(mine_port_graph_macros(
        primitive, maximum_nodes=2,
        include_boundary_relations=True).macro_types)
    promoted = promote_macro_types(primitive, quotient.quotient_macros, level=1)
    center = (7.05, 7.05, 7.05)
    indices = tuple(index for index, point in enumerate(nacl.positions)
                    if math.dist(center, point) <= 5. + 1e-10)
    species = tuple(nacl.species[index] for index in indices)
    positions = tuple(nacl.positions[index] for index in indices)
    enumeration = enumerate_frozen_port_occurrences(
        primitive, species, positions)
    result = execute_partial_completion_sections(
        PartialCompletionLevel(
            primitive, quotient.alternative_macros,
            _parent_map(quotient, promoted), promoted),
        enumeration.occurrences,
        explicit_seed_sites=tuple(zip(species, positions)),
        public_boundary=ExecutionBoundary(center, 8.),
        maximum_waves=2, maximum_accepted_per_wave=16,
        minimum_child_coverage=.5)
    assert result.certificates and result.exact_certificates
    assert result.whole_candidate_batches_frozen_before_section_marking
    assert not result.target_api_present and not result.target_used
    # Scorer boundary is deliberately below all execution assertions.
    initial = {_key(site) for site in zip(species, positions)}
    emitted = {_key(site) for site in result.sites} - initial
    target = {_key(site) for site in zip(nacl.species, nacl.positions)}
    assert emitted and not (emitted - target)


if __name__ == "__main__":
    test_section_can_accept_high_evidence_component_and_defer_rest()
    test_shared_sites_cannot_be_split_into_independent_actions()
    test_deferred_component_self_feeds_and_completes_whole_parent()
    test_nacl_sections_remain_exact_and_target_blind_until_posthoc_score()
    print("partial completion sections: passed")
