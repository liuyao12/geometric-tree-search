const ENVIRONMENTS = {
  box: {
    id: "box",
    label: "Bulk observation window",
    shortLabel: "finite bulk box",
    shape: "orthorhombic box",
    parameters: { halfExtents: [8.35, 8.35, 8.35] },
    note: "A finite public bulk window. Its faces are search boundaries, not inferred crystal surfaces or periodic images.",
  },
  sphere: {
    id: "sphere",
    label: "Finite nucleus",
    shortLabel: "spherical nucleus",
    shape: "sphere",
    parameters: { radius: 8.8 },
    note: "A target-independent spherical nucleus boundary; no surface tension or radial potential is implied.",
  },
  cylinder: {
    id: "cylinder",
    label: "Nanowire / cylindrical pore",
    shortLabel: "cylindrical domain",
    shape: "x-axis cylinder",
    parameters: { halfLength: 8.35, radius: 7.8 },
    note: "A finite cylindrical public domain. The wall is hard geometry, not an atomistic pore potential.",
  },
  slab: {
    id: "slab",
    label: "Free-standing thin film",
    shortLabel: "finite slab",
    shape: "orthorhombic slab",
    parameters: { halfExtents: [8.35, 8.35, 3.2] },
    note: "Two explicit vacuum-facing limits create a finite slab; in-plane periodicity and surface energies are not assumed.",
  },
  substrate: {
    id: "substrate",
    label: "Film on an impenetrable support",
    shortLabel: "supported half-space",
    shape: "bounded half-space above a plane",
    parameters: { lateralHalfExtents: [8.35, 8.35], lowerZ: -3.2, upperZ: 8.35 },
    note: "The lower plane is an excluded support. An optional separately declared 2D registry may rank the interface, but no substrate atoms, chemistry, adhesion, or interface energy are invented.",
  },
  hourglass: {
    id: "hourglass",
    label: "Constricted pore / growth neck",
    shortLabel: "hourglass domain",
    shape: "x-axis hourglass",
    parameters: { halfLength: 8.35, throatRadius: 2.25, radialSlope: .58 },
    note: "A hard constricted public domain for testing frontier passage; it is not a pressure field or wall interaction.",
  },
};

export const GROWTH_ENVIRONMENT_IDS = Object.freeze(Object.keys(ENVIRONMENTS));

export function growthEnvironmentSpec(id) {
  const spec = ENVIRONMENTS[id];
  if (!spec) throw new Error(`Unknown growth environment: ${id}`);
  return spec;
}

export function growthEnvironmentContains(id, point) {
  const { shape, parameters } = growthEnvironmentSpec(id);
  const x = Number(point?.x ?? point?.[0]);
  const y = Number(point?.y ?? point?.[1]);
  const z = Number(point?.z ?? point?.[2]);
  if (![x, y, z].every(Number.isFinite)) throw new Error("Growth-domain point must contain three finite coordinates");
  if (shape === "orthorhombic box" || shape === "orthorhombic slab") {
    return Math.abs(x) <= parameters.halfExtents[0]
      && Math.abs(y) <= parameters.halfExtents[1]
      && Math.abs(z) <= parameters.halfExtents[2];
  }
  if (shape === "sphere") return Math.hypot(x, y, z) <= parameters.radius;
  if (shape === "x-axis cylinder") {
    return Math.abs(x) <= parameters.halfLength && Math.hypot(y, z) <= parameters.radius;
  }
  if (shape === "bounded half-space above a plane") {
    return Math.abs(x) <= parameters.lateralHalfExtents[0]
      && Math.abs(y) <= parameters.lateralHalfExtents[1]
      && z >= parameters.lowerZ && z <= parameters.upperZ;
  }
  if (shape === "x-axis hourglass") {
    return Math.abs(x) <= parameters.halfLength
      && Math.hypot(y, z) <= parameters.throatRadius + parameters.radialSlope * Math.abs(x);
  }
  throw new Error(`Unsupported growth-domain shape: ${shape}`);
}

export function growthEnvironmentSignedMargin(id, point) {
  const { shape, parameters } = growthEnvironmentSpec(id);
  const x = Number(point?.x ?? point?.[0]);
  const y = Number(point?.y ?? point?.[1]);
  const z = Number(point?.z ?? point?.[2]);
  if (![x, y, z].every(Number.isFinite)) throw new Error("Growth-domain point must contain three finite coordinates");
  if (shape === "orthorhombic box" || shape === "orthorhombic slab") {
    return Math.min(parameters.halfExtents[0] - Math.abs(x),
      parameters.halfExtents[1] - Math.abs(y), parameters.halfExtents[2] - Math.abs(z));
  }
  if (shape === "sphere") return parameters.radius - Math.hypot(x, y, z);
  if (shape === "x-axis cylinder") {
    return Math.min(parameters.halfLength - Math.abs(x), parameters.radius - Math.hypot(y, z));
  }
  if (shape === "bounded half-space above a plane") {
    return Math.min(parameters.lateralHalfExtents[0] - Math.abs(x),
      parameters.lateralHalfExtents[1] - Math.abs(y), z - parameters.lowerZ, parameters.upperZ - z);
  }
  if (shape === "x-axis hourglass") {
    return Math.min(parameters.halfLength - Math.abs(x),
      parameters.throatRadius + parameters.radialSlope * Math.abs(x) - Math.hypot(y, z));
  }
  throw new Error(`Unsupported growth-domain shape: ${shape}`);
}

export function growthEnvironmentAudit(id) {
  const spec = growthEnvironmentSpec(id);
  return {
    id: spec.id,
    label: spec.label,
    shape: spec.shape,
    parametersSceneUnits: JSON.parse(JSON.stringify(spec.parameters)),
    admissionRole: "hard target-independent public-boundary gate",
    affectsCandidateGeometry: false,
    affectsCandidateAdmission: true,
    physicalPotentialUsed: false,
    pressureFieldModeled: false,
    surfaceEnergyModeled: false,
    substrateAtomsPresent: false,
    epitaxialRegistryModeled: false,
    periodicImagesImplied: false,
  };
}
