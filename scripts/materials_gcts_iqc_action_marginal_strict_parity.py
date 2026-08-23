#!/usr/bin/env python3
"""No-saturation parity of compute-bounded V4 against consumed V3."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import time
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_fresh_parent_balanced_execution_v4 import \
    _complete_action_marginal_lineages
from materials_gcts_iqc_joint_child_action_marking_fit import CASES
from materials_gcts_iqc_parent_balanced_v3_consumed_benchmark import \
    load_default_result
from materials_gcts_icosahedral_modelset import oracle_crop_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_action_marginal_strict_parity_v1.json"
EXPECTED_FIXTURE_SHA256 = \
    "705427e064df42880b9d2bf637b9765b2eae62c2f23620dda74f9c599d9ecf7b"


def validate_result(result):
    if (result["target_used"] or result["selected_prefixes"] != 8 or
            result["diverse_fallback_prefixes"] != 0 or
            result["raw_nine_action_lineages"] != 1102 or
            not result["exact_receipt_parity"] or
            result["raw_lineage_digest"] != result["expected_v3_digest"]):
        raise AssertionError("strict action-marginal parity drift")
    return result


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("strict action-marginal parity fixture drift")
    return validate_result(json.loads(raw))


def evaluate(workers=4):
    name, relative, center = CASES[0]
    receipt = json.loads(gzip.decompress(
        (Path(__file__).resolve().parent / relative).read_bytes()))["receipt"]
    branches = tuple(SimpleNamespace(**row)
                     for row in receipt["second_branches"])
    seed, _ = oracle_crop_fast(center, 9.)
    started = time.perf_counter()
    lineages, _scheduled, marginal = _complete_action_marginal_lineages(
        center=center, seed_positions=seed.positions,
        seed_species=seed.species, radii=tuple(receipt["radii"][:3]),
        raw=SimpleNamespace(second_branches=branches), workers=workers)
    elapsed = time.perf_counter() - started
    digest = hashlib.sha256(repr(tuple(
        row.all_actions for row in lineages)).encode()).hexdigest()
    expected = load_default_result()["receipt"][
        "raw_nine_action_lineage_digest"]
    result = {
        "case": name,
        "selected_prefixes": len(marginal["selected_rows"]),
        "diverse_fallback_prefixes":
            len(marginal["diverse_fallback_rows"]),
        "joint_universal_actions":
            len(marginal["joint_universal_actions"]),
        "raw_nine_action_lineages": len(lineages),
        "raw_lineage_digest": digest,
        "expected_v3_digest": expected,
        "exact_receipt_parity": digest == expected,
        "third_frontier_seconds": elapsed,
        "target_used": False,
    }
    return validate_result(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    print(json.dumps(evaluate() if args.live else load_default_result(),
                     indent=2, sort_keys=True))
