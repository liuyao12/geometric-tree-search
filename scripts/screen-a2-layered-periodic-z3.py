#!/usr/bin/env python3
"""Exact periodic-quotient screen for A2 layered lattice functions.

The web search grows a boundary patch before looking for periods.  This tool
instead solves the finite weighted quotient directly: for each HNF sublattice,
one Boolean variable represents each oriented translate, every quotient point
must receive exactly 48 solid-angle units, and the selected copy count is
fixed.  Positive certificates are replayed independently with Cramer's-rule
quotient coordinates before they are written.
"""

from __future__ import annotations

import argparse
import gzip
import itertools
import json
import math
import time
from pathlib import Path

from z3 import Bool, If, PbEq, Solver, SolverFor, Sum, is_true, sat, unsat
from sympy import Matrix
from sympy.matrices.normalforms import hermite_normal_form


PERMUTATIONS = tuple(itertools.permutations(range(3)))


def read_ndjson(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def permutation_parity(permutation: tuple[int, int, int]) -> int:
    inversions = sum(
        permutation[left] > permutation[right]
        for left in range(3)
        for right in range(left + 1, 3)
    )
    return -1 if inversions % 2 else 1


A2_LAYER_ISOMETRIES = tuple(
    (sign, permutation)
    for sign in (1, -1)
    for permutation in PERMUTATIONS
    if sign * permutation_parity(permutation) == 1
)


def cell_vertices(cell: dict) -> list[tuple[int, int, int]]:
    q, r, k, kind = cell["q"], cell["r"], cell["k"], cell["kind"]
    axial = (
        ((q, r), (q + 1, r), (q, r + 1))
        if kind == "u"
        else ((q + 1, r + 1), (q, r + 1), (q + 1, r))
    )
    base = [(x + k, y + k, -x - y + k) for x, y in axial]
    return base + [tuple(coordinate + 1 for coordinate in point) for point in base]


def tile_occupancy(cells: list[dict]) -> dict[tuple[int, int, int], int]:
    occupancy: dict[tuple[int, int, int], int] = {}
    for cell in cells:
        for point in cell_vertices(cell):
            occupancy[point] = occupancy.get(point, 0) + 4
    if any(weight <= 0 or weight > 48 for weight in occupancy.values()):
        raise ValueError("invalid A2 layered solid-angle occupancy")
    return occupancy


def record_occupancy(record: dict) -> dict[tuple[int, int, int], int]:
    """Load either the original triangular-prism cells or an exact occupancy receipt."""
    if "occupancy" not in record:
        return tile_occupancy(record["cells"])
    occupancy: dict[tuple[int, int, int], int] = {}
    for entry in record["occupancy"]:
        point, weight = entry[0], entry[1]
        key = tuple(int(coordinate) for coordinate in point)
        if len(key) != 3 or any(coordinate != raw for coordinate, raw in zip(key, point)):
            raise ValueError("non-integral exact occupancy point")
        occupancy[key] = occupancy.get(key, 0) + int(weight)
    if any(weight <= 0 or weight > 48 for weight in occupancy.values()):
        raise ValueError("invalid exact solid-angle occupancy")
    return occupancy


def orientations(occupancy: dict) -> list[dict]:
    result = []
    seen = set()
    for sign, permutation in A2_LAYER_ISOMETRIES:
        transformed = {
            tuple(sign * point[permutation[axis]] for axis in range(3)): weight
            for point, weight in occupancy.items()
        }
        key = tuple(sorted(transformed.items()))
        if key in seen:
            continue
        seen.add(key)
        result.append({
            "occupancy": transformed,
            "sign": sign,
            "permutation": permutation,
        })
    return result


def hnf_candidates(determinant: int):
    candidates = []
    for a in range(1, determinant + 1):
        if determinant % a:
            continue
        for d in range(1, determinant // a + 1):
            if determinant % (a * d):
                continue
            f = determinant // (a * d)
            for b in range(a):
                for c in range(a):
                    for e in range(d):
                        candidates.append((a, b, c, d, e, f))
    return sorted(candidates, key=lambda hnf: (
        max(hnf[0], hnf[3], hnf[5]) - min(hnf[0], hnf[3], hnf[5]),
        hnf[1] + hnf[2] + hnf[4],
        hnf,
    ))


def transformed_hnf(hnf, isometry):
    a, b, c, d, e, f = hnf
    basis = Matrix(((a, b, c), (0, d, e), (0, 0, f)))
    sign, permutation = isometry
    transform = Matrix(3, 3, lambda row, column:
                       sign if permutation[row] == column else 0)
    result = hermite_normal_form(transform * basis)
    return (
        int(result[0, 0]), int(result[0, 1]), int(result[0, 2]),
        int(result[1, 1]), int(result[1, 2]), int(result[2, 2]),
    )


def hnf_orbits(determinant: int) -> list[dict]:
    """Partition every HNF by the proper fixed A2 layer point group."""
    hnfs = hnf_candidates(determinant)
    index = {hnf: position for position, hnf in enumerate(hnfs)}
    parent = list(range(len(hnfs)))

    def find(position):
        while parent[position] != position:
            parent[position] = parent[parent[position]]
            position = parent[position]
        return position

    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left

    for position, hnf in enumerate(hnfs):
        for isometry in A2_LAYER_ISOMETRIES:
            transformed = transformed_hnf(hnf, isometry)
            if transformed not in index:
                raise RuntimeError(f"transformed HNF missing: {hnf} -> {transformed}")
            union(position, index[transformed])
    classes = {}
    for position in range(len(hnfs)):
        classes.setdefault(find(position), []).append(position)
    return [{
        "representative_index": min(members),
        "representative_hnf": hnfs[min(members)],
        "member_indices": sorted(members),
    } for members in sorted(classes.values(), key=min)]


def period_vectors(hnf: tuple[int, int, int, int, int, int]):
    a, b, c, d, e, f = hnf
    return ((a, 0, 0), (b, d, 0), (c, e, f))


def reduce_hnf(point: tuple[int, int, int], hnf) -> tuple[int, int, int]:
    x, y, z = point
    a, b, c, d, e, f = hnf
    quotient = z // f
    x, y, z = x - quotient * c, y - quotient * e, z - quotient * f
    quotient = y // d
    x, y = x - quotient * b, y - quotient * d
    quotient = x // a
    x -= quotient * a
    return x % a, y % d, z % f


def quotient_index(point, hnf) -> int:
    x, y, z = reduce_hnf(point, hnf)
    return x + hnf[0] * (y + hnf[3] * z)


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def replay_certificate(tile_orientations, certificate: dict) -> dict:
    basis = tuple(tuple(vector) for vector in certificate["period_vectors"])
    determinant = abs(dot(basis[0], cross(basis[1], basis[2])))
    if determinant != certificate["determinant"]:
        return {"verified": False, "reason": "determinant_mismatch"}
    numerators = (
        cross(basis[1], basis[2]),
        cross(basis[2], basis[0]),
        cross(basis[0], basis[1]),
    )
    weights: dict[tuple[int, int, int], int] = {}
    for placement in certificate["placements"]:
        orientation_index = placement["orientation_index"]
        if orientation_index < 0 or orientation_index >= len(tile_orientations):
            return {"verified": False, "reason": "unknown_orientation"}
        translation = tuple(placement["translation"])
        for point, weight in tile_orientations[orientation_index]["occupancy"].items():
            translated = tuple(point[axis] + translation[axis] for axis in range(3))
            signature = tuple(dot(translated, numerator) % determinant for numerator in numerators)
            weights[signature] = weights.get(signature, 0) + weight
    if len(weights) != determinant:
        return {"verified": False, "reason": "quotient_not_full", "classes": len(weights)}
    if any(weight != 48 for weight in weights.values()):
        return {"verified": False, "reason": "quotient_weight_mismatch"}
    return {
        "verified": True,
        "method": "independent_cramers_rule_weighted_quotient",
        "determinant": determinant,
        "classes": len(weights),
    }


def popcount(value: int) -> int:
    """Python 3.9-compatible population count for placement masks."""
    return bin(value).count("1")


def exact_weighted_multicover(
    placements: list[dict], copies: int, dfs_node_limit: int | None = None
) -> dict:
    """Solve one rooted quotient exactly with sparse bitset GCTS.

    A global translation and proper A2 rotation fix placement zero.  At every
    state, ``capacities`` is the still-missing solid angle at each quotient
    residue.  The pivot residue must be covered by some remaining placement;
    branching over all such placements is therefore complete.  Failed states
    are memoized with their capacities, remaining cardinality, and the still-
    relevant blocked-placement mask, so a Boolean placement can never be
    reused.  For the larger (10+ copy) searches where memo size dominates, a
    blocked placement that already exceeds a residual capacity can never fit
    after capacities decrease further; dropping that dead bit soundly
    identifies states with identical futures.  Smaller cardinalities retain
    the cheaper raw mask because measured per-node overhead outweighs reuse.
    """
    if copies < 1 or not placements:
        raise ValueError("invalid rooted weighted multicover")
    raw_vectors = [tuple(placement["weights"]) for placement in placements]
    divisor = math.gcd(48, *(
        weight for vector in raw_vectors for weight in vector
    ))
    full_weight = 48 // divisor
    vectors = [tuple(weight // divisor for weight in vector) for vector in raw_vectors]
    capacities = tuple(full_weight - weight for weight in vectors[0])
    if any(capacity < 0 for capacity in capacities):
        return {
            "result": "unsat", "chosen_indices": None,
            "nodes": 1, "failed_states": 1, "eligible_placements": 0,
            "used_mitm": False, "mitm_pairs": 0, "mitm_triples": 0,
            "mitm_quadruples": 0,
        }

    original_indices = []
    eligible_vectors = []
    for index, vector in enumerate(vectors[1:], 1):
        if all(weight <= capacity for weight, capacity in zip(vector, capacities)):
            original_indices.append(index)
            eligible_vectors.append(vector)
    residue_count = len(capacities)
    eligible_count = len(eligible_vectors)
    all_mask = (1 << eligible_count) - 1
    positive_masks = [0] * residue_count
    weight_masks = [
        [0] * (full_weight + 1) for _ in range(residue_count)
    ]
    sparse_vectors = []
    for placement_index, vector in enumerate(eligible_vectors):
        bit = 1 << placement_index
        sparse = []
        for residue, weight in enumerate(vector):
            if not weight:
                continue
            positive_masks[residue] |= bit
            weight_masks[residue][weight] |= bit
            sparse.append((residue, weight))
        sparse_vectors.append(tuple(sparse))
    exceed_masks = [
        [0] * (full_weight + 1) for _ in range(residue_count)
    ]
    for residue in range(residue_count):
        running = 0
        for capacity in range(full_weight, -1, -1):
            exceed_masks[residue][capacity] = running
            running |= weight_masks[residue][capacity]

    nodes = 0
    failed = set()
    if dfs_node_limit is None:
        dfs_node_limit = (
            50000 if copies in (6, 8) else (250000 if copies == 7 else 0)
        )
    fallback = object()

    def search(state_capacities, selected_mask, remaining):
        nonlocal nodes
        nodes += 1
        if dfs_node_limit and nodes > dfs_node_limit:
            return fallback
        if remaining == 0:
            return () if not any(state_capacities) else None
        capacity_fit_mask = all_mask
        for residue, capacity in enumerate(state_capacities):
            capacity_fit_mask &= ~exceed_masks[residue][capacity]

        # ``selected_mask`` contains both chosen placements and canonically
        # skipped pivot alternatives.  Bits outside ``capacity_fit_mask`` are
        # permanently dead because capacities only decrease, so quotient them
        # out before memoization and recursion.  Keep ``remaining`` explicitly
        # because skipped and chosen bits are otherwise indistinguishable for
        # synthetic vectors.
        live_blocked_mask = (
            selected_mask & capacity_fit_mask if copies >= 10 else selected_mask
        )
        state = (state_capacities, live_blocked_mask, remaining)
        if state in failed:
            return None
        fitting_mask = capacity_fit_mask & ~live_blocked_mask

        # The geometric quotient uses equal positive-weight placements, but
        # this exact helper is also tested independently.  If all capacities
        # are filled before the requested cardinality, only all-zero vectors
        # may occupy the remaining Boolean slots.
        if not any(state_capacities):
            if popcount(fitting_mask) < remaining:
                failed.add(state)
                return None
            zero_indices = []
            while fitting_mask and len(zero_indices) < remaining:
                bit = fitting_mask & -fitting_mask
                fitting_mask -= bit
                zero_indices.append(original_indices[bit.bit_length() - 1])
            return tuple(zero_indices)

        pivot_mask = 0
        pivot_score = None
        pivot_residue = None
        for residue, capacity in enumerate(state_capacities):
            if not capacity:
                continue
            choices = fitting_mask & positive_masks[residue]
            choice_count = popcount(choices)
            if not choice_count:
                failed.add(state)
                return None

            # Even the largest ``remaining`` contributions cannot meet this
            # residue.  This is a necessary condition only, hence sound.
            available = 0
            slots = remaining
            for weight in range(full_weight, 0, -1):
                take = min(popcount(choices & weight_masks[residue][weight]), slots)
                available += take * weight
                slots -= take
                if not slots:
                    break
            if available < capacity:
                failed.add(state)
                return None
            score = (choice_count, -capacity, residue)
            if pivot_score is None or score < pivot_score:
                pivot_score = score
                pivot_mask = choices
                pivot_residue = residue

        # A multicover pivot can require contributions from several selected
        # placements.  Without canonical branching, choosing A and then B is
        # revisited as B and then A when both cover the pivot.  In the branch
        # whose first selected pivot placement is ``bit``, permanently exclude
        # every earlier pivot alternative: this declares ``bit`` to be the
        # least selected alternative for this pivot.  Every feasible subset
        # has exactly one such least member, so the reduction is complete and
        # explores each subset once rather than many placement orders.  Try
        # the largest contribution to the MRV pivot first, then retain stable
        # placement-index order within each weight class.
        skipped_pivot_mask = 0
        for pivot_weight in range(full_weight, 0, -1):
            same_weight_mask = pivot_mask & weight_masks[pivot_residue][pivot_weight]
            while same_weight_mask:
                bit = same_weight_mask & -same_weight_mask
                compact_index = bit.bit_length() - 1
                same_weight_mask -= bit
                next_capacities = list(state_capacities)
                for residue, weight in sparse_vectors[compact_index]:
                    next_capacities[residue] -= weight
                suffix = search(
                    tuple(next_capacities),
                    live_blocked_mask | skipped_pivot_mask | bit,
                    remaining - 1,
                )
                if suffix is fallback:
                    return fallback
                if suffix is not None:
                    return (original_indices[compact_index], *suffix)
                skipped_pivot_mask |= bit
        failed.add(state)
        return None

    chosen = search(capacities, 0, copies - 1)
    mitm_pairs = 0
    mitm_triples = 0
    mitm_quadruples = 0
    used_mitm = chosen is fallback
    if used_mitm and copies == 6:
        # Six copies leave five choices after fixing the root.  Exhaustively
        # split those choices 2+3.  Every five-element solution has such a
        # partition, so this is a complete fallback rather than a heuristic.
        pair_sums = {}
        for left in range(eligible_count):
            left_vector = eligible_vectors[left]
            for right in range(left + 1, eligible_count):
                summed = tuple(
                    left_weight + right_weight
                    for left_weight, right_weight in zip(
                        left_vector, eligible_vectors[right]
                    )
                )
                if any(
                    weight > capacity
                    for weight, capacity in zip(summed, capacities)
                ):
                    continue
                pair_sums.setdefault(summed, []).append((left, right))
                mitm_pairs += 1
        chosen = None
        for first in range(eligible_count):
            first_vector = eligible_vectors[first]
            for second in range(first + 1, eligible_count):
                pair = tuple(
                    left + right
                    for left, right in zip(first_vector, eligible_vectors[second])
                )
                if any(
                    weight > capacity
                    for weight, capacity in zip(pair, capacities)
                ):
                    continue
                for third in range(second + 1, eligible_count):
                    triple = tuple(
                        partial + weight
                        for partial, weight in zip(pair, eligible_vectors[third])
                    )
                    mitm_triples += 1
                    if any(
                        weight > capacity
                        for weight, capacity in zip(triple, capacities)
                    ):
                        continue
                    target = tuple(
                        capacity - weight
                        for capacity, weight in zip(capacities, triple)
                    )
                    triple_indices = (first, second, third)
                    disjoint_pair = next((
                        candidate_pair
                        for candidate_pair in pair_sums.get(target, ())
                        if all(index not in triple_indices for index in candidate_pair)
                    ), None)
                    if disjoint_pair is not None:
                        chosen = tuple(
                            original_indices[index]
                            for index in (*triple_indices, *disjoint_pair)
                        )
                        break
                if chosen is not None:
                    break
            if chosen is not None:
                break
    elif used_mitm and copies == 7:
        # Seven copies leave six choices after fixing the root.  Build every
        # fitting triple and match it against an earlier complementary,
        # disjoint triple.  Every six-element solution has a 3+3 partition,
        # so exhausting this table is a complete decision procedure.
        triple_sums = {}
        chosen = None
        for first in range(eligible_count):
            first_vector = eligible_vectors[first]
            for second in range(first + 1, eligible_count):
                pair = tuple(
                    left + right
                    for left, right in zip(first_vector, eligible_vectors[second])
                )
                if any(
                    weight > capacity
                    for weight, capacity in zip(pair, capacities)
                ):
                    continue
                for third in range(second + 1, eligible_count):
                    triple = tuple(
                        partial + weight
                        for partial, weight in zip(pair, eligible_vectors[third])
                    )
                    if any(
                        weight > capacity
                        for weight, capacity in zip(triple, capacities)
                    ):
                        continue
                    mitm_triples += 1
                    target = tuple(
                        capacity - weight
                        for capacity, weight in zip(capacities, triple)
                    )
                    triple_indices = (first, second, third)
                    disjoint_triple = next((
                        candidate_triple
                        for candidate_triple in triple_sums.get(target, ())
                        if all(index not in triple_indices for index in candidate_triple)
                    ), None)
                    if disjoint_triple is not None:
                        chosen = tuple(
                            original_indices[index]
                            for index in (*triple_indices, *disjoint_triple)
                        )
                        break
                    triple_sums.setdefault(triple, []).append(triple_indices)
                if chosen is not None:
                    break
            if chosen is not None:
                break
    elif used_mitm and copies == 8:
        # Eight copies leave seven choices after fixing the root.  Store every
        # fitting triple and stream every fitting quadruple against its exact
        # complement.  Every seven-element solution has a 3+4 partition, and
        # the explicit disjointness check prevents Boolean placement reuse.
        triple_sums = {}
        for first in range(eligible_count):
            first_vector = eligible_vectors[first]
            for second in range(first + 1, eligible_count):
                pair = tuple(
                    left + right
                    for left, right in zip(first_vector, eligible_vectors[second])
                )
                if any(
                    weight > capacity
                    for weight, capacity in zip(pair, capacities)
                ):
                    continue
                for third in range(second + 1, eligible_count):
                    triple = tuple(
                        partial + weight
                        for partial, weight in zip(pair, eligible_vectors[third])
                    )
                    if any(
                        weight > capacity
                        for weight, capacity in zip(triple, capacities)
                    ):
                        continue
                    triple_sums.setdefault(triple, []).append((first, second, third))
                    mitm_triples += 1
        chosen = None
        for first in range(eligible_count):
            first_vector = eligible_vectors[first]
            for second in range(first + 1, eligible_count):
                pair = tuple(
                    left + right
                    for left, right in zip(first_vector, eligible_vectors[second])
                )
                if any(
                    weight > capacity
                    for weight, capacity in zip(pair, capacities)
                ):
                    continue
                for third in range(second + 1, eligible_count):
                    triple = tuple(
                        partial + weight
                        for partial, weight in zip(pair, eligible_vectors[third])
                    )
                    if any(
                        weight > capacity
                        for weight, capacity in zip(triple, capacities)
                    ):
                        continue
                    for fourth in range(third + 1, eligible_count):
                        quadruple = tuple(
                            partial + weight
                            for partial, weight in zip(
                                triple, eligible_vectors[fourth]
                            )
                        )
                        if any(
                            weight > capacity
                            for weight, capacity in zip(quadruple, capacities)
                        ):
                            continue
                        mitm_quadruples += 1
                        target = tuple(
                            capacity - weight
                            for capacity, weight in zip(capacities, quadruple)
                        )
                        quadruple_indices = (first, second, third, fourth)
                        disjoint_triple = next((
                            candidate_triple
                            for candidate_triple in triple_sums.get(target, ())
                            if all(
                                index not in quadruple_indices
                                for index in candidate_triple
                            )
                        ), None)
                        if disjoint_triple is not None:
                            chosen = tuple(
                                original_indices[index]
                                for index in (*quadruple_indices, *disjoint_triple)
                            )
                            break
                    if chosen is not None:
                        break
                if chosen is not None:
                    break
            if chosen is not None:
                break
    if chosen is fallback:
        return {
            "result": "unknown", "chosen_indices": None,
            "nodes": nodes, "failed_states": len(failed),
            "eligible_placements": eligible_count,
            "used_mitm": True, "mitm_pairs": mitm_pairs,
            "mitm_triples": mitm_triples, "mitm_quadruples": mitm_quadruples,
        }
    return {
        "result": "sat" if chosen is not None else "unsat",
        "chosen_indices": [0, *chosen] if chosen is not None else None,
        "nodes": nodes,
        "failed_states": len(failed),
        "eligible_placements": eligible_count,
        "used_mitm": used_mitm,
        "mitm_pairs": mitm_pairs,
        "mitm_triples": mitm_triples,
        "mitm_quadruples": mitm_quadruples,
    }


def screen_candidate(record: dict, args) -> dict:
    started = time.monotonic()
    occupancy = record_occupancy(record)
    tile_orientations = orientations(occupancy)
    weight = sum(occupancy.values())
    hnf_visited = 0
    solver_unknown = 0
    exact_multicover_nodes = 0
    exact_multicover_failed_states = 0
    exact_multicover_mitm_fallbacks = 0
    exact_multicover_mitm_pairs = 0
    exact_multicover_mitm_triples = 0
    exact_multicover_mitm_quadruples = 0
    hnf_covered = 0
    exhausted_by_copies: dict[str, int] = {}
    for copies in range(args.min_copies, args.max_copies + 1):
        numerator = weight * copies
        if numerator % 48:
            continue
        determinant = numerator // 48
        all_candidates = hnf_candidates(determinant)
        orbit_mode = bool(getattr(args, "hnf_orbit_representatives", False))
        orbit_records = hnf_orbits(determinant) if orbit_mode else None
        search_records = orbit_records if orbit_mode else [{
            "representative_index": index,
            "representative_hnf": hnf,
            "member_indices": [index],
        } for index, hnf in enumerate(all_candidates)]
        hnf_start = max(0, getattr(args, "hnf_start", 0))
        configured_stop = getattr(args, "hnf_stop", 0)
        hnf_stop = min(
            len(search_records),
            configured_stop if configured_stop else len(search_records),
        )
        if hnf_start >= hnf_stop:
            raise ValueError("empty HNF range")
        candidates = search_records[hnf_start:hnf_stop]
        copy_unknown = 0
        for local_hnf_index, hnf_record in enumerate(candidates):
            hnf = tuple(hnf_record["representative_hnf"])
            hnf_index = hnf_record["representative_index"]
            hnf_visited += 1
            placements = []
            for orientation_index, orientation in enumerate(tile_orientations):
                for x in range(hnf[0]):
                    for y in range(hnf[3]):
                        for z in range(hnf[5]):
                            vector = [0] * determinant
                            for point, point_weight in orientation["occupancy"].items():
                                translated = (point[0] + x, point[1] + y, point[2] + z)
                                vector[quotient_index(translated, hnf)] += point_weight
                            placements.append({
                                "orientation_index": orientation_index,
                                "translation": (x, y, z),
                                "weights": vector,
                            })

            # Translation and global proper-layer rotation allow an arbitrary
            # tiling copy to be fixed as the identity placement at the origin.
            # The one- and two-copy cases are complete vector/complement tests;
            # only larger motifs need a pseudo-Boolean solver.
            chosen_indices = None
            if copies == 1:
                chosen_indices = [0] if all(weight == 48 for weight in placements[0]["weights"]) else None
                result = sat if chosen_indices else unsat
                model = None
                variables = []
            elif copies == 2:
                complement = tuple(48 - weight for weight in placements[0]["weights"])
                match = next((
                    index for index, placement in enumerate(placements)
                    if index != 0 and tuple(placement["weights"]) == complement
                ), None)
                chosen_indices = [0, match] if match is not None else None
                result = sat if chosen_indices else unsat
                model = None
                variables = []
            elif copies in (3, 4):
                complement = tuple(48 - weight for weight in placements[0]["weights"])
                eligible = [
                    index for index, placement in enumerate(placements)
                    if index != 0 and all(
                        weight <= complement[residue]
                        for residue, weight in enumerate(placement["weights"])
                    )
                ]
                pair_sums: dict[tuple[int, ...], list[tuple[int, int]]] = {}
                for left_offset, left in enumerate(eligible):
                    left_weights = placements[left]["weights"]
                    for right in eligible[left_offset + 1:]:
                        summed = tuple(
                            left_weights[residue] + placements[right]["weights"][residue]
                            for residue in range(determinant)
                        )
                        if any(summed[residue] > complement[residue] for residue in range(determinant)):
                            continue
                        pair_sums.setdefault(summed, []).append((left, right))
                if copies == 3:
                    pair = next(iter(pair_sums.get(complement, [])), None)
                    chosen_indices = [0, *pair] if pair else None
                else:
                    chosen_indices = None
                    for third in eligible:
                        target = tuple(
                            complement[residue] - placements[third]["weights"][residue]
                            for residue in range(determinant)
                        )
                        pair = next((
                            pair for pair in pair_sums.get(target, [])
                            if third not in pair
                        ), None)
                        if pair:
                            chosen_indices = [0, pair[0], pair[1], third]
                            break
                result = sat if chosen_indices else unsat
                model = None
                variables = []
            elif getattr(args, "solver", "exact") == "exact":
                exact_result = exact_weighted_multicover(
                    placements, copies,
                    getattr(args, "exact_node_limit", 0) or None,
                )
                exact_multicover_nodes += exact_result["nodes"]
                exact_multicover_failed_states += exact_result["failed_states"]
                exact_multicover_mitm_fallbacks += int(exact_result["used_mitm"])
                exact_multicover_mitm_pairs += exact_result["mitm_pairs"]
                exact_multicover_mitm_triples += exact_result["mitm_triples"]
                exact_multicover_mitm_quadruples += exact_result["mitm_quadruples"]
                chosen_indices = exact_result["chosen_indices"]
                result = (sat if exact_result["result"] == "sat" else
                          unsat if exact_result["result"] == "unsat" else None)
                model = None
                variables = []
            else:
                variables = [Bool(f"p_{copies}_{hnf_index}_{index}") for index in range(len(placements))]
                solver = SolverFor("QF_FD") if args.solver == "qffd" else Solver()
                solver.set(timeout=args.hnf_timeout_ms)
                solver.add(variables[0])
                if args.solver == "qffd":
                    solver.add(PbEq([(variable, 1) for variable in variables], copies))
                else:
                    solver.add(Sum([If(variable, 1, 0) for variable in variables]) == copies)
                for residue in range(determinant):
                    if args.solver == "qffd":
                        solver.add(PbEq([
                            (variable, placement["weights"][residue])
                            for variable, placement in zip(variables, placements)
                            if placement["weights"][residue]
                        ], 48))
                    else:
                        solver.add(Sum([
                            If(variable, placement["weights"][residue], 0)
                            for variable, placement in zip(variables, placements)
                        ]) == 48)
                result = solver.check()
                model = solver.model() if result == sat else None
            if result == sat:
                if chosen_indices is None:
                    chosen_indices = [
                        index for index, variable in enumerate(variables)
                        if is_true(model.eval(variable))
                    ]
                chosen = [
                    {
                        "orientation_index": placement["orientation_index"],
                        "translation": list(placement["translation"]),
                    }
                    for index, placement in enumerate(placements)
                    if index in chosen_indices
                ]
                certificate = {
                    "kind": "weighted_periodic_hnf_quotient",
                    "certified": True,
                    "can_tile": True,
                    "model": record.get("model", "a2_layered_lattice_function"),
                    "copies": copies,
                    "determinant": determinant,
                    "period_vectors": [list(vector) for vector in period_vectors(hnf)],
                    "placements": chosen,
                    "hnf_index": hnf_index,
                }
                replay = replay_certificate(tile_orientations, certificate)
                if not replay["verified"]:
                    raise RuntimeError(f"certificate replay failed: {replay}")
                return {
                    **record,
                    "classification": "periodic",
                    "periodic_z3": {
                        "certificate": certificate,
                        "replay": replay,
                        "hnf_visited": hnf_visited,
                        "hnf_covered": hnf_covered + len(hnf_record["member_indices"]),
                        "hnf_orbit_representatives": orbit_mode,
                        "hnf_orbit_total": len(orbit_records) if orbit_mode else None,
                        "solver_unknown": solver_unknown,
                        "exact_multicover_nodes": exact_multicover_nodes,
                        "exact_multicover_failed_states": exact_multicover_failed_states,
                        "exact_multicover_mitm_fallbacks": exact_multicover_mitm_fallbacks,
                        "exact_multicover_mitm_pairs": exact_multicover_mitm_pairs,
                        "exact_multicover_mitm_triples": exact_multicover_mitm_triples,
                        "exact_multicover_mitm_quadruples": exact_multicover_mitm_quadruples,
                        "hnf_range": [hnf_start, hnf_stop],
                        "hnf_total": len(all_candidates),
                        "hnf_range_exhausted": False,
                        "exhausted_by_copies": exhausted_by_copies,
                        "milliseconds": round((time.monotonic() - started) * 1000),
                    },
                }
            if result != unsat:
                solver_unknown += 1
                copy_unknown += 1
            else:
                hnf_covered += len(hnf_record["member_indices"])
            progress_every_hnf = getattr(args, "progress_every_hnf", 0)
            if progress_every_hnf and hnf_visited % progress_every_hnf == 0:
                print(
                    f"{record['id']} copies={copies} "
                    f"{'orbit' if orbit_mode else 'hnf'}={hnf_start + local_hnf_index + 1}/{len(search_records)} "
                    f"nodes={exact_multicover_nodes} failed={exact_multicover_failed_states} "
                    f"elapsed_s={round(time.monotonic() - started, 1)}",
                    flush=True,
                )
            if args.candidate_time_ms and (time.monotonic() - started) * 1000 >= args.candidate_time_ms:
                return {
                    **record,
                    "classification": "unresolved",
                    "periodic_z3": {
                        "stopped_by": "candidate_time_limit",
                        "active_copies": copies,
                        "hnf_visited": hnf_visited,
                        "hnf_covered": hnf_covered,
                        "hnf_orbit_representatives": orbit_mode,
                        "hnf_orbit_total": len(orbit_records) if orbit_mode else None,
                        "solver_unknown": solver_unknown,
                        "exact_multicover_nodes": exact_multicover_nodes,
                        "exact_multicover_failed_states": exact_multicover_failed_states,
                        "exact_multicover_mitm_fallbacks": exact_multicover_mitm_fallbacks,
                        "exact_multicover_mitm_pairs": exact_multicover_mitm_pairs,
                        "exact_multicover_mitm_triples": exact_multicover_mitm_triples,
                        "exact_multicover_mitm_quadruples": exact_multicover_mitm_quadruples,
                        "hnf_range": [hnf_start, hnf_stop],
                        "hnf_total": len(all_candidates),
                        "hnf_range_exhausted": False,
                        "exhausted_by_copies": exhausted_by_copies,
                        "milliseconds": round((time.monotonic() - started) * 1000),
                    },
                }
        if copy_unknown == 0 and hnf_start == 0 and hnf_stop == len(search_records):
            exhausted_by_copies[str(copies)] = len(all_candidates)
    return {
        **record,
        "classification": "unresolved",
        "periodic_z3": {
            "stopped_by": None,
            "hnf_visited": hnf_visited,
            "hnf_covered": hnf_covered,
            "hnf_orbit_representatives": orbit_mode,
            "hnf_orbit_total": len(orbit_records) if orbit_mode else None,
            "solver_unknown": solver_unknown,
            "exact_multicover_nodes": exact_multicover_nodes,
            "exact_multicover_failed_states": exact_multicover_failed_states,
            "exact_multicover_mitm_fallbacks": exact_multicover_mitm_fallbacks,
            "exact_multicover_mitm_pairs": exact_multicover_mitm_pairs,
            "exact_multicover_mitm_triples": exact_multicover_mitm_triples,
            "exact_multicover_mitm_quadruples": exact_multicover_mitm_quadruples,
            "hnf_range": [hnf_start, hnf_stop],
            "hnf_total": len(all_candidates),
            "hnf_range_exhausted": solver_unknown == 0
            and hnf_start == 0 and hnf_stop == len(search_records),
            "exhausted_by_copies": exhausted_by_copies,
            "milliseconds": round((time.monotonic() - started) * 1000),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-copies", type=int, default=1)
    parser.add_argument("--max-copies", type=int, default=6)
    parser.add_argument("--hnf-timeout-ms", type=int, default=5000)
    parser.add_argument("--candidate-time-ms", type=int, default=0)
    parser.add_argument("--solver", choices=("exact", "default", "qffd"), default="exact")
    parser.add_argument("--exact-node-limit", type=int, default=0)
    parser.add_argument("--progress-every-hnf", type=int, default=0)
    parser.add_argument(
        "--progress-every-candidate",
        type=int,
        default=1,
        help="print one candidate result every N records; use 0 for summary only",
    )
    parser.add_argument("--hnf-orbit-representatives", action="store_true")
    parser.add_argument("--hnf-start", type=int, default=0)
    parser.add_argument("--hnf-stop", type=int, default=0)
    parser.add_argument("--only-unresolved", action="store_true")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    if args.min_copies < 1 or args.max_copies < args.min_copies:
        parser.error("invalid copy range")

    records = read_ndjson(Path(args.input))
    if args.only_unresolved:
        records = [record for record in records if record.get("classification") == "unresolved"]
    records = records[max(0, args.offset):]
    if args.limit > 0:
        records = records[:args.limit]
    output = Path(args.output)
    output.write_text("")
    counts = {"periodic": 0, "unresolved": 0}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            screened = screen_candidate(record, args)
            counts[screened["classification"]] += 1
            stream.write(json.dumps(screened, separators=(",", ":")) + "\n")
            stream.flush()
            certificate = screened["periodic_z3"].get("certificate")
            suffix = f" {certificate['copies']}-copy det={certificate['determinant']}" if certificate else ""
            if args.progress_every_candidate and (
                index % args.progress_every_candidate == 0 or index == len(records)
            ):
                print(
                    f"{index}/{len(records)} {record['id']} "
                    f"{screened['classification']}{suffix}",
                    flush=True,
                )
    print(json.dumps({"records": len(records), **counts, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
