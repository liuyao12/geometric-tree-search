#!/usr/bin/env python3
"""Static contract for durable, shareable material-workflow routes."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
ATLAS = (ROOT / "apps/iqc-growth-live/evidence-atlas.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_workflow_routing_contract():
    assert "function synchronizeWorkflowAddress" in APP
    assert 'url.searchParams.set("material", material)' in APP
    assert 'url.searchParams.set("stage", String(pipelineStage))' in APP
    assert 'url.searchParams.set("microstate", String(iceViMicrostate.audit.seed))' in APP
    assert 'url.searchParams.delete("specimen")' in APP
    assert 'url.searchParams.delete("study")' in APP
    assert 'window.history[method]({ gctsWorkflow: true, material, stage: pipelineStage }' in APP
    assert "function launchMaterialsWorkflowRoute" in APP
    assert "window.gctsMaterialsWorkflow = Object.freeze" in APP
    assert 'window.addEventListener("popstate", restoreWorkflowRouteFromAddress)' in APP
    assert 'synchronizeWorkflowAddress({ mode: "push" })' in APP
    assert 'if (event.isTrusted) synchronizeWorkflowAddress({ mode: "push", clearStudy: true })' in APP
    assert "window.gctsMaterialsWorkflow?.launch({ scenario, stage, preparation })" in ATLAS

    assert 'buildId: "20260829-335"' in APP
    assert 'app.js?v=20260829-335' in HTML
    assert 'style.css?v=20260829-335' in HTML
    assert 'evidence-atlas.js?v=20260829-335' in HTML
    assert "Build 309 · durable workflow routes" in README


if __name__ == "__main__":
    test_workflow_routing_contract()
    print("workflow routing contract: passed")
