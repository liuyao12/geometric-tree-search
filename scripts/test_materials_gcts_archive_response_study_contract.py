#!/usr/bin/env python3
"""Static release contract for the guided public archive response study."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()


def main() -> None:
    assert 'id: "archive-response", kind: "public calculation"' in APP
    assert 'publicArchive: WORKED_PUBLIC_ARCHIVE.id' in APP
    assert 'preferredFrameIndex: 4' in APP
    assert 'factor: "archived response metric"' in APP
    assert 'settings: { affineLoadMode: "archive-response" }' in APP
    assert 'settings: { affineLoadMode: "none" }' in APP
    assert '"continuation sites", "frontier work", "S(q) response"' in APP
    assert 'scenarioSelect.value === "imported" && importedStructure?.metadata?.entryId === recipe.publicArchive' in APP
    assert 'checks.comparisonAffineLoad = affineLoadMode === armSettings.affineLoadMode' in APP
    assert 'checks.selectedArchiveFrame = importedFrameIndex === recipe.preferredFrameIndex' in APP
    assert 'if (recipe?.publicArchive) url.searchParams.set("specimen", `nomad:${recipe.publicArchive}`)' in APP
    assert 'loadWorkedPublicArchive({ updateAddress: false }).then((loaded)' in APP
    assert 'buildId: "20260827-265"' in APP
    assert 'app.js?v=20260827-265' in HTML
    assert 'style.css?v=20260827-265' in HTML
    print("Archive-response guided study contract passed")


if __name__ == "__main__":
    main()
