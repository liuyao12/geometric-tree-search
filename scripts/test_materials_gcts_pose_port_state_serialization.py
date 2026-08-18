#!/usr/bin/env python3

from materials_gcts_incidence_token_marking import (
    FrozenIncidenceTokenMarking, TokenEvidence)
from materials_gcts_port_incidence_search import PortRole
from materials_gcts_pose_port_state_marking import (
    FrozenPosePortStateMarking, PosePortStateEvidence,
    pose_port_state_marking_digest)
from materials_gcts_pose_port_state_serialization import (
    pose_port_state_marking_from_payload, pose_port_state_marking_payload)


def test_pose_port_state_payload_is_lossless_and_typed():
    role = PortRole("A", (1, 2), "B", (3, 4), 5)
    token = ("role-pair", role, ("nested", 7))
    marking = FrozenPosePortStateMarking(
        FrozenIncidenceTokenMarking(
            -.25, {token: .75}, {token: TokenEvidence(3, 4, 2)},
            4, 2, .5),
        (("role", "role-pair"),), .25, {(1, -2): .8},
        {(1, -2): PosePortStateEvidence(7, 9, 3)}, .4, 8, 2, 1.)
    payload = pose_port_state_marking_payload(marking)
    restored = pose_port_state_marking_from_payload(payload)
    assert restored == marking
    assert pose_port_state_marking_digest(restored) == \
        pose_port_state_marking_digest(marking)
    assert payload["token_marking"]["weights"][0][0]["tuple"][1] == {
        "port_role": ["A", [1, 2], "B", [3, 4], 5]}


if __name__ == "__main__":
    test_pose_port_state_payload_is_lossless_and_typed()
    print("pose-port state serialization passed")
