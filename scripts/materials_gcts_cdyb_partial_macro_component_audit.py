#!/usr/bin/env python3
"""Train-window-only audit of exact partial-macro component decomposition."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_deep_hierarchy_benchmark import TRAIN_CENTERS
from materials_gcts_cdyb_hierarchical_growth_design import _ids
from materials_gcts_cdyb_partial_completion_marking_ablation import (
    TRAIN_SEED_RADIUS, TRAIN_TARGET_RADIUS, _compile, _frontier)
from materials_gcts_macro_derivation import _site_key
from materials_gcts_partial_macro_components import (
    decompose_atomic_frontier, decompose_partial_macro_completion)


@dataclass(frozen=True)
class CdYbPartialMacroComponentAudit:
    training_windows: int
    whole_macro_candidates: int
    whole_macro_exact: int
    whole_macro_mixed: int
    whole_emitted_sites: int
    whole_correct_sites: int
    attached_components: int
    attached_components_exact: int
    attached_components_mixed: int
    residual_subclusters: int
    residual_subclusters_exact: int
    atomic_frontier_components: int
    atomic_frontier_components_exact: int
    atomic_frontier_components_mixed: int
    atomic_frontier_emitted_sites: int
    atomic_frontier_correct_sites: int
    atomic_residual_subclusters: int
    every_atomic_candidate_complete_cover: bool
    represented_novel_sites: int
    original_novel_sites: int
    every_candidate_complete_cover: bool
    every_novel_union_preserved: bool
    target_used_only_for_training_scoring: bool
    evaluation_or_confirmatory_target_opened: bool


def evaluate() -> CdYbPartialMacroComponentAudit:
    atoms, _windows, _species, _positions, primitive, quotient, parent_map = \
        _compile()
    macros = {item.macro_id: item for item in quotient.alternative_macros}
    whole = whole_exact = whole_mixed = 0
    whole_sites = whole_correct_sites = 0
    attached = attached_exact = attached_mixed = residual = residual_exact = 0
    represented_sites = original_sites = 0
    covers = []
    unions = []
    atomic_count = atomic_exact = atomic_mixed = atomic_residual = 0
    atomic_sites = atomic_correct_sites = 0
    atomic_covers = []
    for center in TRAIN_CENTERS:
        lower, raw, frozen, emitted, seed_ids, rows = _frontier(
            atoms, primitive, quotient, parent_map, center,
            TRAIN_SEED_RADIUS, TRAIN_TARGET_RADIUS,
            open_training_target=True)
        target_ids = _ids(atoms, center, TRAIN_TARGET_RADIUS)
        target = {_site_key((atoms.symbols[index], atoms.positions[index]), .03)
                  for index in target_ids}
        seed = {_site_key((atoms.symbols[index], atoms.positions[index]), .03)
                for index in seed_ids}
        row_by_id = {item.candidate.candidate_id: item for item in rows}
        for completion, candidate in zip(raw.completions, frozen):
            whole += 1
            original = set(emitted[candidate.candidate_id])
            correct = original.intersection(target)
            whole_sites += len(original)
            whole_correct_sites += len(correct)
            whole_exact += bool(original) and original.issubset(target)
            whole_mixed += bool(correct) and not original.issubset(target)
            decomposition = decompose_partial_macro_completion(
                lower, macros[completion.macro_id], completion)
            atomic = decompose_atomic_frontier(
                lower, macros[completion.macro_id], completion)
            atomic_covers.append(atomic.complete_cover and
                                 atomic.exact_colored_union)
            for component in atomic.emission_components:
                keys = {_site_key(site, .03) for site in component.sites} - seed
                if not keys:
                    continue
                atomic_count += 1
                component_correct = keys.intersection(target)
                atomic_sites += len(keys)
                atomic_correct_sites += len(component_correct)
                atomic_exact += keys.issubset(target)
                atomic_mixed += (bool(component_correct) and
                                 not keys.issubset(target))
            atomic_residual += sum(bool(
                {_site_key(site, .03) for site in component.sites} - seed)
                for component in atomic.residual_subclusters)
            covers.append(decomposition.complete_cover)
            represented = set()
            for component in decomposition.emission_components:
                keys = {_site_key(site, .03) for site in component.sites} - seed
                represented.update(keys)
                if not keys:
                    continue
                attached += 1
                component_correct = keys.intersection(target)
                attached_exact += keys.issubset(target)
                attached_mixed += (bool(component_correct) and
                                   not keys.issubset(target))
            for component in decomposition.residual_subclusters:
                keys = {_site_key(site, .03) for site in component.sites} - seed
                represented.update(keys)
                if not keys:
                    continue
                residual += 1
                residual_exact += keys.issubset(target)
            represented_sites += len(represented)
            original_sites += len(original)
            unions.append(represented == original)
            if row_by_id[candidate.candidate_id].exact != \
                    (bool(original) and original.issubset(target)):
                raise AssertionError("training whole-macro label changed")
    return CdYbPartialMacroComponentAudit(
        len(TRAIN_CENTERS), whole, whole_exact, whole_mixed,
        whole_sites, whole_correct_sites,
        attached, attached_exact, attached_mixed, residual, residual_exact,
        atomic_count, atomic_exact, atomic_mixed,
        atomic_sites, atomic_correct_sites, atomic_residual,
        all(atomic_covers),
        represented_sites, original_sites, all(covers), all(unions),
        True, False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
