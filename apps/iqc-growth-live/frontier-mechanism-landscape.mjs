import { buildFrozenKineticCompetition }
  from "./frozen-frontier-kinetics.mjs?v=20260901-449";
import { buildEventGeometryObservables }
  from "./kinetic-geometry-response.mjs?v=20260901-449";

export const GRAND_POTENTIAL_CLASSES = Object.freeze([
  "downhill", "uncertainty-overlapping-zero", "uphill",
]);

function finite(value) { return Number.isFinite(Number(value)); }

function grandPotentialClass(value, uncertainty) {
  if (value + uncertainty < 0) return "downhill";
  if (value - uncertainty > 0) return "uphill";
  return "uncertainty-overlapping-zero";
}

function populationClass(materialAtomDelta) {
  if (materialAtomDelta > 0) return "growth";
  if (materialAtomDelta < 0) return "shrinkage";
  return "count-preserving";
}

function probabilityMass(records, predicate) {
  return records.filter(predicate).reduce((sum, record) =>
    sum + record.probabilityWithinFrozenCatalog, 0);
}

export function buildFrontierMechanismLandscape(records, thermodynamics, {
  temperatureKelvin,
  contactReach = 1.35,
} = {}) {
  if (!thermodynamics) {
    return { schema: 1, available: false,
      reason: "Complete externally supplied grand-canonical endpoint evidence is required.",
      targetUsed: false, candidateSetChanged: false,
      claimBoundary: "Barrier and geometry evidence alone do not establish thermodynamic driving." };
  }
  if (!finite(temperatureKelvin) || !finite(thermodynamics.temperatureKelvin)
      || Math.abs(Number(temperatureKelvin) - Number(thermodynamics.temperatureKelvin))
        > Math.max(1e-9, Number(thermodynamics.temperatureKelvin) * 1e-9)) {
    throw new Error("kinetic and thermodynamic landscape temperatures must match exactly");
  }
  if (!Array.isArray(records) || !records.length || records.some((record) =>
    !finite(record.grandPotentialDeltaElectronVolt)
      || !finite(record.grandPotentialDeltaUncertaintyElectronVolt)
      || Number(record.grandPotentialDeltaUncertaintyElectronVolt) < 0)) {
    throw new Error("every landscape event needs a finite grand-potential change and nonnegative uncertainty");
  }
  const competition = buildFrozenKineticCompetition(records,
    { temperatureKelvin: Number(temperatureKelvin), mode: "rate-maximum" });
  const sourceById = new Map(records.map((record) => [record.candidateId, record]));
  const events = competition.records.map((rate) => {
    const source = sourceById.get(rate.candidateId);
    const geometry = buildEventGeometryObservables(source, contactReach);
    const grandPotentialDeltaElectronVolt = Number(source.grandPotentialDeltaElectronVolt);
    const grandPotentialDeltaUncertaintyElectronVolt = Number(
      source.grandPotentialDeltaUncertaintyElectronVolt);
    const drivingClass = grandPotentialClass(grandPotentialDeltaElectronVolt,
      grandPotentialDeltaUncertaintyElectronVolt);
    return {
      candidateId: rate.candidateId,
      eventDirection: rate.eventDirection,
      selectedByMaximumRate: rate.candidateId === competition.selectedCandidateId,
      probabilityWithinFrozenCatalog: rate.probabilityWithinFrozenCatalog,
      log10RatePerSecond: rate.log10RatePerSecond,
      log10RateLowerPerSecond: rate.log10RateLowerPerSecond,
      log10RateUpperPerSecond: rate.log10RateUpperPerSecond,
      barrierElectronVolt: rate.barrierElectronVolt,
      barrierUncertaintyElectronVolt: rate.uncertaintyElectronVolt,
      grandPotentialDeltaElectronVolt,
      grandPotentialDeltaUncertaintyElectronVolt,
      grandPotentialClass: drivingClass,
      materialPopulationClass: populationClass(geometry.materialAtomDelta),
      geometry,
    };
  }).sort((first, second) => first.candidateId.localeCompare(second.candidateId));
  const jointProbabilityMass = {};
  ["growth", "shrinkage", "count-preserving"].forEach((population) => {
    GRAND_POTENTIAL_CLASSES.forEach((driving) => {
      jointProbabilityMass[`${population}:${driving}`] = probabilityMass(events,
        (event) => event.materialPopulationClass === population
          && event.grandPotentialClass === driving);
    });
  });
  const selected = events.find((event) => event.selectedByMaximumRate);
  const expectedGrandPotentialDeltaElectronVolt = events.reduce((sum, event) =>
    sum + event.probabilityWithinFrozenCatalog * event.grandPotentialDeltaElectronVolt, 0);
  return {
    schema: 1,
    available: true,
    model: "coherent finite-frontier kinetic–grand-potential–geometry landscape",
    temperatureKelvin: Number(temperatureKelvin),
    thermodynamicModel: thermodynamics.model,
    ensemble: thermodynamics.ensemble,
    candidateCount: events.length,
    selectedCandidateId: selected.candidateId,
    selectedGrandPotentialClass: selected.grandPotentialClass,
    selectedMaterialPopulationClass: selected.materialPopulationClass,
    downhillProbabilityMass: probabilityMass(events,
      (event) => event.grandPotentialClass === "downhill"),
    uphillProbabilityMass: probabilityMass(events,
      (event) => event.grandPotentialClass === "uphill"),
    zeroOverlappingProbabilityMass: probabilityMass(events,
      (event) => event.grandPotentialClass === "uncertainty-overlapping-zero"),
    expectedGrandPotentialDeltaElectronVolt,
    jointProbabilityMass,
    events,
    targetUsed: false,
    candidateSetChanged: false,
    geometricEndpointsChanged: false,
    thermodynamicAndKineticTemperatureCoherent: true,
    detailedBalanceCertified: false,
    equilibriumClaimed: false,
    claimBoundary: "This landscape juxtaposes method-bound kinetic barriers, finite-catalog rates, independently supplied endpoint ΔΩ, and exact geometric outcomes at one shared T,V,μ state. A potential-energy saddle is not relabeled as a grand free-energy barrier. Downhill endpoints do not prove mechanism completeness, detailed balance, equilibrium, or long-time growth.",
  };
}
