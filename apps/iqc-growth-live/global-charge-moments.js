function finiteSite(site) {
  return Array.isArray(site?.position) && site.position.length === 3
    && site.position.every(Number.isFinite) && Number.isFinite(site.charge);
}

export function chargeMomentSignature(inputSites = []) {
  const sites = inputSites.filter(finiteSite);
  if (!sites.length) return { available: false, siteCount: 0, absoluteCharge: 0,
    radiusRms: 0, dipoleMagnitude: 0, quadrupoleMagnitude: 0 };
  const centroid = [0, 1, 2].map((axis) => sites.reduce((sum, site) => sum + site.position[axis], 0) / sites.length);
  const centered = sites.map((site) => ({ charge: site.charge,
    r: site.position.map((value, axis) => value - centroid[axis]) }));
  const absoluteCharge = centered.reduce((sum, site) => sum + Math.abs(site.charge), 0);
  const radiusSquared = centered.reduce((sum, site) => sum
    + site.r.reduce((total, value) => total + value * value, 0), 0) / sites.length;
  const radiusRms = Math.sqrt(Math.max(0, radiusSquared));
  if (!(absoluteCharge > 0) || !(radiusRms > 1e-12)) return { available: false,
    siteCount: sites.length, absoluteCharge, radiusRms, centroid,
    dipoleMagnitude: 0, quadrupoleMagnitude: 0 };
  const dipole = [0, 0, 0];
  const quadrupole = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  centered.forEach(({ charge, r }) => {
    const r2 = r.reduce((sum, value) => sum + value * value, 0);
    for (let row = 0; row < 3; row++) {
      dipole[row] += charge * r[row];
      for (let column = 0; column < 3; column++) {
        quadrupole[row][column] += charge * (3 * r[row] * r[column] - (row === column ? r2 : 0));
      }
    }
  });
  const dipoleMagnitude = Math.hypot(...dipole) / (absoluteCharge * radiusRms);
  const quadrupoleMagnitude = Math.sqrt(quadrupole.flat()
    .reduce((sum, value) => sum + value * value, 0)) / (absoluteCharge * radiusRms * radiusRms);
  return { available: true, siteCount: sites.length, absoluteCharge, radiusRms, centroid,
    netCharge: centered.reduce((sum, site) => sum + site.charge, 0),
    dipoleMagnitude, quadrupoleMagnitude };
}

export function compareChargeMomentGeometry(currentSites = [], addedSites = [], mode = "none") {
  const before = chargeMomentSignature(currentSites);
  const after = chargeMomentSignature([...currentSites, ...addedSites]);
  const available = before.available && after.available && addedSites.length > 0;
  const dipoleImprovement = available ? before.dipoleMagnitude - after.dipoleMagnitude : 0;
  const quadrupoleImprovement = available ? before.quadrupoleMagnitude - after.quadrupoleMagnitude : 0;
  const dipoleScore = Math.tanh(8 * dipoleImprovement);
  const quadrupoleScore = Math.tanh(8 * quadrupoleImprovement);
  const score = mode === "dipole" ? dipoleScore : mode === "quadrupole" ? quadrupoleScore
    : mode === "combined" ? .5 * (dipoleScore + quadrupoleScore) : 0;
  return { available, mode, score, before, after, dipoleImprovement, quadrupoleImprovement,
    dipoleScore, quadrupoleScore, addedSites: addedSites.length,
    translationInvariant: true, properRotationInvariant: true, uniformScaleInvariant: true,
    candidateGeometryChanged: false, hardAdmissionChanged: false, targetUsed: false,
    electrostaticEnergyInferred: false, electrostaticPotentialSolved: false,
    dielectricResponseInferred: false, electronicStructureModeled: false, physicalTimeIntegrated: false };
}
