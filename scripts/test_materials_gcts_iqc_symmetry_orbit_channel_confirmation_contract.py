#!/usr/bin/env python3
"""Fast contract checks that do not construct the reserved IQC target."""

from materials_gcts_iqc_symmetry_orbit_channel_confirmation import (
    ACTIONS_PER_NUCLEUS, DISTANCE_BIN_WIDTH, FROZEN_DEVELOPMENT_COMMIT,
    MAXIMUM_NEIGHBORS, NEIGHBORHOOD_REACH, PROTOCOL_DIGEST,
    PROTOCOL_PAYLOAD, SELECTION_RULE)


def test_confirmation_protocol_is_frozen_without_opening_target():
    assert FROZEN_DEVELOPMENT_COMMIT == "644d69f"
    assert NEIGHBORHOOD_REACH == 3.
    assert DISTANCE_BIN_WIDTH == .25
    assert MAXIMUM_NEIGHBORS == 8
    assert ACTIONS_PER_NUCLEUS == 2
    assert SELECTION_RULE == \
        "larger exact score-equality orbit; detailed wins ties"
    assert PROTOCOL_PAYLOAD[0] == FROZEN_DEVELOPMENT_COMMIT
    assert PROTOCOL_DIGEST == \
        "3675cd8b4883c611bea899ad6d9c2629882e62b00881f84501898abc99f4030a"


def main():
    test_confirmation_protocol_is_frozen_without_opening_target()
    print("IQC symmetry-orbit confirmation contract test passed")


if __name__ == "__main__":
    main()
