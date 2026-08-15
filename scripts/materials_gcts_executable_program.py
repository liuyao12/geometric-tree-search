#!/usr/bin/env python3
"""One family-blind discovery and execution API for recursive material growth."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from materials_gcts_generic import AtomicConfiguration
from materials_gcts_geometry_vm import compile_metric_overlap_from_seed
from materials_gcts_propagated_marking import (
    MarkedConfiguration, compile_propagated_port_program,
    execute_propagated_wave,
    extend_marked_configuration, fit_propagated_marking,
    initial_marked_configuration, promote_port_instruction)
from materials_gcts_recursive_program import (
    RecursiveProgram, discover_recursive_program, explicit_apply)


@dataclass(frozen=True)
class ExecutableGrowthProgram:
    production_kind: str
    deterministic: bool
    family_label_used: bool
    heldout_atoms_used: bool
    physical_potential_used: bool
    _base: RecursiveProgram = field(repr=False, compare=False)
    _instruction: Any = field(default=None, repr=False, compare=False)
    _marking: Any = field(default=None, repr=False, compare=False)


def discover_executable_program(
        seed: AtomicConfiguration) -> ExecutableGrowthProgram:
    """Select and fully compile a growth program from positions/species only."""
    base = discover_recursive_program(seed)
    if not base.deterministic:
        return ExecutableGrowthProgram(
            "none", False, False, False, False, base)
    if base.family == "internal_section_inflation":
        instruction = compile_metric_overlap_from_seed(seed)
        marking = fit_propagated_marking(instruction, seed)
        return ExecutableGrowthProgram(
            "marked_port_promotion", True, False, False, False, base,
            instruction, marking)
    return ExecutableGrowthProgram(
        base.family, True, False, False, False, base)


def _prepare_promoted_parent(
        seed: AtomicConfiguration,
        program: ExecutableGrowthProgram) -> tuple[MarkedConfiguration, Any]:
    state = initial_marked_configuration(seed, program._marking)
    port_program = compile_propagated_port_program(program._instruction)
    # Exhaust every seed-trained port scale before promoting. This is a
    # family-independent stopping rule: promotion occurs only after no local
    # production remains, rather than at a target atom count or radius.
    for level in range(1, 25):
        generated_at_level = False
        for _ in range(25):
            wave = execute_propagated_wave(
                port_program, program._marking, state, level=level)
            if not wave.emitted_sites:
                break
            generated_at_level = True
            state = extend_marked_configuration(state, wave)
        if level > 1 and not generated_at_level:
            break
    promoted, _ = promote_port_instruction(program._instruction, state)
    return state, compile_propagated_port_program(promoted)


def execute_program(
        seed: AtomicConfiguration,
        program: ExecutableGrowthProgram,
        actions: int) -> tuple[AtomicConfiguration, ...]:
    """Return every explicitly materialized state after a recursive action."""
    if actions < 0:
        raise ValueError("actions must be nonnegative")
    if not program.deterministic:
        raise ValueError("cannot execute a rejected growth program")
    if actions == 0:
        return ()
    if program.production_kind != "marked_port_promotion":
        return tuple(explicit_apply(seed, program._base, action)
                     for action in range(1, actions + 1))
    state, promoted = _prepare_promoted_parent(seed, program)
    states = []
    for level in range(1, actions + 1):
        wave = execute_propagated_wave(
            promoted, program._marking, state, level=level)
        if not wave.emitted_sites:
            break
        state = extend_marked_configuration(state, wave)
        states.append(state.configuration)
    return tuple(states)
