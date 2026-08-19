#!/usr/bin/env python3
"""Regression for target-free post-self-fed port-discharge traces."""

import hashlib

from materials_gcts_iqc_post_self_fed_port_discharge_dataset import (
    DEFAULT_FIXTURE, EXPECTED_FIXTURE_SHA256, ROLLOUT_HORIZON,
    load_fixture_json, validate_dataset)


def test_frozen_port_discharge_dataset():
    raw, payload = load_fixture_json()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_FIXTURE_SHA256
    row = validate_dataset(payload)
    traces = [candidate["trace"] for group in row["groups"]
              for candidate in group["rows"]]
    assert len(traces) == 19
    assert all(not trace["target_used"] for trace in traces)
    assert all(trace["accepted_children"] <= ROLLOUT_HORIZON
               for trace in traces)
    assert row["rollout_target_crop_constructed"] is False
    assert row["fresh_confirmation_claimed"] is False


if __name__ == "__main__":
    test_frozen_port_discharge_dataset()
    print("post-self-fed port-discharge dataset tests passed")
