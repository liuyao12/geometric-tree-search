from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_centrosymmetry_is_frozen_through_leaps_receipts_notebook_and_ledger():
    assert 'buildId: "20260826-167"' in APP
    assert 'app.js?v=20260826-167' in HTML
    assert "function structuralCentrosymmetrySnapshot" in APP
    assert "function centrosymmetryTransition" in APP
    assert "frozen.centrosymmetryTransition = centrosymmetryTransition" in APP
    assert "centrosymmetry: structuralCentrosymmetrySnapshot()" in APP
    assert "centrosymmetryTransition: leap.centrosymmetryTransition || null" in APP

    for token in (
        "reference-configuration complete-shell inference",
        "exact minimum-weight pairing",
        "uniformScaleInvariant: true",
        'id: "centrosymmetry"',
        'label: "mean local inversion asymmetry"',
        'label: "centrosymmetry JS distance"',
        '"05 · inversion asymmetry"',
        "never ranks or admits growth",
        "not named defects, a defect classifier, formation energy",
    ):
        assert token in APP

    assert "Build 166" in README
    assert "Build 166" in DOCS


if __name__ == "__main__":
    test_centrosymmetry_is_frozen_through_leaps_receipts_notebook_and_ledger()
    print("centrosymmetry leap path contract passed")
