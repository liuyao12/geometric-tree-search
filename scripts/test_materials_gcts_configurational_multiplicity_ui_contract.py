from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
NORMALIZATION = (ROOT / "apps/iqc-growth-live/score-normalization.mjs").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_configurational_multiplicity_is_a_complete_score_channel():
    required = (
        'from "./configurational-multiplicity.mjs?v=20260828-316"',
        'scoreTerm("configurational-multiplicity"',
        'activeConfigurationalMultiplicityWeight() * evaluation.configurationalMultiplicity.score',
        'configurationalMultiplicityRanking',
        'id: "configurational-entropy"',
        'controlId: "configurationalMultiplicitySelect"',
        'configurationalMultiplicitySelect.addEventListener("change"',
        'thermodynamicEntropyInferred: false',
        'fitSupportOnly: true',
    )
    for fragment in required:
        assert fragment in APP
    for control in (
        "configurationalMultiplicitySelect",
        "configurationalMultiplicityWeightSelect",
        "configurationalMultiplicityHint",
    ):
        assert f'id="{control}"' in HTML
    assert '"configurational-multiplicity": "configurational-entropy"' in NORMALIZATION
    assert "Build 304" in README


if __name__ == "__main__":
    test_configurational_multiplicity_is_a_complete_score_channel()
    print("configurational multiplicity UI contract passed")
