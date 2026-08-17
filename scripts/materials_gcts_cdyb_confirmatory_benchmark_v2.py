#!/usr/bin/env python3
"""One-shot sealed Cd--Yb confirmation under immutable protocol v2."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_cdyb_confirmatory_preregistration_v2 import (
    FROZEN_MODEL_DIGEST, FROZEN_MODEL_MANIFEST, PROTOCOL_V2,
    TRAIN_CORPUS_DIGEST, OneShotOrderGuard, ConfirmatoryMetrics,
    audit_frozen_source_files, audit_frozen_manifests,
    derive_train_artifact_digests, evaluate_preregistered_gates,
    plus_one_lower_tail, plus_one_upper_tail, protocol_v2_digest)
from materials_gcts_cdyb_confirmatory_preregistration import \
    PROTOCOL as GEOMETRY_PROTOCOL
from materials_gcts_cdyb_confirmatory_execution_erratum import (
    ERRATUM_DIGEST, audit_erratum)
from materials_gcts_cdyb_continuous_completion_marking import (
    FrozenContinuousCompletionMarking, _Row, _corpus_digest, _dedupe, _fit,
    _frontier_rows, _predict, _select_lambda, evaluate as evaluate_train)
from materials_gcts_cdyb_deep_hierarchy_benchmark import TRAIN_CENTERS
from materials_gcts_cdyb_frozen_hierarchy_transfer_audit import (
    PACK_SEPARATION, _pack, _window_ids)
from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_macro_derivation import _site_key
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_partial_completion_execution_policy import (
    FrozenMacroFrequencyPolicy, adapt_continuous_completion_marking,
    completion_continuous_features, rank_execution_candidates)
from materials_gcts_partial_completion_executor import (
    PartialCompletionLevel, _classify, _dynamic_program,
    execute_partial_completion_hierarchy)
from materials_gcts_partial_completion_marking import freeze_completion_candidate
from materials_gcts_partial_completion_policy_arms import (
    FrozenCompletionPolicyArm, SingleUsePostPlanTargetFactory,
    execute_identical_completion_policy_arms, freeze_completion_execution_plan)
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import ExecutionBoundary


EXPECTED_PROTOCOL_DIGEST = \
    "3d4dfca24c7526baff14a2258c715e4caf0631af1c28af8ab41860b8e593c3f6"
SEALED_RESULT_PATH = (Path(__file__).parent / "fixtures" / "materials" /
                      "cdyb_confirmatory_v2_result.json")
SEALED_RESULT_SHA256 = \
    "f884212bd96232b8c7f94bbaa813c778cc4a3853a5d7c10dc68e46b3279dab02"
CONFIRMATORY_TRIAL_CONSUMED = True


@dataclass(frozen=True)
class ArmScore:
    name: str
    accepted_actions: int
    exact_actions: int
    action_precision: float
    unique_emitted_sites: int
    correct_emitted_sites: int
    site_precision: float
    recoverable_action_recall: float
    matched_work_checks: int
    matched_work_reached: bool


@dataclass(frozen=True)
class CdYbConfirmatoryV2Result:
    pretarget_abort_erratum_digest: str
    protocol_digest: str
    source_files_verified: bool
    train_artifacts_verified: bool
    regenerated_training_corpus_digest: str
    regenerated_model_digest: str
    seed_atoms: int
    first_wave_candidates: int
    first_wave_candidate_digest: str
    first_wave_candidates_identical_all_arms: bool
    execution_plan_digest: str
    execution_digest: str
    marked: ArmScore
    unmarked: ArmScore
    frequency: ArmScore
    null_trials: int
    null_exact_actions: tuple[int, ...]
    null_correct_sites: tuple[int, ...]
    null_matched_work_checks: tuple[int, ...]
    recoverable_exact_candidate_actions: int
    marked_correct_site_work_target: int
    exact_action_p: float
    correct_site_p: float
    matched_work_p: float
    matched_work_reduction: float
    multiwave_levels: int
    multiwave_accepted_by_level_wave: tuple[tuple[int, ...], ...]
    self_fed_depth: int
    outer_shell_target_atoms: int
    outer_shell_correct_emitted_atoms: int
    outer_atom_recall: float
    primary_gate_passed: bool
    sustained_growth_gate_passed: bool
    target_factory_calls: int
    order_events: tuple[tuple[str, str], ...]
    all_order_events_passed: bool
    target_used_before_open: bool
    refit_or_retuning_after_target: bool


def _digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        allow_nan=False, default=repr).encode()).hexdigest()


def _parent_map(quotient, promoted):
    parent = {macro_id: prototype_id for prototype_id, macro_id
              in promoted.prototype_macro_types}
    result = []
    cursor = 0
    for geometry in quotient.derivation_classes:
        for _alternative in geometry.alternatives:
            macro = quotient.alternative_macros[cursor]
            result.append((macro.macro_id, parent[geometry.geometry_class_id]))
            cursor += 1
    if cursor != len(quotient.alternative_macros):
        raise AssertionError("incomplete frozen alternative map")
    return tuple(result)


def _compile_hierarchy(species, positions):
    primitive = compile_irregular_port_program(species, positions)
    artifact = primitive
    levels = []
    for index in range(PROTOCOL_V2.maximum_hierarchy_levels):
        quotient = quotient_macro_supports(mine_port_graph_macros(
            artifact, maximum_nodes=3,
            include_boundary_relations=True).macro_types)
        if not quotient.quotient_macros:
            break
        promoted = promote_macro_types(
            artifact, quotient.quotient_macros, level=index + 1)
        levels.append((quotient, promoted, PartialCompletionLevel(
            artifact, quotient.alternative_macros,
            _parent_map(quotient, promoted), promoted)))
        artifact = promoted
    return primitive, tuple(levels)


def _training_rows(primitive, quotient, parent_map, species, positions,
                   namespaces):
    scale = primitive.cover.minimum_distance
    offsets = ((0., 0., 0.), (scale, 0., 0.), (-scale, 0., 0.),
               (0., scale, 0.), (0., -scale, 0.),
               (0., 0., scale), (0., 0., -scale))
    rows = []
    for patch in range(len(TRAIN_CENTERS)):
        origin = (patch * PACK_SEPARATION, 0., 0.)
        for offset in offsets:
            center = tuple(origin[axis] + offset[axis] for axis in range(3))
            rows.extend(_frontier_rows(
                primitive, quotient, parent_map, species, positions,
                namespaces, patch, center))
    return _dedupe(rows)


def _shuffle_rows(rows, seed):
    labels = [row.successful for row in rows]
    generator = random.Random(seed)
    for window in range(len(TRAIN_CENTERS)):
        indices = [index for index, row in enumerate(rows)
                   if row.window == window]
        values = [labels[index] for index in indices]
        generator.shuffle(values)
        for index, value in zip(indices, values):
            labels[index] = value
    return tuple(_Row(row.window, row.candidate_id, row.features, labels[index])
                 for index, row in enumerate(rows))


def _model_from_manifest():
    return FrozenContinuousCompletionMarking(**FROZEN_MODEL_MANIFEST)


def _initial_candidates(primitive, level, seed_occurrences, seed_sites,
                        boundary):
    dynamic = _dynamic_program(primitive, seed_occurrences, .03)
    raw = enumerate_partial_promoted_completions(
        dynamic, level.alternatives, minimum_matched_children=1,
        minimum_child_coverage=.5, explicit_seed_sites=seed_sites,
        public_boundary=boundary,
        frozen_parent_types=level.alternative_parent_types)
    macros = {item.macro_id: item for item in level.alternatives}
    occupied = tuple(seed_sites)
    exclusion = max(.03, primitive.cover.minimum_distance * .45)
    frozen = []
    completion_by_id = {}
    emitted = {}
    for completion in raw.completions:
        sites = tuple(site for child in completion.missing_children
                      for site in child.sites)
        novel, overlap, invalid = _classify(sites, occupied, .03, exclusion)
        candidate = freeze_completion_candidate(
            dynamic, macros[completion.macro_id], completion,
            live_overlap_support=overlap,
            live_collision_support=int(invalid))
        frozen.append(candidate)
        completion_by_id[candidate.candidate_id] = completion
        emitted[candidate.candidate_id] = frozenset(
            _site_key(site, .03) for site in novel)
    return dynamic, tuple(frozen), completion_by_id, macros, emitted


def _frequency_policy(quotient):
    counts = tuple((macro.macro_id, len(
        macro.promotion_occurrences or macro.occurrences))
                   for macro in quotient.alternative_macros)
    total = sum(value for _macro, value in counts)
    return FrozenMacroFrequencyPolicy(
        tuple((macro, (value + 1) / (total + len(counts)))
              for macro, value in counts),
        1 / max(1, total + len(counts)), total, False)


def _arm_model_digest(policy):
    return _digest(None if policy is None else asdict(policy))


def _arm_score(name, accepted_ids, emitted, target, exact_ids,
               recoverable, ranking_order, work_target):
    accepted_ids = tuple(accepted_ids)
    union = set().union(*(emitted[item] for item in accepted_ids)) \
        if accepted_ids else set()
    correct = union.intersection(target)
    exact = sum(item in exact_ids for item in accepted_ids)
    recovered = set()
    checks = 0
    for checks, item in enumerate(ranking_order, 1):
        recovered.update(emitted[item].intersection(target))
        if len(recovered) >= work_target:
            break
    reached = len(recovered) >= work_target
    if not work_target:
        checks, reached = 0, True
    return ArmScore(
        name, len(accepted_ids), exact,
        exact / max(1, len(accepted_ids)), len(union), len(correct),
        len(correct) / max(1, len(union)), exact / max(1, recoverable),
        checks, reached)


def _self_fed_depth(execution):
    depth = 0
    previous_emitted = True
    for level in execution.levels:
        for wave in level.waves:
            if wave.accepted_whole_macros <= 0 or not previous_emitted:
                return depth
            depth += 1
            previous_emitted = wave.appended_child_occurrences > 0
    return depth


def _consumed_trial_implementation():
    guard = OneShotOrderGuard()
    protocol_digest = protocol_v2_digest()
    if protocol_digest != EXPECTED_PROTOCOL_DIGEST:
        raise AssertionError("protocol-v2 digest mismatch")
    if not audit_erratum()["pretarget_abort_only"]:
        raise AssertionError("confirmatory pretarget abort is not certified")
    manifests = audit_frozen_manifests()
    source_checks = audit_frozen_source_files(Path(__file__).parent)
    if (not manifests["corpus_manifest_digest_matches"] or
            not manifests["model_digest_matches"] or
            not all(value for _name, value in source_checks)):
        raise AssertionError("frozen preregistration manifest mismatch")
    guard.record("protocol-verified", protocol_digest)

    train_audit = evaluate_train()
    train_digests = derive_train_artifact_digests(train_audit)
    if not train_digests["all_match"]:
        raise AssertionError("regenerated training audit mismatch")
    guard.record("training-artifacts-verified",
                 train_digests["train_audit_digest"])
    model = _model_from_manifest()
    if train_audit.frozen_model_digest != FROZEN_MODEL_DIGEST:
        raise AssertionError("regenerated model does not match manifest")
    linear = adapt_continuous_completion_marking(model)
    guard.record("model-frozen", FROZEN_MODEL_DIGEST)

    atoms = generate_cdyb(
        GEOMETRY_PROTOCOL.oracle_max_index,
        (GEOMETRY_PROTOCOL.oracle_cube_side_angstrom,) * 3)
    windows = _window_ids(atoms, GEOMETRY_PROTOCOL.train_centers)
    species, positions, namespaces = _pack(
        atoms, GEOMETRY_PROTOCOL.train_centers, windows)
    primitive, hierarchy = _compile_hierarchy(species, positions)
    if len(hierarchy) < PROTOCOL_V2.maximum_hierarchy_levels:
        raise AssertionError("frozen hierarchy has fewer than four levels")
    quotient, _promoted, first_level = hierarchy[0]
    rows = _training_rows(
        primitive, quotient, first_level.alternative_parent_types,
        species, positions, namespaces)
    if _corpus_digest(rows) != TRAIN_CORPUS_DIGEST:
        raise AssertionError("regenerated shuffled-refit corpus mismatch")
    null_models = []
    for trial in range(PROTOCOL_V2.shuffle_trials):
        shuffled = _shuffle_rows(rows, 912_701 + trial)
        ridge = _select_lambda(shuffled)
        null_models.append(adapt_continuous_completion_marking(
            _fit(shuffled, ridge)))

    center = GEOMETRY_PROTOCOL.confirmatory_center
    seed_ids = tuple(index for index, point in enumerate(atoms.positions)
                     if math.dist(point, center) <=
                     GEOMETRY_PROTOCOL.confirmatory_seed_radius + 1e-10)
    seed_species = tuple(atoms.symbols[index] for index in seed_ids)
    seed_positions = tuple(atoms.positions[index] for index in seed_ids)
    seed_sites = tuple(zip(seed_species, seed_positions))
    seed_enumeration = enumerate_frozen_port_occurrences(
        primitive, seed_species, seed_positions)
    guard.record("seed-opened", _digest(tuple(seed_ids)))
    boundary = ExecutionBoundary(center, PROTOCOL_V2.public_boundary_radius)
    dynamic, candidates, completion_by_id, macros, emitted = \
        _initial_candidates(primitive, first_level,
                            seed_enumeration.occurrences, seed_sites, boundary)
    marked_ranking = rank_execution_candidates(
        candidates, completion_by_id, macros,
        primitive.cover.minimum_distance, linear)
    guard.record("first-wave-candidates-frozen",
                 marked_ranking.candidate_digest)

    frequency = _frequency_policy(quotient)
    arm_specs = [FrozenCompletionPolicyArm("marked", linear),
                 FrozenCompletionPolicyArm("unmarked", None),
                 FrozenCompletionPolicyArm("frequency", frequency)]
    arm_specs.extend(FrozenCompletionPolicyArm(
        f"null-{index:02d}", policy)
                     for index, policy in enumerate(null_models))
    comparison = execute_identical_completion_policy_arms(
        first_level, seed_enumeration.occurrences, arms=tuple(arm_specs),
        explicit_seed_sites=seed_sites, public_boundary=boundary,
        maximum_accepted=PROTOCOL_V2.top_budget_per_wave,
        minimum_child_coverage=.5)
    if comparison.candidate_digest != marked_ranking.candidate_digest:
        raise AssertionError("manual and executor first-wave batches differ")
    arm_digests = tuple((
        item.name, FROZEN_MODEL_DIGEST if item.name == "marked" else
        _arm_model_digest(item.policy)) for item in arm_specs)
    plan = freeze_completion_execution_plan(
        comparison, source_digest=PROTOCOL_V2.source_commit,
        training_corpus_digest=TRAIN_CORPUS_DIGEST,
        arm_model_digests=arm_digests)
    guard.record("controls-frozen", plan.plan_digest)

    multiwave = execute_partial_completion_hierarchy(
        tuple(item[2] for item in hierarchy[:4]),
        seed_enumeration.occurrences, explicit_seed_sites=seed_sites,
        public_boundary=boundary, markings=(linear,) * 4,
        maximum_waves_per_level=PROTOCOL_V2.maximum_waves_per_level,
        maximum_accepted_per_wave=PROTOCOL_V2.top_budget_per_wave)
    execution_digest = _digest(asdict(multiwave))
    guard.record("execution-frozen", execution_digest)

    def target_factory():
        target_ids = tuple(index for index, point in enumerate(atoms.positions)
                           if math.dist(point, center) <=
                           GEOMETRY_PROTOCOL.confirmatory_target_radius + 1e-10)
        return target_ids, {_site_key(
            (atoms.symbols[index], atoms.positions[index]), .03)
                            for index in target_ids}
    single_use_factory = SingleUsePostPlanTargetFactory(target_factory)
    target_ids, target = guard.open_target(lambda: single_use_factory.open(plan))

    exact_ids = {item for item, sites in emitted.items()
                 if sites and sites.issubset(target)}
    rankings = {}
    rankings["marked"] = tuple(item.candidate.candidate_id
                               for item in marked_ranking.ranked)
    for spec in arm_specs[1:]:
        ranking = rank_execution_candidates(
            candidates, completion_by_id, macros,
            primitive.cover.minimum_distance, spec.policy)
        rankings[spec.name] = tuple(item.candidate.candidate_id
                                    for item in ranking.ranked)
    result_by_name = {item.name: item.execution for item in comparison.arms}
    accepted = {name: tuple(item.candidate_id for item in execution.certificates)
                for name, execution in result_by_name.items()}
    marked_union = set().union(*(emitted[item] for item in accepted["marked"])) \
        if accepted["marked"] else set()
    work_target = len(marked_union.intersection(target))
    recoverable = len(exact_ids)
    scores = {name: _arm_score(
        name, ids, emitted, target, exact_ids, recoverable,
        rankings[name], work_target) for name, ids in accepted.items()}
    null_scores = tuple(scores[f"null-{index:02d}"]
                        for index in range(PROTOCOL_V2.shuffle_trials))
    exact_p = plus_one_upper_tail(
        scores["marked"].exact_actions,
        tuple(item.exact_actions for item in null_scores))
    site_p = plus_one_upper_tail(
        scores["marked"].correct_emitted_sites,
        tuple(item.correct_emitted_sites for item in null_scores))
    work_p = plus_one_lower_tail(
        scores["marked"].matched_work_checks,
        tuple(item.matched_work_checks for item in null_scores))
    unmarked = scores["unmarked"]
    reduction = (unmarked.matched_work_checks /
                 max(1, scores["marked"].matched_work_checks)
                 if unmarked.matched_work_reached else 0.)
    seed_keys = {_site_key(site, .03) for site in seed_sites}
    final_keys = {_site_key(site, .03) for site in multiwave.final_sites}
    novel_final = final_keys - seed_keys
    outer_target = {_site_key((atoms.symbols[index], atoms.positions[index]), .03)
                    for index in target_ids
                    if math.dist(atoms.positions[index], center) >
                    GEOMETRY_PROTOCOL.confirmatory_seed_radius + 1e-10}
    outer_correct = len(novel_final.intersection(outer_target))
    depth = _self_fed_depth(multiwave)
    metrics = ConfirmatoryMetrics(
        scores["marked"].action_precision,
        scores["marked"].site_precision,
        scores["marked"].recoverable_action_recall,
        exact_p, site_p, work_p, reduction, depth,
        outer_correct / max(1, len(outer_target)))
    primary, sustained = evaluate_preregistered_gates(metrics)
    guard.record_score(execution_digest)
    order = guard.audit()
    return CdYbConfirmatoryV2Result(
        ERRATUM_DIGEST, protocol_digest,
        all(value for _name, value in source_checks),
        train_digests["all_match"], train_audit.training_corpus_digest,
        train_audit.frozen_model_digest, len(seed_ids), len(candidates),
        marked_ranking.candidate_digest,
        comparison.identical_frozen_candidate_batches, plan.plan_digest,
        execution_digest, scores["marked"], scores["unmarked"],
        scores["frequency"], PROTOCOL_V2.shuffle_trials,
        tuple(item.exact_actions for item in null_scores),
        tuple(item.correct_emitted_sites for item in null_scores),
        tuple(item.matched_work_checks for item in null_scores), recoverable,
        work_target, exact_p, site_p, work_p, reduction,
        len(multiwave.levels), tuple(tuple(
            wave.accepted_whole_macros for wave in level.waves)
                                    for level in multiwave.levels),
        depth, len(outer_target), outer_correct, metrics.outer_atom_recall,
        primary, sustained, order["target_factory_calls"], order["events"],
        order["execution_frozen_before_target"] and order["scored_once"] and
        order["target_factory_calls"] == 1, False, False)


def load_sealed_result() -> CdYbConfirmatoryV2Result:
    """Load the immutable one-shot result without reopening its target."""
    raw = SEALED_RESULT_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SEALED_RESULT_SHA256:
        raise AssertionError("sealed confirmatory result fixture changed")
    payload = json.loads(raw)
    for name in ("marked", "unmarked", "frequency"):
        payload[name] = ArmScore(**payload[name])
    for name in ("null_exact_actions", "null_correct_sites",
                 "null_matched_work_checks"):
        payload[name] = tuple(payload[name])
    payload["multiwave_accepted_by_level_wave"] = tuple(
        tuple(item) for item in payload["multiwave_accepted_by_level_wave"])
    payload["order_events"] = tuple(
        tuple(item) for item in payload["order_events"])
    return CdYbConfirmatoryV2Result(**payload)


def evaluate() -> CdYbConfirmatoryV2Result:
    """Return the sealed result; scientific execution cannot be repeated."""
    if not CONFIRMATORY_TRIAL_CONSUMED:
        raise AssertionError("confirmatory consumption latch is inconsistent")
    return load_sealed_result()


def execute_confirmatory_trial():
    raise RuntimeError(
        "CdYb confirmation v2 was consumed once; use load_sealed_result()")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if parser.parse_args().json else result)


if __name__ == "__main__":
    main()
