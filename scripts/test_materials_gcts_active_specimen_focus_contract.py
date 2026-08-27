#!/usr/bin/env python3
"""Static release contract for the active-specimen passport and focus microscope."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "apps/iqc-growth-live/index.html").read_text()
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()


def require(source: str, token: str) -> None:
    assert token in source, f"missing release-contract token: {token}"


for identifier in (
    "activeSamplePassport",
    "activeSampleName",
    "activeSampleSource",
    "activeSampleFormula",
    "activeSampleSiteCount",
    "activeSampleComposition",
    "activeSampleGeometry",
    "activeSampleEvidence",
    "activeSampleNote",
    "stageFocusToggle",
):
    require(INDEX, f'id="{identifier}"')

require(INDEX, "Search a random real material")
require(INDEX, 'aria-label="Active specimen passport"')
require(INDEX, 'aria-pressed="false"')

for token in (
    "function activeSampleCompositionRecords(",
    "function reducedSampleFormula(",
    "function renderActiveSamplePassport(",
    "function renderStageFocus(",
    "function setStageFocus(",
    "renderActiveSamplePassport(material);",
    'stageFocusToggle.addEventListener("click"',
    'event.key === "Escape" && stageFocusEnabled',
    'document.body.classList.toggle("stage-focus", stageFocusEnabled)',
):
    require(APP, token)

for token in (
    ".active-sample-passport",
    ".active-sample-composition",
    ".active-sample-facts",
    ".stage-focus-toggle",
    ".stage-focus .control-panel",
    ".stage-focus .inspector-panel",
    ".stage-focus .viewport",
):
    require(STYLE, token)

assert "display: none" in STYLE[STYLE.index(".stage-focus .evidence-ribbon"):STYLE.index(".stage-focus .lab-grid")]
print("active specimen + focus microscope contract passed")
