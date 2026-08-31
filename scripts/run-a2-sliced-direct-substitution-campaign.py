#!/usr/bin/env python3
"""Resume direct scalar-substitution screens for selected A2-sliced survivors."""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_sliced_direct_substitution",
    ROOT / "scripts" / "screen-a2-sliced-alcove-substitution.py",
)
SCREEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCREEN)


def read_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def parse_scales(value: str) -> list[int]:
    scales = set()
    for part in value.split(","):
        bounds = part.strip().split("-", 1)
        if len(bounds) == 1:
            scales.add(int(bounds[0]))
        else:
            start, stop = map(int, bounds)
            scales.update(range(start, stop + 1))
    if not scales or min(scales) < 2:
        raise argparse.ArgumentTypeError("scales must be integers at least two")
    return sorted(scales)


def result_key(record: dict) -> tuple[str, int, bool]:
    detail = record["alcove_substitution"]
    return record["id"], detail["scale"], bool(detail["include_reflections"])


def valid_result(record: dict) -> bool:
    classification = record.get("alcove_substitution_classification")
    detail = record.get("alcove_substitution", {})
    if classification == "substitution_rule":
        return detail.get("replay", {}).get("verified") is True
    if classification == "no_direct_scalar_substitution":
        if detail.get("certified") is not True:
            return False
        atomic = detail.get("atomic_uncovered_alcove")
        if atomic is not None:
            return detail.get("independent_replay", {}).get("verified") is True
        return True
    return classification == "unresolved" and detail.get("stopped_by") == "time_limit"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--candidate-ids", default="")
    parser.add_argument("--all-unresolved", action="store_true")
    parser.add_argument("--scales", type=parse_scales, default=parse_scales("2-8"))
    parser.add_argument("--models", choices=("proper", "reflected", "both"), default="both")
    parser.add_argument("--timeout-ms", type=int, default=120000)
    args = parser.parse_args()

    source = read_ndjson(Path(args.input))
    unresolved = [row for row in source if row.get("classification") == "unresolved"]
    requested = {item.strip() for item in args.candidate_ids.split(",") if item.strip()}
    if not args.all_unresolved and not requested:
        parser.error("choose --all-unresolved or provide --candidate-ids")
    records = unresolved if args.all_unresolved else [
        row for row in unresolved if row["id"] in requested
    ]
    missing = requested - {row["id"] for row in records}
    if missing:
        parser.error(f"candidate IDs not found among unresolved input rows: {sorted(missing)}")

    output = Path(args.output)
    prior = read_ndjson(output)
    if any(not valid_result(row) for row in prior):
        raise RuntimeError(f"invalid prior result in {output}")
    completed = {result_key(row) for row in prior}
    reflected_options = {
        "proper": (False,),
        "reflected": (True,),
        "both": (False, True),
    }[args.models]

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as stream:
        for scale in args.scales:
            for include_reflections in reflected_options:
                for record in records:
                    key = record["id"], scale, include_reflections
                    if key in completed:
                        continue
                    result = SCREEN.screen(
                        record, scale, args.timeout_ms, include_reflections
                    )
                    if not valid_result(result):
                        raise RuntimeError(f"unverifiable substitution result for {key}")
                    stream.write(json.dumps(result, separators=(",", ":")) + "\n")
                    stream.flush()
                    completed.add(key)
                    print(json.dumps({
                        "id": record["id"],
                        "scale": scale,
                        "model": "reflected" if include_reflections else "proper",
                        "classification": result["alcove_substitution_classification"],
                    }, separators=(",", ":")), flush=True)

    rows = read_ndjson(output)
    print(json.dumps({
        "candidates": len(records),
        "scales": args.scales,
        "models": args.models,
        "results": len(rows),
        "substitution_rules": sum(
            row["alcove_substitution_classification"] == "substitution_rule"
            for row in rows
        ),
        "unresolved": sum(
            row["alcove_substitution_classification"] == "unresolved"
            for row in rows
        ),
        "output": str(output),
    }, indent=2))


if __name__ == "__main__":
    main()
