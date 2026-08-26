"""Source contract for the live geometry-as-physics decision ledger."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"


def test_constraint_ledger_covers_admission_and_ranking_terms() -> None:
    html = (APP_DIR / "index.html").read_text()
    source = (APP_DIR / "app.js").read_text()
    style = (APP_DIR / "style.css").read_text()

    assert 'id="constraintLedger"' in html
    assert 'id="constraintDetail"' in html
    assert "geometry-as-physics ledger" in html
    assert 'style.css?v=20260825-46' in html
    assert 'app.js?v=20260825-133' in html
    assert 'function renderConstraintLedger(state, mode = "configured")' in source
    assert "function geometryConstraintEvidence(name, term, state, mode)" in source
    assert "function renderConstraintDetail(term, state, mode)" in source
    assert 'row.setAttribute("aria-pressed"' in source
    assert 'row.addEventListener("click"' in source
    for field in ("observed evidence", "geometric encoding", "role in search", "claim boundary"):
        assert field in source
    for term in (
        "species / hard core",
        "shared support",
        "novel colored sites",
        "public boundary",
        "coordination capacity",
        "angular envelope",
        "elastic proxy",
        "composition reservoir",
        "formal-charge reservoir",
        "surface completion",
        "GCTS marking",
    ):
        assert term in source
    assert "diagnostic · cannot authorize geometry" in source
    assert "colored minimum-distance exclusion" in source
    assert "species-resolved first-shell envelope" in source
    assert "colored bond-angle support" in source
    assert "bounded transported connection section" in source
    assert 'mode === "specialized"' in source
    assert 'value: "domain unanimity"' in source
    assert 'detail: "cannot authorize this trace"' in source
    assert 'state.textContent = entry.type === "reject" ? "prune" : "keep"' in source
    assert ".search-stack li.reject" in style
    assert "boundaryFailures: evaluation.boundaryFailures" in source
    assert "coordinationOverflows: evaluation.coordinationOverflows?.length || 0" in source
    assert "angularViolations: evaluation.angularViolations?.length || 0" in source
    assert ".constraint-term.fail" in style
    assert ".constraint-term.ranked" in style
    assert ".constraint-term.active" in style
    assert ".constraint-detail" in style
    assert "A contact exclusion is not a pair potential" in source
    assert "This is not elastic energy" in source
    assert "Formal labels are not charge density" in source
    assert 'iceAnchorTrace?.portCount || overlapGrammar?.rules?.length' in source
    assert 'all surviving ${iceAnchorTrace?.moleculeLabel || "H₂O"} poses agree' in source


if __name__ == "__main__":
    test_constraint_ledger_covers_admission_and_ranking_terms()
    print("geometry-as-physics constraint ledger contract: passed")
