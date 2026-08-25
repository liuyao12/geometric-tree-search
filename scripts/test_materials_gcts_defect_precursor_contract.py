#!/usr/bin/env python3
"""Contract for action-generated geometric defect precursors."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_defect_precursors_are_action_generated_explicit_and_non_identifying() -> None:
    for element_id in ("defectPrecursorSelect", "defectPrecursorWeightSelect", "defectPrecursorHint"):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "suppress", "explore", "seam"):
        assert f'value="{mode}"' in HTML
    for weight in ("0.12", "0.24", "0.48"):
        assert f'value="{weight}"' in HTML

    assert "function defectPrecursorsForAction(" in APP
    for component in ("exposedCoordination", "strainOutlier", "compositionDrift", "incompatibleSeam"):
        assert component in APP
    assert ".35 * components.exposedCoordination" in APP
    assert ".30 * components.strainOutlier" in APP
    assert ".15 * components.compositionDrift" in APP
    assert ".20 * components.incompatibleSeam" in APP
    assert 'id: "defect-precursors"' in APP
    assert "activeDefectPrecursorWeight() * evaluation.defectPrecursors.score" in APP
    assert "actionDefectPrecursorRanking" in APP
    assert 'name: "defect precursors"' in APP
    assert "new THREE.DodecahedronGeometry" in APP

    for invariant in (
        "actionGeneratedGeometryOnly: true", "preexistingMicrostructureRolesUsed: false",
        "candidateSetChanged: false", "candidateGeometryChanged: false", "hardAdmissionChanged: false",
        "heldoutTargetUsed: false", "defectIdentityAssigned: false", "vacancyAssigned: false",
        "antisiteAssigned: false", "stackingFaultAssigned: false", "dislocationAssigned: false",
        "formationEnergyInferred: false", "migrationBarrierInferred: false", "mobilityInferred: false",
        "rateInferred: false", "physicalTimeIntegrated: false",
    ):
        assert invariant in APP
    for protocol_mode in ("suppress", "explore", "seam"):
        assert f'defectPrecursorMode: "{protocol_mode}"' in APP

    normalized = " ".join(README.split())
    assert "Action-generated defect-precursor budget" in README
    assert "current candidate action would create" in normalized
    assert "cannot alter a cluster pose" in normalized
    assert "assigns no vacancy, antisite, stacking fault, dislocation" in normalized


if __name__ == "__main__":
    test_defect_precursors_are_action_generated_explicit_and_non_identifying()
    print("materials GCTS defect-precursor contract: passed")
