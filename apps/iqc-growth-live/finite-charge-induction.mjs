export const COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM = 14.3996454784255;
export const CHARGE_INDUCTION_DAMPING_ORDER = 3;

const finite = (value) => Number.isFinite(Number(value));
const norm = (vector) => Math.hypot(...vector);
const add = (first, second) => first.map((value, axis) => value + second[axis]);
const scale = (vector, factor) => vector.map((value) => value * factor);

function responseModel(value) {
  if (["direct", "self-consistent"].includes(value)) return value;
  throw new RangeError("responseModel must be direct or self-consistent");
}

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

/** Damped dipole tensor action: [3 f5 (mu·rhat) rhat - f3 mu] / r^3. */
export function tangToenniesDipoleField(displacement, dipole, dampingLengthAngstrom) {
  if (!Array.isArray(displacement) || displacement.length !== 3
      || !displacement.every(finite) || !Array.isArray(dipole) || dipole.length !== 3
      || !dipole.every(finite)) throw new TypeError("finite displacement[3] and dipole[3] required");
  const dampingLength = Number(dampingLengthAngstrom);
  if (!finite(dampingLength) || dampingLength <= 0 || dampingLength > 10) {
    throw new RangeError("dampingLengthAngstrom must be between 0 and 10");
  }
  const distance = norm(displacement);
  if (!(distance > 1e-10)) throw new Error("coincident dipoles make mutual induction singular");
  const radial = displacement.map((component) => component / distance);
  const projection = dipole.reduce((sum, component, axis) =>
    sum + component * radial[axis], 0);
  const x = distance / dampingLength;
  const f3 = tangToenniesChargeDamping(x);
  const f5 = (() => {
    if (x === 0) return 0;
    if (x < 1) {
      let term = x ** 6 / 720;
      let sum = term;
      for (let index = 7; index < 82; index += 1) {
        term *= x / index;
        sum += term;
        if (Math.abs(term) <= Math.abs(sum) * 1e-16) break;
      }
      return Math.exp(-x) * sum;
    }
    let term = 1;
    let polynomial = 1;
    for (let index = 1; index <= 5; index += 1) {
      term *= x / index;
      polynomial += term;
    }
    return Math.max(0, Math.min(1, 1 - Math.exp(-x) * polynomial));
  })();
  return radial.map((component, axis) =>
    (3 * f5 * projection * component - f3 * dipole[axis]) / distance ** 3);
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
  responseModel: rawResponseModel = "direct",
  maximumIterations = 64,
  convergenceToleranceElectronAngstrom = 1e-8,
  iterationMixing = .5,
} = {}) {
  const sites = rawSites.map((site, index) => normalizedSite(site, `site ${index + 1}`));
  const alpha = Number(polarizabilityAngstrom3);
  const dampingLength = Number(dampingLengthAngstrom);
  const reach = resolvedReach(reachAngstrom);
  const epsilon = Number(relativePermittivity);
  const requestedResponseModel = responseModel(rawResponseModel);
  if (!finite(alpha) || alpha < 0 || alpha > 100) {
    throw new RangeError("polarizabilityAngstrom3 must be between 0 and 100");
  }
  if (!finite(dampingLength) || dampingLength <= 0 || dampingLength > 10) {
    throw new RangeError("dampingLengthAngstrom must be between 0 and 10");
  }
  if (!finite(epsilon) || epsilon < 1 || epsilon > 1000) {
    throw new RangeError("relativePermittivity must be between 1 and 1000");
  }
  if (!Number.isInteger(maximumIterations) || maximumIterations < 1 || maximumIterations > 512) {
    throw new RangeError("maximumIterations must be an integer from 1 to 512");
  }
  if (!finite(convergenceToleranceElectronAngstrom)
      || Number(convergenceToleranceElectronAngstrom) <= 0
      || Number(convergenceToleranceElectronAngstrom) > 1) {
    throw new RangeError("convergenceToleranceElectronAngstrom must be between 0 and 1");
  }
  if (!finite(iterationMixing) || Number(iterationMixing) <= 0 || Number(iterationMixing) > 1) {
    throw new RangeError("iterationMixing must be between 0 and 1");
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
    mutualDampingModel: "Tang-Toennies f3/f5 dipole tensor",
    reachAngstrom: Number.isFinite(reach) ? reach : "global",
    sites: sites.length,
    includedDirectedPairs: 0,
    distanceEvaluations: 0,
    mutualTensorEvaluations: 0,
    requestedResponseModel,
    appliedResponseModel: "off",
    selfConsistentConverged: true,
    convergenceIterations: 0,
    convergenceResidualElectronAngstrom: 0,
    directFallbackApplied: false,
    fallbackReason: null,
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
  const directDipoles = electricFieldGeometryPerAngstrom2
    .map((field) => field.map((component) => alpha * component / epsilon));
  let inducedDipolesElectronAngstrom = directDipoles.map((dipole) => [...dipole]);
  let selfConsistentConverged = requestedResponseModel === "direct" || sites.length === 0;
  let convergenceIterations = 0;
  let convergenceResidualElectronAngstrom = 0;
  let mutualTensorEvaluations = 0;
  let fallbackReason = null;
  if (requestedResponseModel === "self-consistent" && sites.length) {
    const mixing = Number(iterationMixing);
    const tolerance = Number(convergenceToleranceElectronAngstrom);
    for (let iteration = 1; iteration <= maximumIterations; iteration += 1) {
      const targets = sites.map((site, index) => {
        let localField = [...electricFieldGeometryPerAngstrom2[index]];
        sites.forEach((source, sourceIndex) => {
          if (sourceIndex === index) return;
          const displacement = site.position.map((value, axis) => value - source.position[axis]);
          const distance = norm(displacement);
          if (distance > reach) return;
          localField = add(localField, tangToenniesDipoleField(displacement,
            inducedDipolesElectronAngstrom[sourceIndex], dampingLength));
          mutualTensorEvaluations += 1;
        });
        return scale(localField, alpha / epsilon);
      });
      convergenceResidualElectronAngstrom = Math.max(0, ...targets.map((target, index) =>
        norm(target.map((value, axis) => value - inducedDipolesElectronAngstrom[index][axis]))));
      inducedDipolesElectronAngstrom = targets.map((target, index) =>
        target.map((value, axis) => mixing * value
          + (1 - mixing) * inducedDipolesElectronAngstrom[index][axis]));
      convergenceIterations = iteration;
      if (!inducedDipolesElectronAngstrom.flat().every(Number.isFinite)
          || Math.max(0, ...inducedDipolesElectronAngstrom.map(norm)) > 1e6) {
        fallbackReason = "mutual induced-dipole iteration diverged";
        break;
      }
      if (convergenceResidualElectronAngstrom <= tolerance) {
        selfConsistentConverged = true;
        break;
      }
    }
    if (!selfConsistentConverged && !fallbackReason) {
      fallbackReason = `mutual induced-dipole iteration did not converge in ${maximumIterations} steps`;
    }
    if (!selfConsistentConverged) {
      inducedDipolesElectronAngstrom = directDipoles.map((dipole) => [...dipole]);
    }
  }
  const siteInductionEnergyElectronVolt = electricFieldGeometryPerAngstrom2.map((field, index) =>
    -.5 * COULOMB_ENERGY_ELECTRON_VOLT_ANGSTROM / epsilon
      * field.reduce((sum, component, axis) =>
        sum + component * inducedDipolesElectronAngstrom[index][axis], 0));
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
    mutualDampingModel: "Tang-Toennies f3/f5 dipole tensor",
    reachAngstrom: Number.isFinite(reach) ? reach : "global",
    sites: sites.length,
    includedDirectedPairs,
    distanceEvaluations,
    mutualTensorEvaluations,
    requestedResponseModel,
    appliedResponseModel: selfConsistentConverged && requestedResponseModel === "self-consistent"
      ? "self-consistent" : "direct",
    selfConsistentConverged,
    convergenceIterations,
    convergenceResidualElectronAngstrom,
    maximumIterations,
    convergenceToleranceElectronAngstrom: Number(convergenceToleranceElectronAngstrom),
    iterationMixing: Number(iterationMixing),
    directFallbackApplied: requestedResponseModel === "self-consistent" && !selfConsistentConverged,
    fallbackReason,
    chargeFieldOnly: requestedResponseModel === "direct" || !selfConsistentConverged,
    mutualDipoleInductionSolved: requestedResponseModel === "self-consistent"
      && selfConsistentConverged,
    polarizationForceEvaluated: false,
    targetUsed: false,
  };
}

export function incrementalFiniteChargeInduction(currentSites, addedSites, options = {}) {
  let current = finiteDampedChargeInductionEnergy(currentSites, options);
  let projected = finiteDampedChargeInductionEnergy([...currentSites, ...addedSites], options);
  const requestedResponseModel = responseModel(options.responseModel || "direct");
  const attemptedMutualTensorEvaluations = current.mutualTensorEvaluations
    + projected.mutualTensorEvaluations;
  const attemptedConvergenceIterations = Math.max(current.convergenceIterations,
    projected.convergenceIterations);
  const attemptedConvergenceResidualElectronAngstrom = Math.max(
    current.convergenceResidualElectronAngstrom,
    projected.convergenceResidualElectronAngstrom);
  const consistentMutualSolution = requestedResponseModel !== "self-consistent"
    || current.selfConsistentConverged && projected.selfConsistentConverged;
  let directFallbackApplied = false;
  let fallbackReason = null;
  if (!consistentMutualSolution) {
    fallbackReason = [current.fallbackReason, projected.fallbackReason].filter(Boolean).join("; ");
    current = finiteDampedChargeInductionEnergy(currentSites, { ...options,
      responseModel: "direct" });
    projected = finiteDampedChargeInductionEnergy([...currentSites, ...addedSites], { ...options,
      responseModel: "direct" });
    directFallbackApplied = true;
  }
  const polarizationActive = projected.polarizabilityAngstrom3 > 0
    && addedSites.length > 0;
  return {
    available: projected.available && addedSites.length > 0,
    deltaEnergyElectronVolt: projected.energyElectronVolt - current.energyElectronVolt,
    currentEnergyElectronVolt: current.energyElectronVolt,
    projectedEnergyElectronVolt: projected.energyElectronVolt,
    current,
    projected,
    addedSites: addedSites.length,
    distanceEvaluations: current.distanceEvaluations + projected.distanceEvaluations,
    mutualTensorEvaluations: attemptedMutualTensorEvaluations,
    polarizabilityAngstrom3: projected.polarizabilityAngstrom3,
    relativePermittivity: projected.relativePermittivity,
    dampingLengthAngstrom: projected.dampingLengthAngstrom,
    dampingModel: projected.dampingModel,
    mutualDampingModel: projected.mutualDampingModel,
    model: !polarizationActive ? "charge induction off"
      : directFallbackApplied || requestedResponseModel === "direct"
        ? "finite damped direct charge-induced dipoles"
        : "finite damped self-consistent charge-induced dipoles",
    energyIsManyBodyInChargeGeometry: polarizationActive,
    requestedResponseModel,
    appliedResponseModel: !polarizationActive ? "off"
      : directFallbackApplied ? "direct" : requestedResponseModel,
    selfConsistentConverged: requestedResponseModel === "direct"
      || !directFallbackApplied,
    convergenceIterations: attemptedConvergenceIterations,
    convergenceResidualElectronAngstrom: attemptedConvergenceResidualElectronAngstrom,
    directFallbackApplied,
    fallbackReason,
    chargeFieldOnly: !polarizationActive || directFallbackApplied
      || requestedResponseModel === "direct",
    mutualDipoleInductionSolved: polarizationActive
      && requestedResponseModel === "self-consistent" && !directFallbackApplied,
    polarizationForceEvaluated: false,
    parametersFitted: false,
    targetUsed: false,
    claimBoundary: !polarizationActive
      ? "Charge induction is off; no polarization energy or response is inferred."
      : `Finite open-crop, isotropic charge-induced dipole energy with Tang-Toennies-damped charge fields${requestedResponseModel === "self-consistent" && !directFallbackApplied ? " and a converged damped mutual dipole tensor" : ""}. Field superposition makes the energy many-body in geometry.${directFallbackApplied ? ` The requested mutual response failed closed to a consistent direct-only current/projected comparison (${fallbackReason}).` : requestedResponseModel === "direct" ? " Induced dipoles do not polarize one another." : " The induced dipoles were iterated self-consistently to the reported tolerance."} No polarization force, species-specific polarizability fit, periodic response, electronic structure, relaxation, or physical time is inferred.`,
  };
}
