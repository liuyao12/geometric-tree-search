from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
ALIAS_HTML = (ROOT / "iqc-growth-live/index.html").read_text()
REQUEST = (ROOT / "apps/iqc-growth-live/external-physics-request.mjs").read_text()
RESPONSE = (ROOT / "apps/iqc-growth-live/external-physics-response.mjs").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
BENCHMARK = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()


def test_returned_physics_validation_is_interactive_and_receipted():
    for fragment in (
        'validateExternalPhysicsResponse',
        'externalPhysicsResponseInput',
        'validateReturnedExternalPhysicsFile',
        'data-external-physics-response',
        'Validate returned result',
        'externalPhysicsResponseValidation: externalPhysicsResponseValidationReceipt',
        'rawResultsEmbeddedInReceipt: false',
        'candidateSetChanged: false',
        'candidateRankingChanged: false',
        'buildId: "20260831-391"',
    ):
        assert fragment in APP
    assert 'id="externalPhysicsResponseInput"' in HTML
    assert 'accept=".json,application/json"' in HTML
    assert '.external-physics-response-status' in STYLE


def test_response_contract_is_request_linked_and_quantity_specific():
    for fragment in (
        'EXTERNAL_PHYSICS_RESPONSE_SCHEMA',
        'permittedStructureSha256',
        'protocolMatchesRequest',
        'containsGrowthTargetCoordinates: false',
    ):
        assert fragment in REQUEST
    for quantity in ('trajectory', 'clock', 'barrier', 'free-energy', 'probability', 'forces'):
        assert f'{quantity}:' in RESPONSE or f'"{quantity}":' in RESPONSE
    for fragment in (
        'response request SHA-256 does not match',
        'response configuration SHA-256 does not match',
        'response has not passed every frozen validation gate',
        'eligibleAsTransferableLaw: false',
        'usedForCandidateRanking: false',
        'usedAsPotential: false',
        'usedAsPhysicalClock: false',
    ):
        assert fragment in RESPONSE


def test_build_339_is_documented_and_cache_busted():
    for document in (HTML, ALIAS_HTML):
        assert 'app.js?v=20260831-391' in document
        assert 'style.css?v=20260831-391' in document
        assert 'evidence-atlas.js?v=20260831-391' in document
        assert 'returned JSON can be validated against the exact request' in document
    assert 'Build 339 · validate the returned physics evidence' in README
    assert 'Request-linked returned-evidence validation (Build 339)' in BENCHMARK
    assert 'It does not alter candidate geometry' in README
    assert 'candidate generation,\nranking, geometry, potential use, and physical-time use remain false' in BENCHMARK


def main() -> None:
    test_returned_physics_validation_is_interactive_and_receipted()
    test_response_contract_is_request_linked_and_quantity_specific()
    test_build_339_is_documented_and_cache_busted()
    print("external physics response portal contract: passed")


if __name__ == "__main__":
    main()
