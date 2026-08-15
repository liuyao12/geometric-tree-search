#!/usr/bin/env python3
"""Accounting audit for the clean supervised IQC action corpus."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from materials_gcts_iqc_clean_training_action_corpus import _build


@dataclass(frozen=True)
class CleanTrainingCorpusAudit:
    corpus: object
    seed_atom_counts: tuple[int, ...]
    public_domain_atom_counts: tuple[int, ...]
    seed_domains_inside_public_domains: bool
    every_public_domain_inside_training: bool
    pairwise_public_atom_overlaps: tuple[tuple[int, ...], ...]
    public_union_train_atoms: int
    public_union_train_coverage: float
    exact_actions_only: bool
    heldout_deployment_patches_used: bool


def evaluate():
    corpus, seeds, domains, training = _build()
    matrix = tuple(tuple(len(set(left).intersection(right))
                         for right in domains) for left in domains)
    public_union = set().union(*(set(domain) for domain in domains))
    return CleanTrainingCorpusAudit(
        corpus, tuple(map(len, seeds)), tuple(map(len, domains)),
        all(set(seed).issubset(domain)
            for seed, domain in zip(seeds, domains)),
        all(set(domain).issubset(training) for domain in domains), matrix,
        len(public_union), len(public_union) / len(training),
        all(item.exact_actions == len(item.edges)
            for item in corpus.patches), False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
