#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/ionic-pair-geometry.js").read_text()


def test_incremental_ionic_pair_geometry_contract():
    assert 'buildId: "20260826-165"' in APP
    assert 'app.js?v=20260826-165' in HTML
    assert 'from "./ionic-pair-geometry.js?v=20260826-2"' in APP
    assert "export function incrementalIonicPairGeometry" in MODULE
    assert "export function incrementalIonicPairReachProfile" in MODULE
    assert "first.charge * second.charge / normalizedDistance" in MODULE
    assert "incrementalPairsOnly: true" in MODULE
    assert "currentCurrentConstantOmitted: true" in MODULE
    assert "coulombKernelUsed: true" in MODULE
    assert "ewaldSummationUsed: false" in MODULE
    assert "electrostaticEnergyInferred: false" in MODULE

    for control in ("ionicPairSelect", "ionicPairReachSelect", "ionicPairWeightSelect"):
        assert f'id="{control}"' in HTML
        assert f'$("{control}")' in APP
    assert '<option value="madelung">' in HTML
    assert '<option value="global">Global finite configuration</option>' in HTML
    assert 'scoreTerm("ionic-pair"' in APP
    assert 'activeIonicPairWeight() * evaluation.ionicPair.score' in APP
    assert 'id: "ionic-pair", process: "incremental ionic pair interaction geometry' in APP
    assert '"ionic-pair": { stage: 4, controlId: "ionicPairSelect"' in APP
    assert "incrementalIonicPairRanking" in APP
    assert "ionicPairDistanceEvaluations" in APP
    assert '"ionic pair geometry"' in APP

    for nonclaim in (
        "No Coulomb prefactor", "dielectric response", "periodic images", "Ewald sum",
        "neutralizing background", "polarization", "electronic structure", "physical time",
    ):
        assert nonclaim in APP
    assert "Build 158 adds an optional dimensionless incremental ionic-pair" in README


if __name__ == "__main__":
    test_incremental_ionic_pair_geometry_contract()
    print("ionic-pair geometry contract passed")
