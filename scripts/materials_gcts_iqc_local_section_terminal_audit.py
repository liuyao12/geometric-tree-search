#!/usr/bin/env python3
"""Audit the bounded local-section value on fixed IQC portfolio terminals."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures/iqc_local_section_terminal_value.json"


@dataclass(frozen=True)
class IQCLocalSectionTerminalAudit:
    groups: int
    features: int
    terminal_supply: int
    baseline_selected_exact: int
    selected_exact: int
    selected_correct: int
    gain_over_baseline: int
    joint_support_selected_exact: int
    closure_selected_folds: int
    chiral_features: int
    chirality_selected_folds: int
    chiral_selected_exact: int
    chiral_selected_correct: int
    proper_se3_invariant: bool
    lattice_coordinates_used: bool
    chirality_preserved: bool
    development_gate_passed: bool
    fresh_confirmation_authorized: bool
    target_used: bool


def evaluate(path: Path = FIXTURE) -> IQCLocalSectionTerminalAudit:
    data = json.loads(path.read_text())
    if data["format"] != "iqc-local-section-terminal-value-v1":
        raise AssertionError("unexpected local-section fixture")
    source = path.parent / data["source_fixture"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != \
            data["source_fixture_sha256"]:
        raise AssertionError("terminal-value source changed")
    schema = data["schema"]
    chiral = data["explicit_chirality_control"]
    if (data["groups"] != 20 or data["terminal_supply"] != 18
            or len(data["selected_representations"]) != 5
            or len(data["selected_neighbors"]) != 5
            or schema["features"] != 180
            or data["mixed_top_ties"] != 0):
        raise AssertionError("local-section protocol changed")
    target_used = bool(data["target_used_before_selection"])
    gate = data["selected_exact"] >= \
        data["development_gate"]["minimum_selected_exact"]
    return IQCLocalSectionTerminalAudit(
        data["groups"], schema["features"], data["terminal_supply"],
        data["baseline_selected_exact"], data["selected_exact"],
        data["selected_correct"],
        data["selected_exact"] - data["baseline_selected_exact"],
        data["joint_support_control"]["selected_exact"],
        data["prototype_closure_selected_folds"],
        chiral["features"], chiral["chirality_selected_folds"],
        chiral["selected_exact"], chiral["selected_correct"],
        schema["proper_se3_invariant"],
        schema["lattice_coordinates_used"], schema["chirality_preserved"],
        gate, gate and not target_used and
        not data["fresh_confirmation_opened"], target_used)


if __name__ == "__main__":
    print(evaluate())
