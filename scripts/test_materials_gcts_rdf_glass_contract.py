"""Browser contract for dimension-aware partial RDFs and the glass control."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_browser_uses_a_real_amorphous_negative_control_and_partial_rdf() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")

    assert 'import { generateAmorphousMixture } from "./amorphous-glass.js?v=20260824-1"' in source
    assert 'if (scenario === "random") return makeMetallicGlassReference()' in source
    assert 'periodicWindow: true, order: "amorphous"' in source
    assert 'currentMaterial().order !== "amorphous"' in source
    assert "rdfCountsByPair" in source
    assert "intrinsicDimension === 2" in source
    assert 'edgeCorrection: periodic ? "periodic minimum image" : "finite-window translation"' in source
    assert "rdfTailSummary" in source
    assert 'id="rdfPairSelect"' in html
    assert "An amorphous RDF has short-range peaks but should approach g(r)=1" in source
    assert "generatorAudit: scenarioSelect.value === \"random\"" in source
    assert "continuous random positions" in readme
    assert "no longer starts from a jittered cubic grid" in readme
    assert "neither a target RDF" in readme
    assert "short-range peaks" in readme


if __name__ == "__main__":
    test_browser_uses_a_real_amorphous_negative_control_and_partial_rdf()
    print("dimension-aware partial RDF and amorphous control contract: passed")
