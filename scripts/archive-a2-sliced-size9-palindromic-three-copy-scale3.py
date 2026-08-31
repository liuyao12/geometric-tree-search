#!/usr/bin/env python3
"""Build a deterministic archive of size-9 palindromic scale-3 screens."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def load_record(path: Path) -> dict:
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError(f"expected one NDJSON record in {path}")
    record = json.loads(lines[0])
    detail = record["three_copy_alcove_metatile_screen"]
    if (not record["id"].startswith("a2sp_9_")
            or detail["scale"] != 3
            or record["classification"]
            != "no_three_copy_metatile_scalar3_substitution"
            or detail["certified"] is not True):
        raise ValueError(f"unexpected proof identity in {path}")
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    records = [load_record(Path(path)) for path in args.inputs]
    identities = [(record["id"], record["three_copy_alcove_metatile_screen"]
                   ["include_reflections"]) for record in records]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate candidate/model record")
    records.sort(key=lambda record: (
        record["id"],
        record["three_copy_alcove_metatile_screen"]["include_reflections"],
    ))
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
        "identities": identities,
        "uncompressed_sha256": hashlib.sha256(payload).hexdigest(),
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "output": str(output),
    }, indent=2))


if __name__ == "__main__":
    main()
