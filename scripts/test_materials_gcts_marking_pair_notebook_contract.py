from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOC = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_compact_summary_retains_registration_and_first_frontier_identity():
    assert "markingComparisonExperiment: search?.markingComparisonExperiment || null" in APP
    assert "firstFrontierCandidateSetDigest" in APP
    assert "firstFrontierHardAdmittedSetDigest" in APP
    assert "firstFrontierTargetUsed" in APP
    assert "firstMarkingFrontier?.hardAdmittedCandidateSetDigest" in APP


def test_registered_marking_pair_is_checked_independently():
    assert "function notebookRegisteredMarkingPairAudit" in APP
    for invariant in (
        "sameRegistration", "sameArtifacts", "sameFrozenSource", "sameGrowthControls",
        "complementaryArms", "artifactsIntact", "geometryFrozen",
        "targetFreeRegistration", "explicitlyPaused", "oneRecordedFactor",
    ):
        assert invariant in APP
    assert 'intervention.changedFactors[0].key === "marking"' in APP
    assert "firstFrontierComparable" in APP
    assert "firstCandidateDigest === secondCandidateDigest" in APP
    assert "firstHardDigest === secondHardDigest" in APP
    assert "const responseComparable = valid && baselineExecuted && alternativeExecuted" in APP


def test_pair_fails_closed_but_retains_scientific_boundary():
    assert "saved-marking pair not certified" in APP
    assert "do not expose one identical target-free first candidate and hard-admitted set" in APP
    assert "deterministic algorithmic response" in APP
    assert "not an independent specimen" in APP
    assert "physical-time" in DOC
    assert "Build 217" in README
    assert "Build 217" in DOC


def test_build_217_assets_are_cache_busted():
    assert 'buildId: "20260827-254"' in APP
    assert 'app.js?v=20260827-254' in HTML


if __name__ == "__main__":
    test_compact_summary_retains_registration_and_first_frontier_identity()
    test_registered_marking_pair_is_checked_independently()
    test_pair_fails_closed_but_retains_scientific_boundary()
    test_build_217_assets_are_cache_busted()
    print("marking pair notebook contract passed")
