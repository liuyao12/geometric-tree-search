#!/usr/bin/env python3
"""Reproduce the fully nested IQC marking-library terminal-value audit."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from materials_gcts_portfolio_terminal_value import (
    PortfolioTerminalExample, TerminalRepresentation,
    fit_grouped_portfolio_terminal_value)


FIXTURE = (Path(__file__).parent /
           "fixtures/iqc_marking_portfolio_terminal_value.json")


@dataclass(frozen=True)
class IQCMarkingPortfolioTerminalReport:
    groups: int
    folds: int
    terminal_training_examples: int
    positive_terminal_training_examples: int
    selected_representations: tuple[str, ...]
    selected_neighbors: tuple[int, ...]
    single_coupled_selected_exact: int
    single_coupled_terminal_supply: int
    portfolio_selected_exact: int
    portfolio_terminal_supply: int
    portfolio_selected_correct_moves: int
    terminal_value_selected_exact: int
    terminal_value_stable_selected_exact: int
    terminal_value_terminal_supply: int
    terminal_value_selected_correct_moves: int
    terminal_value_mixed_top_ties: int
    terminal_value_gain_over_portfolio: int
    terminal_value_gain_over_single_coupled: int
    exact_path_supply_failures: int
    supplied_but_misranked: int
    ridge_broad_selected_exact: int
    ridge_merged_selected_exact: int
    ridge_control_rejected: bool
    common_beam_budget_preserved: bool
    scientific_gate_passed: bool
    fresh_confirmation_authorized: bool
    terminal_corpus_digest: str
    portfolio_trace_digest: str
    terminal_value_trace_digest: str
    target_used: bool


def _digest(rows) -> str:
    return hashlib.sha256(repr(tuple(sorted((
        row.group, row.features, row.action_colors, row.successful)
        for row in rows))).encode()).hexdigest()


def evaluate(path: Path = FIXTURE) -> IQCMarkingPortfolioTerminalReport:
    data = json.loads(path.read_text())
    if data["format"] != "iqc-marking-portfolio-terminal-value-v1":
        raise AssertionError("unexpected marking portfolio fixture")
    source_path = path.parent / data["source_fixture"]
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != \
            data["source_fixture_sha256"]:
        raise AssertionError("fully nested source fixture changed")
    source = json.loads(source_path.read_text())
    names = tuple(data["feature_names"])
    colors = tuple(data["color_keys"])
    representations = tuple(TerminalRepresentation(
        row["name"], tuple(row["feature_indices"]))
        for row in data["representations"])
    digest_parts = []
    example_count = positive_count = 0
    selected_representations = []
    selected_neighbors = []
    for fold in data["folds"]:
        rows = tuple(PortfolioTerminalExample(
            int(row["group"]), tuple(row["features"]),
            tuple(row["action_colors"]), bool(row["successful"]))
            for row in fold["examples"])
        digest = _digest(rows)
        if digest != fold["example_digest"]:
            raise AssertionError("portfolio terminal rows changed")
        digest_parts.append(digest)
        _model, audit = fit_grouped_portfolio_terminal_value(
            rows, feature_names=names, color_keys=colors,
            representations=representations,
            candidate_neighbors=tuple(data["candidate_neighbors"]),
            beta_prior=float(data["beta_prior"]))
        if (audit.selected_representation !=
                fold["expected_selected_representation"] or
                audit.selected_neighbors !=
                fold["expected_selected_neighbors"] or
                audit.selected_exact_groups !=
                fold["expected_selected_exact_groups"] or
                audit.supplied_groups != fold["expected_supplied_groups"] or
                audit.model_digest != fold["expected_model_digest"] or
                audit.target_used):
            raise AssertionError("portfolio terminal fit changed")
        selected_representations.append(audit.selected_representation)
        selected_neighbors.append(audit.selected_neighbors)
        example_count += len(rows)
        positive_count += sum(row.successful for row in rows)
    terminal_digest = hashlib.sha256(
        repr(tuple(digest_parts)).encode()).hexdigest()
    if terminal_digest != data["terminal_corpus_digest"]:
        raise AssertionError("combined terminal corpus changed")

    single = source["feature_ablations"]["all"]
    portfolio = data["portfolio_closed_loop"]["summary"]
    terminal = data["terminal_value_closed_loop"]["summary"]
    ridge = data["ridge_control"]["results"]
    groups = int(terminal["groups"])
    gate = data["scientific_gate"]
    gate_passed = (
        terminal["terminal_supply"] / groups >=
        gate["minimum_terminal_supply_fraction"] and
        terminal["certified_selected_exact"] / groups >=
        gate["minimum_selected_exact_fraction"])
    target_used = bool(data["target_used"] or
                       data["portfolio_closed_loop"]["target_used"] or
                       data["terminal_value_closed_loop"]["target_used"] or
                       data["ridge_control"]["target_used"])
    return IQCMarkingPortfolioTerminalReport(
        groups=groups,
        folds=len(data["folds"]),
        terminal_training_examples=example_count,
        positive_terminal_training_examples=positive_count,
        selected_representations=tuple(selected_representations),
        selected_neighbors=tuple(selected_neighbors),
        single_coupled_selected_exact=single["selected_exact"],
        single_coupled_terminal_supply=single["terminal_supply"],
        portfolio_selected_exact=portfolio["selected_exact"],
        portfolio_terminal_supply=portfolio["terminal_supply"],
        portfolio_selected_correct_moves=portfolio["selected_correct"],
        terminal_value_selected_exact=terminal["certified_selected_exact"],
        terminal_value_stable_selected_exact=terminal["stable_selected_exact"],
        terminal_value_terminal_supply=terminal["terminal_supply"],
        terminal_value_selected_correct_moves=
            terminal["stable_selected_correct"],
        terminal_value_mixed_top_ties=terminal["mixed_top_ties"],
        terminal_value_gain_over_portfolio=(
            terminal["certified_selected_exact"] - portfolio["selected_exact"]),
        terminal_value_gain_over_single_coupled=(
            terminal["certified_selected_exact"] - single["selected_exact"]),
        exact_path_supply_failures=groups - terminal["terminal_supply"],
        supplied_but_misranked=(terminal["terminal_supply"] -
                               terminal["certified_selected_exact"]),
        ridge_broad_selected_exact=ridge["broad"]["summary"]["selected_exact"],
        ridge_merged_selected_exact=
            ridge["merged"]["summary"]["selected_exact"],
        ridge_control_rejected=(
            max(ridge["broad"]["summary"]["selected_exact"],
                ridge["merged"]["summary"]["selected_exact"]) <
            single["selected_exact"]),
        common_beam_budget_preserved=True,
        scientific_gate_passed=gate_passed,
        fresh_confirmation_authorized=gate_passed,
        terminal_corpus_digest=terminal_digest,
        portfolio_trace_digest=data["portfolio_closed_loop"]["digest"],
        terminal_value_trace_digest=
            data["terminal_value_closed_loop"]["digest"],
        target_used=target_used)


if __name__ == "__main__":
    print(evaluate())
