#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_charge_shape_leap_path_contract():
    assert 'buildId: "20260826-161"' in APP
    assert 'app.js?v=20260826-161' in HTML
    assert 'style.css?v=20260826-68' in HTML
    assert "function structuralChargeMomentSnapshot" in APP
    assert APP.count("chargeMoment: structuralChargeMomentSnapshot()") >= 6
    assert "historyAlignment: \"discrete certified structural leap; not physical time\"" in APP
    assert "historyTruncated: leapEventCount > leapHistory.length" in APP
    assert "executedHistory" in APP
    assert "retainedLeapIndices" in APP
    assert 'class: "executed-path"' in APP
    assert "executed-state" in APP
    assert "renderStructuralLeap(leapHistory[selectedLeapIndex])" in APP
    assert ".charge-shape-portrait .executed-path" in CSS
    assert ".charge-shape-portrait .executed-state" in CSS
    assert '<i class="history"></i>executed leap pathway' in HTML
    assert "supplied-charge moments" in APP
    assert "Build 157" in README


if __name__ == "__main__":
    test_charge_shape_leap_path_contract()
    print("charge-shape leap path contract passed")
