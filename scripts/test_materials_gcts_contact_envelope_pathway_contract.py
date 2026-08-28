from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
FIT = (ROOT / "apps/iqc-growth-live/contact-envelope-fit.js").read_text()
VOID = (ROOT / "apps/iqc-growth-live/interstitial-clearance.js").read_text()


def test_sample_fitted_contact_envelope_is_a_visible_audited_corridor_model():
    assert '<option value="fitted">sample-fitted contacts</option>' in HTML
    assert 'fitAdditiveContactEnvelope' in APP
    assert 'fittedContactRadiiAngstrom' in APP
    assert 'sampleFittedEnvelopeCertificate' in APP
    assert 'selectedViewUsesSampleFittedContactEnvelope' in APP
    assert 'fit residual' in APP
    assert 'fittedStericClearance' in VOID
    assert 'fittedStericThroatClearance' in VOID
    assert 'widestFittedStericPeriodicClearance' in VOID


def test_fit_is_train_only_residual_audited_and_not_a_physical_radius_claim():
    for token in (
        'leading observed colored-contact shell',
        'priorDependentParameterCount',
        'rmsResidualAngstrom',
        'physicalRadiusIdentityInferred: false',
        'oxidationStateOrCoordinationSpecificRadiusInferred: false',
        'energyOrPotentialFitted: false',
        'targetUsed: false',
        'usedAsGrowthInput: false',
    ):
        assert token in FIT
    assert 'Cordero radii supply only a scale/ratio regularizer' in FIT


def test_build_243_assets_are_cache_versioned():
    assert 'buildId: "20260827-281"' in APP
    assert 'app.js?v=20260827-281' in HTML
    assert 'style.css?v=20260827-281' in HTML
    assert 'contact-envelope-fit.js?v=20260827-1' in APP
    assert 'interstitial-clearance.js?v=20260827-10' in APP
