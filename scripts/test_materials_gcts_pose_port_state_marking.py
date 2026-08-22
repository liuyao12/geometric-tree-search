#!/usr/bin/env python3

from materials_gcts_incidence_token_marking import (
    CandidateIncidenceDescriptor, IncidenceTokenExample)
from materials_gcts_pose_port_state_marking import (
    fit_pose_port_state_marking, pose_port_channel_responses,
    pose_port_state_code,
    pose_port_state_marking_digest, score_pose_port_state,
    select_pose_port_channel_diverse)


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
    responses = pose_port_channel_responses(
        model.token_marking, good,
        channel_families=model.channel_families)
    assert len(responses) == 5
    assert pose_port_state_code(
        model.token_marking, good,
        state_bin_width=model.state_bin_width,
        channel_families=model.channel_families) == tuple(
            round(value / model.state_bin_width) for value in responses)
    assert pose_port_state_marking_digest(model) == \
        pose_port_state_marking_digest(model)
    assert all(len(state) == 5 for state in model.state_probabilities)
    candidates = {
        "good": good,
        "bad": bad,
        "open-noisy": descriptor("open", -1, 100),
        "closed-oriented": descriptor("closed", 1, 101),
    }
    selected = select_pose_port_channel_diverse(
        model, candidates, budget=3, baseline_slots=1,
        votes={key: index for index, key in enumerate(candidates)},
        tie_keys={key: key for key in candidates})
    reversed_selected = select_pose_port_channel_diverse(
        model, dict(reversed(tuple(candidates.items()))),
        budget=3, baseline_slots=1,
        votes={key: index for index, key in enumerate(candidates)},
        tie_keys={key: key for key in candidates})
    assert len(selected) == len(set(selected)) == 3
    assert selected == reversed_selected
    assert selected[0] == "good"


if __name__ == "__main__":
    test_finite_state_quotient_is_id_free_and_recurrent()
    print("pose-port state marking tests passed")
