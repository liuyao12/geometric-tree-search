#!/usr/bin/env python3
"""Red audit for one frozen cluster/port grammar across two QC families.

The benchmark intentionally reports failure until one model-selection rule,
learned without a family label or held-out target, chooses a marking that is
exact on both the icosahedral model set and the Fibonacci-product control.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_amplifying_pair_benchmark import evaluate as iqc_pair
from materials_gcts_fibonacci_3d import PHI, make_input
from materials_gcts_recursive_connections import (
    local_cluster_types, map_to_prototypes, point_key)


@dataclass(frozen=True)
class TransferScale:
    state_atoms: int
    target_atoms: int
    accepted_sites: int
    true_sites: int
    precision: float
    novel_recall: float


@dataclass(frozen=True)
class CrossFamilyTransferAudit:
    iqc_pair_exact_scales: int
    fibonacci_anchor_scales: tuple[TransferScale, ...]
    fibonacci_anchor_exact_scales: int
    shared_frozen_marking_selected_without_family_label: bool
    benchmark_passed: bool


def _fibonacci_anchor_scales():
    seed = make_input(9)
    edges = (1.1, 1.7, 2.4, 3.0)
    prototypes = local_cluster_types(seed.positions, seed.species, edges)
    seed_sites = {point_key(point): color for point, color in
                  zip(seed.positions, seed.species)}
    evidence = {}
    for point, cluster_type in zip(seed.positions, prototypes):
        image = point_key(tuple(PHI * value for value in point))
        if image in seed_sites:
            evidence.setdefault(cluster_type, []).append(seed_sites[image])
    reports = []
    for side, target_side in ((15, 24), (24, 39)):
        state, target = make_input(side), make_input(target_side)
        cluster_types = map_to_prototypes(
            local_cluster_types(state.positions, state.species, edges),
            tuple(set(prototypes)))
        known = {point_key(point) for point in state.positions}
        accepted = set()
        for point, cluster_type in zip(state.positions, cluster_types):
            if cluster_type not in evidence:
                continue
            image = point_key(tuple(PHI * value for value in point))
            if image in known:
                continue
            colors = evidence[cluster_type]
            color = min(set(colors), key=lambda item: (-colors.count(item), item))
            accepted.add((image, color))
        target_sites = set(zip(map(point_key, target.positions), target.species))
        known_sites = set(zip(map(point_key, state.positions), state.species))
        novel = target_sites - known_sites
        true = accepted & novel
        reports.append(TransferScale(
            len(state.positions), len(target.positions), len(accepted),
            len(true), len(true) / max(1, len(accepted)),
            len(true) / len(novel)))
    return tuple(reports)


def evaluate():
    iqc = iqc_pair()
    fibonacci = _fibonacci_anchor_scales()
    iqc_exact = sum(scale.precision == 1.0 for scale in iqc.scales)
    fibonacci_exact = sum(scale.precision == 1.0 for scale in fibonacci)
    # These are still two separately selected markings. This flag is the
    # actual transfer requirement and deliberately keeps the common gate red.
    shared = False
    return CrossFamilyTransferAudit(
        iqc_exact, fibonacci, fibonacci_exact, shared,
        shared and iqc_exact == fibonacci_exact == 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
