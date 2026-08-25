#!/usr/bin/env python3
"""Contract for the measurement-to-geometry provenance chain."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
CSS = (APP_DIR / "style.css").read_text()
README = (APP_DIR / "README.md").read_text()


def test_observation_provenance_chain_is_explicit_and_target_free() -> None:
    for element_id in (
        "observationProvenanceState",
        "observationProvenance",
        "observationProvenanceDetail",
    ):
        assert f'id="{element_id}"' in HTML

    assert "function observationProvenanceRecords()" in APP
    assert "function renderObservationProvenance()" in APP
    assert 'id: "conditions"' in APP
    assert 'id: "samples"' in APP
    assert 'id: "uncertainty"' in APP
    assert 'id: "tolerance"' in APP
    assert 'id: "representation"' in APP
    assert 'id: "growth"' in APP
    assert "simulationControlChannelsFromRecordedConditions: 0" in APP
    assert "coordinatesEmbedded: false" in APP
    assert "never passed into clustering, marking, candidate enumeration, or ranking" in APP
    assert "cross-frame atom pairs are never invented" in APP
    assert "Temperature, pressure, environment, snapshot ordering" in APP
    assert "renderObservationProvenance();" in APP

    assert ".observation-provenance" in CSS
    assert ".observation-provenance-detail" in CSS
    assert "observation → geometry provenance" in README
    assert "zero simulation-control channels" in README


if __name__ == "__main__":
    test_observation_provenance_chain_is_explicit_and_target_free()
    print("observation provenance contract: passed")
