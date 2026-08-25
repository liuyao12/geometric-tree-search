#!/usr/bin/env node

import { createHash } from "node:crypto";
import { createWriteStream } from "node:fs";
import { once } from "node:events";

import {
  canonicalPolycubeKey,
  enumeratePolycubes,
  isChiralPolycube,
  polycubeOrientations,
  polycubeSymmetries,
  POLYCUBE_ISOMETRY_COUNT,
  POLYCUBE_ROTATION_COUNT
} from "../assets/polycube-enumerator.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const size = Number(args.get("size"));
if (!Number.isInteger(size) || size < 1 || size > 10) {
  throw new Error("--size must be an integer from 1 through 10");
}
const includeReflections = ["1", "true", "yes"].includes(
  String(args.get("include-reflections") ?? "false").toLowerCase()
);
const output = args.get("output");
if (!output) throw new Error("--output is required");

const knownCounts = {
  proper: [1, 1, 2, 8, 29, 166, 1023, 6922, 48311, 346543],
  full: [1, 1, 2, 7, 23, 112, 607, 3811, 25413, 178083]
};
const groupOrder = includeReflections ? POLYCUBE_ISOMETRY_COUNT : POLYCUBE_ROTATION_COUNT;
const candidates = enumeratePolycubes(size, { includeReflections });
const expectedCount = knownCounts[includeReflections ? "full" : "proper"][size - 1];
if (candidates.length !== expectedCount) {
  throw new Error(`enumeration count ${candidates.length} does not match known count ${expectedCount}`);
}

const idByProperKey = new Map(
  (includeReflections ? [] : candidates).map(candidate => [candidate.key, candidate.id])
);
const orderedKeyHash = createHash("sha256");
for (const candidate of candidates) orderedKeyHash.update(`${candidate.id}\0${candidate.key}\n`);
const candidateKeySha256 = orderedKeyHash.digest("hex");

const stream = createWriteStream(output, { encoding: "utf8" });
const write = async record => {
  if (!stream.write(`${JSON.stringify(record)}\n`)) await once(stream, "drain");
};

await write({
  type: "census_manifest",
  schema: "gcts.z3_polycube_census.v1",
  size,
  candidates: candidates.length,
  lattice: "Z3",
  candidate_equivalence_group: includeReflections
    ? "full_cubic_isometries_and_integer_translation"
    : "proper_cubic_rotations_and_integer_translation",
  allowed_placement_group: includeReflections
    ? "48_signed_permutation_isometries_and_integer_translation"
    : "24_proper_cubic_rotations_and_integer_translation",
  group_order: groupOrder,
  candidate_key_sha256: candidateKeySha256,
  known_count_verified: true
});

for (let index = 0; index < candidates.length; index += 1) {
  const candidate = candidates[index];
  const orientations = polycubeOrientations(candidate.voxels, { includeReflections });
  const stabilizer = polycubeSymmetries(candidate.voxels, { includeReflections });
  if (orientations.length * stabilizer.length !== groupOrder) {
    throw new Error(`${candidate.id} violates orbit-stabilizer`);
  }
  const occupied = new Set(candidate.voxels.map(voxel => voxel.join(",")));
  const reached = new Set([candidate.voxels[0].join(",")]);
  const queue = [candidate.voxels[0]];
  while (queue.length) {
    const [x, y, z] = queue.shift();
    for (const [dx, dy, dz] of [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]]) {
      const key = `${x + dx},${y + dy},${z + dz}`;
      if (!occupied.has(key) || reached.has(key)) continue;
      reached.add(key);
      queue.push(key.split(",").map(Number));
    }
  }
  if (reached.size !== candidate.voxels.length) throw new Error(`${candidate.id} is disconnected`);
  const mirrorProperKey = canonicalPolycubeKey(
    candidate.voxels.map(([x, y, z]) => [-x, y, z])
  );
  await write({
    type: "candidate",
    index,
    id: candidate.id,
    canonical_key: candidate.key,
    voxels: candidate.voxels,
    connected: true,
    chiral: isChiralPolycube(candidate.voxels),
    mirror_proper_key: mirrorProperKey,
    mirror_partner_id: includeReflections ? candidate.id : idByProperKey.get(mirrorProperKey) ?? null,
    orientation_count: orientations.length,
    orientation_keys: orientations.map(orientation => orientation.key),
    stabilizer_order: stabilizer.length,
    stabilizer: stabilizer.map(symmetry => ({
      matrix: symmetry.matrix,
      translation: symmetry.translation,
      determinant: symmetry.determinant
    })),
    orbit_stabilizer_verified: true
  });
}

await write({
  type: "census_summary",
  size,
  candidates: candidates.length,
  candidate_key_sha256: candidateKeySha256,
  ids_contiguous: candidates.every((candidate, index) => candidate.id ===
    `p${size}-${String(index + 1).padStart(String(candidates.length).length, "0")}`)
});
stream.end();
await once(stream, "finish");
process.stderr.write(`wrote ${candidates.length} candidates to ${output}\n`);
