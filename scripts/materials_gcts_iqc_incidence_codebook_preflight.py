#!/usr/bin/env python3
"""Ten-nucleus development gate for a finite IQC incidence codebook."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, replace

from materials_gcts_incidence_codebook_marking import (
    IncidenceCodebookSpec, fit_incidence_codebook,
    incidence_codebook_digest, incidence_codebook_similarities,
    incidence_codebook_view)
from materials_gcts_incidence_token_marking import IncidenceTokenExample
from materials_gcts_iqc_incidence_geometry_selection import _ranked_antichain
from materials_gcts_iqc_orbit_disagreement_preflight import (
    NEXT_CONFIRMATION_CENTER, _development_groups)
from materials_gcts_iqc_symmetry_orbit_channel_preflight import (
    ACTIONS_PER_NUCLEUS)


MESSAGE_FAMILIES = (
    "role-occupied-message-node",
    "role-occupied-message-edge",
    "role-occupied-message-graph",
)
LOCAL_FAMILIES = (
    "vote", "parent-multiplicity", "source-colors", "predicted-colors",
    "coarse-role", "role-support", "occupied-count", "occupied-shell",
    "occupied-shell-colorless",
)
CODEBOOK_GRID = tuple(
    IncidenceCodebookSpec(families, nearest, minimum_groups)
    for families in (
        MESSAGE_FAMILIES, MESSAGE_FAMILIES[:2],
        MESSAGE_FAMILIES + LOCAL_FAMILIES)
    for nearest in (1, 2) for minimum_groups in (2, 3))


@dataclass(frozen=True)
class CodebookAudit:
    spec: IncidenceCodebookSpec
    fold_prototype_counts: tuple[int, ...]
    fold_model_digest: str
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int


@dataclass(frozen=True)
class IncidenceCodebookPreflight:
    codebook_grid: tuple[IncidenceCodebookSpec, ...]
    audits: tuple[CodebookAudit, ...]
    selected_spec: IncidenceCodebookSpec
    selected_correct_by_group: tuple[int, ...]
    selected_actions: int
    selected_correct_actions: int
    selected_false_actions: int
    precision: float
    exact_groups: int
    candidate_graph_digest: str
    descriptor_digest: str
    exact_candidate_geometry_changed: bool
    selection_target_free: bool
    next_confirmation_center: tuple[float, float, float]
    next_confirmation_seed_or_target_accessed: bool
    development_gate_passed: bool
    honest_status: str


def evaluate() -> IncidenceCodebookPreflight:
    groups = _development_groups(
        joint_role_geometry=True, message_passing_rounds=1,
        message_distance_divisor=4, message_role_mode="coarse",
        message_encoding="incidence")
    positive_examples = tuple(tuple(IncidenceTokenExample(
        row.group, row.descriptor, True) for row in group if row.successful)
        for group in groups)
    accumulators = {spec: {"selected": [], "prototypes": [], "digests": []}
                    for spec in CODEBOOK_GRID}
    family_sets = tuple(dict.fromkeys(
        spec.token_families for spec in CODEBOOK_GRID))
    views_by_families = {families: tuple(tuple(incidence_codebook_view(
        row.descriptor, families) for row in group) for group in groups)
        for families in family_sets}
    recurrence_keys = tuple(dict.fromkeys(
        (spec.token_families, spec.minimum_groups)
        for spec in CODEBOOK_GRID))
    for families, minimum_groups in recurrence_keys:
        specs = tuple(spec for spec in CODEBOOK_GRID
                      if spec.token_families == families and
                      spec.minimum_groups == minimum_groups)
        maximum_prototypes = max(spec.nearest_prototypes for spec in specs)
        views = views_by_families[families]
        for heldout_index, rows in enumerate(groups):
            examples = tuple(row for index, group in enumerate(
                positive_examples) if index != heldout_index for row in group)
            model = fit_incidence_codebook(examples, spec=IncidenceCodebookSpec(
                families, maximum_prototypes, minimum_groups))
            similarities = tuple(incidence_codebook_similarities(
                model, view) for view in views[heldout_index])
            for spec in specs:
                accumulator = accumulators[spec]
                accumulator["prototypes"].append(len(model.prototypes))
                accumulator["digests"].append(incidence_codebook_digest(
                    replace(model, spec=spec)))
                scored = tuple((sum(values[:spec.nearest_prototypes]) /
                                max(1, len(values[:spec.nearest_prototypes])),
                                row)
                               for values, row in zip(similarities, rows))
                accumulator["selected"].append(_ranked_antichain(
                    scored, ACTIONS_PER_NUCLEUS))
    audits = []
    for spec in CODEBOOK_GRID:
        accumulator = accumulators[spec]
        selected_groups = accumulator["selected"]
        correct_by_group = tuple(sum(row.successful for row in selected)
                                 for selected in selected_groups)
        total = sum(map(len, selected_groups))
        correct = sum(correct_by_group)
        audits.append(CodebookAudit(
            spec, tuple(accumulator["prototypes"]), hashlib.sha256(repr(tuple(
                accumulator["digests"])).encode()).hexdigest(), correct_by_group,
            total, correct, total - correct,
            correct / total if total else 0.,
            sum(value == ACTIONS_PER_NUCLEUS for value in correct_by_group)))
    selected = max(audits, key=lambda row: (
        row.exact_groups, row.selected_correct_actions, row.precision,
        row.spec.minimum_groups, -len(row.spec.token_families),
        -row.spec.nearest_prototypes))
    passed = bool(selected.selected_actions == 20 and
                  selected.selected_correct_actions == 20 and
                  selected.exact_groups == 10)
    graph_digest = hashlib.sha256(repr(tuple(
        (row.group, row.point, row.color, row.minimum_distance)
        for group in groups for row in group)).encode()).hexdigest()
    descriptor_digest = hashlib.sha256(repr(tuple(
        (row.group, row.descriptor)
        for group in groups for row in group)).encode()).hexdigest()
    return IncidenceCodebookPreflight(
        CODEBOOK_GRID, tuple(audits), selected.spec,
        selected.selected_correct_by_group, selected.selected_actions,
        selected.selected_correct_actions, selected.selected_false_actions,
        selected.precision, selected.exact_groups, graph_digest,
        descriptor_digest, False, True, NEXT_CONFIRMATION_CENTER, False,
        passed, "finite incidence codebook passes ten-nucleus development"
        if passed else
        "finite incidence codebook remains below the development gate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
