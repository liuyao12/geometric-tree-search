#!/usr/bin/env python3

from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample)
from materials_gcts_pose_port_state_marking import (
    fit_pose_port_state_marking, pose_port_state_code,
    pose_port_state_marking_digest, score_pose_port_state)


def descriptor(role, orientation, noise):
    return CandidateIncidenceDescriptor((
        ("role", role),
        ("port-neighbor-angle", orientation),
        ("occupied-shell", noise),
    ))


def test_finite_state_quotient_is_id_free_and_recurrent():
    examples = []
    for group in range(3):
        for repeat in range(4):
            examples.append(IncidenceTokenExample(
                group, descriptor("open", 1, repeat % 2), True))
            examples.append(IncidenceTokenExample(
                group, descriptor("closed", -1, repeat % 2), False))
    model = fit_pose_port_state_marking(
        tuple(examples), minimum_token_support=3,
        minimum_token_groups=2, state_bin_width=.5,
        minimum_state_support=3, minimum_state_groups=2)
    good = descriptor("open", 1, 99)
    bad = descriptor("closed", -1, 99)
    assert score_pose_port_state(model, good) > score_pose_port_state(model, bad)
    assert len(pose_port_state_code(
        model.token_marking, good,
        state_bin_width=model.state_bin_width,
        channel_families=model.channel_families)) == 5
    assert pose_port_state_marking_digest(model) == \
        pose_port_state_marking_digest(model)
    assert all(len(state) == 5 for state in model.state_probabilities)


if __name__ == "__main__":
    test_finite_state_quotient_is_id_free_and_recurrent()
    print("pose-port state marking tests passed")
