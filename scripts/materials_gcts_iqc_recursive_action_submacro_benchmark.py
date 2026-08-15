#!/usr/bin/env python3
"""Target-free next-level promotion/mining audit for six IQC patches."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_action_macro_promotion import promote_batch_action_macros
from materials_gcts_action_submacro_mining import (
    ActionMacroCorpusEntry, mine_action_submacros)
from materials_gcts_action_submacro_promotion import promote_action_submacros
from materials_gcts_frozen_frontier_replay import fit_frozen_frontier_program
from materials_gcts_iqc_action_graph_corpus import (
    TRAINING_CENTER, _build_with_executions)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_sealed_iqc_causal_marking_benchmark import _crop
from materials_gcts_sparse_occurrence_graph import reduce_occurrence_graph


@dataclass(frozen=True)
class RecursiveActionSubmacroBenchmark:
    corpus_digest: str
    initial_admitted_submacro_types: int
    promoted_prototypes: int
    promoted_dense_occurrences: int
    namespaced_support_atoms: int
    promoted_overlap_ports: int
    promoted_overlap_relations: int
    promoted_boundary_ports: int
    promoted_boundary_relations: int
    sparse_source_nodes: int
    sparse_source_edges: int
    sparse_retained_nodes: int
    sparse_retained_edges: int
    next_level_candidates: int
    next_level_exact_classes: int
    next_level_admitted_types: int
    next_level_quotient_types: int
    next_level_exact_quotient_classes: tuple[tuple[int, ...], ...]
    third_level_promoted_prototypes: int
    third_level_promoted_occurrences: int
    third_level_admitted_types: int
    third_level_quotient_types: int
    fourth_level_promoted_prototypes: int
    fourth_level_promoted_occurrences: int
    fourth_level_admitted_types: int
    fourth_level_quotient_types: int
    three_recursive_mined_levels_available: bool
    strict_stationary_audit_invoked: bool
    stationary: bool
    target_used: bool


def evaluate() -> RecursiveActionSubmacroBenchmark:
    corpus, executions, oracle = _build_with_executions()
    training, _ = _crop(oracle, TRAINING_CENTER, 11., "IQC-corpus-train")
    learned = compile_irregular_port_program(
        training.species, training.positions)
    frozen = fit_frozen_frontier_program(learned)
    entries = []
    for patch, execution in zip(corpus.patches, executions):
        promoted_actions = promote_batch_action_macros(frozen, execution)
        entries.extend(ActionMacroCorpusEntry(str(patch.patch_id), macro)
                       for macro in promoted_actions.macros)
    mined_actions = mine_action_submacros(frozen, tuple(entries))
    promoted, promotion = promote_action_submacros(
        frozen, mined_actions.submacro_types, tuple(entries))
    sparse = reduce_occurrence_graph(promoted)
    next_mined = mine_port_graph_macros(promoted, maximum_nodes=3)
    next_quotient = quotient_macro_supports(next_mined.macro_types)

    third_promoted_prototypes = third_promoted_occurrences = 0
    third_admitted = third_quotient_types = 0
    fourth_promoted_prototypes = fourth_promoted_occurrences = 0
    fourth_admitted = fourth_quotient_types = 0
    third_program = None
    third_quotient = None
    if next_quotient.quotient_macros:
        third_program = promote_macro_types(
            promoted, next_quotient.quotient_macros, level=3)
        third_promoted_prototypes = len(third_program.prototypes)
        third_promoted_occurrences = len(third_program.occurrences)
        third_mined = mine_port_graph_macros(
            third_program, maximum_nodes=3)
        third_admitted = len(third_mined.macro_types)
        third_quotient = quotient_macro_supports(third_mined.macro_types)
        third_quotient_types = third_quotient.quotient_types
        if third_quotient.quotient_macros:
            fourth_program = promote_macro_types(
                third_program, third_quotient.quotient_macros, level=4)
            fourth_promoted_prototypes = len(fourth_program.prototypes)
            fourth_promoted_occurrences = len(fourth_program.occurrences)
            fourth_mined = mine_port_graph_macros(
                fourth_program, maximum_nodes=3)
            fourth_admitted = len(fourth_mined.macro_types)
            fourth_quotient_types = quotient_macro_supports(
                fourth_mined.macro_types).quotient_types

    # The strict audit consumes three recursively mined MacroType levels.
    # Initial action-submacro admission supplies the promoted vocabulary but
    # is not silently treated as an atlas-resolved MacroType production.
    three_levels = bool(next_quotient.quotient_types and
                        third_quotient_types and fourth_quotient_types)
    return RecursiveActionSubmacroBenchmark(
        corpus.corpus_digest, len(mined_actions.submacro_types),
        promotion.promoted_types, promotion.promoted_occurrences,
        promotion.namespaced_support_atoms, promotion.overlap_ports,
        promotion.overlap_relations, promotion.boundary_ports,
        promotion.boundary_relations, sparse.source_nodes,
        sparse.source_edges, len(sparse.retained_nodes),
        len(sparse.retained_edges), next_mined.rooted_connected_candidates,
        next_mined.exact_geometry_classes, len(next_mined.macro_types),
        next_quotient.quotient_types, next_quotient.exact_classes,
        third_promoted_prototypes, third_promoted_occurrences,
        third_admitted, third_quotient_types,
        fourth_promoted_prototypes, fourth_promoted_occurrences,
        fourth_admitted, fourth_quotient_types, three_levels,
        False, False,
        corpus.target_used_during_execution or promotion.target_used or
        promoted.target_used)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
