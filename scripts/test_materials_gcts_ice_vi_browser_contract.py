from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()


def test_published_disordered_ice_is_selectable_and_provenanced():
    assert '<option value="iceVI">Ice VI · disordered D₂O average · COD 1567346</option>' in HTML
    assert 'molecularFixture: "ice-vi-cod-1567346-average"' in APP
    assert "generateIceViAverageObservation" in APP
    assert 'countLabel: "400 average sites · 240 occupancy-weighted atoms"' in APP
    assert "ICE_VI_BROWSER_FIXTURE.normalizedAtomsSha256" in APP


def test_average_structure_never_invents_one_molecular_assignment():
    assert 'species: resolved ? atom.species : occupancyChemistryToken(site)' in APP
    assert 'occupationally disordered sites use the irregular colored-support route' in APP
    assert 'uniqueMolecularAssignmentClaimed: false' in APP
    assert 'declines a unique D₂O partition' in APP
    assert 'growth withheld' in APP
    assert 'function decorateIceViOxygenVoidBoundaries' in APP
    assert 'hydrogenOccupancyUsed: false' in APP
    assert 'expectedRingSizeUsed: false' in APP
    assert 'shortest chordless O${learnedCover.voidBoundary.ringSize} boundaries' in APP
    assert 'if (currentMaterial().growthWithheld)' in APP
    assert 'renderConstraintLedger(null, "withheld")' in APP
    assert 'average sites are not emitted atoms' in APP
    assert 'playButton.disabled = pipelineStage === 4 && Boolean(material.growthWithheld)' in APP


def test_ice_rule_microstate_is_optional_geometry_only_and_audited():
    assert 'id="iceViMicrostateControls"' in HTML
    assert 'id="iceViMicrostateButton"' in HTML
    assert 'id="iceViAverageButton"' in HTML
    assert "resolveIceViIceRuleMicrostate" in APP
    assert 'name: "ice VI · sampled D₂O microstate"' in APP
    assert 'growthWithheld: false' in APP
    assert 'realizationSeed: iceViMicrostate.audit.seed' in APP
    assert 'Sample a different ice-rule microstate' in APP
    assert 'Return to diffraction average' in HTML
    assert 'moleculeClasses: 1' in APP
    assert 'observedMetricConformers: molecularConformers.length' in APP
    assert 'waterCover.placements.filter((placement) => placement.family !== "gap")' in APP
    assert 'O${minimumRingSize} gap' in APP
    assert '8 exact O anchors · poses unresolved' in APP
    assert 'forced whole-molecule continuation produces three wrong sites' in APP


def test_curated_occupancy_reaches_receipt_and_display():
    assert 'material.crystallographicOccupancy ? {' in APP
    assert 'alternativesCollapsedToPrimarySpecies: false' in APP
    assert 'currentMaterial()?.recordedMeasurementConditions || null' in APP
    assert 'provenance.countLabel' in APP


if __name__ == "__main__":
    test_published_disordered_ice_is_selectable_and_provenanced()
    test_average_structure_never_invents_one_molecular_assignment()
    test_ice_rule_microstate_is_optional_geometry_only_and_audited()
    test_curated_occupancy_reaches_receipt_and_display()
    print("ice VI browser disorder contract: passed")
