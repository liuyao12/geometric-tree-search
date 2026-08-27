from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/policy-identifiability.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_notebook_retains_coordinate_free_identifiability_only():
    assert "policyIdentifiability: latestPolicySnapshot?.hypothesisIdentifiability" in APP
    assert "candidateCoordinatesEmbedded: false" in APP
    assert "candidateRowsEmbedded: false" in APP
    assert "selectedTrajectory: selectedHypothesisTrajectory" in APP
    assert "identifiabilityUpgradeNeeded" in APP
    assert "coordinate-free hypothesis-identifiability audit" in APP
    assert "policyIdentifiabilityAcrossArms" in MODULE
    assert "candidateSetsPooled: false" in MODULE
    assert "candidatesRegenerated: false" in MODULE
    assert "searchReplayed: false" in MODULE
    assert "coordinatesEmbedded: false" in MODULE
    assert "targetUsed: false" in MODULE


def test_cross_arm_comparison_is_fail_closed_and_noncausal():
    assert "compatibleConditioning" in MODULE
    assert "comparison withheld until every arm contains the same pair" in MODULE
    assert "causalEffectInferred: false" in MODULE
    assert "crossMaterialUniversalityInferred: false" in MODULE
    assert "not a pooled estimate, causal effect, or universality claim" in MODULE
    assert "notebookArmIdentifiabilityComparison" in APP
    assert "renderStudyIdentifiabilityComparison" in APP
    assert "same hypothesis pair across saved arms" in APP
    assert "descriptive contrast" in APP
    assert "renderNotebookIdentifiabilityComparison" in APP
    assert "cross-run hypothesis transfer audit" in APP
    assert "notebookComparison.append(renderNotebookIdentifiabilityComparison" in APP
    assert "audit ${comparison.comparisonDigest}" in APP
    assert ".study-identifiability-comparison" in STYLE
    assert ".notebook-identifiability-comparison" in STYLE
    assert "Build 182" in README
    assert "Build 182" in DOCS


def test_build_182_assets_are_cache_busted():
    assert 'buildId: "20260827-236"' in APP
    assert 'app.js?v=20260827-236' in HTML
    assert 'style.css?v=20260826-104' in HTML
    assert 'policy-identifiability.js?v=20260826-4' in APP
