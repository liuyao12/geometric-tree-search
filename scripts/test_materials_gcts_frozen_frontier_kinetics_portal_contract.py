from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
KINETICS = (ROOT / "apps/iqc-growth-live/frozen-frontier-kinetics.mjs").read_text()
BARRIER = (ROOT / "apps/iqc-growth-live/external-action-barrier.mjs").read_text()
PHYSICS = (ROOT / "apps/iqc-growth-live/physics-compression-map.js").read_text()


def test_finite_temperature_controls_are_explicit_and_prefactor_gated():
    for control_id in (
        "actionBarrierKineticMode", "actionBarrierTemperature",
        "actionBarrierKineticState",
    ):
        assert f'id="{control_id}"' in HTML
    assert "HTST · maximum rate" in HTML
    assert "HTST · seeded KMC draw" in HTML
    assert "physical temperature" in HTML
    assert "converged, uncertainty-bearing attempt frequency" in HTML
    assert "audit?.kineticsEligible" in APP
    assert "actionBarrierKineticModeSelect.disabled = !kineticsEligible" in APP


def test_response_requires_complete_method_bound_prefactors_or_stays_clock_free():
    for token in (
        "attemptFrequencyPerSecond", "attemptFrequencyUncertaintyLog10",
        "prefactorSettingsSha256", "everyPrefactorConverged",
        "prefactorUncertaintyReported", "requested-hard-admitted-actions-only",
        "recrossingCorrection",
    ):
        assert token in BARRIER
    assert "per-candidate kinetic fields require the complete response kinetics declaration" in BARRIER
    assert "kineticsEligible: Boolean(kinetics)" in BARRIER


def test_rates_are_log_stable_and_selection_is_one_exact_frozen_action():
    assert "BOLTZMANN_ELECTRON_VOLT_PER_KELVIN" in KINETICS
    assert "logSumExp" in KINETICS
    assert "Math.log(attemptFrequencyPerSecond)" in KINETICS
    assert "barrierElectronVolt * inverseThermalEnergy" in KINETICS
    assert "probabilityWithinFrozenCatalog" in KINETICS
    assert "selectedCandidateId" in KINETICS
    assert "return [selected]" in APP
    assert "the frozen kinetic event is no longer hard-admitted" in APP
    assert "Commit one kinetic event" in APP


def test_clock_advances_only_after_one_accepted_seeded_event_and_is_receipted():
    commit_guard = 'kineticCompetition?.mode === "seeded-kmc" && acceptedInBatch === 1'
    assert commit_guard in APP
    assert "catalogConditionalKineticClockSeconds = kineticCompetition.clockAfterSeconds" in APP
    assert "externalActionBarrierCheckpoint.kineticClockCommitted = true" in APP
    assert "physicalTimeInferred: Boolean(kineticClockCommitted" in APP
    assert "physicalTimeModeled: catalogConditionalClockCommitted" in APP
    assert "catalog-conditional HTST waiting-time draw" in APP
    assert "eventUniform: kinetic.eventUniform" in APP
    assert "waitingUniform: kinetic.waitingUniform" in APP
    assert "catalogCompleteBeyondFrozenFrontier: false" in APP
    assert '· kinetic catalog`' in APP
    assert "conditional clock" in APP


def test_claim_boundary_keeps_rates_catalog_conditional_not_md_or_global_time():
    assert "catalogCompleteBeyondFrozenFrontier: false" in KINETICS
    assert "Missing mechanisms, recrossing, quantum effects, correlated events" in KINETICS
    assert "finite enumerated hard-admitted catalog" in APP
    assert "transferable potential, MD trajectory, equilibrium ensemble" in APP
    assert "candidateSetChanged: false" in KINETICS
    assert "hardAdmissionChanged: false" in KINETICS
    assert "targetUsed: false" in KINETICS
    assert 'id: "event-kinetics"' in APP
    assert '"event-kinetics", "kinetics", "long-range"' in PHYSICS
    assert '["event-kinetics", "arrivalPathSelect"' not in PHYSICS


if __name__ == "__main__":
    test_finite_temperature_controls_are_explicit_and_prefactor_gated()
    test_response_requires_complete_method_bound_prefactors_or_stays_clock_free()
    test_rates_are_log_stable_and_selection_is_one_exact_frozen_action()
    test_clock_advances_only_after_one_accepted_seeded_event_and_is_receipted()
    test_claim_boundary_keeps_rates_catalog_conditional_not_md_or_global_time()
    print("frozen frontier kinetics portal contract: passed")
