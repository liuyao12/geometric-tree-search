"""Source contract for identical-frontier soft-physics comparisons."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"


def test_policy_comparison_reuses_one_hard_admitted_frontier() -> None:
    html = (APP_DIR / "index.html").read_text()
    source = (APP_DIR / "app.js").read_text()
    readme = (APP_DIR / "README.md").read_text()

    assert 'id="policyComparison"' in html
    assert "same frozen frontier" in html
    assert "Admission geometry is identical in every row" in html
    assert "function capturePolicyComparison(entries)" in source
    assert "const admissible = entries.filter((entry) => entry.evaluation.accepted)" in source
    assert "capturePolicyComparison(evaluated)" in source
    for label in ("mark + recurrence", "elastic 0.16", "composition 0.35", "formal charge 0.25", "surface 0.18", "combined greedy", "active greedy", "sampled T*"):
        assert label in source
    assert 'referenceGuided: !reconstructionCertified' in source
    assert 'candidateSetTargetUsed: false' in source
    assert 'rankingTargetUsed: !reconstructionCertified' in source
    assert '" · target-aware replay" : " · target-blind frontier"' in source
    assert "generic ranks unused" in source
    assert "same already-enumerated, hard-admitted candidate set" in readme


if __name__ == "__main__":
    test_policy_comparison_reuses_one_hard_admitted_frontier()
    print("identical-frontier physics-policy comparison contract: passed")
