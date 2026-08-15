#!/usr/bin/env python3

from materials_gcts_cdyb_transfer_benchmark import (
    build_cdyb_split, evaluate, fit_current_generic)
from materials_gcts_nested_transfer_benchmark import validate_nested_crops


def test_small_published_cdyb_transfer_gate_is_honestly_red() -> None:
    radii = (8.0, 14.0, 19.5)
    split = build_cdyb_split(max_index=3, box_size=40.0, radii=radii)
    validate_nested_crops(split)
    fitted = fit_current_generic(split.training)
    report = evaluate(max_index=3, box_size=40.0, radii=radii)
    assert report.training_atoms < report.validation_atoms < report.test_atoms
    assert fitted.audit.learned_from_seed_only
    assert not fitted.audit.family_label_used
    assert not fitted.program.recursive_candidates
    assert report.training_cover_fraction == 1.0
    assert report.provenance_gate_passed
    assert report.cover_gate_passed
    assert not report.transfer_gate_passed
    assert not report.hierarchy_gate_passed
    assert not report.marking_ablation_gate_passed
    assert not report.benchmark_passed


if __name__ == "__main__":
    test_small_published_cdyb_transfer_gate_is_honestly_red()
    print("published Cd-Yb nested transfer baseline: honest red gate passed")
