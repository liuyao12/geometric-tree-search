#!/usr/bin/env python3
"""Stream-verify a complete five-copy substitution proof archive."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path


MARKER = b',"parent_results":['
SUFFIX = b']}}\n'
PATTERNS = {
    "index": re.compile(rb'"parent_index":(\d+)'),
    "atomic": re.compile(rb'"classification":"atomic_local_obstruction"'),
    "verified": re.compile(rb'"verified":true'),
    "unresolved": re.compile(rb'"classification":"unresolved"'),
    "rule": re.compile(rb'"classification":"mixed_metatile_rule"'),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    parser.add_argument("--archive", required=True)
    args = parser.parse_args()
    summary = json.loads(Path(args.summary).read_text())
    archive = Path(args.archive)
    archive_sha256 = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert archive_sha256 == summary["archive_sha256"]
    assert archive.name == summary["archive"]

    prefix = bytearray()
    with gzip.open(archive, "rb") as stream:
        while MARKER not in prefix:
            chunk = stream.read(1 << 16)
            if not chunk:
                raise ValueError("five-copy archive has no parent-results array")
            prefix.extend(chunk)
        marker_at = prefix.index(MARKER)
        payload_start = bytes(prefix[marker_at + len(MARKER):])
        prefix_record = json.loads(
            bytes(prefix[:marker_at]) + b',"parent_results":[]}}'
        )
        detail = prefix_record["five_copy_alcove_metatile_screen"]
        for key in (
            "certified", "scale", "include_reflections", "family",
            "four_copy_parent_total", "raw_connected_extensions",
            "symmetry_distinct_metatiles", "canonical_sha256",
            "parents_completed", "parent_counts", "closed_alphabet",
        ):
            assert detail[key] == summary[key], key
        assert prefix_record["id"] == summary["id"]
        assert prefix_record["classification"] == summary["classification"]

        result_digest = hashlib.sha256()
        counts = {key: 0 for key in PATTERNS}
        expected_index = 0
        regex_carry = b""
        suffix_carry = payload_start

        def consume(payload: bytes):
            nonlocal regex_carry, expected_index
            if not payload:
                return
            result_digest.update(payload)
            data = regex_carry + payload
            cutoff = max(0, len(data) - 256)
            for key, pattern in PATTERNS.items():
                for match in pattern.finditer(data):
                    if match.start() >= cutoff:
                        break
                    counts[key] += 1
                    if key == "index":
                        value = int(match.group(1))
                        assert value == expected_index, (expected_index, value)
                        expected_index += 1
            regex_carry = data[cutoff:]

        while True:
            chunk = stream.read(1 << 20)
            if not chunk:
                break
            suffix_carry += chunk
            if len(suffix_carry) > len(SUFFIX):
                consume(suffix_carry[:-len(SUFFIX)])
                suffix_carry = suffix_carry[-len(SUFFIX):]
        assert suffix_carry == SUFFIX
        for key, pattern in PATTERNS.items():
            for match in pattern.finditer(regex_carry):
                counts[key] += 1
                if key == "index":
                    value = int(match.group(1))
                    assert value == expected_index, (expected_index, value)
                    expected_index += 1

    total = summary["parents_completed"]
    assert counts == {
        "index": total,
        "atomic": summary["parent_counts"]["atomic_local_obstruction"],
        "verified": total,
        "unresolved": summary["parent_counts"]["unresolved"],
        "rule": summary["parent_counts"]["mixed_metatile_rule"],
    }
    assert result_digest.hexdigest() == summary["parent_results_sha256"]
    assert summary["all_parent_replays_verified"] is True
    cursor = 0
    merged_counts = {key: 0 for key in summary["parent_counts"]}
    for receipt in summary["range_receipts"]:
        start, stop = receipt["parent_range"]
        assert start == cursor and start < stop
        cursor = stop
        for key, value in receipt["parent_counts"].items():
            merged_counts[key] += value
    assert cursor == total
    assert merged_counts == summary["parent_counts"]
    print(json.dumps({
        "id": summary["id"],
        "classification": summary["classification"],
        "parents": total,
        "counts": counts,
        "canonical_sha256": summary["canonical_sha256"],
        "parent_results_sha256": summary["parent_results_sha256"],
        "archive_sha256": archive_sha256,
    }, indent=2))


if __name__ == "__main__":
    main()
