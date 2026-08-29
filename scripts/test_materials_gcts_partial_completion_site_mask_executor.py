#!/usr/bin/env python3
"""Synthetic and NaCl controls for thresholded completion site masks."""

import math

from materials_gcts_cdyb_site_resolved_completion_section import (
    FEATURE_NAMES, FrozenSiteSection)
from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_partial_completion_executor import PartialCompletionLevel
from materials_gcts_partial_completion_site_mask_executor import (
    execute_partial_completion_site_masks)
from materials_gcts_partial_completion_site_policy import (
    adapt_frozen_site_section)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import ExecutionBoundary
from materials_gcts_nacl_partial_completion_execution_benchmark import (
    _key, _parent_map)
from test_materials_gcts_partial_completion_site_policy import _frozen_frontier


def _distance_policy(threshold):
    model = FrozenSiteSection(
        FEATURE_NAMES, (0.,) * len(FEATURE_NAMES),
        (1.,) * len(FEATURE_NAMES),
        (0., 0., 0., -1.) + (0.,) * (len(FEATURE_NAMES) - 4),
        6., .1, "minimum", threshold, False, False)
    return adapt_frozen_site_section(model)


def _constant_policy():
    return adapt_frozen_site_section(FrozenSiteSection(
        FEATURE_NAMES, (0.,) * len(FEATURE_NAMES),
        (1.,) * len(FEATURE_NAMES), (0.,) * len(FEATURE_NAMES),
        10., .1, "minimum", .5, False, False))


def test_partial_mask_never_instantiates_incomplete_child():
    seed_prototype, level, seed, *_rest = _frozen_frontier()
    policy = _distance_policy(.8)
    result = execute_partial_completion_site_masks(
        level, seed, site_policy=policy,
        explicit_seed_sites=seed_prototype.sites,
        maximum_waves=1, pose_tolerance=1e-6)
    wave = result.waves[0]
    assert 0 < len(wave.accepted_site_keys) < len(wave.proposed_novel_site_keys)
    assert wave.deferred_residuals and wave.complete_cover_accounted
    assert result.final_deferred_residuals
    assert not result.child_certificates
    assert len(result.final_occurrences) == len(seed)
    assert not result.promoted_occurrences
    assert result.candidate_sections_frozen_before_site_scores
    assert result.exact_certificates and not result.target_used


def test_accumulated_site_masks_complete_children_then_parent():
    seed_prototype, level, seed, *_rest = _frozen_frontier()
    policy = _distance_policy(.7)
    result = execute_partial_completion_site_masks(
        level, seed, site_policy=policy,
        explicit_seed_sites=seed_prototype.sites,
        maximum_waves=2, pose_tolerance=1e-6)
    assert len(result.waves) >= 2
    assert result.waves[0].completed_children == 1
    assert result.waves[0].completed_parents == 0
    assert result.waves[1].completed_children == 1
    assert result.waves[1].completed_parents == 1
    assert len(result.child_certificates) == 2
    assert len(result.parent_certificates) == 1
    assert result.promoted_occurrences and result.self_fed
    assert not any(item.site_key in result.waves[1].accepted_site_keys
                   for item in result.final_deferred_residuals)
    assert all(item.complete_cover_accounted for item in result.waves)


def test_partial_site_accumulation_is_not_mislabeled_self_fed():
    seed_prototype, level, seed, *_rest = _frozen_frontier()
    policy = _distance_policy(.8)
    result = execute_partial_completion_site_masks(
        level, seed, site_policy=policy,
        explicit_seed_sites=seed_prototype.sites,
        maximum_waves=2, pose_tolerance=1e-6)
    assert len(result.waves) == 2
    assert result.waves[0].accepted_site_keys
    assert not result.child_certificates
    assert not result.self_fed


def test_nacl_site_masks_are_exact_before_posthoc_score():
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
    result = execute_partial_completion_site_masks(
        PartialCompletionLevel(
            primitive, quotient.alternative_macros,
            _parent_map(quotient, promoted), promoted),
        enumeration.occurrences, site_policy=_constant_policy(),
        explicit_seed_sites=tuple(zip(species, positions)),
        public_boundary=ExecutionBoundary(center, 8.),
        maximum_waves=2, minimum_child_coverage=.5)
    assert result.accepted_site_certificates and result.child_certificates
    assert result.parent_certificates and result.exact_certificates
    assert all(item.complete_cover_accounted for item in result.waves)
    assert not result.target_api_present and not result.target_used
    # The full crystal is opened only for this post-execution assertion.
    initial = {_key(site) for site in zip(species, positions)}
    emitted = {_key(site) for site in result.sites} - initial
    target = {_key(site) for site in zip(nacl.species, nacl.positions)}
    assert emitted and not (emitted - target)


if __name__ == "__main__":
    test_partial_mask_never_instantiates_incomplete_child()
    test_accumulated_site_masks_complete_children_then_parent()
    test_partial_site_accumulation_is_not_mislabeled_self_fed()
    test_nacl_site_masks_are_exact_before_posthoc_score()
    print("partial completion site-mask executor: passed")
