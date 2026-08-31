from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
ALIAS_HTML = (ROOT / "iqc-growth-live/index.html").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/external-physics-request.mjs").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
BENCHMARK = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_external_physics_request_is_visible_and_downloadable():
    required_app_fragments = (
        'buildExternalPhysicsRequest',
        'externalPhysicsConfigurationPayload',
        'externalPhysicsRequestPackage',
        'downloadExternalPhysicsRequest',
        'data-dynamical-evidence-export',
        'Download external-physics request',
        'coordinatesEmbeddedInReceipt: false',
        'coordinatesEmbeddedInLocalDownload: true',
        'submittedToExternalService: false',
        'targetCoordinatesEmbedded: false',
        'externalPhysicsRequestExport: externalPhysicsRequestExportReceipt',
        'buildId: "20260830-342"',
    )
    for fragment in required_app_fragments:
        assert fragment in APP


def test_export_schema_covers_all_six_physical_quantities_and_fails_closed():
    for quantity in ('trajectory', 'clock', 'barrier', 'free-energy', 'probability', 'forces'):
        assert f'{quantity}:' in MODULE or f'"{quantity}":' in MODULE
    for fragment in (
        'gcts-external-physics-request-v1',
        'coordinateUnits: "angstrom"',
        'submittedToExternalService: false',
        'targetCoordinatesEmbedded: false',
        'geometricScoresUsedAsEnergyLabels: false',
        'searchStepsUsedAsPhysicalTime: false',
        'physicalInferenceRemainsOpen: true',
    ):
        assert fragment in MODULE


def test_build_338_is_documented_and_cache_busted():
    for document in (HTML, ALIAS_HTML):
        assert 'app.js?v=20260830-342' in document
        assert 'style.css?v=20260830-342' in document
        assert 'evidence-atlas.js?v=20260830-342' in document
        assert 'returned JSON can be validated against the exact request' in document
    assert 'Build 338 · export a calculation-ready external-physics request' in README
    assert 'Calculation-ready external-physics handoff (Build 338)' in BENCHMARK
    assert 'Nothing is submitted' in README
    assert 'target coordinates are absent' in BENCHMARK


def main() -> None:
    test_external_physics_request_is_visible_and_downloadable()
    test_export_schema_covers_all_six_physical_quantities_and_fails_closed()
    test_build_338_is_documented_and_cache_busted()
    print("external physics request portal contract: passed")


if __name__ == "__main__":
    main()
