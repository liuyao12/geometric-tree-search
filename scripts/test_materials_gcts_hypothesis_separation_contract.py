from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/hypothesis-separation.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_selected_pair_can_register_but_never_auto_execute():
    for identifier in ("policySeparationState", "policySeparationArm",
                       "policySeparationRegister", "policySeparationBaseline",
                       "policySeparationAblation", "policySeparationClear",
                       "policySeparationBoundary"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    assert "registerHypothesisSeparationExperiment" in APP
    assert "configureHypothesisSeparationArm" in APP
    assert "clearHypothesisSeparationExperiment" in APP
    assert 'enterPipelineStage(0)' in APP
    assert 'autoExecuted: false' in APP
    assert "no growth executed" in APP
    assert ".policy-separation-experiment" in STYLE


def test_ablation_changes_only_one_soft_score_term():
    assert "applyFrozenHypothesisSeparationMultipliers" in APP
    assert "validateHypothesisSeparationExperiment" in APP
    assert 'experiment.arm === "ablation"' in MODULE
    assert "experiment.ablatedTermId === termId" in MODULE
    assert "weight: 0" in MODULE
    assert "contribution: 0" in MODULE
    assert "candidateGeometryChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "targetUsed: false" in APP
    assert "candidateRowsEmbedded: false" in APP


def test_receipt_and_notebook_preserve_the_registered_factor():
    assert "hypothesisSeparationExperiment: hypothesisSeparationReceipt()" in APP
    assert "hypothesisSeparationExperiment: search?.hypothesisSeparationExperiment" in APP
    assert 'label: "registered score-channel ablation"' in APP
    assert "sourceCandidateSetDigest" in APP
    assert "sourceAuditDigest" in APP
    assert "settingsStillMatch" in APP
    assert "inputScenarioStillMatches" in APP
    assert "hypothesis-separation" in APP
    assert "Build 183" in README
    assert "Build 183" in DOCS


def test_build_183_assets_are_cache_busted():
    assert 'buildId: "20260827-250"' in APP
    assert 'app.js?v=20260827-250' in HTML
    assert 'style.css?v=20260827-250' in HTML
    assert 'hypothesis-separation.js?v=20260826-1' in APP
