#!/usr/bin/env python3

import hashlib

from materials_gcts_rank_calibrated_value import (
    RankValueObservation, fit_rank_value)


def test_beta_smoothed_rank_value_is_finite_and_target_free():
    observations = tuple(RankValueObservation(
        hashlib.sha256(str(index).encode()).hexdigest(), correct, false)
        for index, (correct, false) in enumerate((
            ((0, 0, 3, 3), (3, 3, 0, 0)),
            ((0, 0, 0, 1), (1, 1, 1, 0)))))
    model = fit_rank_value(observations)
    assert model.positive_counts == (0, 0, 1, 2)
    assert model.total_counts == (2, 2, 2, 2)
    assert model.posterior_values == (.25, .25, .5, .75)
    assert model.as_mapping()[4] == .75
    assert not model.target_used_during_application

    partial = fit_rank_value(observations, maximum_rank=6)
    assert partial.total_counts == (2, 2, 2, 2, 0, 0)
    assert partial.posterior_values[4:] == (.5, .5)


if __name__ == "__main__":
    test_beta_smoothed_rank_value_is_finite_and_target_free()
    print("rank-calibrated value tests: passed")
