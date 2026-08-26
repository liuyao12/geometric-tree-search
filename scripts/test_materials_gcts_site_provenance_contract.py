from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/site-provenance.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_atom_instances_are_pickable_and_open_the_microscope():
    for identifier in ("siteProvenanceInspector", "siteProvenanceNext", "siteProvenanceClose", "siteProvenanceState",
                       "siteProvenanceGrid", "siteProvenanceBoundary"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    assert "THREE.Raycaster" in APP
    assert "siteProvenancePickable" in APP
    assert "mesh.userData.atomIds" in APP
    assert "inspectSite(atom)" in APP
    assert "inspectSite(atoms[(current + 1) % atoms.length])" in APP
    assert ".site-provenance-inspector" in STYLE


def test_provenance_is_exact_local_geometry_and_lineage():
    assert "buildSiteProvenance" in APP
    assert "localEnvironment" in MODULE
    assert "creatorClusterId" in MODULE
    assert "clusterMemberships" in MODULE
    assert "nucleusIds" in MODULE
    assert "decisionEvidence" in MODULE
    assert "createdByClusterId" in APP
    assert "createdByRuleId" in APP
    assert "contactAngleStrain" in APP
    assert "loopClosureWitnesses" in APP


def test_site_audit_keeps_claims_and_storage_bounded():
    assert "targetUsed: false" in MODULE
    assert "ephemeralInspectorOnly: true" in MODULE
    assert "includedInReceipt: false" in MODULE
    assert "physicalEnergyInferred: false" in MODULE
    assert "forceInferred: false" in MODULE
    assert "mechanismIdentityInferred: false" in MODULE
    assert "not persisted in the notebook or receipt" in APP


def test_build_185_assets_and_narrative():
    assert 'buildId: "20260826-188"' in APP
    assert 'app.js?v=20260826-188' in HTML
    assert 'style.css?v=20260826-85' in HTML
    assert 'site-provenance.js?v=20260826-1' in APP
    assert "Build 185" in README
    assert "Build 185" in DOCS
