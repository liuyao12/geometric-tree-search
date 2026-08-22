#!/usr/bin/env python3
"""Fast contract for the complete-parent three-block successor."""

from pathlib import Path

from materials_gcts_clusters2_future_option import (
    ChildOption, ParentOption, select_future_options)
from materials_gcts_iqc_three_block_complete_parent_execution import (
    COMPLETE_OPTION_SPEC, COMPLETE_PARENT_WIDTH)


def test_every_admitted_parent_survives_to_the_third_block() -> None:
    parents = tuple(ParentOption(parent, tuple(ChildOption(
        (parent, child), tuple(float((parent + child + channel) % 7)
                               for channel in range(4)))
        for child in range(12))) for parent in range(1, 9))
    selection = select_future_options(parents, COMPLETE_OPTION_SPEC)
    assert COMPLETE_PARENT_WIDTH == 8
    assert set(selection.selected_parent_ids) == set(range(1, 9))
    assert len(selection.selected_child_ids_by_parent) == 8
    assert all(children for _parent, children
               in selection.selected_child_ids_by_parent)


def test_successor_is_target_free_and_reuses_frozen_geometry() -> None:
    source = Path(__file__).with_name(
        "materials_gcts_iqc_three_block_complete_parent_execution.py"
    ).read_text()
    signature = source.split(
        "def freeze_three_block_complete_parent_execution(", 1)[1].split(
            ") -> FrozenThreeBlockPortfolioExecution", 1)[0]
    assert "target" not in signature
    assert "scorer" not in signature
    assert "from materials_gcts_icosahedral_modelset" not in source
    assert "_complete_first_block(" in source
    assert "_second_worker" in source
    assert "_third_parent_worker" in source
    assert "complete parent antichain was truncated" in source


if __name__ == "__main__":
    test_every_admitted_parent_survives_to_the_third_block()
    test_successor_is_target_free_and_reuses_frozen_geometry()
    print("complete-parent three-block successor: passed")
