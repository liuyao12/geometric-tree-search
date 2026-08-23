#!/usr/bin/env python3
"""Fast target-order and parent-balance controls for the fourth-block beam."""

from types import SimpleNamespace

from materials_gcts_iqc_fourth_block_beam import parent_balanced_beam


def test_parent_balanced_beam_is_stable_and_complete():
    scores = (1., 3., 2., 8., 7., 9.)
    parents = (1, 1, 1, 2, 2, 2)
    ties = tuple((index,) for index in range(6))
    selected = parent_balanced_beam(scores, parents, ties, width=2)
    assert selected == (1, 2, 5, 3)
    assert tuple(parents[index] for index in selected) == (1, 1, 2, 2)
    assert parent_balanced_beam(scores, parents, ties, width=2) == selected
    try:
        parent_balanced_beam((1.,), (1, 2), ((0,),), width=2)
    except ValueError:
        pass
    else:
        raise AssertionError("misaligned beam inputs accepted")


if __name__ == "__main__":
    test_parent_balanced_beam_is_stable_and_complete()
    print("parent-balanced fourth-block beam test passed")
