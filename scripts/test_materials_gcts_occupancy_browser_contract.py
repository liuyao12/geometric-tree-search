from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
IO = (ROOT / "apps/iqc-growth-live/structure-io.js").read_text()


def test_lossless_occupancy_contract_is_wired_through_browser_pipeline():
    assert "occupancyAlternatives" in IO
    assert "mergeSiteOccupancies(existing, site, true)" in IO
    assert "occupancyChemistryToken" in APP
    assert "species: occupancyChemistryToken(atom)" in APP
    assert "occupationally disordered sites use the irregular colored-support route" in APP
    assert "alternativesCollapsedToPrimarySpecies: false" in APP
    assert "occupancyRingGeometry" in APP
    assert "conic-gradient" in APP


if __name__ == "__main__":
    test_lossless_occupancy_contract_is_wired_through_browser_pipeline()
    print("occupational-disorder browser contract: passed")
