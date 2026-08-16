#!/usr/bin/env python3
"""Claim audit for the sealed train-majority max-nodes-five IQC hierarchy."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass, replace

from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_frozen_hierarchy_transfer import (
    transfer_frozen_hierarchy_level)
from materials_gcts_iqc_reclustered_transfer_audit import (
    HELDOUT_PATCH_IDS, TRAIN_PATCH_IDS, _frozen_heldout_program,
    _grow_patches, _pack)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurring_action_submacro_audit import (
    PromotedSubmacroLevel, adapt_promoted_submacro_levels,
    audit_action_submacro_records)
from materials_gcts_stationary_production_signature import (
    canonicalize_production)
from materials_gcts_recurrent_core_selector import (
    filter_quotient_by_recurrent_core, select_recurrent_macro_core)


@dataclass(frozen=True)
class Max5TransferClaimAudit:
    train_atoms: int
    heldout_atoms: int
    train_patch_ids: tuple[int, ...]
    heldout_patch_ids: tuple[int, ...]
    raw_domains_mutually_disjoint: bool
    train_heldout_raw_ids_disjoint: bool
    raw_types_by_level: tuple[int, ...]
    selected_types_by_level: tuple[int, ...]
    exact_heldout_types_by_level: tuple[int, ...]
    child_arity_histograms_by_level: tuple[tuple[tuple[int, int], ...], ...]
    exact_raw_support_size_histograms_by_level: tuple[
        tuple[tuple[int, int], ...], ...]
    maximum_raw_support_atoms_by_level: tuple[int, ...]
    raw_atom_coverage_by_level: tuple[float, ...]
    residual_atom_terminals_by_level: tuple[int, ...]
    exact_complete_representation_by_level: tuple[bool, ...]
    minimum_distinct_namespaces_by_level: tuple[int, ...]
    minimum_atom_disjoint_occurrences_by_level: tuple[int, ...]
    common_normalized_production_keys_by_adjacent_levels: tuple[int, ...]
    common_normalized_production_keys_by_three_levels: tuple[int, ...]
    strict_adapted_records: int
    strict_eligible_records: int
    strict_adaptation_rejections: int
    strict_rejection_reason_histogram: tuple[tuple[str, int], ...]
    scale_population_eligible_three_level_witnesses: int
    learned_stationary_scales: tuple[float, ...]
    population_substitution_matrices: tuple[tuple[tuple[int, ...], ...], ...]
    maximum_support_amplification_by_transition: tuple[float, ...]
    any_represented_support_amplification_over_three: bool
    three_consecutive_amplifications_over_three: bool
    strict_stationary: bool
    exact_four_level_heldout_reencoding: bool
    autonomous_growth_or_emission: bool
    exponential_claim: bool
    heldout_used_for_selection: bool
    family_phi_cell_radius_used: bool
    conclusion: str


def _histogram(values):
    return tuple(sorted(Counter(values).items()))


def evaluate(maximum_levels: int = 8) -> Max5TransferClaimAudit:
    executions, raw_domains = _grow_patches()
    train_species, train_positions, train_patch = _pack(
        executions, TRAIN_PATCH_IDS)
    held_species, held_positions, held_patch = _pack(
        executions, HELDOUT_PATCH_IDS)
    mutually_disjoint = all(not left.intersection(right)
                            for index, left in enumerate(raw_domains)
                            for right in raw_domains[index + 1:])
    train_raw = set().union(*(raw_domains[index]
                             for index in TRAIN_PATCH_IDS))
    held_raw = set().union(*(raw_domains[index]
                            for index in HELDOUT_PATCH_IDS))

    train = compile_irregular_port_program(train_species, train_positions)
    held_enumeration = enumerate_frozen_port_occurrences(
        train, held_species, held_positions)
    held = _frozen_heldout_program(train, held_enumeration)

    frozen_levels = []
    raw_type_counts = []
    train_artifact = train
    for level in range(maximum_levels):
        mined = mine_port_graph_macros(
            train_artifact, maximum_nodes=5,
            include_boundary_relations=True)
        quotient = quotient_macro_supports(mined.macro_types)
        if not quotient.quotient_macros:
            break
        raw_type_counts.append(len(quotient.quotient_macros))
        selection = select_recurrent_macro_core(
            quotient.quotient_macros, train_species, train_positions,
            train_patch, training_patch_ids=TRAIN_PATCH_IDS)
        quotient = filter_quotient_by_recurrent_core(quotient, selection)
        if not quotient.quotient_macros:
            break
        promoted = promote_macro_types(
            train_artifact, quotient.quotient_macros, level=level + 1)
        frozen_levels.append((quotient, promoted))
        train_artifact = promoted

    selected_counts = []
    held_counts = []
    child_histograms = []
    support_histograms = []
    maximum_supports = []
    coverages = []
    residuals = []
    complete = []
    minimum_namespaces = []
    minimum_independent = []
    strict_levels = []
    held_sites = tuple(zip(held_species, held_positions))
    held_artifact = held
    for level, (quotient, frozen_promoted) in enumerate(frozen_levels):
        # Exact representative matches are retained separately for the strict
        # stationarity adapter.  Backoff alternatives can preserve transfer,
        # but cannot manufacture a common exact production key.
        dense = match_dense_macro_types(
            held_artifact, quotient.quotient_macros)
        exact_macros = tuple(replace(
            item, occurrences=(),
            promotion_occurrences=item.promotion_occurrences)
            for item in dense.dense_macro_types
            if item.promotion_occurrences)
        strict_levels.append(PromotedSubmacroLevel(
            level, held_artifact, exact_macros))
        step = transfer_frozen_hierarchy_level(
            held_artifact, quotient, frozen_promoted, held_patch,
            raw_atom_sites=held_sites)
        audit = step.audit
        selected_counts.append(len(quotient.quotient_macros))
        held_counts.append(audit.exact_representative_types)
        child_histograms.append(_histogram(
            len(item.node_types) for item in quotient.quotient_macros))
        support_sizes = tuple(len(support)
                              for _, support in step.program.occurrence_supports)
        support_histograms.append(_histogram(support_sizes))
        maximum_supports.append(max(support_sizes, default=0))
        coverages.append(audit.coverage)
        residuals.append(audit.explicit_residual_atoms)
        complete.append(audit.exact_replay and
                        audit.complete_representation_certificate)
        minimum_namespaces.append(
            audit.minimum_distinct_namespaces_per_frozen_type)
        minimum_independent.append(
            audit.minimum_independent_occurrences_per_frozen_type)
        held_artifact = step.program
        if not audit.every_frozen_type_transferred:
            break

    records, adaptation_rejections = adapt_promoted_submacro_levels(
        strict_levels)
    strict = audit_action_submacro_records(records)
    keys_by_level = []
    for level in range(len(strict_levels)):
        keys = set()
        for record in records:
            if record.hierarchy_level != level:
                continue
            keys.add(canonicalize_production(
                record.production).normalized_key)
        keys_by_level.append(keys)
    adjacent = tuple(len(left & right)
                     for left, right in zip(keys_by_level, keys_by_level[1:]))
    triples = tuple(len(keys_by_level[index] & keys_by_level[index + 1] &
                        keys_by_level[index + 2])
                    for index in range(max(0, len(keys_by_level) - 2)))
    scales = tuple(sorted({round(
        witness.evidence.learned_similarity_scale, 12)
        for witness in strict.witnesses
        if witness.evidence.learned_similarity_scale is not None}))
    substitutions = tuple(sorted({
        comparison.chemical_population_audit.substitution_matrix
        for witness in strict.witnesses
        for comparison in witness.evidence.adjacent_comparisons
        if comparison.chemical_population_audit is not None and
        comparison.chemical_population_audit.consistent}, key=repr))
    amplification = tuple(
        right / left if left else 0.
        for left, right in zip(maximum_supports, maximum_supports[1:]))
    any_over_three = any(value > 3. for value in amplification)
    three_consecutive = any(all(value > 3. for value in
                                amplification[index:index + 3])
                            for index in range(max(0,
                                                   len(amplification) - 2)))
    exact_four = (len(selected_counts) >= 4 and
                  tuple(held_counts[:4]) == tuple(selected_counts[:4]) and
                  all(value > 0 for value in selected_counts[:4]) and
                  all(complete[:4]) and
                  all(value >= 2 for value in minimum_namespaces[:4]) and
                  all(value >= 2 for value in minimum_independent[:4]))
    autonomous = False
    exponential = (exact_four and autonomous and strict.stationary and
                   three_consecutive)
    conclusion = (
        "four frozen train-selected macro vocabularies exactly re-encode the "
        "fully observed heldout atoms with explicit residual terminals; this "
        "is not autonomous growth or emission, and no exponential claim follows "
        "unless one strict normalized production recurs over three heldout "
        "levels with equal scale/population substitution and >3 support "
        "amplification over three consecutive transitions")
    return Max5TransferClaimAudit(
        len(train_positions), len(held_positions), TRAIN_PATCH_IDS,
        HELDOUT_PATCH_IDS, mutually_disjoint,
        not train_raw.intersection(held_raw), tuple(raw_type_counts),
        tuple(selected_counts),
        tuple(held_counts), tuple(child_histograms),
        tuple(support_histograms), tuple(maximum_supports), tuple(coverages),
        tuple(residuals), tuple(complete), tuple(minimum_namespaces),
        tuple(minimum_independent), adjacent, triples,
        strict.adapted_records, strict.eligible_records,
        len(adaptation_rejections), _histogram(
            item.reason for item in adaptation_rejections),
        len(strict.witnesses), scales,
        substitutions, amplification, any_over_three, three_consecutive,
        strict.stationary, exact_four, autonomous, exponential, False, False,
        conclusion)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
