#!/usr/bin/env python3
"""Train-only recurrent-core selection across independent patch namespaces."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import Hashable, Sequence


@dataclass(frozen=True)
class ResidualAtomTerminal:
    patch_id: Hashable
    atom_index: int
    species: Hashable
    position: tuple[float, float, float]


@dataclass(frozen=True)
class MacroPatchEvidence:
    macro_id: int
    occurrence_count: int
    patch_ids: tuple[Hashable, ...]
    occurrences_by_patch: tuple[tuple[Hashable, int], ...]
    every_occurrence_patch_local: bool
    selected: bool


@dataclass(frozen=True)
class RecurrentCoreSelection:
    training_patch_ids: tuple[Hashable, ...]
    strict_majority_threshold: int
    input_macro_ids: tuple[int, ...]
    selected_macro_ids: tuple[int, ...]
    rejected_macro_ids: tuple[int, ...]
    selected_macros: tuple[object, ...]
    evidence: tuple[MacroPatchEvidence, ...]
    selected_covered_atom_indices: tuple[int, ...]
    residual_atom_terminals: tuple[ResidualAtomTerminal, ...]
    complete_atom_representation: bool
    representation_certificate_digest: str
    original_macro_ids_preserved: bool
    target_or_heldout_used: bool


def select_recurrent_macro_core(
    macros: Sequence[object], species: Sequence[Hashable],
    positions: Sequence[Sequence[float]], atom_patch_ids: Sequence[Hashable],
    *, training_patch_ids: Sequence[Hashable] | None = None,
) -> RecurrentCoreSelection:
    """Retain types recurring in a strict majority of independent patches.

    ``promotion_occurrences`` is used when present, otherwise the immutable
    admission occurrences are used.  Occurrences spanning namespaces are
    invalid evidence and can never help a type pass the recurrence gate.
    Residual atoms remain exact terminals, making the selected core plus the
    residual list a complete representation of the training corpus.
    """
    if not (len(species) == len(positions) == len(atom_patch_ids)):
        raise ValueError("species, positions, and patch IDs must align")
    if training_patch_ids is None:
        patch_ids = tuple(sorted(set(atom_patch_ids), key=repr))
    else:
        patch_ids = tuple(training_patch_ids)
        if len(set(patch_ids)) != len(patch_ids):
            raise ValueError("training patch namespaces must be unique")
        unknown = set(atom_patch_ids).difference(patch_ids)
        if unknown:
            raise ValueError("atom belongs to a non-training patch namespace")
    if not patch_ids:
        raise ValueError("at least one training patch is required")
    threshold = len(patch_ids) // 2 + 1
    ordered = tuple(sorted(macros, key=lambda item: item.macro_id))
    macro_ids = tuple(item.macro_id for item in ordered)
    if len(set(macro_ids)) != len(macro_ids):
        raise ValueError("macro IDs must be unique")

    selected = []
    evidence = []
    covered = set()
    for macro in ordered:
        occurrences = (getattr(macro, "promotion_occurrences", ()) or
                       getattr(macro, "occurrences", ()))
        counts = {}
        patch_local = True
        local_occurrences = []
        for occurrence in occurrences:
            indices = tuple(occurrence.atom_indices)
            if any(index < 0 or index >= len(species) for index in indices):
                raise ValueError("macro occurrence references an unknown atom")
            namespaces = {atom_patch_ids[index] for index in indices}
            if len(namespaces) != 1:
                patch_local = False
                continue
            patch_id = next(iter(namespaces))
            counts[patch_id] = counts.get(patch_id, 0) + 1
            local_occurrences.append(indices)
        admitted = patch_local and len(counts) >= threshold
        if admitted:
            selected.append(macro)
            for indices in local_occurrences:
                covered.update(indices)
        evidence.append(MacroPatchEvidence(
            macro.macro_id, len(occurrences),
            tuple(sorted(counts, key=repr)),
            tuple(sorted(counts.items(), key=lambda item: repr(item[0]))),
            patch_local, admitted))

    residual = tuple(ResidualAtomTerminal(
        atom_patch_ids[index], index, species[index],
        tuple(float(value) for value in positions[index]))
                     for index in range(len(species)) if index not in covered)
    selected_ids = tuple(item.macro_id for item in selected)
    rejected_ids = tuple(item for item in macro_ids
                         if item not in set(selected_ids))
    represented = covered.union(item.atom_index for item in residual)
    complete = (represented == set(range(len(species))) and
                not covered.intersection(item.atom_index for item in residual))
    certificate = hashlib.sha256(repr((
        selected_ids, tuple(sorted(covered)), residual, complete
    )).encode("utf-8")).hexdigest()
    return RecurrentCoreSelection(
        patch_ids, threshold, macro_ids, selected_ids, rejected_ids,
        tuple(selected), tuple(evidence), tuple(sorted(covered)), residual,
        complete, certificate,
        selected_ids == tuple(item.macro_id for item in selected), False)


def filter_quotient_by_recurrent_core(quotient, selection):
    """Freeze a recurrent subset without renumbering exact geometry classes."""
    selected_ids = set(selection.selected_macro_ids)
    available_ids = {item.macro_id for item in quotient.quotient_macros}
    if not selected_ids.issubset(available_ids):
        raise ValueError("recurrent selection contains an unknown quotient ID")
    selected_macros = tuple(item for item in quotient.quotient_macros
                            if item.macro_id in selected_ids)
    derivations = tuple(item for item in quotient.derivation_classes
                        if item.geometry_class_id in selected_ids)
    alternatives = []
    cursor = 0
    for geometry in quotient.derivation_classes:
        width = len(geometry.alternatives)
        block = quotient.alternative_macros[cursor:cursor + width]
        if len(block) != width:
            raise ValueError("incomplete exact alternative block")
        if geometry.geometry_class_id in selected_ids:
            alternatives.extend(block)
        cursor += width
    if cursor != len(quotient.alternative_macros):
        raise ValueError("unmapped exact alternative records")
    if any(value < 0 or value >= len(quotient.exact_classes)
           for value in selected_ids):
        raise ValueError("geometry class ID cannot index exact support class")
    return replace(
        quotient, quotient_types=len(selected_macros),
        quotient_macros=selected_macros,
        exact_classes=tuple(quotient.exact_classes[index]
                            for index in sorted(selected_ids)),
        derivation_classes=derivations,
        alternative_macros=tuple(alternatives),
        retained_promotion_occurrences=sum(
            len(item.promotion_occurrences) for item in selected_macros))
