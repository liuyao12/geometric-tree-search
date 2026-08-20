#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const inputFiles = String(args.get("inputs") ?? "").split(",").map(value => value.trim()).filter(Boolean);
if (!inputFiles.length) throw new Error("--inputs=<report1.json,report2.json,...> is required");
const outputFile = args.get("output-file") ?? null;
const reports = await Promise.all(inputFiles.map(async file => JSON.parse(await readFile(file, "utf8"))));
const expected = reports[0].configuration ?? {};
const comparableConfiguration = configuration => JSON.stringify({
  candidatesFile: configuration?.candidatesFile ?? null,
  timeMs: configuration?.timeMs ?? null,
  periodicMax: configuration?.periodicMax ?? null,
  isohedralTarget: configuration?.isohedralTarget ?? null,
  displayTarget: configuration?.displayTarget ?? null,
  includeMirrors: configuration?.includeMirrors ?? false,
  includePlacements: configuration?.includePlacements ?? false
});
for (let index = 0; index < reports.length; index += 1) {
  if (reports[index].kind !== "lattice_polyhedron_easy_lane_screen") {
    throw new Error(`${inputFiles[index]} is not an easy-lane report`);
  }
  if (comparableConfiguration(reports[index].configuration) !== comparableConfiguration(expected)) {
    throw new Error(`${inputFiles[index]} has a different screening configuration`);
  }
}
const rows = reports.flatMap(report => report.rows ?? []).sort((left, right) => left.id.localeCompare(right.id));
if (new Set(rows.map(row => row.id)).size !== rows.length) throw new Error("Candidate ids overlap across reports");
const report = {
  schemaVersion: 1,
  kind: "lattice_polyhedron_easy_lane_screen",
  generatedAt: new Date().toISOString(),
  configuration: expected,
  sourceReports: inputFiles.map(file => file.split("/").at(-1)),
  rows
};
const serialized = `${JSON.stringify(report, null, 2)}\n`;
if (outputFile) await writeFile(outputFile, serialized);
else process.stdout.write(serialized);
