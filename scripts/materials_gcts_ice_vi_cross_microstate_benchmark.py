#!/usr/bin/env python3
"""Sealed Ice-VI growth across occupational microstates.

The learner sees one geometry-valid D2O microstate and three training-side
calibration microstates.  It then receives only a spatially disjoint nucleus
from a fifth microstate.  All candidate traces are frozen before the held-out
outer crop is constructed.  The benchmark distinguishes two claims:

* exact oxygen-framework continuation with mutually exclusive D2O pose
  hypotheses; and
* a stronger, generally false claim that the occupational realization itself
  is determined by local geometry.

The oracle bridge is isolated in a subprocess and returns only requested
molecular crops.  No family label, formula, lattice-site index, energy, or
target coordinate enters the grammar or either executor.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from materials_gcts_molecular_conformer_port_growth import (
    execute_molecular_conformer_anchor_growth,
    execute_molecular_conformer_growth,
    fit_molecular_conformer_grammar,
    grammar_audit,
    recognize_seed_conformers,
)
from materials_gcts_molecular_port_growth import score_sites


ROOT = Path(__file__).resolve().parents[1]
NODE = Path("/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
BRIDGE = ROOT / "scripts" / "materials_gcts_ice_vi_microstate_crop.mjs"
REPEATS = (6, 6, 6)
TRAIN_CENTER = (.18, .18, .20)
EVAL_CENTER = (.72, .72, .80)
TRAIN_RADIUS = 9.0
SEED_RADIUS = 5.0
TARGET_RADIUS = 9.0
TRAIN_SEED = 11
CALIBRATION_SEEDS = (3, 7, 13)
EVAL_SEED = 29


def _crop(seed: int, center: Sequence[float], radius: float) -> dict:
    request = {"seed": seed, "repeats": REPEATS,
               "centerFraction": tuple(center), "radius": radius}
    result = subprocess.run(
        (str(NODE), str(BRIDGE), json.dumps(request, separators=(",", ":"))),
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def _site_digest(sites) -> str:
    payload = sorted((species, *(round(value / .01) for value in point))
                     for species, point in sites)
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def _correct_anchor(candidate, targets, tolerance=.08) -> bool:
    return any(species == candidate.anchor[0]
               and math.dist(candidate.anchor[1], point) <= tolerance
               for species, point in targets)


class _SingleUseTarget:
    def __init__(self):
        self.opens = 0

    def open(self):
        if self.opens:
            raise RuntimeError("held-out Ice VI target may be opened only once")
        self.opens += 1
        return _crop(EVAL_SEED, EVAL_CENTER, TARGET_RADIUS)


@dataclass(frozen=True)
class IceViCrossMicrostateReport:
    training_molecules: int
    conformer_types: int
    frozen_ports: int
    directed_type_pairs: int
    calibration_candidates: int
    calibration_selected: int
    calibration_correct: int
    calibration_wrong: int
    calibration_precision: float
    selected_parent_witness_threshold: int
    train_eval_center_separation: float
    required_separation: float
    raw_molecule_id_overlap: int
    seed_molecules: int
    seed_recognized_molecules: int
    seed_conformer_types: tuple[int, ...]
    anchor_wave_candidates: tuple[int, ...]
    anchor_wave_accepted: tuple[int, ...]
    anchor_emitted: int
    anchor_correct: int
    anchor_wrong: int
    anchor_novel_recall: float
    unresolved_anchor_orientations: int
    resolved_anchor_orientations: int
    whole_molecule_wave_accepted: tuple[int, ...]
    whole_molecule_emitted_sites: int
    whole_molecule_correct_sites: int
    whole_molecule_wrong_sites: int
    whole_molecule_site_precision: float
    heldout_target_molecules: int
    heldout_target_open_count: int
    trace_digest: str
    grammar_material_label_used: bool
    grammar_expected_formula_used: bool
    lattice_site_indices_used: bool
    energy_or_potential_used: bool
    target_used_before_scoring: bool
    oxygen_anchor_gate_passed: bool
    occupational_orientation_gate_passed: bool
    stationary_or_exponential_claim: bool


def evaluate() -> IceViCrossMicrostateReport:
    training = _crop(TRAIN_SEED, TRAIN_CENTER, TRAIN_RADIUS)
    grammar = fit_molecular_conformer_grammar(
        training["species"], training["positions"],
        pose_tolerance=.04, minimum_port_observations=2)
    audit = grammar_audit(grammar)

    calibration_rows = []
    for seed in CALIBRATION_SEEDS:
        seed_crop = _crop(seed, TRAIN_CENTER, SEED_RADIUS)
        _, occurrences, _ = recognize_seed_conformers(
            grammar, seed_crop["species"], seed_crop["positions"])
        trace = execute_molecular_conformer_anchor_growth(
            grammar, occurrences,
            boundary_center=tuple(seed_crop["center"]),
            boundary_radius=TARGET_RADIUS, maximum_waves=1)
        target_crop = _crop(seed, TRAIN_CENTER, TARGET_RADIUS)
        target_anchors = tuple((species, tuple(position))
                               for species, position in target_crop["sites"]
                               if species == "O")
        calibration_rows.extend((candidate.parent_witnesses,
                                 _correct_anchor(candidate, target_anchors))
                                for candidate in trace.waves[0].eligible_candidates)
    choices = []
    for threshold in (1, 2, 3, 4):
        labels = [correct for witnesses, correct in calibration_rows
                  if witnesses >= threshold]
        correct = sum(labels)
        wrong = len(labels) - correct
        precision = correct / len(labels) if labels else 0.0
        if labels and precision >= .95:
            choices.append((correct, -threshold, threshold, len(labels), wrong, precision))
    if not choices:
        raise AssertionError("training-side Ice VI consensus has no >=95% precision gate")
    _, _, witness_threshold, calibration_selected, calibration_wrong, calibration_precision = max(choices)
    calibration_correct = calibration_selected - calibration_wrong

    seed_crop = _crop(EVAL_SEED, EVAL_CENTER, SEED_RADIUS)
    _, seed_occurrences, seed_sites = recognize_seed_conformers(
        grammar, seed_crop["species"], seed_crop["positions"])
    target_factory = _SingleUseTarget()
    anchor_trace = execute_molecular_conformer_anchor_growth(
        grammar, seed_occurrences,
        boundary_center=tuple(seed_crop["center"]),
        boundary_radius=TARGET_RADIUS, maximum_waves=8,
        minimum_parent_witnesses=witness_threshold)
    molecule_trace = execute_molecular_conformer_growth(
        grammar, seed_occurrences, seed_sites,
        boundary_center=tuple(seed_crop["center"]),
        boundary_radius=TARGET_RADIUS, maximum_waves=3,
        maximum_accepted_per_wave=40,
        minimum_witnesses=witness_threshold)
    frozen_trace_payload = {
        "anchorCandidateDigests": [wave.candidate_digest for wave in anchor_trace.waves],
        "anchorEmissions": _site_digest(anchor_trace.emitted_anchors),
        "moleculeCandidateDigests": [wave.candidate_digest for wave in molecule_trace.waves],
        "moleculeEmissions": _site_digest(molecule_trace.emitted_sites),
    }
    trace_digest = hashlib.sha256(json.dumps(
        frozen_trace_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if target_factory.opens or anchor_trace.target_used or molecule_trace.target_used:
        raise AssertionError("held-out target was used before trace freeze")

    heldout = target_factory.open()
    target_sites = tuple((species, tuple(position))
                         for species, position in heldout["sites"])
    target_anchors = tuple(site for site in target_sites if site[0] == "O")
    anchor_correct, anchor_wrong, _ = score_sites(
        anchor_trace.emitted_anchors, target_anchors, tolerance=.08)
    molecule_correct, molecule_wrong, _ = score_sites(
        molecule_trace.emitted_sites, target_sites, tolerance=.08)
    novel_anchor_count = heldout["molecules"] - seed_crop["molecules"]
    center_separation = math.dist(training["center"], heldout["center"])
    raw_overlap = len(set(training["moleculeIds"]) & set(heldout["moleculeIds"]))
    anchor_precision = anchor_correct / max(1, anchor_correct + anchor_wrong)
    molecule_precision = molecule_correct / max(1, molecule_correct + molecule_wrong)
    anchor_gate = (anchor_correct > 0 and anchor_wrong == 0
                   and anchor_precision == 1.0
                   and sum(wave.accepted_anchors > 0 for wave in anchor_trace.waves) >= 2
                   and witness_threshold > 1)
    orientation_gate = (molecule_wrong == 0
                        and anchor_trace.unresolved_new_molecules == 0)
    return IceViCrossMicrostateReport(
        training_molecules=audit["training_molecules"],
        conformer_types=audit["conformer_types"],
        frozen_ports=audit["ports"],
        directed_type_pairs=audit["directed_type_pairs"],
        calibration_candidates=len(calibration_rows),
        calibration_selected=calibration_selected,
        calibration_correct=calibration_correct,
        calibration_wrong=calibration_wrong,
        calibration_precision=calibration_precision,
        selected_parent_witness_threshold=witness_threshold,
        train_eval_center_separation=center_separation,
        required_separation=2 * TARGET_RADIUS,
        raw_molecule_id_overlap=raw_overlap,
        seed_molecules=seed_crop["molecules"],
        seed_recognized_molecules=len(seed_occurrences),
        seed_conformer_types=tuple(sorted({item.type_id for item in seed_occurrences})),
        anchor_wave_candidates=tuple(wave.candidate_anchors for wave in anchor_trace.waves),
        anchor_wave_accepted=tuple(wave.accepted_anchors for wave in anchor_trace.waves),
        anchor_emitted=len(anchor_trace.emitted_anchors),
        anchor_correct=anchor_correct, anchor_wrong=anchor_wrong,
        anchor_novel_recall=anchor_correct / novel_anchor_count,
        unresolved_anchor_orientations=anchor_trace.unresolved_new_molecules,
        resolved_anchor_orientations=anchor_trace.resolved_new_molecules,
        whole_molecule_wave_accepted=tuple(wave.accepted for wave in molecule_trace.waves),
        whole_molecule_emitted_sites=len(molecule_trace.emitted_sites),
        whole_molecule_correct_sites=molecule_correct,
        whole_molecule_wrong_sites=molecule_wrong,
        whole_molecule_site_precision=molecule_precision,
        heldout_target_molecules=heldout["molecules"],
        heldout_target_open_count=target_factory.opens,
        trace_digest=trace_digest,
        grammar_material_label_used=audit["material_label_used"],
        grammar_expected_formula_used=audit["expected_formula_used"],
        lattice_site_indices_used=False,
        energy_or_potential_used=False,
        target_used_before_scoring=False,
        oxygen_anchor_gate_passed=anchor_gate,
        occupational_orientation_gate_passed=orientation_gate,
        stationary_or_exponential_claim=False,
    )


if __name__ == "__main__":
    print(json.dumps(asdict(evaluate()), indent=2, sort_keys=True))
