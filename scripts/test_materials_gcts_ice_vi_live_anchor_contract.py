#!/usr/bin/env python3
"""Fast contract for the browser-visible sealed Ice-VI anchor trace."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"
ARTIFACT = APP_DIR / "ice-vi-anchor-trace-artifact.json"
MODULE = APP_DIR / "ice-vi-anchor-trace.js"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
NODE = Path("/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")


def main() -> None:
    artifact = json.loads(ARTIFACT.read_text())
    assert artifact["schema"] == "gcts-ice-vi-anchor-trace-v1"
    assert artifact["provenance"]["trainingMolecules"] == 123
    assert artifact["provenance"]["conformerTypes"] == 5
    assert artifact["provenance"]["frozenPorts"] == 84
    assert artifact["provenance"]["directedTypePairs"] == 20
    assert artifact["provenance"]["selectedParentWitnessThreshold"] == 2
    assert (artifact["provenance"]["calibrationCorrect"],
            artifact["provenance"]["calibrationWrong"]) == (23, 1)
    assert artifact["provenance"]["trainEvalCenterSeparation"] > artifact["provenance"]["requiredSeparation"]
    assert artifact["provenance"]["rawMoleculeIdOverlap"] == 0
    assert artifact["provenance"]["traceDigest"] == "b3697a7107f50b3aed43e1d525c86444aec1a0857a10e94e11959786a6b305fa"
    assert not any(artifact["provenance"][field] for field in (
        "targetUsed", "materialLabelUsed", "expectedFormulaUsed",
        "latticeSiteIndicesUsed", "energyOrPotentialUsed"))
    assert artifact["seedAnchors"] == len(artifact["seedSites"]) == 23
    assert tuple(wave["candidateAnchors"] for wave in artifact["waves"]) == (186, 316, 393, 408)
    assert tuple(wave["acceptedAnchors"] for wave in artifact["waves"]) == (4, 3, 1, 0)
    assert sum(wave["acceptedAnchors"] for wave in artifact["waves"]) == len(artifact["emittedAnchors"]) == 8
    assert artifact["unresolvedOrientationHypotheses"] == 8
    assert artifact["resolvedOrientationHypotheses"] == 0
    assert artifact["fixedPoint"] and artifact["exactBackendCountParity"]
    assert artifact["alternativesAreMutuallyExclusive"]
    assert not artifact["stationaryOrExponentialClaim"]

    script = f"""
      import fs from 'node:fs';
      import {{ executeFrozenIceViAnchorTrace }} from {json.dumps(MODULE.as_uri())};
      const artifact = JSON.parse(fs.readFileSync({json.dumps(str(ARTIFACT))}, 'utf8'));
      const trace = executeFrozenIceViAnchorTrace(artifact);
      if (trace.seedAnchors !== 23 || trace.portCount !== 84
          || trace.waves.map(w => w.acceptedAnchors).join(',') !== '4,3,1,0'
          || trace.unresolvedOrientationHypotheses !== 8 || trace.targetUsed) process.exit(2);
      const tainted = structuredClone(artifact); tainted.provenance.targetUsed = true;
      try {{ executeFrozenIceViAnchorTrace(tainted); process.exit(3); }} catch {{}}
    """
    subprocess.run((str(NODE), "--input-type=module", "-e", script), check=True)

    assert 'executeFrozenIceViAnchorTrace(ICE_VI_ANCHOR_TRACE_ARTIFACT)' in APP
    assert 'scenarioSelect.value === "iceVI"' in APP
    assert '&& (currentMaterial().icePolytype || scenarioSelect.value === "iceVI")' in APP
    assert 'iceAnchorTrace.portCount' in APP
    assert 'iceAnchorTrace.selectionRuleLabel' in APP
    assert 'iceAnchorTrace.orientationSpecies' in APP
    assert 'iceAnchorTrace.gapLabel' in APP
    assert 'function applyLaunchParameters()' in APP
    assert 'parameters.get("material")' in APP
    assert 'parameters.has("microstate")' in APP
    assert 'app.js?v=20260901-438' in HTML
    print("Ice VI live anchor trace contract: passed")


if __name__ == "__main__":
    main()
