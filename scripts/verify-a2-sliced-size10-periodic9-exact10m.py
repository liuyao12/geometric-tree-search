#!/usr/bin/env python3
"""Replay the committed strongest receipts for the size-ten nine-copy campaign."""

from __future__ import annotations

import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SUMMARY_PATH = ROOT / "data" / "a2-sliced-size10-leaders-periodic9-exact10m-summary.json"
ARCHIVE_PATH = ROOT / "data" / "a2-sliced-size10-leaders-periodic9-exact10m-best-receipts.ndjson.gz"


summary = json.loads(SUMMARY_PATH.read_text())
payload = gzip.decompress(ARCHIVE_PATH.read_bytes())
records = [json.loads(line) for line in payload.splitlines() if line.strip()]

assert summary["campaign"] == "a2_sliced_size10_periodic9_exact10m_retry"
assert summary["copies"] == 9
assert summary["exact_node_limits_per_orbit"] == [2_000_000, 10_000_000]
assert summary["claim_scope"] == "fixed_9_copy_weighted_hnf_quotients"
assert summary["strongest_receipt_archive"] == (
    "data/a2-sliced-size10-leaders-periodic9-exact10m-best-receipts.ndjson.gz"
)
assert hashlib.sha256(payload).hexdigest() == summary["strongest_receipt_archive_sha256"]

by_id: dict[str, list[dict]] = defaultdict(list)
for record in records:
    detail = record["periodic_z3"]
    assert detail["hnf_visited"] == 1
    assert detail["hnf_orbit_representatives"] is True
    assert detail["hnf_orbit_total"] == 85
    assert detail["hnf_range"][1] == detail["hnf_range"][0] + 1
    assert record["classification"] in ("periodic", "unresolved")
    if record["classification"] == "periodic":
        assert detail["certificate"]["copies"] == 9
        assert detail["certificate"]["determinant"] == 15
        assert detail["replay"]["verified"] is True
    elif detail["solver_unknown"]:
        assert detail["solver_unknown"] == 1
        expected_cap = 2_000_000 if record["id"] == "a2sa_10_36194" else 10_000_000
        assert detail["exact_multicover_nodes"] > expected_cap
        assert detail["hnf_covered"] == 0
    else:
        assert detail["hnf_covered"] > 0
        assert detail.get("certificate") is None
    by_id[record["id"]].append(record)

summary_by_id = {candidate["id"]: candidate for candidate in summary["candidates"]}
expected = {
    "a2sa_10_36141": (85, 81, 4, 385),
    "a2sa_10_35323": (85, 77, 8, 367),
    "a2sa_10_36194": (44, 31, 12, 171),
}
for candidate_id, (receipt_count, negatives, caps, hnfs) in expected.items():
    candidate_records = by_id[candidate_id]
    assert len(candidate_records) == receipt_count
    assert [row["periodic_z3"]["hnf_range"][0] for row in candidate_records] == list(
        range(receipt_count)
    )
    exact_negative = sum(
        row["classification"] == "unresolved"
        and row["periodic_z3"]["solver_unknown"] == 0
        for row in candidate_records
    )
    unknown = sum(row["periodic_z3"]["solver_unknown"] for row in candidate_records)
    hnf_covered = sum(row["periodic_z3"]["hnf_covered"] for row in candidate_records)
    candidate_summary = summary_by_id[candidate_id]
    assert exact_negative == candidate_summary["exact_negative_orbits"] == negatives
    assert unknown == candidate_summary["node_capped_orbits"] == caps
    assert hnf_covered == candidate_summary["hnfs_exactly_excluded"] == hnfs
    assert sum(row["periodic_z3"]["exact_multicover_nodes"] for row in candidate_records) == (
        candidate_summary["exact_multicover_nodes"]
    )
    assert sum(row["periodic_z3"]["exact_multicover_failed_states"] for row in candidate_records) == (
        candidate_summary["exact_multicover_failed_states"]
    )

periodic = [row for row in records if row["classification"] == "periodic"]
assert len(periodic) == 1 and periodic[0]["id"] == "a2sa_10_36194"
assert periodic[0]["periodic_z3"]["hnf_range"] == [43, 44]
assert summary["periodic_certificates"] == [{"id": "a2sa_10_36194", "orbit": 43}]

print(json.dumps({
    "records_replayed": len(records),
    "campaign_payload_sha256": summary["strongest_receipt_archive_sha256"],
    "exact_negative_orbits": {
        candidate_id: summary_by_id[candidate_id]["exact_negative_orbits"]
        for candidate_id in expected
    },
    "node_capped_orbits": {
        candidate_id: summary_by_id[candidate_id]["node_capped_orbits"]
        for candidate_id in expected
    },
}, indent=2))
