#!/usr/bin/env python3
"""Contracts and negative controls for finite-state cycle recurrence."""

from dataclasses import replace

from materials_gcts_finite_state_cycle_recurrence import (
    CycleObservation, audit_finite_state_cycles)
from materials_gcts_oriented_overlap_ports import IDENTITY
from materials_gcts_stationary_production_signature import (
    PortGraphProduction, ProductionChild, ProductionPort)


def _production(state, level, chemistry=("A", "B", "C")):
    scale = 2.0 ** level
    population_scale = 2 ** level
    points = ((0., 0., 0.), (scale, 0., 0.), (0., scale, 0.))
    children = tuple(ProductionChild(
        (label,), "achiral", IDENTITY, point, (IDENTITY,),
        ((label, population_scale),))
                     for label, point in zip(chemistry, points))
    port_family = ("state-A",) if state == "A" else ("state-B",)
    ports = tuple(ProductionPort(left, right, port_family, (chemistry[left],))
                  for left, right in ((0, 1), (1, 2), (2, 0)))
    return PortGraphProduction(children, ports)


def _records(split, states, independently_observed=True):
    result = []
    for level, state in enumerate(states):
        offset = 10000 if split != "train" else 0
        result.append(CycleObservation(
            level, f"{split}-L{level}-{state}", _production(state, level),
            (frozenset((offset + level * 20 + index for index in range(6))),
             frozenset((offset + level * 20 + 10 + index
                        for index in range(6)))),
            5, split, split == "train", independently_observed))
    return tuple(result)


def test_two_state_cycle_needs_two_train_and_heldout_traversals():
    states = ("A", "B", "A", "B", "A")
    result = audit_finite_state_cycles(
        _records("train", states) + _records("heldout", states))
    assert result.recurrent
    assert result.witnesses[0].period == 2
    assert result.witnesses[0].state_keys[0] != \
        result.witnesses[0].state_keys[1]
    assert result.witnesses[0].transition_scales == (2.0, 2.0)
    assert result.witnesses[0].cycle_scale == 4.0
    assert not result.stationary_gate_weakened


def test_short_prefix_shuffled_state_and_frozen_scale_controls_are_red():
    short = audit_finite_state_cycles(
        _records("train", ("A", "B", "A", "B")) +
        _records("heldout", ("A", "B", "A", "B", "A")))
    assert not short.recurrent and short.train_cycle_candidates == 0
    shuffled = audit_finite_state_cycles(
        _records("train", ("A", "B", "B", "A", "A")) +
        _records("heldout", ("A", "B", "A", "B", "A")))
    assert not shuffled.recurrent
    frozen = audit_finite_state_cycles(
        _records("train", ("A", "B", "A", "B", "A")) +
        _records("heldout", ("A", "B", "A", "B", "A"), False))
    assert not frozen.recurrent
    assert "not independently observed" in frozen.reason
    chemistry = list(_records("train", ("A", "B", "A", "B", "A")))
    chemistry[2] = replace(
        chemistry[2], production=_production(
            "A", 2, chemistry=("A", "B", "X")))
    chemistry_control = audit_finite_state_cycles(
        tuple(chemistry) +
        _records("heldout", ("A", "B", "A", "B", "A")))
    assert not chemistry_control.recurrent
    population = list(_records("train", ("A", "B", "A", "B", "A")))
    production = population[2].production
    changed_child = replace(
        production.children[0], chemical_population=(("A", 5),))
    population[2] = replace(population[2], production=replace(
        production, children=(changed_child,) + production.children[1:]))
    population_control = audit_finite_state_cycles(
        tuple(population) +
        _records("heldout", ("A", "B", "A", "B", "A")))
    assert not population_control.recurrent


if __name__ == "__main__":
    test_two_state_cycle_needs_two_train_and_heldout_traversals()
    test_short_prefix_shuffled_state_and_frozen_scale_controls_are_red()
    print("finite-state cycle recurrence: all assertions passed")
