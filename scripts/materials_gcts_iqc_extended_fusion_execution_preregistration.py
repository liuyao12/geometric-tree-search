#!/usr/bin/env python3
"""Freeze the executable IQC fusion procedure before new seed generation.

This second manifest binds the already-published ten-centre geometry protocol
to exact source files and the inert policy artifact.  It imports no oracle,
cropper, candidate generator, scorer, or target data.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, ORACLE_LIFT_BOUND, SEED_RADIUS, TARGET_RADIUS,
    audit as geometry_audit)


SOURCE_COMMIT = "b893d6a879a5b5c2c9769f74cfc61f881e29b0ee"
GEOMETRY_MANIFEST_DIGEST = \
    "790a04a8375da21f0f344bddf86304b981d720b457f52df7a485e41eb0753676"
FUSION_ARTIFACT_DIGEST = \
    "fbdbdf307227921ad24d11b81aea31e9835acf50ae2359d0807cc184b96c623c"
FUSION_MODEL_DIGEST = \
    "505b65481e3fe2cc25a284ba8dc175e3a794465c2c7bd726f5448c1fac6bbef5"
FUSION_CAPACITY = ("incidence", 1, 2.0)
SEARCH_SCHEDULE = (4, 4, 8)
BEAM_SPECS = ((4.0, 1, 4), (4.0, 2, 4), (2.0, 1, 8))
ACTION_COUNT = 3

SOURCE_HASHES = (
    ("materials_gcts_iqc_frozen_fusion_runtime.py",
     "2d990643594255484f5e44138bd47509229115a4e62ee133bd8c8f9a049287c9"),
    ("materials_gcts_iqc_frozen_fusion_artifact.py",
     "2026a624e03f599573501b27daa373302cd264f96afa6369313354063669fde9"),
    ("materials_gcts_equivariant_port_fusion_value.py",
     "7da436c9cb7e39fa3a67045d43e349009b4b6501ca868258470ba07b215b3b4f"),
    ("materials_gcts_learned_equivariant_port_value.py",
     "e6d8ad0742ce84368e4147117ad9583f1eaf1ab232776aaed5a14a416ce029df"),
    ("materials_gcts_partial_irregular_port_graph.py",
     "a4d92eaaf5c2c04aa30fab1f657dd6d64098375811b55fcb428fded988afde63"),
    ("materials_gcts_partial_irregular_section.py",
     "48b68f9cef034daf0ced881b2dca7130d7c7a6bcdf92a5d7fb1637538ecd58fa"),
    ("materials_gcts_local_section_tensor.py",
     "ebf58df28e96d9bb25319514382e12d85bd355f8100b7cc480580c9b551cd9b2"),
    ("fixtures/iqc_frozen_terminal_fusion_v1.json.bz2",
     "6ab3b23317207577a2805a27f3fa399d312e9c2eefa7d9c858731bd9a456f6d5"),
    ("materials_gcts_iqc_extended_fusion_development_benchmark.py",
     "71201c733eeefc8a6732dd92fdb16ef8562116f59db29470338c4d87e6f45b80"),
)

TARGET_ORDER = (
    "verify manifests, source hashes, and inert model; materialize detached "
    "radius-9 seeds; freeze every terminal action, scalar order, fusion "
    "order, and digest for all ten nuclei; serialize the pre-target receipt; "
    "only then construct all radius-14.562305898749054 targets exactly once; "
    "perform pure scoring without refit, rerank, retry, or exclusion"
)
BATCH_METRICS = (
    "for scalar and fusion on identical terminal candidates report terminal "
    "supply, exact selected nuclei, correct selected sites out of 30, first "
    "exact rank, candidate counts, seed/target atoms, bound-plus-one "
    "stability, raw-ID disjointness, and every per-centre result"
)
GATE = (
    "development transfer improves only if fusion exact nuclei and correct "
    "sites are each at least the scalar incumbent; no significance, fresh "
    "confirmation, sustained growth, stationarity, or exponential claim"
)


@dataclass(frozen=True)
class IQCExtendedFusionExecutionPreregistration:
    source_commit: str
    geometry_manifest_digest: str
    centers: tuple[tuple[float, float, float], ...]
    seed_radius: float
    target_radius: float
    oracle_lift_bound: int
    fusion_artifact_digest: str
    fusion_model_digest: str
    fusion_capacity: tuple[str, int, float]
    search_schedule: tuple[int, ...]
    beam_specs: tuple[tuple[float, int, int], ...]
    action_count: int
    source_hashes: tuple[tuple[str, str], ...]
    source_hashes_match: bool
    target_order: str
    batch_metrics: str
    gate: str
    oracle_or_cropper_imported: bool
    seed_or_target_materialized: bool
    candidates_or_scores_computed: bool
    manifest_digest: str


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def audit():
    geometry = geometry_audit()
    if geometry.manifest_digest != GEOMETRY_MANIFEST_DIGEST:
        raise AssertionError("extended-development geometry manifest drift")
    root = Path(__file__).resolve().parent
    hashes_match = all(hashlib.sha256((root / name).read_bytes()).hexdigest()
                       == digest for name, digest in SOURCE_HASHES)
    payload = {
        "source_commit": SOURCE_COMMIT,
        "geometry_manifest_digest": GEOMETRY_MANIFEST_DIGEST,
        "centers": DEVELOPMENT_CENTERS,
        "seed_radius": SEED_RADIUS,
        "target_radius": TARGET_RADIUS,
        "oracle_lift_bound": ORACLE_LIFT_BOUND,
        "fusion_artifact_digest": FUSION_ARTIFACT_DIGEST,
        "fusion_model_digest": FUSION_MODEL_DIGEST,
        "fusion_capacity": FUSION_CAPACITY,
        "search_schedule": SEARCH_SCHEDULE,
        "beam_specs": BEAM_SPECS,
        "action_count": ACTION_COUNT,
        "source_hashes": SOURCE_HASHES,
        "source_hashes_match": hashes_match,
        "target_order": TARGET_ORDER,
        "batch_metrics": BATCH_METRICS,
        "gate": GATE,
        "oracle_or_cropper_imported": False,
        "seed_or_target_materialized": False,
        "candidates_or_scores_computed": False,
    }
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    return IQCExtendedFusionExecutionPreregistration(
        *payload.values(), digest)


if __name__ == "__main__":
    print(json.dumps(asdict(audit()), indent=2, sort_keys=True))
