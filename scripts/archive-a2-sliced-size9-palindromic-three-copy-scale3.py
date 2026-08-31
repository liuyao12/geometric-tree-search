#!/usr/bin/env python3
"""Build the deterministic 04636 three-copy scale-3 proof archive."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def load_record(path: Path, reflected: bool) -> dict:
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError(f"expected one NDJSON record in {path}")
    record = json.loads(lines[0])
    detail = record["three_copy_alcove_metatile_screen"]
    if (record["id"] != "a2sp_9_04636"
            or detail["scale"] != 3
            or detail["include_reflections"] is not reflected
            or record["classification"]
            != "no_three_copy_metatile_scalar3_substitution"
            or detail["certified"] is not True):
        raise ValueError(f"unexpected proof identity in {path}")
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proper", required=True)
    parser.add_argument("--reflected", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    records = [
        load_record(Path(args.proper), False),
        load_record(Path(args.reflected), True),
    ]
    payload = "".join(json.dumps(record, separators=(",", ":")) + "\n"
                      for record in records).encode()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    with temporary.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:
            stream.write(payload)
    temporary.replace(output)
    print(json.dumps({
        "records": len(records),
        "uncompressed_sha256": hashlib.sha256(payload).hexdigest(),
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "output": str(output),
    }, indent=2))


if __name__ == "__main__":
    main()
