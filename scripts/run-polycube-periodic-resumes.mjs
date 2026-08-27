#!/usr/bin/env node

import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { basename, resolve } from "node:path";
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
  "input-report", "resume-active-hnf"
]);
const forwardedArgs = rawArgs.filter(raw => {
  const separator = raw.indexOf("=");
  const name = raw.slice(2, separator < 0 ? undefined : separator);
  return !controlNames.has(name);
});
const outputPrefix = parsed.get("output-prefix");
if (!outputPrefix) throw new Error("--output-prefix is required");
if (parsed.has("output-file") || parsed.has("input-report") || parsed.has("resume-active-hnf")) {
  throw new Error("The periodic resume driver owns output, input-report, and resume flags");
}
if (parsed.has("key") || parsed.has("candidate-id")) {
  throw new Error("Resume geometry and identity come from --resume-report; omit --key and --candidate-id");
}
const maxSlices = Math.max(1, Math.floor(Number(parsed.get("max-slices")) || 1));
const firstIndex = Math.max(0, Math.floor(Number(parsed.get("first-index")) || 0));
let sourcePath = parsed.get("resume-report") ? resolve(parsed.get("resume-report")) : null;
if (!sourcePath) throw new Error("--resume-report is required");
if (!existsSync(sourcePath)) throw new Error(`Missing resume source ${sourcePath}`);
const screenScript = new URL("./screen-3d-aperiodic-polycubes.mjs", import.meta.url);
const sha256Text = text => createHash("sha256").update(text).digest("hex");
const parseNdjson = (text, label) => {
  try {
    return text.split(/\r?\n/u).filter(Boolean).map(JSON.parse);
  } catch (error) {
    throw new Error(`${label} is not valid NDJSON: ${error.message}`);
  }
};
const candidateRecord = records => {
  const candidates = records.filter(record => record.type === "candidate");
  if (candidates.length !== 1) throw new Error("A periodic resume slice must contain exactly one candidate");
  return candidates[0];
};
const requireReplayableCutoff = (records, label) => {
  const candidate = candidateRecord(records);
  const periodic = candidate.periodic_fast;
  if (periodic?.stopped_by == null || !Number.isFinite(periodic.active_hnf_index)) {
    throw new Error(`${label} has no replayable active HNF cutoff`);
  }
  return candidate;
};

for (let offset = 0; offset < maxSlices; offset++) {
  const index = firstIndex + offset;
  const outputPath = resolve(`${outputPrefix}-resume${index}.ndjson`);
  if (existsSync(outputPath)) throw new Error(`Refusing to overwrite ${outputPath}`);
  const sourceText = readFileSync(sourcePath, "utf8");
  const sourceRecords = parseNdjson(sourceText, `Periodic resume source for slice ${index}`);
  const sourceCandidate = requireReplayableCutoff(sourceRecords, `Periodic resume source ${sourcePath}`);
  const childArgs = [
    screenScript.pathname,
    ...forwardedArgs,
    `--input-report=${sourcePath}`,
    "--resume-active-hnf=true",
    `--output-file=${outputPath}`
  ];
  const child = spawnSync(process.execPath, childArgs, {
    encoding: "utf8",
    maxBuffer: 128 * 1024 * 1024
  });
  if (child.status !== 0) {
    throw new Error(`Periodic slice ${index} failed: ${child.stderr || child.stdout || `exit ${child.status}`}`);
  }
  if (!existsSync(outputPath)) throw new Error(`Periodic slice ${index} did not write ${outputPath}`);
  const outputText = readFileSync(outputPath, "utf8");
  const records = parseNdjson(outputText, `Periodic slice ${index}`);
  const start = records.find(record => record.type === "screen_start");
  const candidate = candidateRecord(records);
  const periodic = candidate.periodic_fast;
  if (!start || !periodic || candidate.id !== sourceCandidate.id || candidate.key !== sourceCandidate.key) {
    throw new Error(`Periodic slice ${index} changed candidate identity or omitted its result`);
  }
  const expectedHash = sha256Text(sourceText);
  const hashCommitment = (start.input_report_sha256 ?? []).find(entry =>
    resolve(entry?.path ?? "") === sourcePath
  );
  if (start.resume_active_hnf !== true
    || start.input_reports?.length !== 1
    || resolve(start.input_reports[0]) !== sourcePath
    || hashCommitment?.sha256 !== expectedHash
    || periodic.hnf_skipped !== sourceCandidate.periodic_fast.active_hnf_index) {
    throw new Error(`Periodic slice ${index} did not commit to and resume its exact HNF source`);
  }
  const terminal = periodic.certified
    ? "certified_periodic_tiler"
    : periodic.hnf_range_exhausted
      ? "exact_hnf_exhaustion"
      : null;
  if (!terminal && (periodic.stopped_by == null || !Number.isFinite(periodic.active_hnf_index))) {
    throw new Error(`${candidate.id} stopped without a replayable active HNF cutoff`);
  }
  process.stdout.write(`${JSON.stringify({
    type: "periodic_resume_slice",
    index,
    output: outputPath,
    sha256: sha256Text(outputText),
    candidate_id: candidate.id,
    copies: start.periodic_min_tiles,
    nodes: periodic.nodes,
    hnf_skipped: periodic.hnf_skipped,
    hnf_visited: periodic.hnf_visited,
    active_hnf_index: periodic.active_hnf_index,
    stopped_by: periodic.stopped_by,
    terminal,
    source: basename(sourcePath)
  })}\n`);
  if (terminal) break;
  sourcePath = outputPath;
}
