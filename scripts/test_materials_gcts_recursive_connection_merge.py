#!/usr/bin/env python3
"""Controls for independent-configuration recursive connection merging."""

from materials_gcts_recursive_connections import (
    LocalClusterType, learn_recurrent_cluster_prototypes,
    learn_recursive_connection_marking,
    merge_recursive_connection_markings)


def marking(target):
    positions = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
    types = (LocalClusterType("A", (2,)),) * 3
    return learn_recursive_connection_marking(
        positions, types, target, 2., minimum_positive_support=1,
        minimum_purity=.0 + 1e-9)


def main():
    shared = ((2., 0., 0.),)
    first = marking(shared + ((0., 2., 0.),))
    second = marking(shared)
    third = marking(((0., 2., 0.),))
    merged = merge_recursive_connection_markings(
        (first, second, third), minimum_positive_support=2,
        minimum_positive_groups=2, minimum_purity=.1)
    assert merged.accepted_states
    assert all(merged.evidence[state].positive >= 2
               for state in merged.accepted_states)
    recurrent = learn_recurrent_cluster_prototypes((
        (LocalClusterType("A", (1,)), LocalClusterType("B", (4,))),
        (LocalClusterType("A", (1,)), LocalClusterType("B", (5,))),
        (LocalClusterType("A", (1,)), LocalClusterType("B", (6,))),
    ), minimum_groups=2)
    assert LocalClusterType("A", (1,)) in recurrent
    assert sum(row.color_key == "B" for row in recurrent) == 1
    try:
        merge_recursive_connection_markings(
            (first,), minimum_positive_groups=0)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid independent-group floor must fail")
    incompatible = type(first)(
        3., first.separation_bin_width, first.prototypes, first.evidence,
        first.accepted_states, first.minimum_positive_support,
        first.minimum_purity, first.target_color_evidence)
    try:
        merge_recursive_connection_markings((first, incompatible))
    except ValueError:
        pass
    else:
        raise AssertionError("incompatible scale must fail")
    print("recursive connection merge tests passed")


if __name__ == "__main__":
    main()
