"""Browser integration contract for supplied formal oxidation-state bookkeeping."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text(encoding="utf-8")
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text(encoding="utf-8")
README = (ROOT / "apps/iqc-growth-live/README.md").read_text(encoding="utf-8")


def test_formal_charge_is_optional_soft_ranking_and_never_inferred() -> None:
    assert 'from "./formal-charge-balance.js?v=20260824-1"' in APP
    assert "learnFormalChargeTarget(referenceAtoms.map" in APP
    assert "formalChargeBalanceForFreshSites" in APP
    assert 'id="chargePreferenceSelect"' in HTML
    assert 'id="chargePreferenceHint"' in HTML
    assert 'id="chargeValue"' in HTML
    assert "if (!formalChargeTarget?.available || chargePreference === \"none\") return 0" in APP
    ranking = APP[APP.index("function commutingFrontierBatch()") : APP.index("function refineCandidateTranslation")]
    assert "activeFormalChargeWeight() * evaluation.formalChargeBalance.scaledDelta" in ranking
    admission = APP[APP.index("const accepted = conflicts") : APP.index("return { accepted", APP.index("const accepted = conflicts"))]
    assert "formalChargeBalance" not in admission
    assert "oxidationStatesInferred: false" in APP
    assert "The app never guesses common oxidation states" in README
    assert "not charge density, Coulomb energy, redox chemistry" in APP


if __name__ == "__main__":
    test_formal_charge_is_optional_soft_ranking_and_never_inferred()
    print("formal oxidation-state reservoir integration contract: passed")
