from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/policy-identifiability.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_identifiability_matrix_is_target_blind_and_candidate_frozen():
    assert 'excludedTermIds: ["known-window-gain", "exploration"]' in APP
    assert "candidateSetChanged: false" in MODULE
    assert "hardAdmissionChanged: false" in MODULE
    assert "candidateGeometryChanged: false" in MODULE
    assert "coordinatesEmbedded: false" in MODULE
    assert "targetUsed: false" in MODULE
    assert "executed: false" in MODULE
    assert "unique candidate keys" in MODULE
    assert "policyIdentifiabilityTrajectory" in MODULE
    assert "candidatesRegenerated: false" in MODULE
    assert "searchReplayed: false" in MODULE


def test_matrix_reports_linear_and_rank_correlation_with_claim_boundaries():
    assert "pearson" in MODULE
    assert "spearman" in MODULE
    assert '"near-redundant"' in MODULE
    assert '"opposed-rank"' in MODULE
    assert '"locally-distinct"' in MODULE
    assert "not causal or physical independence" in MODULE
    assert "causalIndependenceInferred: false" in APP
    assert "physicalIndependenceInferred: false" in APP
    assert "orthonormalBasis" in MODULE
    assert "residualize" in MODULE
    assert 'mode = "raw"' in MODULE
    assert '"conditional"' in MODULE
    assert "constant-or-collinear" in MODULE
    assert "explained-by-conditioning" in MODULE


def test_portal_exposes_interactive_matrix_and_receipt_audit():
    for identifier in ("policyIdentifiabilityState", "policyIdentifiabilityMatrix",
                       "policyIdentifiabilityDetail", "policyIdentifiabilityRaw",
                       "policyIdentifiabilityConditional", "policyIdentifiabilityHistoryState",
                       "policyIdentifiabilityHistory"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    assert "Are the geometry channels independent?" in HTML
    assert "renderPolicyIdentifiabilityAudit(snapshot)" in APP
    assert "hypothesisIdentifiability:" in APP
    assert "receiptPolicyIdentifiabilityMode" in APP
    assert 'modes: { raw:' in APP
    assert 'conditional: receiptPolicyIdentifiabilityMode' in APP
    assert "exact emitted species-labelled sites" in APP
    assert "frozen grammar / marking priority" in APP
    assert "buildPolicyIdentifiabilityHistory" in APP
    assert "renderPolicyIdentifiabilityHistory" in APP
    assert "selectedHypothesisTrajectory:" in APP
    assert "physicalTimeInferred: false" in APP
    assert "mechanismPersistenceInferred: false" in APP
    assert ".policy-identifiability-matrix" in STYLE
    assert "Build 180" in README
    assert "Build 180" in DOCS


def test_current_assets_are_cache_busted():
    assert 'buildId: "20260827-260"' in APP
    assert 'app.js?v=20260827-260' in HTML
    assert 'style.css?v=20260827-260' in HTML
    assert 'policy-identifiability.js?v=20260826-4' in APP
