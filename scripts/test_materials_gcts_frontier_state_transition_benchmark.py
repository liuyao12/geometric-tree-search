#!/usr/bin/env python3

import json
from pathlib import Path

from materials_gcts_frontier_state_grammar import FrontierWaveSnapshot
from materials_gcts_frontier_state_transition_benchmark import audit_snapshots


def _snapshots():
    path = Path("/tmp/gcts_iqc_regenerative_traces.json")
    if path.exists():
        rows = json.loads(path.read_text())
        return tuple(FrontierWaveSnapshot(
            row["wave"], tuple(map(tuple, row["positions"])),
            tuple(map(tuple, row["species"]))) for row in rows)
    from materials_gcts_frontier_attachment_benchmark import evaluate
    source = evaluate(regenerative_wave_count=16)
    return tuple(FrontierWaveSnapshot(
        row.wave, row.positions, row.species)
        for row in source.regenerative_growth_traces)


def test_real_iqc_state_transitions_are_executable_but_not_stationary():
    result = audit_snapshots(_snapshots())
    assert result.source_waves == 16
    assert result.source_sites == 368
    assert result.source_sites_exact
    assert result.recurring_state_types == 5
    assert result.finite_proper_state_types == 3
    assert result.packed_proper_occurrences == 30
    assert result.transition_observations == 14
    assert result.exact_transition_rules == 8
    assert result.maximum_children_per_rule == 1
    assert result.rules_seen_on_multiple_transitions == 0
    assert result.positive_mdl_rules == 0
    assert not result.stationary_rule_ids
    assert not result.executable_stationary_rule
    assert not result.generic_million_site_iqc_claim
    assert not result.target_used
    assert not result.compiler_uses_material_family_cell_or_target


if __name__ == "__main__":
    test_real_iqc_state_transitions_are_executable_but_not_stationary()
    print("frontier-state transition benchmark: honest red gate passed")
