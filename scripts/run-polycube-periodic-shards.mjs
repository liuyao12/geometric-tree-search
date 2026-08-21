#!/usr/bin/env node

import { spawn, spawnSync } from "node:child_process";
import { createWriteStream, existsSync, mkdirSync, readFileSync, renameSync, unlinkSync, writeFileSync } from "node:fs";
import { availableParallelism } from "node:os";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { polycubePeriodicHnfBasisCount } from "../assets/polycube-periodic-tiler.js";
import { voxelsFromPolycubeKey } from "../assets/polycube-enumerator.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const integerArg = (name, fallback, minimum = 0) => {
  const value = Number(args.get(name) ?? fallback);
  if (!Number.isInteger(value) || value < minimum) {
    throw new Error(`--${name} must be an integer at least ${minimum}`);
  }
  return value;
};
const booleanArg = (name, fallback) => {
  if (!args.has(name)) return fallback;
  return !["0", "false", "no"].includes(String(args.get(name)).toLowerCase());
};

const key = args.get("key");
if (!key) throw new Error("--key is required");
const voxels = voxelsFromPolycubeKey(key);
const copies = integerArg("copies", NaN, 1);
const id = String(args.get("id") ?? `custom-${voxels.length}`).replace(/[^A-Za-z0-9_.-]+/g, "-");
const outputDirectory = resolve(String(args.get("output-dir") ?? `runs/periodic-copy${copies}-${id}`));
const totalHnfBases = polycubePeriodicHnfBasisCount(voxels.length * copies);
const rangeStart = Math.min(integerArg("hnf-start-index", 0), totalHnfBases);
const rangeEnd = Math.min(integerArg("hnf-end-index", totalHnfBases), totalHnfBases);
if (rangeEnd < rangeStart) throw new Error("--hnf-end-index must be at least --hnf-start-index");
const requestedShards = integerArg("shards", Math.min(16, Math.max(1, rangeEnd - rangeStart)), 1);
const shardSize = integerArg(
  "shard-size",
  Math.max(1, Math.ceil((rangeEnd - rangeStart) / requestedShards)),
  1
);
const concurrency = integerArg(
  "concurrency",
  Math.min(requestedShards, Math.max(1, availableParallelism?.() ?? 4)),
  1
);
const progressMs = integerArg("progress-ms", 30_000, 1000);
const periodicTimeMs = integerArg("periodic-time-ms", 3_600_000, 1);
const nodeLimit = integerArg("nodes", 1_000_000_000, 1);
const resume = booleanArg("resume", true);
const pipeline = fileURLToPath(new URL("./screen-3d-aperiodic-polycubes.mjs", import.meta.url));
const auditor = fileURLToPath(new URL("./audit-polycube-periodic-shards.mjs", import.meta.url));

mkdirSync(outputDirectory, { recursive: true });
const intervals = [];
for (let start = rangeStart; start < rangeEnd; start += shardSize) {
  intervals.push([start, Math.min(rangeEnd, start + shardSize)]);
}
if (!intervals.length) intervals.push([rangeStart, rangeEnd]);
const shardPath = ([start, end]) => resolve(outputDirectory, `hnf-${start}-${end}.ndjson`);
const stderrPath = ([start, end]) => resolve(outputDirectory, `hnf-${start}-${end}.stderr`);

const auditInterval = (interval, report) => spawnSync(process.execPath, [
  auditor,
  `--expected-start=${interval[0]}`,
  `--expected-end=${interval[1]}`,
  report
], { encoding: "utf8" });

const pending = [];
let reused = 0;
for (const interval of intervals) {
  const report = shardPath(interval);
  if (resume && existsSync(report) && auditInterval(interval, report).status === 0) {
    reused += 1;
  } else {
    pending.push(interval);
  }
}

process.stdout.write(`${JSON.stringify({
  type: "shard_run_start",
  id,
  key,
  volume: voxels.length,
  copies,
  quotient_cells: voxels.length * copies,
  total_hnf_bases: totalHnfBases,
  requested_range: [rangeStart, rangeEnd],
  shards: intervals.length,
  shard_size: shardSize,
  concurrency,
  progress_ms: progressMs,
  reused,
  pending: pending.length,
  output_directory: outputDirectory
})}\n`);

let nextPending = 0;
let active = 0;
let completed = reused;
let failure = null;
const activeChildren = new Set();
const activeRanges = new Map();
const progressTimer = setInterval(() => {
  if (!activeRanges.size) return;
  process.stdout.write(`${JSON.stringify({
    type: "shard_run_progress",
    completed,
    shards: intervals.length,
    pending: pending.length - nextPending,
    active_ranges: [...activeRanges.values()]
  })}\n`);
}, progressMs);

const runShard = interval => new Promise(resolveShard => {
  const [start, end] = interval;
  const report = shardPath(interval);
  const temporaryReport = `${report}.tmp`;
  const errorReport = stderrPath(interval);
  for (const path of [temporaryReport, errorReport]) if (existsSync(path)) unlinkSync(path);
  const stdout = createWriteStream(temporaryReport, { flags: "wx" });
  const stderr = createWriteStream(errorReport, { flags: "wx" });
  const child = spawn(process.execPath, [
    pipeline,
    `--key=${key}`,
    `--periodic-min-tiles=${copies}`,
    `--periodic-max-tiles=${copies}`,
    `--periodic-hnf-start-index=${start}`,
    `--periodic-hnf-end-index=${end}`,
    `--periodic-time-ms=${periodicTimeMs}`,
    "--periodic-budget-clock=cpu",
    `--nodes=${nodeLimit}`,
    "--box-screen=false",
    "--general-periodic=false",
    "--isohedral-screen=false",
    "--stop-after=periodic",
    "--report-chirality=false"
  ], { stdio: ["ignore", "pipe", "pipe"] });
  activeChildren.add(child);
  activeRanges.set(child.pid, interval);
  child.stdout.pipe(stdout);
  child.stderr.pipe(stderr);
  child.on("error", error => resolveShard({ interval, error }));
  child.on("close", code => {
    activeChildren.delete(child);
    activeRanges.delete(child.pid);
    stdout.end();
    stderr.end();
    if (code !== 0) {
      resolveShard({ interval, error: new Error(`shard [${start},${end}) exited ${code}`) });
      return;
    }
    renameSync(temporaryReport, report);
    const audited = auditInterval(interval, report);
    if (audited.status !== 0) {
      resolveShard({ interval, error: new Error(audited.stderr.trim() || `shard [${start},${end}) failed audit`) });
      return;
    }
    resolveShard({ interval, audit: JSON.parse(audited.stdout) });
  });
});

await new Promise(resolveAll => {
  const launch = () => {
    if ((failure && active === 0) || (nextPending >= pending.length && active === 0)) {
      resolveAll();
      return;
    }
    if (failure) {
      for (const child of activeChildren) child.kill("SIGTERM");
      return;
    }
    while (!failure && active < concurrency && nextPending < pending.length) {
      const interval = pending[nextPending++];
      active += 1;
      runShard(interval).then(result => {
        active -= 1;
        if (result.error) {
          failure = result.error;
        } else {
          completed += 1;
          process.stdout.write(`${JSON.stringify({
            type: "shard_complete",
            range: interval,
            completed,
            shards: intervals.length,
            exact_cover_nodes: result.audit.totals.exact_cover_nodes,
            milliseconds: result.audit.totals.milliseconds
          })}\n`);
        }
        launch();
      });
    }
  };
  launch();
});

clearInterval(progressTimer);
if (failure) throw failure;
const reports = intervals.map(shardPath);
const finalAudit = spawnSync(process.execPath, [
  auditor,
  `--expected-start=${rangeStart}`,
  `--expected-end=${rangeEnd}`,
  ...reports
], { encoding: "utf8" });
if (finalAudit.status !== 0) throw new Error(finalAudit.stderr.trim() || "final shard audit failed");
const auditPath = resolve(outputDirectory, "audit.json");
const temporaryAuditPath = `${auditPath}.tmp`;
writeFileSync(temporaryAuditPath, finalAudit.stdout);
renameSync(temporaryAuditPath, auditPath);
const audit = JSON.parse(readFileSync(auditPath, "utf8"));
process.stdout.write(`${JSON.stringify({
  type: "shard_run_complete",
  id,
  key,
  copies,
  audit: auditPath,
  totals: audit.totals
})}\n`);
