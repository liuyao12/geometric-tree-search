#!/usr/bin/env python3
"""Train-only exact quotient of macro supports before promotion.

The quotient identifies macro types whose *resulting colored atomic supports*
are congruent by a proper rigid motion.  It never changes atomic coordinates,
chemistry, occurrence poses, or the positive-MDL admission decision.  Within
each class a deterministic minimum-description representative supplies the
dictionary entry, while all exact train embeddings remain available to the
next-level cover/promotion.

Uniform-scale similarity is reported separately.  It is deliberately not an
execution equivalence because ``ClusterOccurrence`` stores SE(3), not scale;
merging such supports would silently change exact geometry.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Hashable, Sequence

from materials_gcts_oriented_overlap_ports import (
    fit_occurrence_pose, make_prototype)
from materials_gcts_port_graph_macros import MacroOccurrence, MacroType


@dataclass(frozen=True)
class MacroSupportQuotient:
    source_types: int
    quotient_types: int
    exact_classes: tuple[tuple[int, ...], ...]
    quotient_macros: tuple[MacroType, ...]
    source_promotion_occurrences: int
    retained_promotion_occurrences: int
    exact_train_support_cover_preserved: bool
    scale_similar_but_not_congruent_pairs: int
    chemistry_population_preserved: bool
    exact_geometry_preserved: bool
    improper_reflections_merged: bool
    uniform_scale_merged: bool
    target_or_material_metadata_used: bool


def _species_key(value: Hashable) -> str:
    return f"{type(value).__module__}.{type(value).__qualname__}:{value!r}"


def _population(macro: MacroType) -> tuple[tuple[str, int], ...]:
    labels = tuple(_species_key(species) for species, _ in macro.atom_union)
    return tuple(sorted((label, labels.count(label)) for label in set(labels)))


def scale_free_metric_key(macro: MacroType, tolerance: float = 1e-5) -> tuple:
    """Cheap reflection-insensitive diagnostic, never an admission key."""
    sites = macro.atom_union
    distances = [math.dist(left[1], right[1])
                 for index, left in enumerate(sites)
                 for right in sites[index + 1:]
                 if math.dist(left[1], right[1]) > tolerance]
    if not distances:
        return (_population(macro), ())
    scale = min(distances)
    per_site = []
    for index, (species, point) in enumerate(sites):
        neighborhood = tuple(sorted(
            (_species_key(other_species),
             round(math.dist(point, other_point) / scale / tolerance))
            for other, (other_species, other_point) in enumerate(sites)
            if other != index))
        per_site.append((_species_key(species), neighborhood))
    return _population(macro), tuple(sorted(per_site, key=repr))


def _dedupe_occurrences(values: Sequence[MacroOccurrence]) -> tuple[MacroOccurrence, ...]:
    chosen = {}
    for item in values:
        # Atom union is the execution support.  Keep a deterministic exact
        # derivation when several graph embeddings render that same support.
        key = tuple(item.atom_indices)
        rank = (item.node_occurrences, item.root_occurrence,
                item.maximum_cycle_residual)
        if key not in chosen or rank < chosen[key][0]:
            chosen[key] = rank, item
    return tuple(chosen[key][1] for key in sorted(chosen))


def quotient_macro_supports(
        macros: Sequence[MacroType], *, pose_tolerance: float = .03,
) -> MacroSupportQuotient:
    """Quotient exact colored supports using training data only.

    A representative is chosen by dictionary cost, then higher admitted MDL,
    then greater exact cover, then stable macro id.  Evidence occurrences and
    MDL remain those of that admitted representative; only the independent
    promotion/cover occurrence pool is united.
    """
    if pose_tolerance <= 0 or not math.isfinite(pose_tolerance):
        raise ValueError("pose_tolerance must be finite and positive")
    ordered = tuple(sorted(macros, key=lambda item: item.macro_id))
    prototypes = {item.macro_id: make_prototype(
        item.macro_id, item.atom_union, tolerance=pose_tolerance)
                  for item in ordered}
    groups: list[list[MacroType]] = []
    for macro in ordered:
        for group in groups:
            representative = group[0]
            if _population(macro) != _population(representative):
                continue
            try:
                fit_occurrence_pose(
                    0, prototypes[representative.macro_id], macro.atom_union,
                    tolerance=pose_tolerance)
            except ValueError:
                continue
            group.append(macro)
            break
        else:
            groups.append([macro])

    quotient = []
    exact_classes = []
    for new_id, group in enumerate(groups):
        representative = min(group, key=lambda item: (
            item.dictionary_tokens, -item.mdl_saving,
            -len(item.promotion_occurrences or item.occurrences),
            item.macro_id))
        promotion = _dedupe_occurrences(tuple(
            occurrence for member in group
            for occurrence in (member.promotion_occurrences or
                               member.occurrences)))
        quotient.append(replace(
            representative, macro_id=new_id,
            promotion_occurrences=promotion))
        exact_classes.append(tuple(item.macro_id for item in group))

    scale_groups = {}
    for macro in ordered:
        scale_groups.setdefault(scale_free_metric_key(macro), []).append(macro)
    exact_pair_count = sum(len(group) * (len(group) - 1) // 2
                           for group in groups)
    scale_pair_count = sum(len(group) * (len(group) - 1) // 2
                           for group in scale_groups.values())
    source_occurrences = sum(len(item.promotion_occurrences or item.occurrences)
                             for item in ordered)
    retained_occurrences = sum(len(item.promotion_occurrences)
                               for item in quotient)
    source_cover = {tuple(item.atom_indices) for macro in ordered
                    for item in (macro.promotion_occurrences or
                                 macro.occurrences)}
    retained_cover = {tuple(item.atom_indices) for macro in quotient
                      for item in macro.promotion_occurrences}
    return MacroSupportQuotient(
        len(ordered), len(quotient), tuple(exact_classes), tuple(quotient),
        source_occurrences, retained_occurrences,
        source_cover == retained_cover,
        max(0, scale_pair_count - exact_pair_count), True, True, False, False,
        False)
