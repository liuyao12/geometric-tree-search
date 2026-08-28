import { writeFile } from "node:fs/promises";
import { enumerateA2LayeredPolyprisms } from "../assets/a2-layered-polyprisms.js";

const readArg = (name, fallback) => {
  const prefix = `--${name}=`;
  return process.argv.find(argument => argument.startsWith(prefix))?.slice(prefix.length) ?? fallback;
};
const size = Math.max(1, Math.floor(Number(readArg("size", 7)) || 7));
const output = readArg("output", `data/a2-layered-size${size}-census.ndjson`);
const layerEssentialOnly = readArg("layer-essential", "false") === "true";
const minLayerCount = Math.max(1, Math.floor(Number(readArg("min-layers", 1)) || 1));
const minDistinctCrossSections = Math.max(1,
  Math.floor(Number(readArg("min-cross-sections", 1)) || 1));
const minCrossSectionChanges = Math.max(0,
  Math.floor(Number(readArg("min-cross-section-changes", 0)) || 0));
const requireTransverseProfileAsymmetry = readArg("transverse-asymmetric", "false") === "true";
const requireAllCrossSectionsDistinct = readArg("all-cross-sections-distinct", "false") === "true";
const census = enumerateA2LayeredPolyprisms({
  size,
  layerEssentialOnly,
  minLayerCount,
  minDistinctCrossSections,
  minCrossSectionChanges,
  requireTransverseProfileAsymmetry,
  requireAllCrossSectionsDistinct
});
const records = census.map((candidate, index) => ({
  id: `a2lp_${size}_${String(index).padStart(5, "0")}`,
  size,
  key: candidate.key,
  cells: candidate.cells,
  morphology: candidate.morphology,
  classification: "unscreened"
}));
await writeFile(output, `${records.map(record => JSON.stringify(record)).join("\n")}\n`, "utf8");
console.log(JSON.stringify({
  size,
  candidates: records.length,
  layerEssentialOnly,
  minLayerCount,
  minDistinctCrossSections,
  minCrossSectionChanges,
  requireTransverseProfileAsymmetry,
  requireAllCrossSectionsDistinct,
  output
}, null, 2));
