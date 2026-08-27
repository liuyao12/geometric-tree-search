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
    assert "not a causal effect, calibrated material predictor, energy relation, kinetic law" in APP
    assert "creationResponseLeapProfile" in MODULE
    assert 'id="sitePopulationLeapProfile"' in HTML
    assert 'id="sitePopulationArtifactState"' in HTML
    assert 'id="sitePopulationArtifactCopy"' in HTML
    assert ".site-population-leap-profile" in STYLE
    assert ".site-population-artifact" in STYLE
    assert "leapProfiles" in APP
    assert "blockedCreationResponseSurrogate" in MODULE
    assert 'id="sitePopulationSurrogate"' in HTML
    assert ".site-response-surrogate" in STYLE
    assert "blockedSurrogates" in APP
    assert "surrogatePredictionsEmbeddedInFullReceipt: true" in APP
    assert "fitUsedHeldout: false" in MODULE
    assert "featureSelectionUsedOutcome: false" in MODULE
    assert "heldoutFeatureSupportCoverage" in MODULE
    assert "maximumStandardizedFeatureExcess" in MODULE
    assert "featureSupportDefinition" in MODULE
    assert ".site-surrogate-support" in STYLE
    assert ".site-surrogate-coefficients" in STYLE
    assert "quadraticControl" in MODULE
    assert "modelSelectedUsingHeldout: false" in MODULE
    assert "maximumInteractingBaseFeatures: 6" in MODULE
    assert ".site-surrogate-coefficients.interactions" in STYLE
    assert "structuralContext" in APP
    assert "createdBeforeBatchCommit: true" in APP
    assert "contextFeatures" in APP
    assert "includeStructuralContext" in MODULE
    assert 'source: "structural-context"' in MODULE
    assert "contextualBlockedSurrogates" in APP
    assert ".site-surrogate-coefficients.context" in STYLE
    assert "structural-state support transfer" in APP
    assert "skill is not an interpolation test" in APP
    assert ".site-surrogate-support.context" in STYLE
    assert "LOCAL_CREATION_CONTEXT_FEATURE_IDS" in MODULE
    assert "contextFeatureIds" in MODULE
    assert "supportedHeldoutSkillVersusTrainingMean" in MODULE
    assert "localContextBlockedSurrogates" in APP
    assert "local attachment-state transfer" in APP
    assert ".site-surrogate-support.local-context" in STYLE
    assert "interpolationReadiness" in MODULE
    assert '"full-interpolation"' in MODULE
    assert '"mixed-domain"' in MODULE
    assert '"extrapolation-only"' in MODULE
    assert "minimumSupportedPlacementsForSubsetSkill" in MODULE
    assert "featureEnvelopeChosenUsingHeldout: false" in MODULE
    assert "site-surrogate-readiness" in APP
    assert ".site-surrogate-readiness" in STYLE
    assert "creationResponseHorizonSweep" in MODULE
    assert "horizonSelectedUsingHeldout: false" in MODULE
    assert "allPredeclaredHorizonsReported: true" in MODULE
    assert "localContextHorizonSweeps" in APP
    assert "site-surrogate-horizons" in APP
    assert ".site-surrogate-horizons" in STYLE
    assert "crossRunHorizonReadinessAtlas" in MODULE
    assert "placementRowsPooled: false" in MODULE
    assert "modelsRefitAcrossRuns: false" in MODULE
    assert "independentRunsAssumed: false" in MODULE
    assert "notebookResponseReadiness" in APP
    assert "renderNotebookResponseReadiness" in APP
    assert "cross-run response readiness" in HTML
    assert ".notebook-response-readiness" in STYLE
    assert "notebookResponseReadinessDetail" in APP
    assert "horizon microscope" in APP
    assert "maximum envelope excess" in APP
    assert "largest frozen standardized coefficients" in APP
    assert "notebook-response-readiness-detail" in HTML
    assert ".notebook-response-feature-panel" in STYLE


def test_build_197_assets_and_narrative():
    assert 'buildId: "20260827-245"' in APP
    assert 'app.js?v=20260827-245' in HTML
    assert 'style.css?v=20260827-245' in HTML
    assert 'creation-response-association.js?v=20260826-13' in APP
    assert "Build 194" in README
    assert "Build 196" in README
    assert "Build 196" in DOCS
    assert "Build 197" in README
    assert "Build 197" in DOCS
    assert "Build 198" in README
    assert "Build 198" in DOCS
    assert "Build 199" in README
    assert "Build 199" in DOCS
    assert "Build 200" in README
    assert "Build 200" in DOCS
    assert "Build 201" in README
    assert "Build 201" in DOCS
    assert "Build 202" in README
    assert "Build 202" in DOCS
    assert "Build 203" in README
    assert "Build 203" in DOCS
    assert "Build 204" in README
    assert "Build 204" in DOCS
    assert "Build 205" in README
    assert "Build 205" in DOCS
    assert "Build 206" in README
    assert "Build 206" in DOCS
    assert "0/142" in README
    assert "0/142" in DOCS
    assert "Build 194" in DOCS
