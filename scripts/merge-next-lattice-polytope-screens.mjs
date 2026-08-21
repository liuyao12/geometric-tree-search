#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import { POLYDB_FEW_LATTICE_POINTS_COUNTS } from "../assets/lattice-polytope-census.js";

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

const size = reports[0].report.configuration?.size;
const expectedConfiguration = reports[0].report.configuration;
const source = expectedConfiguration.source ?? "blanco_santos";
const parts = new Set();
const ranges = [];
for (const { file, report } of reports) {
  if (report.kind !== "blanco_santos_extendable_shell_one_screen") {
    throw new Error(`${file} is not a first-stage census report`);
  }
  if (report.configuration?.size !== size) throw new Error(`${file} has a different census size`);
  if ((report.configuration?.source ?? "blanco_santos") !== source) throw new Error(`${file} has a different census source`);
  for (const key of ["timeMs", "nodeLimit", "orientationGroup", "translations", "mirrors", "globalZeroFacePruning", "fastLocalEdgePreflight"]) {
    if (report.configuration?.[key] !== expectedConfiguration?.[key]) {
      throw new Error(`${file} has a different ${key} configuration`);
    }
  }
  for (const part of report.configuration?.parts ?? []) {
    if (parts.has(part)) throw new Error(`Census part ${part} appears more than once`);
    parts.add(part);
  }
  if (source === "polydb") {
    for (const record of report.sources ?? []) {
      if (!Number.isInteger(record.start) || !Number.isInteger(record.end) || record.end <= record.start) {
        throw new Error(`${file} has an invalid polyDB source range`);
      }
      ranges.push({ start: record.start, end: record.end });
    }
  }
}
if (source === "polydb") {
  ranges.sort((left, right) => left.start - right.start);
  for (let index = 1; index < ranges.length; index += 1) {
    if (ranges[index - 1].end !== ranges[index].start) {
      throw new Error(`polyDB ranges have a gap or overlap at ${ranges[index - 1].end}/${ranges[index].start}`);
    }
  }
}

const sum = key => reports.reduce((total, { report }) => total + (report.counts?.[key] ?? 0), 0);
const survivors = reports.flatMap(({ report }) => report.survivors ?? []);
const unresolved = reports.flatMap(({ report }) => report.unresolved ?? []);
const screenedCandidates = reports.reduce((total, { report }) => total + report.screenedCandidates, 0);
const counts = {
  localEdgeObstruction: sum("localEdgeObstruction"),
  extendableShellObstruction: sum("extendableShellObstruction"),
  shellOneWitness: sum("shellOneWitness"),
  incomplete: sum("incomplete"),
  other: sum("other")
};
if (Object.values(counts).reduce((sumValue, value) => sumValue + value, 0) !== screenedCandidates) {
  throw new Error("Merged outcome counts do not equal the screened candidate count");
}
if (survivors.length !== counts.shellOneWitness || unresolved.length !== counts.incomplete + counts.other) {
  throw new Error("Merged candidate detail counts do not match the outcome totals");
}

const report = {
  schemaVersion: 1,
  kind: "blanco_santos_extendable_shell_one_screen_merged",
  generatedAt: new Date().toISOString(),
  configuration: {
    size,
    source,
    parts: [...parts].sort((left, right) => left - right),
    ...(source === "polydb" ? {
      ranges,
      start: ranges[0]?.start ?? null,
      end: ranges.at(-1)?.end ?? null,
      completeConfiguredSize: ranges[0]?.start === 0
        && ranges.at(-1)?.end === POLYDB_FEW_LATTICE_POINTS_COUNTS[size]
        && screenedCandidates === POLYDB_FEW_LATTICE_POINTS_COUNTS[size]
    } : {}),
    timeMs: expectedConfiguration.timeMs,
    nodeLimit: expectedConfiguration.nodeLimit,
    orientationGroup: expectedConfiguration.orientationGroup,
    translations: expectedConfiguration.translations,
    mirrors: expectedConfiguration.mirrors,
    globalZeroFacePruning: expectedConfiguration.globalZeroFacePruning,
    fastLocalEdgePreflight: expectedConfiguration.fastLocalEdgePreflight
  },
  sources: reports.flatMap(({ report }) => report.sources ?? []),
  sourceReports: inputFiles.map(file => file.split("/").at(-1)),
  screenedCandidates,
  counts,
  survivors,
  unresolved,
  elapsedMs: reports.reduce((total, { report }) => total + (report.elapsedMs ?? 0), 0),
  interpretation: `This exhaustive first-stage screen leaves only candidates with an exact extendable shell-one witness. Local-edge and exhausted shell failures are non-tiling certificates in the configured face-to-face ${expectedConfiguration.mirrors ? "full-cubic-isometry" : "proper-cubic-rotation"} lattice model; survivors still require deeper shell and periodic screening.`
};
const serialized = `${JSON.stringify(report, null, 2)}\n`;
if (outputFile) await writeFile(outputFile, serialized);
else process.stdout.write(serialized);
