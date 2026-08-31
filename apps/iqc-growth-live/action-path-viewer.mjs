const finite = (value) => Number.isFinite(Number(value));

function vector(value, label) {
  if (!Array.isArray(value) || value.length !== 3 || !value.every(finite)) {
    throw new TypeError(`${label} must be a finite Cartesian three-vector`);
  }
  return value.map(Number);
}

function squaredDistance(first, second) {
  return first.reduce((sum, value, axis) => sum + (value - second[axis]) ** 2, 0);
}

function normalizedSite(site, domain, fixed) {
  return { pathSiteId: String(site.pathSiteId), species: String(site.species), domain, fixed,
    positionAngstrom: vector(site.positionAngstrom, `path site ${site.pathSiteId}`) };
}

export function buildActionPathViewerFrame(path, imageIndex, { maximumFixedSites = 180 } = {}) {
  if (!path || !Array.isArray(path.images) || !path.images.length) {
    throw new TypeError("a path viewer frame needs validated coordinate-bearing images");
  }
  if (!Number.isInteger(imageIndex) || imageIndex < 0 || imageIndex >= path.images.length) {
    throw new RangeError("path image index is outside the validated image chain");
  }
  if (!Number.isInteger(maximumFixedSites) || maximumFixedSites < 0) {
    throw new RangeError("maximumFixedSites must be a nonnegative integer");
  }
  const image = path.images[imageIndex];
  const dynamicSites = image.sites.map((site) => normalizedSite(site, site.domain, false));
  const focusSites = dynamicSites.filter((site) => site.domain !== "reservoir");
  const focus = focusSites.length ? focusSites : dynamicSites;
  const center = focus.reduce((sum, site) => sum.map((value, axis) =>
    value + site.positionAngstrom[axis]), [0, 0, 0]).map((value) => value / focus.length);
  const fixedSites = (path.fixedMaterialSites || []).map((site) =>
    normalizedSite(site, "material", true));
  const allMaterialFacingPositions = path.images.flatMap((entry) => entry.sites
    .filter((site) => site.domain !== "reservoir").map((site) =>
      vector(site.positionAngstrom, `path site ${site.pathSiteId}`)));
  const allDynamicPositions = allMaterialFacingPositions.length ? allMaterialFacingPositions
    : path.images.flatMap((entry) => entry.sites.map((site) =>
      vector(site.positionAngstrom, `path site ${site.pathSiteId}`)));
  const rankedFixed = fixedSites.map((site) => ({ site,
    distanceSquared: allDynamicPositions.length ? Math.min(...allDynamicPositions.map((position) =>
      squaredDistance(site.positionAngstrom, position)))
      : squaredDistance(site.positionAngstrom, center) }))
    .sort((first, second) => first.distanceSquared - second.distanceSquared
      || first.site.pathSiteId.localeCompare(second.site.pathSiteId));
  const displayedFixedSites = rankedFixed.slice(0, maximumFixedSites).map((entry) => entry.site);
  const sites = [...displayedFixedSites, ...dynamicSites];
  const maximumRadius = Math.max(1e-6, ...sites.map((site) =>
    Math.sqrt(squaredDistance(site.positionAngstrom, center))));
  const trails = dynamicSites.map((site) => {
    const positions = path.images.map((entry) => entry.sites.find((candidate) =>
      candidate.pathSiteId === site.pathSiteId)?.positionAngstrom).filter(Boolean).map((position) =>
      vector(position, `path trail ${site.pathSiteId}`));
    return { pathSiteId: site.pathSiteId, species: site.species, positions };
  });
  return { schema: "gcts-action-path-viewer-frame-v1", imageIndex,
    imageCount: path.images.length, reactionCoordinate: Number(image.reactionCoordinate),
    energyElectronVolt: Number(image.energyElectronVolt),
    relativeEnergyElectronVolt: Number(image.energyElectronVolt)
      - Number(path.images[0].energyElectronVolt),
    maximumForceElectronVoltPerAngstrom: Number(image.maximumForceElectronVoltPerAngstrom),
    saddle: imageIndex === path.saddleImageIndex, center, maximumRadius, sites, trails,
    fixedMaterialSiteCount: fixedSites.length,
    displayedFixedMaterialSiteCount: displayedFixedSites.length,
    movingOrReservoirSiteCount: dynamicSites.length,
    materialSiteCount: fixedSites.length + dynamicSites.filter((site) =>
      site.domain === "material").length,
    interfaceSiteCount: dynamicSites.filter((site) => site.domain === "interface").length,
    reservoirSiteCount: dynamicSites.filter((site) => site.domain === "reservoir").length,
    exactReturnedImage: true, interpolationUsed: false, targetUsed: false };
}

export function projectActionPathViewerFrame(frame, { width, height, yaw = .65,
  pitch = -.35, padding = 18 } = {}) {
  if (!(finite(width) && Number(width) > 0 && finite(height) && Number(height) > 0)) {
    throw new TypeError("path projection needs positive finite width and height");
  }
  const cy = Math.cos(yaw); const sy = Math.sin(yaw);
  const cp = Math.cos(pitch); const sp = Math.sin(pitch);
  const rotate = (position) => {
    const x = position[0] - frame.center[0];
    const y = position[1] - frame.center[1];
    const z = position[2] - frame.center[2];
    const firstX = cy * x + sy * z;
    const firstZ = -sy * x + cy * z;
    return [firstX, cp * y - sp * firstZ, sp * y + cp * firstZ];
  };
  const scale = Math.max(1e-9, Math.min((Number(width) - padding * 2),
    (Number(height) - padding * 2)) / (frame.maximumRadius * 2.15));
  const project = (position) => {
    const rotated = rotate(position);
    const perspective = 1 / Math.max(.64, 1 + rotated[2] / (frame.maximumRadius * 8));
    return { x: Number(width) / 2 + rotated[0] * scale * perspective,
      y: Number(height) / 2 - rotated[1] * scale * perspective,
      depth: rotated[2], perspective };
  };
  return { ...frame, width: Number(width), height: Number(height), yaw, pitch,
    projectedSites: frame.sites.map((site) => ({ ...site, ...project(site.positionAngstrom) }))
      .sort((first, second) => first.depth - second.depth
        || first.pathSiteId.localeCompare(second.pathSiteId)),
    projectedTrails: frame.trails.map((trail) => ({ ...trail,
      points: trail.positions.map(project) })), projectionKind: "proper-rotation-perspective",
    interpolationUsed: false };
}
