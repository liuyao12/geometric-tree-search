#!/usr/bin/env python3
"""Replay atomic-obstruction and positive-rule receipts from direct campaigns."""

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
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def replay_atomic_obstruction(record: dict) -> bool:
    detail = record["alcove_substitution"]
    target = SCREEN.inflated_cells(record["alcoves"], detail["scale"])
    orientations = SCREEN.oriented_cells(
        record["alcoves"], detail["include_reflections"]
    )
    witness = tuple(detail["atomic_uncovered_alcove"])
    if witness not in target:
        return False
    for orientation in orientations:
        own = [SCREEN.cell_key(cell) for cell in orientation["cells"]]
        for anchor in own:
            if anchor[3] != witness[3]:
                continue
            delta = tuple(witness[axis] - anchor[axis] for axis in range(3))
            if all((cell[0] + delta[0], cell[1] + delta[1],
                    cell[2] + delta[2], cell[3]) in target for cell in own):
                return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--expected-results", type=int, default=0)
    args = parser.parse_args()
    rows = [row for path in args.inputs for row in read_ndjson(Path(path))]
    if args.expected_results and len(rows) != args.expected_results:
        raise RuntimeError(f"expected {args.expected_results} rows, found {len(rows)}")
    keys = set()
    counts = {"negative": 0, "positive": 0}
    for row in rows:
        detail = row["alcove_substitution"]
        key = row["id"], detail["scale"], bool(detail["include_reflections"])
        if key in keys:
            raise RuntimeError(f"duplicate campaign result {key}")
        keys.add(key)
        classification = row["alcove_substitution_classification"]
        if classification == "no_direct_scalar_substitution":
            if detail.get("certified") is not True:
                raise RuntimeError(f"uncertified negative {key}")
            if "atomic_uncovered_alcove" not in detail:
                raise RuntimeError(f"negative lacks replayable atomic witness {key}")
            if not replay_atomic_obstruction(row):
                raise RuntimeError(f"atomic obstruction replay failed {key}")
            counts["negative"] += 1
        elif classification == "substitution_rule":
            if detail.get("replay", {}).get("verified") is not True:
                raise RuntimeError(f"positive rule replay failed {key}")
            counts["positive"] += 1
        else:
            raise RuntimeError(f"campaign result is inconclusive {key}")
    print(json.dumps({"results": len(rows), **counts}, indent=2))


if __name__ == "__main__":
    main()
