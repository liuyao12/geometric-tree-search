#!/usr/bin/env python3
"""Freeze the one-shot recurrent-cluster IQC supply confirmation.

This file contains protocol metadata only.  It deliberately imports no oracle,
cropper, candidate generator, marking fitter, or scorer.  The reserved nucleus
must not be materialized until this manifest and its implementation hashes are
committed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_iqc_expanded_development_preregistration import (
    RESERVED_CONFIRMATION_CENTER, TARGET_RADIUS)


SOURCE_COMMIT = "8c2f37047f49d61b48280175ddb9c8fd084c75d1"
TRAINING_GROUPS = 10
DEVELOPMENT_VALIDATION_GROUPS = 8
PROTOTYPE_MINIMUM_GROUPS = 2
SEPARATION_BIN_WIDTH = .5
MINIMUM_POSITIVE_SUPPORT = 2
MINIMUM_POSITIVE_GROUPS = 2
MINIMUM_PURITY = .5
ROOT_SCAN_ORDER = "lexicographic point then dominant source color"
SUCCESSOR_DEPENDENCY = "both ordered affine endpoints"
SUCCESSOR_FILTER = "causal endpoint + hard core + public target radius"
TARGET_OPEN_RULE = (
    "freeze recurrent prototypes, merged ports, every root candidate, every "
    "one-step successor candidate, and their digests before opening once")
POSTHOC_GATE = (
    "at least one exact colored root and at least one exact colored "
    "root-to-child continuation; supply ceiling only, not selected growth")
SOURCE_FILE_HASHES = (
    ("materials_gcts_recursive_connections.py",
     "b869e98422eb02d911f438dab442bba48237eb799cb80eeb563d6708413e5489"),
    ("materials_gcts_successor_state_marking.py",
     "350daf443446edf7321b15976febc0ffe2e9678e4b5c8998624010213861ddca"),
    ("materials_gcts_iqc_recurrent_prototype_connection_audit.py",
     "29db1548af9f4d8320b953a9dfc2f55cef78cfdc6a093ddf2ed99a94740a71a6"),
    ("materials_gcts_iqc_expanded_development_baseline.py",
     "9e454dbe21bd24314d97ee664222a613f1cef55c41e7bd108e4d826412474b41"),
    ("materials_gcts_persistent_frontier_beam.py",
     "5ef42a59cce1c5658b9d7b96eb32b6ecbde90e8eab5bedad6c74567baaba9020"),
)


@dataclass(frozen=True)
class RecurrentSupplyConfirmationPreregistration:
    source_commit: str
    confirmation_center: tuple[float, float, float]
    target_radius: float
    training_groups: int
    development_validation_groups: int
    prototype_minimum_groups: int
    separation_bin_width: float
    minimum_positive_support: int
    minimum_positive_groups: int
    minimum_purity: float
    root_scan_order: str
    successor_dependency: str
    successor_filter: str
    target_open_rule: str
    posthoc_gate: str
    source_file_hashes: tuple[tuple[str, str], ...]
    source_hashes_match: bool
    seed_or_target_materialized: bool
    candidate_or_score_computed: bool
    manifest_digest: str


def _actual_hash(filename: str) -> str:
    path = Path(__file__).resolve().parent / filename
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> RecurrentSupplyConfirmationPreregistration:
    hashes_match = all(_actual_hash(filename) == digest
                       for filename, digest in SOURCE_FILE_HASHES)
    payload = {
        "source_commit": SOURCE_COMMIT,
        "confirmation_center": RESERVED_CONFIRMATION_CENTER,
        "target_radius": TARGET_RADIUS,
        "training_groups": TRAINING_GROUPS,
        "development_validation_groups": DEVELOPMENT_VALIDATION_GROUPS,
        "prototype_minimum_groups": PROTOTYPE_MINIMUM_GROUPS,
        "separation_bin_width": SEPARATION_BIN_WIDTH,
        "minimum_positive_support": MINIMUM_POSITIVE_SUPPORT,
        "minimum_positive_groups": MINIMUM_POSITIVE_GROUPS,
        "minimum_purity": MINIMUM_PURITY,
        "root_scan_order": ROOT_SCAN_ORDER,
        "successor_dependency": SUCCESSOR_DEPENDENCY,
        "successor_filter": SUCCESSOR_FILTER,
        "target_open_rule": TARGET_OPEN_RULE,
        "posthoc_gate": POSTHOC_GATE,
        "source_file_hashes": SOURCE_FILE_HASHES,
        "source_hashes_match": hashes_match,
        "seed_or_target_materialized": False,
        "candidate_or_score_computed": False,
    }
    digest = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return RecurrentSupplyConfirmationPreregistration(
        SOURCE_COMMIT, RESERVED_CONFIRMATION_CENTER, TARGET_RADIUS,
        TRAINING_GROUPS, DEVELOPMENT_VALIDATION_GROUPS,
        PROTOTYPE_MINIMUM_GROUPS, SEPARATION_BIN_WIDTH,
        MINIMUM_POSITIVE_SUPPORT, MINIMUM_POSITIVE_GROUPS, MINIMUM_PURITY,
        ROOT_SCAN_ORDER, SUCCESSOR_DEPENDENCY, SUCCESSOR_FILTER,
        TARGET_OPEN_RULE, POSTHOC_GATE, SOURCE_FILE_HASHES, hashes_match,
        False, False, digest)


def main():
    print(json.dumps(asdict(audit()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
