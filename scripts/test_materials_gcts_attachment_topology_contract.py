#!/usr/bin/env python3
"""Contract for non-lattice terrace/step/kink attachment topology."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_attachment_topology_is_explicit_non_lattice_and_soft() -> None:
    for element_id in ("attachmentTopologySelect", "attachmentTopologyWeightSelect", "attachmentTopologyHint"):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "kink", "step", "terrace"):
        assert f'value="{mode}"' in HTML
    for weight in ("0.12", "0.24", "0.48"):
        assert f'value="{weight}"' in HTML

    assert "function attachmentTopologyForCandidate(" in APP
    assert "reach = 1.45 * referenceSpacing" in APP
    assert "lateralDirections" in APP
    assert 'angularSectorCount: 6' in APP
    assert 'kind = neighbors.length >= 3 && lateralDirections >= 2 ? "kink"' in APP
    assert 'neighbors.length >= 2 && lateralDirections >= 1 ? "step" : "terrace"' in APP
    assert 'id: "attachment-topology"' in APP
    assert "activeAttachmentTopologyWeight() * evaluation.attachmentTopology.score" in APP
    assert "attachmentTopologyRanking" in APP
    assert 'name: "attachment topology"' in APP
    assert "new THREE.TetrahedronGeometry" in APP
    assert "new THREE.BoxGeometry" in APP
    assert "new THREE.RingGeometry" in APP

    for invariant in (
        "candidateGeometryChanged: false", "hardAdmissionChanged: false", "heldoutTargetUsed: false",
        "activationBarrierInferred: false", "attachmentCoefficientInferred: false",
        "growthRateInferred: false", "latticeRequired: false", "physicalTimeIntegrated: false",
    ):
        assert invariant in APP
    for protocol_mode in ("kink", "step"):
        assert f'attachmentTopologyMode: "{protocol_mode}"' in APP

    normalized = " ".join(README.split())
    assert "Non-lattice terrace, step, and kink geometry" in README
    assert "irregular and rotated clusters as well as lattice crystals" in normalized
    assert "candidate digest remain unchanged" in normalized
    assert "does not infer an activation barrier" in normalized


if __name__ == "__main__":
    test_attachment_topology_is_explicit_non_lattice_and_soft()
    print("materials GCTS attachment-topology contract: passed")
