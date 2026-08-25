#!/usr/bin/env python3
"""Source contract for bounded public NOMAD relaxation ensembles."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
DATABASE = (ROOT / "apps/iqc-growth-live/structure-database.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
STRUCTURE_IO = (ROOT / "apps/iqc-growth-live/structure-io.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
NODE_TEST = (ROOT / "scripts/test-materials-structure-database.mjs").read_text()


def test_nomad_query_selects_full_runs_only_for_geometry_optimizations():
    assert '"results.properties.geometry_optimization.final_energy_difference"' in DATABASE
    assert 'const hasRelaxation = Boolean(entry.results?.properties?.geometry_optimization)' in DATABASE
    assert 'system: { atoms: "*" }' in DATABASE
    assert 'calculation: { energy: "*", forces: "*", system_ref: "*", method_ref: "*" }' in DATABASE
    assert '"system[-1]": { atoms: "*" }' in DATABASE
    assert 'MAX_NOMAD_RESPONSE_BYTES = 32 * 1024 * 1024' in DATABASE


def test_fixed_topology_pairing_sampling_and_supercell_transport_are_explicit():
    for token in (
        "calculationForSystem",
        "referencedSystemIndex",
        "sampledFrameIndices",
        "MAX_NOMAD_RELAXATION_FRAMES = 24",
        "symbols.length === finalSymbols.length",
        "symbols.every((symbol, index) => symbol === finalSymbols[index])",
        "...(frames.length > 1 ? { frames } : {})",
        "preferredFrameIndex",
        "physicalTimeAvailable: false",
        "integratedAsTrajectory: false",
        "usedAsGeometricEnsembleOnly: true",
        "structure.frames?.map((frame) => expandPeriodicFrame(frame, repetitions))",
    ):
        assert token in DATABASE


def test_interactive_relaxation_strip_and_honest_boundary_are_present():
    for token in (
        'id="relaxationSequence"',
        'id="relaxationSequenceChart"',
        "Ordered calculation snapshots are geometric evidence, not physical-time integration",
    ):
        assert token in HTML
    for token in (
        "function renderRelaxationSequence",
        "function selectImportedFrame",
        "energyPerPrimitiveAtomElectronVolt - finalEnergy",
        'point.addEventListener("click"',
        "Archive order is displayed but never treated as elapsed time",
        "sourceRelaxationSequence",
        "archivedCalculationSeriesSha256",
        "frameCalculationSha256: trajectoryCalculationDigests",
        "forceVectorsEvPerAngstrom",
        "temporalOrderingUsed: false",
        'if (["hard", "learned", "explicit", "observed"].includes(record.status))',
        'if (record.status === "observed") return "observed archived structural sequence"',
    ):
        assert token in APP
    assert ".relaxation-energy" in STYLE
    assert ".relaxation-force" in STYLE
    assert ".relaxation-point.active" in STYLE
    assert '"ordered relaxation snapshots" : "trajectory frames"' in STRUCTURE_IO


def test_scientific_nonclaims_and_mocked_sequence_regression_are_documented():
    for token in (
        "interactive same-run relaxation",
        "Archive ordering is not interpreted as physical time",
        "frames are never concatenated into a fictitious material",
        "energies never select a GCTS action",
    ):
        assert token in README
    for token in (
        "relaxationSystems",
        "relaxationCalculations",
        "retainedSystemIndices",
        "expandedRelaxation.frames[2].atoms.length",
        "required.run.system",
        "required.run.calculation",
    ):
        assert token in NODE_TEST


def test_build_114_is_cache_busted():
    assert 'buildId: "20260825-121"' in APP
    assert 'structure-io.js?v=20260825-6' in APP
    assert 'structure-database.js?v=20260825-4' in APP
    assert 'app.js?v=20260825-121' in HTML


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
    print("materials NOMAD relaxation ensemble contract: passed")
