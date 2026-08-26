#!/usr/bin/env python3
"""Contract for nucleus-lineage-resolved morphology and scaling evidence."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_nucleus_morphology_contract() -> None:
    assert 'buildId: "20260825-145"' in APP
    assert 'app.js?v=20260825-145' in HTML
    for element_id in ("leapLineageSummary", "leapLineageList"):
        assert f'id="{element_id}"' in HTML
        assert f'$("{element_id}")' in APP
    for function_name in (
        "radiallyStratifiedIndices",
        "coordinationDeficitForIndices",
        "lineageMorphologyAudit",
    ):
        assert f"function {function_name}" in APP
    for field in (
        "fractionalAtomCount",
        "effectiveNucleusCount",
        "sharedInterfaceAtoms",
        "globalRadiusContainsInterNucleusSeparation",
        "sharedSitesCountedFractionallyForPopulation",
        "sharedSitesIncludedInEveryLineageShape",
        "crystallographicGrainIdentityInferred: false",
        "interfacialEnergyInferred: false",
    ):
        assert field in APP
    assert 'scope: "whole explicit configuration"' in APP
    assert 'massAccounting: "fractional shared-site population"' in APP
    assert 'radiusAccounting: "inclusive lineage geometry"' in APP
    assert 'value="lineageRadius"' in HTML
    assert 'value="nuclei"' in HTML
    assert 'value="shared"' in HTML
    assert ".leap-lineage-summary" in CSS
    assert ".leap-lineage-list" in CSS
    assert "Build 127" in README
    assert "not inferred grain identities" in README


if __name__ == "__main__":
    test_nucleus_morphology_contract()
    print("nucleus morphology contract passed")
