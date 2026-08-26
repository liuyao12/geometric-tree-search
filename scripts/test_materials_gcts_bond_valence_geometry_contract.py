from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = (ROOT / "apps/iqc-growth-live/bond-valence-geometry.js").read_text()


def test_bond_valence_module_is_target_blind_and_fail_closed():
    assert "incrementalBondValenceSatisfaction" in MODULE
    assert "export function bondValenceStateSummary" in MODULE
    assert "vectorScore" in MODULE
    assert "combinedScore" in MODULE
    assert "V_i = sum_j s_ij rhat_ij" in MODULE
    assert "no checked bond-valence parameter connects the candidate" in MODULE
    assert "oxidationStatesInferred: false" in MODULE
    assert "uniformScaleInvariant: false" in MODULE
    assert "physicalAngstromScaleRequired: true" in MODULE
    assert "candidateGeometryChanged: false" in MODULE
    assert "hardAdmissionChanged: false" in MODULE
    assert "targetUsed: false" in MODULE


def test_bond_valence_provenance_and_claim_boundary_are_explicit():
    assert "IUCr bvparm2020.cif" in MODULE
    assert "6f921b6fd20b00fdbe4705a38f02e5c45ae91f1c39be55eb6b0620a454875b89" in MODULE
    assert "s = exp((R0 - R) / B)" in MODULE
    assert "bondEnergyInferred: false" in MODULE
    assert "electronDensityModeled: false" in MODULE
    assert "chargeTransferModeled: false" in MODULE
    assert "10.1107/S0108768106026553" in MODULE
    assert "anisotropyCanBePhysical: true" in MODULE
    assert "lonePairModeled: false" in MODULE
