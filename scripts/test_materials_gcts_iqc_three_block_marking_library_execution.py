#!/usr/bin/env python3
"""Fast contract for the five-channel complete-parent successor."""

from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_three_block_marking_library_execution import (
    LOCAL_SECTION_CHANNEL, select_marking_library_children)


def _branch(parent):
    actions = tuple((((float(child + 3), 0., 0.), "X"),
                     ((0., float(child + 3), 0.), "Y"),
                     ((0., 0., float(child + 3)), "Z"))
                    for child in range(12))
    scores = tuple(tuple(float((parent + child + channel) % 7)
                         for channel in range(4))
                   for child in range(12))
    return SimpleNamespace(
        first_rank=parent,
        first_actions=(((0., 0., 0.), "X"),
                       ((2., 0., 0.), "Y"),
                       ((0., 2., 0.), "Z")),
        second_actions=actions,
        second_channel_scores=scores)


def test_library_unions_local_children_without_authorizing_geometry() -> None:
    branches = tuple(_branch(parent) for parent in range(1, 9))
    result = select_marking_library_children(
        branches=branches,
        seed_positions=((-1., 0., 0.), (0., -1., 0.), (0., 0., -1.)),
        seed_species=("X", "Y", "Z"))
    assert {parent for parent, _children in result["union_rows"]} == \
        set(range(1, 9))
    assert all(len(children) == 2 for _parent, children
               in result["local_rows"])
    for (parent, legacy), (_, local), (_, union) in zip(
            result["legacy_rows"], result["local_rows"],
            result["union_rows"]):
        assert set(legacy) | set(local) == set(union)
        assert all(0 <= child < len(branches[parent - 1].second_actions)
                   for child in union)
    assert sum(name == LOCAL_SECTION_CHANNEL
               for name, _parent in result["selected_by_channels"]) == 8
    assert len(result["digest"]) == 64


def test_executor_has_no_scoring_or_geometry_authorization_api() -> None:
    source = Path(__file__).with_name(
        "materials_gcts_iqc_three_block_marking_library_execution.py"
    ).read_text()
    signature = source.split(
        "def freeze_three_block_marking_library_execution(", 1)[1].split(
            ") -> FrozenThreeBlockMarkingLibraryExecution", 1)[0]
    assert "target" not in signature
    assert "scorer" not in signature
    assert "from materials_gcts_icosahedral_modelset" not in source
    assert "select_child_ids(" in source
    assert "_third_parent_worker" in source
    assert "set(legacy).issubset(union)" in source


if __name__ == "__main__":
    test_library_unions_local_children_without_authorizing_geometry()
    test_executor_has_no_scoring_or_geometry_authorization_api()
    print("five-channel IQC marking-library executor: passed")
