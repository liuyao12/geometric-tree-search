#!/usr/bin/env python3
"""Fit a frozen fourth-block pose/port marking on consumed IQC nuclei.

Nuclei 0 and 1 are development data: their parent/successor targets have
already been opened by reach diagnostics.  This module labels every candidate
on causal fourth-block frontiers, retains the existing invariant descriptor
and five channel families, and freezes one model for a later untouched
nucleus.  Exact parent/action identities are not serialized into the model.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import pickle
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_frontier_attachment_benchmark import \
    _dominant_source_color
from materials_gcts_incidence_token_marking import IncidenceTokenExample
from materials_gcts_iqc_bounded_lineage_value import _correct, _truth_index
from materials_gcts_iqc_fourth_block_beam_fixture import \
    load_default_result as load_beams
from materials_gcts_iqc_frozen_fusion_runtime import (
    FusionSearchState, _child, load_default_runtime)
from materials_gcts_iqc_pose_port_state_audit import _descriptors
from materials_gcts_iqc_recurrent_branch_autonomous_confirmation import \
    UPSTREAM_ANGULAR_BIN_WIDTH
from materials_gcts_iqc_self_fed_complete_frontier_execution import \
    _bounded_at_radius
from materials_gcts_iqc_spatial_beam_transfer_benchmark import CLUSTER_EDGES
from materials_gcts_iqc_three_block_channel_execution import \
    _replay_action_set
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_pose_port_state_marking import (
    FrozenPosePortStateMarking, fit_pose_port_state_marking,
    pose_port_state_marking_digest, score_pose_port_state)
from materials_gcts_recursive_connections import local_cluster_types


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / \
    "fixtures/iqc_fourth_block_action_marking_v1.pkl.gz"
EXPECTED_FIXTURE_SHA256 = \
    "e70e2b2f7401a4127b8f7ba1cd9a1d118376ddc34bfe55f5ea459ff2f0cded6e"
EXPECTED_MODEL_DIGEST = \
    "5f30f3424d18194ac3b584a66f16a1d32778206d2ce75e01171e7de0e8be7563"
DEVELOPMENT_GROUPS = (0, 1)
DEPTH = 3


@dataclass(frozen=True)
class FrozenFourthBlockActionMarking:
    model: FrozenPosePortStateMarking
    source_beam_result_digest: str
    development_groups: tuple[int, ...]
    exact_parents_by_group: tuple[int, ...]
    causal_stages: int
    training_candidates: int
    training_positive_actions: int
    original_first_correct_ranks: tuple[int, ...]
    fitted_first_correct_ranks: tuple[int, ...]
    model_digest: str
    fixture_payload_digest: str
    targets_used_for_training: bool = True
    confirmation_target_used: bool = False
    raw_ids_or_absolute_coordinates_in_model: bool = False
    candidate_geometry_changed: bool = False


def _training_rows():
    beams = load_beams()
    runtime = load_default_runtime()
    examples = []
    stages = []
    exact_counts = []
    for group in DEVELOPMENT_GROUPS:
        beam = beams["beams"][group]
        if beam["heldout_target_opened"] or beam["target_used_for_ranking"]:
            raise AssertionError("development beam was not target sealed")
        target, _ = oracle_crop_fast(beam["center"], beam["next_radius"])
        truth = _truth_index(target.positions, target.species)
        exact = tuple(row for row in beam["candidates"] if all(
            _correct(point, color, truth)
            for point, color in row["actions"]))
        if not exact:
            raise AssertionError("development beam lacks an exact parent")
        exact_counts.append(len(exact))
        seed, _ = oracle_crop_fast(beam["center"], beam["seed_radius"])
        for parent in exact:
            source = SimpleNamespace(
                group=tuple(beam["center"]),
                seed_positions=tuple(seed.positions),
                seed_species=tuple(seed.species))
            for block, radius in enumerate(beam["replay_radii"]):
                state, _orders = _replay_action_set(
                    source, runtime,
                    parent["actions"][3 * block:3 * block + 3], radius)
                source = SimpleNamespace(
                    group=tuple(beam["center"]),
                    seed_positions=state.positions,
                    seed_species=state.species)
            frontier = _bounded_at_radius(
                runtime["connection"], source,
                local_cluster_types(source.seed_positions,
                                    source.seed_species, CLUSTER_EDGES),
                beam["next_radius"])
            state = FusionSearchState(
                tuple(source.seed_positions), tuple(source.seed_species),
                frontier, (), (), (), 0., ())
            for depth in range(DEPTH):
                descriptors = _descriptors(
                    state.positions, state.species, state.proposals,
                    UPSTREAM_ANGULAR_BIN_WIDTH)
                labels = {point: _correct(
                    point, str(_dominant_source_color(
                        state.proposals, point)), truth)
                    for point in state.proposals.votes}
                examples.extend(IncidenceTokenExample(
                    group, descriptor, labels[point])
                    for point, descriptor in descriptors.items())
                order = tuple(sorted(state.proposals.votes,
                                     key=lambda point: (
                    -score_pose_port_state(
                        runtime["state_model"], descriptors[point]),
                    -state.proposals.votes[point], point)))
                correct = tuple(point for point in order if labels[point])
                if not correct:
                    raise AssertionError("exact training path exhausted")
                stages.append((state, descriptors, labels,
                               order.index(correct[0]) + 1))
                point = correct[0]
                state = _child(
                    source, runtime["connection"], runtime["state_model"],
                    state, point, descriptors[point], beam["next_radius"])
    return beams, tuple(examples), tuple(stages), tuple(exact_counts)


def fit_artifact():
    beams, examples, stages, exact_counts = _training_rows()
    model = fit_pose_port_state_marking(
        examples, minimum_token_support=4, minimum_token_groups=2,
        token_shrinkage=.5, state_bin_width=1.,
        minimum_state_support=8, minimum_state_groups=2)
    fitted_ranks = []
    for state, descriptors, labels, _rank in stages:
        order = tuple(sorted(state.proposals.votes, key=lambda point: (
            -score_pose_port_state(model, descriptors[point]),
            -state.proposals.votes[point], point)))
        fitted_ranks.append(next(
            rank for rank, point in enumerate(order, 1) if labels[point]))
    model_digest = pose_port_state_marking_digest(model)
    metrics = (
        beams["result_digest"], DEVELOPMENT_GROUPS, exact_counts,
        len(stages), len(examples), sum(row.successful for row in examples),
        tuple(stage[-1] for stage in stages), tuple(fitted_ranks),
        model_digest, True, False, False, False)
    payload_digest = hashlib.sha256(repr(metrics).encode()).hexdigest()
    return FrozenFourthBlockActionMarking(
        model, beams["result_digest"], DEVELOPMENT_GROUPS, exact_counts,
        len(stages), len(examples), sum(row.successful for row in examples),
        tuple(stage[-1] for stage in stages), tuple(fitted_ranks),
        model_digest, payload_digest)


def validate_artifact(artifact):
    if (not isinstance(artifact, FrozenFourthBlockActionMarking)
            or artifact.development_groups != DEVELOPMENT_GROUPS
            or not artifact.targets_used_for_training
            or artifact.confirmation_target_used
            or artifact.raw_ids_or_absolute_coordinates_in_model
            or artifact.candidate_geometry_changed
            or pose_port_state_marking_digest(artifact.model) !=
            artifact.model_digest):
        raise AssertionError("fourth-block action marking drift")
    metrics = (
        artifact.source_beam_result_digest, artifact.development_groups,
        artifact.exact_parents_by_group, artifact.causal_stages,
        artifact.training_candidates, artifact.training_positive_actions,
        artifact.original_first_correct_ranks,
        artifact.fitted_first_correct_ranks, artifact.model_digest,
        artifact.targets_used_for_training, artifact.confirmation_target_used,
        artifact.raw_ids_or_absolute_coordinates_in_model,
        artifact.candidate_geometry_changed)
    if hashlib.sha256(repr(metrics).encode()).hexdigest() != \
            artifact.fixture_payload_digest:
        raise AssertionError("fourth-block marking payload drift")
    if EXPECTED_MODEL_DIGEST and artifact.model_digest != \
            EXPECTED_MODEL_DIGEST:
        raise AssertionError("fourth-block marking model digest drift")
    return artifact


def load_default_artifact(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(raw).hexdigest() != \
            EXPECTED_FIXTURE_SHA256:
        raise AssertionError("fourth-block marking fixture byte drift")
    payload = pickle.loads(gzip.decompress(raw))
    if not isinstance(payload, dict):
        raise AssertionError("fourth-block marking fixture schema drift")
    return validate_artifact(FrozenFourthBlockActionMarking(**payload))


def load_fourth_block_runtime():
    runtime = dict(load_default_runtime())
    runtime["state_model"] = load_default_artifact().model
    return runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        artifact = validate_artifact(fit_artifact())
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        # Store a plain payload rather than pickling the script's __main__
        # dataclass identity; the nested frozen marking types retain their
        # importable module identities.
        payload = dict(artifact.__dict__)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            pickle.dumps(payload, protocol=5), compresslevel=9, mtime=0))
    else:
        artifact = load_default_artifact()
    print({
        "development_groups": artifact.development_groups,
        "exact_parents_by_group": artifact.exact_parents_by_group,
        "causal_stages": artifact.causal_stages,
        "training_candidates": artifact.training_candidates,
        "training_positive_actions": artifact.training_positive_actions,
        "original_first_correct_ranks":
            artifact.original_first_correct_ranks,
        "fitted_first_correct_ranks": artifact.fitted_first_correct_ranks,
        "model_digest": artifact.model_digest,
        "confirmation_target_used": artifact.confirmation_target_used,
    })


if __name__ == "__main__":
    main()
