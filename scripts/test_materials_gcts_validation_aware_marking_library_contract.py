#!/usr/bin/env python3
"""Static contract for Build 298's validation-aware marking library."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def require(source: str, needle: str) -> None:
    assert needle in source, f"missing contract text: {needle}"


def test_validation_aware_marking_library_contract() -> None:
    require(APP, "function markingValidationAuditRecord()")
    require(APP, 'schema: "gcts-heldout-channel-sign-v1"')
    require(APP, "const validationAudit = markingValidationAuditRecord()")
    require(APP, "marking.validationAudit = validationAudit")
    require(APP, "function markingValidationLabel(marking)")
    require(APP, "heldoutBalancedAccuracy")
    require(APP, 'row.classList.toggle("validation-weak"')
    require(APP, "heldoutSignAudit: activeMarking.validationAudit || null")
    require(APP, 'buildId: "20260828-310"')
    require(HTML, 'app.js?v=20260828-310')
    require(HTML, 'style.css?v=20260828-310')
    require(STYLE, ".marking-portfolio-rows > article.validation-weak")
    require(README, "Build 298 · validation-aware marking library")
    require(README, "validation never alters the")


if __name__ == "__main__":
    test_validation_aware_marking_library_contract()
    print("validation-aware marking library contract passed")
