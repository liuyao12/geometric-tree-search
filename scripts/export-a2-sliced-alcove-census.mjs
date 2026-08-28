import { writeFile } from "node:fs/promises";
import {
  enumerateA2SlicedAlcoves,
  makeA2SlicedAlcoveUnion
} from "../assets/a2-sliced-alcoves.js";

const readArg = (name, fallback) => {
  const prefix = `--${name}=`;
  return process.argv.find(argument => argument.startsWith(prefix))?.slice(prefix.length) ?? fallback;
};
const size = Math.max(1, Math.floor(Number(readArg("size", 7)) || 7));
const directedOnly = readArg("transverse-asymmetric", "false") === "true";
const output = readArg("output", `data/a2-sliced-alcove-size${size}-census.ndjson`);
const census = enumerateA2SlicedAlcoves({
  size,
  requireTransverseProfileAsymmetry: directedOnly
});
const records = census.map((candidate, index) => {
  const data = makeA2SlicedAlcoveUnion(candidate.cells);
  return {
    id: `a2sa_${size}_${String(index).padStart(5, "0")}`,
    size,
    key: candidate.key,
    alcoves: candidate.cells,
    occupancy: data.occ.map(([point, weight]) => [point, weight]),
    morphology: candidate.morphology,
    model: "a2_sliced_exact_lattice_function",
    classification: "unscreened"
  };
});
await writeFile(output, `${records.map(record => JSON.stringify(record)).join("\n")}\n`, "utf8");
console.log(JSON.stringify({ size, candidates: records.length, directedOnly, output }, null, 2));
