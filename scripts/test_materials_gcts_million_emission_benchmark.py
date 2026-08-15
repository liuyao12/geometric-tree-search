#!/usr/bin/env python3

from materials_gcts_million_emission_benchmark import evaluate


def test_learned_programs_explicitly_emit_and_certify_millions() -> None:
    result = evaluate()
    assert result.crystal.sites_emitted == 7_077_888
    assert result.crystal.macro_actions == 5
    assert abs(result.crystal.minimum_growth_per_action - 8.0) < 1e-12
    assert result.quasicrystal.sites_emitted == 2_791_097
    assert result.quasicrystal.macro_actions == 6
    assert result.quasicrystal.minimum_growth_per_action > 4.1
    assert result.quasicrystal.coordinate_digest == (
        result.quasicrystal.independent_oracle_digest)
    assert not result.heldout_sites_used_for_learning
    assert not result.physical_potential_used
    assert result.quasicrystal_gcts_marking_compiled
    assert not result.coordinate_lift_used_during_emission
    assert result.benchmark_passed


if __name__ == "__main__":
    test_learned_programs_explicitly_emit_and_certify_millions()
    print("explicit million-site crystal/IQC certificate passed")
