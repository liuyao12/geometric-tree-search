"""Source contract for the claim-bounded heterogeneous-geometry audit."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_microstructure_audit_is_visible_reproducible_and_non_generative() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    source = (APP / "app.js").read_text(encoding="utf-8")
    audit = (APP / "microstructure-audit.js").read_text(encoding="utf-8")
    css = (APP / "style.css").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")
    normalized_readme = " ".join(readme.split())

    assert 'from "./microstructure-audit.js?v=20260824-1"' in source
    assert "function learnMicrostructureEvidence()" in source
    assert "function buildMicrostructureLedger()" in source
    assert "function drawMicrostructureProjection(" in source
    assert "function buildMicrostructureProjection()" in source
    assert 'ledger.className = "microstructure-ledger"' in source
    assert "heterogeneousGeometryAudit: receiptMicrostructureAudit()" in source
    assert "classByPlacement.set(placementIndex, classIndex)" in source
    assert "classifyPlacementPoseOrbits" in source

    assert "gapBoundaryTypeIds" in audit
    assert "coordinationBaselines" in audit
    assert "crossPoseContacts" in audit
    assert "siteRoles: atoms.map" in audit
    assert "occupationalAlternativeSites" in audit
    assert "defectLabelsGiven: false" in audit
    assert "grainBoundaryClaimed: false" in audit
    assert "defectFormationEnergyModeled: false" in audit
    assert "literalTerminalsPromoted: false" in audit
    assert "gapBoundaryClassesEmitAtoms: false" in audit
    assert "gapBoundaryClassesReusableAsConstraints: true" in audit
    assert ".microstructure-ledger" in css
    assert ".microstructure-map" in css
    assert ".microstructure-grid" in css
    assert "heterogeneous-geometry audit" in readme
    assert "not automatic vacancy, dislocation, grain, or grain-boundary labels" in normalized_readme

    # Frozen local roles may choose an observed initial seed, but they must not
    # alter candidate geometry, admission, action ranking, or marking training.
    search_logic = source[source.index("function ruleMarkingScore"):source.index("function renderMarkingLibrary")]
    assert search_logic.count("microstructureEvidence") == 1
    assert "const roleByIndex = new Map((microstructureEvidence?.siteRoles || [])" in search_logic
    assert "candidateGeometryChanged: false" in search_logic
    assert "heldoutTargetUsed: false" in search_logic
    assert "const { adjacencyReach, coordinationBaselines, siteRoles, ...audit }" in source
    assert 'app.js?v=20260825-126' in html


if __name__ == "__main__":
    test_microstructure_audit_is_visible_reproducible_and_non_generative()
    print("geometric microstructure UI/receipt contract: passed")
