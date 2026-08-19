#!/usr/bin/env python3

from materials_gcts_iqc_self_fed_frontier_preregistration import (
    ACTION_REACH_SCHEDULE, FIRST_BLOCK_RADIUS, ORIGINAL_SEED_RADIUS,
    SECOND_BLOCK_RADIUS, EXPECTED_MANIFEST_DIGEST, audit)


def test_manifest_is_target_free_and_freezes_second_block():
    row = audit()
    assert ACTION_REACH_SCHEDULE == (8, 8, 8)
    assert SECOND_BLOCK_RADIUS == FIRST_BLOCK_RADIUS + ORIGINAL_SEED_RADIUS
    assert row.boundary_rule_reproduced
    assert not row.oracle_or_cropper_imported
    assert not row.second_block_candidates_computed
    assert not row.outer_target_materialized
    assert "six self-fed actions" in row.autonomous_gate
    assert row.manifest_digest == EXPECTED_MANIFEST_DIGEST


if __name__ == "__main__":
    test_manifest_is_target_free_and_freezes_second_block()
    print("self-fed frontier preregistration tests passed")
