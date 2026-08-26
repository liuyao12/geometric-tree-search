from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
ENV = (ROOT / "apps/iqc-growth-live/growth-environments.js").read_text()
ENVELOPE = (ROOT / "apps/iqc-growth-live/observation-envelope.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_public_domain_reach_is_user_declared_and_separate_from_input():
    assert 'id="growthDomainScaleSelect"' in HTML
    for scale in ("1", "2", "4"):
        assert f'value="{scale}"' in HTML
    assert "function scaledGrowthEnvironmentSpec(id, scale = 1)" in ENV
    assert "growthEnvironmentContains(confinementSelect.value, position, growthDomainScale)" in APP
    assert "growthEnvironmentSignedMargin(confinementSelect.value, site.p, growthDomainScale)" in APP


def test_domain_passport_distinguishes_replay_from_continuation():
    assert 'id="growthDomainPassport"' in HTML
    assert "function currentGrowthDomainSnapshot()" in APP
    assert "replayedObservedSites:" in APP
    assert "novelInsideObservationAtoms:" in APP
    assert "geometricContinuationAtoms:" in APP
    assert "continuationAtoms: observationClassification.beyond" in APP
    assert "fitObservationEnvelope" in APP
    assert "classifyObservationSites" in APP
    assert "export function observationEnvelopeSignedMargin" in ENVELOPE
    assert "only sites beyond its signed boundary count as geometric continuation" in APP
    assert "targetUsedForContinuation: false" in APP
    assert "periodicImagesImplied: false" in APP
    assert "domain: currentGrowthDomainSnapshot()" in APP
    assert 'value="continuationSites"' in HTML


def test_growth_reach_is_receipt_visible_but_does_not_authorize_geometry():
    assert "observationToGrowthDomain: currentGrowthDomainSnapshot()" in APP
    assert "publicReachScale: spec.publicReachScale" in ENV
    assert "affectsCandidateGeometry: false" in ENV
    assert "physicalPotentialUsed: false" in ENV
    assert "Build 133" in README
    assert "novelty is no longer mislabeled as spatial continuation" in README
    assert 'buildId: "20260825-138"' in APP
    assert 'app.js?v=20260825-138' in HTML
