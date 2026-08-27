import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");

function functionSource(name) {
  const start = source.indexOf(`function ${name}(`);
  assert.notEqual(start, -1, `missing function ${name}`);
  const brace = source.indexOf("{", start);
  let depth = 0;
  for (let index = brace; index < source.length; index++) {
    if (source[index] === "{") depth++;
    if (source[index] === "}") depth--;
    if (depth === 0) return source.slice(start, index + 1);
  }
  throw new Error(`unterminated function ${name}`);
}

const context = vm.createContext({
  referenceAtoms: [],
  receiptComposition: () => ({}),
  occupationalAlternatives: () => null,
});
for (const name of ["integerGcd", "chemicalSubscript", "activeSampleSpeciesLabel",
  "activeSampleCompositionRecords", "reducedSampleFormula"]) {
  vm.runInContext(functionSource(name), context);
}

assert.equal(vm.runInContext('reducedSampleFormula([["Na",108],["Cl",108]])', context), "NaCl");
assert.equal(vm.runInContext('reducedSampleFormula([["H",144],["O",72]])', context), "H₂O");
assert.equal(vm.runInContext('reducedSampleFormula([["Al",24],["Cu",8],["Fe",4]])', context), "Al₆Cu₂Fe");
assert.equal(vm.runInContext('reducedSampleFormula([["D",0.5],["O",1]])', context), "D 0.50 · O 1.00");

context.occupationalAlternatives = (species) => species === "Cl"
  ? { alternatives: [{ species: "Cl", fraction: 1 }], total: 1, label: "Cl 100%" }
  : species === "occ[Fe=0.5;Ni=0.5]"
    ? { alternatives: [{ species: "Fe", fraction: .5 }, { species: "Ni", fraction: .5 }],
      total: 1, label: "Fe 50% / Ni 50%" } : null;
assert.equal(vm.runInContext('activeSampleSpeciesLabel("Cl")', context), "Cl");
assert.equal(vm.runInContext('activeSampleSpeciesLabel("occ[Fe=0.5;Ni=0.5]")', context), "Fe 50% / Ni 50%");
assert.equal(vm.runInContext('reducedSampleFormula([["Cl",75],["Na",75]])', context), "ClNa");

context.receiptComposition = () => ({ O: 72, H: 144 });
context.referenceAtoms = [{}];
assert.deepEqual(
  JSON.parse(vm.runInContext('JSON.stringify(activeSampleCompositionRecords({elements:["H","O"]}))', context)),
  [["H", 144], ["O", 72]],
);

console.log("specimen formula executable audit passed");
