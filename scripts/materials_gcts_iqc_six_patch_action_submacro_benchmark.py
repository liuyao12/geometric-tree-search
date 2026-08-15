#!/usr/bin/env python3
"""Durable target-free six-patch IQC action-submacro benchmark.

The six executions are frozen before this audit.  Patch IDs namespace action
macro IDs, node IDs, and atom supports; no post-hoc target labels participate
in candidate enumeration, canonicalization, evidence selection, or MDL.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass

from materials_gcts_action_macro_promotion import promote_batch_action_macros
from materials_gcts_action_submacro_mining import (
    ActionMacroCorpusEntry, mine_action_submacros)
from materials_gcts_frozen_frontier_replay import fit_frozen_frontier_program
from materials_gcts_iqc_action_graph_corpus import (
    TRAINING_CENTER, _build_with_executions)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_oriented_overlap_ports import (
    is_proper_rotation, make_prototype)
from materials_gcts_sealed_iqc_causal_marking_benchmark import _crop


@dataclass(frozen=True)
class SixPatchActionSubmacroBenchmark:
    corpus_digest: str
    training_atoms: int
    source_patches: int
    action_macros: int
    action_macro_counts_by_patch: tuple[int, ...]
    exact_action_node_cover_by_patch: tuple[bool, ...]
    connected_induced_candidates: int
    exact_canonical_classes: int
    rejected_insufficient_disjoint_evidence: int
    rejected_nonpositive_mdl: int
    admitted_submacro_types: int
    admitted_node_count_histogram: tuple[tuple[int, int], ...]
    independent_patch_supported_types: int
    independent_patch_support_histogram: tuple[tuple[int, int], ...]
    proof_occurrence_count_histogram: tuple[tuple[int, int], ...]
    prototype_promotable_types: int
    independently_supported_prototype_promotable_types: int
    executable_next_level_program_emitted: bool
    recurrence_observed: bool
    hierarchy_stationarity_claimed: bool
    target_labels_stored: bool
    target_used: bool


def _histogram(values):
    return tuple(sorted(Counter(values).items()))


def _prototype_promotable(program, submacro) -> bool:
    """Exact gate for vocabulary promotion, not a generative-level claim."""
    if (not submacro.exact_induced_graph_verified or
            not submacro.proper_se3_colored_union_verified or
            submacro.mdl_saving <= 0 or not submacro.boundary_slots or
            len(submacro.occurrences) < 2 or
            any(not is_proper_rotation(child.rotation)
                for child in submacro.child_placements)):
        return False
    try:
        make_prototype(
            submacro.submacro_id, submacro.atom_union,
            tolerance=program.overlap_tolerance)
    except (AssertionError, ValueError):
        return False
    return True


def evaluate() -> SixPatchActionSubmacroBenchmark:
    corpus, executions, oracle = _build_with_executions()
    training, _ = _crop(oracle, TRAINING_CENTER, 11., "IQC-corpus-train")
    learned = compile_irregular_port_program(
        training.species, training.positions)
    frozen = fit_frozen_frontier_program(learned)

    entries = []
    macro_counts = []
    exact_covers = []
    for patch, execution in zip(corpus.patches, executions):
        promoted = promote_batch_action_macros(frozen, execution)
        macro_counts.append(len(promoted.macros))
        exact_covers.append(promoted.exact_cover_of_accepted_nodes)
        entries.extend(ActionMacroCorpusEntry(str(patch.patch_id), macro)
                       for macro in promoted.macros)

    mined = mine_action_submacros(frozen, tuple(entries))
    patch_supports = tuple(len({occurrence.patch_id
                                for occurrence in submacro.occurrences})
                           for submacro in mined.submacro_types)
    promotable = tuple(_prototype_promotable(frozen, submacro)
                       for submacro in mined.submacro_types)
    independent = tuple(count >= 2 for count in patch_supports)
    return SixPatchActionSubmacroBenchmark(
        corpus.corpus_digest, corpus.training_atoms, mined.source_patches,
        mined.source_action_macros, tuple(macro_counts), tuple(exact_covers),
        mined.connected_induced_candidates, mined.exact_canonical_classes,
        mined.rejected_insufficient_disjoint_evidence,
        mined.rejected_nonpositive_mdl, len(mined.submacro_types),
        _histogram(len(item.node_types) for item in mined.submacro_types),
        sum(independent), _histogram(patch_supports),
        _histogram(len(item.occurrences) for item in mined.submacro_types),
        sum(promotable),
        sum(left and right for left, right in zip(independent, promotable)),
        False, bool(mined.submacro_types), False,
        corpus.target_labels_stored,
        corpus.target_used_during_execution or mined.target_used)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
