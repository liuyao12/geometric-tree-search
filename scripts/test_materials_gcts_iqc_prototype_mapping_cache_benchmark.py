"""Regression for the target-free frozen prototype-mapping cache audit."""

from materials_gcts_iqc_prototype_mapping_cache_benchmark import \
    load_default_result


def test_cached_and_uncached_parent_actions_are_identical_and_faster():
    row = load_default_result()
    assert row["exact_action_parity"] is True
    assert row["target_used"] is False
    assert row["state_counts"] == [8, 38, 143]
    assert row["uncached_seconds"] / row["cached_seconds"] > 2.


if __name__ == "__main__":
    test_cached_and_uncached_parent_actions_are_identical_and_faster()
    print("IQC prototype mapping cache benchmark: passed")
