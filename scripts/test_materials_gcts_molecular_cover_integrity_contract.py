#!/usr/bin/env python3
"""Static and receipt contract for Build 291's molecular set-cover proof."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_molecular_cover_proof_is_visible_and_interactive():
    assert 'id="molecularCoverProof"' in HTML
    assert '$("molecularCoverProof")' in APP
    assert "function molecularCoverIntegrityRecord()" in APP
    assert "function renderMolecularCoverProof()" in APP
    assert "dataset.molecularProofFocus" in APP
    assert "molecularCoverFocus = record.focus" in APP
    assert "buildClusterOverlay();" in APP
    assert ".molecular-cover-proof" in CSS
    assert ".molecular-cover-histogram" in CSS


def test_proof_separates_atom_closure_from_interstitial_geometry():
    for fragment in (
        "exactMolecularPartition",
        "connectionNovelAtomSites",
        "connectionSupportsAreOverlapOnly",
        "voidNovelAtomSites",
        "voidSupportsAreBoundaryOnly",
        "residualAtomSites",
        "ownershipHistogram",
        "⋃ ${moleculeLabel} supports = Ωatoms",
        "bridge supports ⊆ atom cover",
        "void boundaries ⊆ atom cover",
        "molecule-only atom closure",
        "no physical void volume is inferred",
    ):
        assert fragment in APP
    assert "molecularCoverIntegrity: molecularCoverIntegrityRecord()" in APP
    for boundary in (
        "referenceWindowOnly: true",
        "periodicReference: currentPbc().some(Boolean)",
        "targetUsed: false",
        "potentialUsed: false",
        "emptyVolumeInferred: false",
    ):
        assert boundary in APP


def test_build_and_narrative_are_current():
    assert "Build 291 · molecular set-cover integrity certificate" in README
    assert 'buildId: "20260901-450"' in APP
    assert 'app.js?v=20260901-450' in HTML
    assert 'style.css?v=20260901-450' in HTML


if __name__ == "__main__":
    test_molecular_cover_proof_is_visible_and_interactive()
    test_proof_separates_atom_closure_from_interstitial_geometry()
    test_build_and_narrative_are_current()
    print("molecular cover integrity contract passed")
