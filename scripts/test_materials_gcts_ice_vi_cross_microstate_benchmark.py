#!/usr/bin/env python3
"""Regression for sealed Ice-VI cross-microstate continuation."""

from materials_gcts_ice_vi_cross_microstate_benchmark import evaluate


def main() -> None:
    report = evaluate()
    assert report.training_molecules == 123
    assert report.conformer_types == 5
    assert report.frozen_ports == 84
    assert report.directed_type_pairs == 20
    assert report.calibration_candidates == 683
    assert (report.calibration_selected, report.calibration_correct,
            report.calibration_wrong) == (24, 23, 1)
    assert report.calibration_precision >= .95
    assert report.selected_parent_witness_threshold == 2
    assert report.train_eval_center_separation > report.required_separation
    assert report.raw_molecule_id_overlap == 0
    assert report.seed_molecules == report.seed_recognized_molecules == 23
    assert report.seed_conformer_types == (0, 1, 2, 3, 4)
    assert report.anchor_wave_accepted == (4, 3, 1, 0)
    assert (report.anchor_emitted, report.anchor_correct,
            report.anchor_wrong) == (8, 8, 0)
    assert report.unresolved_anchor_orientations == 8
    assert report.resolved_anchor_orientations == 0
    assert report.oxygen_anchor_gate_passed
    assert not report.occupational_orientation_gate_passed
    assert report.whole_molecule_wave_accepted == (4, 2, 1)
    assert (report.whole_molecule_emitted_sites,
            report.whole_molecule_correct_sites,
            report.whole_molecule_wrong_sites) == (21, 18, 3)
    assert report.heldout_target_open_count == 1
    assert len(report.trace_digest) == 64
    assert not report.grammar_material_label_used
    assert not report.grammar_expected_formula_used
    assert not report.lattice_site_indices_used
    assert not report.energy_or_potential_used
    assert not report.target_used_before_scoring
    assert not report.stationary_or_exponential_claim
    print("Ice VI sealed cross-microstate benchmark: passed")


if __name__ == "__main__":
    main()
