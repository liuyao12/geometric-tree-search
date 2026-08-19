#!/usr/bin/env python3
"""One-shot frozen-fusion evaluation on ten preregistered IQC nuclei.

``prepare_candidate_receipt`` has no target API.  It crops detached seeds,
freezes every terminal action and both policy orders, then emits an inert JSON
receipt.  ``score_candidate_receipt`` accepts only that receipt, opens all ten
targets once, and performs pure lookups.  No fitting, feature generation,
candidate generation, or ranking occurs after target construction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, ORACLE_LIFT_BOUND, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_extended_fusion_execution_preregistration import (
    FUSION_ARTIFACT_DIGEST, FUSION_MODEL_DIGEST,
    audit as execution_preregistration)
from materials_gcts_iqc_frozen_fusion_runtime import (
    freeze_nucleus, load_default_runtime)
from materials_gcts_iqc_incidence_token_preflight import _key
from materials_gcts_iqc_spatial_beam_transfer_benchmark import _crop
from materials_gcts_icosahedral_modelset import oracle_patch_fast


RECEIPT_FORMAT = "gcts-iqc-extended-fusion-candidates-v1"


@dataclass(frozen=True)
class IQCExtendedFusionDevelopmentBenchmark:
    execution_manifest_digest: str
    fusion_artifact_digest: str
    fusion_model_digest: str
    centers: tuple[tuple[float, float, float], ...]
    seed_radius: float
    target_radius: float
    oracle_lift_bound: int
    seed_atoms: tuple[int, ...]
    target_atoms: tuple[int, ...]
    candidate_counts_by_depth: tuple[tuple[int, ...], ...]
    retained_counts_by_depth: tuple[tuple[int, ...], ...]
    terminal_counts: tuple[int, ...]
    candidate_digests: tuple[str, ...]
    candidate_receipt_digest: str
    bound_plus_one_stable_by_center: tuple[bool, ...]
    target_domains_pairwise_disjoint: bool
    scalar_terminal_supply_by_center: tuple[bool, ...]
    scalar_selected_exact_by_center: tuple[bool, ...]
    scalar_selected_correct_by_center: tuple[int, ...]
    scalar_first_exact_rank_by_center: tuple[int | None, ...]
    fusion_terminal_supply_by_center: tuple[bool, ...]
    fusion_selected_exact_by_center: tuple[bool, ...]
    fusion_selected_correct_by_center: tuple[int, ...]
    fusion_first_exact_rank_by_center: tuple[int | None, ...]
    scalar_terminal_supply: int
    scalar_selected_exact: int
    scalar_selected_correct: int
    fusion_terminal_supply: int
    fusion_selected_exact: int
    fusion_selected_correct: int
    selected_sites: int
    fusion_noninferior_to_scalar: bool
    target_open_count: int
    candidate_receipt_frozen_before_target: bool
    target_used_for_fit_features_candidates_or_ranking: bool
    fresh_confirmation_claimed: bool
    stationary_or_exponential_claimed: bool
    honest_status: str


def _canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _digest(payload):
    body = dict(payload)
    body.pop("receipt_digest", None)
    return hashlib.sha256(_canonical(body)).hexdigest()


def _crop_all(radius, *, lift_bound):
    physical_radius = math.ceil(max(math.dist((0., 0., 0.), center)
                                    for center in DEVELOPMENT_CENTERS) + radius)
    oracle, _ = oracle_patch_fast(lift_bound, physical_radius)
    return tuple(_crop(
        oracle, center, radius, "IQC-extended-fusion-development")
        for center in DEVELOPMENT_CENTERS)


def prepare_candidate_receipt():
    """Materialize detached seeds and freeze actions; never open targets."""
    protocol = execution_preregistration()
    if not protocol.source_hashes_match:
        raise AssertionError("extended fusion execution manifest drift")
    runtime = load_default_runtime()
    if (runtime["artifact_digest"] != FUSION_ARTIFACT_DIGEST
            or runtime["fusion_model"].model_digest != FUSION_MODEL_DIGEST):
        raise AssertionError("frozen fusion artifact drift")
    seeds = _crop_all(SEED_RADIUS, lift_bound=ORACLE_LIFT_BOUND)
    nuclei = tuple(freeze_nucleus(
        runtime, center=center, seed_positions=seed.positions,
        seed_species=seed.species, target_radius=TARGET_RADIUS)
        for center, seed in zip(DEVELOPMENT_CENTERS, seeds))
    rows = []
    for nucleus in nuclei:
        rows.append({
            "center": list(nucleus.center),
            "seed_atoms": nucleus.seed_atoms,
            "candidate_counts_by_depth": list(
                nucleus.candidate_counts_by_depth),
            "retained_counts_by_depth": list(
                nucleus.retained_counts_by_depth),
            "terminal_count": nucleus.terminal_count,
            "candidate_digest": nucleus.candidate_digest,
            "scalar_stable_index": nucleus.scalar_stable_index,
            "fusion_stable_index": nucleus.fusion_stable_index,
            "scalar_order": list(nucleus.scalar_order),
            "fusion_order": list(nucleus.fusion_order),
            "terminal_actions": [[list(point) + [color]
                                  for point, color in terminal.actions]
                                 for terminal in nucleus.terminals],
        })
    payload = {
        "format": RECEIPT_FORMAT,
        "execution_manifest_digest": protocol.manifest_digest,
        "fusion_artifact_digest": runtime["artifact_digest"],
        "fusion_model_digest": runtime["fusion_model"].model_digest,
        "seed_radius": SEED_RADIUS,
        "target_radius": TARGET_RADIUS,
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "nuclei": rows,
        "target_open_count": 0,
        "target_used": False,
    }
    payload["receipt_digest"] = _digest(payload)
    return payload


def validate_candidate_receipt(payload):
    protocol = execution_preregistration()
    if (payload.get("format") != RECEIPT_FORMAT
            or payload.get("execution_manifest_digest") !=
                protocol.manifest_digest
            or payload.get("fusion_artifact_digest") != FUSION_ARTIFACT_DIGEST
            or payload.get("fusion_model_digest") != FUSION_MODEL_DIGEST
            or payload.get("target_open_count") != 0
            or payload.get("target_used") is not False
            or payload.get("receipt_digest") != _digest(payload)
            or tuple(tuple(map(float, row["center"]))
                     for row in payload.get("nuclei", ())) !=
                DEVELOPMENT_CENTERS):
        raise ValueError("invalid or mutated pre-target candidate receipt")
    for row in payload["nuclei"]:
        count = int(row["terminal_count"])
        indices = set(range(count))
        if (count < 1 or len(row["terminal_actions"]) != count
                or set(map(int, row["scalar_order"])) != indices
                or set(map(int, row["fusion_order"])) != indices
                or int(row["scalar_stable_index"]) not in indices
                or int(row["fusion_stable_index"]) not in indices
                or any(len(actions) != 3
                       for actions in row["terminal_actions"])):
            raise ValueError("invalid frozen nucleus candidate table")
    return payload


def _actions(row, index):
    return tuple((tuple(map(float, action[:3])), str(action[3]))
                 for action in row["terminal_actions"][index])


def _score_order(row, order, truth):
    exact = tuple(all(truth.get(_key(point)) == color
                      for point, color in _actions(row, index))
                  for index in range(int(row["terminal_count"])))
    correct = tuple(sum(truth.get(_key(point)) == color
                        for point, color in _actions(row, index))
                    for index in range(int(row["terminal_count"])))
    ordered = tuple(map(int, row[order]))
    selected = ordered[0]
    first_exact = next((rank for rank, index in enumerate(ordered, 1)
                        if exact[index]), None)
    return any(exact), exact[selected], correct[selected], first_exact


def score_candidate_receipt(payload):
    """Open the target exactly once, then perform pure receipt scoring."""
    receipt = validate_candidate_receipt(payload)
    immutable = _canonical(receipt)
    targets = _crop_all(TARGET_RADIUS, lift_bound=ORACLE_LIFT_BOUND)
    checks = _crop_all(TARGET_RADIUS, lift_bound=ORACLE_LIFT_BOUND + 1)
    target_open_count = 1
    stable = tuple((tuple(target.positions), tuple(target.species)) ==
                   (tuple(check.positions), tuple(check.species))
                   for target, check in zip(targets, checks))
    target_keys = tuple({_key(point) for point in target.positions}
                        for target in targets)
    disjoint = all(not (target_keys[left] & target_keys[right])
                   for left in range(len(target_keys))
                   for right in range(left + 1, len(target_keys)))
    scalar, fusion = [], []
    for row, target in zip(receipt["nuclei"], targets):
        truth = {_key(point): str(color) for point, color in
                 zip(target.positions, target.species)}
        scalar.append(_score_order(row, "scalar_order", truth))
        fusion.append(_score_order(row, "fusion_order", truth))
    if immutable != _canonical(receipt):
        raise AssertionError("candidate receipt mutated after target open")
    selected_sites = 3 * len(DEVELOPMENT_CENTERS)
    scalar_supply = sum(row[0] for row in scalar)
    scalar_exact = sum(row[1] for row in scalar)
    scalar_correct = sum(row[2] for row in scalar)
    fusion_supply = sum(row[0] for row in fusion)
    fusion_exact = sum(row[1] for row in fusion)
    fusion_correct = sum(row[2] for row in fusion)
    noninferior = fusion_exact >= scalar_exact and \
        fusion_correct >= scalar_correct
    return IQCExtendedFusionDevelopmentBenchmark(
        receipt["execution_manifest_digest"],
        receipt["fusion_artifact_digest"], receipt["fusion_model_digest"],
        DEVELOPMENT_CENTERS, SEED_RADIUS, TARGET_RADIUS, ORACLE_LIFT_BOUND,
        tuple(int(row["seed_atoms"]) for row in receipt["nuclei"]),
        tuple(len(target.positions) for target in targets),
        tuple(tuple(map(int, row["candidate_counts_by_depth"]))
              for row in receipt["nuclei"]),
        tuple(tuple(map(int, row["retained_counts_by_depth"]))
              for row in receipt["nuclei"]),
        tuple(int(row["terminal_count"]) for row in receipt["nuclei"]),
        tuple(str(row["candidate_digest"]) for row in receipt["nuclei"]),
        receipt["receipt_digest"], stable, disjoint,
        tuple(row[0] for row in scalar), tuple(row[1] for row in scalar),
        tuple(row[2] for row in scalar), tuple(row[3] for row in scalar),
        tuple(row[0] for row in fusion), tuple(row[1] for row in fusion),
        tuple(row[2] for row in fusion), tuple(row[3] for row in fusion),
        scalar_supply, scalar_exact, scalar_correct,
        fusion_supply, fusion_exact, fusion_correct, selected_sites,
        noninferior, target_open_count, True, False, False, False,
        ("frozen fusion is noninferior on the preregistered extended "
         "development batch" if noninferior else
         "frozen fusion regresses on the preregistered extended development "
         "batch"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", type=Path)
    group.add_argument("--score", type=Path)
    args = parser.parse_args()
    if args.prepare:
        payload = prepare_candidate_receipt()
        args.prepare.write_bytes(_canonical(payload))
        print(json.dumps({
            "receipt_digest": payload["receipt_digest"],
            "nuclei": len(payload["nuclei"]),
            "target_open_count": payload["target_open_count"],
        }, indent=2, sort_keys=True))
    else:
        payload = json.loads(args.score.read_bytes())
        print(json.dumps(asdict(score_candidate_receipt(payload)),
                         indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
