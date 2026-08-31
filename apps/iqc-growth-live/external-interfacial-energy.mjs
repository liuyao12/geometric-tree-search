export const INTERFACIAL_ENERGY_REQUEST_SCHEMA = "gcts-interfacial-free-energy-request-v1";
export const INTERFACIAL_ENERGY_RESPONSE_SCHEMA = "gcts-interfacial-free-energy-response-v1";

const EPS = 1e-9;

function requiredText(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function finite(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new TypeError(`${label} must be finite`);
  return number;
}

function positive(value, label) {
  const number = finite(value, label);
  if (!(number > 0)) throw new RangeError(`${label} must be positive`);
  return number;
}

function sha256Text(value, label) {
  const text = requiredText(value, label);
  if (!/^[0-9a-f]{64}$/i.test(text)) throw new TypeError(`${label} must be a SHA-256 digest`);
  return text.toLowerCase();
}

function vector(value, dimension, label) {
  if (!Array.isArray(value) || value.length !== dimension) {
    throw new TypeError(`${label} must have ${dimension} Cartesian components`);
  }
  const result = value.map((entry, index) => finite(entry, `${label}[${index}]`));
  const norm = Math.hypot(...result);
  if (!(norm > EPS)) throw new RangeError(`${label} must be nonzero`);
  return result.map((entry) => entry / norm);
}

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort()
    .map((key) => [key, canonicalValue(value[key])]));
  return value;
}

export function canonicalInterfacialEnergyJson(value) {
  return JSON.stringify(canonicalValue(value));
}

export async function interfacialEnergySha256(value) {
  const bytes = new TextEncoder().encode(typeof value === "string"
    ? value : canonicalInterfacialEnergyJson(value));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function buildInterfacialEnergyRequest(input) {
  if (input?.targetUsed === true || input?.targetCoordinatesEmbedded === true) {
    throw new Error("an interfacial-energy request cannot use a growth target");
  }
  const dimension = Number(input?.intrinsicDimension);
  if (![2, 3].includes(dimension)) throw new RangeError("intrinsicDimension must be 2 or 3");
  const structureSha256 = sha256Text(input.structureSha256, "structure SHA-256");
  const suppliedBasis = input.orientationBasisCartesian || (dimension === 3
    ? [[1, 0, 0], [0, 1, 0], [0, 0, 1]] : null);
  if (!Array.isArray(suppliedBasis) || suppliedBasis.length !== dimension) {
    throw new Error(`a ${dimension}-vector orthonormal Cartesian orientation basis is required`);
  }
  const orientationBasisCartesian = suppliedBasis.map((entry, index) =>
    vector(entry, 3, `orientation basis vector ${index + 1}`));
  for (let first = 0; first < dimension; first += 1) {
    for (let second = first + 1; second < dimension; second += 1) {
      if (Math.abs(dot(orientationBasisCartesian[first], orientationBasisCartesian[second])) > 1e-7) {
        throw new Error("orientation basis vectors must be mutually orthogonal");
      }
    }
  }
  return {
    schema: INTERFACIAL_ENERGY_REQUEST_SCHEMA,
    generatedAt: String(input.generatedAt),
    application: { name: "Materials Growth Lab", buildId: String(input.buildId) },
    specimen: {
      scenarioId: String(input.scenarioId),
      materialName: requiredText(input.materialName, "material name"),
      elements: [...new Set((input.elements || []).map(String))].sort(),
      structureSha256,
      intrinsicDimension: dimension,
      orientationBasisCartesian,
      orientationCoordinates: "normal components multiply the ordered Cartesian basis vectors",
      sourceProvenance: input.sourceProvenance || null,
      recordedConditions: input.recordedConditions || null,
    },
    calculation: {
      quantity: dimension === 3
        ? "orientation-resolved solid/environment interfacial free energy"
        : "orientation-resolved edge free energy for a two-dimensional solid",
      requiredOrientationConvention: "oriented unit normal in the supplied Cartesian specimen frame",
      suitableMethods: ["cleavage or slab free-energy calculation", "capillary fluctuation method",
        "orientation-resolved interface calculation or measurement"],
      requiredOutputs: ["one finite positive free energy and one-sigma uncertainty per oriented normal",
        "adjacent phase or substrate", "temperature and ensemble when relevant",
        "method, version, complete settings digest, convergence and validation declarations"],
      units: dimension === 3 ? "joule per square metre" : "joule per metre",
      responseSchema: INTERFACIAL_ENERGY_RESPONSE_SCHEMA,
    },
    expectedResponse: {
      schema: INTERFACIAL_ENERGY_RESPONSE_SCHEMA,
      requestSha256: "SHA-256 of this complete request file",
      structureSha256,
      intrinsicDimension: dimension,
      orientationBasisCartesian,
      interface: { adjacentPhase: "required", temperatureKelvin: "positive when applicable" },
      method: { family: "required", program: "required", version: "declared or null",
        settingsSha256: "64 hexadecimal characters" },
      orientations: [{ orientationId: "unique", normal: `array[${dimension}]`,
        interfacialFreeEnergy: "finite positive", uncertainty: "finite nonnegative" }],
    },
    safeguards: {
      requestOnly: true,
      targetCoordinatesEmbedded: false,
      targetUsedForSelection: false,
      morphologyUsedToInferInterfacialEnergy: false,
      geometricUndercoordinationUsedAsInterfacialEnergy: false,
      orientedNormalsNotSilentlyInversionSymmetrized: true,
      millerIndicesRequired: false,
      responseMayOnlyBuildConditionalNormalizedWulffGeometry: true,
      responseMayNotChangeGrowthRankingWithoutSeparateExplicitValidation: true,
    },
  };
}

function solveLinear(matrix, values) {
  const n = values.length;
  const augmented = matrix.map((row, index) => [...row, values[index]]);
  for (let column = 0; column < n; column += 1) {
    let pivot = column;
    for (let row = column + 1; row < n; row += 1) {
      if (Math.abs(augmented[row][column]) > Math.abs(augmented[pivot][column])) pivot = row;
    }
    if (Math.abs(augmented[pivot][column]) < 1e-11) return null;
    [augmented[column], augmented[pivot]] = [augmented[pivot], augmented[column]];
    const scale = augmented[column][column];
    for (let entry = column; entry <= n; entry += 1) augmented[column][entry] /= scale;
    for (let row = 0; row < n; row += 1) {
      if (row === column) continue;
      const factor = augmented[row][column];
      for (let entry = column; entry <= n; entry += 1) {
        augmented[row][entry] -= factor * augmented[column][entry];
      }
    }
  }
  return augmented.map((row) => row[n]);
}

function combinations(count, choose) {
  const result = [];
  const visit = (start, selected) => {
    if (selected.length === choose) { result.push([...selected]); return; }
    for (let index = start; index <= count - (choose - selected.length); index += 1) {
      selected.push(index); visit(index + 1, selected); selected.pop();
    }
  };
  visit(0, []); return result;
}

function dot(first, second) {
  return first.reduce((sum, value, index) => sum + value * second[index], 0);
}

function squaredDistance(first, second) {
  return first.reduce((sum, value, index) => sum + (value - second[index]) ** 2, 0);
}

function positivelySpans(normals, dimension) {
  const candidates = [];
  normals.forEach((normal) => candidates.push(normal, normal.map((value) => -value)));
  if (dimension === 2) {
    normals.forEach((normal) => candidates.push([-normal[1], normal[0]], [normal[1], -normal[0]]));
  } else {
    combinations(normals.length, 2).forEach(([first, second]) => {
      const ray = cross(normals[first], normals[second]);
      if (Math.hypot(...ray) > EPS) {
        const unit = normalized(ray); candidates.push(unit, unit.map((value) => -value));
      }
    });
  }
  return !candidates.some((direction) => normals.every((normal) => dot(normal, direction) <= 1e-9));
}

function dedupePoints(points, tolerance = 1e-7) {
  const kept = [];
  points.forEach((point) => {
    if (!kept.some((other) => squaredDistance(point, other) <= tolerance ** 2)) kept.push(point);
  });
  return kept;
}

function cross(first, second) {
  return [first[1] * second[2] - first[2] * second[1],
    first[2] * second[0] - first[0] * second[2],
    first[0] * second[1] - first[1] * second[0]];
}

function normalized(value) {
  const norm = Math.hypot(...value);
  return value.map((entry) => entry / norm);
}

function orderFacetVertices(vertices, normal) {
  if (vertices.length <= 2) return vertices;
  const center = vertices[0].map((_, axis) => vertices.reduce((sum, point) => sum + point[axis], 0) / vertices.length);
  const reference = Math.abs(normal[0]) < 0.8 ? [1, 0, 0] : [0, 1, 0];
  const u = normalized(cross(normal, reference));
  const v = cross(normal, u);
  return [...vertices].sort((first, second) => Math.atan2(dot(first.map((x, i) => x - center[i]), v),
    dot(first.map((x, i) => x - center[i]), u)) - Math.atan2(dot(second.map((x, i) => x - center[i]), v),
    dot(second.map((x, i) => x - center[i]), u)));
}

export function buildNormalizedWulffGeometry(orientations, intrinsicDimension) {
  const dimension = Number(intrinsicDimension);
  if (![2, 3].includes(dimension)) throw new RangeError("intrinsicDimension must be 2 or 3");
  if (!Array.isArray(orientations) || orientations.length < dimension + 1) {
    throw new Error(`at least ${dimension + 1} oriented energies are required`);
  }
  const gammaMin = Math.min(...orientations.map((entry) => entry.interfacialFreeEnergy));
  const planes = orientations.map((entry) => ({ ...entry,
    supportDistance: entry.interfacialFreeEnergy / gammaMin }));
  if (!positivelySpans(planes.map((entry) => entry.normal), dimension)) {
    throw new Error("supplied oriented normals do not positively span the specimen frame; the Wulff envelope is unbounded");
  }
  const vertices = dedupePoints(combinations(planes.length, dimension).map((indices) => {
    const point = solveLinear(indices.map((index) => planes[index].normal),
      indices.map((index) => planes[index].supportDistance));
    if (!point || !planes.every((plane) => dot(plane.normal, point) <= plane.supportDistance + 1e-7)) return null;
    return point;
  }).filter(Boolean));
  if (vertices.length < dimension + 1) throw new Error("the supplied energies do not produce a finite full-dimensional Wulff envelope");
  const facets = planes.map((plane, planeIndex) => {
    const facetVertices = vertices.filter((point) =>
      Math.abs(dot(plane.normal, point) - plane.supportDistance) <= 2e-7);
    return { orientationId: plane.orientationId, planeIndex, normal: plane.normal,
      supportDistance: plane.supportDistance,
      vertexIndices: (dimension === 3 ? orderFacetVertices(facetVertices, plane.normal) : facetVertices)
        .map((point) => vertices.indexOf(point)) };
  }).filter((facet) => facet.vertexIndices.length >= dimension);
  const activeIds = new Set(facets.map((facet) => facet.orientationId));
  let orderedVertices = vertices;
  if (dimension === 2) {
    const center = vertices[0].map((_, axis) => vertices.reduce((sum, point) => sum + point[axis], 0) / vertices.length);
    orderedVertices = [...vertices].sort((first, second) => Math.atan2(first[1] - center[1], first[0] - center[0])
      - Math.atan2(second[1] - center[1], second[0] - center[0]));
  }
  return {
    intrinsicDimension: dimension, normalization: "support distances divided by minimum supplied interfacial free energy",
    gammaMinimum: gammaMin, vertices: orderedVertices, facets,
    activeOrientationIds: [...activeIds].sort(),
    inactiveOrientationIds: planes.filter((plane) => !activeIds.has(plane.orientationId))
      .map((plane) => plane.orientationId).sort(),
    orientationCount: planes.length, vertexCount: vertices.length, facetCount: facets.length,
    bounded: true, physicalScaleInferred: false, millerIndicesInferred: false,
    morphologyUsedToInferEnergy: false, targetUsed: false,
    equilibriumShapeConditionalOnSuppliedOrientations: true,
    completeEquilibriumShapeCertified: false,
  };
}

export function validateInterfacialEnergyResponse(response, expected) {
  if (response?.schema !== INTERFACIAL_ENERGY_RESPONSE_SCHEMA) throw new Error("unsupported interfacial-energy response schema");
  const requestSha256 = sha256Text(response.requestSha256, "response request SHA-256");
  const structureSha256 = sha256Text(response.structureSha256, "response structure SHA-256");
  if (requestSha256 !== sha256Text(expected.requestSha256, "expected request SHA-256")) throw new Error("response does not match the exact request");
  if (structureSha256 !== sha256Text(expected.structureSha256, "expected structure SHA-256")) throw new Error("response does not match the exact specimen geometry");
  const dimension = Number(response.intrinsicDimension);
  if (dimension !== Number(expected.intrinsicDimension) || ![2, 3].includes(dimension)) throw new Error("response intrinsic dimension mismatch");
  const method = {
    family: requiredText(response.method?.family, "method family"),
    program: requiredText(response.method?.program, "method program"),
    version: response.method?.version == null ? null : String(response.method.version),
    settingsSha256: sha256Text(response.method?.settingsSha256, "method settings SHA-256"),
  };
  const adjacentPhase = requiredText(response.interface?.adjacentPhase, "adjacent phase or substrate");
  const validation = response.validation || {};
  for (const field of ["passed", "converged", "uncertaintyReported", "orientationSetPredeclared"]) {
    if (validation[field] !== true) throw new Error(`validation.${field} must be true`);
  }
  const expectedUnits = dimension === 3 ? "joule per square metre" : "joule per metre";
  if (response.units !== expectedUnits) throw new Error(`response units must be '${expectedUnits}'`);
  if (!Array.isArray(response.orientations)) throw new TypeError("response orientations must be an array");
  const ids = new Set(); const normals = [];
  const orientations = response.orientations.map((entry, index) => {
    const orientationId = requiredText(entry?.orientationId, `orientation ${index + 1} id`);
    if (ids.has(orientationId)) throw new Error(`duplicate orientation ID ${orientationId}`);
    ids.add(orientationId);
    const normal = vector(entry.normal, dimension, `orientation ${orientationId} normal`);
    if (normals.some((other) => dot(normal, other) > 1 - 1e-8)) throw new Error("duplicate oriented normals are not permitted");
    normals.push(normal);
    const interfacialFreeEnergy = positive(entry.interfacialFreeEnergy, `${orientationId} free energy`);
    const uncertainty = finite(entry.uncertainty, `${orientationId} uncertainty`);
    if (uncertainty < 0) throw new RangeError(`${orientationId} uncertainty must be nonnegative`);
    if (!(interfacialFreeEnergy - 3 * uncertainty > 0)) {
      throw new Error(`${orientationId} free energy is not positive at the three-sigma lower bound`);
    }
    return { orientationId, normal, interfacialFreeEnergy, uncertainty };
  });
  const geometry = buildNormalizedWulffGeometry(orientations, dimension);
  return {
    schema: INTERFACIAL_ENERGY_RESPONSE_SCHEMA, requestSha256, structureSha256,
    intrinsicDimension: dimension, method, interface: { ...response.interface, adjacentPhase },
    units: expectedUnits, orientations, validation: { ...validation }, geometry,
    responseAccepted: true, candidateSetChanged: false, candidateRankingChanged: false,
    usedAsGrowthLaw: false, usedAsAttachmentRate: false, targetUsed: false,
  };
}
