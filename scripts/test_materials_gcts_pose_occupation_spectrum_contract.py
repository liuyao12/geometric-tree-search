#!/usr/bin/env python3
"""Static contract for Build 293's proper-pose occupation microscope."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(source: str, fragment: str) -> None:
    assert fragment in source, f"missing required fragment: {fragment}"


def main() -> None:
    require(APP, "function poseOrbitOccupationRecord(cluster, poseModel = galleryPoseModel(cluster))")
    require(APP, "effectiveOccupiedPoseOrbits: populations.length ? Math.exp(entropyNats) : 0")
    require(APP, "normalizedOccupationEntropy: normalizedEntropy")
    require(APP, 'populationOrder: "descending occupancy; display ranks are not raw orientation IDs"')
    require(APP, "probabilityOrFreeEnergyClaimed: false")
    require(APP, "function renderClusterPoseOccupation(inspector, cluster, poseModel)")
    require(APP, 'class="cluster-pose-spectrum"')
    require(APP, "Pose occupancies are computed after translation, atom order, and every tied proper-symmetry gauge are quotiented")
    require(APP, "Occupancy ranks summarize the supplied configuration; they are not probabilities, Boltzmann weights, or free energies")
    require(APP, "properPoseOccupation: {")
    require(APP, "dominantOccurrenceFraction: receiptRound(poseOccupation.dominantOccurrenceFraction)")
    require(APP, "singletonPoseOrbits: poseOccupation.singletonPoseOrbits")
    require(APP, "targetUsed: false")
    require(CSS, ".cluster-pose-spectrum-bars")
    require(CSS, ".cluster-pose-spectrum-detail")
    require(README, "Build 293 · proper-pose occupation microscope")
    require(APP, 'buildId: "20260829-333"')
    require(HTML, 'app.js?v=20260829-333')
    require(HTML, 'style.css?v=20260829-333')
    print("proper-pose occupation spectrum contract passed")


if __name__ == "__main__":
    main()
