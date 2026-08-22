#!/usr/bin/env python3
"""Contract/result regression for the bounded joint IQC confirmation."""

from materials_gcts_iqc_lazy_joint_confirmation import (
    DEFAULT_FIXTURE, load_default_result)
from materials_gcts_iqc_lazy_joint_confirmation_preregistration import (
    EXPECTED_MANIFEST_DIGEST, validate_preregistration)


def test_confirmation_contract_or_result():
    assert validate_preregistration() == EXPECTED_MANIFEST_DIGEST
    if not DEFAULT_FIXTURE.exists():
        return
    row = load_default_result()
    assert row["receipt_serialized_before_target"]
    assert row["receipt_unchanged_after_target"]
    assert row["expanded_prefixes"] <= row["maximum_expanded_prefixes"]
    assert row["expanded_prefixes"] < row[
        "eager_marking_library_prefixes"]
    assert row["saved_geometry_expansions"] > 0
    assert not row["target_used_for_candidate_or_ranking"]
    assert not row["winner_selected_or_validated"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]
    assert not row["rerun_or_fallback_allowed"]


if __name__ == "__main__":
    test_confirmation_contract_or_result()
    print("lazy joint IQC confirmation contract/result: passed")
