#!/usr/bin/env python3
"""Exact parity for the atom-inverted occurrence overlap index."""

import random

from materials_gcts_irregular_port_atlas import _overlap_pairs_from_supports


def test_overlap_pair_index_matches_cartesian_reference():
    rng = random.Random(713)
    for count in (2, 7, 19):
        supports = tuple((index, tuple(sorted(rng.sample(
            range(31), rng.randint(2, 9))))) for index in range(count))
        for minimum in (1, 2, 4):
            brute = frozenset(
                (left_id, right_id)
                for left_id, left in supports
                for right_id, right in supports
                if left_id != right_id and
                len(set(left).intersection(right)) >= minimum)
            assert _overlap_pairs_from_supports(supports, minimum) == brute


if __name__ == "__main__":
    test_overlap_pair_index_matches_cartesian_reference()
    print("overlap pair index parity: assertions passed")
