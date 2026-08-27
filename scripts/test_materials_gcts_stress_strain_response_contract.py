from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/stress-strain-response.js").read_text()


def test_archive_response_is_visible_interactive_and_fail_closed():
    assert "fitArchivedStressStrainResponse" in APP
    assert "archivedResponseDeformationGradient" in APP
    assert 'value="archive-response"' in HTML
    assert "stressStrainResponseChart" in APP
    assert "stressStrainUseButton" in APP
    assert "promotionPassed" in MODULE
    assert "crossValidatedSkill >= .2" in MODULE
    assert "maximumLinearStrain" in MODULE
    assert "targetCoordinatesUsed: false" in MODULE


def test_archive_response_is_soft_metric_only():
    assert 'if (affineLoadMode === "archive-response")' in APP
    assert "archivedResponseDeformationGradient(archivedStressStrainResponse(), importedFrameIndex, m)" in APP
    assert "exact coordinates and hard gates unchanged" in APP


def test_archive_response_is_receipt_and_manifest_auditable():
    assert "archivedResponseArtifactSha256" in APP
    assert "archivedStressStrainResponse: archivedResponseArtifact" in APP
    assert "fitArtifactEmbedded: true" in APP
    assert 'id: "stress-strain-response"' in APP
    assert "generalElasticTensorClaimed: false" in MODULE
    assert "independentValidationClaimed: false" in MODULE
    assert "candidateGeometryChanged: false" in MODULE
    assert "hardAdmissionChanged: false" in MODULE


def test_build_257_cache_contract():
    assert 'buildId: "20260827-264"' in APP
    assert "app.js?v=20260827-264" in HTML
    assert "style.css?v=20260827-264" in HTML
