#!/usr/bin/env python3
"""Contract for archived stress as a bounded tensor-shaped geometric metric."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"
APP = (APP_DIR / "app.js").read_text(encoding="utf-8")
DATABASE = (APP_DIR / "structure-database.js").read_text(encoding="utf-8")
HTML = (APP_DIR / "index.html").read_text(encoding="utf-8")
README = (APP_DIR / "README.md").read_text(encoding="utf-8")


def test_archived_stress_is_explicit_bounded_geometry() -> None:
    assert 'stress: Object.freeze({ id: "stress"' in DATABASE
    assert 'calculation?.stress?.total?.value' in DATABASE
    assert 'stressTensorGigaPascal' in DATABASE
    assert 'stressHydrostaticGigaPascal' in DATABASE
    assert 'stressDeviatoricFrobeniusGigaPascal' in DATABASE
    assert 'stressArchiveUnit: "Pa"' in DATABASE
    assert 'stressUnit: "GPa"' in DATABASE
    assert 'stressUsedForGrowth: false' in DATABASE
    assert 'stress: "*"' in DATABASE

    for mode in ("archive-stress", "archive-stress-reverse"):
        assert f'value="{mode}"' in HTML
        assert f'"{mode}"' in APP
    assert 'normalizedStressShapeDeformation' in APP
    assert 'calculation-stress' in APP
    assert 'stressTensorSha256' in APP
    assert 'stressAffineMetricMode' in APP
    assert 'exact coordinates and hard admission never change' in APP
    assert 'unit-compliance' in APP

    normalized_readme = " ".join(README.split())
    assert "Build 253" in README
    assert "F = I + m σ / ||σ||F" in README
    assert "exact candidate coordinates and every hard admission gate are unchanged" in normalized_readme
    assert "not an elastic tensor, modulus" in normalized_readme


if __name__ == "__main__":
    test_archived_stress_is_explicit_bounded_geometry()
    print("archived stress geometry contract: passed")

