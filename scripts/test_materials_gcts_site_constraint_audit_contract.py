from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/site-constraint-audit.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_selected_site_expands_into_learned_constraint_channels():
    for identifier in ("siteConstraintState", "siteConstraintMeters", "siteConstraintChannels"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    assert "selectedSiteConstraintAudit" in APP
    assert "coloredLocalConstraintMismatch" in APP
    assert "buildSiteConstraintAudit" in APP
    assert "renderSiteConstraintAudit" in APP
    assert ".site-constraint-meters" in STYLE
    assert ".site-constraint-channels" in STYLE


def test_contact_coordination_and_angle_semantics_remain_separate():
    assert 'kind: "contact"' in MODULE
    assert 'kind: "coordination"' in MODULE
    assert 'kind: "angle"' in MODULE
    assert "normalizedResidual" in MODULE
    assert "medianObserved" in MODULE
    assert "maximumObserved" in MODULE
    assert "frontier deficit" in MODULE
    assert "over capacity" in MODULE
    assert "within band" in MODULE
    assert "outside band" in MODULE
    assert "contactAngleMismatch" in MODULE
    assert "coordinationDeficit" in MODULE


def test_site_constraint_claims_fail_closed():
    assert "targetUsed: false" in MODULE
    assert "physicalPotentialUsed: false" in MODULE
    assert "forceInferred: false" in MODULE
    assert "surfaceEnergyInferred: false" in MODULE
    assert "defectIdentityInferred: false" in MODULE
    assert "no target, energy, force, defect identity, or physical mechanism" in APP


def test_build_186_assets_and_narrative():
    assert 'buildId: "20260827-263"' in APP
    assert 'app.js?v=20260827-263' in HTML
    assert 'style.css?v=20260827-263' in HTML
    assert 'site-constraint-audit.js?v=20260826-1' in APP
    assert "Build 186" in README
    assert "Build 186" in DOCS
