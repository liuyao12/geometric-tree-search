#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const inputFiles = String(args.get("inputs") ?? "")
  .split(",")
  .map(value => value.trim())
  .filter(Boolean);
if (!inputFiles.length) throw new Error("--inputs=<report1.json,report2.json,...> is required");
const outputFile = args.get("output-file") ?? null;
const reports = await Promise.all(inputFiles.map(async file => ({
  file,
  report: JSON.parse(await readFile(file, "utf8"))
})));

const configuration = reports[0].report.configuration;
const comparableKeys = [
  "targetShellDepth", "includeMirrors", "cascade", "timeMs", "nodeLimit",
  "failureMemo", "failureMemoSymmetry", "seededTieBreaks", "globalZeroFacePruning",
  "includeWitness", "candidatesFile", "orientationGroup", "model", "shellDefinition",
  "deadFaceRule"
];
const candidateIds = new Set();
for (const { file, report } of reports) {
  if (report.kind !== "lattice_polyhedron_complete_shell_screen") {
    throw new Error(`${file} is not a complete-shell screen report`);
  }
  for (const key of comparableKeys) {
    if (JSON.stringify(report.configuration?.[key]) !== JSON.stringify(configuration?.[key])) {
      throw new Error(`${file} has a different ${key} configuration`);
    }
  }
  if (JSON.stringify(report.configuration?.seeds) !== JSON.stringify(configuration?.seeds)) {
    throw new Error(`${file} has different seeds`);
  }
  for (const candidate of report.candidates ?? []) {
    if (candidateIds.has(candidate.candidate)) throw new Error(`Candidate ${candidate.candidate} appears more than once`);
    candidateIds.add(candidate.candidate);
  }
}

const rows = reports.flatMap(({ report }) => report.rows ?? []);
const candidates = reports.flatMap(({ report }) => report.candidates ?? [])
  .sort((left, right) => left.candidate.localeCompare(right.candidate));
if (rows.length !== candidates.reduce((sum, candidate) => sum + candidate.trials, 0)) {
  throw new Error("Merged row count does not equal the candidate trial count");
}
const totals = {
  trials: rows.length,
  targetHits: rows.filter(row => row.success).length,
  certifiedNonTilerTrials: rows.filter(row => row.certified && row.canTile === false).length,
  incompleteTrials: rows.filter(row => row.searchIncomplete).length
};
const report = {
  schemaVersion: 1,
  kind: "lattice_polyhedron_complete_shell_screen",
  generatedAt: new Date().toISOString(),
  configuration,
  sourceReports: inputFiles.map(file => file.split("/").at(-1)),
  rows,
  candidates,
  totals,
  interpretation: reports[0].report.interpretation
};
const serialized = `${JSON.stringify(report, null, 2)}\n`;
if (outputFile) await writeFile(outputFile, serialized);
else process.stdout.write(serialized);
