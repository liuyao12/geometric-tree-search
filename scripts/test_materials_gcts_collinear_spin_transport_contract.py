"""Static contract for transporting supplied collinear scalar-spin colors."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_collinear_scalar_spin_reaches_marking_admission_and_receipt() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    coloring = (APP / "collinear-spin-coloring.js").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")
    benchmark = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(
        encoding="utf-8")

    assert 'from "./collinear-spin-coloring.js?v=20260827-1"' in source
    assert "calculationSpin: Number.isFinite(atom.calculationSpin)" in source
    assert "scalarSpinTemplateReferenceIndex: site.referenceIndex" in source
    assert "copyPlacedScalarSpin(atom, site)" in source
    assert "scalarSpinSitesCompatible(first, second)" in source
    assert "spinConflicts === 0" in source
    assert 'id: "scalar-spin-color"' in source
    assert "scalarSpinColorTransportAudit" in source
    assert "scalarSpinOverlapChecks" in source
    assert "scalarSpinCompatibilityPrunes" in source
    assert "drawClusterCardScalarSpins" in source
    assert "transportedScalarSpinColors" in source
    assert 'id="spinColoringSelect"' in html
    assert 'id="spinColoringHint"' in html
    assert "chemistry-only ablation" in html
    assert "vectorAxisInferred: false" in coloring
    assert "magneticEnergyInferred: false" in coloring
    assert 'buildId: "20260827-273"' in source
    assert 'app.js?v=20260827-273' in html
    assert "Build 250 makes supplied collinear scalar spin populations" in readme
    assert "Collinear scalar spin as an exact site color (Build 250)" in benchmark


if __name__ == "__main__":
    test_collinear_scalar_spin_reaches_marking_admission_and_receipt()
    print("collinear scalar-spin transport integration contract: passed")
