"""Live-portal contract for the published Cd5.7Yb positions-only fixture."""

import json
import math
import re
from pathlib import Path

from materials_gcts_cdyb_oracle import generate_cdyb


ROOT = Path(__file__).parents[1]


def test_published_cdyb_is_a_selectable_positions_only_sample() -> None:
    app = (ROOT / "apps/iqc-growth-live/app.js").read_text(encoding="utf-8")
    html = (ROOT / "apps/iqc-growth-live/index.html").read_text(encoding="utf-8")
    readme = (ROOT / "apps/iqc-growth-live/README.md").read_text(encoding="utf-8")
    fixture = (ROOT / "apps/iqc-growth-live/cdyb-browser-fixture.js").read_text(encoding="utf-8")

    assert 'from "./cdyb-browser-fixture.js?v=20260824-1"' in app
    assert 'option value="cdyb"' in html
    assert 'publishedFixture: "cdyb-offcenter-r14"' in app
    assert 'function makeCdYbReferenceConfiguration()' in app
    assert 'family: "published-cdyb"' in app
    assert 'phaseLabelUsedByLearner: false' in app
    assert 'cutAndProjectCoordinatesEmbedded: false' in app
    assert 'sourceSitesEmbedded: false' in app
    assert 'buildId: "20260825-142"' in app
    assert 'app.js?v=20260825-142' in html
    assert 'style.css?v=20260825-51' in html
    assert 'id="publishedFixtureProvenance"' in html
    assert 'id="publishedFixtureArticle"' in html
    assert 'function renderPublishedFixtureProvenance()' in app
    assert "506-atom off-centre radius-14" in readme
    assert "six-dimensional coordinates" in readme

    embedded = [json.loads(record) for record in re.findall(
        r'Object\.freeze\((\["(?:Cd|Yb)"[^)]*\])\)', fixture)]
    origin = (3.1, 5.7, 8.2)
    oracle = generate_cdyb(4, (60.0,) * 3)
    expected = [[species, *(round(point[axis] - origin[axis], 8) for axis in range(3))]
                for species, point in zip(oracle.symbols, oracle.positions)
                if math.dist(origin, point) <= 14.0 + 1e-10]
    assert embedded == expected


if __name__ == "__main__":
    test_published_cdyb_is_a_selectable_positions_only_sample()
    print("published Cd-Yb live portal contract: passed")
