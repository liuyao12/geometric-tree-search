"""Source contract for the live physics-to-geometry validity map."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_growth_validity_map_separates_authority_from_activity() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    css = (APP / "style.css").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")
    normalized_readme = " ".join(readme.split())

    assert 'id="leapPhysicsState"' in html
    assert 'id="leapPhysicsFilters"' in html
    assert html.count('data-physics-filter="') == 4
    for value in ("all", "structural", "hypothesis", "open"):
        assert f'data-physics-filter="{value}"' in html

    assert "function physicsEvidenceBucket(record)" in source
    assert "function physicsEvidenceClass(record)" in source
    assert '["hard", "learned", "explicit"]' in source
    assert '["soft", "sampled"]' in source
    assert 'required input channel unavailable' in source
    assert 'result[physicsEvidenceBucket(record)] += 1' in source
    assert 'records.filter((record) => physicsEvidenceBucket(record) === selectedLeapPhysicsFilter)' in source
    assert 'button.dataset.physicsFilter' in source
    assert '["evidence class", physicsEvidenceClass(selected)]' in source

    assert ".leap-physics-filters" in css
    assert ".leap-physics-filters button:focus-visible" in css
    assert "The structural-leap inspector classifies every physics-to-geometry record" in normalized_readme
    assert "Filtering never changes the candidate set, score, admission gate" in normalized_readme


if __name__ == "__main__":
    test_growth_validity_map_separates_authority_from_activity()
    print("growth-validity map contract: passed")
