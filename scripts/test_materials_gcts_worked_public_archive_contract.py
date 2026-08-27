#!/usr/bin/env python3
"""Static release contract for the shareable exact-entry worked example."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
DATABASE = (ROOT / "apps/iqc-growth-live/structure-database.js").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()


def main() -> None:
    entry_id = "KFBchFQ1IQAE-JEgzOS1XzZlfsTz"
    assert 'id="workedArchiveButton"' in HTML
    assert 'id="workedArchiveState"' in HTML
    assert 'id="workedArchivePermalink"' in HTML
    assert f"nomad:{entry_id}" in HTML
    assert entry_id in APP
    assert "WORKED_PUBLIC_ARCHIVE" in APP
    assert "loadWorkedPublicArchive" in APP
    assert 'get("specimen")' in APP
    assert "nomadStructureByEntryId" in DATABASE
    assert "entry.entry_id !== entryId" in DATABASE
    assert "query: { entry_id: entryId }" in DATABASE
    assert "nomadExactEntryRequest: true" in DATABASE
    assert "nomadRequestedEntryId: entryId" in DATABASE
    assert "exactEntryRequest:" in APP
    assert "shareableSpecimen:" in APP
    assert "worked-archive" in STYLE
    assert 'buildId: "20260827-261"' in APP
    assert "app.js?v=20260827-261" in HTML
    assert "style.css?v=20260827-261" in HTML
    print("Worked public archive contract passed")


if __name__ == "__main__":
    main()
