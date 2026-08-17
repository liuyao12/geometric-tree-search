#!/usr/bin/env python3

import json
from pathlib import Path

from materials_gcts_frontier_state_grammar import FrontierWaveSnapshot
from materials_gcts_frontier_state_promotion_benchmark import audit_snapshots


def _cached_trace_if_available():
    # Developer convenience only.  The authoritative benchmark calls
    # evaluate() and regenerates the trace; the focused regression may reuse a
    # temporary trace produced by that exact benchmark during local iteration.
    path = Path("/tmp/gcts_iqc_regenerative_traces.json")
    if not path.exists():
        return None
    rows = json.loads(path.read_text())
    return tuple(FrontierWaveSnapshot(
        row["wave"], tuple(map(tuple, row["positions"])),
        tuple(map(tuple, row["species"]))) for row in rows)


def test_exact_iqc_frontier_states_improve_structure_but_stay_honestly_red():
    snapshots = _cached_trace_if_available()
    if snapshots is None:
        from materials_gcts_frontier_attachment_benchmark import evaluate
        source = evaluate(regenerative_wave_count=16)
        snapshots = tuple(FrontierWaveSnapshot(
            row.wave, row.positions, row.species)
            for row in source.regenerative_growth_traces)
    sizes = (12, 104, 12, 4, 36, 24, 24, 12,
             8, 24, 24, 24, 24, 12, 12, 12)
    result = audit_snapshots(snapshots, sizes, True)
    assert result.emitted_sites == 368
    assert result.candidate_connected_subgraphs == 2563
    assert result.normalized_state_types == 119
    assert result.recurring_state_types == 5
    assert result.recurring_type_size_histogram == ((2, 2), (3, 2), (4, 1))
    assert result.recurring_occurrences == 366
    assert result.proper_pose_verified_occurrences == 92
    assert result.repeated_covered_sites == 336
    assert result.explicit_residual_sites == 32
    assert result.complete_cover
    assert result.three_wave_state_audits
    assert result.equal_expanding_scale_candidates == 1
    assert result.proper_equal_expanding_scale_candidates == 0
    assert result.equal_expanding_support_candidates == 0
    assert result.strict_stationary_witnesses == 0
    assert not result.state_transition_executor_available
    assert not result.autonomous_growth_claimed
    assert result.old_four_wave_supermacros == (132, 96, 80, 60)
    assert not result.frontier_state_exponential_gate
    assert not result.state_compiler_uses_family_cell_or_target


if __name__ == "__main__":
    test_exact_iqc_frontier_states_improve_structure_but_stay_honestly_red()
    print("frontier-state IQC promotion benchmark: honest red gate passed")
