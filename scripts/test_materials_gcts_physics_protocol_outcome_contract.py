#!/usr/bin/env python3
"""Portal contract for matched physics-protocol saved-run outcomes."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "apps" / "iqc-growth-live"


def main() -> None:
    source = (APP / "app.js").read_text()
    module = (APP / "physics-protocol-outcome.js").read_text()
    html = (APP / "index.html").read_text()
    alias = (ROOT / "iqc-growth-live" / "index.html").read_text()
    css = (APP / "style.css").read_text()
    readme = (APP / "README.md").read_text()
    docs = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text()

    for needle in (
        'from "./physics-protocol-outcome.js?v=20260827-2"',
        "function physicsProtocolControlVector()",
        "controlVector: physicsProtocolControlVector()",
        "function notebookPhysicsProtocolExperiment(receipt)",
        "physicsProtocolExperiment: notebookPhysicsProtocolExperiment(receipt)",
        "physicsPreflightManifest: { ...physicsPreflightManifest",
        "function renderNotebookPhysicsProtocolOutcome(selected)",
        "comparePhysicsProtocolOutcomes(selected)",
        "renderNotebookPhysicsProtocolOutcome(selected)",
        'schema: 4, records, counts',
        'buildId: "20260827-280"',
        'let growthSeedProtocol = "observed-window"',
        "function initializeObservedWindowSeed()",
        "seedProtocol: growthSeedAudit",
        "seedConfigurationDigest: search?.seedProtocol?.seedConfigurationDigest || null",
    ):
        assert needle in source, needle

    for needle in (
        "export function comparePhysicsProtocolOutcomes",
        '"controls-mismatch"',
        '"candidate-frontier-target-tainted"',
        '"candidate-identity-mismatch"',
        '"seed-identity-unavailable"',
        '"seed-mismatch"',
        '"history-truncated"',
        '"target-tainted"',
        "candidateSetMustRemainIdentical",
        "commonUpdates",
        "physicalTimeInferred: false",
        "causalPhysicalMechanismInferred: false",
    ):
        assert needle in module, needle

    for document in (html, alias):
        assert 'id="notebookPhysicsProtocolOutcome"' in document
        assert 'id="growthSeedProtocolSelect"' in document
        assert 'value="observed-window" selected' in document
        assert "all reversible controls" in document
        assert 'app.js?v=20260827-280' in document
    assert ".notebook-physics-protocol-outcome" in css
    assert ".notebook-physics-protocol-grid" in css
    assert "Build 269 · target-free observed-window growth" in readme
    assert "Target-free observed-window growth (Build 269)" in docs
    print("matched physics-protocol outcome portal contract: passed")


if __name__ == "__main__":
    main()
