#!/usr/bin/env python3

from materials_gcts_icosahedral_modelset import oracle_patch, oracle_patch_fast


def test_fast_oracle_is_exactly_the_reference_oracle() -> None:
    for bound, radius in ((3, 9.0), (4, 15.0)):
        reference, reference_lifts = oracle_patch(bound, radius)
        fast, fast_lifts = oracle_patch_fast(bound, radius)
        assert fast_lifts == reference_lifts
        assert len(fast.positions) == len(reference.positions)
        assert set(zip(fast.positions, fast.species)) == set(
            zip(reference.positions, reference.species))


if __name__ == "__main__":
    test_fast_oracle_is_exactly_the_reference_oracle()
    print("fast IQC oracle: exact reference equivalence passed")
