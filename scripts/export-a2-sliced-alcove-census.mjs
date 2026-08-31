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
const legacyDirectedOnly = readArg("transverse-asymmetric", "false") === "true";
const transverseProfile = readArg(
  "transverse-profile",
  legacyDirectedOnly ? "asymmetric" : "all"
);
if (!["all", "asymmetric", "palindromic"].includes(transverseProfile)) {
  throw new Error("--transverse-profile must be all, asymmetric, or palindromic");
}
const output = readArg("output", `data/a2-sliced-alcove-size${size}-census.ndjson`);
const completeCensus = enumerateA2SlicedAlcoves({ size });
const selectedCensus = completeCensus
  .map((candidate, completeIndex) => ({ candidate, completeIndex }))
  .filter(({ candidate }) => transverseProfile === "all"
    || candidate.morphology.transverse_profile_asymmetric === (transverseProfile === "asymmetric"));
const records = selectedCensus.map(({ candidate, completeIndex }, selectedIndex) => {
  const data = makeA2SlicedAlcoveUnion(candidate.cells);
  const idPrefix = transverseProfile === "palindromic" ? "a2sp" : "a2sa";
  const idIndex = transverseProfile === "palindromic" ? completeIndex : selectedIndex;
  return {
    id: `${idPrefix}_${size}_${String(idIndex).padStart(5, "0")}`,
    size,
    key: candidate.key,
    alcoves: candidate.cells,
    occupancy: data.occ.map(([point, weight]) => [point, weight]),
    morphology: candidate.morphology,
    source_complete_census_index: completeIndex,
    transverse_profile_class: candidate.morphology.transverse_profile_asymmetric
      ? "asymmetric"
      : "palindromic",
    model: "a2_sliced_exact_lattice_function",
    classification: "unscreened"
  };
});
await writeFile(output, `${records.map(record => JSON.stringify(record)).join("\n")}\n`, "utf8");
console.log(JSON.stringify({
  size,
  complete_candidates: completeCensus.length,
  candidates: records.length,
  transverse_profile: transverseProfile,
  output
}, null, 2));
