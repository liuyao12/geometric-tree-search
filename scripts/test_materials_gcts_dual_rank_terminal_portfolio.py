#!/usr/bin/env python3

from materials_gcts_dual_rank_terminal_portfolio import (
    select_dual_rank_terminal_portfolio)


def test_dual_rank_union_preserves_both_heads_and_stable_identity():
    ids = ("a", "b", "c", "d", "e")
    scalar = (0, 1, 2, 3, 4)
    fusion = (2, 1, 4, 3, 0)
    row = select_dual_rank_terminal_portfolio(
        ids, scalar, fusion, per_channel_budget=2)
    assert row.scalar_head == (0, 1)
    assert row.fusion_head == (2, 1)
    assert row.selected_indices == (0, 2, 1)
    assert row.selected_candidate_ids == ("a", "c", "b")
    assert len(row.candidate_digest) == len(row.selection_digest) == 64
    assert not row.target_used
    assert row == select_dual_rank_terminal_portfolio(
        ids, scalar, fusion, per_channel_budget=2)


def test_candidate_permutation_is_identity_equivariant():
    ids = ("a", "b", "c", "d")
    first = select_dual_rank_terminal_portfolio(
        ids, (1, 3, 0, 2), (3, 2, 1, 0), per_channel_budget=2)
    permutation = (2, 0, 3, 1)
    permuted_ids = tuple(ids[index] for index in permutation)
    inverse = {old: new for new, old in enumerate(permutation)}
    second = select_dual_rank_terminal_portfolio(
        permuted_ids,
        tuple(inverse[index] for index in (1, 3, 0, 2)),
        tuple(inverse[index] for index in (3, 2, 1, 0)),
        per_channel_budget=2)
    assert first.selected_candidate_ids == second.selected_candidate_ids


def test_invalid_orders_and_ids_fail_closed():
    for args in (
        (("a", "a"), (0, 1), (1, 0), 1),
        (("a", "b"), (0, 0), (1, 0), 1),
        (("a", "b"), (0, 1), (1, 0), 0),
    ):
        try:
            select_dual_rank_terminal_portfolio(
                args[0], args[1], args[2], per_channel_budget=args[3])
        except ValueError:
            pass
        else:
            raise AssertionError("invalid portfolio input did not fail closed")


if __name__ == "__main__":
    test_dual_rank_union_preserves_both_heads_and_stable_identity()
    test_candidate_permutation_is_identity_equivariant()
    test_invalid_orders_and_ids_fail_closed()
    print("dual-rank terminal portfolio tests passed")
