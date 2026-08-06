#!/usr/bin/env python3
"""Run the self-contained point-set, overlap-cover, and policy regressions."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
TESTS = (
    "test_materials_pointset_clusters.py",
    "test_materials_pointset_benchmarks.py",
    "test_materials_overlap_cover.py",
    "test_materials_cover_ranking.py",
    "test_materials_cover_scaling_benchmark.py",
    "test_materials_cover_curriculum.py",
    "test_materials_cover_value_benchmark.py",
    "test_materials_hierarchical_overlap_experiment.py",
)


def main() -> None:
    environment = dict(os.environ)
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        str(SCRIPTS) if not existing else str(SCRIPTS) + os.pathsep + existing)
    started = time.monotonic()
    for script in TESTS:
        test_started = time.monotonic()
        subprocess.run(
            [sys.executable, str(SCRIPTS / script)],
            cwd=ROOT,
            env=environment,
            check=True,
        )
        print(f"PASS {script} ({time.monotonic() - test_started:.2f}s)",
              flush=True)
    print(
        f"materials overlap-policy suite passed: {len(TESTS)} tests in "
        f"{time.monotonic() - started:.2f}s")


if __name__ == "__main__":
    main()
