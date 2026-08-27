from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/site-creation-physics-audit.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_every_emitted_placement_freezes_the_actual_score_decomposition():
    assert "frozenCreationPhysicsTerms" in APP
    assert "activeCandidateScoreTerms" in APP
    assert "physicsTerms: frozenCreationPhysicsTerms(evaluation)" in APP
    assert "raw: receiptRound(term.raw)" in APP
    assert "weight: receiptRound(term.weight)" in APP
    assert "contribution: receiptRound(term.contribution)" in APP
    assert "renderSiteCreationPhysicsAudit(snapshot.decisionEvidence)" in APP


def test_hard_admission_is_separate_from_soft_ranking():
    for gate in ("hard-core", "public-boundary", "shared-support", "novel-emission",
                 "known-window", "coordination", "angles", "feedstock", "marking"):
        assert f'id: "{gate}"' in APP
    assert "admissionGates: frozenCreationAdmissionGates(evaluation)" in APP
    assert "activeTerms" in MODULE
    assert "diagnosticTerms" in MODULE
    assert "allHardGatesPassed" in MODULE


def test_site_creation_ledger_is_visible_and_claims_fail_closed():
    for identifier in ("siteCreationPhysicsState", "siteCreationPhysicsRows", "siteCreationPhysicsBoundary"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    assert ".site-creation-physics-audit" in STYLE
    assert "targetUsed: false" in MODULE
    assert "scoreIsEnergy: false" in MODULE
    assert "scoreIsProbability: false" in MODULE
    assert "dynamicalTrajectoryIntegrated: false" in MODULE
    assert "physicalTimeIntegrated: false" in MODULE
    assert "not energies, probabilities, forces, barriers, rates, dynamics, or physical time" in APP


def test_build_191_assets_and_narrative():
    assert 'buildId: "20260827-226"' in APP
    assert 'app.js?v=20260827-226' in HTML
    assert 'style.css?v=20260826-104' in HTML
    assert 'site-creation-physics-audit.js?v=20260826-1' in APP
    assert "Build 191" in README
    assert "Build 191" in DOCS
