"""Source contract for target-independent external growth geometry."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_external_geometry_drives_render_search_and_receipt() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    source = (APP / "app.js").read_text(encoding="utf-8")
    environments = (APP / "growth-environments.js").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")

    for mode in ("box", "sphere", "cylinder", "slab", "substrate", "hourglass"):
        assert f'<option value="{mode}">' in html
        assert f"{mode}: {{" in environments

    assert "growthEnvironmentContains(confinementSelect.value, position)" in source
    assert "const spec = growthEnvironmentSpec(confinementSelect.value)" in source
    assert "externalGeometry: receiptExternalGeometry()" in source
    assert "parametersAngstrom" in source
    assert 'admissionRole: "hard target-independent public-boundary gate"' in environments
    assert "affectsCandidateGeometry: false" in environments
    assert "physicalPotentialUsed: false" in environments
    assert "epitaxialRegistryModeled: false" in environments
    assert "surfaceEnergyModeled: false" in environments
    assert "External geometry as a hard public boundary" in readme
    assert 'app.js?v=20260825-105' in html


if __name__ == "__main__":
    test_external_geometry_drives_render_search_and_receipt()
    print("external growth geometry contract: passed")
