#!/usr/bin/env python3
"""Contract for the training-only parent-local habit atlas."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_habit_atlas_is_training_only_equivariant_and_soft() -> None:
    for element_id in ("habitAnisotropySelect", "habitAnisotropyWeightSelect", "habitAnisotropyHint"):
        assert f'id="{element_id}"' in HTML
    for mode in ("none", "faceted", "roughening", "axial"):
        assert f'value="{mode}"' in HTML
    for weight in ("0.12", "0.24", "0.48"):
        assert f'value="{weight}"' in HTML

    assert "function habitAnisotropyForCandidate(" in APP
    assert "new Array(BALANCE_DIRECTIONS.length).fill(0)" in APP
    assert "rule.fitCount ?? rule.count" in APP
    assert 'trainingSupportField: "fitCount only; heldout count excluded"' in APP
    assert "axis.clone().applyQuaternion(parentRotation)" in APP
    assert "totalSupport <= 0 ? 0" in APP
    assert 'id: "habit-anisotropy"' in APP
    assert "activeHabitAnisotropyWeight() * evaluation.habitAnisotropy.score" in APP
    assert "habitAnisotropyRanking" in APP
    assert 'name: "habit anisotropy"' in APP
    assert "candidate.habitAnisotropy.spokes" in APP

    for invariant in (
        "candidateSetChanged: false", "candidateGeometryChanged: false", "hardAdmissionChanged: false",
        "heldoutTargetUsed: false", "surfaceEnergyInferred: false", "wulffConstructionInferred: false",
        "millerIndicesInferred: false", "kineticCoefficientInferred: false", "latticeRequired: false",
        "physicalTimeIntegrated: false",
    ):
        assert invariant in APP
    for protocol_mode in ("faceted", "roughening", "axial"):
        assert f'habitAnisotropyMode: "{protocol_mode}"' in APP

    normalized = " ".join(README.split())
    assert "Training-only local habit atlas" in README
    assert "held-out support is explicitly excluded" in normalized
    assert "preserves the score" in normalized
    assert "not surface free energy, a Wulff construction" in normalized
    assert "cannot authorize a pose" in normalized


if __name__ == "__main__":
    test_habit_atlas_is_training_only_equivariant_and_soft()
    print("materials GCTS habit-anisotropy contract: passed")
