#!/usr/bin/env python3
"""Focused and metamorphic tests for train-only recurrent-core selection."""

from dataclasses import dataclass

from materials_gcts_port_graph_macros import MacroOccurrence
from materials_gcts_recurrent_core_selector import select_recurrent_macro_core


@dataclass(frozen=True)
class _Macro:
    macro_id: int
    promotion_occurrences: tuple[MacroOccurrence, ...]
    occurrences: tuple[MacroOccurrence, ...] = ()


def _occurrence(identifier, atoms):
    return MacroOccurrence(identifier, (identifier,), tuple(atoms), 0.)


def _fixture(namespace_labels=(0, 1, 2, 3, 4)):
    species = tuple("A" for _ in range(10))
    positions = tuple((float(index), 0., 0.) for index in range(10))
    patch_ids = tuple(label for label in namespace_labels for _ in range(2))
    recurrent = _Macro(17, tuple(_occurrence(index, (2 * index, 2 * index + 1))
                                 for index in (0, 1, 2)))
    one_patch = _Macro(91, (
        _occurrence(10, (6, 7)), _occurrence(11, (6, 7)),
        _occurrence(12, (6, 7))))
    return species, positions, patch_ids, (one_patch, recurrent)


def test_strict_patch_majority_preserves_ids_and_residual_atoms():
    species, positions, patches, macros = _fixture()
    result = select_recurrent_macro_core(
        macros, species, positions, patches,
        training_patch_ids=(0, 1, 2, 3, 4))
    assert result.strict_majority_threshold == 3
    assert result.input_macro_ids == (17, 91)
    assert result.selected_macro_ids == (17,)
    assert result.rejected_macro_ids == (91,)
    assert result.original_macro_ids_preserved
    assert result.complete_atom_representation
    assert len(result.representation_certificate_digest) == 64
    assert result.selected_covered_atom_indices == (0, 1, 2, 3, 4, 5)
    assert tuple(item.atom_index for item in result.residual_atom_terminals) == (
        6, 7, 8, 9)
    assert not result.target_or_heldout_used


def test_patch_relabeling_and_within_patch_duplicates_do_not_change_gate():
    species, positions, patches, macros = _fixture(("e", "a", "d", "b", "c"))
    duplicate = _Macro(17, macros[1].promotion_occurrences + (
        _occurrence(99, (0, 1)),))
    result = select_recurrent_macro_core(
        (macros[0], duplicate), species, positions, patches,
        training_patch_ids=("a", "b", "c", "d", "e"))
    assert result.selected_macro_ids == (17,)
    assert next(item for item in result.evidence
                if item.macro_id == 17).patch_ids == ("a", "d", "e")


def test_cross_patch_occurrence_is_rejected_and_heldout_namespace_forbidden():
    species, positions, patches, _ = _fixture()
    crossing = _Macro(4, (_occurrence(0, (1, 2)),))
    result = select_recurrent_macro_core(
        (crossing,), species, positions, patches)
    assert not result.evidence[0].every_occurrence_patch_local
    assert not result.selected_macro_ids
    try:
        select_recurrent_macro_core(
            (), species, positions, patches[:-1] + ("heldout",),
            training_patch_ids=(0, 1, 2, 3, 4))
    except ValueError as error:
        assert "non-training" in str(error)
    else:
        raise AssertionError("heldout namespace entered train-only selector")


if __name__ == "__main__":
    test_strict_patch_majority_preserves_ids_and_residual_atoms()
    test_patch_relabeling_and_within_patch_duplicates_do_not_change_gate()
    test_cross_patch_occurrence_is_rejected_and_heldout_namespace_forbidden()
    print("recurrent-core selector: all assertions passed")
