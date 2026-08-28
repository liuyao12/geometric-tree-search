from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/creation-response-association.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_split_is_blocked_between_complete_structural_leaps():
    assert "leapIndex: Math.min(...emittedAtoms.map((atom) => atom.createdAtLeap))" in APP
    assert "blockedCreationResponseValidation" in APP
    assert "trainingLeaps = leapIndices.slice(0, trainingBlockCount)" in MODULE
    assert "heldoutLeaps = leapIndices.slice(trainingBlockCount)" in MODULE
    assert "blockedByCompleteStructuralLeap: true" in MODULE
    assert "randomSplitUsed: false" in MODULE


def test_term_selection_never_reads_heldout_response():
    assert "trainingAudit.associations" in MODULE
    assert MODULE.index("const selected = candidates[0]") < MODULE.index("const heldoutAudit")
    assert "selectionUsedHeldout: false" in MODULE
    assert "signRetained" in MODULE
    assert "minimumSamplesPerSplit: 8" in APP


def test_validation_is_visible_and_fails_closed():
    assert 'id="sitePopulationValidation"' in HTML
    assert '$("sitePopulationValidation")' in APP
    assert ".site-population-response > article.retained" in STYLE
    assert ".site-population-response > article.reversed" in STYLE
    assert "blocked validation unavailable" in APP
    assert "frozen term has insufficient variation or support" in MODULE
    assert "causalEffectInferred: false" in MODULE
    assert "independentMaterialSamples: false" in MODULE


def test_post_reconstruction_caption_reports_actual_continuation():
    assert "const reconstructionWasCertified = reconstructionCertified" in APP
    assert '"compressed-grammar continuation"' in APP
    assert "!reconstructionWasCertified && reconstructionCertified" in APP


def test_build_195_assets_and_narrative():
    assert 'buildId: "20260827-273"' in APP
    assert 'app.js?v=20260827-273' in HTML
    assert 'style.css?v=20260827-273' in HTML
    assert 'creation-response-association.js?v=20260826-13' in APP
    assert "Build 195" in README
    assert "Build 195" in DOCS
