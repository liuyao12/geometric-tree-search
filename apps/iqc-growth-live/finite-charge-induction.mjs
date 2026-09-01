export const COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM = 14.3996454784255;
export const CHARGE_INDUCTION_DAMPING_ORDER = 3;

const finite = (value) => Number.isFinite(Number(value));
const norm = (vector) => Math.hypot(...vector);

function normalizedSite(site, label) {
  if (!site || !Array.isArray(site.position) || site.position.length !== 3
      || !site.position.every(finite) || !finite(site.charge)) {
    throw new TypeError(`${label} must provide finite position[3] and charge`);
  }
  return { position: site.position.map(Number), charge: Number(site.charge),
    species: site.species === undefined ? null : String(site.species) };
}

export function tangToenniesChargeDamping(argument) {
  const x = Number(argument);
  if (!finite(x) || x < 0) throw new RangeError("damping argument must be finite and nonnegative");
  if (x === 0) return 0;
  if (x < 1) {
    let term = x ** (CHARGE_INDUCTION_DAMPING_ORDER + 1)
      / 24;
    let sum = term;
    for (let index = CHARGE_INDUCTION_DAMPING_ORDER + 2; index < 80; index += 1) {
      term *= x / index;
      sum += term;
      if (Math.abs(term) <= Math.abs(sum) * 1e-16) break;
    }
    return Math.exp(-x) * sum;
  }
  let term = 1;
  let polynomial = 1;
  for (let index = 1; index <= CHARGE_INDUCTION_DAMPING_ORDER; index += 1) {
    term *= x / index;
    polynomial += term;
  }
  return Math.max(0, Math.min(1, 1 - Math.exp(-x) * polynomial));
}

function resolvedReach(reachAngstrom) {
  if (reachAngstrom === "global" || reachAngstrom === Infinity) return Infinity;
  if (!finite(reachAngstrom) || Number(reachAngstrom) <= 0) {
    throw new RangeError("reachAngstrom must be positive or global");
  }
  return Number(reachAngstrom);
}

export function finiteDampedChargeInductionEnergy(rawSites, {
  polarizabilityAngstrom3 = 0,
  dampingLengthAngstrom = .3,
  reachAngstrom = "global",
  relativePermittivity = 1,
} = {}) {
  const sites = rawSites.map((site, index) => normalizedSite(site, `site ${index + 1}`));
  const alpha = Number(polarizabilityAngstrom3);
  const dampingLength = Number(dampingLengthAngstrom);
  const reach = resolvedReach(reachAngstrom);
  const epsilon = Number(relativePermittivity);
  if (!finite(alpha) || alpha < 0 || alpha > 100) {
    throw new RangeError("polarizabilityAngstrom3 must be between 0 and 100");
  }
  if (!finite(dampingLength) || dampingLength <= 0 || dampingLength > 10) {
    throw new RangeError("dampingLengthAngstrom must be between 0 and 10");
  }
  if (!finite(epsilon) || epsilon < 1 || epsilon > 1000) {
    throw new RangeError("relativePermittivity must be between 1 and 1000");
  }
  if (alpha === 0) return {
    available: false,
    energyElectronVolt: 0,
    siteInductionEnergyElectronVolt: sites.map(() => 0),
    electricFieldGeometryPerAngstrom2: sites.map(() => [0, 0, 0]),
    inducedDipolesElectronAngstrom: sites.map(() => [0, 0, 0]),
    maximumInducedDipoleElectronAngstrom: 0,
    rmsInducedDipoleElectronAngstrom: 0,
    polarizabilityAngstrom3: 0,
    relativePermittivity: epsilon,
    dampingLengthAngstrom: dampingLength,
    dampingModel: "Tang-Toennies f3(r/lambda)",
    reachAngstrom: Number.isFinite(reach) ? reach : "global",
    sites: sites.length,
    includedDirectedPairs: 0,
    distanceEvaluations: 0,
    chargeFieldOnly: true,
    mutualDipoleInductionSolved: false,
    polarizationForceEvaluated: false,
    targetUsed: false,
  };
  let distanceEvaluations = 0;
  let includedDirectedPairs = 0;
  const electricFieldGeometryPerAngstrom2 = sites.map((site, index) => {
    const field = [0, 0, 0];
    sites.forEach((source, sourceIndex) => {
      if (sourceIndex === index) return;
      const displacement = site.position.map((value, axis) => value - source.position[axis]);
      const distance = norm(displacement);
      distanceEvaluations += 1;
      if (!(distance > 1e-10)) throw new Error("coincident charged sites make induction singular");
      if (distance > reach) return;
      const damping = tangToenniesChargeDamping(distance / dampingLength);
      const scale = source.charge * damping / distance ** 3;
      displacement.forEach((component, axis) => { field[axis] += scale * component; });
      includedDirectedPairs += 1;
    });
    return field;
  });
  const inducedDipolesElectronAngstrom = electricFieldGeometryPerAngstrom2
    .map((field) => field.map((component) => alpha * component / epsilon));
  const siteInductionEnergyElectronVolt = electricFieldGeometryPerAngstrom2.map((field) =>
    -.5 * COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM * alpha / epsilon ** 2
      * field.reduce((sum, component) => sum + component ** 2, 0));
  const energyElectronVolt = siteInductionEnergyElectronVolt.reduce((sum, value) => sum + value, 0);
  return {
    available: sites.length > 0 && alpha > 0,
    energyElectronVolt,
    siteInductionEnergyElectronVolt,
    electricFieldGeometryPerAngstrom2,
    inducedDipolesElectronAngstrom,
    maximumInducedDipoleElectronAngstrom: Math.max(0,
      ...inducedDipolesElectronAngstrom.map(norm)),
    rmsInducedDipoleElectronAngstrom: Math.sqrt(inducedDipolesElectronAngstrom
      .reduce((sum, dipole) => sum + norm(dipole) ** 2, 0) / Math.max(1, sites.length)),
    polarizabilityAngstrom3: alpha,
    relativePermittivity: epsilon,
    dampingLengthAngstrom: dampingLength,
    dampingModel: "Tang-Toennies f3(r/lambda)",
    reachAngstrom: Number.isFinite(reach) ? reach : "global",
    sites: sites.length,
    includedDirectedPairs,
    distanceEvaluations,
    chargeFieldOnly: true,
    mutualDipoleInductionSolved: false,
    polarizationForceEvaluated: false,
    targetUsed: false,
  };
}

export function incrementalFiniteChargeInduction(currentSites, addedSites, options = {}) {
  const current = finiteDampedChargeInductionEnergy(currentSites, options);
  const projected = finiteDampedChargeInductionEnergy([...currentSites, ...addedSites], options);
  return {
    available: projected.available && addedSites.length > 0,
    deltaEnergyElectronVolt: projected.energyElectronVolt - current.energyElectronVolt,
    currentEnergyElectronVolt: current.energyElectronVolt,
    projectedEnergyElectronVolt: projected.energyElectronVolt,
    current,
    projected,
    addedSites: addedSites.length,
    distanceEvaluations: current.distanceEvaluations + projected.distanceEvaluations,
    polarizabilityAngstrom3: projected.polarizabilityAngstrom3,
    relativePermittivity: projected.relativePermittivity,
    dampingLengthAngstrom: projected.dampingLengthAngstrom,
    dampingModel: projected.dampingModel,
    model: "finite damped charge-induced dipoles",
    energyIsManyBodyInChargeGeometry: true,
    chargeFieldOnly: true,
    mutualDipoleInductionSolved: false,
    polarizationForceEvaluated: false,
    parametersFitted: false,
    targetUsed: false,
    claimBoundary: "Finite open-crop, isotropic charge-induced dipole energy with Tang-Toennies-damped charge fields. Field superposition makes the energy many-body in geometry, but induced dipoles do not polarize one another; no polarization force, species-specific polarizability fit, periodic response, electronic structure, relaxation, or physical time is inferred.",
  };
}
