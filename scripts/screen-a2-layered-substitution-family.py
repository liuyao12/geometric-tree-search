#!/usr/bin/env python3
"""Screen the complete small cellular A2 planar/layer inflation grid."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load_substitution():
    spec = importlib.util.spec_from_file_location(
        "a2_substitution", ROOT / "scripts" / "screen-a2-layered-substitution.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SUBSTITUTION = load_substitution()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--minimum", type=int, default=2)
    parser.add_argument("--maximum", type=int, default=8)
    parser.add_argument("--timeout-ms", type=int, default=120000)
    args = parser.parse_args()
    if args.minimum < 2 or args.maximum < args.minimum:
        parser.error("invalid expansive scale range")

    records = [
        json.loads(line)
        for line in Path(args.input).read_text().splitlines()
        if line.strip()
    ]
    output = Path(args.output)
    output.write_text("")
    counts = {}
    inflations = 0
    with output.open("a") as stream:
        for planar_scale in range(args.minimum, args.maximum + 1):
            for vertical_scale in range(args.minimum, args.maximum + 1):
                if planar_scale == vertical_scale:
                    continue
                inflations += 1
                local_counts = {}
                for record in records:
                    result = SUBSTITUTION.screen(
                        record, 2, args.timeout_ms,
                        planar_scale, 0, vertical_scale,
                    )
                    classification = result["substitution_classification"]
                    counts[classification] = counts.get(classification, 0) + 1
                    local_counts[classification] = local_counts.get(classification, 0) + 1
                    stream.write(json.dumps(result, separators=(",", ":")) + "\n")
                    stream.flush()
                print(
                    f"planar={planar_scale} layer={vertical_scale} {local_counts}",
                    flush=True,
                )
    print(json.dumps({
        "candidates": len(records),
        "inflations": inflations,
        "records": len(records) * inflations,
        "counts": counts,
        "output": str(output),
    }, indent=2))


if __name__ == "__main__":
    main()
