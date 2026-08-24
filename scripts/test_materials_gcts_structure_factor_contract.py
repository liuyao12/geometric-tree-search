"""Browser contract for the reciprocal-space structural evidence view."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_powder_structure_factor_is_interactive_and_posthoc_only() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    observable = (APP / "structure-observables.js").read_text(encoding="utf-8")

    assert 'id="structureObservableSelect"' in html
    assert 'value="sq">reciprocal space · S(q)' in html
    assert "powderStructureFactor" in source
    assert 'structureObservableSelection === "sq"' in source
    assert 'drawChartFrame(rdfChart, "q a", "S")' in source
    assert "Math.sin(value) / value" in observable
    assert "dimension === 2 ? besselJ0(value)" in observable
    assert "function intrinsicPlaneNormal(source)" in source
    assert "directVector.dot(planeNormal) ** 2" in source
    assert "unit scattering weights" in source
    assert "omits X-ray form factors" in source
    assert "not experimental intensity or a growth input" in source
    assert "structureFactorError" in source
    assert 'if (pipelineStage < 4) return {' in source
    assert 'order: "not classified"' in source
    assert "evaluated only after Material Growth begins" in source
    assert source.count("powderStructureFactor") == 2, "S(q) may be imported and evaluated only in the evidence cache"
    assert 'role: "posthoc validation only; never a growth feature or branch score"' in source
    assert "experimentalIntensityClaimed: false" in source


if __name__ == "__main__":
    test_powder_structure_factor_is_interactive_and_posthoc_only()
    print("interactive posthoc powder S(q) contract: passed")
