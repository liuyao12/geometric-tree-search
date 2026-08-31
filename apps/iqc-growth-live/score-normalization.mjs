const spec = (sourceQuantity, sourceUnit, referenceScale, transform, outputDomain) => Object.freeze({
  sourceQuantity, sourceUnit, referenceScale, transform, outputDomain,
  outputUnit: "dimensionless score coordinate",
});

export const SCORE_NORMALIZATION_SPECS = Object.freeze({
  "grammar-priority": spec("frozen rule recurrence, marking, and hierarchy support", "counts + dimensionless marking coefficients", "rule-local training support", "combine only frozen grammar fields already attached to the exact action", "implementation-defined finite scalar"),
  "known-window-gain": spec("new exact species-position matches", "sites", "one matched reference site", "count previously missing supplied sites recovered by this action", "nonnegative integer; forced to zero after reconstruction"),
  "geometric-strain": spec("colored contact and angle residuals", "Å + radians", "sample-learned colored envelope widths", "divide each residual by its learned envelope scale, aggregate contact and angle terms", "nonnegative mismatch"),
  "external-calibration": spec("frozen cross-archive geometry features", "source geometry units before standardization", "source-only means, scales, and support bounds", "standardize with the frozen source artifact; abstain outside source support", "bounded transferred score or zero on abstention"),
  composition: spec("species-fraction deviation before and after attachment", "fraction", "observed composition vector", "evaluate the change in finite-configuration composition distance", "signed fraction-distance change"),
  "solute-partition": spec("emitted solute fraction × declared spatial field", "fraction × dimensionless field", "max(0.15, sqrt(f(1-f))) from observed composition", "tanh-normalize enrichment contrast, then multiply by the declared spatial score", "[-1, 1]"),
  "formal-charge": spec("net supplied formal-charge imbalance before and after attachment", "supplied charge labels", "site count and observed mean formal charge", "compare projected mean/net formal-charge deviation with the supplied reference", "signed charge-balance change"),
  "charge-geometry": spec("opposite-charge contacts and local vector imbalance", "supplied charge labels + Å", "selected reach in d_nn", "normalize distances by d_nn and average bounded pair/field-neutrality descriptors", "[-1, 1]"),
  "charge-moment": spec("finite-crop charge dipole and quadrupole", "supplied charge × Å and × Å²", "configuration radius and total absolute supplied charge", "center and normalize multipole magnitudes before comparing the candidate-added state", "bounded shape-improvement score"),
  "ionic-pair": spec("incremental q_i q_j / r pair geometry", "supplied charge² / Å", "d_nn and selected finite reach", "replace r by r/d_nn, average finite current-added and added-added pairs", "dimensionless Madelung-like increment"),
  "bond-valence": spec("exp((R0-r)/B) scalar and vector sums", "Å parameters and distances", "IUCr R0/B pair parameters + supplied valence labels", "form sample-relative scalar-sum and spherical vector-balance residuals", "bounded satisfaction score"),
  surface: spec("ordered coordination deficit on new and healed existing sites", "missing-neighbor fraction", "sample-learned ordered coordination bounds", "0.60 × new-site mean deficit − 0.40 × healed-existing deficit", "signed deficit change"),
  "bulk-surface": spec("fresh-site support gain + interface integrity", "sites + dimensionless deficit", "largest observed cluster action and [-1,1] interface clamp", "weighted sum of capped action size and healed-minus-new deficit", "[-1, 1]"),
  attachment: spec("contact count and six parent-local lateral support sectors", "counts", "1.45 d_nn neighborhood", "map terrace/step/kink topology to the selected bounded hypothesis score", "[-1, 1]"),
  habit: spec("parent-local attachment direction frequency", "training witness counts", "12 proper-frame spherical bins", "normalize fit-only recurring-rule bin support; held-out counts do not fit the atlas", "bounded directional-support score"),
  defect: spec("exposed coordination, local strain, composition drift, seam burden", "dimensionless descriptors", "fixed 0.35/0.30/0.15/0.20 mixture", "combine four separately bounded precursor channels", "[0, 1] burden"),
  coherency: spec("accepted-history local mismatch marks", "dimensionless mismatch", "cluster-graph hop distance", "average R-hop marks with 1/(1+hop) decay", "bounded inherited mismatch"),
  "collective-response": spec("accepted mismatch marks over the connected cluster graph", "dimensionless mismatch + graph hops", "declared screening length xi in graph hops", "propagate marks with exp(-hop/xi), then compare the candidate-local mismatch and orientation with the screened field", "[-1, 1]"),
  "configurational-multiplicity": spec("fit-supported symmetry-distinct outgoing connection rules", "training witness counts", "maximum effective continuation count across frozen parent types", "compute Shannon effective action count exp(H), normalize across the frozen grammar, then apply the declared diversity/funnel/balanced hypothesis", "[-1, 1]"),
  "constraint-tensor": spec("unit contact-direction outer products around emitted sites", "dimensionless direction cosines", "1.45 d_nn contact reach and unit tensor trace", "eigendecompose the normalized 3x3 direction tensor and score its 3D, lamellar, or axial dimensionality", "[-1, 1]"),
  front: spec("angular support occupancy and backing-depth spread", "sector counts + Å", "eight sectors and 2.4 d_nn reach", "normalize sector occupancy and depth spread, then apply selected morphology hypothesis", "[-1, 1]"),
  "wulff-shape": spec("finite-nucleus support mismatch against validated oriented interfacial energies", "Å support + supplied gamma units before reduction", "least-squares translated support and one positive scale fitted to the occupied pre-candidate nucleus", "compare mean squared normalized support residual before and after the unchanged candidate; tanh-bound the improvement and abstain outside declared oriented angular coverage", "[-1, 1]"),
  "kinetic-habit": spec("validated steady normal growth velocity at one declared driving condition", "metre per second before reduction", "geometric mean over the validated oriented velocity set", "compact oriented angular interpolation, log velocity contrast, then tanh; abstain outside declared angular coverage", "[-1, 1]"),
  "interface-flux": spec("validated spatially resolved net incorporation flux over one frozen interface", "atoms per square metre per second before reduction", "geometric mean over the validated interface quadrature", "compact spatial and outward-normal interpolation, log flux contrast, then tanh; abstain outside declared local coverage", "[-1, 1]"),
  capillary: spec("occupied/open local solid angle", "direction counts", "32 equal-area directions, 38° caps, 2.2 d_nn reach", "convert screened direction fractions to pocket/exposed preference", "[-1, 1]"),
  epitaxy: spec("fresh-site distance to declared 2D template nodes", "Å", "template spacing and 3.5 d_nn height reach", "normalize nearest registry residual and apply height-decaying support", "bounded registry score"),
  drive: spec("parent-to-child direction alignment", "cosine", "declared external axis", "dot normalized displacement with the declared direction", "[-1, 1]"),
  thermal: spec("position in a declared scalar field", "Å before reduction", "seed-centroid plane or 4 d_nn sphere with 2 d_nn transition", "map signed distance to a reduced hot/cold/front coordinate", "[-1, 1]"),
  robustness: spec("minimum contact, overlap, and public-boundary margin", "Å", "effective metric tolerance epsilon", "divide the minimum margin by epsilon and apply tanh(x/2)", "[-1, 1]"),
  microstructure: spec("frozen gap, pose-interface, coordination, or occupancy role", "categorical / bounded role score", "input-derived role vocabulary", "map the selected role contrast to one bounded candidate-local scalar", "[-1, 1]"),
  loop: spec("independent parent paths agreeing on a full colored child pose", "witness counts", "number of already placed independent parents", "normalize compatible multi-parent consensus without changing exact overlap checks", "bounded compatibility score"),
  arrival: spec("minimum swept clearance along finite approach routes", "Å", "2 d_nn path length and hard-exclusion radii", "sample nine points per route, normalize minimum clearance by d_nn", "bounded accessibility score"),
  exposure: spec("unblocked source-ray samples for emitted sites", "visible sample fraction", "six samples over 3 d_nn per declared source direction", "average hard-clearance line-of-sight indicators", "[0, 1] visibility"),
  "action-barrier": spec("validated candidate-resolved transition barrier", "electronvolt per complete frozen action", "median and robust scale within the exact candidate batch", "tanh((median(E)-E)/(2*max(1.4826 MAD, range/4)))", "[-1, 1]; lower barrier is positive"),
  exploration: spec("deterministic candidate-keyed Gumbel offset", "dimensionless seeded variate", "declared T* and integer path seed", "multiply the frozen variate by T*; geometry and hard gates remain unchanged", "unbounded branch-order offset"),
});

export const SCORE_NORMALIZATION_ALIASES = Object.freeze({
  elastic: "geometric-strain",
  "affine-load": "geometric-strain",
  charge: "formal-charge",
  "bulk-surface-driving": "bulk-surface",
  "attachment-topology": "attachment",
  "habit-anisotropy": "habit",
  "defect-precursors": "defect",
  "coherency-memory": "coherency",
  "front-morphology": "front",
  "capillary-geometry": "capillary",
  "thermal-field": "thermal",
  "loop-closure": "loop",
  "arrival-path": "arrival",
  "feed-exposure": "exposure",
});

export const SCORE_PHYSICS_MANIFEST_IDS = Object.freeze({
  "grammar-priority": "connection",
  "known-window-gain": "score-ledger",
  "geometric-strain": "local",
  "external-calibration": "geometry-calculation-calibration",
  composition: "chemistry",
  "solute-partition": "solute-partition",
  "formal-charge": "chemistry",
  "charge-geometry": "charge-geometry",
  "charge-moment": "charge-moment",
  "ionic-pair": "ionic-pair",
  "bond-valence": "bond-valence",
  surface: "surface",
  "bulk-surface": "bulk-surface-driving",
  attachment: "attachment-topology",
  habit: "habit-anisotropy",
  defect: "defect-precursors",
  coherency: "coherency-memory",
  "collective-response": "long-range",
  "configurational-multiplicity": "configurational-entropy",
  "constraint-tensor": "constraint-rigidity",
  front: "front-morphology",
  "wulff-shape": "interfacial-free-energy",
  "kinetic-habit": "orientation-attachment-kinetics",
  "interface-flux": "spatial-interface-flux",
  capillary: "capillary-geometry",
  epitaxy: "epitaxy",
  drive: "drive",
  thermal: "thermal-field",
  robustness: "robustness",
  microstructure: "microstructure",
  loop: "loop-closure",
  arrival: "kinetics",
  exposure: "feed-exposure",
  "action-barrier": "action-barrier-ranking",
  exploration: "path-ensemble",
});

const auditCache = new Map();

export function scoreNormalizationAudit(id, context = {}) {
  const canonicalId = SCORE_NORMALIZATION_ALIASES[id] || id;
  const definition = SCORE_NORMALIZATION_SPECS[canonicalId];
  if (!definition) throw new Error(`missing score normalization specification for ${id}`);
  const nearestNeighborAngstrom = Number.isFinite(context.nearestNeighborAngstrom)
    ? context.nearestNeighborAngstrom : null;
  const metricToleranceAngstrom = Number.isFinite(context.metricToleranceAngstrom)
    ? context.metricToleranceAngstrom : null;
  const cacheKey = `${id}|${nearestNeighborAngstrom ?? "null"}|${metricToleranceAngstrom ?? "null"}`;
  if (auditCache.has(cacheKey)) return auditCache.get(cacheKey);
  const audit = Object.freeze({
    id,
    canonicalId,
    physicsManifestId: SCORE_PHYSICS_MANIFEST_IDS[canonicalId],
    ...definition,
    resolvedScales: Object.freeze({ nearestNeighborAngstrom, metricToleranceAngstrom }),
    declaredWeightUnit: "dimensionless multiplier",
    candidateGeometryChanged: false,
    hardAdmissionChanged: false,
    physicalTimeModeled: false,
  });
  auditCache.set(cacheKey, audit);
  return audit;
}
