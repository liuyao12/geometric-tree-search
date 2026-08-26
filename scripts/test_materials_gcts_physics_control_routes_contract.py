#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_physics_control_routes_contract():
    assert "const PHYSICS_CONTROL_ROUTES = Object.freeze" in APP
    assert "function openPhysicsControlRoute" in APP
    assert "if (pipelineStage !== route.stage) enterPipelineStage(route.stage)" in APP
    assert 'const group = control.closest("details")' in APP
    assert "if (group) group.open = true" in APP
    assert 'control.focus({ preventScroll: true })' in APP
    assert "no setting changed" in APP
    assert "No local control · requires external physics or a new geometric state variable" in APP
    assert 'connection: { stage: 3, controlId: "markingRepresentationSelect"' in APP

    routes = {
        "steric": "clusterToleranceSelect",
        "connection": "markingRepresentationSelect",
        "chemistry": "compositionPreferenceSelect",
        "charge-geometry": "chargeGeometrySelect",
        "charge-moment": "chargeMomentSelect",
        "solute-partition": "solutePartitionSelect",
        "bulk-surface-driving": "growthDrivingSelect",
        "attachment-topology": "attachmentTopologySelect",
        "habit-anisotropy": "habitAnisotropySelect",
        "defect-precursors": "defectPrecursorSelect",
        "coherency-memory": "coherencyMemorySelect",
        "capillary-geometry": "capillaryGeometrySelect",
        "epitaxy": "epitaxyTemplateSelect",
        "thermal-field": "thermalFieldSelect",
        "microstructure": "microstructureCouplingSelect",
        "multi-nucleus": "growthNucleiSelect",
        "loop-closure": "loopClosurePreferenceSelect",
        "feed-exposure": "feedExposureSelect",
        "kinetics": "arrivalPathSelect",
        "path-ensemble": "explorationScaleSelect",
    }
    for record, control in routes.items():
        assert record in APP
        assert f'controlId: "{control}"' in APP

    assert ".leap-physics-actions" in CSS
    assert ".physics-control-target" in CSS
    assert "Build 152 makes the live **physics → geometry translation** operational" in README
    assert "leaves its value untouched" in README


if __name__ == "__main__":
    test_physics_control_routes_contract()
    print("physics control routes contract passed")
