#!/usr/bin/env python3
"""Static integration contract for Build 285's material-consequence decisiveness stage."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(fragment: str, source: str = APP) -> None:
    assert fragment in source, f"missing material-decisiveness fragment: {fragment}"


def main() -> None:
    require('const materialChangedFields = [...(shadow?.materialConsequence?.changedFields || [])]')
    require('{ id: "material", changed: materialChanged }')
    require('materialChangedFieldCount: materialChangedFields.length')
    require('materialChangingChannels: channels.filter((entry) => entry.materialChanged).length')
    require('{ id: "material", label: "material" }')
    require('{ id: "material", label: "material fingerprint" }')
    require('material: "MATERIAL FINGERPRINT CHANGED"')
    require('history.changedFrontiersByStage.material')
    require('materialChangedFields: [...entry.materialChangedFields]')
    require('physicalTimeModeled: false')
    require('causalHierarchyInferred: false')
    require('<span>material</span>', HTML)
    require('<option value="material">material fingerprint</option>', HTML)
    require('repeat(7, minmax(28px, .62fr))', CSS)
    require('Build 285 · material-consequence decisiveness pathway', README)
    require('application: { name: "Materials Growth Lab", buildId: "20260828-323" }')
    print("material-consequence decisiveness contract passed")


if __name__ == "__main__":
    main()
