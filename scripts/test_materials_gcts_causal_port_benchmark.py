#!/usr/bin/env python3

from materials_gcts_causal_port_benchmark import evaluate


def test_causal_port_marking_has_a_real_but_incomplete_effect() -> None:
    result = evaluate(512, 10)
    assert result.incoming_context_uses_only_smaller_radius_atoms
    assert not result.heldout_geometry_used_for_fitting
    assert result.level_one_marking_effect
    assert not result.all_levels_transfer
    assert not result.benchmark_passed


if __name__ == "__main__":
    test_causal_port_marking_has_a_real_but_incomplete_effect()
    print("causal incoming-port marking: honest partial gate passed")
