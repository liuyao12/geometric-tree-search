export const COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM = 14.3996454784255;
export const BOLTZMANN_ELECTRON_VOLT_PER_KELVIN = 8.617333262145e-5;

export const FINITE_POINT_CHARGE_PROVENANCE = Object.freeze({
  model: "finite open-boundary formal-point-charge Coulomb interaction with optional Born–Mayer repulsive core and exact analytic gradient",
  coulombConstantSource: "2018 CODATA elementary charge and vacuum permittivity",
  coulombConstantElectronVoltAngstrom: COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM,
  boltzmannConstantElectronVoltPerKelvin: BOLTZMANN_ELECTRON_VOLT_PER_KELVIN,
  boundaryCondition: "finite open boundary; no periodic images or neutralizing background",
});

const finite = (value) => Number.isFinite(Number(value));

function normalizedSite(site, label) {
  if (!Array.isArray(site?.position) || site.position.length !== 3
      || !site.position.every(finite) || !finite(site?.charge)) {
    throw new TypeError(`${label} needs a finite Cartesian position and formal charge`);
  }
  return { position: site.position.map(Number), charge: Number(site.charge) };
}

function vectorNorm(vector) {
  return Math.hypot(...vector);
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
  const observable = rankingObservable(rawRankingObservable);
  const reach = declaredReach(reachAngstrom);
  const current = currentSites.map((site, index) => normalizedSite(site, `current site ${index + 1}`));
  const added = addedSites.map((site, index) => normalizedSite(site, `added site ${index + 1}`));
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
  let pairCount = 0;
  let distanceEvaluations = 0;
  const addedForceVectorsElectronVoltPerAngstrom = added.map(() => [0, 0, 0]);
  const addedCoulombForceVectorsElectronVoltPerAngstrom = added.map(() => [0, 0, 0]);
  const addedBornMayerForceVectorsElectronVoltPerAngstrom = added.map(() => [0, 0, 0]);
  const prefactor = COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM / Number(relativePermittivity);
  const bornAmplitude = Number(bornMayerAmplitudeElectronVolt);
  const bornDecay = Number(bornMayerDecayAngstrom);
  const accumulate = (first, second, firstAddedIndex, secondAddedIndex = null) => {
    const displacement = first.position.map((value, axis) => value - second.position[axis]);
    const separation = vectorNorm(displacement);
    distanceEvaluations += 1;
    if (!(separation > 1e-10)) throw new Error("coincident charged sites make the point-charge model singular");
    if (separation > reach) return;
    const chargeDistanceTerm = first.charge * second.charge / separation;
    const coulombEnergy = prefactor * chargeDistanceTerm;
    const bornMayerEnergy = bornAmplitude * Math.exp(-separation / bornDecay);
    const energy = coulombEnergy + bornMayerEnergy;
    signedChargeDistanceSumPerAngstrom += chargeDistanceTerm;
    if (coulombEnergy < 0) attractiveEnergyElectronVolt += -coulombEnergy;
    else repulsiveEnergyElectronVolt += coulombEnergy;
    bornMayerRepulsiveEnergyElectronVolt += bornMayerEnergy;
    repulsiveEnergyElectronVolt += bornMayerEnergy;
    const coulombForceScale = prefactor * first.charge * second.charge / separation ** 3;
    const bornMayerForceScale = bornMayerEnergy / (bornDecay * separation);
    displacement.forEach((component, axis) => {
      const coulombForce = coulombForceScale * component;
      const bornMayerForce = bornMayerForceScale * component;
      const force = coulombForce + bornMayerForce;
      addedForceVectorsElectronVoltPerAngstrom[firstAddedIndex][axis] += force;
      addedCoulombForceVectorsElectronVoltPerAngstrom[firstAddedIndex][axis] += coulombForce;
      addedBornMayerForceVectorsElectronVoltPerAngstrom[firstAddedIndex][axis] += bornMayerForce;
      if (secondAddedIndex !== null) {
        addedForceVectorsElectronVoltPerAngstrom[secondAddedIndex][axis] -= force;
        addedCoulombForceVectorsElectronVoltPerAngstrom[secondAddedIndex][axis] -= coulombForce;
        addedBornMayerForceVectorsElectronVoltPerAngstrom[secondAddedIndex][axis] -= bornMayerForce;
      }
    });
    pairCount += 1;
  };
  added.forEach((site, addedIndex) => current.forEach((neighbor) =>
    accumulate(site, neighbor, addedIndex)));
  added.forEach((site, index) => added.slice(index + 1)
    .forEach((neighbor, relativeIndex) => accumulate(site, neighbor, index, index + relativeIndex + 1)));
  const coulombDeltaEnergyElectronVolt = prefactor * signedChargeDistanceSumPerAngstrom;
  const deltaEnergyElectronVolt = coulombDeltaEnergyElectronVolt
    + bornMayerRepulsiveEnergyElectronVolt;
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
  const reducedRmsForce = rmsAddedForceElectronVoltPerAngstrom
    * Number(forceReferenceLengthAngstrom) / thermalEnergyElectronVolt;
  const forceCancellationScore = (1 - reducedRmsForce) / (1 + reducedRmsForce);
  const combinedScore = (energyScore + forceCancellationScore) / 2;
  const score = observable === "force-cancellation" ? forceCancellationScore
    : observable === "combined" ? combinedScore : energyScore;
  const sumCharge = (sites) => sites.reduce((sum, site) => sum + site.charge, 0);
  const currentNetFormalCharge = sumCharge(current);
  const addedNetFormalCharge = sumCharge(added);
  return {
    available: pairCount > 0,
    score,
    energyScore,
    forceCancellationScore,
    combinedScore,
    deltaEnergyElectronVolt,
    coulombDeltaEnergyElectronVolt,
    bornMayerRepulsiveEnergyElectronVolt,
    energyPerAddedSiteElectronVolt: deltaEnergyElectronVolt / added.length,
    attractiveEnergyElectronVolt,
    repulsiveEnergyElectronVolt,
    signedChargeDistanceSumPerAngstrom,
    thermalEnergyElectronVolt,
    reducedThermalEnergyPerAddedSite,
    addedForceVectorsElectronVoltPerAngstrom,
    addedCoulombForceVectorsElectronVoltPerAngstrom,
    addedBornMayerForceVectorsElectronVoltPerAngstrom,
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
    pairInteractionTorqueVectorElectronVolt,
    pairInteractionTorqueMagnitudeElectronVolt,
    forceReferenceLengthAngstrom: Number(forceReferenceLengthAngstrom),
    reducedRmsForce,
    rankingObservable: observable,
    currentNetFormalCharge,
    addedNetFormalCharge,
    projectedNetFormalCharge: currentNetFormalCharge + addedNetFormalCharge,
    pairCount,
    distanceEvaluations,
    currentSites: current.length,
    addedSites: added.length,
    relativePermittivity: Number(relativePermittivity),
    bornMayerAmplitudeElectronVolt: bornAmplitude,
    bornMayerDecayAngstrom: bornDecay,
    bornMayerRepulsionApplied: bornAmplitude > 0,
    pairInteractionModel: bornAmplitude > 0 ? "Coulomb + Born–Mayer" : "Coulomb",
    temperatureKelvin: Number(temperatureKelvin),
    reachAngstrom: Number.isFinite(reach) ? reach : "global",
    scoreDefinition: observable === "force-cancellation"
      ? "(1-y)/(1+y), y = F_rms d_nn / (k_B T)"
      : observable === "combined"
        ? "mean of energy and electrostatic-force-cancellation scores"
        : "-x/(1+|x|), x = delta U / (N_added k_B T)",
    incrementalPairsOnly: true,
    currentCurrentConstantOmitted: true,
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
    pairInteractionForceIsNegativeEnergyGradient: true,
    bornMayerParametersFitted: false,
    totalMechanicalForceInferred: false,
    relaxationIntegrated: false,
    candidateGeometryChanged: false,
    hardAdmissionChanged: false,
    targetUsed: false,
    periodicImagesUsed: false,
    ewaldSummationUsed: false,
    neutralizingBackgroundUsed: false,
    dielectricResponseSolved: false,
    polarizationModeled: false,
    chargeTransferModeled: false,
    electronicStructureModeled: false,
    physicalTimeIntegrated: false,
    claimBoundary: bornAmplitude > 0
      ? "This is a conditional finite open-boundary Coulomb + isotropic Born–Mayer pair hypothesis. A and rho are declared generic parameters, not fitted species-pair coefficients. It omits periodic images, Ewald summation, polarization, charge transfer, dispersion, many-body terms, electronic structure, and reservoir response. The force is not a validated total mechanical force and is not integrated into relaxation or time."
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
    nearestNeighborAngstrom: Number(nearestNeighborAngstrom),
    candidateSetChanged: false,
    candidateGeometryChanged: false,
    hardAdmissionChanged: false,
    targetUsed: false,
    ewaldConvergenceInferred: false,
    thermodynamicLimitInferred: false,
  };
}
