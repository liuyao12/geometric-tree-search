#!/usr/bin/env node
/** Reduce an exact A2-sliced periodic screen to reflection-class representatives. */

import { readFile, writeFile } from "node:fs/promises";
import {
  a2SlicedAlcoveVertices,
  canonicalA2SlicedAlcoves
} from "../assets/a2-sliced-alcoves.js";

const readArg = name => {
  const prefix = `--${name}=`;
  return process.argv.find(argument => argument.startsWith(prefix))?.slice(prefix.length);
};
const input = readArg("input");
const output = readArg("output");
const copies = Math.max(1, Math.floor(Number(readArg("copies")) || 1));
if (!input || !output) {
  throw new Error("Usage: select-a2-sliced-survivors.mjs --input=screen.ndjson --output=survivors.ndjson --copies=N");
}

const cellFromVertices = vertices => {
  const base = [0, 1, 2].map(axis => Math.min(...vertices.map(point => point[axis])));
  const ranked = vertices.map(point => ({
    point,
    rank: point.reduce((sum, value, axis) => sum + value - base[axis], 0)
  })).sort((left, right) => left.rank - right.rank);
  if (ranked.map(entry => entry.rank).join(",") !== "0,1,2,3") {
    throw new Error("reflected tetrahedron left the A2-sliced alcove complex");
  }
  const first = ranked[1].point.findIndex((value, axis) => value - base[axis] === 1);
  const second = ranked[2].point.findIndex((value, axis) =>
    value - ranked[1].point[axis] === 1);
  const third = 3 - first - second;
  if (new Set([first, second, third]).size !== 3) {
    throw new Error("could not recover reflected alcove order");
  }
  return { base, order: [first, second, third] };
};

const reflectionClassKey = alcoves => {
  const proper = canonicalA2SlicedAlcoves(alcoves).key;
  const reflected = canonicalA2SlicedAlcoves(alcoves.map(alcove => cellFromVertices(
    a2SlicedAlcoveVertices(alcove).map(([x, y, z]) => [y, x, z])
  ))).key;
  return [proper, reflected].sort()[0];
};

const records = (await readFile(input, "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);
const survivors = records.filter(record => record.classification === "unresolved");
for (const record of records) {
  const screen = record.periodic_z3 ?? {};
  if (record.classification === "periodic") {
    if (screen.certificate?.copies !== copies || screen.replay?.verified !== true) {
      throw new Error(`invalid periodic certificate for ${record.id}`);
    }
  } else if (record.classification !== "unresolved"
      || screen.solver_unknown !== 0
      || screen.hnf_range_exhausted !== true
      || screen.exhausted_by_copies?.[String(copies)] == null) {
    throw new Error(`incomplete periodic screen for ${record.id}`);
  }
}

const classes = new Map();
for (const record of survivors) {
  const key = reflectionClassKey(record.alcoves);
  if (!classes.has(key)) classes.set(key, []);
  classes.get(key).push(record);
}
const representatives = [...classes.entries()].map(([key, members]) => {
  members.sort((left, right) => left.id.localeCompare(right.id));
  const representative = members[0];
  return {
    ...representative,
    reflection_class: {
      key,
      size: members.length,
      members: members.map(record => record.id)
    }
  };
}).sort((left, right) =>
  (right.periodic_z3.exact_multicover_nodes ?? 0) - (left.periodic_z3.exact_multicover_nodes ?? 0)
  || right.morphology.layer_count - left.morphology.layer_count
  || left.id.localeCompare(right.id)
).map((record, index) => ({
  ...record,
  survivor_priority: index + 1,
  survivor_count: classes.size
}));

await writeFile(output, representatives.map(record => JSON.stringify(record)).join("\n") + "\n", "utf8");
console.log(JSON.stringify({
  records: records.length,
  periodic: records.length - survivors.length,
  survivors: survivors.length,
  reflection_classes: classes.size,
  copies_exhausted: copies,
  output,
  representatives: representatives.map(record => record.id)
}, null, 2));
