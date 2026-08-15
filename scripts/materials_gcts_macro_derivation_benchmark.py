#!/usr/bin/env python3
"""Sealed cross-family gate for self-fed promoted-macro execution."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from materials_gcts_cdyb_transfer_benchmark import build_cdyb_split
from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_derivation import (
    execute_macro_derivation, score_macro_derivation)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_periodic_growth import replicate
from materials_gcts_port_graph_macros import mine_port_graph_macros


@dataclass(frozen=True)
class MacroDerivationCase:
    system: str
    training_atoms: int
    target_atoms: int
    learned_macro_types: int
    frozen_macro_productions: int
    seed_macro_atoms: int
    level_emitted_nodes: tuple[int, ...]
    level_emitted_atoms: tuple[int, ...]
    represented_atom_counts: tuple[int, ...]
    attempted_candidates: int
    accepted_steps: int
    certificates_valid: bool
    symbolic_count: int
    explicit_count: int
    independent_count_verified: bool
    stationary_contract_available: bool
    proposed_novel_atoms: int
    correct_novel_atoms: int
    precision: float
    heldout_recall: float
    target_used_during_derivation: bool
    growth_gate_passed: bool


@dataclass(frozen=True)
class MacroDerivationBenchmark:
    cases: tuple[MacroDerivationCase, ...]
    all_targets_sealed: bool
    all_overlap_certificates_valid: bool
    any_real_growth_gate_passed: bool


def _case(training: AtomicConfiguration,
          target: AtomicConfiguration) -> MacroDerivationCase:
    atomic = compile_irregular_port_program(
        training.species, training.positions)
    mined = mine_port_graph_macros(atomic, maximum_nodes=2)
    promoted = promote_macro_types(atomic, mined.macro_types)
    if not promoted.occurrences or not promoted.atlas.ports:
        raise ValueError("promoted level has no executable overlap production")
    derivation = execute_macro_derivation(
        promoted, promoted.occurrences,
        explicit_seed_sites=tuple(zip(training.species, training.positions)),
        maximum_levels=2)
    score = score_macro_derivation(
        derivation, target.species, target.positions)
    certificates = all(
        step.certificate.overlap_is_subset and
        step.certificate.emitted_is_exact_difference and
        step.certificate.adjacency_witnessed_in_training and
        step.certificate.conflicting_sites == 0
        for step in derivation.steps)
    passed = (score.proposed_novel_atoms > 0 and score.precision >= .99 and
              derivation.independent_count_verified and certificates and
              not score.target_used_during_derivation)
    return MacroDerivationCase(
        training.name, len(training.positions), len(target.positions),
        len(mined.macro_types), len(derivation.productions),
        len(derivation.seed_sites),
        tuple(level.emitted_nodes for level in derivation.explicit_levels),
        tuple(level.emitted_atoms for level in derivation.explicit_levels),
        (len(derivation.seed_sites),) + tuple(
            level.atoms_after for level in derivation.explicit_levels),
        derivation.attempted_candidates, len(derivation.steps), certificates,
        derivation.symbolic_atom_count, derivation.explicit_atom_count,
        derivation.independent_count_verified,
        derivation.stationary_normalized_key is not None,
        score.proposed_novel_atoms, score.correct_novel_atoms,
        score.precision, score.heldout_recall,
        score.target_used_during_derivation, passed)


def evaluate() -> MacroDerivationBenchmark:
    nacl_source = next(item for item in benchmark_systems()
                       if item.name == "NaCl-rocksalt")
    nacl_target = replicate(nacl_source)
    nacl = AtomicConfiguration(
        nacl_source.name, nacl_source.positions, nacl_source.species)
    iqc, _ = oracle_patch(3, 9.0)
    iqc_target, _ = oracle_patch(4, 15.0)
    cdyb = build_cdyb_split()
    cases = tuple(_case(training, target) for training, target in (
        (nacl, nacl_target), (iqc, iqc_target),
        (cdyb.training, cdyb.validation)))
    return MacroDerivationBenchmark(
        cases,
        all(not case.target_used_during_derivation for case in cases),
        all(case.certificates_valid for case in cases),
        any(case.growth_gate_passed for case in cases))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
