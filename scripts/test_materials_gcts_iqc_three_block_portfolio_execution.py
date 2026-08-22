#!/usr/bin/env python3
"""Fast contract for the target-free clusters-squared portfolio."""

from pathlib import Path


def test_portfolio_execution_is_bounded_and_target_free() -> None:
    source = Path(__file__).with_name(
        "materials_gcts_iqc_three_block_portfolio_execution.py").read_text()
    signature = source.split(
        "def freeze_three_block_portfolio_execution(", 1)[1].split(
            ") -> FrozenThreeBlockPortfolioExecution", 1)[0]
    assert "target" not in signature
    assert "scorer" not in signature
    assert "oracle_patch" not in source
    assert "_crop(" not in source
    assert "FIRST_PARENT_WIDTH = 8" in source
    assert "SECOND_OPTION_TOP_K = 8" in source
    assert "SECOND_PARENT_WIDTH = 4" in source
    assert "select_future_options(" in source
    assert "def _complete_first_block(" in source
    assert "-selection.fused_scores[index], index" in source
    assert "_channel_tree(" in source
    assert "ProcessPoolExecutor" in source


if __name__ == "__main__":
    test_portfolio_execution_is_bounded_and_target_free()
    print("target-free clusters-squared three-block portfolio: passed")
