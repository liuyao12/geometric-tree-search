#!/usr/bin/env python3
"""Post-hoc domain/exactness audit of the target-free action corpus."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from materials_gcts_frozen_frontier_replay import _site_key
from materials_gcts_iqc_action_graph_corpus import (
    PATCH_CENTERS, TRAINING_CENTER, IQCActionGraphCorpus,
    _build_with_executions)
from materials_gcts_sealed_iqc_causal_marking_benchmark import _crop


@dataclass(frozen=True)
class PatchExactnessAudit:
    patch_id: int
    center: tuple[float, float, float]
    target_atoms: int
    accepted_actions: int
    proposed_unique_atoms: int
    correct_unique_atoms: int
    wrong_unique_atoms: int
    precision: float
    posthoc_exact: bool


@dataclass(frozen=True)
class ActionGraphCorpusAudit:
    corpus: IQCActionGraphCorpus
    training_target_raw_id_overlaps: tuple[int, ...]
    pairwise_target_raw_id_overlaps: tuple[tuple[int, ...], ...]
    every_patch_disjoint_from_training: bool
    every_patch_pair_disjoint: bool
    patch_exactness: tuple[PatchExactnessAudit, ...]
    exact_patches: tuple[int, ...]
    noisy_patches: tuple[int, ...]
    corpus_filtered_by_posthoc_target: bool
    scoring_performed_after_all_executions: bool


def evaluate():
    corpus, executions, oracle = _build_with_executions()
    _, training_ids = _crop(
        oracle, TRAINING_CENTER, 11., "IQC-corpus-train-audit")
    targets = tuple(_crop(
        oracle, center, 11., f"IQC-corpus-target-audit-{index}")
                    for index, center in enumerate(PATCH_CENTERS))
    target_ids = tuple(ids for _, ids in targets)
    train_overlap = tuple(len(set(training_ids).intersection(ids))
                          for ids in target_ids)
    pairwise = tuple(tuple(
        (0 if left == right else
         len(set(target_ids[left]).intersection(target_ids[right])))
        for right in range(len(target_ids)))
                     for left in range(len(target_ids)))
    reports = []
    for patch, center, result, (target, _) in zip(
            corpus.patches, PATCH_CENTERS, executions, targets):
        initial = {_site_key(site, .03) for site in result.initial_sites}
        proposed = {_site_key(site, .03) for site in result.sites} - initial
        target_keys = {_site_key(site, .03)
                       for site in zip(target.species, target.positions)}
        correct = proposed.intersection(target_keys)
        reports.append(PatchExactnessAudit(
            patch.patch_id, center, len(target.positions),
            patch.action_nodes, len(proposed), len(correct),
            len(proposed - target_keys), len(correct) / max(1, len(proposed)),
            proposed == correct and bool(proposed)))
    reports = tuple(reports)
    return ActionGraphCorpusAudit(
        corpus, train_overlap, pairwise, not any(train_overlap),
        all(pairwise[left][right] == 0 for left in range(len(pairwise))
            for right in range(left + 1, len(pairwise))), reports,
        tuple(item.patch_id for item in reports if item.posthoc_exact),
        tuple(item.patch_id for item in reports if not item.posthoc_exact),
        False, True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
