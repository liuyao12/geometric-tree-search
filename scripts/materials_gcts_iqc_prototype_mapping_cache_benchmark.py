#!/usr/bin/env python3
"""Target-free consumed-parent audit of frozen prototype mapping reuse."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_prototype_mapping_cache_consumed_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "c6d10831e33ae3abdce8098eccf4b2362311066a823e6ea3e0ed27667e459be8"


def validate_result(row):
    if (row["schema_version"] != 1 or row["target_used"] or
            not row["exact_action_parity"] or
            not row["incremental_local_types"] or
            row["state_counts"] != [8, 38, 143] or
            row["geometry_cache_hits"] != 187 or
            row["geometry_cache_misses"] != 189 or
            row["prototype_mapping_cache_entries"] != 687 or
            len(row["action_digest"]) != 64 or
            row["uncached_seconds"] <= row["cached_seconds"] or
            row["uncached_seconds"] / row["cached_seconds"] < 2.):
        raise AssertionError("prototype mapping cache benchmark drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if (EXPECTED_FIXTURE_SHA256 and
            hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256):
        raise AssertionError("prototype mapping cache fixture byte drift")
    return validate_result(json.loads(raw))


def main():
    row = load_default_result()
    row = {**row, "speedup":
           row["uncached_seconds"] / row["cached_seconds"]}
    print(json.dumps(row, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
