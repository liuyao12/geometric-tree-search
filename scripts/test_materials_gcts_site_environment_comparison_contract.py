from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/site-environment-comparison.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_two_site_comparison_is_interactive_and_visually_distinct():
    for identifier in ("siteProvenancePin", "siteProvenanceCycle", "siteEnvironmentComparison", "siteComparisonState",
                       "siteComparisonGrid", "siteComparisonChannels", "siteComparisonBoundary",
                       "siteComparisonClear"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    assert "pinnedSiteId" in APP
    assert "pinnedSiteSelectionMaterial" in APP
    assert "renderSiteEnvironmentComparison" in APP
    assert "cycleInspectedSite" in APP
    assert ".site-environment-comparison" in STYLE


def test_comparison_uses_colored_coordination_radial_shells_and_lineage():
    assert "distanceShells" in (ROOT / "apps/iqc-growth-live/site-provenance.js").read_text()
    assert "speciesCounts" in MODULE
    assert "rmsDistanceDeltaAngstrom" in MODULE
    assert "rmsAngleDeltaDegrees" in MODULE
    assert "orientationalOrder" in MODULE
    assert "localOrientationalOrder" in APP
    assert "localCentrosymmetry" in APP
    assert "exactOptimalPairing" in MODULE
    assert "amplitudeDelta" in MODULE
    assert "contactAngleMismatch" in MODULE
    assert "coordinationDeficit" in MODULE
    assert "depthDelta" in MODULE
    assert "compareSiteEnvironments" in APP


def test_coordinate_free_claims_fail_closed():
    assert "targetUsed: false" in MODULE
    assert "absoluteCoordinatesUsed: false" in MODULE
    assert "translationIndependent: true" in MODULE
    assert "globalRotationIndependent: true" in MODULE
    assert "fullLocalIsometryProved: false" in MODULE
    assert "defectIdentityInferred: false" in MODULE
    assert "energyEquivalenceInferred: false" in MODULE
    assert "physicalMechanismInferred: false" in MODULE
    assert "angularPermutationResolved: false" in MODULE
    assert "namedDefectClassified: false" in MODULE
    assert "defectFormationEnergyInferred: false" in MODULE
    assert "positionAngstrom" not in MODULE
    assert "does not establish neighbor correspondence, local isometry" in APP


def test_build_190_assets_and_narrative():
    assert 'buildId: "20260827-246"' in APP
    assert 'app.js?v=20260827-246' in HTML
    assert 'style.css?v=20260827-246' in HTML
    assert 'site-environment-comparison.js?v=20260826-3' in APP
    assert 'site-provenance.js?v=20260826-2' in APP
    assert "Build 190" in README
    assert "Build 190" in DOCS
