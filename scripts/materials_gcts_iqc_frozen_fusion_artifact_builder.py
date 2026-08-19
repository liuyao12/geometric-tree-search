#!/usr/bin/env python3
"""Migrate the authorized IQC development checkpoints to inert JSON.

This is a provenance tool, not a runtime dependency.  It accepts only the
five named families of pre-existing development caches, verifies the selected
fold-one fusion digest, and writes a compressed explicit-data artifact.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import pickle
import sys
from pathlib import Path

from materials_gcts_equivariant_port_fusion_value import (
    FrozenEquivariantPortFusionValue)
from materials_gcts_grouped_irregular_vocabulary import merge_grouped_vocabulary
from materials_gcts_iqc_frozen_fusion_artifact import (
    canonical_json, runtime_payload)
from materials_gcts_iqc_frozen_fusion_runtime import (
    BRANCH_NAMES, BRANCH_VARIANTS, COLORS, FEATURE_NAMES)
from materials_gcts_iqc_pose_port_state_audit import _examples
from materials_gcts_iqc_pose_port_autonomous_preregistration_v2 import (
    MINIMUM_STATE_GROUPS, MINIMUM_STATE_SUPPORT, MINIMUM_TOKEN_GROUPS,
    MINIMUM_TOKEN_SUPPORT, STATE_BIN_WIDTH, TOKEN_SHRINKAGE)
from materials_gcts_iqc_recurrent_path_selector_audit import _program
from materials_gcts_learned_equivariant_port_value import (
    LearnedEquivariantPortExample, LearnedEquivariantPortSpec,
    fit_learned_equivariant_port_value)
from materials_gcts_portfolio_terminal_value import (
    FrozenPortfolioTerminalValue, PortfolioTerminalExample,
    TerminalRepresentation, portfolio_terminal_value_digest)
from materials_gcts_pose_port_state_marking import fit_pose_port_state_marking
from materials_gcts_recurrent_branch_value import (
    RecurrentBranchExample, _fit)


FOLD = 1
HELDOUT = (11, 16, 21, 26)
VARIANT_NEIGHBORS = (25, 15, 9)
GRAPH_SPEC = LearnedEquivariantPortSpec(
    3, .25, 10., 2, 100, .16, "pairwise")
EXPECTED_FUSION_DIGEST = \
    "505b65481e3fe2cc25a284ba8dc175e3a794465c2c7bd726f5448c1fac6bbef5"


def _sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path):
    with path.open("rb") as stream:
        return pickle.load(stream)


def _branch_models(broad, train):
    result = {}
    for name, indices in BRANCH_VARIANTS.items():
        heads = []
        for depth, neighbors in enumerate(VARIANT_NEIGHBORS):
            rows = tuple(RecurrentBranchExample(
                row.group, tuple(row.features[index] for index in indices),
                row.action_colors, row.successful)
                for group in train for row in broad[group][depth])
            heads.append(_fit(
                rows, tuple(BRANCH_NAMES[index] for index in indices),
                COLORS, neighbors, .5))
        result[name] = tuple(heads)
    return result


def _fusion_model(states, features, graphs, sources, train):
    def action_key(actions):
        return tuple(sorted(actions))

    def exact(source, actions):
        truth = source.truth
        key = lambda point: tuple(round(float(value), 6) for value in point)
        return all(truth.get(key(point)) == color for point, color in actions)

    table = {group: tuple((
        features[(group, action_key(row[2]))],
        tuple(color for _point, color in row[2]),
        graphs[(group, action_key(row[2]))],
        exact(sources[group], row[2])) for row in states[group])
        for group in range(30)}
    representation = TerminalRepresentation(
        "incidence", tuple(range(len(FEATURE_NAMES) - 4, len(FEATURE_NAMES))))
    examples = tuple(PortfolioTerminalExample(
        group, row[0], row[1], row[3])
        for group in train for row in table[group])
    projected = tuple(RecurrentBranchExample(
        row.group, tuple(row.features[index]
                         for index in representation.feature_indices),
        row.action_colors, row.successful) for row in examples)
    scalar = FrozenPortfolioTerminalValue(
        representation, _fit(
            projected,
            tuple(FEATURE_NAMES[index]
                  for index in representation.feature_indices),
            COLORS, 1, .5))
    graph = fit_learned_equivariant_port_value(tuple(
        LearnedEquivariantPortExample(group, row[2], row[3])
        for group in train for row in table[group]), GRAPH_SPEC)
    digest = hashlib.sha256(repr((
        portfolio_terminal_value_digest(scalar), graph.model_digest, 2.,
        tuple(FEATURE_NAMES), tuple(COLORS), len(train))).encode()).hexdigest()
    return FrozenEquivariantPortFusionValue(
        scalar, graph, 2., tuple(FEATURE_NAMES), tuple(COLORS), len(train),
        digest)


def build(cache_dir: Path, output: Path, source_commit: str):
    source_path = cache_dir / "gcts-autonomous-all30-paths.pkl"
    branch_path = cache_dir / f"gcts-nested-channel-fold-{FOLD}.pkl"
    state_path = cache_dir / f"gcts-portfolio-states-v2-fold-{FOLD}.pkl"
    geometry_path = cache_dir / f"gcts-irregular-geometry-v1-fold-{FOLD}.pkl"
    graph_path = cache_dir / \
        f"gcts-irregular-complete-incidence-v3-fold-{FOLD}.pkl"
    vocabulary_paths = tuple(cache_dir / f"gcts-irregular-group-{index}.pkl"
                             for index in range(10))
    paths = (source_path, branch_path, state_path, geometry_path, graph_path,
             *vocabulary_paths)
    if any(not path.is_file() for path in paths):
        raise FileNotFoundError("one or more authorized development caches missing")
    sources, corpora, _ = _load(source_path)
    broad, _onpolicy = _load(branch_path)
    states = _load(state_path)
    features, _old_graphs = _load(geometry_path)
    graphs = _load(graph_path)
    train = tuple(group for group in range(30) if group not in HELDOUT)
    state_model = fit_pose_port_state_marking(
        _examples(corpora, HELDOUT),
        minimum_token_support=MINIMUM_TOKEN_SUPPORT,
        minimum_token_groups=MINIMUM_TOKEN_GROUPS,
        token_shrinkage=TOKEN_SHRINKAGE,
        state_bin_width=STATE_BIN_WIDTH,
        minimum_state_support=MINIMUM_STATE_SUPPORT,
        minimum_state_groups=MINIMUM_STATE_GROUPS)
    branch_models = _branch_models(broad, train)
    fusion = _fusion_model(states, features, graphs, sources, train)
    if fusion.model_digest != EXPECTED_FUSION_DIGEST:
        raise AssertionError(
            "selected fusion model does not reproduce: "
            f"{fusion.model_digest} != {EXPECTED_FUSION_DIGEST}")
    vocabularies, coverage = [], []
    for path in vocabulary_paths:
        vocabulary, cover = _load(path)
        vocabularies.append(vocabulary)
        coverage.append(cover.repeated_coverage)
    grouped = merge_grouped_vocabulary(
        vocabularies, coverage, minimum_group_support=3)
    _prototypes, connection = _program(sources)
    provenance = {
        "migration_only_pickle_inputs": [
            {"name": path.name, "sha256": _sha(path)} for path in paths],
        "training_groups": list(train),
        "excluded_outer_groups": list(HELDOUT),
        "fusion_capacity": ["incidence", 1, 2.],
        "migration_python_version": sys.version,
        "new_development_atoms_seen": False,
        "new_development_targets_seen": False,
    }
    payload = runtime_payload(
        source_commit=source_commit, connection=connection,
        grouped_vocabulary=grouped, state_model=state_model,
        branch_models=branch_models, fusion_model=fusion,
        provenance=provenance)
    raw = canonical_json(payload)
    compressed = bz2.compress(raw, compresslevel=9)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(compressed)
    return {
        "artifact_digest": payload["artifact_digest"],
        "payload_sha256": hashlib.sha256(raw).hexdigest(),
        "compressed_sha256": hashlib.sha256(compressed).hexdigest(),
        "compressed_bytes": len(compressed),
        "fusion_model_digest": fusion.model_digest,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path("/tmp"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    print(json.dumps(build(
        args.cache_dir, args.output, args.source_commit),
        indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
