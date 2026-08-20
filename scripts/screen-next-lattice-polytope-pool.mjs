#!/usr/bin/env node

import { createHash } from "node:crypto";
import { writeFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import {
  BLANCO_SANTOS_CENSUS_URLS,
  parseBlancoSantosLatticePoints,
  parsePolyDbLatticePolytopes,
  POLYDB_FEW_LATTICE_POINTS_COUNTS,
  polyDbLatticePolytopeAggregateRequest
} from "../assets/lattice-polytope-census.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const numberArg = (name, fallback) => {
  const value = Number(args.get(name));
  return Number.isFinite(value) ? value : fallback;
};
const size = Math.max(5, Math.min(15, Math.floor(numberArg("size", 11))));
const source = args.get("source") ?? (size > 11 ? "polydb" : "blanco_santos");
if (!["blanco_santos", "polydb"].includes(source)) throw new Error("--source must be blanco_santos or polydb");
if (source === "blanco_santos" && size > 11) throw new Error("The Blanco–Santos text census stops at size 11; use --source=polydb");
const allUrls = source === "blanco_santos" ? BLANCO_SANTOS_CENSUS_URLS(size) : [];
const requestedParts = new Set(String(args.get("parts") ?? "")
  .split(",")
  .map(value => Math.floor(Number(value)))
  .filter(value => value >= 1 && value <= allUrls.length));
const urls = allUrls.filter((_, index) => !requestedParts.size || requestedParts.has(index + 1));
const offset = Math.max(0, Math.floor(numberArg("offset", 0)));
const maxCandidates = Math.max(1, Math.floor(numberArg("max-candidates", Infinity)));
const polyDbStart = Math.max(0, Math.floor(numberArg("start", offset)));
const polyDbEnd = Math.max(polyDbStart, Math.floor(numberArg(
  "end",
  Number.isFinite(maxCandidates)
    ? polyDbStart + maxCandidates
    : POLYDB_FEW_LATTICE_POINTS_COUNTS[size] ?? polyDbStart
)));
const polyDbPageSize = Math.max(10, Math.min(5000, Math.floor(numberArg("polydb-page-size", 1000))));
const fetchRetries = Math.max(0, Math.min(10, Math.floor(numberArg("fetch-retries", 5))));
const timeMs = Math.max(10, Math.floor(numberArg("time-ms", 250)));
const nodeLimit = Math.max(1, Math.floor(numberArg("node-limit", 200000)));
const outputFile = args.get("output-file") ?? null;
const progressEvery = Math.max(1, Math.floor(numberArg("progress-every", 1000)));
const includeMirrors = args.get("include-mirrors") === "true";
const globalZeroFacePruning = args.get("global-zero-face-pruning") === "true";

const sourceRecords = [];
let candidates = [];
const sourceRequests = source === "polydb"
  ? Array.from(
      { length: Math.ceil((polyDbEnd - polyDbStart) / polyDbPageSize) },
      (_, index) => polyDbLatticePolytopeAggregateRequest(
        size,
        polyDbStart + index * polyDbPageSize,
        Math.min(polyDbEnd, polyDbStart + (index + 1) * polyDbPageSize)
      )
    )
  : urls.map(url => ({ url }));
const fetchText = async request => {
  let lastError = null;
  for (let attempt = 0; attempt <= fetchRetries; attempt += 1) {
    try {
      const response = await fetch(request.url);
      if (response.ok) return response.text();
      lastError = new Error(`Failed to fetch ${request.url}: ${response.status}`);
      if (response.status < 500 || attempt === fetchRetries) throw lastError;
    } catch (error) {
      lastError = error;
      if (attempt === fetchRetries) throw error;
    }
    await new Promise(resolve => setTimeout(resolve, Math.min(8000, 500 * 2 ** attempt)));
  }
  throw lastError;
};
for (const request of sourceRequests) {
  const text = await fetchText(request);
  const parsed = source === "polydb"
    ? parsePolyDbLatticePolytopes(JSON.parse(text))
    : parseBlancoSantosLatticePoints(text);
  sourceRecords.push({
    url: source === "polydb" ? new URL(request.url).origin + new URL(request.url).pathname : request.url,
    ...(source === "polydb" ? { start: request.start, end: request.end } : {}),
    bytes: Buffer.byteLength(text),
    sha256: createHash("sha256").update(text).digest("hex"),
    candidates: parsed.length
  });
  candidates.push(...parsed);
}
if (source !== "polydb") candidates = candidates.slice(offset, offset + maxCandidates);

const solveFirstExtendableShell = async candidate => {
  let final = null;
  for await (const message of createTilingStream({
    mode_key: "cube",
    custom_system: {
      name: `Size-${size} screen ${candidate.id}`,
      figure_refs: [],
      polycubes: [],
      polyhedra: [{ name: `Candidate ${candidate.id}`, vertices: candidate.vertices }],
      polycube_lattice: "z3"
    },
    criterion: "shell",
    target_val: 1,
    tiling_strategy: "free_range",
    move_order: "shell",
    face_order: "mrv",
    exhaustive: true,
    agent_exhaustive: true,
    forced_move_layer_lag_cap: 0,
    generic_complete_shell_enumeration: true,
    generic_global_zero_face_pruning: globalZeroFacePruning,
    generic_failure_memo: false,
    generic_geometric_nogood: false,
    include_mirrors: includeMirrors,
    template_preflight: false,
    snapshot_every: 0,
    placement_details: false,
    branch_cap: null,
    candidate_cap: null,
    node_limit: nodeLimit,
    time_limit_ms: timeMs,
    ui_yield_interval_ms: 1000000
  }, tileSpecs, { stop: false })) {
    if (message.type === "finished") final = message;
  }
  return final;
};

const started = performance.now();
const counts = {
  localEdgeObstruction: 0,
  extendableShellObstruction: 0,
  shellOneWitness: 0,
  incomplete: 0,
  other: 0
};
const survivors = [];
const unresolved = [];
for (let index = 0; index < candidates.length; index += 1) {
  const candidate = candidates[index];
  const final = await solveFirstExtendableShell(candidate);
  const kind = final?.tiling_evidence?.kind ?? null;
  if (kind === "local_edge_obstruction" && final?.can_tile === false) {
    counts.localEdgeObstruction += 1;
  } else if (
    ["finite_shell_obstruction", "finite_extendable_shell_obstruction"].includes(kind)
    && final?.can_tile === false
  ) {
    counts.extendableShellObstruction += 1;
  } else if (final?.success) {
    counts.shellOneWitness += 1;
    survivors.push({
      id: candidate.id,
      latticePoints: candidate.lattice_points.length,
      vertices: candidate.vertices,
      shellTiles: final.tile_count,
      visitedNodes: final.search_stats?.visited_nodes ?? 0,
      maximumCandidates: final.search_stats?.generic_global_extension_max_candidates ?? 0
    });
  } else if (final?.search_incomplete) {
    counts.incomplete += 1;
    unresolved.push({
      id: candidate.id,
      latticePoints: candidate.lattice_points.length,
      vertices: candidate.vertices,
      bestShellDepth: final?.search_stats?.max_complete_shell_depth ?? 0,
      maximumLiveTiles: final?.search_stats?.max_live_tiles ?? 1,
      visitedNodes: final?.search_stats?.visited_nodes ?? 0,
      terminationReason: final?.search_stats?.termination_reason ?? "bounded_incomplete"
    });
  } else {
    counts.other += 1;
    unresolved.push({
      id: candidate.id,
      latticePoints: candidate.lattice_points.length,
      vertices: candidate.vertices,
      resultKind: final?.result_kind ?? "missing_result",
      evidenceKind: kind
    });
  }
  if ((index + 1) % progressEvery === 0 || index + 1 === candidates.length) {
    process.stderr.write(
      `${index + 1}/${candidates.length}: edge ${counts.localEdgeObstruction}, shell ${counts.extendableShellObstruction}, survivors ${counts.shellOneWitness}, incomplete ${counts.incomplete}\n`
    );
  }
}

const report = {
  schemaVersion: 1,
  kind: "blanco_santos_extendable_shell_one_screen",
  generatedAt: new Date().toISOString(),
  configuration: {
    size,
    source,
    ...(source === "polydb" ? { polyDbStart, polyDbEnd, polyDbPageSize, fetchRetries } : {}),
    parts: urls.map(url => allUrls.indexOf(url) + 1),
    offset,
    maxCandidates: Number.isFinite(maxCandidates) ? maxCandidates : null,
    timeMs,
    nodeLimit,
    orientationGroup: includeMirrors ? "full cubic isometries" : "proper cubic rotations",
    translations: "integer",
    mirrors: includeMirrors,
    globalZeroFacePruning
  },
  sources: sourceRecords,
  screenedCandidates: candidates.length,
  counts,
  survivors,
  unresolved,
  elapsedMs: Math.round(performance.now() - started),
  interpretation: `Local edge and exhausted extendable-shell failures are exact only in the configured face-to-face ${includeMirrors ? "full-cubic-isometry" : "proper-cubic-rotation"} lattice model. A shell-one witness or bounded timeout is not evidence of aperiodicity.`
};
const serialized = `${JSON.stringify(report, null, 2)}\n`;
if (outputFile) await writeFile(outputFile, serialized);
else process.stdout.write(serialized);
