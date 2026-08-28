from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
AUDIT = (ROOT / "apps/iqc-growth-live/archive-response-frontier-audit.js").read_text()


def test_frozen_frontier_intervention_is_visible_and_receipt_native():
    for identifier in (
        "studyFrontierAudit",
        "studyFrontierAuditState",
        "studyFrontierAuditMetrics",
        "studyFrontierAuditRanks",
        "studyFrontierAuditBoundary",
    ):
        assert f'id="{identifier}"' in HTML
        assert identifier in APP
    assert "frozenFrontierIntervention" in APP
    assert "buildArchiveResponseFrontierAudit()" in APP
    assert ".study-frontier-audit" in CSS


def test_counterfactual_replaces_only_the_strain_contribution():
    assert "observedGeometricStrain: entry.evaluation.geometricStrain.total" in APP
    assert "responseGeometricStrain: entry.evaluation.affineLoadedGeometricStrain.total" in APP
    assert "candidate.baselineScore - responseTerm.contribution + controlContribution" in AUDIT
    assert 'candidate.scoreTerms?.find((term) => term.id === "geometric-strain")' in AUDIT
    assert "candidateSetChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "candidateGeometryChanged: false" in APP
    assert "targetUsedToConstructCounterfactual: false" in APP
    assert "capturedBeforeDisplayedCommit: true" in APP
    assert "executed: false" in APP


def test_rank_audit_is_complete_and_target_role_is_explicit():
    for field in (
        "responseRank",
        "controlRank",
        "pairwiseRankInversions",
        "spearmanRho",
        "maximumRankDisplacement",
        "winnerChanged",
        "auditDigest",
        "rankingTargetUsed",
    ):
        assert field in APP
    assert "known-window replay" in APP
    assert "target-free continuation" in APP
    assert "not energy, kinetics, or a physical potential" in APP


def test_build_259_cache_and_narrative_contract():
    assert 'buildId: "20260827-274"' in APP
    assert "app.js?v=20260827-274" in HTML
    assert "style.css?v=20260827-274" in HTML
    assert "Build 258 · frozen-frontier response intervention" in README
