"""Contract for the interactive physics-to-geometry evidence map."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"


def test_physics_map_preserves_claim_boundaries() -> None:
    atlas = (APP_DIR / "evidence-atlas.js").read_text(encoding="utf-8")
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    css = (APP_DIR / "style.css").read_text(encoding="utf-8")

    for layer in ("bonding", "orientation", "order", "defects", "kinetics"):
        assert f"{layer}: {{" in atlas
        assert f'data-physics="{layer}"' in html

    assert "const PHYSICS_MAP" in atlas
    assert "function renderPhysics(key)" in atlas
    assert 'renderPhysics("bonding")' in atlas
    assert "physicsMapDetail" in atlas
    assert "physics-system-table" in atlas

    # Structural continuation must not be presented as an energy, rate, or
    # thermodynamic phase predictor.
    assert "No charge density, bond order, electronic free energy, force, or reaction barrier" in atlas
    assert "A marking is a learned connection section—not a physical potential or clock" in atlas
    assert "not a growth rate or thermodynamic phase diagram" in atlas
    assert "Proposal checks and backtracks measure computational work, not elapsed physical time" in atlas

    # Ice must expose what is geometrically green and what remains physical
    # work rather than hiding unresolved proton degrees of freedom.
    assert "Bent H₂O + tetrahedral O network" in atlas
    assert "H₂O, bridge, and O₆ gap supports" in atlas
    assert "Full proton assignment open" in atlas
    assert "No proton barrier or entropy" in atlas

    assert 'data-atlas-tab="physics"' in html
    assert 'data-atlas-panel="physics"' in html
    assert "Every encoding is paired with its approximation boundary" in html
    assert "does not turn geometry into an uncalibrated energy model" in html
    assert "repeat(6,1fr)" in css
    assert ".physics-map-tabs" in css
    assert ".physics-flow" in css
    assert ".physics-system-table" in css


if __name__ == "__main__":
    test_physics_map_preserves_claim_boundaries()
    print("physics-to-geometry map contract: passed")
