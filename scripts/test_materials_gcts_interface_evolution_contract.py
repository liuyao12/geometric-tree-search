from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_interface_state_is_frozen_on_both_sides_of_structural_leaps():
    assert "function structuralInterfaceSnapshot()" in APP
    assert "interfaces: structuralInterfaceSnapshot()" in APP
    assert "alignment: \"structural leap index\"" in APP
    assert "coordinateFrameUsed: false" in APP
    assert "physicalTimeModeled: false" in APP
    assert "grainIdentityInferred: false" in APP
    assert "interfacialEnergyInferred: false" in APP
    assert "mobilityInferred: false" in APP


def test_selected_pair_drives_a_structural_leap_evolution_strip():
    assert 'id="nucleusInterfaceEvolution"' in HTML
    assert 'id="nucleusInterfaceEvolutionState"' in HTML
    assert "function interfaceEvolutionForPair(pairKey)" in APP
    assert "renderNucleusInterfaceEvolution(selected.key)" in APP
    for metric in ('"sites"', '"patches"', '"thickness"', '"exposure"'):
        assert metric in APP
    assert ".nucleus-interface-evolution-plot" in CSS


def test_notebook_exposes_coordinate_free_interface_observables():
    for observable in ("interfaceSites", "interfaceThickness", "interfaceExposure"):
        assert f'value="{observable}"' in HTML
        assert f"{observable}:" in APP
    assert "interfacePassport:" in APP
    assert "interfaces: leap.after?.interfaces || null" in APP
    assert "Build 130" in README
    assert 'buildId: "20260826-158"' in APP
    assert 'app.js?v=20260826-158' in HTML
