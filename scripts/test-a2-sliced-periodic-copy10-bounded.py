#!/usr/bin/env python3
"""Replay archived bounded ten-copy A2 quotient campaign receipts."""

import hashlib
import io
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parent.parent
CASES = (
    (
        "a2-sliced-alcove-size9-periodic-copy10-exact500k-summary.json",
        "a2-sliced-alcove-size9-periodic-copy10-exact500k-shards.tar.gz",
        [(38, 47), (37, 48), (38, 47)],
    ),
    (
        "a2-sliced-alcove-size9-periodic-copy10-exact2m-11364-summary.json",
        "a2-sliced-alcove-size9-periodic-copy10-exact2m-11364-shards.tar.gz",
        [(46, 39)],
    ),
    (
        "a2-sliced-alcove-size9-periodic-copy10-exact2m-remaining-summary.json",
        "a2-sliced-alcove-size9-periodic-copy10-exact2m-remaining-shards.tar.gz",
        [(44, 41), (47, 38)],
    ),
)


for summary_name, archive_name, expected_counts in CASES:
    summary = json.loads((ROOT / "data" / summary_name).read_text())
    archive = ROOT / "data" / archive_name
    node_limit = summary["exact_node_limit_per_orbit"]
    assert summary["classification"] == "bounded_inconclusive"
    assert summary["copies"] == 10
    assert summary["periodic_certificates"] == []
    assert [(item["exact_negative_orbits"], item["node_capped_orbits"])
            for item in summary["candidates"]] == expected_counts

    campaign_digest = hashlib.sha256()
    with tarfile.open(archive, "r:gz") as bundle:
        members = {Path(member.name).name: member for member in bundle.getmembers()
                   if member.isfile()}
        assert len(members) == sum(item["orbit_total"] for item in summary["candidates"])
        for candidate in summary["candidates"]:
            exact_negative = 0
            capped = 0
            hnf_covered = 0
            nodes = 0
            milliseconds = 0
            for receipt in candidate["receipts"]:
                member = members[receipt["path"]]
                payload = bundle.extractfile(member).read()
                assert hashlib.sha256(payload).hexdigest() == receipt["sha256"]
                campaign_digest.update(f"{receipt['path']}:{receipt['sha256']}\n".encode())
                rows = [json.loads(line) for line in io.BytesIO(payload) if line.strip()]
                assert len(rows) == 1 and rows[0]["id"] == candidate["id"]
                detail = rows[0]["periodic_z3"]
                assert detail["hnf_range"] == receipt["orbit_range"]
                assert detail["hnf_visited"] == 1
                assert detail["solver_unknown"] == receipt["solver_unknown"]
                assert detail["exact_multicover_nodes"] == receipt["exact_multicover_nodes"]
                assert detail["milliseconds"] == receipt["milliseconds"]
                if detail["solver_unknown"]:
                    capped += 1
                    assert detail["exact_multicover_nodes"] > node_limit
                    assert detail["hnf_covered"] == 0
                else:
                    exact_negative += 1
                    assert detail["hnf_covered"] > 0
                hnf_covered += detail["hnf_covered"]
                nodes += detail["exact_multicover_nodes"]
                milliseconds += detail["milliseconds"]
            assert exact_negative == candidate["exact_negative_orbits"]
            assert capped == candidate["node_capped_orbits"]
            assert hnf_covered == candidate["hnfs_exactly_excluded"]
            assert nodes == candidate["exact_multicover_nodes"]
            assert milliseconds == candidate["milliseconds"]

    assert campaign_digest.hexdigest() == summary["campaign_receipt_sha256"]

print("A2 bounded ten-copy periodic campaign archives replayed")
