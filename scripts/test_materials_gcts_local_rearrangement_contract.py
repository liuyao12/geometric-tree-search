#!/usr/bin/env python3
"""Source contract for atom-resolved local best-affine rearrangement geometry."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/relaxation-local-environment.js").read_text()


def test_local_rearrangement_is_visible_and_independently_toggleable():
    for token in (
        'id="relaxationLocalEnvironmentState"',
        'id="relaxationLocalEnvironmentToggle"',
        'id="relaxationLocalEnvironmentToggleLabel"',
        "Local rearrangement √D²min",
    ):
        assert token in HTML or token in APP


def test_d2min_uses_periodic_neighbor_vectors_and_a_best_affine_fit():
    for token in (
        "function relaxationLocalEnvironmentField()",
        "const neighborCount = Math.min(12, atomCount - 1)",
        "fractional.getComponent(axis) - Math.round(fractional.getComponent(axis))",
        "bestAffineNeighborhoodResidual",
        "d2MinAngstromSquared",
        "rootD2MinAngstrom",
    ):
        assert token in APP
    for token in (
        "crossMoment[row][column] += target[row] * source[column]",
        "sourceMoment[row][column] += source[row] * source[column]",
        "multiply(crossMoment, invert3(sourceMoment))",
        "value - targetVectors[sample][axis]",
    ):
        assert token in MODULE


def test_visualization_and_receipt_keep_exact_metrics_separate():
    for token in (
        "percentile90RootD2MinAngstrom",
        "relaxationLocalEnvironmentRecords",
        "relaxationLocalEnvironmentSha256",
        "selectedToFinalLocalEnvironment",
        "localBestAffineMapsEmbedded: false",
        "physicalTimeUsed: false",
        "usedForGrowth: false",
        "new THREE.IcosahedronGeometry(.27, 1)",
        "halos.setColorAt",
        "lostNeighborPairs",
        "gainedNeighborPairs",
        "meanNeighborPersistenceFraction",
        "sourceNeighborIndices: record.sourceNeighborIndices",
        "targetNeighborIndices: record.targetNeighborIndices",
        "uniqueLostNeighborPairs",
        "uniqueGainedNeighborPairs",
        "primitiveSourceIndex",
        "supercellImage",
        "sourceNeighborIdentities",
        "targetNeighborIdentities",
    ):
        assert token in APP


def test_claim_boundary_is_kinematic_not_plastic_or_kinetic():
    for token in (
        "D²min and kNN identity exchange are kinematic differences",
        "A nearest-neighbor ranking is not a chemical bond graph.",
    ):
        assert token in APP
    for token in (
        "regularized least-squares affine map",
        "not a plastic-strain tensor, defect",
        "fixed-k graph is geometric adjacency, not bond order",
    ):
        assert token in README


def test_build_114_is_cache_busted():
    assert 'buildId: "20260825-146"' in APP
    assert 'app.js?v=20260825-146' in HTML


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
    print("materials local rearrangement contract: passed")
