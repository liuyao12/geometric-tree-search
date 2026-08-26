from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()


def test_bond_valence_is_an_explicit_optional_growth_channel():
    assert 'from "./bond-valence-geometry.js?v=20260826-1"' in APP
    assert 'const bondValenceSelect = $("bondValenceSelect")' in APP
    assert 'activeBondValenceWeight() * evaluation.bondValence.score' in APP
    assert 'scoreTerm("bond-valence", "local bond-valence residual"' in APP
    assert '"bond-valence": [evaluation.bondValence.score, activeBondValenceWeight()]' in APP
    assert 'bondValenceMode === "none" ? 0 : result.score' in APP
    assert 'bondValenceSelect.addEventListener("change"' in APP


def test_bond_valence_keeps_geometry_and_claim_boundaries_separate():
    assert 'parameterPolicy: "exact species + exact supplied oxidation state + explicit distance range; unsupported pairs fail closed"' in APP
    assert 'physicalAngstromScaleRequired: true' in APP
    assert 'uniformScaleInvariant: false' in APP
    assert 'bondEnergyInferred: false' in APP
    assert 'electronDensityModeled: false' in APP
    assert 'candidateSetChanged: false, candidateGeometryChanged: false' in APP
    assert 'hardAdmissionChanged: false, heldoutTargetUsed: false' in APP


def test_bond_valence_residual_panel_is_interactive_and_receipted():
    assert 'id="bondValenceSelect"' in HTML
    assert 'id="bondValenceCandidates"' in HTML
    assert 'id="bondValenceResiduals"' in HTML
    assert 'Local valence-sum residual' in HTML
    assert '.bond-valence-card' in CSS
    assert '.bond-valence-residual-track i.before' in CSS
    assert '.bond-valence-residual-track i.after' in CSS
    assert 'function renderBondValenceResiduals(snapshot)' in APP
    assert 'bondValenceResidualAudit:' in APP
    assert 'provenance: BOND_VALENCE_PROVENANCE' in APP
