from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/creation-response-association.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_one_sample_is_built_per_whole_cluster_placement():
    assert "creationResponseAssociationRecords" in APP
    assert "placementId: placement.id" in APP
    assert "placement.freshAtomIds" in APP
    assert "physicsTerms: placement.decisionEvidence.physicsTerms" in APP
    assert "new Set(ids).size !== ids.length" in MODULE
    assert 'groupingUnit: "one accepted whole-cluster placement"' in MODULE
    assert "atomLevelPseudoreplicationAvoided: true" in MODULE
    assert "canonicalCreationResponseDataset" in MODULE
    assert "datasetSha256" in APP
    assert "creationResponseEvidence" in APP
    assert "recordsEmbeddedInFullReceipt: true" in APP
    assert "recordsEmbeddedInNotebook: false" in APP


def test_creation_terms_are_compared_with_exact_later_geometry():
    for outcome in ("nonaffine", "radialDrift", "shellChange", "centerDisplacement",
                    "equivalentShear", "absoluteVolumeResponse"):
        assert f"{outcome}:" in APP
        assert f'value="{outcome}"' in HTML
    assert "averageRanks" in MODULE
    assert "spearmanRho" in MODULE
    assert "Math.abs(term.weight) > 1e-12" in MODULE


def test_association_microscope_is_interactive_and_claims_fail_closed():
    for identifier in ("sitePopulationResponseState", "sitePopulationResponseOutcome",
                       "sitePopulationResponsePlot", "sitePopulationResponseTerms",
                       "sitePopulationResponseBoundary"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    assert ".site-population-response" in STYLE
    assert "site-association-point.selected" in STYLE
    assert "sitePopulationResponseOutcome.addEventListener" in APP
    assert "targetUsed: false" in MODULE
    assert "causalEffectInferred: false" in MODULE
    assert "independentMaterialSamples: false" in MODULE
    assert "not a causal effect, calibrated predictor, energy relation, kinetic law" in APP
    assert "creationResponseLeapProfile" in MODULE
    assert 'id="sitePopulationLeapProfile"' in HTML
    assert 'id="sitePopulationArtifactState"' in HTML
    assert 'id="sitePopulationArtifactCopy"' in HTML
    assert ".site-population-leap-profile" in STYLE
    assert ".site-population-artifact" in STYLE
    assert "leapProfiles" in APP


def test_build_197_assets_and_narrative():
    assert 'buildId: "20260826-197"' in APP
    assert 'app.js?v=20260826-197' in HTML
    assert 'style.css?v=20260826-93' in HTML
    assert 'creation-response-association.js?v=20260826-4' in APP
    assert "Build 194" in README
    assert "Build 196" in README
    assert "Build 196" in DOCS
    assert "Build 197" in README
    assert "Build 197" in DOCS
    assert "Build 194" in DOCS
