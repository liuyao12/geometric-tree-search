#!/usr/bin/env python3

from materials_gcts_recurrent_branch_value import (
    RecurrentBranchExample, fit_grouped_recurrent_branch_value)
from materials_gcts_recurrent_state_diverse_beam import (
    RecurrentStateBeamCandidate, RecurrentStateBeamSpec,
    recurrent_branch_state_code, select_recurrent_state_diverse_beam)


def _head():
    examples = tuple(
        RecurrentBranchExample(group, (signal,), (color,), signal < 0)
        for group in range(3) for signal, color in
        ((-2., "A"), (-1., "A"), (1., "B"), (2., "B")))
    model, _audit = fit_grouped_recurrent_branch_value(
        examples, feature_names=("signal",), color_keys=("A", "B"),
        candidate_neighbors=(1,), beta_prior=.5)
    return model


def test_recurrent_state_beam_is_bounded_and_permutation_invariant():
    head = _head()
    rows = tuple(RecurrentStateBeamCandidate(
        (value,), (color,), f"candidate-{index}", index)
        for index, (value, color) in enumerate(
            ((-2., "A"), (-1.9, "A"), (1., "B"), (2., "B"))))
    spec = RecurrentStateBeamSpec(.5, 1, 3)
    selected = select_recurrent_state_diverse_beam(head, rows, spec)
    reversed_selected = select_recurrent_state_diverse_beam(
        head, tuple(reversed(rows)), spec)
    assert tuple(row.tie_key for row in selected) == \
        tuple(row.tie_key for row in reversed_selected)
    assert len(selected) <= spec.beam_width
    assert len({recurrent_branch_state_code(
        head, row.features, row.action_colors,
        state_bin_width=spec.state_bin_width) for row in selected}) == \
        len(selected)


if __name__ == "__main__":
    test_recurrent_state_beam_is_bounded_and_permutation_invariant()
    print("recurrent state diverse beam passed")
