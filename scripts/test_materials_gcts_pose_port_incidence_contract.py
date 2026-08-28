#!/usr/bin/env python3
"""Static contract for Build 294's pose by connection-port incidence microscope."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(source: str, fragment: str) -> None:
    assert fragment in source, f"missing required fragment: {fragment}"


def main() -> None:
    require(APP, "function clusterPosePortIncidence(cluster)")
    require(APP, "const orderedMatrix = rowOrder.map((row) => matrix[row.rawPose]);")
    require(APP, "numericRank: Math.max(1, decomposition.rank)")
    require(APP, 'matrixMeaning: "retained training witness count for a symmetry-reduced pose orbit and outgoing port role"')
    require(APP, "candidateGeometryChanged: false")
    require(APP, "physicalPotential: false")
    require(APP, "function clusterPosePortRank(cluster) {")
    require(APP, "return clusterPosePortIncidence(cluster).numericRank;")
    require(APP, "function renderClusterPosePortIncidence(inspector, cluster, familyIndex)")
    require(APP, 'class="cluster-pose-port-incidence"')
    require(APP, "The numeric rank of this witnessed matrix—not the raw number of rotations or port labels—supplies the directional channel demand")
    require(APP, "posePortIncidence: posePortIncidence ? {")
    require(APP, "matrix: posePortIncidence.matrix.map((row) => row.slice())")
    require(APP, "retainedWitnessSamples: posePortIncidence.retainedWitnessSamples")
    require(CSS, ".cluster-pose-port-grid")
    require(CSS, ".cluster-pose-port-detail")
    require(README, "Build 294 · pose × connection-port incidence microscope")
    require(APP, 'buildId: "20260828-296"')
    require(HTML, 'app.js?v=20260828-296')
    require(HTML, 'style.css?v=20260828-296')
    print("pose by connection-port incidence contract passed")


if __name__ == "__main__":
    main()
