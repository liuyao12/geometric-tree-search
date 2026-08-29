#!/usr/bin/env python3
"""Portal contract for the target-free pre-growth physics protocol composer."""

from html.parser import HTMLParser
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "apps" / "iqc-growth-live"


class SelectOptionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.current_select = None
        self.options = {}

    def handle_starttag(self, tag, attrs) -> None:
        values = dict(attrs)
        if tag == "select" and values.get("id"):
            self.current_select = values["id"]
            self.options.setdefault(self.current_select, set())
        elif tag == "option" and self.current_select:
            self.options[self.current_select].add(values.get("value", ""))

    def handle_endtag(self, tag) -> None:
        if tag == "select":
            self.current_select = None


def main() -> None:
    source = (APP / "app.js").read_text()
    module = (APP / "physics-compression-map.js").read_text()
    html = (APP / "index.html").read_text()
    root_html = (ROOT / "iqc-growth-live" / "index.html").read_text()
    css = (APP / "style.css").read_text()

    option_parser = SelectOptionParser()
    option_parser.feed(html)
    bindings = re.findall(
        r'^\s*\["([^"]+)",\s*"([^"]+)",\s*"([^"]+)"', module, re.MULTILINE)
    assert len(bindings) == 31
    assert len({record_id for record_id, _, _ in bindings}) == len(bindings)
    for record_id, control_id, neutral_value in bindings:
        assert control_id in option_parser.options, (record_id, control_id)
        assert neutral_value in option_parser.options[control_id], (record_id, neutral_value)

    for needle in (
        'id="growthPhysicsProtocolComposer"',
        'id="growthPhysicsProtocolState"',
        'id="growthPhysicsProtocolCoverage"',
        'id="growthPhysicsProtocolSelection"',
        'id="growthPhysicsAblationSelect"',
        'id="growthPhysicsAblationDetail"',
        'id="growthPhysicsPairTracker"',
        'id="growthPhysicsPairTrackerSteps"',
        'id="growthPhysicsPairSave"',
        'id="growthPhysicsPairPartner"',
        'id="growthPhysicsPairOpen"',
        'data-physics-protocol-preset="executing"',
        'data-physics-protocol-preset="actionable"',
        'data-physics-protocol-preset="clear"',
        "freeze before the first candidate frontier",
        'app.js?v=20260829-329',
    ):
        assert needle in html, needle

    for needle in (
        "export function buildPhysicsInvestigationProtocol",
        "export function buildPhysicsProtocolIntervention",
        "export function buildPhysicsProtocolControlBinding",
        "export const PHYSICS_ABLATION_CONTROL_BINDINGS",
        'interventionKind: "explicit-neutral-control-value"',
        'state === "ready-to-configure"',
        '"shared-control-conflict"',
        '"already-neutral"',
        "exactlyOneControlChanges: readyToConfigure",
        "changedControlIds: readyToConfigure",
        'selectionMadeBeforeCandidateEnumeration: true',
        'candidateSetInspected: false',
        'coordinatesEmbedded: false',
        'targetUsed: false',
        'physicalTimeModeled: false',
        'state === "ready"',
        'Unready or evidence-only layers remain explicit',
        'exactlyOneSelectedLayerChanged: true',
        'otherProtocolLayersRemainByteIdentical: true',
        'candidateSetMustRemainIdentical',
        'first-frontier candidate digest must match',
    ):
        assert needle in module, needle

    for needle in (
        "buildPhysicsCompressionMap, buildPhysicsEffectMatrix, buildPhysicsInvestigationProtocol",
        "buildPhysicsLineagePath, buildPhysicsProtocolIntervention",
        "PHYSICS_ABLATION_CONTROL_BINDINGS",
        'from "./physics-compression-map.js?v=20260828-320"',
        "function physicsProtocolForRecords(records)",
        "function physicsProtocolControlSnapshot(recordId)",
        "function physicsProtocolControlVector()",
        "controlVector: physicsProtocolControlVector()",
        "function notebookPhysicsProtocolExperiment(receipt)",
        "comparePhysicsProtocolOutcomes(selected)",
        "buildPhysicsProtocolResponseFingerprint(audit)",
        'responseEyebrow.textContent = "structural response fingerprint"',
        'axes.setAttribute("aria-label", "Structural response domains")',
        "function applyPhysicsProtocolArm(interventionPlan, activeArm,",
        "function newPhysicsProtocolPairSessionId()",
        "function updatePhysicsProtocolSelection(recordIds)",
        "function renderPhysicsProtocolComposer(manifest)",
        "function renderPhysicsProtocolPairTracker(protocol)",
        "renderPhysicsProtocolPairTracker(frozenPhysicsPreflightManifest.investigationProtocol)",
        "function preparePhysicsProtocolPartner()",
        "buildPhysicsProtocolPairProgress(protocol, experimentNotebookEntries",
        "currentScenarioId: scenarioSelect.value",
        "currentSeedConfigurationDigest: growthSeedAudit?.seedConfigurationDigest",
        "currentPairSessionId: physicsProtocolPairSessionId",
        "buildPhysicsProtocolCampaignReadiness(experimentNotebookEntries",
        'campaignEyebrow.textContent = "registered replicate readiness"',
        "await saveCurrentExperimentNotebookEntry()",
        "selectedNotebookEntryIds = [...currentPhysicsPairProgress.selectedEntryIds]",
        "physicsProtocolAblatedRecordId",
        "physicsProtocolArmRegistration",
        "armRegistration: publicPhysicsProtocolArmRegistration",
        "const interventionPlan = physicsProtocolArmRegistration?.interventionPlan",
        'growthPhysicsAblationSelect.addEventListener("change"',
        "investigationProtocol: physicsProtocolForRecords(records)",
        'schema: 5, records, counts',
        'physicsPreflightManifest: { ...physicsPreflightManifest',
        'frozenBeforeFirstStructuralAction: Boolean(frozenPhysicsPreflightManifest)',
        'if (leapEventCount > 0) return;',
        'no control changed.',
        'buildId: "20260829-329"',
    ):
        assert needle in source, needle

    for needle in (
        ".physics-protocol-composer",
        ".physics-protocol-presets",
        ".physics-protocol-coverage",
        ".physics-protocol-selection",
        ".physics-protocol-intervention",
        ".physics-protocol-arm-buttons",
        ".physics-pair-tracker",
        ".physics-pair-steps",
        ".physics-protocol-selection button.ablated",
        ".protocol-selected",
        ".notebook-physics-protocol-outcome",
        ".notebook-physics-protocol-grid",
        ".notebook-physics-response",
        ".notebook-physics-response-axes",
        ".notebook-physics-response-detail",
        ".notebook-physics-campaign",
        ".notebook-physics-campaign-stats",
        ".notebook-physics-campaign-domains",
    ):
        assert needle in css, needle

    assert '<base href="../apps/iqc-growth-live/">' in root_html
    assert 'id="growthPhysicsProtocolComposer"' in root_html
    assert 'id="notebookPhysicsProtocolOutcome"' in html
    assert 'id="notebookPhysicsProtocolOutcome"' in root_html
    assert 'app.js?v=20260829-329' in root_html
    print("physics protocol composer portal contract: passed")


if __name__ == "__main__":
    main()
