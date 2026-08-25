#!/usr/bin/env python3
"""Contract for user-declared external driving geometry."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
README = (APP_DIR / "README.md").read_text()


def test_external_drive_is_target_blind_soft_ordering_only() -> None:
    for element_id in (
        "externalDriveSelect",
        "externalDriveWeightSelect",
        "externalDriveHint",
        "externalDriveBadge",
        "externalDriveGlyph",
        "externalDriveBadgeLabel",
    ):
        assert f'id="{element_id}"' in HTML

    for mode in ("none", "z-plus", "z-minus", "radial-out", "radial-in"):
        assert f'value="{mode}"' in HTML

    assert "function activeExternalDriveWeight()" in APP
    assert "function externalDriveModeLabel(mode = externalDriveMode)" in APP
    assert "function externalDriveForCandidate(candidate)" in APP
    assert "const externalDriveGroup = new THREE.Group()" in APP
    assert 'color: 0xf0c96a' in APP
    assert 'externalDriveMode === "radial-in"' in APP
    assert '"radial-out": "↗", "radial-in": "↙"' in APP
    assert "+ activeExternalDriveWeight() * evaluation.externalDrive.alignment" in APP
    assert 'id: "drive"' in APP
    assert 'label: `${externalDriveModeLabel()} ${activeExternalDriveWeight().toFixed(2)}`' in APP
    assert 'targetUsed: false' in APP
    assert 'candidateGeometryChanged: false' in APP
    assert 'physicalFieldSolved: false' in APP
    assert 'externalDrivingGeometry:' in APP
    assert 'globalAxis: externalDriveMode === "z-plus" ? [0, 0, 1]' in APP
    assert 'seedRelative: externalDriveMode === "radial-out" || externalDriveMode === "radial-in"' in APP
    assert 'externalDrive: [search.externalDrivingGeometry?.mode, search.externalDrivingGeometry?.effectiveWeight]' in APP
    assert '"external drive": {' in APP
    assert 'name: "external drive"' in APP
    assert "same candidate" in HTML.lower()

    assert "external driving geometry" in README.lower()
    assert "exact same cluster and" in README
    assert "a solved physical field" in README
    assert "candidateGeometryChanged=false" in README


if __name__ == "__main__":
    test_external_drive_is_target_blind_soft_ordering_only()
    print("external driving geometry contract: passed")
