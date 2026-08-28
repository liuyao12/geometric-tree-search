from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"
APP = (APP_DIR / "app.js").read_text(encoding="utf-8")
HTML = (APP_DIR / "index.html").read_text(encoding="utf-8")
ENVELOPES = (APP_DIR / "colored-distance-envelopes.js").read_text(encoding="utf-8")
ATLAS = (APP_DIR / "evidence-atlas.js").read_text(encoding="utf-8")
README = (APP_DIR / "README.md").read_text(encoding="utf-8")
DOCS = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(encoding="utf-8")


def test_local_constraint_mismatch_is_identity_free_and_keeps_coordination_separate():
    assert "export function coloredLocalConstraintMismatch" in ENVELOPES
    assert "neighborIndices" in ENVELOPES
    assert "contactAngleMismatch: .55 * distance + .45 * angle" in ENVELOPES
    assert "coordinationDeficit" in ENVELOPES
    assert "targetUsed: false" in ENVELOPES
    assert "physicalPotentialUsed: false" in ENVELOPES


def test_live_map_uses_spatial_neighbors_and_preserves_scientific_boundaries():
    assert "function currentLocalConstraintMismatchField()" in APP
    assert "nearbyAtoms(atoms[center].p, reach)" in APP
    assert "maximumDisplayedCenters = 1200" in APP
    assert 'samplingPolicy: atoms.length <= maximumDisplayedCenters' in APP
    assert 'useInSearch: "diagnostic field only' in APP
    assert "stress: false" in APP
    assert "elasticEnergy: false" in APP
    assert "defectIdentity: false" in APP
    assert "physicalTime: false" in APP


def test_interactive_layers_receipt_and_ledger_are_complete():
    for identifier in (
        "localConstraintMismatchToggle",
        "localConstraintMismatchToggleLabel",
        "localConstraintMismatchMetric",
    ):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    for mode in ("combined", "distance", "angle", "coordination"):
        assert f'value="{mode}"' in HTML
    assert "currentLocalConstraintMismatch:" in APP
    assert "localConstraintMismatchSha256" in APP
    assert 'id: "local-mismatch-map"' in APP
    assert "usedToAdmitGrowth: false" in APP
    assert "usedToRankCurrentGrowth: false" in APP
    assert "free surface" in APP


def test_current_release_retains_build_168_and_is_versioned():
    assert 'buildId: "20260827-267"' in APP
    assert 'app.js?v=20260827-267' in HTML
    assert 'colored-distance-envelopes.js?v=20260827-9' in APP
    assert 'evidence-atlas.js?v=20260827-23' in HTML
    assert "current-state contact/angle mismatch" in ATLAS
    assert "Build 168" in README
    assert "Build 168" in DOCS
