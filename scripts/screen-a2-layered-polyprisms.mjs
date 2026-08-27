import { appendFile, readFile, writeFile } from "node:fs/promises";
import { enumerateA2LayeredPolyprisms } from "../assets/a2-layered-polyprisms.js";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const readArg = (name, fallback) => {
  const prefix = `--${name}=`;
  const value = process.argv.find(argument => argument.startsWith(prefix))?.slice(prefix.length);
  return value === undefined ? fallback : value;
};
const size = Math.max(3, Number(readArg("size", 5)) || 5);
const offset = Math.max(0, Number(readArg("offset", 0)) || 0);
const limit = Math.max(1, Number(readArg("limit", Number.POSITIVE_INFINITY)) || Number.POSITIVE_INFINITY);
const timeMs = Math.max(50, Number(readArg("time-ms", 1500)) || 1500);
const motifTiles = Math.max(1, Number(readArg("motif-tiles", 6)) || 6);
const output = readArg("output", `data/a2-layered-size${size}-screen.ndjson`);
const input = readArg("unresolved-from", null);
const completeCensus = enumerateA2LayeredPolyprisms({ size });
const censusIndex = new Map(completeCensus.map((candidate, index) => [candidate.key, index]));
let census = completeCensus;
if (input) {
  const prior = (await readFile(input, "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);
  const unresolvedKeys = new Set(prior.filter(record => record.classification === "unresolved").map(record => record.key));
  census = census.filter(candidate => unresolvedKeys.has(candidate.key));
}
const candidates = census.slice(offset, offset + limit);

await writeFile(output, "", "utf8");
const run = async (candidate, strategy) => {
  const config = {
    mode_key: "cube",
    custom_system: {
      name: `A2 layered ${size}:${candidate.key}`,
      a2_layered_polyprisms: [{ name: `A2-${size}`, cells: candidate.cells }]
    },
    criterion: "count",
    target_val: 36,
    tiling_strategy: strategy,
    include_mirrors: false,
    template_preflight: true,
    periodic_tile_count: motifTiles,
    periodic_stop_at_growth_goal: true,
    exhaustive: false,
    branch_cap: null,
    candidate_cap: null,
    node_limit: 250000,
    time_limit_ms: timeMs,
    snapshot_every: 0,
    ui_yield_interval_ms: 1000,
    placement_details: false
  };
  let finished = null;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    if (message.type === "finished") finished = message;
  }
  return {
    success: !!finished?.success,
    tile_count: finished?.tile_count ?? 0,
    can_tile: finished?.can_tile ?? null,
    result_kind: finished?.result_kind ?? null,
    certificate: finished?.tiling_evidence?.certificate_kind ?? null,
    motif_tiles: finished?.tiling_evidence?.motif_tile_count ?? null,
    search_incomplete: !!finished?.search_incomplete,
    termination_reason: finished?.termination_reason ?? finished?.reason ?? null,
    nodes: finished?.search_stats?.nodes ?? finished?.search_stats?.search_nodes ?? null,
    backtracks: finished?.search_stats?.backtracks ?? null,
    elapsed_ms: finished?.elapsed_ms ?? null
  };
};

const summary = { size, total: candidates.length, periodic: 0, unresolved: 0, rejected: 0 };
for (let index = 0; index < candidates.length; index += 1) {
  const candidate = candidates[index];
  const translational = await run(candidate, "translational");
  const isohedral = translational.can_tile === true ? null : await run(candidate, "isohedral");
  const certified = [translational, isohedral].find(result => result?.can_tile === true);
  const rejected = [translational, isohedral].find(result => result?.can_tile === false);
  const classification = certified ? "periodic" : rejected ? "rejected" : "unresolved";
  summary[classification] += 1;
  const record = {
    id: `a2lp_${size}_${String(censusIndex.get(candidate.key)).padStart(5, "0")}`,
    size,
    key: candidate.key,
    cells: candidate.cells,
    classification,
    translational,
    isohedral
  };
  await appendFile(output, `${JSON.stringify(record)}\n`, "utf8");
  process.stdout.write(`${index + 1}/${candidates.length} ${record.id} ${classification}`
    + `${certified ? ` ${certified.certificate ?? "certificate"}` : ""}\n`);
}
console.log(JSON.stringify({ ...summary, output }, null, 2));
