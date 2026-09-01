export const COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM = 14.3996454784255;
export const BOLTZMANN_ELECTRON_VOLT_PER_KELVIN = 8.617333262145e-5;
export const TANG_TOENNIES_DISPERSION_ORDER = 6;

import { canonicalSpeciesPairKey } from "./born-mayer-pair-matrix.mjs";
import { finiteDifferenceIncrementalChargeInductionForces,
  incrementalFiniteChargeInduction } from "./finite-charge-induction.mjs?v=20260901-443";

export const FINITE_POINT_CHARGE_PROVENANCE = Object.freeze({
  model: "finite open-boundary formal-point-charge Coulomb interaction with optional Born–Mayer repulsion, damped dispersion, and damped charge-induced-dipole energy",
  coulombConstantSource: "2018 CODATA elementary charge and vacuum permittivity",
  coulombConstantElectronVoltAngstrom: COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM,
  boltzmannConstantElectronVoltPerKelvin: BOLTZMANN_ELECTRON_VOLT_PER_KELVIN,
  boundaryCondition: "finite open boundary; no periodic images or neutralizing background",
  interactingDipoleReference: "B. T. Thole, Chemical Physics 59 (1981) 341–350",
  interactingDipoleReferenceDoi: "10.1016/0301-0104(81)85176-2",
  implementationBoundary: "The optional f3/f5 Tang-Toennies tensor is a declared finite geometry hypothesis inspired by smeared interacting-dipole models; it is not a fitted Thole/AMOEBA parameterization.",
});

const finite = (value) => Number.isFinite(Number(value));

function normalizedSite(site, label) {
  if (!Array.isArray(site?.position) || site.position.length !== 3
      || !site.position.every(finite) || !finite(site?.charge)) {
    throw new TypeError(`${label} needs a finite Cartesian position and formal charge`);
  }
  return { position: site.position.map(Number), charge: Number(site.charge),
    species: site.species === null || site.species === undefined ? null : String(site.species) };
}

function normalizedPairMatrix(rawMatrix) {
  if (rawMatrix === null || rawMatrix === undefined) return {
    available: false, policy: "uniform", records: [], parameters: new Map(),
  };
  if (!Array.isArray(rawMatrix?.records)) {
    throw new TypeError("bornMayerPairMatrix must expose a records array");
  }
  const parameters = new Map();
  const records = rawMatrix.records.map((record, index) => {
    const species = Array.isArray(record?.species) ? record.species.map(String) : [];
    if (species.length !== 2 || species.some((token) => !token)) {
      throw new TypeError(`Born-Mayer pair record ${index + 1} needs two species tokens`);
    }
    const key = canonicalSpeciesPairKey(species[0], species[1]);
    if (parameters.has(key)) throw new Error(`duplicate Born-Mayer pair record: ${key}`);
    const amplitudeElectronVolt = Number(record.amplitudeElectronVolt);
    const decayAngstrom = Number(record.decayAngstrom);
    if (!finite(amplitudeElectronVolt) || amplitudeElectronVolt < 0 || amplitudeElectronVolt > 1e6
        || !finite(decayAngstrom) || decayAngstrom <= 0 || decayAngstrom > 10) {
      throw new RangeError(`Born-Mayer pair record ${key} has invalid A or rho`);
    }
    const normalized = { key, species, amplitudeElectronVolt, decayAngstrom,
      geometryConditioned: Boolean(record.geometryConditioned),
      parameterSource: String(record.parameterSource || "declared pair record") };
    parameters.set(key, normalized);
    return normalized;
  });
  return { available: records.length > 0, policy: String(rawMatrix.policy || "pair-matrix"),
    records, parameters };
}

function vectorNorm(vector) {
  return Math.hypot(...vector);
}

function factorial(value) {
  let result = 1;
  for (let index = 2; index <= value; index++) result *= index;
  return result;
}

/** Tang–Toennies f_n(x), evaluated without small-x cancellation. */
export function tangToenniesDamping(order, rawX) {
  const x = Number(rawX);
  if (!Number.isInteger(order) || order < 0 || order > 20 || !Number.isFinite(x) || x < 0) {
    throw new RangeError("Tang-Toennies damping requires integer order 0..20 and finite x >= 0");
  }
  if (x === 0) return 0;
  if (x < 1) {
    let term = x ** (order + 1) / factorial(order + 1);
    let tail = term;
    for (let index = order + 2; index < order + 80; index++) {
      term *= x / index;
      tail += term;
      if (Math.abs(term) <= 1e-16 * Math.abs(tail)) break;
    }
    return Math.exp(-x) * tail;
  }
  let term = 1;
  let partial = 1;
  for (let index = 1; index <= order; index++) {
    term *= x / index;
    partial += term;
  }
  return Math.max(0, Math.min(1, 1 - Math.exp(-x) * partial));
}

export function tangToenniesDampingDerivative(order, rawX) {
  const x = Number(rawX);
  if (!Number.isInteger(order) || order < 0 || order > 20 || !Number.isFinite(x) || x < 0) {
    throw new RangeError("Tang-Toennies derivative requires integer order 0..20 and finite x >= 0");
  }
  return Math.exp(-x) * x ** order / factorial(order);
}

function cross(first, second) {
  return [
    first[1] * second[2] - first[2] * second[1],
    first[2] * second[0] - first[0] * second[2],
    first[0] * second[1] - first[1] * second[0],
  ];
}

function rankingObservable(value) {
  if (["energy", "force-cancellation", "combined"].includes(value)) return value;
  throw new RangeError("rankingObservable must be energy, force-cancellation, or combined");
}

function inductionForceMode(value) {
  if (["omitted", "finite-difference"].includes(value)) return value;
  throw new RangeError("inductionForceMode must be omitted or finite-difference");
}

function declaredReach(value) {
  if (value === "global" || value === Infinity) return Infinity;
  if (!finite(value) || Number(value) <= 0) throw new RangeError("reachAngstrom must be positive or global");
  return Number(value);
}

export function incrementalFinitePointChargeElectrostatics(currentSites = [], addedSites = [], {
  relativePermittivity = 1,
  temperatureKelvin = 300,
  reachAngstrom = "global",
  forceReferenceLengthAngstrom = 1,
  rankingObservable: rawRankingObservable = "energy",
  bornMayerAmplitudeElectronVolt = 0,
  bornMayerDecayAngstrom = .3,
  bornMayerPairMatrix = null,
  dispersionC6ElectronVoltAngstrom6 = 0,
  dispersionDampingLengthAngstrom = .3,
  inductionPolarizabilityAngstrom3 = 0,
  inductionDampingLengthAngstrom = .3,
  inductionResponseModel = "direct",
  inductionMaximumIterations = 128,
  inductionConvergenceToleranceElectronAngstrom = 1e-6,
  inductionIterationMixing = .5,
  inductionForceMode: rawInductionForceMode = "omitted",
  inductionForceStepAngstrom = 1e-4,
} = {}) {
  if (!finite(relativePermittivity) || Number(relativePermittivity) < 1
      || Number(relativePermittivity) > 1000) {
    throw new RangeError("relativePermittivity must be between 1 and 1000");
  }
  if (!finite(temperatureKelvin) || Number(temperatureKelvin) < 1
      || Number(temperatureKelvin) > 5000) {
    throw new RangeError("temperatureKelvin must be between 1 and 5000 K");
  }
  if (!finite(forceReferenceLengthAngstrom) || Number(forceReferenceLengthAngstrom) <= 0) {
    throw new RangeError("forceReferenceLengthAngstrom must be positive");
  }
  if (!finite(bornMayerAmplitudeElectronVolt) || Number(bornMayerAmplitudeElectronVolt) < 0
      || Number(bornMayerAmplitudeElectronVolt) > 1e6) {
    throw new RangeError("bornMayerAmplitudeElectronVolt must be between 0 and 1e6 eV");
  }
  if (!finite(bornMayerDecayAngstrom) || Number(bornMayerDecayAngstrom) <= 0
      || Number(bornMayerDecayAngstrom) > 10) {
    throw new RangeError("bornMayerDecayAngstrom must be between 0 and 10 angstrom");
  }
  if (!finite(dispersionC6ElectronVoltAngstrom6) || Number(dispersionC6ElectronVoltAngstrom6) < 0
      || Number(dispersionC6ElectronVoltAngstrom6) > 1e7) {
    throw new RangeError("dispersionC6ElectronVoltAngstrom6 must be between 0 and 1e7 eV angstrom^6");
  }
  if (!finite(dispersionDampingLengthAngstrom) || Number(dispersionDampingLengthAngstrom) <= 0
      || Number(dispersionDampingLengthAngstrom) > 10) {
    throw new RangeError("dispersionDampingLengthAngstrom must be between 0 and 10 angstrom");
  }
  if (!finite(inductionPolarizabilityAngstrom3) || Number(inductionPolarizabilityAngstrom3) < 0
      || Number(inductionPolarizabilityAngstrom3) > 100) {
    throw new RangeError("inductionPolarizabilityAngstrom3 must be between 0 and 100 angstrom^3");
  }
  if (!finite(inductionDampingLengthAngstrom) || Number(inductionDampingLengthAngstrom) <= 0
      || Number(inductionDampingLengthAngstrom) > 10) {
    throw new RangeError("inductionDampingLengthAngstrom must be between 0 and 10 angstrom");
  }
  const observable = rankingObservable(rawRankingObservable);
  const requestedInductionForceMode = inductionForceMode(rawInductionForceMode);
  const reach = declaredReach(reachAngstrom);
  const current = currentSites.map((site, index) => normalizedSite(site, `current site ${index + 1}`));
  const added = addedSites.map((site, index) => normalizedSite(site, `added site ${index + 1}`));
  const pairMatrix = normalizedPairMatrix(bornMayerPairMatrix);
  if (pairMatrix.available && [...current, ...added].some((site) => !site.species)) {
    throw new TypeError("species tokens are required when a Born-Mayer pair matrix is supplied");
  }
  if (!current.length || !added.length) return {
    available: false,
    score: 0,
    pairCount: 0,
    currentSites: current.length,
    addedSites: added.length,
    reason: !current.length ? "current charged solid unavailable" : "candidate adds no charged sites",
  };
  let signedChargeDistanceSumPerAngstrom = 0;
  let attractiveEnergyElectronVolt = 0;
  let repulsiveEnergyElectronVolt = 0;
  let bornMayerRepulsiveEnergyElectronVolt = 0;
  let dampedDispersionEnergyElectronVolt = 0;
  let pairCount = 0;
  let distanceEvaluations = 0;
  const addedForceVectorsElectronVoltPerAngstrom = added.map(() => [0, 0, 0]);
  const addedCoulombForceVectorsElectronVoltPerAngstrom = added.map(() => [0, 0, 0]);
  const addedBornMayerForceVectorsElectronVoltPerAngstrom = added.map(() => [0, 0, 0]);
  const addedDispersionForceVectorsElectronVoltPerAngstrom = added.map(() => [0, 0, 0]);
  const prefactor = COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM / Number(relativePermittivity);
  const bornAmplitude = Number(bornMayerAmplitudeElectronVolt);
  const bornDecay = Number(bornMayerDecayAngstrom);
  const dispersionC6 = Number(dispersionC6ElectronVoltAngstrom6);
  const dispersionDampingLength = Number(dispersionDampingLengthAngstrom);
  const pairParameterUsage = new Map();
  let pairMatrixFallbackCount = 0;
  const accumulate = (first, second, firstAddedIndex, secondAddedIndex = null) => {
    const displacement = first.position.map((value, axis) => value - second.position[axis]);
    const separation = vectorNorm(displacement);
    distanceEvaluations += 1;
    if (!(separation > 1e-10)) throw new Error("coincident charged sites make the point-charge model singular");
    if (separation > reach) return;
    const chargeDistanceTerm = first.charge * second.charge / separation;
    const coulombEnergy = prefactor * chargeDistanceTerm;
    const pairKey = first.species && second.species
      ? canonicalSpeciesPairKey(first.species, second.species) : null;
    const pairParameter = pairKey ? pairMatrix.parameters.get(pairKey) : null;
    if (pairMatrix.available && !pairParameter) pairMatrixFallbackCount += 1;
    const pairAmplitude = pairParameter?.amplitudeElectronVolt ?? bornAmplitude;
    const pairDecay = pairParameter?.decayAngstrom ?? bornDecay;
    const bornMayerEnergy = pairAmplitude * Math.exp(-separation / pairDecay);
    const dampingArgument = separation / dispersionDampingLength;
    const dispersionDamping = tangToenniesDamping(TANG_TOENNIES_DISPERSION_ORDER,
      dampingArgument);
    const dispersionDampingDerivative = tangToenniesDampingDerivative(
      TANG_TOENNIES_DISPERSION_ORDER, dampingArgument);
    const dispersionEnergy = -dispersionC6 * dispersionDamping / separation ** 6;
    const energy = coulombEnergy + bornMayerEnergy + dispersionEnergy;
    signedChargeDistanceSumPerAngstrom += chargeDistanceTerm;
    if (coulombEnergy < 0) attractiveEnergyElectronVolt += -coulombEnergy;
    else repulsiveEnergyElectronVolt += coulombEnergy;
    bornMayerRepulsiveEnergyElectronVolt += bornMayerEnergy;
    dampedDispersionEnergyElectronVolt += dispersionEnergy;
    repulsiveEnergyElectronVolt += bornMayerEnergy;
    attractiveEnergyElectronVolt += -dispersionEnergy;
    const coulombForceScale = prefactor * first.charge * second.charge / separation ** 3;
    const bornMayerForceScale = bornMayerEnergy / (pairDecay * separation);
    const dispersionForceScale = dispersionC6 * (dispersionDampingDerivative
      / (dispersionDampingLength * separation ** 7) - 6 * dispersionDamping / separation ** 8);
    displacement.forEach((component, axis) => {
      const coulombForce = coulombForceScale * component;
      const bornMayerForce = bornMayerForceScale * component;
      const dispersionForce = dispersionForceScale * component;
      const force = coulombForce + bornMayerForce + dispersionForce;
      addedForceVectorsElectronVoltPerAngstrom[firstAddedIndex][axis] += force;
      addedCoulombForceVectorsElectronVoltPerAngstrom[firstAddedIndex][axis] += coulombForce;
      addedBornMayerForceVectorsElectronVoltPerAngstrom[firstAddedIndex][axis] += bornMayerForce;
      addedDispersionForceVectorsElectronVoltPerAngstrom[firstAddedIndex][axis] += dispersionForce;
      if (secondAddedIndex !== null) {
        addedForceVectorsElectronVoltPerAngstrom[secondAddedIndex][axis] -= force;
        addedCoulombForceVectorsElectronVoltPerAngstrom[secondAddedIndex][axis] -= coulombForce;
        addedBornMayerForceVectorsElectronVoltPerAngstrom[secondAddedIndex][axis] -= bornMayerForce;
        addedDispersionForceVectorsElectronVoltPerAngstrom[secondAddedIndex][axis] -= dispersionForce;
      }
    });
    pairCount += 1;
    if (pairKey) {
      const usage = pairParameterUsage.get(pairKey) || { key: pairKey,
        species: [first.species, second.species].sort(), pairCount: 0,
        amplitudeElectronVolt: pairAmplitude, decayAngstrom: pairDecay,
        geometryConditioned: Boolean(pairParameter?.geometryConditioned),
        parameterSource: pairParameter?.parameterSource || "declared uniform reference fallback" };
      usage.pairCount += 1;
      pairParameterUsage.set(pairKey, usage);
    }
  };
  added.forEach((site, addedIndex) => current.forEach((neighbor) =>
    accumulate(site, neighbor, addedIndex)));
  added.forEach((site, index) => added.slice(index + 1)
    .forEach((neighbor, relativeIndex) => accumulate(site, neighbor, index, index + relativeIndex + 1)));
  const coulombDeltaEnergyElectronVolt = prefactor * signedChargeDistanceSumPerAngstrom;
  const chargeInduction = incrementalFiniteChargeInduction(current, added, {
    polarizabilityAngstrom3: Number(inductionPolarizabilityAngstrom3),
    dampingLengthAngstrom: Number(inductionDampingLengthAngstrom),
    reachAngstrom: Number.isFinite(reach) ? reach : "global",
    relativePermittivity: Number(relativePermittivity),
    responseModel: inductionResponseModel,
    maximumIterations: inductionMaximumIterations,
    convergenceToleranceElectronAngstrom: inductionConvergenceToleranceElectronAngstrom,
    iterationMixing: inductionIterationMixing,
  });
  const chargeInductionForce = requestedInductionForceMode === "finite-difference"
    && Number(inductionPolarizabilityAngstrom3) > 0
    ? finiteDifferenceIncrementalChargeInductionForces(current, added, {
      polarizabilityAngstrom3: Number(inductionPolarizabilityAngstrom3),
      dampingLengthAngstrom: Number(inductionDampingLengthAngstrom),
      reachAngstrom: Number.isFinite(reach) ? reach : "global",
      relativePermittivity: Number(relativePermittivity),
      responseModel: inductionResponseModel,
      maximumIterations: inductionMaximumIterations,
      convergenceToleranceElectronAngstrom: inductionConvergenceToleranceElectronAngstrom,
      iterationMixing: inductionIterationMixing,
      forceStepAngstrom: inductionForceStepAngstrom,
    }) : {
      available: false,
      forceVectorsElectronVoltPerAngstrom: added.map(() => [0, 0, 0]),
      centralDifferenceEnergyEvaluations: 0,
      distanceEvaluations: 0,
      mutualTensorEvaluations: 0,
      maximumRichardsonErrorElectronVoltPerAngstrom: null,
      rmsRichardsonErrorElectronVoltPerAngstrom: null,
      reason: Number(inductionPolarizabilityAngstrom3) > 0
        ? "polarization force omitted by declared control" : "charge induction off",
      targetUsed: false,
    };
  if (chargeInductionForce.available) {
    chargeInductionForce.forceVectorsElectronVoltPerAngstrom.forEach((force, index) =>
      force.forEach((component, axis) => {
        addedForceVectorsElectronVoltPerAngstrom[index][axis] += component;
      }));
  }
  const chargeInductionDeltaEnergyElectronVolt = chargeInduction.deltaEnergyElectronVolt;
  const deltaEnergyElectronVolt = coulombDeltaEnergyElectronVolt
    + bornMayerRepulsiveEnergyElectronVolt + dampedDispersionEnergyElectronVolt
    + chargeInductionDeltaEnergyElectronVolt;
  if (chargeInductionDeltaEnergyElectronVolt < 0) {
    attractiveEnergyElectronVolt += -chargeInductionDeltaEnergyElectronVolt;
  } else repulsiveEnergyElectronVolt += chargeInductionDeltaEnergyElectronVolt;
  const thermalEnergyElectronVolt = BOLTZMANN_ELECTRON_VOLT_PER_KELVIN
    * Number(temperatureKelvin);
  const reducedThermalEnergyPerAddedSite = deltaEnergyElectronVolt
    / (added.length * thermalEnergyElectronVolt);
  const energyScore = -reducedThermalEnergyPerAddedSite
    / (1 + Math.abs(reducedThermalEnergyPerAddedSite));
  const forceMagnitudesElectronVoltPerAngstrom = addedForceVectorsElectronVoltPerAngstrom
    .map(vectorNorm);
  const rmsAddedForceElectronVoltPerAngstrom = Math.sqrt(
    forceMagnitudesElectronVoltPerAngstrom.reduce((sum, value) => sum + value ** 2, 0)
      / Math.max(1, forceMagnitudesElectronVoltPerAngstrom.length));
  const maximumAddedForceElectronVoltPerAngstrom = Math.max(0,
    ...forceMagnitudesElectronVoltPerAngstrom);
  const netAddedForceVectorElectronVoltPerAngstrom = [0, 1, 2].map((axis) =>
    addedForceVectorsElectronVoltPerAngstrom.reduce((sum, vector) => sum + vector[axis], 0));
  const netAddedForceMagnitudeElectronVoltPerAngstrom = vectorNorm(
    netAddedForceVectorElectronVoltPerAngstrom);
  const addedCentroidAngstrom = [0, 1, 2].map((axis) =>
    added.reduce((sum, site) => sum + site.position[axis], 0) / added.length);
  const torqueFor = (vectors) => added.reduce((sum, site, index) => {
    const lever = site.position.map((value, axis) => value - addedCentroidAngstrom[axis]);
    const torque = cross(lever, vectors[index]);
    return sum.map((value, axis) => value + torque[axis]);
  }, [0, 0, 0]);
  const pairInteractionTorqueVectorElectronVolt = torqueFor(
    addedForceVectorsElectronVoltPerAngstrom);
  const pairInteractionTorqueMagnitudeElectronVolt = vectorNorm(
    pairInteractionTorqueVectorElectronVolt);
  const electrostaticTorqueVectorElectronVolt = torqueFor(
    addedCoulombForceVectorsElectronVoltPerAngstrom);
  const electrostaticTorqueMagnitudeElectronVolt = vectorNorm(electrostaticTorqueVectorElectronVolt);
  const bornMayerTorqueVectorElectronVolt = torqueFor(
    addedBornMayerForceVectorsElectronVoltPerAngstrom);
  const bornMayerTorqueMagnitudeElectronVolt = vectorNorm(bornMayerTorqueVectorElectronVolt);
  const dispersionTorqueVectorElectronVolt = torqueFor(
    addedDispersionForceVectorsElectronVoltPerAngstrom);
  const dispersionTorqueMagnitudeElectronVolt = vectorNorm(dispersionTorqueVectorElectronVolt);
  const inductionTorqueVectorElectronVolt = torqueFor(
    chargeInductionForce.forceVectorsElectronVoltPerAngstrom);
  const inductionTorqueMagnitudeElectronVolt = vectorNorm(inductionTorqueVectorElectronVolt);
  const reducedRmsForce = rmsAddedForceElectronVoltPerAngstrom
    * Number(forceReferenceLengthAngstrom) / thermalEnergyElectronVolt;
  const forceCancellationScore = (1 - reducedRmsForce) / (1 + reducedRmsForce);
  const combinedScore = (energyScore + forceCancellationScore) / 2;
  const score = observable === "force-cancellation" ? forceCancellationScore
    : observable === "combined" ? combinedScore : energyScore;
  const sumCharge = (sites) => sites.reduce((sum, site) => sum + site.charge, 0);
  const currentNetFormalCharge = sumCharge(current);
  const addedNetFormalCharge = sumCharge(added);
  const bornMayerApplied = bornAmplitude > 0
    || pairMatrix.records.some((record) => record.amplitudeElectronVolt > 0);
  return {
    available: pairCount > 0,
    score,
    energyScore,
    forceCancellationScore,
    combinedScore,
    deltaEnergyElectronVolt,
    coulombDeltaEnergyElectronVolt,
    bornMayerRepulsiveEnergyElectronVolt,
    dampedDispersionEnergyElectronVolt,
    chargeInductionDeltaEnergyElectronVolt,
    chargeInductionCurrentEnergyElectronVolt: chargeInduction.currentEnergyElectronVolt,
    chargeInductionProjectedEnergyElectronVolt: chargeInduction.projectedEnergyElectronVolt,
    energyPerAddedSiteElectronVolt: deltaEnergyElectronVolt / added.length,
    attractiveEnergyElectronVolt,
    repulsiveEnergyElectronVolt,
    signedChargeDistanceSumPerAngstrom,
    thermalEnergyElectronVolt,
    reducedThermalEnergyPerAddedSite,
    addedForceVectorsElectronVoltPerAngstrom,
    addedCoulombForceVectorsElectronVoltPerAngstrom,
    addedBornMayerForceVectorsElectronVoltPerAngstrom,
    addedDispersionForceVectorsElectronVoltPerAngstrom,
    addedInductionForceVectorsElectronVoltPerAngstrom:
      chargeInductionForce.forceVectorsElectronVoltPerAngstrom,
    forceMagnitudesElectronVoltPerAngstrom,
    rmsAddedForceElectronVoltPerAngstrom,
    maximumAddedForceElectronVoltPerAngstrom,
    netAddedForceVectorElectronVoltPerAngstrom,
    netAddedForceMagnitudeElectronVoltPerAngstrom,
    addedCentroidAngstrom,
    electrostaticTorqueVectorElectronVolt,
    electrostaticTorqueMagnitudeElectronVolt,
    bornMayerTorqueVectorElectronVolt,
    bornMayerTorqueMagnitudeElectronVolt,
    dispersionTorqueVectorElectronVolt,
    dispersionTorqueMagnitudeElectronVolt,
    inductionTorqueVectorElectronVolt,
    inductionTorqueMagnitudeElectronVolt,
    pairInteractionTorqueVectorElectronVolt,
    pairInteractionTorqueMagnitudeElectronVolt,
    forceReferenceLengthAngstrom: Number(forceReferenceLengthAngstrom),
    reducedRmsForce,
    rankingObservable: observable,
    currentNetFormalCharge,
    addedNetFormalCharge,
    projectedNetFormalCharge: currentNetFormalCharge + addedNetFormalCharge,
    pairCount,
    distanceEvaluations: distanceEvaluations + chargeInduction.distanceEvaluations
      + chargeInductionForce.distanceEvaluations,
    pairDistanceEvaluations: distanceEvaluations,
    inductionDistanceEvaluations: chargeInduction.distanceEvaluations,
    currentSites: current.length,
    addedSites: added.length,
    relativePermittivity: Number(relativePermittivity),
    bornMayerAmplitudeElectronVolt: bornAmplitude,
    bornMayerDecayAngstrom: bornDecay,
    bornMayerRepulsionApplied: bornMayerApplied,
    bornMayerPairPolicy: pairMatrix.policy,
    bornMayerPairMatrixApplied: pairMatrix.available,
    bornMayerPairMatrixRecordCount: pairMatrix.records.length,
    bornMayerPairMatrixFallbackCount: pairMatrixFallbackCount,
    bornMayerPairParameterUsage: [...pairParameterUsage.values()].sort((first, second) =>
      first.key.localeCompare(second.key)),
    dispersionC6ElectronVoltAngstrom6: dispersionC6,
    dispersionDampingLengthAngstrom: dispersionDampingLength,
    dispersionDampingModel: "Tang-Toennies f6(r/lambda)",
    dispersionApplied: dispersionC6 > 0,
    inductionPolarizabilityAngstrom3: Number(inductionPolarizabilityAngstrom3),
    inductionDampingLengthAngstrom: Number(inductionDampingLengthAngstrom),
    inductionDampingModel: chargeInduction.dampingModel,
    inductionMutualDampingModel: chargeInduction.mutualDampingModel,
    inductionRequestedResponseModel: chargeInduction.requestedResponseModel,
    inductionAppliedResponseModel: chargeInduction.appliedResponseModel,
    inductionSelfConsistentConverged: chargeInduction.selfConsistentConverged,
    inductionConvergenceIterations: chargeInduction.convergenceIterations,
    inductionConvergenceResidualElectronAngstrom:
      chargeInduction.convergenceResidualElectronAngstrom,
    inductionDirectFallbackApplied: chargeInduction.directFallbackApplied,
    inductionFallbackReason: chargeInduction.fallbackReason,
    inductionMutualTensorEvaluations: chargeInduction.mutualTensorEvaluations,
    inductionForceModeRequested: requestedInductionForceMode,
    inductionForceModeApplied: chargeInductionForce.available ? "finite-difference" : "omitted",
    inductionForceAvailable: chargeInductionForce.available,
    inductionForceStepAngstrom: chargeInductionForce.forceStepAngstrom
      ?? Number(inductionForceStepAngstrom),
    inductionForceEnergyEvaluations: chargeInductionForce.centralDifferenceEnergyEvaluations,
    inductionForceDistanceEvaluations: chargeInductionForce.distanceEvaluations,
    inductionForceMutualTensorEvaluations: chargeInductionForce.mutualTensorEvaluations,
    inductionForceMaximumRichardsonErrorElectronVoltPerAngstrom:
      chargeInductionForce.maximumRichardsonErrorElectronVoltPerAngstrom,
    inductionForceRmsRichardsonErrorElectronVoltPerAngstrom:
      chargeInductionForce.rmsRichardsonErrorElectronVoltPerAngstrom,
    inductionForceResponseConsistent: Boolean(chargeInductionForce.responseConsistent),
    inductionForceFailureReason: chargeInductionForce.available ? null : chargeInductionForce.reason,
    chargeInductionApplied: Number(inductionPolarizabilityAngstrom3) > 0,
    maximumInducedDipoleElectronAngstrom:
      chargeInduction.projected.maximumInducedDipoleElectronAngstrom,
    rmsInducedDipoleElectronAngstrom:
      chargeInduction.projected.rmsInducedDipoleElectronAngstrom,
    addedInducedDipoleVectorsElectronAngstrom:
      chargeInduction.projected.inducedDipolesElectronAngstrom.slice(current.length),
    chargeInductionModel: chargeInduction.model,
    pairInteractionModel: `${bornMayerApplied
      ? `Coulomb + Born–Mayer${pairMatrix.available ? " species-pair matrix" : ""}` : "Coulomb"}${dispersionC6 > 0 ? " + damped dispersion" : ""}${Number(inductionPolarizabilityAngstrom3) > 0 ? " + damped charge induction" : ""}`,
    temperatureKelvin: Number(temperatureKelvin),
    reachAngstrom: Number.isFinite(reach) ? reach : "global",
    scoreDefinition: observable === "force-cancellation"
      ? "(1-y)/(1+y), y = F_rms d_nn / (k_B T)"
      : observable === "combined"
        ? `mean of total energy and ${Number(inductionPolarizabilityAngstrom3) > 0
          ? chargeInductionForce.available ? "numerical total-energy-gradient" : "pair-force-only"
          : "exact energy-gradient"} cancellation scores`
        : "-x/(1+|x|), x = delta U / (N_added k_B T)",
    incrementalPairsOnly: Number(inductionPolarizabilityAngstrom3) === 0,
    incrementalManyBodyStateDifferenceEvaluated:
      Number(inductionPolarizabilityAngstrom3) > 0,
    currentCurrentConstantOmitted: true,
    pairCurrentCurrentConstantOmitted: true,
    inductionCurrentAndProjectedStatesEvaluated:
      Number(inductionPolarizabilityAngstrom3) > 0,
    formalPointChargesAssumed: true,
    suppliedFormalChargeOnly: true,
    coulombPrefactorApplied: true,
    declaredUniformRelativePermittivityApplied: true,
    finiteOpenBoundaryUsed: true,
    electrostaticEnergyEvaluated: true,
    electrostaticForceEvaluated: true,
    electrostaticForceIsEnergyGradient: true,
    pairInteractionEnergyEvaluated: true,
    pairInteractionForceEvaluated: true,
    pairInteractionForceIsNegativeEnergyGradient: Number(inductionPolarizabilityAngstrom3) === 0
      || chargeInductionForce.available,
    bornMayerParametersFitted: false,
    dispersionParametersFitted: false,
    inductionParametersFitted: false,
    chargeInductionEnergyEvaluated: Number(inductionPolarizabilityAngstrom3) > 0,
    chargeInductionEnergyIsManyBodyInChargeGeometry: Number(inductionPolarizabilityAngstrom3) > 0,
    mutualDipoleInductionSolved: chargeInduction.mutualDipoleInductionSolved,
    polarizationForceEvaluated: chargeInductionForce.available,
    totalMechanicalForceInferred: false,
    relaxationIntegrated: false,
    candidateGeometryChanged: false,
    hardAdmissionChanged: false,
    targetUsed: false,
    periodicImagesUsed: false,
    ewaldSummationUsed: false,
    neutralizingBackgroundUsed: false,
    dielectricResponseSolved: false,
    polarizationModeled: Number(inductionPolarizabilityAngstrom3) > 0,
    chargeTransferModeled: false,
    electronicStructureModeled: false,
    physicalTimeIntegrated: false,
    claimBoundary: bornMayerApplied || dispersionC6 > 0 || Number(inductionPolarizabilityAngstrom3) > 0
      ? `This is a conditional finite open-boundary Coulomb${bornMayerApplied ? " + isotropic Born–Mayer" : ""}${dispersionC6 > 0 ? " + Tang-Toennies-damped dispersion" : ""}${Number(inductionPolarizabilityAngstrom3) > 0 ? " + damped charge-induced-dipole energy" : ""} hypothesis. ${bornMayerApplied ? pairMatrix.available ? "The supplied species-pair matrix may be conditioned on frozen observed contact geometry, but no energy or force coefficient is fitted." : "A and rho are declared generic parameters, not fitted species-pair coefficients." : " Short-range repulsion is omitted."}${dispersionC6 > 0 ? " C6 and the damping length are declared generic controls, not fitted species-pair dispersion coefficients." : " Dispersion is omitted."}${Number(inductionPolarizabilityAngstrom3) > 0 ? ` Charge-field superposition makes the induction energy many-body in geometry.${chargeInduction.mutualDipoleInductionSolved ? " A damped mutual dipole tensor was iterated self-consistently to the reported tolerance." : chargeInduction.directFallbackApplied ? ` The requested mutual response failed closed to a consistent direct-only comparison (${chargeInduction.fallbackReason}).` : " Induced dipoles do not polarize one another."} ${chargeInductionForce.available ? `Polarization force is included as a response-consistent fourth-order Richardson numerical energy gradient using ${chargeInductionForce.centralDifferenceEnergyEvaluations} induction-energy evaluations.` : `Polarization force is omitted (${chargeInductionForce.reason}).`}` : " Polarization is omitted."} It omits periodic images, Ewald summation, charge transfer, electronic structure, and reservoir response. The displayed force is not a validated total mechanical force and is not integrated into relaxation or time.`
      : "This is the pair interaction energy and exact analytic electrostatic force on emitted supplied formal point charges in a declared uniform isotropic relative permittivity over one finite open-boundary crop. It omits periodic images, Ewald summation, polarization, charge transfer, self energy, short-range repulsion, dispersion, electronic structure, and solvent or reservoir response. The force is not a total mechanical force and is not integrated into relaxation or time; the model is conditional, not a validated material energy or force field.",
  };
}

export function finitePointChargeReachProfile(currentSites = [], addedSites = [], {
  nearestNeighborAngstrom,
  reachesNearestNeighborUnits = [2, 4, 8, "global"],
  relativePermittivity = 1,
  temperatureKelvin = 300,
  rankingObservable: rawRankingObservable = "energy",
  bornMayerAmplitudeElectronVolt = 0,
  bornMayerDecayAngstrom = .3,
  bornMayerPairMatrix = null,
  dispersionC6ElectronVoltAngstrom6 = 0,
  dispersionDampingLengthAngstrom = .3,
  inductionPolarizabilityAngstrom3 = 0,
  inductionDampingLengthAngstrom = .3,
  inductionResponseModel = "direct",
  inductionMaximumIterations = 128,
  inductionConvergenceToleranceElectronAngstrom = 1e-6,
  inductionIterationMixing = .5,
  inductionForceMode: rawInductionForceMode = "omitted",
  inductionForceStepAngstrom = 1e-4,
} = {}) {
  if (!finite(nearestNeighborAngstrom) || Number(nearestNeighborAngstrom) <= 0) {
    throw new RangeError("nearestNeighborAngstrom must be positive");
  }
  const reaches = [...new Set(reachesNearestNeighborUnits
    .map((reach) => reach === "global" ? "global" : Number(reach)))]
    .filter((reach) => reach === "global" || Number.isFinite(reach) && reach > 0);
  const samples = reaches.map((reach) => incrementalFinitePointChargeElectrostatics(
    currentSites, addedSites, {
      relativePermittivity,
      temperatureKelvin,
      forceReferenceLengthAngstrom: Number(nearestNeighborAngstrom),
      rankingObservable: rawRankingObservable,
      bornMayerAmplitudeElectronVolt,
      bornMayerDecayAngstrom,
      bornMayerPairMatrix,
      dispersionC6ElectronVoltAngstrom6,
      dispersionDampingLengthAngstrom,
      inductionPolarizabilityAngstrom3,
      inductionDampingLengthAngstrom,
      inductionResponseModel,
      inductionMaximumIterations,
      inductionConvergenceToleranceElectronAngstrom,
      inductionIterationMixing,
      inductionForceMode: rawInductionForceMode,
      inductionForceStepAngstrom,
      reachAngstrom: reach === "global" ? "global" : reach * Number(nearestNeighborAngstrom),
    }));
  const availableSamples = samples.filter((sample) => sample.available);
  const scores = availableSamples.map((sample) => sample.score);
  const energies = availableSamples.map((sample) => sample.deltaEnergyElectronVolt);
  return {
    available: samples.some((sample) => sample.available),
    reaches,
    samples: samples.map((sample, index) => ({ ...sample,
      reach: reaches[index], reachNearestNeighborUnits: reaches[index] })),
    scoreSpread: scores.length ? Math.max(...scores) - Math.min(...scores) : 0,
    deltaEnergySpreadElectronVolt: energies.length
      ? Math.max(...energies) - Math.min(...energies) : 0,
    distanceEvaluations: samples.reduce((sum, sample) =>
      sum + (sample.distanceEvaluations || 0), 0),
    relativePermittivity: Number(relativePermittivity),
    temperatureKelvin: Number(temperatureKelvin),
    rankingObservable: rankingObservable(rawRankingObservable),
    bornMayerAmplitudeElectronVolt: Number(bornMayerAmplitudeElectronVolt),
    bornMayerDecayAngstrom: Number(bornMayerDecayAngstrom),
    bornMayerPairPolicy: bornMayerPairMatrix?.policy || "uniform",
    bornMayerPairMatrixApplied: Boolean(bornMayerPairMatrix?.records?.length),
    dispersionC6ElectronVoltAngstrom6: Number(dispersionC6ElectronVoltAngstrom6),
    dispersionDampingLengthAngstrom: Number(dispersionDampingLengthAngstrom),
    inductionPolarizabilityAngstrom3: Number(inductionPolarizabilityAngstrom3),
    inductionDampingLengthAngstrom: Number(inductionDampingLengthAngstrom),
    inductionResponseModel,
    inductionMaximumIterations,
    inductionConvergenceToleranceElectronAngstrom,
    inductionIterationMixing,
    inductionForceModeRequested: inductionForceMode(rawInductionForceMode),
    chargeInductionApplied: Number(inductionPolarizabilityAngstrom3) > 0,
    inductionParametersFitted: false,
    mutualDipoleInductionSolved: Number(inductionPolarizabilityAngstrom3) > 0
      && inductionResponseModel === "self-consistent" && availableSamples.length > 0
      && availableSamples.every((sample) => sample.mutualDipoleInductionSolved),
    inductionDirectFallbackSamples: availableSamples.filter((sample) =>
      sample.inductionDirectFallbackApplied).length,
    inductionMaximumConvergenceIterations: Math.max(0, ...availableSamples.map((sample) =>
      sample.inductionConvergenceIterations || 0)),
    inductionMaximumConvergenceResidualElectronAngstrom: Math.max(0,
      ...availableSamples.map((sample) =>
        sample.inductionConvergenceResidualElectronAngstrom || 0)),
    inductionMutualTensorEvaluations: availableSamples.reduce((sum, sample) =>
      sum + (sample.inductionMutualTensorEvaluations || 0), 0),
    polarizationForceEvaluated: Number(inductionPolarizabilityAngstrom3) > 0
      && availableSamples.length > 0
      && availableSamples.every((sample) => sample.polarizationForceEvaluated),
    inductionForceUnavailableSamples: availableSamples.filter((sample) =>
      Number(inductionPolarizabilityAngstrom3) > 0 && !sample.inductionForceAvailable).length,
    inductionForceEnergyEvaluations: availableSamples.reduce((sum, sample) =>
      sum + (sample.inductionForceEnergyEvaluations || 0), 0),
    inductionForceDistanceEvaluations: availableSamples.reduce((sum, sample) =>
      sum + (sample.inductionForceDistanceEvaluations || 0), 0),
    inductionForceMutualTensorEvaluations: availableSamples.reduce((sum, sample) =>
      sum + (sample.inductionForceMutualTensorEvaluations || 0), 0),
    inductionForceMaximumRichardsonErrorElectronVoltPerAngstrom: Math.max(0,
      ...availableSamples.map((sample) =>
        sample.inductionForceMaximumRichardsonErrorElectronVoltPerAngstrom || 0)),
    nearestNeighborAngstrom: Number(nearestNeighborAngstrom),
    candidateSetChanged: false,
    candidateGeometryChanged: false,
    hardAdmissionChanged: false,
    targetUsed: false,
    ewaldConvergenceInferred: false,
    thermodynamicLimitInferred: false,
  };
}
