#!/usr/bin/env python3
"""Receipt-boundary controls for commuting hybrid execution."""

from types import SimpleNamespace
from unittest.mock import patch

from materials_gcts_iqc_commuting_hybrid_execution import \
    freeze_commuting_hybrid_execution


def test_commuting_first_receipt_is_the_downstream_receipt() -> None:
    first = SimpleNamespace(
        execution_digest="first-receipt", second_branches=("branch",),
        target_used=False)
    downstream = SimpleNamespace(
        second_branch_receipt_digest="first-receipt",
        second_branches=("branch",),
        deterministic_receipt_digest="downstream-receipt",
        target_used=False)
    model = SimpleNamespace(model_digest="marking", target_used=False)
    with patch(
            "materials_gcts_iqc_commuting_hybrid_execution."
            "freeze_commuting_second_frontier", return_value=first), patch(
            "materials_gcts_iqc_commuting_hybrid_execution."
            "_finish_from_commuting_second",
            return_value=downstream):
        row = freeze_commuting_hybrid_execution(
            center=(0., 0., 0.), seed_positions=((0., 0., 0.),),
            seed_species=("X",), first_radius=1., second_radius=2.,
            third_radius=3., fourth_radius=4., marking_model=model,
            workers=1)
    assert row.first_frontier is first
    assert row.downstream is downstream
    assert row.candidate_geometry_unchanged
    assert not row.target_used


if __name__ == "__main__":
    test_commuting_first_receipt_is_the_downstream_receipt()
    print("IQC commuting hybrid execution tests passed")
