#!/usr/bin/env python3

from dataclasses import dataclass, replace

from materials_gcts_macro_stationary_adapter import AdaptedMacroProduction
from materials_gcts_oriented_overlap_ports import IDENTITY
from materials_gcts_recurring_action_submacro_audit import (
    ActionSubmacroRecord, PromotedSubmacroLevel,
    adapt_promoted_submacro_levels, audit_action_submacro_records,
    audit_promoted_submacro_levels)
from materials_gcts_stationary_production_signature import (
    PortGraphProduction, ProductionChild, ProductionPort,
    canonicalize_production)


def _production(scale: float, population: int,
                perturbation=(0.0, 0.0, 0.0)) -> PortGraphProduction:
    points = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
              (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    children = []
    for index, point in enumerate(points):
        translation = tuple(scale * point[axis] +
                            (perturbation[axis] if index == 3 else 0.0)
                            for axis in range(3))
        children.append(ProductionChild(
            ("Na*1", "Cl*1"), "achiral", IDENTITY, translation,
            (IDENTITY,), (("Na", population), ("Cl", population))))
    ports = tuple(ProductionPort(
        index, index + 1, ("learned-overlap",), ("Na", "Cl"))
                  for index in range(3))
    return PortGraphProduction(tuple(children), ports)


def _supports(level: int):
    base = 1000 * level
    return (frozenset(range(base, base + 20)),
            frozenset(range(base + 100, base + 120)))


def _record(level: int, *, scale=None, population=None, mdl=20,
            supports=None, perturbation=(0.0, 0.0, 0.0), clean=True):
    scale = float(2 ** level if scale is None else scale)
    population = 2 ** level if population is None else population
    return ActionSubmacroRecord(
        level, f"macro-{level}", _production(scale, population, perturbation),
        _supports(level) if supports is None else supports, mdl, True, clean)


def test_injectable_positive_control_requires_full_strong_contract():
    result = audit_action_submacro_records(tuple(_record(i) for i in range(3)))
    assert result.stationary
    assert result.evaluated_consecutive_triples == 1
    witness = result.witnesses[0]
    assert witness.evidence.observed_levels == (0, 1, 2)
    assert witness.evidence.learned_similarity_scale == 2.0
    assert tuple(comparison.chemical_population_audit.substitution_matrix
                 for comparison in witness.evidence.adjacent_comparisons) == (
                     ((2,),), ((2,),))
    assert witness.independent_occurrences == (2, 2, 2)


def test_one_scale_copy_amorphous_and_nonpositive_mdl_are_rejected():
    assert not audit_action_submacro_records((_record(0), _record(1))).stationary

    copied = replace(_record(0), production=PortGraphProduction(
        _record(0).production.children, ()))
    assert not audit_action_submacro_records((
        copied, replace(copied, hierarchy_level=1, record_id="copy-1"),
        replace(copied, hierarchy_level=2, record_id="copy-2"))).stationary

    amorphous = (_record(0), _record(1, perturbation=(.137, -.091, .043)),
                 _record(2))
    assert not audit_action_submacro_records(amorphous).stationary

    mdl_failure = (_record(0), _record(1, mdl=0), _record(2))
    assert not audit_action_submacro_records(mdl_failure).stationary


def test_unequal_scale_substitution_and_spatial_dependence_are_rejected():
    unequal_scale = (_record(0, scale=1), _record(1, scale=2),
                     _record(2, scale=6))
    assert not audit_action_submacro_records(unequal_scale).stationary

    unequal_substitution = (_record(0, population=1),
                            _record(1, population=2),
                            _record(2, population=6))
    assert not audit_action_submacro_records(unequal_substitution).stationary

    overlapping = (frozenset(range(20)), frozenset(range(1, 21)))
    dependent = (_record(0), _record(1, supports=overlapping), _record(2))
    result = audit_action_submacro_records(dependent)
    assert not result.stationary
    assert any("independent spatial" in item.reason for item in result.rejected)


@dataclass(frozen=True)
class _Macro:
    macro_id: int
    occurrences: tuple
    mdl_saving: int


@dataclass(frozen=True)
class _Occurrence:
    atom_indices: tuple[int, ...]


def test_real_level_adapter_is_injectable_and_shares_semantic_cache():
    seen_cache_ids = []

    def adapter(artifact, macro, *, tolerance, prototype_semantics_cache):
        del artifact, tolerance
        seen_cache_ids.append(id(prototype_semantics_cache))
        production = _production(float(2 ** macro.macro_id),
                                 2 ** macro.macro_id)
        canonical = canonicalize_production(production)
        return AdaptedMacroProduction(
            production, canonical, 3, 1,
            tuple(child.chemical_population for child in production.children),
            False, False, False, False, False)

    levels = tuple(PromotedSubmacroLevel(
        level, object(), (_Macro(level, (
            _Occurrence(tuple(range(100 * level, 100 * level + 20))),
            _Occurrence(tuple(range(100 * level + 40,
                                    100 * level + 60)))), 10),))
                   for level in range(3))
    result = audit_promoted_submacro_levels(levels, adapter=adapter)
    assert result.stationary

    # Multiple macros at one level use exactly one shared cache.
    duplicate = PromotedSubmacroLevel(0, object(),
        (levels[0].submacros[0], levels[0].submacros[0]))
    adapt_promoted_submacro_levels((duplicate,), adapter=adapter)
    assert seen_cache_ids[-1] == seen_cache_ids[-2]


def test_leakage_flag_cannot_be_hidden_by_a_valid_geometry_signature():
    records = (_record(0), _record(1, clean=False), _record(2))
    result = audit_action_submacro_records(records)
    assert not result.stationary
    assert not result.leakage_clean

    target_taught = replace(_record(1), learned_from_training_only=False)
    result = audit_action_submacro_records((_record(0), target_taught,
                                            _record(2)))
    assert not result.stationary
    assert not result.leakage_clean
