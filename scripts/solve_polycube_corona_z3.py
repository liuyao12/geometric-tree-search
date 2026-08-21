#!/usr/bin/env python3

import argparse
import itertools
import json
import time
from pathlib import Path

import z3


DIRECTIONS = (
    (1, 0, 0), (-1, 0, 0),
    (0, 1, 0), (0, -1, 0),
    (0, 0, 1), (0, 0, -1),
)


def determinant(matrix):
    return (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )


def proper_rotations():
    rotations = []
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1, 1), repeat=3):
            matrix = [[0, 0, 0] for _ in range(3)]
            for row in range(3):
                matrix[row][permutation[row]] = signs[row]
            if determinant(matrix) == 1:
                rotations.append(matrix)
    return rotations


def transform(cell, matrix):
    return tuple(sum(matrix[row][axis] * cell[axis] for axis in range(3)) for row in range(3))


def normalize(cells):
    minimum = tuple(min(cell[axis] for cell in cells) for axis in range(3))
    return tuple(sorted(tuple(cell[axis] - minimum[axis] for axis in range(3)) for cell in cells))


def orientations(voxels):
    unique = {}
    for matrix in proper_rotations():
        oriented = normalize(tuple(transform(cell, matrix) for cell in voxels))
        unique.setdefault(oriented, oriented)
    return tuple(unique.values())


def root_stabilizer_permutations(root, placements):
    root_set = set(normalize(root))
    placement_index = {placement: index for index, placement in enumerate(placements)}
    permutations = []
    seen = set()
    for matrix in proper_rotations():
        transformed_root = tuple(transform(cell, matrix) for cell in root)
        minimum = tuple(min(cell[axis] for cell in transformed_root) for axis in range(3))
        normalized_root = tuple(sorted(tuple(
            cell[axis] - minimum[axis] for axis in range(3)
        ) for cell in transformed_root))
        if set(normalized_root) != root_set:
            continue
        permutation = tuple(placement_index[tuple(sorted(tuple(
            transform(cell, matrix)[axis] - minimum[axis] for axis in range(3)
        ) for cell in placement))] for placement in placements)
        if permutation not in seen:
            seen.add(permutation)
            permutations.append(permutation)
    return tuple(permutations)


def target_cells(root, layers):
    root_set = set(root)
    target = set()
    frontier = set(root)
    for _ in range(layers):
        next_frontier = set()
        for cell in frontier:
            for direction in DIRECTIONS:
                neighbor = tuple(cell[axis] + direction[axis] for axis in range(3))
                if neighbor in root_set or neighbor in target:
                    continue
                target.add(neighbor)
                next_frontier.add(neighbor)
        frontier = next_frontier
    return target


def enumerate_placements(root, layers):
    root_set = set(root)
    target = target_cells(root, layers)
    placement_set = set()
    for pivot in sorted(target):
        for orientation in orientations(root):
            for anchor in orientation:
                translation = tuple(pivot[axis] - anchor[axis] for axis in range(3))
                cells = tuple(sorted(tuple(cell[axis] + translation[axis] for axis in range(3)) for cell in orientation))
                if root_set.isdisjoint(cells):
                    placement_set.add(cells)
    return target, tuple(sorted(placement_set))


def parse_key(key):
    return tuple(tuple(int(value) for value in cell.split(",")) for cell in key.split(";") if cell)


def parse_cell_key(key):
    cell = tuple(int(value) for value in str(key).split(","))
    if len(cell) != 3:
        raise ValueError(f"Invalid cell key: {key}")
    return cell


def main():
    parser = argparse.ArgumentParser(description="Solve a finite polycube corona as an exact pseudo-Boolean cover in Z3.")
    parser.add_argument("--key", required=True)
    parser.add_argument("--layer", type=int, default=5)
    parser.add_argument("--timeout-ms", type=int, default=300_000)
    parser.add_argument("--backend", choices=("smt", "qffpbv", "pb2bv-sat"), default="smt")
    parser.add_argument("--random-seed", type=int, default=0)
    parser.add_argument("--min-placements", type=int)
    parser.add_argument("--max-placements", type=int)
    parser.add_argument("--require-next-layer-coverability", action="store_true")
    parser.add_argument("--cell-coverability-report")
    parser.add_argument("--pair-coverability-report")
    parser.add_argument("--triple-coverability-report")
    parser.add_argument("--quadruple-coverability-report")
    parser.add_argument("--triple-encoding", choices=("dnf", "choice-cnf"), default="choice-cnf")
    parser.add_argument("--pair-encoding", choices=("dnf", "choice-cnf", "witness-cnf"), default="dnf")
    parser.add_argument("--lookahead-conflict-encoding", choices=("edge-cnf", "grouped-pb"), default="edge-cnf")
    parser.add_argument("--root-symmetry-breaking", action="store_true")
    parser.add_argument("--forbidden-clause-report")
    parser.add_argument("--output")
    args = parser.parse_args()
    if (args.layer < 1 or args.timeout_ms < 1
            or (args.min_placements is not None and args.min_placements < 1)
            or (args.max_placements is not None and args.max_placements < 1)):
        parser.error("layer, timeout, and placement bounds (when supplied) must be positive")
    if (args.min_placements is not None and args.max_placements is not None
            and args.min_placements > args.max_placements):
        parser.error("min-placements cannot exceed max-placements")

    started = time.perf_counter()
    root = parse_key(args.key)
    target, placements = enumerate_placements(root, args.layer)
    by_cell = {}
    for index, placement in enumerate(placements):
        for cell in placement:
            by_cell.setdefault(cell, []).append(index)

    variables = [z3.Bool(f"p_{index}") for index in range(len(placements))]
    placement_index_by_key = {
        ";".join(sorted(",".join(str(value) for value in cell) for cell in placement)): index
        for index, placement in enumerate(placements)
    }
    if args.backend == "qffpbv":
        solver = z3.Tactic("qffpbv").solver()
    elif args.backend == "pb2bv-sat":
        sat_tactic = z3.With(z3.Tactic("sat"), random_seed=args.random_seed)
        solver = z3.Then("simplify", "pb-preprocess", "pb2bv", sat_tactic).solver()
    else:
        solver = z3.Solver()
    solver.set(timeout=args.timeout_ms)
    for cell in sorted(target):
        indices = by_cell.get(cell, [])
        if not indices:
            solver.add(z3.BoolVal(False))
        else:
            solver.add(z3.PbEq([(variables[index], 1) for index in indices], 1))
    for cell, indices in sorted(by_cell.items()):
        if cell not in target and len(indices) > 1:
            solver.add(z3.PbLe([(variables[index], 1) for index in indices], 1))
    if args.min_placements is not None:
        solver.add(z3.PbGe([(variable, 1) for variable in variables], args.min_placements))
    if args.max_placements is not None:
        solver.add(z3.PbLe([(variable, 1) for variable in variables], args.max_placements))
    root_stabilizer_size = 1
    symmetry_breaking_constraints = 0
    if args.root_symmetry_breaking:
        stabilizer_permutations = root_stabilizer_permutations(root, placements)
        root_stabilizer_size = len(stabilizer_permutations)
        identity = tuple(range(len(placements)))
        for symmetry_index, permutation in enumerate(stabilizer_permutations):
            if permutation == identity:
                continue
            prefix_equal = z3.BoolVal(True)
            for index, image_index in enumerate(permutation):
                image = variables[image_index]
                solver.add(z3.Implies(prefix_equal, z3.Or(z3.Not(variables[index]), image)))
                symmetry_breaking_constraints += 1
                if index + 1 < len(permutation):
                    next_prefix = z3.Bool(f"lex_{symmetry_index}_{index + 1}")
                    solver.add(next_prefix == z3.And(
                        prefix_equal,
                        variables[index] == image
                    ))
                    symmetry_breaking_constraints += 1
                    prefix_equal = next_prefix
    lookahead_target_count = 0
    lookahead_raw_placement_count = 0
    lookahead_placement_count = 0
    lookahead_conflict_count = 0
    lookahead_conflict_group_count = 0
    cell_coverability = []
    if args.cell_coverability_report:
        cell_report = json.loads(Path(args.cell_coverability_report).read_text(encoding="utf-8"))
        cell_coverability = cell_report.get("cells", cell_report) if isinstance(cell_report, dict) else cell_report
        if not isinstance(cell_coverability, list):
            raise ValueError("Cell coverability report must contain a cells list")
    pair_coverability = []
    if args.pair_coverability_report:
        pair_report = json.loads(Path(args.pair_coverability_report).read_text(encoding="utf-8"))
        pair_coverability = pair_report.get("pairs", pair_report) if isinstance(pair_report, dict) else pair_report
        if not isinstance(pair_coverability, list):
            raise ValueError("Pair coverability report must contain a pairs list")
    triple_coverability = []
    if args.triple_coverability_report:
        triple_report = json.loads(Path(args.triple_coverability_report).read_text(encoding="utf-8"))
        triple_coverability = triple_report.get("triples", triple_report) if isinstance(triple_report, dict) else triple_report
        if not isinstance(triple_coverability, list):
            raise ValueError("Triple coverability report must contain a triples list")
    quadruple_coverability = []
    if args.quadruple_coverability_report:
        quadruple_report = json.loads(Path(args.quadruple_coverability_report).read_text(encoding="utf-8"))
        quadruple_coverability = quadruple_report.get("quadruples", quadruple_report) if isinstance(quadruple_report, dict) else quadruple_report
        if not isinstance(quadruple_coverability, list):
            raise ValueError("Quadruple coverability report must contain a quadruples list")
    pair_coverability_count = 0
    pair_coverability_terms = 0
    pair_coverability_choice_variables = 0
    pair_coverability_incompatibilities = 0
    triple_coverability_count = 0
    triple_coverability_terms = 0
    triple_coverability_choice_variables = 0
    triple_coverability_incompatibilities = 0
    quadruple_coverability_count = 0
    quadruple_coverability_choice_variables = 0
    quadruple_coverability_incompatibilities = 0
    cell_coverability_count = 0
    if (args.require_next_layer_coverability or cell_coverability or pair_coverability
            or triple_coverability or quadruple_coverability):
        next_target, next_placements = enumerate_placements(root, args.layer + 1)
        next_ring = next_target - target
        normalized_cells = set()
        for cell_number, cell_key in enumerate(cell_coverability):
            cell = parse_cell_key(cell_key)
            if cell not in next_ring:
                raise ValueError(f"Cell coverability entry {cell_number} is not a next-ring cell")
            normalized_cells.add(cell)
        normalized_pairs = set()
        for pair_number, pair in enumerate(pair_coverability):
            if not isinstance(pair, list) or len(pair) != 2:
                raise ValueError(f"Pair coverability entry {pair_number} must contain two cell keys")
            cells = tuple(sorted((parse_cell_key(pair[0]), parse_cell_key(pair[1]))))
            if cells[0] == cells[1] or cells[0] not in next_ring or cells[1] not in next_ring:
                raise ValueError(f"Pair coverability entry {pair_number} is not a distinct next-ring cell pair")
            normalized_pairs.add(cells)
        normalized_triples = set()
        for triple_number, triple in enumerate(triple_coverability):
            if not isinstance(triple, list) or len(triple) != 3:
                raise ValueError(f"Triple coverability entry {triple_number} must contain three cell keys")
            cells = tuple(sorted(parse_cell_key(cell) for cell in triple))
            if len(set(cells)) != 3 or any(cell not in next_ring for cell in cells):
                raise ValueError(f"Triple coverability entry {triple_number} is not a distinct next-ring cell triple")
            normalized_triples.add(cells)
        normalized_quadruples = set()
        for quadruple_number, quadruple in enumerate(quadruple_coverability):
            if not isinstance(quadruple, list) or len(quadruple) != 4:
                raise ValueError(f"Quadruple coverability entry {quadruple_number} must contain four cell keys")
            cells = tuple(sorted(parse_cell_key(cell) for cell in quadruple))
            if len(set(cells)) != 4 or any(cell not in next_ring for cell in cells):
                raise ValueError(f"Quadruple coverability entry {quadruple_number} is not a distinct next-ring cell quadruple")
            normalized_quadruples.add(cells)
        constrained_cells = set(next_ring) if args.require_next_layer_coverability else set(normalized_cells)
        for pair in normalized_pairs:
            constrained_cells.update(pair)
        for triple in normalized_triples:
            constrained_cells.update(triple)
        for quadruple in normalized_quadruples:
            constrained_cells.update(quadruple)
        next_by_cell = {}
        for index, placement in enumerate(next_placements):
            for cell in placement:
                if cell in constrained_cells:
                    next_by_cell.setdefault(cell, []).append(index)
        relevant_indices = sorted(set(itertools.chain.from_iterable(next_by_cell.values())))
        outer_index_by_placement = {placement: index for index, placement in enumerate(placements)}
        conflict_sets = {}
        for index in relevant_indices:
            placement = next_placements[index]
            same_outer_index = outer_index_by_placement.get(placement)
            conflicts = set()
            for cell in placement:
                conflicts.update(by_cell.get(cell, ()))
            if same_outer_index is not None:
                conflicts.discard(same_outer_index)
            conflict_sets[index] = frozenset(conflicts)
        retained_by_cell = {}
        retained_indices = set()
        for cell in sorted(constrained_cells):
            if pair_coverability or triple_coverability or quadruple_coverability:
                retained = list(next_by_cell.get(cell, ()))
            else:
                representative_by_conflicts = {}
                for index in next_by_cell.get(cell, ()):
                    representative_by_conflicts.setdefault(conflict_sets[index], index)
                unique = list(representative_by_conflicts.items())
                retained = [
                    index for conflicts, index in unique
                    if not any(other < conflicts for other, _ in unique)
                ]
            retained_by_cell[cell] = retained
            retained_indices.update(retained)
        availability = {index: z3.Bool(f"a_{index}") for index in sorted(retained_indices)}
        conflicts_by_outer = {}
        for index in sorted(retained_indices):
            for conflict in sorted(conflict_sets[index]):
                conflicts_by_outer.setdefault(conflict, []).append(index)
                lookahead_conflict_count += 1
        if args.lookahead_conflict_encoding == "grouped-pb":
            for conflict, indices in sorted(conflicts_by_outer.items()):
                solver.add(z3.PbLe(
                    [(variables[conflict], len(indices))]
                    + [(availability[index], 1) for index in indices],
                    len(indices)
                ))
                lookahead_conflict_group_count += 1
        else:
            for conflict, indices in sorted(conflicts_by_outer.items()):
                for index in indices:
                    solver.add(z3.Or(z3.Not(availability[index]), z3.Not(variables[conflict])))
        coverability_cells = set(next_ring) if args.require_next_layer_coverability else normalized_cells
        for cell in sorted(coverability_cells):
            candidates = [availability[index] for index in retained_by_cell.get(cell, ())]
            solver.add(z3.Or(candidates) if candidates else z3.BoolVal(False))
        placement_cell_sets = {
            index: frozenset(next_placements[index]) for index in relevant_indices
        }
        for pair_index, (left_cell, right_cell) in enumerate(sorted(normalized_pairs)):
            if args.pair_encoding == "witness-cnf":
                left_indices = retained_by_cell.get(left_cell, ())
                right_indices = retained_by_cell.get(right_cell, ())
                if len(right_indices) < len(left_indices):
                    left_indices, right_indices = right_indices, left_indices
                witness_choices = []
                for left_index in left_indices:
                    compatible = [
                        availability[right_index]
                        for right_index in right_indices
                        if left_index == right_index or placement_cell_sets[left_index].isdisjoint(
                            placement_cell_sets[right_index]
                        )
                    ]
                    if not compatible:
                        continue
                    witness = z3.Bool(f"w_{pair_index}_{left_index}")
                    witness_choices.append(witness)
                    solver.add(z3.Or(z3.Not(witness), availability[left_index]))
                    solver.add(z3.Or(z3.Not(witness), z3.Or(compatible)))
                    pair_coverability_terms += len(compatible)
                solver.add(z3.Or(witness_choices) if witness_choices else z3.BoolVal(False))
                pair_coverability_choice_variables += len(witness_choices)
                continue
            if args.pair_encoding == "choice-cnf":
                left_choices = {
                    index: z3.Bool(f"q_{pair_index}_l_{index}")
                    for index in retained_by_cell.get(left_cell, ())
                }
                right_choices = {
                    index: z3.Bool(f"q_{pair_index}_r_{index}")
                    for index in retained_by_cell.get(right_cell, ())
                }
                solver.add(z3.Or(list(left_choices.values())) if left_choices else z3.BoolVal(False))
                solver.add(z3.Or(list(right_choices.values())) if right_choices else z3.BoolVal(False))
                for index, choice in itertools.chain(left_choices.items(), right_choices.items()):
                    solver.add(z3.Or(z3.Not(choice), availability[index]))
                for left_index, left_choice in left_choices.items():
                    for right_index, right_choice in right_choices.items():
                        if left_index == right_index or placement_cell_sets[left_index].isdisjoint(
                            placement_cell_sets[right_index]
                        ):
                            continue
                        solver.add(z3.Or(z3.Not(left_choice), z3.Not(right_choice)))
                        pair_coverability_incompatibilities += 1
                pair_coverability_choice_variables += len(left_choices) + len(right_choices)
                continue
            compatible_terms = {}
            for left_index in retained_by_cell.get(left_cell, ()):
                for right_index in retained_by_cell.get(right_cell, ()):
                    if left_index != right_index and not placement_cell_sets[left_index].isdisjoint(
                        placement_cell_sets[right_index]
                    ):
                        continue
                    pair_key = tuple(sorted((left_index, right_index)))
                    compatible_terms.setdefault(pair_key, (
                        availability[left_index]
                        if left_index == right_index
                        else z3.And(availability[left_index], availability[right_index])
                    ))
            solver.add(z3.Or(list(compatible_terms.values())) if compatible_terms else z3.BoolVal(False))
            pair_coverability_terms += len(compatible_terms)
        for triple_index, (left_cell, middle_cell, right_cell) in enumerate(sorted(normalized_triples)):
            if args.triple_encoding == "choice-cnf":
                choice_groups = []
                for side, cell in enumerate((left_cell, middle_cell, right_cell)):
                    choices = {
                        index: z3.Bool(f"t_{triple_index}_{side}_{index}")
                        for index in retained_by_cell.get(cell, ())
                    }
                    solver.add(z3.Or(list(choices.values())) if choices else z3.BoolVal(False))
                    for index, choice in choices.items():
                        solver.add(z3.Or(z3.Not(choice), availability[index]))
                    choice_groups.append(choices)
                    triple_coverability_choice_variables += len(choices)
                for left_group_index in range(3):
                    for right_group_index in range(left_group_index + 1, 3):
                        for left_index, left_choice in choice_groups[left_group_index].items():
                            for right_index, right_choice in choice_groups[right_group_index].items():
                                if left_index == right_index or placement_cell_sets[left_index].isdisjoint(
                                    placement_cell_sets[right_index]
                                ):
                                    continue
                                solver.add(z3.Or(z3.Not(left_choice), z3.Not(right_choice)))
                                triple_coverability_incompatibilities += 1
                continue
            compatible_terms = {}
            for left_index in retained_by_cell.get(left_cell, ()):
                for middle_index in retained_by_cell.get(middle_cell, ()):
                    if left_index != middle_index and not placement_cell_sets[left_index].isdisjoint(
                        placement_cell_sets[middle_index]
                    ):
                        continue
                    for right_index in retained_by_cell.get(right_cell, ()):
                        if ((left_index != right_index and not placement_cell_sets[left_index].isdisjoint(
                                placement_cell_sets[right_index]
                            ))
                                or (middle_index != right_index and not placement_cell_sets[middle_index].isdisjoint(
                                    placement_cell_sets[right_index]
                                ))):
                            continue
                        indices = tuple(sorted(set((left_index, middle_index, right_index))))
                        compatible_terms.setdefault(indices, z3.And([
                            availability[index] for index in indices
                        ]))
            solver.add(z3.Or(list(compatible_terms.values())) if compatible_terms else z3.BoolVal(False))
            triple_coverability_terms += len(compatible_terms)
        for quadruple_index, quadruple in enumerate(sorted(normalized_quadruples)):
            choice_groups = []
            for side, cell in enumerate(quadruple):
                choices = {
                    index: z3.Bool(f"u_{quadruple_index}_{side}_{index}")
                    for index in retained_by_cell.get(cell, ())
                }
                solver.add(z3.Or(list(choices.values())) if choices else z3.BoolVal(False))
                for index, choice in choices.items():
                    solver.add(z3.Or(z3.Not(choice), availability[index]))
                choice_groups.append(choices)
                quadruple_coverability_choice_variables += len(choices)
            for left_group_index in range(4):
                for right_group_index in range(left_group_index + 1, 4):
                    for left_index, left_choice in choice_groups[left_group_index].items():
                        for right_index, right_choice in choice_groups[right_group_index].items():
                            if left_index == right_index or placement_cell_sets[left_index].isdisjoint(
                                placement_cell_sets[right_index]
                            ):
                                continue
                            solver.add(z3.Or(z3.Not(left_choice), z3.Not(right_choice)))
                            quadruple_coverability_incompatibilities += 1
        pair_coverability_count = len(normalized_pairs)
        triple_coverability_count = len(normalized_triples)
        quadruple_coverability_count = len(normalized_quadruples)
        cell_coverability_count = len(coverability_cells)
        lookahead_target_count = len(constrained_cells)
        lookahead_raw_placement_count = len(relevant_indices)
        lookahead_placement_count = len(retained_indices)
    forbidden_clauses = []
    if args.forbidden_clause_report:
        clause_report = json.loads(Path(args.forbidden_clause_report).read_text(encoding="utf-8"))
        forbidden_clauses = clause_report.get("clauses", clause_report) if isinstance(clause_report, dict) else clause_report
        for clause_number, clause in enumerate(forbidden_clauses):
            if not isinstance(clause, list) or not clause:
                raise ValueError(f"Forbidden clause {clause_number} must be a nonempty placement-key list")
            try:
                indices = sorted(set(placement_index_by_key[str(key)] for key in clause))
            except KeyError as error:
                raise ValueError(f"Forbidden clause {clause_number} contains an unknown placement: {error.args[0]}") from error
            solver.add(z3.PbLe([(variables[index], 1) for index in indices], len(indices) - 1))

    constraint_count = len(solver.assertions())
    status = solver.check()
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    selected = []
    if status == z3.sat:
        model = solver.model()
        selected = [placements[index] for index, variable in enumerate(variables) if z3.is_true(model.eval(variable))]
    report = {
        "kind": "polycube_corona_z3_exact_cover",
        "key": args.key,
        "layer": args.layer,
        "model": "proper cubic rotations; root fixed; primary target cells exactly once; secondary cells at most once",
        "backend": args.backend,
        "random_seed": args.random_seed,
        "min_placements": args.min_placements,
        "max_placements": args.max_placements,
        "require_next_layer_coverability": args.require_next_layer_coverability,
        "cell_coverability_constraints": cell_coverability_count,
        "lookahead_target_cells": lookahead_target_count,
        "lookahead_raw_placements": lookahead_raw_placement_count,
        "lookahead_placements": lookahead_placement_count,
        "lookahead_conflicts": lookahead_conflict_count,
        "lookahead_conflict_encoding": args.lookahead_conflict_encoding,
        "lookahead_conflict_groups": lookahead_conflict_group_count,
        "pair_coverability_constraints": pair_coverability_count,
        "pair_coverability_terms": pair_coverability_terms,
        "pair_coverability_encoding": args.pair_encoding,
        "pair_coverability_choice_variables": pair_coverability_choice_variables,
        "pair_coverability_incompatibilities": pair_coverability_incompatibilities,
        "triple_coverability_constraints": triple_coverability_count,
        "triple_coverability_terms": triple_coverability_terms,
        "triple_coverability_encoding": args.triple_encoding,
        "triple_coverability_choice_variables": triple_coverability_choice_variables,
        "triple_coverability_incompatibilities": triple_coverability_incompatibilities,
        "quadruple_coverability_constraints": quadruple_coverability_count,
        "quadruple_coverability_encoding": "choice-cnf",
        "quadruple_coverability_choice_variables": quadruple_coverability_choice_variables,
        "quadruple_coverability_incompatibilities": quadruple_coverability_incompatibilities,
        "root_symmetry_breaking": args.root_symmetry_breaking,
        "root_stabilizer_size": root_stabilizer_size,
        "symmetry_breaking_constraints": symmetry_breaking_constraints,
        "target_cells": len(target),
        "placements_considered": len(placements),
        "variables": len(variables),
        "constraints": constraint_count,
        "forbidden_clauses": len(forbidden_clauses),
        "timeout_ms": args.timeout_ms,
        "milliseconds": elapsed_ms,
        "classification": (
            "verified_pending" if status == z3.sat
            else "certified_non_tiler" if status == z3.unsat and args.min_placements is None and args.max_placements is None and not forbidden_clauses
            else "unsat_under_forbidden_clauses" if status == z3.unsat and args.min_placements is None and args.max_placements is None
            else "placement_bound_exhausted" if status == z3.unsat
            else "incomplete"
        ),
        "z3_status": str(status),
        "reason_unknown": solver.reason_unknown() if status == z3.unknown else None,
        "corona": [{"cells": [list(cell) for cell in placement]} for placement in selected] if selected else None,
        "warning": (
            "UNSAT depends on externally supplied forbidden clauses; validate their continuation proofs before treating this as a non-tiling certificate."
            if status == z3.unsat and args.min_placements is None and args.max_placements is None and forbidden_clauses
            else (
                f"Only patches in the configured placement-count range "
                f"[{args.min_placements if args.min_placements is not None else 0}, "
                f"{args.max_placements if args.max_placements is not None else 'unbounded'}] were exhausted; "
                "this is not a non-tiling or aperiodicity certificate."
            )
            if status == z3.unsat and (args.min_placements is not None or args.max_placements is not None)
            else "A solver timeout is not a non-tiling or aperiodicity certificate."
            if status == z3.unknown
            else None
        ),
    }
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "corona"}))


if __name__ == "__main__":
    main()
