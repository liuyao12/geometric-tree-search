#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/ionic-pair-geometry.js").read_text()


def test_ionic_pair_cutoff_convergence_contract():
    assert 'buildId: "20260826-165"' in APP
    assert 'app.js?v=20260826-165' in HTML
    assert 'style.css?v=20260826-71' in HTML
    assert 'incrementalIonicPairReachProfile' in MODULE
    assert 'export function rankIonicPairReachProfiles' in MODULE
    assert 'rankIonicPairReachProfiles(candidates.map' in APP
    assert 'reaches: [2, 4, 8, "global"]' in APP
    assert 'function buildIonicPairConvergence(snapshot)' in APP
    assert 'function renderIonicPairConvergence(snapshot)' in APP
    assert 'function previewIonicConvergenceCandidate' in APP
    assert 'id="ionicConvergencePlot"' in HTML
    assert 'id="ionicConvergenceDetail"' in HTML
    assert '.ionic-convergence-plot .candidate-line.selected' in CSS
    assert '.ionic-convergence-plot .winner' in CSS
    assert 'ionicPairReachConvergence' in APP
    assert 'rankReversalCandidates' in APP
    assert 'uniqueReachWinners' in APP
    assert 'candidateSetChanged: false' in APP
    assert 'hardAdmissionChanged: false' in APP
    assert 'candidateGeometryChanged: false' in APP
    assert 'targetUsed: false' in APP
    assert 'dielectricOrEwaldConvergenceInferred: false' in APP
    assert 'thermodynamicLimitInferred: false' in APP
    assert 'Build 159 adds an interactive finite-reach convergence audit' in README


if __name__ == "__main__":
    test_ionic_pair_cutoff_convergence_contract()
    print("ionic-pair convergence contract passed")
