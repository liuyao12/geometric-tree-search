from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
DB = (ROOT / "apps/iqc-growth-live/structure-database.js").read_text()
IO = (ROOT / "apps/iqc-growth-live/structure-io.js").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/collinear-spin-geometry.js").read_text()

assert 'app.js?v=20260831-400' in HTML
assert 'collinear-spin-geometry.js?v=20260826-1' in APP
for element_id in ("spinGeometryState", "spinMapSelect", "spinMapState",
                   "spinCorrelationPlot", "spinMapExtremes", "spinGeometryDetail"):
    assert f'id="{element_id}"' in HTML
assert 'magnetic moment in μ<sub>B</sub>' in HTML
assert 'no arrows' in HTML

assert 'charges: "*"' in DB
assert 'calculation?.charges' in DB
assert 'atomicSpinSourcePath' in DB
assert 'atomicSpinUnit: null' in DB
assert 'atomicSpinAxisAvailable: false' in DB
assert 'atomicSpinsUsedForGrowth: false' in DB
assert 'calculationSpin' in DB
assert 'calculationSpin' in IO and 'frame.spins || root.spins' in IO

assert 'analyzeCollinearSpinGeometry' in MODULE
for invariant in ("translationInvariant: true", "properRotationInvariant: true",
                  "permutationInvariant: true", "globalSpinSignPairInvariant: true"):
    assert invariant in MODULE
for boundary in ("vectorAxisInferred: false", "magneticMomentUnitInferred: false",
                 "exchangeEnergyInferred: false", "magneticHamiltonianInferred: false",
                 "temperatureOrOrderingTransitionInferred: false"):
    assert boundary in MODULE

assert 'collinearSpinGeometry:' in APP
assert 'usedForClusterIdentification: false' in APP
assert 'usedForMarkingLearning: false' in APP
assert 'usedForCandidateGeneration: false' in APP
assert 'usedForAdmission: false' in APP
assert 'usedForBranchRanking: false' in APP
assert 'vectorArrowsDisplayed: false' in APP
assert 'id: "collinear-spin"' in APP
assert 'spinMapMode === "polarity"' in APP
assert '["polarity", "correlation"].includes(spinMapSelect.value)' in APP
assert 'activeSpinWeight' not in APP
assert 'spinRanking' not in APP

print("collinear spin portal: ingestion, visualization, provenance, and non-use boundaries passed")
