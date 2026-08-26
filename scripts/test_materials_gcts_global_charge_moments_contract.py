#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/global-charge-moments.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_global_charge_moments_contract():
    assert 'buildId: "20260826-157"' in APP
    assert 'app.js?v=20260826-157' in HTML
    for control in ("chargeMomentSelect", "chargeMomentWeightSelect", "chargeMomentHint"):
        assert f'id="{control}"' in HTML
        assert f'$("{control}")' in APP
    for mode in ("none", "dipole", "quadrupole", "combined"):
        assert f'value="{mode}"' in HTML
    assert "chargeMomentSignature" in MODULE
    assert "compareChargeMomentGeometry" in MODULE
    assert "properRotationInvariant: true" in MODULE
    assert "uniformScaleInvariant: true" in MODULE
    assert "electrostaticEnergyInferred: false" in MODULE
    assert "electronicStructureModeled: false" in MODULE
    assert 'id: "charge-moment"' in APP
    assert 'controlId: "chargeMomentSelect"' in APP
    assert "globalChargeMomentRanking" in APP
    assert "candidateSetChanged: false" in APP
    assert "heldoutTargetUsed: false" in APP
    assert "Build 155" in README


if __name__ == "__main__":
    test_global_charge_moments_contract()
    print("global charge moments contract passed")
