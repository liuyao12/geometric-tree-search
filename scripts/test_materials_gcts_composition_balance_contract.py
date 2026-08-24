"""Browser integration contract for arbitrary-component reservoir balancing."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text(encoding="utf-8")
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text(encoding="utf-8")
README = (ROOT / "apps/iqc-growth-live/README.md").read_text(encoding="utf-8")


def test_composition_reservoir_is_soft_multicomponent_and_audited() -> None:
    assert 'from "./composition-balance.js?v=20260824-1"' in APP
    assert "learnCompositionTarget(referenceAtoms.map" in APP
    assert "compositionBalanceForFreshSites" in APP
    assert 'id="compositionPreferenceSelect"' in HTML
    assert "multicomponent soft balance" in HTML
    ranking = APP[APP.index("function commutingFrontierBatch()") : APP.index("function refineCandidateTranslation")]
    assert "activeCompositionBalanceWeight() * evaluation.compositionBalance.scaledDelta" in ranking
    admission = APP[APP.index("const accepted = conflicts") : APP.index("return { accepted", APP.index("const accepted = conflicts"))]
    assert "compositionBalance" not in admission
    assert "observed multicomponent fractions used only for optional soft frontier balancing" in APP
    assert "No oxidation state, formal charge" in README


if __name__ == "__main__":
    test_composition_reservoir_is_soft_multicomponent_and_audited()
    print("multicomponent composition reservoir integration contract: passed")
