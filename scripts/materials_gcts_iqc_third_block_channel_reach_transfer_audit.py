#!/usr/bin/env python3
"""All-development transfer audit for compute-matched channel reach.

The fixed selector screened on consumed nuclei 1 and 2 spends eight child
expansions as three scalar leaders plus one leader from each of five frozen
pose/port channels.  Here it is replayed on every exact parent in the other
consumed development nuclei.  The four design-parent candidate trees are
loaded byte-for-byte from their frozen fixture; all other trees are generated
target-free in worker processes.  One target opening then compares supply to
the original scalar top-8 executor.

This is a preservation/transfer test over already-consumed development
nuclei, not a fresh confirmation and not an autonomous commit rule.
"""

from __future__ import annotations

import argparse
import concurrent.futures.process as process
import gzip
import hashlib
import json
import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_child_option_third_block_audit import (
    EXPECTED_RESULT_DIGEST as SOURCE_RESULT_DIGEST, THIRD_BLOCK_RADIUS,
    load_default_result as load_source_result)
from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_frozen_fusion_artifact import canonical_json
from materials_gcts_iqc_frozen_fusion_runtime import (
    action_key, load_default_runtime)
from materials_gcts_iqc_self_fed_terminal_dataset import (
    OUTER_ORACLE_LIFT_BOUND, SECOND_BLOCK_RADIUS)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_iqc_third_block_channel_reach_audit import (
    ACTION_BUDGET, BASELINE_SLOTS,
    EXPECTED_RESULT_DIGEST as DESIGN_RESULT_DIGEST, ParentChannelReach,
    _channel_tree, _key, _replay_unordered,
    _source_exact_parent_receipts,
    load_default_result as load_design_result)
from materials_gcts_icosahedral_modelset import oracle_patch_fast


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_third_block_channel_reach_transfer_v1.json.gz"
EXPECTED_FIXTURE_SHA256 = \
    "28cf985bbf462c78a1a47ba71c99a48ceded33a07a13a853f10135a42bcaf4d0"
EXPECTED_RESULT_DIGEST = \
    "f761fa971d1f1e1a121836bec3e8b234f94abdef4b70bf0048750413a44aef7e"


def _worker(payload):
    group, center, seed_positions, seed_species, parent_receipts = payload
    runtime = load_default_runtime()
    original = SimpleNamespace(
        group=tuple(center), seed_positions=tuple(seed_positions),
        seed_species=tuple(seed_species))
    inherited, inherited_orders = _replay_unordered(
        original, runtime, parent_receipts[0]["inherited_actions"],
        TARGET_RADIUS)
    rows = []
    for receipt in parent_receipts:
        if receipt["inherited_actions"] != \
                parent_receipts[0]["inherited_actions"]:
            raise AssertionError("group inherited action-set drift")
        second = SimpleNamespace(
            group=tuple(center), seed_positions=inherited.positions,
            seed_species=inherited.species)
        parent, parent_orders = _replay_unordered(
            second, runtime, receipt["parent_actions"], SECOND_BLOCK_RADIUS)
        third = SimpleNamespace(
            group=tuple(center), seed_positions=parent.positions,
            seed_species=parent.species)
        terminals, counts = _channel_tree(third, runtime)
        terminal_actions = tuple(action_key(state.actions)
                                 for state in terminals)
        body = (group, int(receipt["parent_stable_index"]), counts,
                terminal_actions)
        rows.append(asdict(ParentChannelReach(
            group, int(receipt["parent_stable_index"]), inherited_orders,
            parent_orders, counts, len(terminals), terminal_actions,
            hashlib.sha256(repr(body).encode()).hexdigest())))
    return tuple(rows)


def _prepare_pool():
    try:
        process._check_system_limits()
    except PermissionError:
        process._check_system_limits = lambda: None


def _baseline_by_parent(source):
    result = {}
    for group in source["scored_groups"]:
        group_index = int(group["group"])
        for parent in group["parents"]:
            if parent["parent_exact"]:
                result[(group_index, int(parent["parent_stable_index"]))] = \
                    int(parent["complete_exact_terminal_supply"])
    return result


def evaluate(*, workers=4):
    if workers < 1:
        raise ValueError("workers must be positive")
    source = load_source_result()
    design = load_design_result()
    if (source["result_digest"] != SOURCE_RESULT_DIGEST or
            design["result_digest"] != DESIGN_RESULT_DIGEST or
            design["supplied_parents"] != 4):
        raise AssertionError("channel-reach upstream evidence drift")
    parent_receipts = _source_exact_parent_receipts(source)
    if sum(map(len, parent_receipts.values())) != 15:
        raise AssertionError("exact-parent universe drift")

    cached = {(int(row["group"]), int(row["parent_stable_index"])): row
              for row in design["receipt"]}
    seed_physical = math.ceil(max(math.dist((0., 0., 0.), center)
                                  for center in DEVELOPMENT_CENTERS)
                              + SEED_RADIUS)
    seed_oracle, _ = oracle_patch_fast(
        OUTER_ORACLE_LIFT_BOUND, seed_physical)
    seeds = tuple(_crop(seed_oracle, center, SEED_RADIUS,
                        "IQC-channel-reach-transfer-seed")
                  for center in DEVELOPMENT_CENTERS)
    payloads = []
    for group, receipts in sorted(parent_receipts.items()):
        if all((group, int(row["parent_stable_index"])) in cached
               for row in receipts):
            continue
        seed = seeds[group]
        payloads.append((group, DEVELOPMENT_CENTERS[group],
                         tuple(seed.positions), tuple(seed.species), receipts))
    if workers == 1:
        generated = tuple(_worker(payload) for payload in payloads)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            generated = tuple(pool.map(_worker, payloads))
    generated_rows = {(
        int(row["group"]), int(row["parent_stable_index"])): row
        for group_rows in generated for row in group_rows}
    rows = []
    for group, receipts in sorted(parent_receipts.items()):
        for parent in receipts:
            key = group, int(parent["parent_stable_index"])
            row = cached.get(key, generated_rows.get(key))
            if row is None:
                raise AssertionError("missing channel-reach parent receipt")
            rows.append(row)
    receipt = tuple(rows)
    receipt_digest = hashlib.sha256(canonical_json(receipt)).hexdigest()

    # Targets remain absent until all fifteen exact-parent trees are frozen.
    target_physical = math.ceil(max(math.dist((0., 0., 0.), center)
                                    for center in DEVELOPMENT_CENTERS)
                                + THIRD_BLOCK_RADIUS)
    target_oracle, _ = oracle_patch_fast(
        OUTER_ORACLE_LIFT_BOUND, target_physical)
    targets = tuple(_crop(target_oracle, center, THIRD_BLOCK_RADIUS,
                          "IQC-channel-reach-transfer-target")
                    for center in DEVELOPMENT_CENTERS)
    scored = []
    for row in receipt:
        truth = {_key(point): str(color) for point, color in zip(
            targets[int(row["group"])].positions,
            targets[int(row["group"])].species)}
        exact = sum(all(truth.get(_key(point)) == str(color)
                        for point, color in actions)
                    for actions in row["terminal_actions"])
        scored.append({
            "group": int(row["group"]),
            "parent_stable_index": int(row["parent_stable_index"]),
            "exact_terminal_paths": exact,
            "supplied": exact > 0,
        })

    baseline = _baseline_by_parent(source)
    baseline_groups = {group for (group, parent), count in baseline.items()
                       if count > 0}
    channel_groups = {row["group"] for row in scored if row["supplied"]}
    baseline_parents = sum(count > 0 for count in baseline.values())
    channel_parents = sum(row["supplied"] for row in scored)
    design_groups = frozenset((1, 2))
    transfer_groups = frozenset(parent_receipts) - design_groups
    preserved_transfer = baseline_groups & transfer_groups <= channel_groups
    recovered_design = design_groups <= channel_groups
    gate = (preserved_transfer and recovered_design and
            len(channel_groups) >= len(baseline_groups) and
            channel_parents >= baseline_parents)
    body = {
        "schema_version": 1,
        "source_result_digest": source["result_digest"],
        "design_result_digest": design["result_digest"],
        "action_budget": ACTION_BUDGET,
        "baseline_slots": BASELINE_SLOTS,
        "channel_slots": 5,
        "matched_child_expansion_budget": True,
        "exact_parents": len(scored),
        "design_parents_reused": len(cached),
        "generated_transfer_parents": len(generated_rows),
        "receipt": receipt,
        "receipt_digest": receipt_digest,
        "scored_parents": tuple(scored),
        "baseline_supplied_parents": baseline_parents,
        "channel_supplied_parents": channel_parents,
        "baseline_supplied_groups": len(baseline_groups),
        "channel_supplied_groups": len(channel_groups),
        "baseline_exact_paths": sum(baseline.values()),
        "channel_exact_paths": sum(row["exact_terminal_paths"]
                                   for row in scored),
        "design_groups": tuple(sorted(design_groups)),
        "transfer_groups": tuple(sorted(transfer_groups)),
        "baseline_supplied_group_ids": tuple(sorted(baseline_groups)),
        "channel_supplied_group_ids": tuple(sorted(channel_groups)),
        "baseline_transfer_groups_preserved": preserved_transfer,
        "design_groups_recovered": recovered_design,
        "development_preservation_gate_passed": gate,
        "target_open_count": 1,
        "target_used_for_candidate_generation_or_ranking": False,
        "selector_proposed_after_consumed_failure": True,
        "consumed_development_only": True,
        "fresh_confirmation_claimed": False,
        "causal_superiority_claimed": False,
        "autonomous_commit_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["source_result_digest"] != SOURCE_RESULT_DIGEST or
            body["design_result_digest"] != DESIGN_RESULT_DIGEST or
            body["action_budget"] != 8 or body["baseline_slots"] != 3 or
            body["channel_slots"] != 5 or
            not body["matched_child_expansion_budget"] or
            body["exact_parents"] != 15 or
            body["design_parents_reused"] != 4 or
            body["generated_transfer_parents"] != 11 or
            body["baseline_supplied_parents"] != 11 or
            body["channel_supplied_parents"] != 15 or
            body["baseline_supplied_groups"] != 6 or
            body["channel_supplied_groups"] != 8 or
            body["baseline_exact_paths"] != 90 or
            body["channel_exact_paths"] != 472 or
            not body["baseline_transfer_groups_preserved"] or
            not body["design_groups_recovered"] or
            not body["development_preservation_gate_passed"] or
            body["target_open_count"] != 1 or
            body["target_used_for_candidate_generation_or_ranking"] or
            not body["selector_proposed_after_consumed_failure"] or
            not body["consumed_development_only"] or
            body["fresh_confirmation_claimed"] or
            body["causal_superiority_claimed"] or
            body["autonomous_commit_claimed"] or
            body["stationary_or_exponential_claimed"]):
        raise AssertionError("IQC channel-reach transfer audit drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("IQC channel-reach transfer digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("IQC channel-reach transfer fixture drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    row = evaluate(workers=args.workers)
    text = json.dumps(row, indent=2, sort_keys=True) + "\n"
    if args.write:
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            text.encode(), compresslevel=9, mtime=0))
    print(text, end="")


if __name__ == "__main__":
    main()
