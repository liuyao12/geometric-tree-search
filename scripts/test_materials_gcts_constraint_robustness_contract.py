#!/usr/bin/env python3
"""Contract for target-blind geometric constraint-margin ordering."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()
ENVIRONMENTS = (APP_DIR / "growth-environments.js").read_text()


def test_constraint_robustness_is_soft_target_blind_ordering() -> None:
    for element_id in (
        "robustnessPreferenceSelect",
        "robustnessWeightSelect",
        "robustnessHint",
    ):
        assert f'id="{element_id}"' in HTML
    assert 'value="margin"' in HTML
    for weight in ("0.12", "0.24", "0.48"):
        assert f'value="{weight}"' in HTML

    assert "export function growthEnvironmentSignedMargin(id, point, scale = 1)" in ENVIRONMENTS
    assert "function constraintRobustnessForCandidate(fresh, merged)" in APP
    assert "coloredPairExclusion(site.species, atom.species)" in APP
    assert "growthEnvironmentSignedMargin(confinementSelect.value, site.p, growthDomainScale)" in APP
    assert "MERGE_TOLERANCE - site.p.distanceTo(atom.p)" in APP
    assert "Math.tanh(normalizedMinimum / 2)" in APP
    assert "+ activeRobustnessWeight() * evaluation.constraintRobustness.score" in APP
    assert 'id: "robustness"' in APP
    assert "constraintRobustnessRanking:" in APP

    for nonclaim in (
        "candidateGeometryChanged: false",
        "hardAdmissionChanged: false",
        "targetUsed: false",
        "temperatureModeled: false",
        "probabilityInferred: false",
        "freeEnergyInferred: false",
        "perturbationEnsembleUsedForRanking: false",
    ):
        assert nonclaim in APP

    assert "geometric robustness" in README.lower()
    assert "never changes the" in README
    assert "not a pose" in README
    assert "post-decision validation" in README


if __name__ == "__main__":
    test_constraint_robustness_is_soft_target_blind_ordering()
    print("constraint robustness contract: passed")
