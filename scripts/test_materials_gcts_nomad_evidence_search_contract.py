#!/usr/bin/env python3
"""Static release contract for evidence-targeted public-archive retrieval."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
DATABASE = (ROOT / "apps/iqc-growth-live/structure-database.js").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()


def main() -> None:
    for identifier in ("databaseEvidenceSelect", "databaseEvidenceHint", "databaseFamilySelect",
                       "databaseFamilyHint", "databaseFamilySource"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    for mode in ("geometry", "relaxation", "forces", "calibration"):
        assert f'value="{mode}"' in HTML
        assert f'{mode}: Object.freeze(' in DATABASE
    for family in ("bulk", "twoD", "water"):
        assert f'value="{family}"' in HTML
        assert f'{family}: Object.freeze(' in DATABASE
    assert "normalizeNomadStructureFamily" in DATABASE
    assert "nomadStructureCandidates" in DATABASE
    assert "loadNomadStructureCandidate" in DATABASE
    assert "renderDatabaseStructureFamily" in APP
    assert "renderDatabaseCandidateTray" in APP
    assert "explicitCandidateSelection" in APP
    assert "structureFamily: structureFamily.id" in APP
    assert "structureFamilyUsedForGrowth: false" in APP
    assert "nomadStructureEvidenceProfile" in DATABASE
    assert "nomadEvidenceTargetAccepts" in DATABASE
    assert "calibrationReady: relaxationFrames >= 5" in DATABASE
    assert "evidenceTarget: evidenceTarget.id" in APP
    assert "publicDatabaseEvidence:" in APP
    assert "clientSideEvidenceGate: true" in APP
    assert "targetUsedForGrowth: false" in APP
    assert "database-evidence" in STYLE
    assert 'id="databaseCandidateTray"' in HTML
    assert "database-candidate-tray" in STYLE
    assert 'structure-database.js?v=20260827-9' in APP
    assert 'buildId: "20260827-238"' in APP
    assert 'app.js?v=20260827-238' in HTML
    print("NOMAD evidence-targeted search contract passed")


if __name__ == "__main__":
    main()
