"""Source contract for interactive, non-executing pathway-sensitivity previews."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"


def test_policy_sensitivity_history_is_frozen_and_coordinate_free() -> None:
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    source = (APP_DIR / "app.js").read_text(encoding="utf-8")
    css = (APP_DIR / "style.css").read_text(encoding="utf-8")
    readme = (APP_DIR / "README.md").read_text(encoding="utf-8")

    for element_id in ("policySensitivityState", "policyHistory", "policyPreviewState"):
        assert f'id="{element_id}"' in html

    assert "function frozenFrontierDigest(entries)" in source
    assert "candidateSetTargetUsed: false" in source
    assert "rankingTargetUsed: !reconstructionCertified" in source
    assert "policyComparisonHistory.push(lastPolicyComparison)" in source
    assert "if (policyComparisonHistory.length > 48)" in source
    assert "function previewPolicyWinner(policy, snapshot)" in source
    assert "const frontierReadout = { value: frontierMetric.textContent, detail: frontierDelta.textContent }" in source
    assert "frontierMetric.textContent = frontierReadout.value" in source
    assert "Preview the ${policy.label} winner without executing it" in source
    assert 'row.setAttribute("aria-pressed"' in source
    assert "frontiers disagree" in source

    preview = source[source.index("function previewPolicyWinner"):source.index("function renderPolicyComparison")]
    for forbidden in ("atoms.push", "materializeCandidate", "placedClusters.push", "frontierCandidates ="):
        assert forbidden not in preview

    assert "policySensitivity: {" in source
    assert "candidateCoordinatesEmbedded: false" in source
    assert "candidateSetDigest: snapshot.candidateDigest" in source
    assert "selectedCandidateDigest: policy.candidateDigest" in source
    receipt_section = source[source.index("policySensitivity: {"):source.index("finiteIceAnchorTrace:")]
    for forbidden in ("policy.preview", "preview.p", "preview.rotation", "candidateKey: policy.candidateKey"):
        assert forbidden not in receipt_section

    assert ".policy-history" in css
    assert ".policy-comparison button" in css
    assert "clicking it previews" in readme
    assert "without executing the action" in readme
    assert "Candidate enumeration is always target-free" in readme


if __name__ == "__main__":
    test_policy_sensitivity_history_is_frozen_and_coordinate_free()
    print("interactive policy sensitivity contract: passed")
