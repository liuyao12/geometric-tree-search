"""Contract for measurement-condition provenance without simulated thermodynamics."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"


def test_recorded_conditions_are_visible_but_never_controls() -> None:
    parser = (APP_DIR / "structure-io.js").read_text(encoding="utf-8")
    source = (APP_DIR / "app.js").read_text(encoding="utf-8")
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    css = (APP_DIR / "style.css").read_text(encoding="utf-8")

    assert '"_diffrn_ambient_temperature"' in parser
    assert '"_diffrn_ambient_pressure"' in parser
    assert '"_diffrn_ambient_environment"' in parser
    assert '"_cell_measurement_temperature"' in parser
    assert '"_cell_measurement_pressure"' in parser
    assert 'unit: "K"' in parser
    assert 'unit: "kPa"' in parser
    assert "recorded diffraction/cell-measurement conditions" in parser

    assert 'id="measurementConditions"' in html
    assert 'id="measurementConditionChips"' in html
    assert "renderMeasurementConditions()" in source
    assert "activeMeasurementConditions()" in source
    assert ".measurement-conditions" in css

    for boundary in (
        "usedAsSimulationControl: false",
        "temperatureInferred: false",
        "pressureInferred: false",
        "synthesisConditionsClaimed: false",
        "thermodynamicStateReconstructed: false",
    ):
        assert boundary in source

    assert "growthTemperature" not in source
    assert "simulationPressure" not in source


if __name__ == "__main__":
    test_recorded_conditions_are_visible_but_never_controls()
    print("measurement conditions contract: passed")
