#!/usr/bin/env python3
"""Audit rejected pruning changes around the fixed-width IQC portfolio."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures/iqc_marking_pruning_controls.json"


@dataclass(frozen=True)
class IQCMarkingPruningControlReport:
    groups: int
    beam: tuple[int, ...]
    baseline_selected_exact: int
    baseline_terminal_supply: int
    reach12_root_supply: int
    reach12_terminal_supply: int
    reach12_selected_exact: int
    stage_value_selected_exact: int
    stage_value_terminal_supply: int
    descendant_viability_selected_exact: int
    descendant_viability_terminal_supply: int
    controls_improve_baseline: bool
    development_gate_passed: bool
    fresh_confirmation_authorized: bool
    target_used: bool


def evaluate(path: Path = FIXTURE) -> IQCMarkingPruningControlReport:
    data = json.loads(path.read_text())
    if data["format"] != "iqc-marking-pruning-controls-v1":
        raise AssertionError("unexpected pruning-control fixture")
    source = path.parent / data["source_fixture"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != \
            data["source_fixture_sha256"]:
        raise AssertionError("portfolio terminal source changed")
    groups = int(data["groups"])
    baseline = data["portfolio_terminal_baseline"]
    reach = data["root_reach_control"]["results"]["12"]
    stage = data["independent_stage_value_control"]["summary"]
    viability = data["descendant_viability_control"]["summary"]
    if (tuple(data["beam"]) != (4, 4, 8) or groups != 20 or
            any(len(row) != 3 for row in
                data["independent_stage_value_control"]["selected_heads"]) or
            any(len(row) != 3 for row in
                data["descendant_viability_control"]["selected_heads"])):
        raise AssertionError("pruning-control protocol changed")
    target_used = any((
        data["target_used"], data["root_reach_control"]["target_used"],
        data["independent_stage_value_control"]["target_used"],
        data["descendant_viability_control"]["target_used"]))
    controls_improve = max(
        reach["selected_exact"], stage["selected_exact"],
        viability["selected_exact"]) > baseline["selected_exact"]
    gate = int(data["development_gate"]["minimum_selected_exact"])
    passed = max(baseline["selected_exact"], reach["selected_exact"],
                 stage["selected_exact"],
                 viability["selected_exact"]) >= gate
    return IQCMarkingPruningControlReport(
        groups, tuple(data["beam"]), baseline["selected_exact"],
        baseline["terminal_supply"], reach["stage_supply"][0],
        reach["terminal_supply"], reach["selected_exact"],
        stage["selected_exact"], stage["terminal_supply"],
        viability["selected_exact"], viability["terminal_supply"],
        controls_improve, passed, passed and not target_used, target_used)


if __name__ == "__main__":
    print(evaluate())
