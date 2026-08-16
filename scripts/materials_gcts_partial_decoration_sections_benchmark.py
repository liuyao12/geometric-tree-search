#!/usr/bin/env python3
"""Compose unseen cluster decorations from train-observed local sections."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass

from materials_gcts_geometry_decoration_vocabulary_benchmark import (
    _decorations)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_recurrent_macro_execution_benchmark import (
    compile_disjoint_iqc_execution_fixture)


@dataclass(frozen=True)
class PartialDecorationSectionAudit:
    training_atoms: int
    heldout_atoms: int
    geometry_types: int
    train_occurrences: int
    heldout_occurrences: int
    train_full_decoration_alternatives: int
    train_unary_states: int
    train_pair_states: int
    lopo_occurrences: int
    lopo_modal_exact_accuracy: float
    lopo_factor_exact_accuracy: float
    lopo_modal_site_accuracy: float
    lopo_factor_site_accuracy: float
    heldout_modal_exact_accuracy: float
    heldout_factor_exact_accuracy: float
    heldout_modal_site_accuracy: float
    heldout_factor_site_accuracy: float
    heldout_factor_predictions_unseen_as_whole: int
    heldout_unseen_whole_predictions_exact: int
    factor_improves_heldout_exact: bool
    factor_improves_heldout_sites: bool
    target_species_used_for_fit_or_model_selection: bool
    family_phi_cell_or_potential_used: bool
    partial_section_gate_passed: bool
    limitation: str


@dataclass(frozen=True)
class _TreeModel:
    labels: tuple[str, ...]
    parent: tuple[int, ...]
    root_counts: tuple[tuple[str, int], ...]
    conditional_counts: tuple[
        tuple[int, tuple[tuple[tuple[str, str], int], ...]], ...]


def _mutual_information(rows, left, right, labels, alpha=1.):
    pair = Counter((row[left], row[right]) for row in rows)
    left_counts = Counter(row[left] for row in rows)
    right_counts = Counter(row[right] for row in rows)
    total = len(rows) + alpha * len(labels) ** 2
    result = 0.
    for a in labels:
        for b in labels:
            pab = (pair[a, b] + alpha) / total
            pa = (left_counts[a] + alpha * len(labels)) / total
            pb = (right_counts[b] + alpha * len(labels)) / total
            result += pab * math.log(pab / (pa * pb))
    return result


def _maximum_spanning_tree(rows, size, labels):
    if size == 1:
        return (-1,)
    edges = sorted((
        (_mutual_information(rows, left, right, labels), left, right)
        for left in range(size) for right in range(left + 1, size)),
        key=lambda item: (-item[0], item[1], item[2]))
    components = list(range(size))

    def find(node):
        while components[node] != node:
            components[node] = components[components[node]]
            node = components[node]
        return node

    adjacency = defaultdict(list)
    for _weight, left, right in edges:
        a, b = find(left), find(right)
        if a == b:
            continue
        components[b] = a
        adjacency[left].append(right)
        adjacency[right].append(left)
        if sum(len(value) for value in adjacency.values()) == 2 * (size - 1):
            break
    parent = [-2] * size
    parent[0] = -1
    stack = [0]
    while stack:
        node = stack.pop()
        for child in sorted(adjacency[node], reverse=True):
            if parent[child] != -2:
                continue
            parent[child] = node
            stack.append(child)
    if any(value == -2 for value in parent):
        raise AssertionError("factor tree is disconnected")
    return tuple(parent)


def _fit_tree(rows):
    if not rows:
        raise ValueError("at least one decoration is required")
    size = len(rows[0])
    if any(len(row) != size for row in rows):
        raise ValueError("decoration sizes disagree")
    labels = tuple(sorted({label for row in rows for label in row}))
    parent = _maximum_spanning_tree(rows, size, labels)
    root = Counter(row[0] for row in rows)
    conditionals = []
    for child in range(1, size):
        p = parent[child]
        counts = Counter((row[p], row[child]) for row in rows)
        conditionals.append((child, tuple(sorted(counts.items()))))
    return _TreeModel(labels, parent, tuple(sorted(root.items())),
                      tuple(conditionals))


def _predict(model, alpha=1.):
    labels = model.labels
    root_counts = Counter(dict(model.root_counts))
    conditional = {child: Counter(dict(counts))
                   for child, counts in model.conditional_counts}
    children = defaultdict(list)
    for child, parent in enumerate(model.parent):
        if parent >= 0:
            children[parent].append(child)

    cache = {}

    def solve(node, parent_label=None):
        cache_key = node, parent_label
        if cache_key in cache:
            return cache[cache_key]
        choices = {}
        pointers = {}
        for label in labels:
            if parent_label is None:
                total = sum(root_counts.values()) + alpha * len(labels)
                score = math.log((root_counts[label] + alpha) / total)
            else:
                counts = conditional[node]
                total = sum(counts[parent_label, candidate]
                            for candidate in labels) + alpha * len(labels)
                score = math.log((counts[parent_label, label] + alpha) / total)
            selected = {}
            for child in children[node]:
                child_scores, child_pointers = solve(child, label)
                best = max(child_scores, key=lambda item: (
                    child_scores[item], repr(item)))
                score += child_scores[best]
                selected[child] = (best, child_pointers[best])
            choices[label] = score
            pointers[label] = selected
        cache[cache_key] = choices, pointers
        return cache[cache_key]

    scores, pointers = solve(0)
    root = max(scores, key=lambda item: (scores[item], repr(item)))
    result = [None] * len(model.parent)

    def fill(node, label, selected):
        result[node] = label
        for child, (child_label, grandchildren) in selected.items():
            fill(child, child_label, grandchildren)

    fill(0, root, pointers[root])
    return tuple(result)


def _scores(actual, predicted):
    exact = sum(left == right for left, right in zip(actual, predicted))
    sites = sum(sum(a == b for a, b in zip(left, right))
                for left, right in zip(actual, predicted))
    total_sites = sum(len(row) for row in actual)
    return exact, sites, total_sites


def evaluate():
    fixture, open_target = compile_disjoint_iqc_execution_fixture()
    train_species = tuple(species for species, _point in fixture.training_sites)
    train_positions = tuple(point for _species, point in fixture.training_sites)
    geometry = compile_irregular_port_program(
        tuple("*" for _ in train_positions), train_positions)
    train_rows = _decorations(
        geometry, train_species, train_positions, geometry.occurrences,
        geometry.occurrence_supports)
    train_by_type = defaultdict(list)
    patch_by_occurrence = {}
    supports = dict(geometry.occurrence_supports)
    for occurrence, (type_id, decoration) in zip(
            geometry.occurrences, train_rows):
        train_by_type[type_id].append(decoration)
        patches = {fixture.training_patch_ids[atom]
                   for atom in supports[occurrence.occurrence_id]}
        if len(patches) != 1:
            raise AssertionError("primitive occurrence crosses train patches")
        patch_by_occurrence[occurrence.occurrence_id] = next(iter(patches))

    lopo_actual = []
    lopo_modal = []
    lopo_factor = []
    patch_ids = tuple(sorted(set(fixture.training_patch_ids)))
    for patch in patch_ids:
        fit_by_type = defaultdict(list)
        held_rows = []
        for occurrence, (type_id, decoration) in zip(
                geometry.occurrences, train_rows):
            if patch_by_occurrence[occurrence.occurrence_id] == patch:
                held_rows.append((type_id, decoration))
            else:
                fit_by_type[type_id].append(decoration)
        models = {type_id: _fit_tree(rows)
                  for type_id, rows in fit_by_type.items() if rows}
        modes = {type_id: Counter(rows).most_common(1)[0][0]
                 for type_id, rows in fit_by_type.items() if rows}
        for type_id, actual in held_rows:
            if type_id not in models:
                continue
            lopo_actual.append(actual)
            lopo_modal.append(modes[type_id])
            lopo_factor.append(_predict(models[type_id]))

    models = {type_id: _fit_tree(rows)
              for type_id, rows in train_by_type.items()}
    modes = {type_id: Counter(rows).most_common(1)[0][0]
             for type_id, rows in train_by_type.items()}
    target = open_target()
    enumeration = enumerate_frozen_port_occurrences(
        geometry, tuple("*" for _ in target.positions), target.positions)
    held_rows = _decorations(
        geometry, target.species, target.positions, enumeration.occurrences,
        enumeration.occurrence_supports)
    held_actual = []
    held_modal = []
    held_factor = []
    unseen_predictions = unseen_exact = 0
    alternatives = {type_id: set(rows)
                    for type_id, rows in train_by_type.items()}
    for type_id, actual in held_rows:
        factor = _predict(models[type_id])
        held_actual.append(actual)
        held_modal.append(modes[type_id])
        held_factor.append(factor)
        if factor not in alternatives[type_id]:
            unseen_predictions += 1
            unseen_exact += factor == actual

    lopo_modal_exact, lopo_modal_sites, lopo_sites = _scores(
        lopo_actual, lopo_modal)
    lopo_factor_exact, lopo_factor_sites, _ = _scores(
        lopo_actual, lopo_factor)
    held_modal_exact, held_modal_sites, held_sites = _scores(
        held_actual, held_modal)
    held_factor_exact, held_factor_sites, _ = _scores(
        held_actual, held_factor)
    # Report actual populated factor-table state counts, not dense capacity.
    unary_states = sum(len({row[index] for row in rows})
                       for rows in train_by_type.values()
                       for index in range(len(rows[0])))
    pair_states = sum(len({(row[left], row[right]) for row in rows})
                      for rows in train_by_type.values()
                      for left in range(len(rows[0]))
                      for right in range(left + 1, len(rows[0])))
    exact_accuracy = held_factor_exact / max(1, len(held_actual))
    site_accuracy = held_factor_sites / max(1, held_sites)
    gate = exact_accuracy >= .9 and site_accuracy >= .99
    return PartialDecorationSectionAudit(
        len(train_positions), len(target.positions), len(geometry.prototypes),
        len(geometry.occurrences), len(enumeration.occurrences),
        sum(len(set(rows)) for rows in train_by_type.values()),
        unary_states, pair_states, len(lopo_actual),
        lopo_modal_exact / max(1, len(lopo_actual)),
        lopo_factor_exact / max(1, len(lopo_actual)),
        lopo_modal_sites / max(1, lopo_sites),
        lopo_factor_sites / max(1, lopo_sites),
        held_modal_exact / max(1, len(held_actual)), exact_accuracy,
        held_modal_sites / max(1, held_sites), site_accuracy,
        unseen_predictions, unseen_exact,
        held_factor_exact > held_modal_exact,
        held_factor_sites > held_modal_sites,
        False, False, gate,
        "The factorized section predicts frozen geometry occurrences on "
        "supplied coordinates. It composes train-observed unary/pair species "
        "factors but is not an autonomous coordinate-growth model.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
