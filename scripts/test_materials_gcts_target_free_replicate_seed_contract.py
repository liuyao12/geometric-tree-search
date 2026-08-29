#!/usr/bin/env python3
"""Contract for fitted local nuclei that never activate known-window replay."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "apps" / "iqc-growth-live"


def main() -> None:
    source = (APP / "app.js").read_text()
    html = (APP / "index.html").read_text()
    alias = (ROOT / "iqc-growth-live" / "index.html").read_text()

    for document in (html, alias):
        assert '<option value="local-frontier">Local occurrence nucleus · target-free continuation</option>' in document

    for needle in (
        'mode === "local-frontier"',
        'function knownWindowReplayActive()',
        'return growthSeedProtocol === "reconstruct" && !reconstructionCertified;',
        'function targetFreeGrowthAuthorized()',
        'growthSeedProtocol === "local-frontier"',
        'knownWindowReplayRequested: growthSeedProtocol === "reconstruct"',
        'targetFreeContinuationAuthorized: growthSeedProtocol === "local-frontier"',
        'seedSelectionMode: nucleationSiteMode',
        'Remaining observed sites are neither snapped to nor scored',
        'const audit = knownWindowReplayActive() ? referenceCoverageAudit()',
        'const reconstructing = targetAware && knownWindowReplayActive()',
        'const relaxationAuthorized = targetFreeGrowthAuthorized()',
        'targetFreeGrowthAuthorized: targetFreeGrowthAuthorized()',
        'exactKnownWindowReplay: growthSeedProtocol === "reconstruct" ? reconstructionCertified : null',
        'seedSelectionMode: search?.seedProtocol?.seedSelectionMode || null',
        'Use Local occurrence nucleus and change the observed nucleation site',
    ):
        assert needle in source, needle

    assert source.count("knownWindowReplayActive()") >= 20
    assert 'buildId: "20260829-328"' in source
    print("target-free replicate seed contract: passed")


if __name__ == "__main__":
    main()
