#!/usr/bin/env python3
"""Command-line entry point for the corner-generated circle packing search."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from circle_packing_search import Solver


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bends", nargs="+", type=int)
    parser.add_argument("--max-circles", type=int)
    parser.add_argument("--node-limit", type=int, default=100_000)
    parser.add_argument("--tolerance", type=float, default=1e-9)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        solver = Solver(
            args.bends,
            max_circles=args.max_circles,
            node_limit=args.node_limit,
            tolerance=args.tolerance,
        )
    except ValueError as error:
        parser.error(str(error))

    result = solver.solve()
    contacts = None
    if result.circles is not None:
        contacts = [sorted(neighbors) for neighbors in solver.contacts(result.circles)]
    held = None
    if result.circles is not None:
        result_contacts = solver.contacts(result.circles)
        held = [solver.is_held(result.circles, index, result_contacts)
                for index in range(len(result.circles))]
    payload = {
        "status": result.status,
        "bends": list(solver.denominators),
        "max_circles": solver.max_circles,
        "nodes": result.nodes,
        "max_depth": result.max_depth,
        "reason": result.reason,
        "contacts": contacts,
        "held": held,
        "circles": None if result.circles is None else [
            {
                "bend": circle.denominator,
                "radius": circle.radius,
                "center": [circle.x, circle.y],
            }
            for circle in result.circles
        ],
    }
    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n")
    return {"found": 0, "exhausted": 1, "node_limit": 2}[result.status]


if __name__ == "__main__":
    raise SystemExit(main())
