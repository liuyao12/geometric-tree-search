#!/usr/bin/env python3

from materials_gcts_iterated_metric_port_benchmark import evaluate


def test_metric_ports_execute_exactly_then_honestly_stall() -> None:
    result = evaluate()
    assert result.initial_atoms == 1969
    assert result.final_atoms == 2349
    assert result.waves[0].accepted_sites == 380
    assert result.waves[0].true_accepted_sites == 380
    assert result.waves[0].precision == 1.0
    assert result.waves[1].one_vote_candidates == 3960
    assert result.waves[1].accepted_sites == 0
    assert result.stalled
    assert not result.oracle_colors_used_for_insertion
    assert not result.heldout_geometry_used_for_fitting
    assert not result.regenerative_growth
    assert not result.benchmark_passed


if __name__ == "__main__":
    test_metric_ports_execute_exactly_then_honestly_stall()
    print("iterated metric ports: honest regenerative gate passed")
