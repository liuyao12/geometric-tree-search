import assert from "node:assert/strict";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const cases = [
  { mode: "letter_o", target: 200, minimumIsotropy: 0.75, periodic: true },
  { mode: "2_cross", target: 200, minimumIsotropy: 0.75, periodic: true },
  { mode: "1_cross", target: 20, minimumIsotropy: 0.75, periodic: true },
  { mode: "cube", target: 40, minimumIsotropy: 0.75, periodic: true },
  { mode: "cube", target: 20, minimumIsotropy: 0.75, periodic: true, periodicTileCount: 1 },
  { mode: "cube", target: 20, minimumIsotropy: 0.75, periodic: true, periodicTileCount: 3 },
  { mode: "cube", target: 20, minimumIsotropy: 0.75, periodic: true, periodicTileCount: 4 },
  { mode: "rhombic", target: 20, minimumIsotropy: 0.75 },
  { mode: "trunc_oct", target: 20, minimumIsotropy: 0.75 },
  { mode: "hex_prism", target: 20, minimumIsotropy: 0.75 }
];

async function run({ mode, target, minimumIsotropy, periodic = false, periodicTileCount = 2 }) {
  const config = {
    mode_key: mode,
    custom_system: {
      name: `Standalone balanced-growth ${mode}`,
      figure_refs: [`${mode}::0`],
      polycubes: [],
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
    periodic_tile_count: periodicTileCount
  };

  let finalSnapshot = null;
  let finished = null;
  let periodicCertificate = null;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    if (message.type === "full_update") finalSnapshot = message;
    if (message.periodic_template?.kind) periodicCertificate = message.periodic_template;
    if (message.type === "finished") finished = message;
  }

  assert.ok(finished?.success, `${mode} must reach ${target} tiles`);
  assert.equal(finalSnapshot?.placements?.length, target);
  if (periodic) {
    assert.ok(periodicCertificate, `${mode} must expose its exact periodic-cell certificate`);
    assert.equal(
      periodicCertificate.cell_volume,
      periodicCertificate.tile_volume * periodicCertificate.motif.length,
      `${mode} periodic quotient must have neither gaps nor overlaps`
    );
    assert.equal(
      finished.search_stats.forced_total,
      target - 1,
      `${mode} certified continuation must be one uninterrupted forced cascade`
    );
  }

  const centers = finalSnapshot.placements.map(placement => placement.center);
  const spans = [0, 1, 2].map(axis =>
    Math.max(...centers.map(center => center[axis]))
    - Math.min(...centers.map(center => center[axis]))
  );
  const isotropy = Math.min(...spans) / Math.max(...spans);
  assert.ok(spans.every(span => span > 0), `${mode} must grow in all three directions`);
  assert.ok(
    isotropy >= minimumIsotropy,
    `${mode} center-span isotropy ${isotropy} must be at least ${minimumIsotropy}`
  );
  assert.equal(finished.search_stats.branch_choices_visited, 0);
  assert.equal(finished.search_stats.backtracks, 0);
  assert.equal(finished.search_stats.marking_observed_failures, 0, "standalone growth installs no GCTS plugin");

  return {
    mode,
    tiles: target,
    spans,
    isotropy,
    periodicCellVolume: periodicCertificate?.cell_volume ?? null
  };
}

const results = [];
for (const testCase of cases) results.push(await run(testCase));
console.log("3D standalone balanced-growth regressions passed", results);
