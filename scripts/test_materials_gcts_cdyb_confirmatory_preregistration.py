#!/usr/bin/env python3
"""Checks for the target-free Cd--Yb confirmatory preregistration."""

from materials_gcts_cdyb_confirmatory_preregistration import (
    PROTOCOL, audit_protocol, protocol_digest)


def test_confirmatory_protocol_is_frozen_before_target_access():
    audit = audit_protocol()
    assert PROTOCOL.confirmatory_center == (35.0, 35.0, -35.0)
    assert PROTOCOL.confirmatory_seed_radius == 14.0
    assert PROTOCOL.confirmatory_target_radius == 25.0
    assert PROTOCOL.shuffle_trials == 31
    assert audit["minimum_train_center_separation"] > 55.0
    assert audit["prior_evaluation_center_separation"] > 55.0
    assert audit["train_target_domains_disjoint"]
    assert audit["prior_target_domains_disjoint"]
    assert audit["confirmatory_crop_unclipped"]
    assert not audit["target_or_oracle_imported"]
    assert len(protocol_digest()) == 64


if __name__ == "__main__":
    test_confirmatory_protocol_is_frozen_before_target_access()
    print("CdYb confirmatory preregistration: passed")
