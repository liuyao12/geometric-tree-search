"""Source contract for the progressive growth-physics control taxonomy."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_growth_controls_are_grouped_without_changing_control_identity() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    css = (APP / "style.css").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")
    normalized_readme = " ".join(readme.split())

    assert html.count('class="growth-control-group"') == 5
    assert html.count('class="growth-control-group" open') == 1
    for state_id in (
        "growthCoreGroupState",
        "growthChemistryGroupState",
        "growthInterfaceGroupState",
        "growthFieldsGroupState",
        "growthExecutionGroupState",
    ):
        assert html.count(f'id="{state_id}"') == 1

    for control_id in (
        "markingLibrarySelect",
        "compositionPreferenceSelect",
        "chargeGeometrySelect",
        "attachmentTopologySelect",
        "coherencyMemorySelect",
        "thermalFieldSelect",
        "loopClosurePreferenceSelect",
        "arrivalPathSelect",
        "growthNucleiSelect",
        "hierarchicalGrowthButton",
    ):
        assert html.count(f'id="{control_id}"') == 1

    assert 'id="expandGrowthGroupsButton"' in html
    assert 'id="collapseGrowthGroupsButton"' in html
    assert "GCTS marking &amp; local strain" in html
    assert "Composition &amp; supplied charge" in html
    assert "Attachment, coherency &amp; morphology" in html
    assert "Loading &amp; mesoscopic compatibility" in html
    assert "Transport, nuclei &amp; tree search" in html

    assert "function renderGrowthControlGroupSummaries()" in source
    assert 'querySelectorAll(".growth-control-group")' in source
    assert "group.open = true" in source
    assert "group.open = false" in source
    assert "renderGrowthControlGroupSummaries();" in source

    assert ".growth-control-group > summary" in css
    assert ".growth-control-group > summary:focus-visible" in css
    assert ".growth-group-actions" in css
    assert "five native, keyboard-accessible disclosure groups" in readme
    assert "Disclosure changes presentation only" in normalized_readme


if __name__ == "__main__":
    test_growth_controls_are_grouped_without_changing_control_identity()
    print("growth-control progressive-disclosure contract: passed")
