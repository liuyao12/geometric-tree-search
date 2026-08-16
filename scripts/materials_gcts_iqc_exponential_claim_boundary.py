#!/usr/bin/env python3
"""Adversarial claim boundary for the next sealed IQC hierarchy transfer.

The strict gate is deliberately injectable.  Real transfer evidence can enter
only after the hierarchy has been frozen; synthetic records are used solely to
prove that every individual guard can turn a would-be witness red.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class HeldoutLevelEvidence:
    level: int
    normalized_production_key: str
    adjacent_learned_scale: float | None
    population_substitution: tuple[tuple[int, ...], ...] | None
    exact_colored_replay: bool
    complete_atom_cover: bool
    chemistry_preserved: bool
    chirality_preserved: bool
    directed_ports_preserved: bool
    independent_occurrences: int
    heldout_only: bool = True


@dataclass(frozen=True)
class ExponentialClaimAudit:
    stationary: bool
    evaluated_consecutive_triples: int
    passing_triples: tuple[tuple[int, int, int], ...]
    raw_id_disjoint: bool
    spatial_domains_disjoint: bool
    input_permutation_invariant: bool
    proper_se3_invariant: bool
    shuffled_semantic_control_rejected: bool
    perturbed_semantic_control_rejected: bool
    amorphous_rejected: bool
    family_phi_cell_radius_leakage: bool
    reason: str


@dataclass(frozen=True)
class MissingTypeEvidence:
    macro_id: int
    children: int
    training_occurrences: int
    training_patches: tuple[int, ...]
    training_atoms: int
    atoms_unique_against_other_types: int
    mdl_saving: int


@dataclass(frozen=True)
class OptionalVocabularyAudit:
    train_atoms: int
    heldout_atoms: int
    raw_patch_domains_mutually_disjoint: bool
    train_heldout_raw_ids_disjoint: bool
    frozen_level_one_types: int
    replayed_level_one_types: int
    missing: tuple[MissingTypeEvidence, ...]
    heldout_atom_cover_with_missing_absent: float
    all_missing_atom_redundant_on_train: bool
    all_missing_confined_to_one_training_patch: bool
    heldout_zero_of_three_patch_presence_upper_95: float
    next_level_macros_using_missing_types: int
    transferred_exact_promoted_levels: int
    current_stationary_claim: bool
    safe_optional_for_observed_atom_cover: bool
    safe_optional_for_recursive_grammar: bool
    statistical_rarity_established: bool
    conclusion: str


@dataclass(frozen=True)
class PipelineAdversarialAudit:
    iqc_input_permutation_invariant: bool
    iqc_generic_proper_se3_invariant: bool
    shuffled_semantic_control_rejected: bool
    perturbed_semantic_control_rejected: bool
    amorphous_macro_and_stationarity_rejected: bool
    family_phi_cell_expected_radius_unused: bool
    passed: bool


def audit_exponential_claim(
        levels: Sequence[HeldoutLevelEvidence], *,
        raw_id_disjoint: bool,
        spatial_domains_disjoint: bool,
        input_permutation_invariant: bool,
        proper_se3_invariant: bool,
        shuffled_semantic_control_rejected: bool,
        perturbed_semantic_control_rejected: bool,
        amorphous_rejected: bool,
        family_phi_cell_radius_leakage: bool,
        tolerance: float = 1e-6,
) -> ExponentialClaimAudit:
    """Admit only one exact production across three heldout levels."""
    if tolerance <= 0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and positive")
    ordered = tuple(sorted(levels, key=lambda item: item.level))
    passing = []
    evaluated = 0
    global_guards = (
        raw_id_disjoint and spatial_domains_disjoint and
        input_permutation_invariant and proper_se3_invariant and
        shuffled_semantic_control_rejected and
        perturbed_semantic_control_rejected and amorphous_rejected and
        not family_phi_cell_radius_leakage)
    for left, middle, right in zip(ordered, ordered[1:], ordered[2:]):
        if (middle.level, right.level) != (left.level + 1, left.level + 2):
            continue
        evaluated += 1
        exact_semantics = all(
            item.exact_colored_replay and item.complete_atom_cover and
            item.chemistry_preserved and item.chirality_preserved and
            item.directed_ports_preserved and item.independent_occurrences >= 2
            and item.heldout_only for item in (left, middle, right))
        same_production = (
            left.normalized_production_key ==
            middle.normalized_production_key ==
            right.normalized_production_key)
        scales = left.adjacent_learned_scale, middle.adjacent_learned_scale
        equal_scales = (all(value is not None and value > tolerance and
                            math.isfinite(value) for value in scales) and
                        math.isclose(scales[0], scales[1],
                                     rel_tol=tolerance, abs_tol=tolerance))
        substitutions = (left.population_substitution,
                         middle.population_substitution)
        equal_population = (substitutions[0] is not None and
                            substitutions[0] == substitutions[1])
        if (global_guards and exact_semantics and same_production and
                equal_scales and equal_population):
            passing.append((left.level, middle.level, right.level))
    stationary = bool(passing)
    reason = "" if stationary else (
        "no leakage-clean exact chemistry/chirality/directed-port production "
        "survives three heldout levels with equal learned scales and exact "
        "population substitution")
    return ExponentialClaimAudit(
        stationary, evaluated, tuple(passing), raw_id_disjoint,
        spatial_domains_disjoint, input_permutation_invariant,
        proper_se3_invariant, shuffled_semantic_control_rejected,
        perturbed_semantic_control_rejected, amorphous_rejected,
        family_phi_cell_radius_leakage, reason)


def audit_missing_level_one_types() -> OptionalVocabularyAudit:
    """Inspect the three absent frozen IQC types without renumbering them."""
    from materials_gcts_dense_macro_matching import match_dense_macro_types
    from materials_gcts_iqc_reclustered_transfer_audit import (
        HELDOUT_PATCH_IDS, TRAIN_PATCH_IDS, _frozen_heldout_program,
        _grow_patches, _pack)
    from materials_gcts_irregular_port_atlas import (
        compile_irregular_port_program, enumerate_frozen_port_occurrences)
    from materials_gcts_macro_promotion import promote_macro_types
    from materials_gcts_port_graph_macros import mine_port_graph_macros
    from materials_gcts_promoted_type_quotient import quotient_macro_supports

    executions, raw_domains = _grow_patches()
    train_species, train_positions, train_patch = _pack(
        executions, TRAIN_PATCH_IDS)
    held_species, held_positions, _ = _pack(executions, HELDOUT_PATCH_IDS)
    training = compile_irregular_port_program(train_species, train_positions)
    held_enumeration = enumerate_frozen_port_occurrences(
        training, held_species, held_positions)
    held_program = _frozen_heldout_program(training, held_enumeration)
    mined = mine_port_graph_macros(
        training, maximum_nodes=3, include_boundary_relations=True)
    quotient = quotient_macro_supports(mined.macro_types)
    dense = match_dense_macro_types(held_program, quotient.quotient_macros)
    matched = {item.macro_id for item in dense.dense_macro_types
               if item.promotion_occurrences}
    missing = tuple(item for item in quotient.quotient_macros
                    if item.macro_id not in matched)
    atoms_by_type = {
        item.macro_id: {atom for occurrence in (
            item.promotion_occurrences or item.occurrences)
                        for atom in occurrence.atom_indices}
        for item in quotient.quotient_macros}
    evidence = []
    for item in missing:
        occurrences = item.promotion_occurrences or item.occurrences
        patches = tuple(sorted({train_patch[atom]
                                for occurrence in occurrences
                                for atom in occurrence.atom_indices}))
        other_atoms = set().union(*(
            atoms for macro_id, atoms in atoms_by_type.items()
            if macro_id != item.macro_id))
        atoms = atoms_by_type[item.macro_id]
        evidence.append(MissingTypeEvidence(
            item.macro_id, len(item.node_types), len(occurrences), patches,
            len(atoms), len(atoms - other_atoms), item.mdl_saving))

    promoted = promote_macro_types(training, quotient.quotient_macros, level=1)
    prototype_for_macro = {macro_id: type_id for type_id, macro_id in
                           promoted.prototype_macro_types}
    missing_prototypes = {prototype_for_macro[item.macro_id]
                          for item in missing
                          if item.macro_id in prototype_for_macro}
    next_mined = mine_port_graph_macros(
        promoted, maximum_nodes=3, include_boundary_relations=True)
    dependent = sum(bool(set(item.node_types) & missing_prototypes)
                    for item in next_mined.macro_types)
    held_atoms = {atom for item in dense.dense_macro_types
                  if item.promotion_occurrences
                  for occurrence in item.promotion_occurrences
                  for atom in occurrence.atom_indices}
    held_cover = len(held_atoms) / max(1, len(held_positions))
    redundant = all(item.atoms_unique_against_other_types == 0
                    for item in evidence)
    one_patch = all(len(item.training_patches) == 1 for item in evidence)
    # Exact one-sided Clopper-Pearson upper bound for zero presences in three
    # heldout patches.  It is deliberately wide: absence is not proof of rarity.
    upper = 1. - .05 ** (1. / len(HELDOUT_PATCH_IDS))
    observed_cover_safe = held_cover == 1. and redundant
    grammar_safe = observed_cover_safe and dependent == 0 and not evidence
    rare = upper < .1
    train_raw = set().union(*(raw_domains[index]
                              for index in TRAIN_PATCH_IDS))
    held_raw = set().union(*(raw_domains[index]
                             for index in HELDOUT_PATCH_IDS))
    mutually_disjoint = all(not left.intersection(right)
                            for index, left in enumerate(raw_domains)
                            for right in raw_domains[index + 1:])
    train_heldout_disjoint = not train_raw.intersection(held_raw)
    if not mutually_disjoint or not train_heldout_disjoint:
        raise AssertionError("predeclared IQC raw domains are not sealed")
    conclusion = (
        "optional for atom cover on these eight observed patches, but not "
        "optional for the frozen recursive grammar: all missing types have "
        "only one-patch train support, the zero-of-three upper bound is too "
        "wide to establish rarity, two next-level macros use missing promoted "
        "types, and frozen type-map closure is absent")
    return OptionalVocabularyAudit(
        len(train_positions), len(held_positions),
        mutually_disjoint, train_heldout_disjoint,
        len(quotient.quotient_macros), len(matched), tuple(evidence),
        held_cover, redundant, one_patch, upper, dependent, 0, False,
        observed_cover_safe, grammar_safe, rare, conclusion)


def audit_pipeline_adversaries() -> PipelineAdversarialAudit:
    """Exercise real generic geometry plus guarded semantic null controls."""
    import inspect
    from materials_gcts_boundary_recursive_safety_audit import (
        _configuration_cases, _fingerprint, _variant)
    from materials_gcts_irregular_port_atlas import (
        compile_irregular_port_program)
    from materials_gcts_semantic_action_quotient import (
        ExactActionTerminal, SemanticDescriptor,
        select_semantic_action_quotient)

    _, iqc, amorphous = _configuration_cases()
    base = _fingerprint(iqc.species, iqc.positions)
    permutation = base == _fingerprint(*_variant(iqc, "permuted"))
    rigid = base == _fingerprint(*_variant(iqc, "rigid"))
    amorphous_fingerprint = _fingerprint(
        amorphous.species, amorphous.positions)
    # Fingerprint field 10 is the admitted exact macro count.  With no macro,
    # a three-level stationary production is impossible.
    amorphous_rejected = amorphous_fingerprint[10] == 0

    terminals = tuple(ExactActionTerminal(
        f"patch-{index:02d}", f"alternative-{index:02d}",
        ("directed-path", 3), ("A", "B", "C"),
        (1., 1.4, 1.8), (("X", index),)) for index in range(18))
    null = select_semantic_action_quotient(
        terminals, descriptors=(SemanticDescriptor(
            "topology-null", "terminal", None, 1),),
        required_deployments=16)
    score = null.descriptor_scores[0]
    shuffled = (null.selected_descriptor is None and
                score.validation_mdl_saving <=
                score.shuffled_control_mdl_saving)
    perturbed = (null.selected_descriptor is None and
                 score.validation_mdl_saving <=
                 score.perturbation_control_mdl_saving)
    # Public seed/scorer crop radii define finite domains, but neither is
    # included in compile_irregular_port_program's learner payload.  There is
    # no expected recursive radius, family, phi, or cell field in this route.
    learner_parameters = set(inspect.signature(
        compile_irregular_port_program).parameters)
    forbidden = {"family", "family_label", "phi", "cell", "unit_cell",
                 "radius", "expected_radius", "target", "target_labels"}
    no_leakage = not learner_parameters.intersection(forbidden)
    passed = (permutation and rigid and shuffled and perturbed and
              amorphous_rejected and no_leakage)
    return PipelineAdversarialAudit(
        permutation, rigid, shuffled, perturbed, amorphous_rejected,
        no_leakage, passed)


def adversarial_contract_self_test() -> tuple[bool, ...]:
    """Return one positive and independent red mutations of every guard."""
    from dataclasses import replace
    base = tuple(HeldoutLevelEvidence(
        level, "exact-production", 2. if level < 2 else None,
        ((2, 1), (0, 1)) if level < 2 else None,
        True, True, True, True, True, 2) for level in range(3))
    keywords = dict(
        raw_id_disjoint=True, spatial_domains_disjoint=True,
        input_permutation_invariant=True, proper_se3_invariant=True,
        shuffled_semantic_control_rejected=True,
        perturbed_semantic_control_rejected=True, amorphous_rejected=True,
        family_phi_cell_radius_leakage=False)
    outcomes = [audit_exponential_claim(base, **keywords).stationary]
    for key in tuple(keywords):
        broken = dict(keywords)
        broken[key] = (True if key == "family_phi_cell_radius_leakage" else
                       False)
        outcomes.append(not audit_exponential_claim(
            base, **broken).stationary)
    mutations = (
        replace(base[2], normalized_production_key="different"),
        replace(base[1], adjacent_learned_scale=3.),
        replace(base[1], population_substitution=((3, 1), (0, 1))),
        replace(base[1], chemistry_preserved=False),
        replace(base[1], chirality_preserved=False),
        replace(base[1], directed_ports_preserved=False),
        replace(base[1], exact_colored_replay=False),
        replace(base[1], complete_atom_cover=False),
        replace(base[1], independent_occurrences=1),
        replace(base[1], heldout_only=False),
    )
    for mutation in mutations:
        candidate = (base[0], mutation, base[2])
        outcomes.append(not audit_exponential_claim(
            candidate, **keywords).stationary)
    return tuple(outcomes)
