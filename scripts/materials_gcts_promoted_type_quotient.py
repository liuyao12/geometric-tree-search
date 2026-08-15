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
from collections import Counter
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
    derivation_classes: tuple["GeometryClassDerivations", ...] = ()
    alternative_macros: tuple[MacroType, ...] = ()


@dataclass(frozen=True)
class DerivationAlternative:
    alternative_id: int
    source_macro_id: int
    node_types: tuple[int, ...]
    edges: tuple
    child_placements: tuple
    boundary_slots: tuple


@dataclass(frozen=True)
class SupportDerivationAlternatives:
    atom_indices: tuple[int, ...]
    alternatives: tuple[tuple[int, MacroOccurrence], ...]


@dataclass(frozen=True)
class GeometryClassDerivations:
    geometry_class_id: int
    source_macro_ids: tuple[int, ...]
    alternatives: tuple[DerivationAlternative, ...]
    occurrences: tuple[SupportDerivationAlternatives, ...]


@dataclass(frozen=True)
class DerivationAlternativeMarking:
    maximum_context_order: int
    exact_scores: tuple[tuple[tuple[int, tuple], tuple[tuple[int, int], ...]], ...]
    marginal_scores: tuple[tuple[int, tuple[tuple[int, int], ...]], ...]
    training_samples: int
    target_used: bool


def fit_derivation_alternative_marking(
        quotient: MacroSupportQuotient, *, maximum_context_order: int = 2,
) -> DerivationAlternativeMarking:
    """Fit a bounded train-only policy over already fixed exact alternatives."""
    if maximum_context_order < 0:
        raise ValueError("context order cannot be negative")
    exact = {}
    marginal = {}
    samples = 0
    for geometry in quotient.derivation_classes:
        alternatives = {item.alternative_id: item for item in
                        geometry.alternatives}
        for occurrence in geometry.occurrences:
            for alternative_id, _ in occurrence.alternatives:
                alternative = alternatives[alternative_id]
                incoming_values = [(
                    slot.direction, getattr(slot, "port_key",
                                            getattr(slot, "port", ())))
                    for slot in alternative.boundary_slots
                    if slot.direction == "incoming"]
                incoming = tuple(sorted(incoming_values, key=repr))
                context = incoming[:maximum_context_order]
                exact.setdefault((geometry.geometry_class_id, context),
                                 Counter())[alternative_id] += 1
                marginal.setdefault(geometry.geometry_class_id,
                                    Counter())[alternative_id] += 1
                samples += 1
    return DerivationAlternativeMarking(
        maximum_context_order,
        tuple(sorted((key, tuple(sorted(value.items())))
                     for key, value in exact.items())),
        tuple(sorted((key, tuple(sorted(value.items())))
                     for key, value in marginal.items())),
        samples, False)


def rank_derivation_alternatives(
        quotient: MacroSupportQuotient,
        marking: DerivationAlternativeMarking, geometry_class_id: int,
        incoming_context: Sequence = (),
) -> tuple[int, ...]:
    """Rank fixed alternatives; never changes their geometry or incidence."""
    geometry = next((item for item in quotient.derivation_classes
                     if item.geometry_class_id == geometry_class_id), None)
    if geometry is None:
        raise ValueError("unknown geometry class")
    context = tuple(sorted(incoming_context, key=repr))[
        :marking.maximum_context_order]
    exact = dict(marking.exact_scores)
    marginal = dict(marking.marginal_scores)
    exact_count = dict(exact.get((geometry_class_id, context), ()))
    marginal_count = dict(marginal.get(geometry_class_id, ()))
    return tuple(sorted((item.alternative_id for item in geometry.alternatives),
                        key=lambda item: (-exact_count.get(item, 0),
                                          -marginal_count.get(item, 0), item)))


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
    derivation_classes = []
    alternative_macros = []
    for new_id, group in enumerate(groups):
        representative = min(group, key=lambda item: (
            item.dictionary_tokens, -item.mdl_saving,
            -len(item.promotion_occurrences or item.occurrences),
            item.macro_id))
        all_derivations = tuple(
            occurrence for member in group
            for occurrence in (member.promotion_occurrences or
                               member.occurrences))
        promotion = _dedupe_occurrences(all_derivations)
        quotient.append(replace(
            representative, macro_id=new_id,
            promotion_occurrences=promotion,
            promotion_derivations=all_derivations))
        exact_classes.append(tuple(item.macro_id for item in group))
        alternatives = tuple(DerivationAlternative(
            index, member.macro_id, member.node_types, member.edges,
            member.child_placements, member.boundary_slots)
                             for index, member in enumerate(sorted(
                                 group, key=lambda item: item.macro_id)))
        alternative_id = {item.source_macro_id: item.alternative_id
                          for item in alternatives}
        by_support = {}
        for member in group:
            for occurrence in (member.promotion_occurrences or
                               member.occurrences):
                by_support.setdefault(tuple(occurrence.atom_indices), []).append(
                    (alternative_id[member.macro_id], occurrence))
        derivation_classes.append(GeometryClassDerivations(
            new_id, tuple(item.macro_id for item in group), alternatives,
            tuple(SupportDerivationAlternatives(
                support, tuple(sorted(values, key=lambda item: (
                    item[0], item[1].node_occurrences))))
                  for support, values in sorted(by_support.items()))))
        for member in sorted(group, key=lambda item: item.macro_id):
            alternative_macros.append(replace(
                member, macro_id=len(alternative_macros),
                promotion_derivations=(member.promotion_occurrences or
                                       member.occurrences)))

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
        False, tuple(derivation_classes), tuple(alternative_macros))
