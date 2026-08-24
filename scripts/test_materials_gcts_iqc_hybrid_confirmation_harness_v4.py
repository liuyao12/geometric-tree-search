#!/usr/bin/env python3
"""Pre-execution checks for the V4 hybrid one-shot harness."""

from pathlib import Path

from materials_gcts_iqc_hybrid_confirmation_v4 import (
    ATTEMPT_MARKER, DEFAULT_FIXTURE, _attempt_marker_bytes)
from materials_gcts_iqc_hybrid_confirmation_preregistration_v4 import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST, validate_preregistration)


def test_consumed_attempt_receipt_binds_the_committed_protocol_and_center():
    assert validate_preregistration() == EXPECTED_MANIFEST_DIGEST
    text = _attempt_marker_bytes().decode()
    assert EXPECTED_MANIFEST_DIGEST in text
    assert "360.0" in text
    assert Path(DEFAULT_FIXTURE).exists()
    assert Path(ATTEMPT_MARKER).read_bytes() == _attempt_marker_bytes()
    assert CONFIRMATION_CENTER == (360., 0., 0.)


if __name__ == "__main__":
    test_consumed_attempt_receipt_binds_the_committed_protocol_and_center()
    print("IQC hybrid V4 confirmation harness tests passed")
