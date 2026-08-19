import assert from "node:assert/strict";
import {
  canonicalLatticePatchStateKey,
  createTilingStream,
  latticePatchFingerprint,
  PROPER_CUBIC_ROTATIONS,
  tileSpecs
} from "../apps/3d-lattice-tiler/engine.js";

assert.equal(PROPER_CUBIC_ROTATIONS.length, 24);
assert.equal(new Set(PROPER_CUBIC_ROTATIONS.map(matrix => matrix.flat().join(","))).size, 24);
const labeledPointPatch = [
  { prototile_idx: 0, vertices: [[0, 0, 0]] },
  { prototile_idx: 1, vertices: [[1, 0, 0]] },
  { prototile_idx: 2, vertices: [[0, 2, 0]] },
  { prototile_idx: 3, vertices: [[0, 0, 3]] }
];
const rotateAndTranslatePatch = (placements, matrix, translation) => placements.map(placement => ({
  prototile_idx: placement.prototile_idx,
  vertices: placement.vertices.map(vertex => [0, 1, 2].map(row =>
    matrix[row][0] * vertex[0]
      + matrix[row][1] * vertex[1]
      + matrix[row][2] * vertex[2]
      + translation[row]
  ))
}));
const quarterTurn = [[0, -1, 0], [1, 0, 0], [0, 0, 1]];
const rigidCopy = rotateAndTranslatePatch(labeledPointPatch, quarterTurn, [7, -5, 11]).reverse();
const rootedRigidCopy = rotateAndTranslatePatch(labeledPointPatch, quarterTurn, [7, -5, 11]);
const reflectedCopy = rotateAndTranslatePatch(
  labeledPointPatch,
  [[-1, 0, 0], [0, 1, 0], [0, 0, 1]],
  [7, -5, 11]
);
const canonicalPatchKey = canonicalLatticePatchStateKey(labeledPointPatch);
assert.equal(canonicalPatchKey, canonicalLatticePatchStateKey(rigidCopy));
assert.equal(latticePatchFingerprint(canonicalPatchKey), latticePatchFingerprint(canonicalLatticePatchStateKey(rigidCopy)));
assert.notEqual(
  canonicalPatchKey,
  canonicalLatticePatchStateKey(reflectedCopy),
  "proper-rotation canonicalization must not identify a reflected labeled patch"
);
assert.equal(
  canonicalLatticePatchStateKey(labeledPointPatch, { rooted: true }),
  canonicalLatticePatchStateKey(rootedRigidCopy, { rooted: true }),
  "root-preserving rigid copies must share a rooted shell-state key"
);
assert.notEqual(
  canonicalLatticePatchStateKey(labeledPointPatch, { rooted: true }),
  canonicalLatticePatchStateKey(rigidCopy, { rooted: true }),
  "rooted shell-state keys must not forget which placement defines the shell"
);

async function solve(overrides) {
  const config = {
    mode_key: "cube",
    criterion: "count",
    target_val: 24,
    tiling_strategy: "auto",
    move_order: "balanced",
    face_order: "mrv",
    template_preflight: true,
    periodic_tile_count: 2,
    time_limit_ms: 10000,
    ui_yield_interval_ms: 1000,
    ...overrides
  };
  let final = null;
  let latestSnapshot = null;
  let periodicCertificate = null;
  const translationalChecks = [];
  const checkpointFingerprints = [];
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    if (message.periodic_template) periodicCertificate = message.periodic_template;
    if (message.type === "translational_check") {
      translationalChecks.push({ patchSize: message.patch_size, certified: message.certified });
      if (message.patch_fingerprint) checkpointFingerprints.push(message.patch_fingerprint);
    }
    if (message.type === "full_update") latestSnapshot = message;
    if (message.type === "finished") final = message;
  }
  assert.ok(final, "strategy run must emit a terminal result");
  return { final, latestSnapshot, periodicCertificate, translationalChecks, checkpointFingerprints };
}

const translational = await solve({ tiling_strategy: "translational", placement_details: true });
assert.equal(translational.final.success, true);
assert.ok(translational.periodicCertificate, "translational mode requires an exact patch certificate");
assert.equal(translational.final.search_stats.branch_choices_visited, 0);
assert.equal(translational.final.search_stats.growth_axis_rank, 3);
const translationalColorOffset = tileSpecs.TRANSLATIONAL_CELL_COLOR_OFFSET;
const translationalCellColorId = (baseColorId, cell) =>
  translationalColorOffset + baseColorId * 8 + cell.reduce((index, coordinate, axis) =>
    index + (((coordinate % 2) + 2) % 2) * (2 ** axis), 0);
for (const placement of translational.latestSnapshot?.placements ?? []) {
  assert.ok(Number.isInteger(placement.periodic_motif_index));
  assert.ok(Number.isInteger(placement.periodic_base_color_id));
  assert.ok(Array.isArray(placement.periodic_cell));
  assert.equal(
    placement.color_id,
    translationalCellColorId(placement.periodic_base_color_id, placement.periodic_cell),
    "each translation direction must toggle the motif tile's own base RGB color"
  );
}
const rgbChannels = color => [1, 3, 5].map(index => Number.parseInt(color.slice(index, index + 2), 16));
for (let baseColorId = 0; baseColorId < tileSpecs.BASE_COLOR_PALETTE_SIZE; baseColorId++) {
  const variantOffset = translationalColorOffset + baseColorId * 8;
  const baseTranslationColor = rgbChannels(tileSpecs.COLOR_PALETTE[variantOffset]);
  for (let axis = 0; axis < 3; axis++) {
    const shiftedColor = rgbChannels(tileSpecs.COLOR_PALETTE[variantOffset + 2 ** axis]);
    for (let channel = 0; channel < 3; channel++) {
      assert.equal(
        (shiftedColor[channel] - baseTranslationColor[channel] + 256) % 256,
        channel === axis ? 128 : 0,
        `translation axis ${axis} must change only RGB channel ${axis} for base color ${baseColorId}`
      );
    }
  }
}
assert.ok(
  new Set(translational.latestSnapshot.placements.map(placement => placement.color_id)).size >= 4,
  "three-dimensional translational growth must expose multiple directional RGB classes"
);

for (const polycubeLattice of ["fcc", "half"]) {
  const latticeRun = await solve({
    polycube_lattice: polycubeLattice,
    periodic_patch_max_tiles: 4
  });
  assert.equal(latticeRun.final.success, true, `${polycubeLattice} translational growth must be certified`);
  assert.equal(latticeRun.final.search_stats.growth_axis_rank, 3);
}

const noOneTilePatch = await solve({
  mode_key: "tet_oct",
  target_val: 8,
  tiling_strategy: "translational",
  periodic_tile_count: 1
});
assert.equal(noOneTilePatch.final.success, false, "translational mode must not fall back");
assert.equal(noOneTilePatch.final.tile_count, 1);
assert.equal(noOneTilePatch.final.search_stats.branch_choices_visited, 0);

const progressivePatchCheck = await solve({
  mode_key: "tet_oct",
  target_val: 8,
  tiling_strategy: "translational",
  periodic_tile_count: undefined,
  periodic_patch_max_tiles: 4
});
assert.deepEqual(
  progressivePatchCheck.translationalChecks.map(check => check.patchSize),
  [1, 2, 3],
  "translational mode must test candidate patch sizes progressively"
);
assert.equal(progressivePatchCheck.final.success, true);
assert.equal(progressivePatchCheck.periodicCertificate?.motif.length, 3);

const unboundedPatchCheck = await solve({
  mode_key: "census_10_45026",
  target_val: 8,
  tiling_strategy: "translational",
  periodic_patch_unbounded: true,
  periodic_patch_max_tiles: null,
  periodic_motif_node_limit: 1,
  time_limit_ms: 500
});
assert.ok(
  unboundedPatchCheck.translationalChecks.some(check => check.patchSize > 4),
  "uncertified translational search must continue beyond four-tile patches"
);

const isohedral = await solve({
  tiling_strategy: "isohedral",
  target_val: 12
});
assert.equal(isohedral.final.success, true);
assert.equal(isohedral.final.result_kind, "certified_tiling");
assert.equal(isohedral.final.can_tile, true, "isohedral success requires a tile-transitive quotient certificate");
assert.equal(isohedral.final.tiling_evidence?.kind, "isohedral_certificate");
assert.match(isohedral.periodicCertificate?.kind ?? "", /isohedral_periodic_quotient$/);
assert.equal(isohedral.final.search_stats.growth_axis_rank, 3);

const generic = await solve({
  tiling_strategy: "generic",
  target_val: 12
});
assert.equal(generic.final.success, true);
assert.equal(generic.periodicCertificate, null, "generic mode must skip structural fast paths");
assert.ok(generic.final.search_stats.branch_choices_visited > 0);

const genericPatchCertificate = await solve({
  tiling_strategy: "generic",
  target_val: 1,
  template_preflight: false,
  generic_periodic_certificate: true
});
assert.equal(genericPatchCertificate.final.result_kind, "certified_tiling");
assert.equal(genericPatchCertificate.final.can_tile, true);
assert.equal(genericPatchCertificate.final.tiling_evidence?.strategy, "generic");
assert.equal(genericPatchCertificate.final.tiling_evidence?.source, "gcts_target_patch");
assert.equal(genericPatchCertificate.periodicCertificate?.kind, "one_tile_boundary_quotient");
assert.equal(genericPatchCertificate.final.search_stats.generic_periodic_certificate_attempted, true);
assert.equal(genericPatchCertificate.final.search_stats.generic_periodic_certificate_completed, true);
assert.equal(genericPatchCertificate.final.search_stats.generic_periodic_certificate_found, true);

const genericCheckpointCertificate = await solve({
  tiling_strategy: "generic",
  target_val: 20,
  template_preflight: false,
  generic_periodic_certificate: true,
  generic_periodic_certificate_check_new_maximum: true
});
assert.equal(genericCheckpointCertificate.final.result_kind, "certified_tiling");
assert.equal(genericCheckpointCertificate.final.can_tile, true);
assert.equal(genericCheckpointCertificate.final.tile_count, 2);
assert.equal(genericCheckpointCertificate.final.tiling_evidence?.source, "gcts_growth_checkpoint");
assert.deepEqual(
  genericCheckpointCertificate.final.search_stats.generic_periodic_certificate_check_sizes,
  [2],
  "a smaller exact quotient must be detected before an arbitrary larger display target"
);

const internalPeriodControl = await solve({
  mode_key: "cube",
  custom_system: {
    name: "Internal-period positive control 10_24775",
    figure_refs: [],
    polycubes: [],
    polyhedra: [{
      name: "Candidate 10_24775",
      vertices: [[-1,-1,0],[-1,1,1],[0,0,2],[0,1,-1],[1,0,0],[1,2,1]]
    }],
    polycube_lattice: "z3"
  },
  tiling_strategy: "free_range",
  move_order: "balanced",
  target_val: 60,
  template_preflight: false,
  generic_periodic_certificate: true,
  generic_periodic_certificate_time_limit_ms: 10000,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 2,
  generic_failure_memo: true,
  include_mirrors: false,
  snapshot_every: 1,
  placement_details: true,
  time_limit_ms: 10000,
  node_limit: 1000
});
assert.equal(internalPeriodControl.final.result_kind, "certified_tiling");
assert.equal(internalPeriodControl.periodicCertificate?.motif.length, 3);
assert.equal(internalPeriodControl.final.search_stats.generic_periodic_internal_motif_attempted, true);
assert.equal(internalPeriodControl.final.search_stats.generic_periodic_internal_motif_found, true);
assert.equal(internalPeriodControl.final.search_stats.generic_periodic_internal_motif_bases_tested, 1);

const exactNodeBudget = await solve({
  mode_key: "cube",
  tiling_strategy: "free_range",
  target_val: 6,
  template_preflight: false,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_connected_patch_enumeration: true,
  node_limit: 6,
  time_limit_ms: 10000
});
assert.equal(exactNodeBudget.final.result_kind, "patch_found");
assert.equal(exactNodeBudget.final.tile_count, 6);
assert.equal(exactNodeBudget.final.search_stats.visited_nodes, 6);
assert.equal(exactNodeBudget.final.search_stats.generic_connected_patch_enumeration, true);
assert.ok(exactNodeBudget.final.search_stats.generic_connected_patch_candidate_states > 0);
assert.ok(exactNodeBudget.final.search_stats.generic_connected_patch_max_candidates > 6);

const exactCubeShell = await solve({
  mode_key: "cube",
  criterion: "shell",
  target_val: 1,
  tiling_strategy: "free_range",
  move_order: "shell",
  template_preflight: false,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_complete_shell_enumeration: true,
  generic_failure_memo_symmetry: "rigid",
  node_limit: 100,
  time_limit_ms: 10000
});
assert.equal(exactCubeShell.final.result_kind, "patch_found");
assert.equal(exactCubeShell.final.tile_count, 7, "the first cube shell is the six face-neighbors of the root");
assert.equal(exactCubeShell.final.tiling_evidence?.kind, "finite_complete_shell");
assert.equal(exactCubeShell.final.search_stats.generic_complete_shell_enumeration, true);
assert.equal(
  exactCubeShell.final.search_stats.generic_failure_memo_key_equivalence,
  "rooted_orientation_preserving_cubic_rigid_motion"
);
assert.ok(exactCubeShell.final.search_stats.max_complete_shell_depth >= 1);

const unattachedScalenePair = {
  name: "No proper-lattice face attachment",
  polycubes: [],
  polyhedra: ["A", "B"].map(name => ({
    name,
    vertices: [[0, 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3]]
  }))
};
const completeObstruction = await solve({
  mode_key: "cube",
  custom_system: unattachedScalenePair,
  tiling_strategy: "free_range",
  move_order: "global",
  target_val: 2,
  template_preflight: false,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_connected_patch_enumeration: true,
  node_limit: 100
});
assert.equal(completeObstruction.final.result_kind, "no_tiling");
assert.equal(completeObstruction.final.tiling_evidence?.kind, "finite_patch_obstruction");
assert.match(completeObstruction.final.tiling_evidence?.note ?? "", /global face-extension search/);

const completeShellObstruction = await solve({
  mode_key: "cube",
  custom_system: unattachedScalenePair,
  criterion: "shell",
  target_val: 1,
  tiling_strategy: "free_range",
  move_order: "shell",
  template_preflight: false,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_complete_shell_enumeration: true,
  node_limit: 100
});
assert.equal(completeShellObstruction.final.result_kind, "no_tiling");
assert.equal(completeShellObstruction.final.can_tile, false);
assert.equal(completeShellObstruction.final.tiling_evidence?.kind, "finite_shell_obstruction");
assert.equal(completeShellObstruction.final.tiling_evidence?.target_shell_depth, 1);

const heuristicExhaustion = await solve({
  mode_key: "cube",
  custom_system: unattachedScalenePair,
  tiling_strategy: "free_range",
  move_order: "balanced",
  target_val: 2,
  template_preflight: false,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_connected_patch_enumeration: false,
  node_limit: 100
});
assert.notEqual(heuristicExhaustion.final.result_kind, "no_tiling");
assert.equal(heuristicExhaustion.final.tiling_evidence?.kind ?? null, null);

const candidate1026470System = {
  name: "Candidate 10_26470 checkpoint certificate",
  figure_refs: [],
  polycubes: [],
  polyhedra: [{
    name: "Candidate 10_26470",
    vertices: [[-1,0,0],[-1,0,1],[0,-1,0],[0,1,0],[0,1,2],[1,0,0],[1,0,1]]
  }]
};

const checkpointTimeout = await solve({
  mode_key: "cube",
  custom_system: candidate1026470System,
  tiling_strategy: "generic",
  target_val: 40,
  template_preflight: false,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_failure_memo: true,
  generic_failure_memo_symmetry: "fixed",
  seeded_tie_breaks: true,
  random_seed: 1,
  node_limit: 5000,
  time_limit_ms: 10000,
  generic_periodic_certificate: true,
  generic_periodic_certificate_check_new_maximum: true,
  generic_periodic_certificate_checkpoint_min_tiles: 40,
  generic_periodic_certificate_time_limit_ms: 1
});
assert.equal(checkpointTimeout.final.success, true, "an optional certificate timeout must not erase a finite witness");
assert.equal(checkpointTimeout.final.result_kind, "patch_found");
assert.equal(checkpointTimeout.final.search_incomplete, false);
assert.equal(checkpointTimeout.final.search_stats.generic_periodic_certificate_target_timed_out, true);
assert.equal(checkpointTimeout.final.search_stats.generic_periodic_certificate_target_found, false);
assert.equal(checkpointTimeout.final.search_stats.generic_failure_memo_key_equivalence, "fixed_frame");

const checkpointCandidateCertificate = await solve({
  mode_key: "cube",
  custom_system: candidate1026470System,
  tiling_strategy: "generic",
  target_val: 40,
  template_preflight: false,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_failure_memo: true,
  generic_failure_memo_symmetry: "rigid",
  seeded_tie_breaks: true,
  random_seed: 2,
  node_limit: 500,
  generic_periodic_certificate: true,
  generic_periodic_certificate_check_new_maximum: true,
  generic_periodic_certificate_check_distinct_patches: true,
  generic_periodic_certificate_checkpoint_sampling_policy: "hybrid",
  generic_periodic_certificate_checkpoint_sampling_prefix: 4,
  generic_periodic_certificate_checkpoint_sampling_stride: 16,
  generic_periodic_certificate_time_limit_ms: 5000
});
assert.equal(checkpointCandidateCertificate.final.result_kind, "certified_tiling");
assert.equal(checkpointCandidateCertificate.final.tile_count, 8);
assert.equal(checkpointCandidateCertificate.final.tiling_evidence?.certificate_kind, "8_tile_boundary_quotient");
assert.deepEqual(checkpointCandidateCertificate.final.tiling_evidence?.period_vectors, [
  [-2, -2, 0],
  [-2, 0, 2],
  [-2, 2, 0]
]);
assert.equal(
  checkpointCandidateCertificate.final.tiling_evidence?.periodic_template?.proof?.lattice_determinant,
  16
);
assert.equal(
  checkpointCandidateCertificate.final.search_stats.generic_failure_memo_key_equivalence,
  "orientation_preserving_cubic_rigid_motion"
);

const candidate1016113System = {
  name: "Candidate 10_16113 distinct checkpoint regression",
  figure_refs: [],
  polycubes: [],
  polyhedra: [{
    name: "Candidate 10_16113",
    vertices: [[0,1,0],[0,2,1],[1,0,-1],[1,0,2],[1,1,-1],[2,1,0]]
  }]
};
const distinctCheckpointCap = await solve({
  mode_key: "cube",
  custom_system: candidate1016113System,
  tiling_strategy: "generic",
  target_val: 40,
  template_preflight: false,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_failure_memo: true,
  seeded_tie_breaks: true,
  random_seed: 1,
  node_limit: 100,
  time_limit_ms: 5000,
  generic_periodic_certificate: true,
  generic_periodic_certificate_check_new_maximum: true,
  generic_periodic_certificate_check_distinct_patches: true,
  generic_periodic_certificate_checkpoint_max_checks_per_size: 3,
  generic_periodic_certificate_checkpoint_max_total_checks: 10,
  generic_periodic_certificate_checkpoint_total_time_limit_ms: 5000,
  generic_periodic_certificate_time_limit_ms: 500
});
const distinctCheckSizes = distinctCheckpointCap.final.search_stats.generic_periodic_certificate_check_sizes;
assert.equal(distinctCheckpointCap.final.search_stats.generic_periodic_certificate_distinct_patch_mode, true);
assert.equal(
  distinctCheckpointCap.final.search_stats.generic_failure_memo_key_equivalence,
  "fixed_frame"
);
assert.equal(distinctCheckpointCap.final.search_stats.generic_periodic_certificate_checks_attempted, 10);
assert.ok(
  new Set(distinctCheckSizes).size < distinctCheckSizes.length,
  "distinct branch patches at the same size must receive separate exact checks"
);
assert.ok(distinctCheckpointCap.final.search_stats.generic_periodic_certificate_total_cap_skips > 0);
assert.equal(distinctCheckpointCap.final.search_incomplete, true);

const distinctCheckpointPerSizeCap = await solve({
  mode_key: "cube",
  custom_system: candidate1016113System,
  tiling_strategy: "generic",
  target_val: 40,
  template_preflight: false,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_failure_memo: true,
  seeded_tie_breaks: true,
  random_seed: 1,
  node_limit: 100,
  time_limit_ms: 5000,
  generic_periodic_certificate: true,
  generic_periodic_certificate_check_new_maximum: true,
  generic_periodic_certificate_check_distinct_patches: true,
  generic_periodic_certificate_checkpoint_max_checks_per_size: 1,
  generic_periodic_certificate_checkpoint_max_total_checks: 100,
  generic_periodic_certificate_checkpoint_total_time_limit_ms: 5000,
  generic_periodic_certificate_time_limit_ms: 500
});
const perSizeCheckSizes = distinctCheckpointPerSizeCap.final.search_stats.generic_periodic_certificate_check_sizes;
assert.equal(new Set(perSizeCheckSizes).size, perSizeCheckSizes.length);
assert.ok(distinctCheckpointPerSizeCap.final.search_stats.generic_periodic_certificate_per_size_cap_skips > 0);

const spreadCheckpointConfig = {
  mode_key: "cube",
  custom_system: candidate1016113System,
  tiling_strategy: "generic",
  target_val: 60,
  template_preflight: false,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_failure_memo: true,
  seeded_tie_breaks: true,
  random_seed: 1,
  node_limit: 100,
  time_limit_ms: 5000,
  generic_periodic_certificate: true,
  generic_periodic_certificate_check_new_maximum: true,
  generic_periodic_certificate_check_distinct_patches: true,
  generic_periodic_certificate_checkpoint_sampling_policy: "spread",
  generic_periodic_certificate_checkpoint_sampling_stride: 8,
  generic_periodic_certificate_checkpoint_max_checks_per_size: 3,
  generic_periodic_certificate_checkpoint_max_total_checks: 100,
  generic_periodic_certificate_checkpoint_total_time_limit_ms: 5000,
  generic_periodic_certificate_time_limit_ms: 500
};
const spreadCheckpoint = await solve(spreadCheckpointConfig);
const spreadCheckpointReplay = await solve(spreadCheckpointConfig);
const spreadStats = spreadCheckpoint.final.search_stats;
const spreadReplayStats = spreadCheckpointReplay.final.search_stats;
assert.equal(spreadStats.generic_periodic_certificate_checkpoint_sampling_policy, "spread");
assert.equal(spreadStats.generic_periodic_certificate_checkpoint_sampling_stride, 8);
assert.ok(
  spreadStats.generic_periodic_certificate_checkpoint_eligible_states
  > spreadStats.generic_periodic_certificate_checks_attempted
);
assert.ok(spreadStats.generic_periodic_certificate_checkpoint_sampling_skips > 0);
assert.deepEqual(
  {
    sizes: spreadStats.generic_periodic_certificate_check_sizes,
    eligible: spreadStats.generic_periodic_certificate_checkpoint_eligible_states,
    samplingSkips: spreadStats.generic_periodic_certificate_checkpoint_sampling_skips
  },
  {
    sizes: spreadReplayStats.generic_periodic_certificate_check_sizes,
    eligible: spreadReplayStats.generic_periodic_certificate_checkpoint_eligible_states,
    samplingSkips: spreadReplayStats.generic_periodic_certificate_checkpoint_sampling_skips
  },
  "spread sampling must be exactly replayable"
);
assert.ok(spreadCheckpoint.checkpointFingerprints.every(value => /^[0-9a-f]{32}$/.test(value)));
assert.equal(
  new Set(spreadCheckpoint.checkpointFingerprints).size,
  spreadCheckpoint.checkpointFingerprints.length,
  "one path must never check the same patch fingerprint twice"
);
assert.deepEqual(
  spreadCheckpoint.checkpointFingerprints,
  spreadCheckpointReplay.checkpointFingerprints,
  "checkpoint fingerprints must be stable across exact replay"
);

const hybridCheckpoint = await solve({
  ...spreadCheckpointConfig,
  generic_periodic_certificate_checkpoint_sampling_policy: "hybrid",
  generic_periodic_certificate_checkpoint_sampling_prefix: 4,
  generic_periodic_certificate_checkpoint_max_checks_per_size: 7,
  generic_periodic_certificate_checkpoint_max_total_checks: 280
});
const hybridStats = hybridCheckpoint.final.search_stats;
assert.equal(hybridStats.generic_periodic_certificate_checkpoint_sampling_policy, "hybrid");
assert.equal(hybridStats.generic_periodic_certificate_checkpoint_sampling_prefix, 4);
assert.ok(hybridStats.generic_periodic_certificate_checkpoint_sampling_skips > 0);
assert.ok(
  hybridStats.generic_periodic_certificate_checks_attempted
  > spreadStats.generic_periodic_certificate_checks_attempted,
  "hybrid sampling must retain the prefix sample while adding later branch states"
);

const distinctCheckpointTimeBudget = await solve({
  mode_key: "cube",
  custom_system: candidate1016113System,
  tiling_strategy: "generic",
  target_val: 40,
  template_preflight: false,
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_failure_memo: true,
  seeded_tie_breaks: true,
  random_seed: 1,
  node_limit: 100,
  time_limit_ms: 5000,
  generic_periodic_certificate: true,
  generic_periodic_certificate_check_new_maximum: true,
  generic_periodic_certificate_check_distinct_patches: true,
  generic_periodic_certificate_checkpoint_max_checks_per_size: 10,
  generic_periodic_certificate_checkpoint_max_total_checks: 100,
  generic_periodic_certificate_checkpoint_total_time_limit_ms: 1,
  generic_periodic_certificate_time_limit_ms: 500
});
assert.equal(
  distinctCheckpointTimeBudget.final.search_stats.generic_periodic_certificate_checkpoint_time_budget_exhausted,
  true
);
assert.ok(
  distinctCheckpointTimeBudget.final.search_stats.generic_periodic_certificate_checkpoint_time_budget_skips > 0
);
assert.equal(
  distinctCheckpointTimeBudget.final.result_kind,
  "search_incomplete",
  "exhausting an optional checkpoint budget must not create a false tiling conclusion"
);

const seededPatch = async seed => solve({
  tiling_strategy: "generic",
  target_val: 20,
  template_preflight: false,
  placement_details: true,
  random_seed: seed,
  seeded_tie_breaks: true
});
const seededPatchA = await seededPatch(17);
const seededPatchReplay = await seededPatch(17);
const seededPatchB = await seededPatch(18);
const placementWitness = run => run.latestSnapshot.placements
  .map(placement => `${placement.orientation_id}@${placement.translation.join(",")}`)
  .sort();
assert.deepEqual(
  placementWitness(seededPatchA),
  placementWitness(seededPatchReplay),
  "seeded balanced tie-breaking must replay exactly for the same seed"
);
assert.notDeepEqual(
  placementWitness(seededPatchA),
  placementWitness(seededPatchB),
  "different seeds must diversify equally ranked balanced-search patches"
);
assert.equal(seededPatchA.final.search_stats.seeded_tie_breaks, true);

const freestyle = await solve({
  tiling_strategy: "freestyle",
  target_val: 12
});
assert.equal(freestyle.final.success, true);
assert.equal(freestyle.final.result_kind, "patch_found");
assert.equal(freestyle.final.search_stats.tiling_strategy, "generic");

const freeRange = await solve({
  tiling_strategy: "free_range",
  move_order: "no_brainer",
  greedy_no_backtrack: false,
  template_preflight: false,
  target_val: 12
});
assert.equal(freeRange.final.success, true);
assert.equal(freeRange.final.search_stats.tiling_strategy, "generic");
assert.ok(freeRange.final.search_stats.branch_choices_visited > 0);

const freeRangeBacktracking = await solve({
  mode_key: "gyrobifastigium",
  tiling_strategy: "free_range",
  move_order: "no_brainer",
  greedy_no_backtrack: false,
  template_preflight: false,
  target_val: 8,
  time_limit_ms: 5000
});
assert.equal(freeRangeBacktracking.final.success, true);
assert.ok(freeRangeBacktracking.final.search_stats.forced_total > 0, "Free-range must apply forced moves first");
assert.equal(
  freeRangeBacktracking.final.search_stats.backtracking_enabled,
  true,
  "Free-range must retain branch recovery even when the first branch happens to succeed"
);

const honestBestEffortLimit = await solve({
  mode_key: "census_10_45026",
  tiling_strategy: "free_range",
  move_order: "balanced",
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  template_preflight: false,
  target_val: 50,
  time_limit_ms: 50
});
assert.equal(honestBestEffortLimit.final.success, false);
assert.equal(honestBestEffortLimit.final.search_incomplete, true);
assert.equal(
  honestBestEffortLimit.final.search_stats.termination_reason,
  "time_limit",
  "retaining the best patch must not roll terminal stop diagnostics back to an earlier snapshot"
);

for (const [mode_key, polycube_lattice] of [
  ["letter_o", "fcc"],
  ["letter_o", "half"],
  ["2_cross", "fcc"],
  ["2_cross", "half"]
]) {
  const refined = await solve({
    mode_key,
    polycube_lattice,
    periodic_patch_max_tiles: 4,
    periodic_template_max_volume: undefined
  });
  assert.equal(
    refined.final.result_kind,
    "certified_tiling",
    `${mode_key} must be checked on the ${polycube_lattice} refined lattice`
  );
}

const certificateBeforeDisplayTarget = await solve({
  mode_key: "fcc_pure",
  target_val: 20,
  tiling_strategy: "translational",
  periodic_patch_max_tiles: 4
});
assert.equal(certificateBeforeDisplayTarget.final.result_kind, "certified_tiling");
assert.equal(
  certificateBeforeDisplayTarget.final.success,
  true,
  "an exact infinite-tiling certificate must count as success even if its preview is shorter than the display target"
);

const retainedCertifiedPreview = await solve({
  mode_key: "cube",
  criterion: "layer",
  target_val: 50,
  tiling_strategy: "translational",
  periodic_patch_max_tiles: 4,
  safety_max_tiles: 2,
  snapshot_every: 0
});
assert.equal(retainedCertifiedPreview.final.result_kind, "certified_tiling");
assert.equal(retainedCertifiedPreview.final.tile_count, 2);
assert.equal(
  retainedCertifiedPreview.latestSnapshot?.tile_count,
  2,
  "the terminal snapshot must retain the best displayed patch after certified growth rolls back"
);

const reflectionHoneycomb = await solve({
  mode_key: "tetragonal_disphenoid",
  criterion: "count",
  target_val: 40,
  tiling_strategy: "isohedral",
  include_mirrors: true
});
assert.equal(reflectionHoneycomb.final.result_kind, "certified_tiling");
assert.equal(reflectionHoneycomb.final.success, true);
assert.equal(reflectionHoneycomb.final.search_stats.growth_axis_rank, 3);
assert.ok(
  reflectionHoneycomb.final.search_stats.reflection_continuations_seen > 0,
  "isohedral mode must retain face-reflection continuations for Coxeter-style honeycombs"
);

for (const mode_key of ["corner_tetra", "big_corner_tetra"]) {
  const obstruction = await solve({
    mode_key,
    criterion: "layer",
    target_val: 1,
    tiling_strategy: "freestyle",
    include_mirrors: true
  });
  assert.equal(obstruction.final.result_kind, "no_tiling");
  assert.equal(obstruction.final.can_tile, false);
  assert.equal(obstruction.final.tiling_evidence?.kind, "local_edge_obstruction");
}

console.log("3D strategy regressions passed", {
  translational_tiles: translational.final.tile_count,
  isohedral_tiles: isohedral.final.tile_count,
  generic_choices: generic.final.search_stats.branch_choices_visited,
  rejected_uncertified_tiles: noOneTilePatch.final.tile_count
});
