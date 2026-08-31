import { cartesianNormalToIntrinsic, orientedEnergyKernelEstimate }
  from "./wulff-shape-regularizer.mjs";

const ANGSTROM_CUBED_TO_METRE_CUBED = 1e-30;
const EPS = 1e-30;

function finite(value, label) {
  const result = Number(value);
  if (!Number.isFinite(result)) throw new TypeError(`${label} must be finite`);
  return result;
}

function positive(value, label) {
  const result = finite(value, label);
  if (!(result > 0)) throw new RangeError(`${label} must be positive`);
  return result;
}

function digest(value, label) {
  if (typeof value !== "string" || !/^[0-9a-f]{64}$/i.test(value)) {
    throw new TypeError(`${label} must be a SHA-256 digest`);
  }
  return value.toLowerCase();
}

function unit(value, label) {
  if (!Array.isArray(value) || value.length !== 3) throw new TypeError(`${label} must contain 3 components`);
  const vector = value.map((entry, index) => finite(entry, `${label}[${index}]`));
  const norm = Math.hypot(...vector);
  if (!(norm > 1e-12)) throw new RangeError(`${label} must be nonzero`);
  return vector.map((entry) => entry / norm);
}

export function periodicSiteNumberDensity({ cellVolumeCubicAngstrom, siteOccupancies }) {
  const volume = positive(cellVolumeCubicAngstrom, "periodic cell volume");
  if (!Array.isArray(siteOccupancies) || !siteOccupancies.length) {
    throw new Error("periodic site occupancies are required");
  }
  const occupiedSites = siteOccupancies.reduce((sum, entry, index) => {
    const occupancy = finite(entry, `site occupancy ${index + 1}`);
    if (!(occupancy > 0 && occupancy <= 1 + 1e-8)) throw new RangeError("site occupancies must lie in (0, 1]");
    return sum + Math.min(1, occupancy);
  }, 0);
  return {
    occupiedSites,
    cellVolumeCubicAngstrom: volume,
    siteNumberDensityAtomsPerCubicMetre: occupiedSites / (volume * ANGSTROM_CUBED_TO_METRE_CUBED),
    atomicVolumeCubicAngstromPerOccupiedSite: volume / occupiedSites,
    source: "supplied periodic cell and crystallographic site occupancies",
    geometricReferenceOnly: true,
    massDensityInferred: false,
    thermalExpansionInferred: false,
    targetUsed: false,
  };
}

export function coupleInterfaceSupplyAndAttachment({
  patches, orientations, orientationBasisCartesian, siteNumberDensityAtomsPerCubicMetre,
  fluxCouplingStateSha256, kineticsCouplingStateSha256, maximumAngleRadians = Math.PI / 4,
}) {
  const fluxState = digest(fluxCouplingStateSha256, "flux coupling-state SHA-256");
  const kineticsState = digest(kineticsCouplingStateSha256, "kinetics coupling-state SHA-256");
  if (fluxState !== kineticsState) throw new Error("transport and attachment responses declare different driving states");
  const density = positive(siteNumberDensityAtomsPerCubicMetre, "site number density");
  if (!Array.isArray(patches) || patches.length < 4) throw new Error("at least four validated flux patches are required");
  if (!Array.isArray(orientations) || orientations.length < 3) throw new Error("validated oriented velocities are required");
  if (!Array.isArray(orientationBasisCartesian) || ![2, 3].includes(orientationBasisCartesian.length)) {
    throw new Error("a 2D or 3D orientation basis is required");
  }
  const mapped = orientations.map((entry) => ({
    orientationId: entry.orientationId,
    normal: entry.normal,
    interfacialFreeEnergy: positive(entry.normalGrowthVelocity, `${entry.orientationId} velocity`),
    uncertainty: finite(entry.uncertainty, `${entry.orientationId} uncertainty`),
  }));
  const records = patches.map((patch) => {
    const normalCartesian = unit(patch.outwardNormalCartesian, `${patch.patchId} outward normal`);
    const normalIntrinsic = cartesianNormalToIntrinsic(normalCartesian, orientationBasisCartesian);
    if (!normalIntrinsic) return { patchId: patch.patchId, supported: false,
      reason: "patch normal is unresolved in the specimen orientation frame" };
    const estimate = orientedEnergyKernelEstimate(mapped, normalIntrinsic, maximumAngleRadians);
    if (!estimate.supported) return { patchId: patch.patchId, supported: false, reason: estimate.reason,
      normalCartesian, normalIntrinsic };
    const attachmentVelocity = positive(estimate.interfacialFreeEnergy, `${patch.patchId} attachment velocity`);
    const attachmentUncertainty = finite(estimate.uncertainty, `${patch.patchId} attachment uncertainty`);
    const flux = positive(patch.netIncorporationFlux, `${patch.patchId} flux`);
    const fluxUncertainty = finite(patch.uncertainty, `${patch.patchId} flux uncertainty`);
    if (fluxUncertainty < 0 || attachmentUncertainty < 0) throw new RangeError("uncertainties must be nonnegative");
    const supplyVelocity = flux / density;
    const supplyUncertainty = fluxUncertainty / density;
    const ratio = supplyVelocity / attachmentVelocity;
    const supplyUpper = supplyVelocity + 3 * supplyUncertainty;
    const supplyLower = Math.max(0, supplyVelocity - 3 * supplyUncertainty);
    const attachmentUpper = attachmentVelocity + 3 * attachmentUncertainty;
    const attachmentLower = Math.max(0, attachmentVelocity - 3 * attachmentUncertainty);
    const regime = supplyUpper < attachmentLower ? "supply-limited"
      : attachmentUpper < supplyLower ? "attachment-limited" : "uncertainty-overlap";
    return {
      patchId: patch.patchId, supported: true, normalCartesian, normalIntrinsic,
      netIncorporationFluxAtomsPerSquareMetreSecond: flux,
      fluxUncertaintyAtomsPerSquareMetreSecond: fluxUncertainty,
      supplyEquivalentVelocityMetrePerSecond: supplyVelocity,
      supplyVelocityUncertaintyMetrePerSecond: supplyUncertainty,
      attachmentVelocityMetrePerSecond: attachmentVelocity,
      attachmentVelocityUncertaintyMetrePerSecond: attachmentUncertainty,
      supplyToAttachmentRatio: ratio, log10SupplyToAttachmentRatio: Math.log10(Math.max(EPS, ratio)),
      slowerVelocityScaleMetrePerSecond: Math.min(supplyVelocity, attachmentVelocity),
      regime, classificationUsesNonoverlappingThreeSigmaIntervals: regime !== "uncertainty-overlap",
      contributingOrientationIds: estimate.contributingOrientationIds,
    };
  });
  const supported = records.filter((entry) => entry.supported);
  const counts = Object.fromEntries(["supply-limited", "attachment-limited", "uncertainty-overlap"]
    .map((regime) => [regime, supported.filter((entry) => entry.regime === regime).length]));
  return {
    couplingStateSha256: fluxState, siteNumberDensityAtomsPerCubicMetre: density,
    maximumAngleRadians, patchCount: records.length, supportedPatchCount: supported.length,
    abstainedPatchCount: records.length - supported.length, regimeCounts: counts, records,
    rateControlResolved: supported.some((entry) => entry.classificationUsesNonoverlappingThreeSigmaIntervals),
    candidateRankingChanged: false, candidateSetChanged: false, candidateGeometryChanged: false,
    effectiveGrowthVelocityInferred: false, resistancesInSeriesAssumed: false,
    diffusionCoefficientInferred: false, attachmentProbabilityInferred: false,
    physicalTimeIntegrated: false, targetUsed: false,
    claimBoundary: "J/rho is a supply-equivalent velocity scale and v is an independently supplied steady attachment velocity. Their ratio diagnoses a possible bottleneck only where the two external solves share one explicit driving-state digest. No series-resistance law, effective growth rate, concentration field, diffusivity, or physical clock is inferred.",
  };
}

export function syntheticGrowthRegimePreview(preset = "mixed", patchCount = 14) {
  const records = Array.from({ length: patchCount }, (_, index) => {
    const phase = 2 * Math.PI * index / patchCount;
    const logRatio = preset === "supply" ? -1.15 + .25 * Math.sin(phase)
      : preset === "attachment" ? 1.15 + .25 * Math.cos(phase)
        : 1.15 * Math.sin(phase);
    const ratio = 10 ** logRatio;
    return { patchId: `preview-${index + 1}`, supported: true, supplyToAttachmentRatio: ratio,
      log10SupplyToAttachmentRatio: logRatio,
      regime: logRatio < -.28 ? "supply-limited" : logRatio > .28 ? "attachment-limited" : "uncertainty-overlap",
      classificationUsesNonoverlappingThreeSigmaIntervals: Math.abs(logRatio) > .28 };
  });
  return { records, patchCount, supportedPatchCount: patchCount, abstainedPatchCount: 0,
    regimeCounts: Object.fromEntries(["supply-limited", "attachment-limited", "uncertainty-overlap"]
      .map((regime) => [regime, records.filter((entry) => entry.regime === regime).length])),
    synthetic: true, targetUsed: false };
}
