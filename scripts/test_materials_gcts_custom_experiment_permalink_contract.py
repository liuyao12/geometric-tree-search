#!/usr/bin/env python3
"""Static contract for versioned, fail-closed custom experiment permalinks."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(fragment: str) -> None:
    assert fragment in APP, fragment


def test_custom_experiment_permalink_contract() -> None:
    require("const CUSTOM_EXPERIMENT_SCHEMA_VERSION = 1")
    require("const CUSTOM_EXPERIMENT_MAX_PAYLOAD_LENGTH = 12_000")
    for exclusion in (
        "coordinatesEmbedded: false",
        "learnedWeightsEmbedded: false",
        "activeMarkingIdEmbedded: false",
        "growthHistoryEmbedded: false",
        "targetCoordinatesEmbedded: false",
        "recomputeFromPositions: true",
    ):
        require(exclusion)

    require("function customExperimentManifest()")
    require("function encodeCustomExperimentPayload(manifest)")
    require("function decodeCustomExperimentPayload(payload)")
    require("function validateCustomExperimentManifest(manifest, materialParameter)")
    require("function exactObjectKeys(value, expected)")
    require("function selectAcceptsSerializedValue(select, value)")
    require('material === "imported"')
    require('url.searchParams.set("experimentVersion", String(CUSTOM_EXPERIMENT_SCHEMA_VERSION))')
    require('url.searchParams.set("experiment", encodeCustomExperimentPayload(manifest))')
    require('url.searchParams.set("material", manifest.input.material)')
    require('url.searchParams.set("stage", String(pipelineStage))')
    require("function synchronizeLoadedCustomExperimentAddress()")
    require('window.history.replaceState({}, "", fresh)')

    manifest = APP[APP.index("function customExperimentManifest"):APP.index("function encodeCustomExperimentPayload")]
    for control in (
        "geometryMode", "clusterToleranceMode", "markingDraft.channels", "markingDraft.reach",
        "markingDraft.representation", "scalarSpinColoringMode()", "markingSearchMode",
        "policySelect.value", "growthProtocolMode", "currentGrowthProtocolSettings()",
        "structureObservableSelection", "orientationalOrderHarmonic",
    ):
        assert control in manifest
    assert "referenceAtoms" not in manifest
    assert "trainedMarking" not in manifest
    assert "activeMarkingId" not in manifest
    assert "atoms:" not in manifest

    launch_start = APP.index("function applyLaunchParameters")
    launch = APP[launch_start:APP.index("restoreMarkingLibrary();", launch_start)]
    for fragment in (
        'requestedExperimentVersion !== String(CUSTOM_EXPERIMENT_SCHEMA_VERSION)',
        "decodeCustomExperimentPayload(requestedExperiment)",
        "validateCustomExperimentManifest(decoded, parameters.get(\"material\"))",
        "applyGrowthProtocolSettings(manifest.growth.settings",
        'activeMarkingId = ""',
        'activeExternalCalibrationMarkingId = ""',
        "if (customExperimentLaunchAudit) return 0",
    ):
        assert fragment in launch
    assert "setPlaying(true)" not in launch

    require('studyCompassShare.textContent = studyShareUrl ? "Copy study link"')
    require(': experimentShareUrl ? "Copy experiment link" : "Link unavailable"')
    require("function copyShareableInvestigationUrl()")
    assert 'app.js?v=20260828-315' in HTML
    assert 'style.css?v=20260828-315' in HTML
    assert 'evidence-atlas.js?v=20260828-315' in HTML
    assert 'buildId: "20260828-315"' in APP
    assert "Build 310 · reconstructable custom investigations" in README
    assert "contains no atomic coordinates" in README
    assert "fail closed at known positions" in README


if __name__ == "__main__":
    test_custom_experiment_permalink_contract()
    print("custom experiment permalink contract: passed")
