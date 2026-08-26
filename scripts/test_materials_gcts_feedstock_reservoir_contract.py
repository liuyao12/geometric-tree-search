from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/feedstock-reservoir.js").read_text()


def test_finite_inventory_is_distinct_from_soft_composition_balance():
    assert 'value="open" selected>Open source' in HTML
    for mode in ("finite-1", "finite-4", "finite-16"):
        assert f'value="{mode}"' in HTML
    assert "initializeFeedstockReservoir" in MODULE
    assert "evaluateFeedstockDemand" in MODULE
    assert "compositionBalanceForFreshSites" in APP
    assert "feedstockSupplyForFreshSites" in APP


def test_species_supply_is_a_hard_atomic_action_and_batch_gate():
    assert "&& angularViolations.length === 0 && feedstockSupply.admitted" in APP
    assert "if (!feedstockSupplyForFreshSites(trialFresh).admitted) continue" in APP
    assert "consumeFeedstockForFreshSites(evaluation.fresh)" in APP
    assert "feedstock exhausted:" in APP
    assert 'name: "feedstock inventory", status: state.feedstockSupply?.admitted ? "pass" : "fail"' in APP


def test_inventory_is_visible_in_leaps_notebook_and_receipt():
    assert 'id="feedstockInventoryInspector"' in HTML
    assert 'id="feedstockInventoryBars"' in HTML
    assert "feedstock: currentFeedstockSnapshot()" in APP
    assert 'value="feedstockRemaining"' in HTML
    assert "feedstockInventory:" in APP
    assert "observedSeedConsumesInventory: false" in APP
    assert "chemicalPotentialInferred: false" in MODULE
    assert "physicalTimeModeled: false" in MODULE
    assert "Build 131" in README
    assert 'buildId: "20260826-159"' in APP
    assert 'app.js?v=20260826-159' in HTML
