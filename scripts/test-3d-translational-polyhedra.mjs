import assert from "node:assert/strict";
import { performance } from "node:perf_hooks";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const cases = [
  { mode: "rhombic", target: 500 },
  { mode: "trunc_oct", target: 500 },
  { mode: "hex_prism", target: 500 }
];

async function run({ mode, target }) {
  const config = {
    mode_key: mode,
    custom_system: {
      name: `Certified translational ${mode}`,
      figure_refs: [`${mode}::0`],
      polycubes: [],
      polyhedra: [],
      polycube_lattice: "z3"
    },
    polycube_lattice: "z3",
    criterion: "count",
    target_val: target,
    exhaustive: false,
    include_mirrors: false,
    snapshot_every: 1000,
    placement_details: true,
    face_order: "mrv",
    move_order: "rl",
    agent_exhaustive: true,
    branch_cap: null,
    node_limit: 10000,
    candidate_cap: null,
    time_limit_ms: 30000,
    ui_yield_interval_ms: 1000,
    template_preflight: true,
    periodic_tile_count: 2
  };

  let certificate = null;
  let prototileInfo = null;
  let finalSnapshot = null;
  let finished = null;
  const started = performance.now();
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    if (message.type === "prototile_info") prototileInfo = message;
    if (message.periodic_template?.kind === "one_tile_translational_lattice_polyhedron") {
      certificate = message.periodic_template;
    }
    if (message.type === "full_update") finalSnapshot = message;
    if (message.type === "finished") finished = message;
  }
  const milliseconds = Math.round(performance.now() - started);

  assert.ok(certificate, `${mode} must expose its translational lattice certificate`);
  assert.equal(certificate.proof.method, "paired_facets_integral_lattice_and_equal_covolume");
  assert.equal(certificate.proof.face_pairs.length * 2, prototileInfo.tiles[0].faces.length);
  assert.ok(
    Math.abs(certificate.proof.polyhedron_volume - certificate.proof.lattice_determinant) <= 1e-9
  );
  assert.equal(certificate.motif.length, 1);
  assert.ok(finished?.success, `${mode} must reach ${target} tiles`);
  assert.equal(finalSnapshot?.placements?.length, target);
  assert.equal(finished.search_stats.branch_choices_visited, 0);
  assert.equal(finished.search_stats.backtracks, 0);
  assert.equal(finished.search_stats.growth_axis_rank, 3);
  assert.ok(finished.search_stats.growth_isotropy >= 0.75);

  return {
    mode,
    tiles: target,
    milliseconds,
    facePairs: certificate.proof.face_pairs.length,
    cellVolume: certificate.cell_volume,
    spans: finished.search_stats.growth_spans,
    isotropy: finished.search_stats.growth_isotropy
  };
}

const results = [];
for (const testCase of cases) results.push(await run(testCase));
console.log("3D translational lattice-polyhedron regressions passed", results);
