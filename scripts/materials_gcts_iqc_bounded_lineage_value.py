#!/usr/bin/env python3
"""Grouped target-blind value for complete bounded IQC lineages.

The candidate universe is the exact union of the four completed consumed
receipts and the later bounded joint confirmation receipt.  Every candidate
is frozen before a consumed target is opened.  Features use only public seed
geometry, the three unordered three-site action blocks, and the already-frozen
joint/base prefix scores.  They contain no raw type/candidate IDs, absolute
coordinates, lattice/module coordinates, material label, or target sites.

The outer audit leaves out an entire nucleus.  Representation and ridge are
selected by another grouped leave-one-nucleus-out loop inside the remaining
groups.  Complete within-nucleus label shuffles preserve exact-lineage counts
and refit the same nested procedure.  This is development evidence; a passing
gate would still require a separately preregistered disjoint confirmation.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import pickle
import random
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from materials_gcts_iqc_bounded_lineage_completion import (
    EXPECTED_RESULT_DIGEST as COMPLETION_RESULT_DIGEST,
    load_default_result as load_completion)
from materials_gcts_iqc_joint_child_action_marking_fit import CASES
from materials_gcts_iqc_frozen_fusion_runtime import (
    INCIDENCE_NAMES, PARTIAL_NAMES, SECTION_NAMES, _local_section, _partial,
    load_default_runtime)
from materials_gcts_icosahedral_modelset import oracle_crop_fast
from materials_gcts_iqc_three_block_portfolio_execution import _prepare_pool


ROOT = Path(__file__).resolve().parent
FRESH_CASE = (
    "fresh-bounded-joint",
    "fixtures/iqc_lazy_joint_confirmation_v1.json.gz",
    (160., -180., -140.))
POSITION_TOLERANCE = 1e-5
RIDGES = (1., 10., 100.)
SHUFFLES = 31
CANDIDATE_SCOPE = "joint-child-per-parent"
SELECTION_MODES = ("global-lineage", "parent-conditional")
DEFAULT_FIXTURE = ROOT / "fixtures/iqc_bounded_lineage_value_v1.json.gz"
DEVELOPMENT_FEATURE_CACHE = Path(
    "/tmp/gcts_iqc_joint_lineage_features_v1.pkl.gz")
EXPECTED_FIXTURE_SHA256 = (
    "8e80474205d4330c827d6612e444bd50a0781d7d9eeeaf877bae0e8c0846aecd")
EXPECTED_RESULT_DIGEST = (
    "847164eb90d27cb2afb0305b6bb29d51c74152706a0a554fc1a483581cac89c6")


@dataclass(frozen=True)
class Example:
    group: int
    nucleus: str
    parent: int
    features: tuple[float, ...]
    colors: tuple[str, ...]
    tie_key: tuple
    graphs: tuple
    exact: bool


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def _summary(values):
    values = tuple(sorted(map(float, values)))
    if not values:
        return (0., 0., 0., 0.)
    return (values[0], values[(len(values) - 1) // 2],
            sum(values) / len(values), values[-1])


def _median_nearest_neighbor(points):
    nearest = []
    for index, point in enumerate(points):
        nearest.append(min(math.dist(point, other)
                           for other_index, other in enumerate(points)
                           if other_index != index))
    nearest.sort()
    return nearest[len(nearest) // 2]


def _pair_distances(points, scale):
    return tuple(sorted(math.dist(points[left], points[right]) / scale
                        for left in range(len(points))
                        for right in range(left + 1, len(points))))


def _triangle_area(points, scale):
    first = tuple(points[1][axis] - points[0][axis] for axis in range(3))
    second = tuple(points[2][axis] - points[0][axis] for axis in range(3))
    cross = (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0])
    return .5 * math.sqrt(sum(value * value for value in cross)) / scale ** 2


def _block_seed_features(actions, seed_positions, seed_species, scale):
    nearest = {kind: [] for kind in ("all", "same", "different")}
    counts = []
    for point, color in actions:
        distances = tuple((math.dist(point, seed) / scale, species)
                          for seed, species in zip(
                              seed_positions, seed_species))
        categories = {
            "all": tuple(distance for distance, _species in distances),
            "same": tuple(distance for distance, species in distances
                          if species == color),
            "different": tuple(distance for distance, species in distances
                               if species != color),
        }
        for kind, values in categories.items():
            nearest[kind].extend(sorted(values)[:2])
        row = []
        for radius in (1.25, 2.25, 3.5):
            row.extend((
                sum(distance <= radius for distance, species in distances
                    if species == color),
                sum(distance <= radius for distance, species in distances
                    if species != color)))
        counts.append(tuple(row))
    result = []
    for kind in ("all", "same", "different"):
        result.extend(sorted(nearest[kind]))
    for column in range(6):
        result.extend(_summary(row[column] for row in counts))
    return tuple(result)


def _feature_schema():
    names = [
        "prefix:joint-score", "prefix:base-score",
        "prefix:joint-reciprocal-rank", "prefix:base-reciprocal-rank",
        "prefix:selected-by-joint", "prefix:selected-by-base"]
    groups = ["prefix"] * len(names)
    for block in range(3):
        block_names = (
            *(f"block{block}:radius:{index}" for index in range(3)),
            *(f"block{block}:pair:{index}" for index in range(3)),
            f"block{block}:triangle-area",
            *(f"block{block}:color:{color}" for color in "XYZ"))
        names.extend(block_names)
        groups.extend(["shape"] * len(block_names))
    for first, second in ((0, 1), (0, 2), (1, 2)):
        cross_names = tuple(
            f"cross{first}{second}:distance:{index}" for index in range(9))
        names.extend(cross_names)
        groups.extend(["shape"] * len(cross_names))
        for kind in ("same", "different"):
            summary_names = tuple(
                f"cross{first}{second}:{kind}:{field}"
                for field in ("min", "median", "mean", "max"))
            names.extend(summary_names)
            groups.extend(["shape"] * len(summary_names))
    names.extend(f"lineage:pair:{index}" for index in range(36))
    groups.extend(["shape"] * 36)
    names.extend(f"lineage:radius:{index}" for index in range(9))
    groups.extend(["shape"] * 9)
    for block in range(3):
        for kind in ("all", "same", "different"):
            local_names = tuple(
                f"block{block}:seed:{kind}:nearest:{index}"
                for index in range(6))
            names.extend(local_names)
            groups.extend(["section"] * len(local_names))
        for column in range(6):
            count_names = tuple(
                f"block{block}:seed-count:{column}:{field}"
                for field in ("min", "median", "mean", "max"))
            names.extend(count_names)
            groups.extend(["section"] * len(count_names))
    graph_names = (
        "graph:nodes", "graph:overlap-edges", "graph:isolated-nodes",
        "graph:witnessed-incidence", "graph:chirality-negative",
        "graph:chirality-zero", "graph:chirality-positive",
        "graph:shared-species-atoms")
    for block in range(3):
        transported_names = (
            *(f"stage{block}:transported:{name}" for name in SECTION_NAMES),
            *(f"stage{block}:transported:{name}" for name in
              PARTIAL_NAMES + INCIDENCE_NAMES),
            *(f"stage{block}:transported:{name}" for name in graph_names))
        names.extend(transported_names)
        groups.extend(["transported"] * len(transported_names))
    return tuple(names), tuple(groups)


FEATURE_NAMES, FEATURE_GROUPS = _feature_schema()
REPRESENTATIONS = (
    ("shape", tuple(index for index, group in enumerate(FEATURE_GROUPS)
                    if group == "shape")),
    ("shape+prefix", tuple(index for index, group in enumerate(FEATURE_GROUPS)
                           if group in ("shape", "prefix"))),
    ("shape+section", tuple(index for index, group in enumerate(FEATURE_GROUPS)
                            if group in ("shape", "section"))),
    ("transported", tuple(index for index, group in enumerate(FEATURE_GROUPS)
                          if group == "transported")),
    ("shape+transported", tuple(
        index for index, group in enumerate(FEATURE_GROUPS)
        if group in ("shape", "transported"))),
    ("all", tuple(range(len(FEATURE_NAMES)))),
)


def lineage_features(*, actions, center, seed_positions, seed_species,
                     prefix_row, scale=None, section_cache=None,
                     transported_features=()):
    if len(actions) != 9:
        raise ValueError("bounded lineage must contain nine actions")
    actions = tuple((tuple(map(float, point)), str(color))
                    for point, color in actions)
    blocks = tuple(actions[start:start + 3] for start in (0, 3, 6))
    scale = (_median_nearest_neighbor(seed_positions) if scale is None
             else float(scale))
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("invalid seed nearest-neighbor scale")
    sources = tuple(map(str, prefix_row[2]))
    values = [
        float(prefix_row[4]), float(prefix_row[6]),
        1. / float(prefix_row[3]), 1. / float(prefix_row[5]),
        float("joint" in sources), float("base" in sources)]
    for block in blocks:
        points = tuple(point for point, _color in block)
        values.extend(sorted(math.dist(point, center) / scale
                             for point in points))
        values.extend(_pair_distances(points, scale))
        values.append(_triangle_area(points, scale))
        values.extend(sum(color == wanted for _point, color in block) / 3.
                      for wanted in "XYZ")
    for first, second in ((0, 1), (0, 2), (1, 2)):
        distances = tuple(math.dist(left[0], right[0]) / scale
                          for left in blocks[first]
                          for right in blocks[second])
        values.extend(sorted(distances))
        same = tuple(math.dist(left[0], right[0]) / scale
                     for left in blocks[first] for right in blocks[second]
                     if left[1] == right[1])
        different = tuple(math.dist(left[0], right[0]) / scale
                          for left in blocks[first]
                          for right in blocks[second]
                          if left[1] != right[1])
        values.extend(_summary(same))
        values.extend(_summary(different))
    points = tuple(point for point, _color in actions)
    values.extend(_pair_distances(points, scale))
    values.extend(sorted(math.dist(point, center) / scale
                         for point in points))
    for block in blocks:
        cache_key = tuple(block)
        section = None if section_cache is None else section_cache.get(
            cache_key)
        if section is None:
            section = _block_seed_features(
                block, seed_positions, seed_species, scale)
            if section_cache is not None:
                section_cache[cache_key] = section
        values.extend(section)
    values.extend(map(float, transported_features))
    result = tuple(values)
    if len(result) != len(FEATURE_NAMES) or any(
            not math.isfinite(value) for value in result):
        raise AssertionError("bounded lineage feature schema drift")
    return result


def _transported_stage_features(*, seed_positions, seed_species,
                                prior_actions, block_actions, runtime):
    occupied_positions = tuple(seed_positions) + tuple(
        point for point, _color in prior_actions)
    occupied_species = tuple(seed_species) + tuple(
        color for _point, color in prior_actions)
    positions = occupied_positions + tuple(
        point for point, _color in block_actions)
    species = occupied_species + tuple(
        color for _point, color in block_actions)
    state = SimpleNamespace(
        positions=positions, species=species, actions=tuple(block_actions))
    source = SimpleNamespace(
        seed_positions=occupied_positions, seed_species=occupied_species)
    partial, graph = _partial(
        source, state, runtime["grouped_vocabulary"])
    incidence = tuple(graph.incidence_edges)
    graph_features = (
        float(len(graph.nodes)), float(len(graph.edges)),
        float(graph.isolated_nodes),
        float(sum(edge.connection_witnessed for edge in incidence)),
        float(sum(edge.chirality < 0 for edge in incidence)),
        float(sum(edge.chirality == 0 for edge in incidence)),
        float(sum(edge.chirality > 0 for edge in incidence)),
        float(sum(count for edge in graph.edges
                  for _species, count in edge.shared_species)),
    )
    values = tuple(_local_section(state)) + tuple(partial) + graph_features
    expected = len(SECTION_NAMES) + len(PARTIAL_NAMES) + \
        len(INCIDENCE_NAMES) + 8
    if len(values) != expected or any(not math.isfinite(value)
                                      for value in values):
        raise AssertionError("transported stage feature schema drift")
    return values, graph


def _load_source(relative):
    raw = (ROOT / relative).read_bytes()
    return raw, json.loads(gzip.decompress(raw))


def _candidate_case(payload):
    group, (name, relative, center), completed = payload
    runtime = load_default_runtime()
    source_raw, source = _load_source(relative)
    receipt = source["receipt"]
    selected_rows = tuple(receipt.get("selected_prefix_rows", ()))
    if not selected_rows:
        if completed is None:
            raise AssertionError("old receipt lacks completion metadata")
        # The old receipt has no bounded schedule row. Reconstruct the exact
        # schedule metadata from its frozen branches and seed.
        from materials_gcts_joint_prefix_schedule import (
            load_default_schedule, schedule_prefixes)
        schedule, _artifact = load_default_schedule()
        seed, _ = oracle_crop_fast(center, 9.)
        scheduled = schedule_prefixes(
            schedule=schedule, seed_positions=seed.positions,
            seed_species=seed.species,
            branches=tuple(SimpleNamespace(**row)
                           for row in receipt["second_branches"]))
        selected_rows = tuple(scheduled["selected_rows"])
    selected = {(int(row[0]), int(row[1])): tuple(row)
                for row in selected_rows if "joint" in tuple(map(str, row[2]))}
    if len(selected) != 8 or {parent for parent, _child in selected} != \
            set(range(1, 9)):
        raise AssertionError("joint lineage scope must retain one child per parent")
    seed, _ = oracle_crop_fast(center, 9.)
    seed_scale = _median_nearest_neighbor(seed.positions)
    section_cache = {}
    transported_cache = {}
    candidates = []
    for lineage in receipt["lineages"]:
        pair = (int(lineage["parent_id"]),
                int(lineage["child_stable_index"]))
        if pair in selected:
            candidates.append(lineage)
    if completed is not None:
        for row in completed["generated"]:
            candidates.extend(row["lineages"])
    unique = {}
    for lineage in candidates:
        pair = (int(lineage["parent_id"]),
                int(lineage["child_stable_index"]))
        if pair not in selected:
            continue
        action_key = tuple((tuple(map(float, point)), str(color))
                           for point, color in lineage["all_actions"])
        unique[(pair, action_key)] = lineage
    candidates = tuple(unique[key] for key in sorted(unique, key=repr))
    pairs = {(int(row["parent_id"]), int(row["child_stable_index"]))
             for row in candidates}
    if pairs != set(selected):
        raise AssertionError("bounded lineage candidate pair incomplete")
    feature_rows = []
    for lineage in candidates:
        pair = (int(lineage["parent_id"]),
                int(lineage["child_stable_index"]))
        actions = tuple((tuple(map(float, point)), str(color))
                        for point, color in lineage["all_actions"])
        blocks = tuple(actions[start:start + 3]
                       for start in (0, 3, 6))
        transported = []
        stage_graphs = []
        prior = ()
        for block in blocks:
            cache_key = (prior, block)
            stage = transported_cache.get(cache_key)
            if stage is None:
                stage = _transported_stage_features(
                    seed_positions=seed.positions,
                    seed_species=seed.species, prior_actions=prior,
                    block_actions=block, runtime=runtime)
                transported_cache[cache_key] = stage
            values, graph = stage
            transported.extend(values)
            stage_graphs.append(graph)
            prior += block
        feature_rows.append((
            int(lineage["parent_id"]),
            lineage_features(
                actions=actions, center=center,
                seed_positions=seed.positions,
                seed_species=seed.species,
                prefix_row=selected[pair], scale=seed_scale,
                section_cache=section_cache,
                transported_features=tuple(transported)),
            tuple(color for _point, color in actions), actions,
            tuple(stage_graphs)))
    candidate_digest = hashlib.sha256(repr(tuple(
        row[3] for row in feature_rows)).encode()).hexdigest()
    return {
        "group": group, "name": name, "center": tuple(center),
        "source_fixture_sha256": hashlib.sha256(source_raw).hexdigest(),
        "radii": tuple(map(float, receipt["radii"])),
        "seed_atoms": len(seed.positions), "rows": tuple(feature_rows),
        "candidate_digest": candidate_digest,
        "target_used_before_candidate_freeze": False,
    }


def _candidate_rows(workers=4):
    completion = load_completion()
    if completion["result_digest"] != COMPLETION_RESULT_DIGEST:
        raise AssertionError("bounded lineage completion source drift")
    completed_by_name = {row["name"]: row
                         for row in completion["cases"]}
    cases = tuple(CASES) + (FRESH_CASE,)
    source_shas = tuple(hashlib.sha256(
        (ROOT / case[1]).read_bytes()).hexdigest() for case in cases)
    cache_key = hashlib.sha256(repr((
        FEATURE_NAMES, CANDIDATE_SCOPE, "stage-graphs-v1",
        completion["result_digest"],
        source_shas)).encode()).hexdigest()
    if DEVELOPMENT_FEATURE_CACHE.exists():
        cached_key, cached_groups = pickle.loads(gzip.decompress(
            DEVELOPMENT_FEATURE_CACHE.read_bytes()))
        if cached_key == cache_key:
            return tuple(cached_groups), completion
    payloads = tuple((group, case, completed_by_name.get(case[0]))
                     for group, case in enumerate(cases))
    if workers == 1:
        groups = tuple(_candidate_case(payload) for payload in payloads)
    else:
        _prepare_pool()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            groups = tuple(pool.map(_candidate_case, payloads))
    groups = tuple(sorted(groups, key=lambda row: row["group"]))
    DEVELOPMENT_FEATURE_CACHE.write_bytes(gzip.compress(
        pickle.dumps((cache_key, groups), protocol=5), compresslevel=6,
        mtime=0))
    return groups, completion


def _truth_index(positions, species):
    cells = {}
    for point, color in zip(positions, species):
        key = tuple(math.floor(float(value) / POSITION_TOLERANCE)
                    for value in point)
        cells.setdefault((str(color), key), []).append(
            tuple(map(float, point)))
    return cells


def _correct(point, color, truth):
    key = tuple(math.floor(float(value) / POSITION_TOLERANCE)
                for value in point)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for candidate in truth.get((str(color), (
                        key[0] + dx, key[1] + dy, key[2] + dz)), ()):
                    if math.dist(point, candidate) <= POSITION_TOLERANCE:
                        return True
    return False


def load_examples():
    candidate_groups, completion = _candidate_rows()
    frozen_digest = hashlib.sha256(repr(tuple(
        (row["name"], row["candidate_digest"])
        for row in candidate_groups)).encode()).hexdigest()
    examples = []
    audits = []
    for row in candidate_groups:
        # These are all consumed development/confirmation targets.  They are
        # opened only after the complete candidate feature receipt above is
        # immutable.
        target, _ = oracle_crop_fast(row["center"], row["radii"][2])
        truth = _truth_index(target.positions, target.species)
        positives = 0
        for parent, features, colors, actions, graphs in row["rows"]:
            exact = all(_correct(point, color, truth)
                        for point, color in actions)
            positives += exact
            examples.append(Example(
                row["group"], row["name"], parent, features, colors,
                actions, graphs, exact))
        audits.append({
            key: row[key] for key in (
                "group", "name", "center", "source_fixture_sha256",
                "radii", "seed_atoms", "candidate_digest",
                "target_used_before_candidate_freeze")
        } | {"candidates": len(row["rows"]),
             "exact_lineages": positives,
             "target_opened_after_candidate_freeze": True})
    if frozen_digest != hashlib.sha256(repr(tuple(
            (row["name"], row["candidate_digest"])
            for row in candidate_groups)).encode()).hexdigest():
        raise AssertionError("candidate receipt mutated after target open")
    return tuple(examples), tuple(audits), frozen_digest, completion


def _fit(rows, indices, ridge, mode="global-lineage"):
    import numpy as np
    matrix = np.asarray([[row.features[index] for index in indices]
                         for row in rows], dtype=float)
    means = matrix.mean(axis=0)
    scales = matrix.std(axis=0)
    scales[scales < 1e-9] = 1.
    normalized = (matrix - means) / scales
    contrasts = []
    strata = (tuple(sorted({(row.group, row.parent) for row in rows}))
              if mode == "parent-conditional" else
              tuple((group, None)
                    for group in sorted({row.group for row in rows})))
    for group, parent in strata:
        mask = np.asarray([row.group == group and
                           (parent is None or row.parent == parent)
                           for row in rows])
        labels = np.asarray([row.exact for row in rows])
        positive = normalized[mask & labels]
        negative = normalized[mask & ~labels]
        if not len(positive) or not len(negative):
            if mode == "parent-conditional":
                continue
            raise ValueError("every fitted lineage group needs both labels")
        contrasts.append(positive.mean(axis=0) - negative.mean(axis=0))
    if len(contrasts) < 3:
        raise ValueError("lineage value needs three contrasted strata")
    contrasts = np.asarray(contrasts)
    average = contrasts.mean(axis=0)
    dispersion = ((contrasts - average) ** 2).mean(axis=0)
    weights = average / (ridge + dispersion)
    return means, scales, weights


def _scores(model, rows, indices):
    import numpy as np
    means, scales, weights = model
    matrix = np.asarray([[row.features[index] for index in indices]
                         for row in rows], dtype=float)
    return tuple(map(float, ((matrix - means) / scales) @ weights))


def _rank(model, rows, indices, mode="global-lineage"):
    scores = _scores(model, rows, indices)
    full_order = tuple(sorted(range(len(rows)), key=lambda index: (
        -scores[index], repr(rows[index].tie_key))))
    if mode == "parent-conditional":
        parent_tops = []
        for parent in sorted({row.parent for row in rows}):
            indices_for_parent = tuple(index for index, row in enumerate(rows)
                                       if row.parent == parent)
            parent_tops.append(min(indices_for_parent, key=lambda index: (
                -scores[index], repr(rows[index].tie_key))))
        order = tuple(sorted(parent_tops, key=lambda index: (
            -scores[index], repr(rows[index].tie_key))))
    else:
        order = full_order
    first_exact = next((rank for rank, index in enumerate(full_order, 1)
                        if rows[index].exact), None)
    return bool(rows[order[0]].exact), first_exact, order[0], scores[order[0]]


def _capacity(rows, mode, representation, ridge):
    selected = supplied = rank_sum = 0
    for group in sorted({row.group for row in rows}):
        training = tuple(row for row in rows if row.group != group)
        held = tuple(row for row in rows if row.group == group)
        if not any(row.exact for row in held):
            continue
        supplied += 1
        exact, rank, _index, _score = _rank(
            _fit(training, representation[1], ridge, mode), held,
            representation[1], mode)
        selected += exact
        rank_sum += rank or len(held) + 1
    return (mode, representation[0], ridge, supplied, selected, rank_sum)


def _select_capacity(rows):
    capacities = tuple(_capacity(rows, mode, representation, ridge)
                       for mode in SELECTION_MODES
                       for representation in REPRESENTATIONS
                       for ridge in RIDGES)
    order = {row[0]: index for index, row in enumerate(REPRESENTATIONS)}
    mode_order = {name: index for index, name in enumerate(SELECTION_MODES)}
    selected = min(capacities, key=lambda row: (
        -row[4], -row[3], row[5], mode_order[row[0]],
        order[row[1]], row[2]))
    representation = REPRESENTATIONS[order[selected[1]]]
    return selected, capacities, representation


def _outer(rows):
    folds = []
    for group in sorted({row.group for row in rows}):
        training = tuple(row for row in rows if row.group != group)
        held = tuple(row for row in rows if row.group == group)
        selected, _capacities, representation = _select_capacity(training)
        model = _fit(training, representation[1], selected[2], selected[0])
        exact, rank, index, score = _rank(
            model, held, representation[1], selected[0])
        folds.append({
            "group": group, "nucleus": held[0].nucleus,
            "candidates": len(held),
            "exact_lineages": sum(row.exact for row in held),
            "scope": CANDIDATE_SCOPE,
            "selection_mode": selected[0],
            "representation": representation[0], "ridge": selected[2],
            "selected_exact": exact, "first_exact_rank": rank,
            "selected_parent": held[index].parent,
            "selected_score": score,
        })
    return tuple(folds)


def _shuffle(rows, iteration):
    by_group = {}
    for row in rows:
        by_group.setdefault(row.group, []).append(row)
    shuffled = []
    for group, group_rows in sorted(by_group.items()):
        labels = [row.exact for row in group_rows]
        seed = int(hashlib.sha256(
            f"bounded-lineage-null:{iteration}:{group}".encode()
        ).hexdigest()[:16], 16)
        random.Random(seed).shuffle(labels)
        shuffled.extend(Example(
            row.group, row.nucleus, row.parent, row.features, row.colors,
            row.tie_key, row.graphs, bool(label))
            for row, label in zip(group_rows, labels))
    return tuple(shuffled)


def evaluate(shuffles=SHUFFLES):
    rows, case_audit, candidate_digest, completion = load_examples()
    if len({row.group for row in rows}) != 5 or any(
            not any(row.exact for row in rows if row.group == group)
            for group in {row.group for row in rows}):
        raise AssertionError("bounded lineage corpus lacks grouped supply")
    folds = _outer(rows)
    selected = sum(row["selected_exact"] for row in folds)
    shuffle_rows = []
    for iteration in range(shuffles):
        null_folds = _outer(_shuffle(rows, iteration))
        shuffle_rows.append({
            "iteration": iteration,
            "selected_exact_groups": sum(
                row["selected_exact"] for row in null_folds),
            "first_exact_rank_sum": sum(
                row["first_exact_rank"] or row["candidates"] + 1
                for row in null_folds),
        })
    p_value = ((1 + sum(row["selected_exact_groups"] >= selected
                        for row in shuffle_rows)) /
               (1 + len(shuffle_rows)))
    full_selected, capacities, representation = _select_capacity(rows)
    full_model = _fit(
        rows, representation[1], full_selected[2], full_selected[0])
    means, scales, weights = full_model
    model_payload = (
        CANDIDATE_SCOPE, full_selected[0], representation[0], full_selected[2],
        tuple(map(float, means)),
        tuple(map(float, scales)), tuple(map(float, weights)))
    model_digest = hashlib.sha256(repr(model_payload).encode()).hexdigest()
    body = {
        "schema_version": 1,
        "feature_names": FEATURE_NAMES,
        "feature_count": len(FEATURE_NAMES),
        "representations": tuple((name, len(indices))
                                 for name, indices in REPRESENTATIONS),
        "candidate_scope": CANDIDATE_SCOPE,
        "selection_modes": SELECTION_MODES,
        "ridges": RIDGES,
        "groups": len(case_audit), "examples": len(rows),
        "positive_examples": sum(row.exact for row in rows),
        "cases": case_audit,
        "candidate_digest_frozen_before_targets": candidate_digest,
        "completion_result_digest": completion["result_digest"],
        "outer_folds": folds,
        "outer_selected_exact_groups": selected,
        "outer_supplied_groups": len(folds),
        "outer_first_exact_rank_sum": sum(
            row["first_exact_rank"] or row["candidates"] + 1
            for row in folds),
        "full_capacities": capacities,
        "selected_selection_mode": full_selected[0],
        "selected_representation": representation[0],
        "selected_ridge": full_selected[2],
        "model_digest": model_digest,
        "shuffle_controls": tuple(shuffle_rows),
        "shuffle_p_value": p_value,
        "grouped_winner_gate_passed": bool(
            selected >= 4 and p_value <= .05),
        "candidate_target_used": False,
        "targets_opened_after_candidate_freeze": True,
        "raw_ids_or_absolute_coordinates_in_features": False,
        "lattice_module_family_or_target_fields_in_features": False,
        "development_targets_consumed": True,
        "fresh_confirmation_claimed": False,
        "autonomous_growth_claimed": False,
        "stationary_or_exponential_claimed": False,
    }
    return {**body, "result_digest": hashlib.sha256(
        canonical_json(body)).hexdigest()}


def validate_result(row):
    body = dict(row)
    digest = body.pop("result_digest")
    if (hashlib.sha256(canonical_json(body)).hexdigest() != digest or
            body["schema_version"] != 1 or body["candidate_target_used"] or
            not body["targets_opened_after_candidate_freeze"] or
            body["raw_ids_or_absolute_coordinates_in_features"] or
            body["lattice_module_family_or_target_fields_in_features"] or
            not body["development_targets_consumed"] or
            body["fresh_confirmation_claimed"] or
            body["autonomous_growth_claimed"] or
            body["stationary_or_exponential_claimed"]):
        raise AssertionError("bounded lineage value result drift")
    if EXPECTED_RESULT_DIGEST and digest != EXPECTED_RESULT_DIGEST:
        raise AssertionError("bounded lineage value digest drift")
    return row


def load_default_result(path=DEFAULT_FIXTURE):
    raw = Path(path).read_bytes()
    if EXPECTED_FIXTURE_SHA256 and hashlib.sha256(
            raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise AssertionError("bounded lineage value fixture drift")
    return validate_result(json.loads(gzip.decompress(raw)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--shuffles", type=int, default=SHUFFLES)
    args = parser.parse_args()
    if args.write:
        row = validate_result(evaluate(args.shuffles))
        DEFAULT_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_FIXTURE.write_bytes(gzip.compress(
            (json.dumps(row, indent=2, sort_keys=True) + "\n").encode(),
            compresslevel=9, mtime=0))
    else:
        row = load_default_result()
    print(json.dumps({key: row[key] for key in (
        "groups", "examples", "positive_examples",
        "outer_selected_exact_groups", "outer_supplied_groups",
        "outer_first_exact_rank_sum", "selected_representation",
        "candidate_scope", "selected_selection_mode", "selected_ridge",
        "shuffle_p_value",
        "grouped_winner_gate_passed", "result_digest")},
        indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
