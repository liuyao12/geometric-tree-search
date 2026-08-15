#!/usr/bin/env python3
"""Recurring and noncongruent controls for action-macro promotion."""

from materials_gcts_action_macro_promotion import promote_batch_action_macros
from materials_gcts_batch_frontier_search import (
    BatchFrontierResult, ConsensusCandidate, ConsensusWave,
    SymbolicConsensusNode)
from materials_gcts_frozen_frontier_replay import _placed_sites, _render, _site_key
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, IDENTITY, expand_port_orbit)
from test_materials_gcts_batch_frontier_search import _synthetic_frozen_program


def _synthetic_three_wave_result(noncongruent_third=False):
    program, _ = _synthetic_frozen_program()
    parents = tuple(ClusterOccurrence(
        index, 0, IDENTITY, (10.0 * index, 0.0, 0.0))
        for index in range(3))
    directions = ((1.0, 0.0, 0.0),
                  (0.0, 1.0, 0.0),
                  (0.0, 0.0, 1.0))
    occurrences = list(parents)
    orbit = expand_port_orbit(
        program.prototypes[0], program.prototypes[1],
        program.productions[0].port, program.overlap_tolerance)
    symbolic = [SymbolicConsensusNode(
        item.occurrence_id, item.type_id, item.rotation, item.translation,
        0, None, None, None, 1.0) for item in parents]
    waves = []
    accepted_ids = []
    sites_before = len(_placed_sites(program, parents))
    for wave in (1, 2, 3):
        records = []
        for direction_index, direction in enumerate(directions):
            if noncongruent_third and wave == 3 and direction_index == 2:
                direction = (0.0, 0.0, 2.0)
            parent = parents[wave - 1]
            relative_rotation, relative_translation = min(
                orbit, key=lambda item: sum(
                    (item[1][axis] - direction[axis]) ** 2
                    for axis in range(3)))
            if noncongruent_third and wave == 3 and direction_index == 2:
                relative_translation = direction
            translation = tuple(parent.translation[axis] +
                                relative_translation[axis]
                                for axis in range(3))
            occurrence = ClusterOccurrence(
                len(occurrences), 1, relative_rotation, translation)
            occurrences.append(occurrence)
            candidate_id = f"wave-{wave}-action-{direction_index}"
            accepted_ids.append(candidate_id)
            rendered = _render(
                program.prototypes[1], occurrence.rotation,
                occurrence.translation)
            emitted = tuple(sorted(_site_key(
                site, program.overlap_tolerance) for site in rendered))
            records.append(ConsensusCandidate(
                candidate_id, parent.occurrence_id, 0, 1, emitted,
                1, 1.0, True, None))
            symbolic.append(SymbolicConsensusNode(
                occurrence.occurrence_id, 1, occurrence.rotation,
                occurrence.translation, wave, parent.occurrence_id, 0,
                candidate_id, 1.0))
        sites_after = len(_placed_sites(program, occurrences))
        waves.append(ConsensusWave(
            wave, tuple(records), 3, 1, 3, 3, 0, 0, 0, 0, True,
            sites_before, sites_after))
        sites_before = sites_after
    initial = _placed_sites(program, parents)
    sites = _placed_sites(program, occurrences)
    result = BatchFrontierResult(
        1.0, initial, sites, tuple(occurrences), tuple(symbolic),
        tuple(waves), tuple(accepted_ids), False)
    return program, result


def test_same_action_macro_recurs_across_three_translated_waves():
    program, batch = _synthetic_three_wave_result()
    promoted = promote_batch_action_macros(program, batch)
    assert promoted.exact_cover_of_accepted_nodes
    assert promoted.accepted_nodes == promoted.covered_accepted_nodes == 9
    assert len(promoted.macros) == 3
    assert all(macro.certificate.colored_union_is_exact and
               macro.certificate.edge_overlaps_are_exact_intersections and
               macro.certificate.incoming_boundaries_are_train_frozen_ports and
               macro.certificate.pairwise_compatible_antichain
               for macro in promoted.macros)
    assert len({macro.normalized_production_key
                for macro in promoted.macros}) == 1
    assert promoted.recurrences[0].waves == (1, 2, 3)
    assert promoted.recurrences[0].recurs_across_three_consecutive_waves
    assert not promoted.recurrences[0].hierarchy_stationarity_claimed
    assert not promoted.target_used


def test_noncongruent_wave_is_not_forced_into_recurring_macro():
    program, batch = _synthetic_three_wave_result(noncongruent_third=True)
    promoted = promote_batch_action_macros(program, batch)
    keys = tuple(macro.normalized_production_key for macro in promoted.macros)
    assert keys[0] == keys[1]
    assert keys[2] != keys[0]
    assert not any(item.recurs_across_three_consecutive_waves
                   for item in promoted.recurrences)


if __name__ == "__main__":
    test_same_action_macro_recurs_across_three_translated_waves()
    test_noncongruent_wave_is_not_forced_into_recurring_macro()
    print("exact batch action-macro promotion: passed")
