#!/usr/bin/env python3
"""Optimistic and alternative-consistent quotient hierarchy comparison."""

from __future__ import annotations

from dataclasses import dataclass

from materials_gcts_iqc_action_graph_corpus import _build_with_executions
from materials_gcts_iqc_reclustered_growth_corpus import _pack
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import (
    fit_derivation_alternative_marking, quotient_macro_supports)
from materials_gcts_recurring_action_submacro_audit import (
    PromotedSubmacroLevel, audit_promoted_submacro_levels)


@dataclass(frozen=True)
class DerivationHierarchyCase:
    mode: str
    admitted_types: tuple[int, ...]
    quotient_types: tuple[int, ...]
    artifact_occurrences: tuple[int, ...]
    derivation_alternatives: tuple[int, ...]
    derivation_supports: tuple[int, ...]
    bounded_marking_samples: tuple[int, ...]
    stationary_common_keys: int
    stationary_witnesses: int
    stationary: bool


def _case(base, mode):
    artifact = base
    admitted = []
    quotients = []
    occurrences = []
    alternatives = []
    supports = []
    samples = []
    levels = []
    for level in range(12):
        mined = mine_port_graph_macros(
            artifact, maximum_nodes=3, include_boundary_relations=True)
        quotient = quotient_macro_supports(mined.macro_types)
        admitted.append(len(mined.macro_types))
        quotients.append(quotient.quotient_types)
        occurrences.append(len(artifact.occurrences))
        alternatives.append(sum(len(item.alternatives)
                                for item in quotient.derivation_classes))
        supports.append(sum(len(item.occurrences)
                            for item in quotient.derivation_classes))
        samples.append(fit_derivation_alternative_marking(
            quotient).training_samples)
        if not quotient.quotient_macros:
            break
        levels.append(PromotedSubmacroLevel(
            level, artifact, quotient.quotient_macros))
        macros = (quotient.quotient_macros if mode == "optimistic-union" else
                  quotient.alternative_macros)
        artifact = promote_macro_types(
            artifact, macros, level=getattr(artifact, "level", 0) + 1,
            union_derivation_witnesses=mode == "optimistic-union")
    strict = audit_promoted_submacro_levels(levels)
    return DerivationHierarchyCase(
        mode, tuple(admitted), tuple(quotients), tuple(occurrences),
        tuple(alternatives), tuple(supports), tuple(samples),
        strict.common_normalized_keys, len(strict.witnesses),
        strict.stationary)


def evaluate():
    _, executions, _ = _build_with_executions()
    species, positions, _, _ = _pack(executions)
    base = compile_irregular_port_program(species, positions)
    return (_case(base, "optimistic-union"),
            _case(base, "alternative-consistent"))


if __name__ == "__main__":
    print(evaluate())
