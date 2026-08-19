#!/usr/bin/env python3

import copy
import json

from materials_gcts_iqc_self_fed_frontier_candidates import (
    DEFAULT_FIXTURE, validate_candidate_receipt)


def test_frozen_receipt_validates_and_rejects_mutation():
    row = validate_candidate_receipt(json.loads(DEFAULT_FIXTURE.read_text()))
    assert row["target_open_count"] == 0
    assert not row["target_used"]
    assert row["inherited_state_atoms"] > row["original_seed_atoms"]
    assert row["terminal_count"] > 0
    broken = copy.deepcopy(row)
    broken["fusion_order"][0], broken["fusion_order"][1] = \
        broken["fusion_order"][1], broken["fusion_order"][0]
    try:
        validate_candidate_receipt(broken)
    except AssertionError:
        pass
    else:
        raise AssertionError("mutated self-fed receipt was accepted")


if __name__ == "__main__":
    test_frozen_receipt_validates_and_rejects_mutation()
    print("self-fed frontier candidate tests passed")
