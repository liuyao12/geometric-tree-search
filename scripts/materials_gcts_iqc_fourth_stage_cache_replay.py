#!/usr/bin/env python3
"""Replay the frozen 64-parent fourth stage with current target-free caches."""

from __future__ import annotations

import hashlib
import json
import time
from types import SimpleNamespace

from materials_gcts_iqc_fresh_parent_balanced_execution_v3 import \
    _chunked_fourth_parents
from materials_gcts_iqc_parent_balanced_confirmation_preregistration import (
    FOURTH_RADIUS, SEED_RADIUS)
from materials_gcts_iqc_parent_balanced_v3_consumed_benchmark import (
    CONSUMED_CENTER, load_default_result)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


WORKERS = 4


def evaluate():
    row = load_default_result()
    receipt = row["receipt"]
    seed, _lifts = oracle_crop_fast(CONSUMED_CENTER, SEED_RADIUS)
    lineages = tuple(SimpleNamespace(**receipt["raw_nine_action_lineages"][
        raw_index]) for raw_index in
        receipt["selected_nine_action_lineage_indices"])
    tasks = tuple((
        tuple(CONSUMED_CENTER), tuple(seed.positions), tuple(seed.species),
        FOURTH_RADIUS, index, lineage)
        for index, lineage in enumerate(lineages))
    started = time.perf_counter()
    groups = _chunked_fourth_parents(tasks, WORKERS)
    elapsed = time.perf_counter() - started
    candidates = tuple(candidate for _parent, _count, rows in groups
                       for candidate in rows)
    digest = hashlib.sha256(repr(tuple((
        candidate.parent_lineage_index, candidate.fourth_stable_index,
        candidate.all_actions) for candidate in candidates)).encode()
    ).hexdigest()
    old_seconds = dict(receipt["stage_seconds"])["chunked_fourth_frontiers"]
    result = {
        "schema_version": 1,
        "parents": len(groups),
        "candidates": len(candidates),
        "workers": WORKERS,
        "candidate_digest": digest,
        "original_candidate_digest": receipt["candidate_digest"],
        "exact_candidate_digest_parity": digest == receipt["candidate_digest"],
        "old_stage_seconds": old_seconds,
        "cached_stage_seconds": elapsed,
        "stage_speedup": old_seconds / elapsed,
        "target_used": False,
    }
    if (result["parents"] != 64 or result["candidates"] != 512 or
            not result["exact_candidate_digest_parity"]):
        raise AssertionError("fourth-stage cache replay drift")
    return result


def main():
    print(json.dumps(evaluate(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
