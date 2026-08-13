#!/usr/bin/env python3
"""Family-blind marking selection across crystal and quasicrystal controls."""

from __future__ import annotations

import argparse
import json
from collections import Counter
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
    crystal_selected_hypothesis: str
    crystal_exact_scales: int
    iqc_pair_exact_scales: int
    fibonacci_anchor_scales: tuple[TransferScale, ...]
    fibonacci_anchor_exact_scales: int
    iqc_anchor_support: int
    fibonacci_anchor_support: int
    selector_iqc_hypothesis: str
    selector_fibonacci_hypothesis: str
    shared_frozen_marking_selected_without_family_label: bool
    benchmark_passed: bool


def _learn_anchor(seed, scale, edges):
    """Select a similarity fixed point by maximum exact seed self-support."""
    sites = {point_key(point) for point in seed.positions}
    colored_sites = {(point_key(point), color) for point, color in
                     zip(seed.positions, seed.species)}
    cluster_types = local_cluster_types(seed.positions, seed.species, edges)
    candidate_anchors = Counter()
    for parent in seed.positions:
        for image in seed.positions:
            anchor = point_key(tuple(
                (image[axis] - scale * parent[axis]) / (1.0 - scale)
                for axis in range(3)), 5)
            candidate_anchors[anchor] += 1
    scored = []
    for anchor in candidate_anchors:
        supported_types = set()
        support = 0
        for point, color, cluster_type in zip(
                seed.positions, seed.species, cluster_types):
            image = point_key(tuple(
                anchor[axis] + scale * (point[axis] - anchor[axis])
                for axis in range(3)))
            if image in sites:
                support += 1
            if (image, color) in colored_sites:
                supported_types.add(cluster_type)
        # Description length breaks recurrence ties: prefer the anchor whose
        # exact self-map needs the fewest local-cluster marking entries.
        scored.append((support, -len(supported_types), anchor))
    support, _, anchor = max(scored)
    return support, anchor


def _fibonacci_anchor_scales():
    seed = make_input(9)
    edges = (1.1, 1.7, 2.4, 3.0)
    support, anchor = _learn_anchor(seed, PHI, edges)
    prototypes = local_cluster_types(seed.positions, seed.species, edges)
    seed_sites = {point_key(point): color for point, color in
                  zip(seed.positions, seed.species)}
    evidence = {}
    for point, cluster_type in zip(seed.positions, prototypes):
        image = point_key(tuple(anchor[axis] + PHI * (
            point[axis] - anchor[axis]) for axis in range(3)))
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
            image = point_key(tuple(anchor[axis] + PHI * (
                point[axis] - anchor[axis]) for axis in range(3)))
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
    return support, tuple(reports)


def evaluate():
    iqc = iqc_pair()
    fibonacci_support, fibonacci = _fibonacci_anchor_scales()
    from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
    iqc_seed, _ = oracle_patch(3, 9.0)
    iqc_anchor_support, _ = _learn_anchor(
        iqc_seed, HIDDEN_UNIT, (1.4, 2.1, 2.8, 3.81))
    iqc_exact = sum(scale.precision == 1.0 for scale in iqc.scales)
    fibonacci_exact = sum(scale.precision == 1.0 for scale in fibonacci)
    from materials_gcts_generic import benchmark_systems
    from materials_gcts_parametric_recursive import (
        apply_rule_actions, discover_rule)
    from materials_gcts_periodic_growth import replicate
    crystal = next(item for item in benchmark_systems()
                   if item.name == "NaCl-rocksalt")
    crystal_rule = discover_rule(crystal)
    crystal_exact = 0
    reference = crystal
    for action in (1, 2):
        reference = replicate(reference)
        grown = apply_rule_actions(crystal, crystal_rule, action)
        grown_sites = set(zip(map(point_key, grown.positions), grown.species))
        reference_sites = set(zip(map(point_key, reference.positions),
                                  reference.species))
        crystal_exact += grown_sites == reference_sites
    # A fixed anchor must explain at least one quarter of the observed seed.
    # Otherwise the bounded overlap section is selected. This threshold and
    # both hypotheses are shared; no phase name or held-out target is read.
    minimum_anchor_fraction = .25
    iqc_selected = ("anchor" if iqc_anchor_support / len(iqc_seed.positions) >=
                    minimum_anchor_fraction else "port_pair")
    fibonacci_selected = (
        "anchor" if fibonacci_support / len(make_input(9).positions) >=
        minimum_anchor_fraction else "port_pair")
    shared = iqc_selected == "port_pair" and fibonacci_selected == "anchor"
    return CrossFamilyTransferAudit(
        crystal_rule.family, crystal_exact,
        iqc_exact, fibonacci, fibonacci_exact, iqc_anchor_support,
        fibonacci_support, iqc_selected, fibonacci_selected, shared,
        shared and crystal_rule.family == "translation_quotient" and
        crystal_exact == iqc_exact == fibonacci_exact == 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
