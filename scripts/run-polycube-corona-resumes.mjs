#!/usr/bin/env node

import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

const rawArgs = process.argv.slice(2);
const parsed = new Map(rawArgs.map(raw => {
  const separator = raw.indexOf("=");
  return separator < 0
    ? [raw.replace(/^--/u, ""), "true"]
    : [raw.slice(2, separator), raw.slice(separator + 1)];
}));
const controlNames = new Set([
  "output-prefix", "max-slices", "first-index", "resume-report", "output-file",
  "obstruction-resume-report"
]);
const forwardedArgs = rawArgs.filter(raw => {
  const separator = raw.indexOf("=");
  const name = raw.slice(2, separator < 0 ? undefined : separator);
  return !controlNames.has(name);
});
const outputPrefix = parsed.get("output-prefix");
if (!outputPrefix) throw new Error("--output-prefix is required");
if (!parsed.get("candidate-id")) {
  throw new Error("The exact corona resume driver requires one explicit --candidate-id");
}
if (parsed.has("output-file") || parsed.has("obstruction-resume-report")) {
  throw new Error("The resume driver owns output and resume-report arguments");
}
const maxSlices = Math.max(1, Math.floor(Number(parsed.get("max-slices")) || 1));
const firstIndex = Math.max(0, Math.floor(Number(parsed.get("first-index")) || 0));
let sourcePath = parsed.get("resume-report") ? resolve(parsed.get("resume-report")) : null;
if (sourcePath && !existsSync(sourcePath)) throw new Error(`Missing resume source ${sourcePath}`);
const screenScript = new URL("./screen-3d-aperiodic-polycubes.mjs", import.meta.url);
const sha256Text = text => createHash("sha256").update(text).digest("hex");
const parseNdjson = (text, label) => {
  try {
    return text.split(/\r?\n/u).filter(Boolean).map(JSON.parse);
  } catch (error) {
    throw new Error(`${label} is not valid NDJSON: ${error.message}`);
  }
};

for (let offset = 0; offset < maxSlices; offset++) {
  const index = firstIndex + offset;
  const outputPath = resolve(`${outputPrefix}-resume${index}.ndjson`);
  if (existsSync(outputPath)) throw new Error(`Refusing to overwrite ${outputPath}`);
  const sourceText = sourcePath ? readFileSync(sourcePath, "utf8") : null;
  const childArgs = [screenScript.pathname, ...forwardedArgs, `--output-file=${outputPath}`];
  if (sourcePath) childArgs.push(`--obstruction-resume-report=${sourcePath}`);
  const child = spawnSync(process.execPath, childArgs, {
    encoding: "utf8",
    maxBuffer: 128 * 1024 * 1024
  });
  if (child.status !== 0) {
    throw new Error(`Corona slice ${index} failed: ${child.stderr || child.stdout || `exit ${child.status}`}`);
  }
  if (!existsSync(outputPath)) throw new Error(`Corona slice ${index} did not write ${outputPath}`);
  const outputText = readFileSync(outputPath, "utf8");
  const records = parseNdjson(outputText, `Corona slice ${index}`);
  const start = records.find(record => record.type === "screen_start");
  const candidates = records.filter(record => record.type === "candidate");
  if (!start || candidates.length !== 1) {
    throw new Error(`Corona slice ${index} must contain one screen_start and one candidate`);
  }
  if (sourceText) {
    const expectedHash = sha256Text(sourceText);
    if (start.obstruction_resume_report_sha256 !== expectedHash
      || resolve(start.obstruction_resume_report ?? "") !== sourcePath) {
      throw new Error(`Corona slice ${index} did not commit to its exact resume source`);
    }
  }
  const candidate = candidates[0];
  const obstruction = candidate.obstruction;
  if (!obstruction) throw new Error(`Corona slice ${index} contains no obstruction result`);
  if (obstruction.incomplete) {
    if (!obstruction.stopped_by || !Array.isArray(obstruction.resume_path)
      || obstruction.resume_path.length === 0) {
      throw new Error(`${candidate.id} stopped without a replayable exact corona frontier`);
    }
  }
  const terminal = obstruction.certified
    ? "certified_non_tiler"
    : obstruction.incomplete
      ? null
      : "corona_found";
  process.stdout.write(`${JSON.stringify({
    type: "corona_resume_slice",
    index,
    output: outputPath,
    sha256: sha256Text(outputText),
    candidate_id: candidate.id,
    layer: obstruction.layer,
    nodes: obstruction.nodes,
    stopped_by: obstruction.stopped_by,
    resume_path_length: obstruction.resume_path?.length ?? 0,
    terminal
  })}\n`);
  if (terminal) break;
  sourcePath = outputPath;
}
