#!/usr/bin/env python3
"""Static contract for Build 295's rank-revealing GCTS channel basis."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(source: str, fragment: str) -> None:
    assert fragment in source, f"missing required fragment: {fragment}"


def main() -> None:
    require(APP, "function numericMatrixDecomposition(matrix, tolerance = 1e-8)")
    require(APP, "return { rank, pivotColumns };")
    require(APP, "const decomposition = numericMatrixDecomposition(orderedMatrix);")
    require(APP, "const directionalChannelLimit = 10;")
    require(APP, "directionalBasisTruncated: decomposition.rank > directionalChannelLimit")
    require(APP, 'scalarFields: ["compatibility", "failure"]')
    require(APP, 'class="cluster-channel-basis"')
    require(APP, "additional independent directions are truncated by the declared 12-channel ceiling")
    require(APP, "pivotRoleColumns: posePortIncidence.pivotRoleColumns.slice()")
    require(APP, "directionalBasis: posePortIncidence.directionalBasis.map((channel) => ({")
    require(APP, "directionalBasisTruncated: posePortIncidence.directionalBasisTruncated")
    require(CSS, ".cluster-channel-basis")
    require(CSS, ".port-head.basis-column")
    require(README, "Build 295 · rank-revealing channel basis")
    require(APP, 'buildId: "20260828-322"')
    require(HTML, 'app.js?v=20260828-322')
    require(HTML, 'style.css?v=20260828-322')
    print("rank-revealing channel basis contract passed")


if __name__ == "__main__":
    main()
