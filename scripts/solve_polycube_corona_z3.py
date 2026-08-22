#!/usr/bin/env python3

import argparse
import itertools
import json
import sys
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


def cell_key(cell):
    return ",".join(str(value) for value in cell)


def canonical_pair_key(pair):
    return ";".join(cell_key(cell) for cell in sorted(pair))


def cell_token(cell):
    return "_".join(f"m{-value}" if value < 0 else f"p{value}" for value in cell)


def main():
    parser = argparse.ArgumentParser(description="Solve a finite polycube corona as an exact pseudo-Boolean cover in Z3.")
    parser.add_argument("--key", required=True)
    parser.add_argument("--layer", type=int, default=5)
    parser.add_argument("--timeout-ms", type=int, default=300_000)
    parser.add_argument("--max-witnesses", type=int, default=1)
    parser.add_argument("--backend", choices=("smt", "qffpbv", "pb2bv-sat"), default="smt")
    parser.add_argument("--random-seed", type=int, default=0)
    parser.add_argument("--min-placements", type=int)
    parser.add_argument("--max-placements", type=int)
    parser.add_argument("--require-next-layer-coverability", action="store_true")
    parser.add_argument("--cell-coverability-report")
    parser.add_argument("--pair-coverability-report")
    parser.add_argument("--pair-soft-minimum", type=int)
    parser.add_argument("--pair-soft-orbit-minimum", type=int)
    parser.add_argument("--triple-coverability-report")
    parser.add_argument("--quadruple-coverability-report")
    parser.add_argument("--triple-encoding", choices=("dnf", "choice-cnf"), default="choice-cnf")
    parser.add_argument("--pair-encoding", choices=("dnf", "choice-cnf", "witness-cnf"), default="dnf")
    parser.add_argument("--lookahead-conflict-encoding", choices=("edge-cnf", "grouped-pb"), default="edge-cnf")
    parser.add_argument("--root-symmetry-breaking", action="store_true")
    parser.add_argument("--forbidden-clause-report")
    parser.add_argument("--formula-cache")
    parser.add_argument("--interactive-jsonl", action="store_true")
    parser.add_argument("--interactive-replace-pairs", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    if (args.layer < 1 or args.timeout_ms < 1 or args.max_witnesses < 1
            or (args.min_placements is not None and args.min_placements < 1)
            or (args.max_placements is not None and args.max_placements < 1)
            or (args.pair_soft_minimum is not None and args.pair_soft_minimum < 1)
            or (args.pair_soft_orbit_minimum is not None and args.pair_soft_orbit_minimum < 1)):
        parser.error("layer, timeout, witness count, and placement bounds (when supplied) must be positive")
    if (args.min_placements is not None and args.max_placements is not None
            and args.min_placements > args.max_placements):
        parser.error("min-placements cannot exceed max-placements")
    if args.formula_cache and not args.require_next_layer_coverability:
        parser.error("formula caching currently requires --require-next-layer-coverability")
    if args.interactive_jsonl and (not args.require_next_layer_coverability or args.max_witnesses != 1):
        parser.error("interactive mode requires next-layer coverability and max-witnesses=1")
    if args.interactive_replace_pairs and not args.interactive_jsonl:
        parser.error("--interactive-replace-pairs requires --interactive-jsonl")
    if args.pair_soft_minimum is not None and args.interactive_jsonl:
        parser.error("--pair-soft-minimum is not yet supported with --interactive-jsonl")
    if args.pair_soft_orbit_minimum is not None and args.interactive_jsonl:
        parser.error("--pair-soft-orbit-minimum is not yet supported with --interactive-jsonl")
    if args.pair_soft_minimum is not None and args.pair_soft_orbit_minimum is not None:
        parser.error("pair soft constraint and orbit minimums are mutually exclusive")
    if ((args.pair_soft_minimum is not None or args.pair_soft_orbit_minimum is not None)
            and not args.pair_coverability_report):
        parser.error("pair soft minimums require --pair-coverability-report")

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
    pair_coverability = []
    pair_soft_orbit_groups = []
    if args.pair_coverability_report:
        pair_report = json.loads(Path(args.pair_coverability_report).read_text(encoding="utf-8"))
        pair_coverability = pair_report.get("pairs", pair_report) if isinstance(pair_report, dict) else pair_report
        if not isinstance(pair_coverability, list):
            raise ValueError("Pair coverability report must contain a pairs list")
        if isinstance(pair_report, dict):
            pair_soft_orbit_groups = pair_report.get("orbit_groups", [])
            if not isinstance(pair_soft_orbit_groups, list):
                raise ValueError("Pair coverability orbit_groups must be a list")
    pair_report_keys = set()
    for pair_number, pair in enumerate(pair_coverability):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError(f"Pair coverability entry {pair_number} must contain two cell keys")
        pair_report_keys.add(canonical_pair_key(tuple(parse_cell_key(cell) for cell in pair)))
    cache_path = Path(args.formula_cache) if args.formula_cache else None
    cache_metadata_path = Path(f"{args.formula_cache}.json") if args.formula_cache else None
    cache_signature = json.dumps({
        "version": 2,
        "key": args.key,
        "layer": args.layer,
        "min_placements": args.min_placements,
        "max_placements": args.max_placements,
        "require_next_layer_coverability": args.require_next_layer_coverability,
        "lookahead_conflict_encoding": args.lookahead_conflict_encoding,
        "root_symmetry_breaking": args.root_symmetry_breaking,
        "pair_encoding": args.pair_encoding,
        "pair_soft_minimum": args.pair_soft_minimum,
        "pair_soft_orbit_minimum": args.pair_soft_orbit_minimum,
        "pair_soft_orbit_groups": pair_soft_orbit_groups,
        "interactive_replace_pairs": args.interactive_replace_pairs,
    }, sort_keys=True)
    cache_metadata = None
    if cache_path and cache_path.is_file() and cache_metadata_path.is_file():
        candidate_metadata = json.loads(cache_metadata_path.read_text(encoding="utf-8"))
        cached_pair_keys = set(candidate_metadata.get("pair_keys", ()))
        if (candidate_metadata.get("signature") == cache_signature
                and (args.interactive_replace_pairs or cached_pair_keys.issubset(pair_report_keys))):
            cache_metadata = candidate_metadata
    if args.backend == "qffpbv":
        solver = z3.Tactic("qffpbv").solver()
    elif args.backend == "pb2bv-sat":
        sat_tactic = z3.With(z3.Tactic("sat"), random_seed=args.random_seed)
        solver = z3.Then("simplify", "pb-preprocess", "pb2bv", sat_tactic).solver()
    else:
        solver = z3.Solver()
    solver.set(timeout=args.timeout_ms)
    formula_cache_hit = cache_metadata is not None
    cached_pair_keys = set(cache_metadata.get("pair_keys", ())) if cache_metadata else set()
    formula_cache_load_ms = 0
    if formula_cache_hit:
        cache_load_started = time.perf_counter()
        solver.from_file(str(cache_path))
        formula_cache_load_ms = round((time.perf_counter() - cache_load_started) * 1000)
    for cell in sorted(target):
        indices = by_cell.get(cell, [])
        if formula_cache_hit:
            continue
        if not indices:
            solver.add(z3.BoolVal(False))
        else:
            solver.add(z3.PbEq([(variables[index], 1) for index in indices], 1))
    for cell, indices in sorted(by_cell.items()):
        if not formula_cache_hit and cell not in target and len(indices) > 1:
            solver.add(z3.PbLe([(variables[index], 1) for index in indices], 1))
    if not formula_cache_hit and args.min_placements is not None:
        solver.add(z3.PbGe([(variable, 1) for variable in variables], args.min_placements))
    if not formula_cache_hit and args.max_placements is not None:
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
                if not formula_cache_hit:
                    solver.add(z3.Implies(prefix_equal, z3.Or(z3.Not(variables[index]), image)))
                symmetry_breaking_constraints += 1
                if index + 1 < len(permutation):
                    next_prefix = z3.Bool(f"lex_{symmetry_index}_{index + 1}")
                    if not formula_cache_hit:
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
    cached_pair_stats = cache_metadata.get("pair_stats", {}) if cache_metadata else {}
    pair_coverability_terms = int(cached_pair_stats.get("terms", 0))
    pair_coverability_choice_variables = int(cached_pair_stats.get("choice_variables", 0))
    pair_coverability_incompatibilities = int(cached_pair_stats.get("incompatibilities", 0))
    triple_coverability_count = 0
    triple_coverability_terms = 0
    triple_coverability_choice_variables = 0
    triple_coverability_incompatibilities = 0
    quadruple_coverability_count = 0
    quadruple_coverability_choice_variables = 0
    quadruple_coverability_incompatibilities = 0
    pair_soft_orbit_variables = []
    cell_coverability_count = 0
    formula_cache_write_ms = 0
    formula_cache_pairs_added = 0
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
        normalized_soft_orbit_groups = []
        for group_number, group in enumerate(pair_soft_orbit_groups):
            if not isinstance(group, list) or not group:
                raise ValueError(f"Pair soft orbit group {group_number} must be a nonempty list")
            normalized_group = []
            for pair_number, pair in enumerate(group):
                if not isinstance(pair, list) or len(pair) != 2:
                    raise ValueError(
                        f"Pair soft orbit group {group_number} entry {pair_number} must contain two cell keys"
                    )
                cells = tuple(sorted((parse_cell_key(pair[0]), parse_cell_key(pair[1]))))
                if cells not in normalized_pairs:
                    raise ValueError(
                        f"Pair soft orbit group {group_number} contains a pair absent from pairs"
                    )
                normalized_group.append(cells)
            normalized_soft_orbit_groups.append(tuple(sorted(set(normalized_group))))
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
            if pair_coverability or triple_coverability or quadruple_coverability or args.formula_cache:
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
                if not formula_cache_hit:
                    solver.add(z3.PbLe(
                        [(variables[conflict], len(indices))]
                        + [(availability[index], 1) for index in indices],
                        len(indices)
                    ))
                lookahead_conflict_group_count += 1
        else:
            for conflict, indices in sorted(conflicts_by_outer.items()):
                for index in indices:
                    if not formula_cache_hit:
                        solver.add(z3.Or(z3.Not(availability[index]), z3.Not(variables[conflict])))
        coverability_cells = set(next_ring) if args.require_next_layer_coverability else normalized_cells
        for cell in sorted(coverability_cells):
            candidates = [availability[index] for index in retained_by_cell.get(cell, ())]
            if not formula_cache_hit:
                solver.add(z3.Or(candidates) if candidates else z3.BoolVal(False))
        placement_cell_sets = {
            index: frozenset(next_placements[index]) for index in relevant_indices
        }
        def pair_activation(left_cell, right_cell):
            return z3.Bool(f"pair_active_{cell_token(left_cell)}__{cell_token(right_cell)}")

        def encode_pair_constraint(left_cell, right_cell):
            nonlocal pair_coverability_terms
            nonlocal pair_coverability_choice_variables
            nonlocal pair_coverability_incompatibilities
            pair_name = f"{cell_token(left_cell)}__{cell_token(right_cell)}"
            activation = pair_activation(left_cell, right_cell) if (
                args.interactive_replace_pairs
                or args.pair_soft_minimum is not None
                or args.pair_soft_orbit_minimum is not None
            ) else None

            def add_pair_formula(formula):
                solver.add(z3.Implies(activation, formula) if activation is not None else formula)

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
                    witness_variable = z3.Bool(f"w_{pair_name}_{left_index}")
                    witness_choices.append(witness_variable)
                    add_pair_formula(z3.Or(z3.Not(witness_variable), availability[left_index]))
                    add_pair_formula(z3.Or(z3.Not(witness_variable), z3.Or(compatible)))
                    pair_coverability_terms += len(compatible)
                add_pair_formula(z3.Or(witness_choices) if witness_choices else z3.BoolVal(False))
                pair_coverability_choice_variables += len(witness_choices)
                return
            if args.pair_encoding == "choice-cnf":
                left_choices = {
                    index: z3.Bool(f"q_{pair_name}_l_{index}")
                    for index in retained_by_cell.get(left_cell, ())
                }
                right_choices = {
                    index: z3.Bool(f"q_{pair_name}_r_{index}")
                    for index in retained_by_cell.get(right_cell, ())
                }
                add_pair_formula(z3.Or(list(left_choices.values())) if left_choices else z3.BoolVal(False))
                add_pair_formula(z3.Or(list(right_choices.values())) if right_choices else z3.BoolVal(False))
                for index, choice in itertools.chain(left_choices.items(), right_choices.items()):
                    add_pair_formula(z3.Or(z3.Not(choice), availability[index]))
                for left_index, left_choice in left_choices.items():
                    for right_index, right_choice in right_choices.items():
                        if left_index == right_index or placement_cell_sets[left_index].isdisjoint(
                                placement_cell_sets[right_index]):
                            continue
                        add_pair_formula(z3.Or(z3.Not(left_choice), z3.Not(right_choice)))
                        pair_coverability_incompatibilities += 1
                pair_coverability_choice_variables += len(left_choices) + len(right_choices)
                return
            compatible_terms = {}
            for left_index in retained_by_cell.get(left_cell, ()):
                for right_index in retained_by_cell.get(right_cell, ()):
                    if left_index != right_index and not placement_cell_sets[left_index].isdisjoint(
                            placement_cell_sets[right_index]):
                        continue
                    placement_pair = tuple(sorted((left_index, right_index)))
                    compatible_terms.setdefault(placement_pair, (
                        availability[left_index]
                        if left_index == right_index
                        else z3.And(availability[left_index], availability[right_index])
                    ))
            add_pair_formula(z3.Or(list(compatible_terms.values())) if compatible_terms else z3.BoolVal(False))
            pair_coverability_terms += len(compatible_terms)

        for left_cell, right_cell in sorted(normalized_pairs):
            normalized_pair_key = canonical_pair_key((left_cell, right_cell))
            if normalized_pair_key in cached_pair_keys:
                continue
            formula_cache_pairs_added += 1
            encode_pair_constraint(left_cell, right_cell)
        if args.pair_soft_minimum is not None:
            if args.pair_soft_minimum > len(normalized_pairs):
                raise ValueError(
                    "pair soft minimum cannot exceed the pair-coverability constraint count"
                )
            solver.add(z3.PbGe([
                (pair_activation(left_cell, right_cell), 1)
                for left_cell, right_cell in sorted(normalized_pairs)
            ], args.pair_soft_minimum))
        if args.pair_soft_orbit_minimum is not None:
            if args.pair_soft_orbit_minimum > len(normalized_soft_orbit_groups):
                raise ValueError(
                    "pair soft orbit minimum cannot exceed the pair orbit group count"
                )
            for group_index, group in enumerate(normalized_soft_orbit_groups):
                group_variable = z3.Bool(f"pair_soft_orbit_{group_index}")
                pair_soft_orbit_variables.append(group_variable)
                for pair in group:
                    solver.add(z3.Implies(group_variable, pair_activation(*pair)))
            solver.add(z3.PbGe([
                (variable, 1) for variable in pair_soft_orbit_variables
            ], args.pair_soft_orbit_minimum))
        if cache_path and (not formula_cache_hit or formula_cache_pairs_added):
            cache_write_started = time.perf_counter()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_temporary = Path(f"{cache_path}.tmp")
            metadata_temporary = Path(f"{cache_metadata_path}.tmp")
            cache_temporary.write_text(solver.sexpr(), encoding="utf-8")
            cache_temporary.replace(cache_path)
            metadata_temporary.write_text(json.dumps({
                "signature": cache_signature,
                "pair_keys": sorted(
                    cached_pair_keys
                    | {canonical_pair_key(pair) for pair in normalized_pairs}
                ),
                "pair_stats": {
                    "terms": pair_coverability_terms,
                    "choice_variables": pair_coverability_choice_variables,
                    "incompatibilities": pair_coverability_incompatibilities,
                },
            }, indent=2) + "\n", encoding="utf-8")
            metadata_temporary.replace(cache_metadata_path)
            formula_cache_write_ms = round((time.perf_counter() - cache_write_started) * 1000)
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
    forbidden_clause_keys = set()
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
            forbidden_clause_keys.add(tuple(sorted(str(key) for key in clause)))
            solver.add(z3.PbLe([(variables[index], 1) for index in indices], len(indices) - 1))

    constraint_count = len(solver.assertions())
    construction_ms = round((time.perf_counter() - started) * 1000)
    if args.interactive_jsonl:
        normalized_pair_keys = {canonical_pair_key(pair) for pair in normalized_pairs}
        encoded_pair_keys = set(cached_pair_keys) | normalized_pair_keys
        pair_cells_by_key = {
            canonical_pair_key(pair): pair for pair in normalized_pairs
        }
        for key in cached_pair_keys:
            pair_cells_by_key.setdefault(
                key,
                tuple(parse_cell_key(cell) for cell in key.split(";"))
            )
        active_pair_keys = set(normalized_pair_keys)
        print(json.dumps({
            "type": "ready",
            "construction_milliseconds": construction_ms,
            "formula_cache_hit": formula_cache_hit,
            "formula_cache_pairs_reused": len(cached_pair_keys),
            "formula_cache_pairs_added": formula_cache_pairs_added,
            "formula_cache_load_milliseconds": formula_cache_load_ms,
            "formula_cache_write_milliseconds": formula_cache_write_ms,
            "pair_coverability_constraints": len(active_pair_keys),
            "pair_coverability_formulas": len(encoded_pair_keys),
            "interactive_replace_pairs": args.interactive_replace_pairs,
            "forbidden_clauses": len(forbidden_clause_keys),
            "constraints": constraint_count,
        }), flush=True)
        for line in sys.stdin:
            command = json.loads(line)
            if command.get("type") == "stop":
                break
            if command.get("type") != "next":
                raise ValueError("Interactive command type must be next or stop")
            clauses_added = 0
            for clause_number, clause in enumerate(command.get("clauses", ())):
                if not isinstance(clause, list) or not clause:
                    raise ValueError(f"Interactive clause {clause_number} must be nonempty")
                clause_key = tuple(sorted(str(key) for key in clause))
                if clause_key in forbidden_clause_keys:
                    continue
                try:
                    indices = sorted(set(placement_index_by_key[key] for key in clause_key))
                except KeyError as error:
                    raise ValueError(
                        f"Interactive clause {clause_number} contains an unknown placement: {error.args[0]}"
                    ) from error
                solver.add(z3.PbLe([(variables[index], 1) for index in indices], len(indices) - 1))
                forbidden_clause_keys.add(clause_key)
                clauses_added += 1
            pairs_added = 0
            replacement_pairs = command.get("replace_pairs")
            if replacement_pairs is not None and not args.interactive_replace_pairs:
                raise ValueError("replace_pairs requires --interactive-replace-pairs")
            supplied_pairs = replacement_pairs if replacement_pairs is not None else command.get("pairs", ())
            supplied_pair_keys = set()
            for pair_number, pair in enumerate(supplied_pairs):
                if not isinstance(pair, list) or len(pair) != 2:
                    raise ValueError(f"Interactive pair {pair_number} must contain two cell keys")
                cells = tuple(sorted(parse_cell_key(cell) for cell in pair))
                if cells[0] == cells[1] or cells[0] not in next_ring or cells[1] not in next_ring:
                    raise ValueError(f"Interactive pair {pair_number} is not a distinct next-ring cell pair")
                normalized_key = canonical_pair_key(cells)
                supplied_pair_keys.add(normalized_key)
                pair_cells_by_key[normalized_key] = cells
                if normalized_key not in encoded_pair_keys:
                    encode_pair_constraint(*cells)
                    encoded_pair_keys.add(normalized_key)
                    pairs_added += 1
            if replacement_pairs is not None:
                active_pair_keys = supplied_pair_keys
            else:
                active_pair_keys.update(supplied_pair_keys)
            command_timeout_ms = int(command.get("timeout_ms", args.timeout_ms))
            if command_timeout_ms < 1:
                raise ValueError("Interactive timeout must be positive")
            solver.set(timeout=command_timeout_ms)
            check_started = time.perf_counter()
            pair_assumptions = []
            if args.interactive_replace_pairs:
                pair_assumptions = [
                    pair_activation(*pair_cells_by_key[key])
                    if key in active_pair_keys
                    else z3.Not(pair_activation(*pair_cells_by_key[key]))
                    for key in sorted(encoded_pair_keys)
                ]
            interactive_status = solver.check(*pair_assumptions)
            interactive_check_ms = round((time.perf_counter() - check_started) * 1000)
            selected = []
            if interactive_status == z3.sat:
                model = solver.model()
                selected = [
                    placements[index] for index, variable in enumerate(variables)
                    if z3.is_true(model.eval(variable, model_completion=True))
                ]
            print(json.dumps({
                "type": "result",
                "z3_status": str(interactive_status),
                "reason_unknown": solver.reason_unknown() if interactive_status == z3.unknown else None,
                "check_milliseconds": interactive_check_ms,
                "clauses_added": clauses_added,
                "pairs_added": pairs_added,
                "forbidden_clauses": len(forbidden_clause_keys),
                "pair_coverability_constraints": len(active_pair_keys),
                "pair_coverability_formulas": len(encoded_pair_keys),
                "interactive_replace_pairs": args.interactive_replace_pairs,
                "constraints": len(solver.assertions()),
                "corona": [
                    {"cells": [list(cell) for cell in placement]} for placement in selected
                ] if selected else None,
            }), flush=True)
        return

    witnesses = []
    check_ms = 0
    batch_blocking_clauses = 0
    batch_terminal_status = "limit"
    batch_reason_unknown = None
    terminal_status = None
    while len(witnesses) < args.max_witnesses:
        remaining_timeout_ms = max(1, args.timeout_ms - check_ms)
        solver.set(timeout=remaining_timeout_ms)
        check_started = time.perf_counter()
        terminal_status = solver.check()
        witness_check_ms = round((time.perf_counter() - check_started) * 1000)
        check_ms += witness_check_ms
        if terminal_status != z3.sat:
            batch_terminal_status = str(terminal_status)
            batch_reason_unknown = solver.reason_unknown() if terminal_status == z3.unknown else None
            break
        model = solver.model()
        selected_indices = [
            index for index, variable in enumerate(variables)
            if z3.is_true(model.eval(variable, model_completion=True))
        ]
        selected = [placements[index] for index in selected_indices]
        witnesses.append({
            "check_milliseconds": witness_check_ms,
            "placements": len(selected),
            "pair_soft_satisfied": sum(
                1 for pair in normalized_pairs
                if args.pair_soft_minimum is not None
                and z3.is_true(model.eval(pair_activation(*pair), model_completion=True))
            ) if args.pair_soft_minimum is not None else None,
            "pair_soft_orbits_satisfied": sum(
                1 for variable in pair_soft_orbit_variables
                if z3.is_true(model.eval(variable, model_completion=True))
            ) if args.pair_soft_orbit_minimum is not None else None,
            "corona": [{"cells": [list(cell) for cell in placement]} for placement in selected],
        })
        if len(witnesses) >= args.max_witnesses:
            break
        selected_index_set = set(selected_indices)
        solver.add(z3.Or([
            z3.Not(variable) if index in selected_index_set else variable
            for index, variable in enumerate(variables)
        ]))
        batch_blocking_clauses += 1
    status = z3.sat if witnesses else terminal_status
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    selected = witnesses[0]["corona"] if witnesses else None
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
        "pair_soft_minimum": args.pair_soft_minimum,
        "pair_soft_satisfied": witnesses[0]["pair_soft_satisfied"] if witnesses else None,
        "pair_soft_orbit_minimum": args.pair_soft_orbit_minimum,
        "pair_soft_orbits_satisfied": (
            witnesses[0]["pair_soft_orbits_satisfied"] if witnesses else None
        ),
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
        "max_witnesses": args.max_witnesses,
        "witness_count": len(witnesses),
        "batch_blocking_clauses": batch_blocking_clauses,
        "batch_terminal_status": batch_terminal_status,
        "batch_reason_unknown": batch_reason_unknown,
        "formula_cache": str(cache_path) if cache_path else None,
        "formula_cache_hit": formula_cache_hit,
        "formula_cache_pairs_reused": len(cached_pair_keys),
        "formula_cache_pairs_added": formula_cache_pairs_added,
        "formula_cache_load_milliseconds": formula_cache_load_ms,
        "formula_cache_write_milliseconds": formula_cache_write_ms,
        "construction_milliseconds": construction_ms,
        "check_milliseconds": check_ms,
        "milliseconds": elapsed_ms,
        "classification": (
            "verified_pending" if status == z3.sat
            else "certified_non_tiler" if status == z3.unsat and args.min_placements is None and args.max_placements is None and not forbidden_clauses
            else "unsat_under_forbidden_clauses" if status == z3.unsat and args.min_placements is None and args.max_placements is None
            else "placement_bound_exhausted" if status == z3.unsat
            else "incomplete"
        ),
        "z3_status": str(status),
        "reason_unknown": batch_reason_unknown if status == z3.unknown else None,
        "corona": selected,
        "coronas": [witness["corona"] for witness in witnesses],
        "witnesses": witnesses,
        "warning": (
            "Additional batch enumeration timed out after returning valid witnesses; the returned patches remain exact, but the batch is incomplete."
            if witnesses and batch_terminal_status == "unknown"
            else "UNSAT depends on externally supplied forbidden clauses; validate their continuation proofs before treating this as a non-tiling certificate."
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
    print(json.dumps({
        key: value for key, value in report.items()
        if key not in ("corona", "coronas", "witnesses")
    }))


if __name__ == "__main__":
    main()
