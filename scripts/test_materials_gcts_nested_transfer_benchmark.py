#!/usr/bin/env python3
"""Contract tests for the generic nested-crop transfer scorer."""

from __future__ import annotations

from dataclasses import dataclass

from materials_gcts_generic import AtomicConfiguration
from materials_gcts_nested_transfer_benchmark import (
    FittedProgram, GrowthTrace, NestedCropSplit, ProgramAudit,
    TransferThresholds, evaluate_nested_transfer, validate_nested_crops)


@dataclass(frozen=True)
class _Program:
    spacing: float
    even_species: str
    odd_species: str


def _configuration(name, count):
    positions = tuple((float(index), 0.0, 0.0) for index in range(count))
    species = tuple("Cd" if index % 2 else "Yb" for index in range(count))
    return AtomicConfiguration(name, positions, species, provenance="fixture")


def _split():
    return NestedCropSplit(
        _configuration("inner", 3), _configuration("middle", 6),
        _configuration("outer", 10), (0.0, 0.0, 0.0),
        (2.1, 5.1, 9.1), "a" * 64)


def _fit(seed):
    spacing = seed.positions[1][0] - seed.positions[0][0]
    program = _Program(spacing, seed.species[0], seed.species[1])
    return FittedProgram(program, ProgramAudit(
        len(seed.positions), len(seed.positions), 2, 0, 8, 3,
        True, False, False))


def _grow(program, seed, origin, radius, marked):
    assert seed.name == "inner"
    assert radius == 9.1
    count = int(radius / program.spacing) + 1
    sites = frozenset(
        (((index * program.spacing, 0.0, 0.0)),
         program.even_species if index % 2 == 0 else program.odd_species)
        for index in range(count))
    return GrowthTrace(sites, 10 if marked else 100, 7,
                       3 if marked else 93, 3)


def _serialize(program):
    return repr(program).encode()


def test_green_contract():
    report = evaluate_nested_transfer(
        _split(), _fit, _grow, _serialize,
        TransferThresholds(matching_tolerance=0.0))
    assert report.benchmark_passed
    assert report.validation.colored_recall == 1.0
    assert report.test.colored_recall == 1.0
    assert report.marking_proposal_reduction == 10.0
    assert report.marking_failed_proposal_reduction == 31.0


def test_rejects_non_nested_fixture():
    split = _split()
    bad = NestedCropSplit(split.training, split.training, split.test,
                          split.origin, split.radii, split.fixture_sha256)
    try:
        validate_nested_crops(bad)
    except ValueError as error:
        assert "strict cumulative" in str(error)
    else:
        raise AssertionError("non-nested fixture was accepted")


def test_family_label_and_weak_ablation_stay_red():
    def bad_fit(seed):
        fitted = _fit(seed)
        audit = ProgramAudit(
            fitted.audit.fitted_atoms, fitted.audit.covered_training_sites,
            fitted.audit.cluster_types, fitted.audit.gap_cluster_types,
            fitted.audit.marking_states, fitted.audit.hierarchy_depth,
            True, True, False)
        return FittedProgram(fitted.program, audit)

    def weak_grow(program, seed, origin, radius, marked):
        trace = _grow(program, seed, origin, radius, marked)
        return GrowthTrace(trace.emitted_sites, 10, 7, 3, 3)

    report = evaluate_nested_transfer(
        _split(), bad_fit, weak_grow, _serialize,
        TransferThresholds(matching_tolerance=0.0))
    assert not report.provenance_gate_passed
    assert not report.marking_ablation_gate_passed
    assert not report.benchmark_passed


if __name__ == "__main__":
    test_green_contract()
    test_rejects_non_nested_fixture()
    test_family_label_and_weak_ablation_stay_red()
    print("nested transfer benchmark contract passed")
