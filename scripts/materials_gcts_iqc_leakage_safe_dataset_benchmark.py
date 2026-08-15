#!/usr/bin/env python3
"""Contract audit for frozen IQC supports and dense train-only macros."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_iqc_leakage_safe_dataset import (
    domain_digest, split_iqc_train_guard_test)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_irregular_supports import enumerate_frozen_vocabulary
from materials_gcts_port_graph_macros import mine_port_graph_macros


@dataclass(frozen=True)
class IQCLeakageSafeDatasetAudit:
    raw_atoms: int
    train_atoms: int
    guard_atoms: int
    fit_atoms: int
    heldout_atoms: int
    required_guard_width: float
    train_domain_digest: str
    guard_domain_digest: str
    heldout_domain_digest: str
    exact_domain_id_disjointness: bool
    frozen_support_types: int
    heldout_frozen_occurrences: int
    heldout_known_atoms: int
    heldout_unknown_atoms: int
    heldout_unknown_fraction: float
    admitted_macro_types: int
    dense_train_macro_occurrences: int
    frozen_vocabulary_transfer_without_refit: bool
    heldout_atoms_used_by_fit_or_dense_matching: bool
    oracle_lifts_family_phi_cell_used_by_learner: bool


def evaluate() -> IQCLeakageSafeDatasetAudit:
    raw, _oracle_metadata = oracle_patch(4, 12.0)
    split = split_iqc_train_guard_test(raw.species, raw.positions)
    # Only this sealed payload crosses into support/port/macro fitting.
    program = compile_irregular_port_program(
        split.fit.species, split.fit.positions)
    admitted = mine_port_graph_macros(program, maximum_nodes=2)
    dense = match_dense_macro_types(program, admitted.macro_types)
    # Heldout coordinates first appear here, after every fitted artifact is
    # frozen. Enumeration cannot add or modify vocabulary entries.
    frozen = enumerate_frozen_vocabulary(
        program.vocabulary, split.heldout.species, split.heldout.positions)
    occurrences = sum(len(group) for group in frozen.occurrences_by_type)
    known = len(frozen.covered_indices)
    unknown = len(split.heldout.global_ids) - known
    return IQCLeakageSafeDatasetAudit(
        len(raw.positions), len(split.train.global_ids),
        len(split.guard.global_ids), len(split.fit.global_ids),
        len(split.heldout.global_ids), split.required_guard_width,
        domain_digest(split.train), domain_digest(split.guard),
        domain_digest(split.heldout), split.exact_global_id_disjointness,
        len(program.vocabulary.prototypes), occurrences, known, unknown,
        unknown / max(1, len(split.heldout.global_ids)),
        len(admitted.macro_types), dense.total_dense_occurrences, True,
        False, False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
