#!/usr/bin/env python3

from materials_gcts_icosahedral_modelset import (
    HIDDEN_UNIT, HIDDEN_WINDOW, hidden_species, lift_point, oracle_patch,
    project, star_vectors, vector_norm)
from materials_gcts_latent_macro_growth import _latent_patch
from materials_gcts_recursive_scaling_benchmark import evaluate


def test_recursive_scaling_crosses_one_million() -> None:
    result = evaluate()
    assert result.crystal.rule_family == "translation_quotient"
    assert result.crystal.atom_counts[:4] == (216, 1728, 13824, 110592)
    assert result.crystal.first_million_action == 5
    assert result.crystal.first_million_atoms == 7_077_888
    assert all(factor == 8.0 for factor in result.crystal.growth_factors)

    assert result.quasicrystal.rule_family == "internal_section_inflation"
    assert result.quasicrystal.atom_counts[:3] == (507, 1969, 8603)
    assert result.quasicrystal.first_million_action == 6
    assert result.quasicrystal.first_million_atoms >= 1_000_000
    assert all(factor > 3.8 for factor in
               result.quasicrystal.growth_factors[1:])

    assert (result.substitution_quasicrystal.rule_family ==
            "substitution_product")
    assert result.substitution_quasicrystal.atom_counts == (
        729, 3375, 13824, 59319, 250047, 1061208)
    assert result.substitution_quasicrystal.first_million_action == 5


def test_second_iqc_inflation_has_an_independent_oracle_certificate() -> None:
    training, _ = oracle_patch(3, 9.0)
    grown = _latent_patch(training, 9.0 * HIDDEN_UNIT ** 2)
    assert len(grown.positions) == 8603
    internal_vectors = star_vectors(-1.0 / HIDDEN_UNIT)
    lifts = set()
    for point, chemical in zip(grown.positions, grown.species):
        lift, residual = lift_point(point, HIDDEN_UNIT)
        assert residual < 1e-5
        internal_radius = vector_norm(project(lift, internal_vectors))
        assert internal_radius <= HIDDEN_WINDOW + 1e-10
        assert chemical == hidden_species(internal_radius)
        lifts.add(lift)
    assert len(lifts) == 8603
