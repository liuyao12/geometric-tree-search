// Free-polycube representatives retained after the deeper 2026-08-20 screen.
// The original four one-sided entries form two enantiomeric pairs. Reflecting
// all of space preserves tiling existence, so one representative per pair is
// sufficient even though reflections remain forbidden as placement moves.

const PERIODIC_P9_43172_TEMPLATE = Object.freeze({
  period_vectors: Object.freeze([[3, 0, 0], [0, 8, 0], [0, 0, 3]]),
  motif: Object.freeze([
    { prototile_idx: 0, orientation_index: 0, translation: [0, 0, 0] },
    { prototile_idx: 0, orientation_index: 3, translation: [0, -6, -2] },
    { prototile_idx: 0, orientation_index: 2, translation: [0, -5, 0] },
    { prototile_idx: 0, orientation_index: 3, translation: [1, 1, 0] },
    { prototile_idx: 0, orientation_index: 0, translation: [1, -1, -2] },
    { prototile_idx: 0, orientation_index: 1, translation: [1, -2, 0] },
    { prototile_idx: 0, orientation_index: 2, translation: [1, -4, -2] },
    { prototile_idx: 0, orientation_index: 1, translation: [0, -3, -2] }
  ].map(entry => Object.freeze({ ...entry, translation: Object.freeze(entry.translation) })))
});

const records = [
  {
    id: "p9-42947",
    survivor_priority: 1,
    voxels: [[0,0,1],[0,1,0],[0,1,1],[0,1,2],[1,0,0],[1,0,1],[1,1,0],[1,2,0],[2,0,1]],
    mirror_equivalent_id: "p9-42969",
    description: "The sole unresolved free-polycube representative from the volume-9 catalogue funnel.",
    screening: {
      status: "inconclusive",
      certificate: null,
      requires_mirrors: false,
      periodic_hnf_max_motif_tiles: 13,
      periodic_hnf_candidates_exhausted: 169511,
      periodic_nodes: 13121513,
      periodic_milliseconds: 614437,
      periodic_hnf_report: "data/polycube-volume9-periodic-through13-2026-08-20.json",
      corona_completed_radius: 4,
      corona_completed_seed: 3,
      corona_completed_nodes: 8042,
      corona_completed_milliseconds: 157,
      corona_completed_placements: 64,
      corona_next_radius: 5,
      corona_next_status: "time_limit",
      corona_next_time_limit_ms: 30000,
      corona_next_nodes: 2574336,
      corona_continuation_states_checked: 7387,
      corona_continuation_states_extended: 0,
      corona_nogood_portfolio_report: "data/polycube-volume9-continuation-nogoods-2026-08-20.json",
      corona_nogood_portfolio_trials: 4,
      corona_nogood_continuation_checks: 54,
      corona_nogood_explained_obstructions: 54,
      corona_nogood_clauses: 6573,
      corona_nogood_prunes: 4949332,
      corona_nogood_radius5_witness: false,
      corona_nogood_outer_exhausted: false
    },
    shell_screening: {
      robust_completed_shell: 4,
      deepest_completed_shell: 4
    }
  },
  {
    id: "p9-43172",
    survivor_priority: null,
    voxels: [[0,0,1],[0,1,0],[0,1,1],[0,1,2],[1,1,0],[1,1,2],[1,2,0],[2,1,0],[2,1,1]],
    mirror_equivalent_id: "p9-43188",
    description: "Volume-9 polycube retained as a regression for an exact eight-copy translational quotient.",
    screening: {
      status: "exact_rejection",
      certificate: "translational",
      requires_mirrors: false,
      motif_tiles: 8,
      period_vectors: PERIODIC_P9_43172_TEMPLATE.period_vectors,
      periodic_template: PERIODIC_P9_43172_TEMPLATE,
      periodic_source: "an exact 8-copy HNF quotient, independently replayed by Cramer's-rule cosets and by the webapp face-pairing verifier",
      periodic_hnf_max_motif_tiles: 8,
      periodic_hnf_candidates_visited: 27380,
      periodic_nodes: 174273,
      periodic_milliseconds: 10558,
      quotient_determinant: 72,
      quotient_cells_verified: 72,
      independent_verifier: "cramers_rule_quotient_partition"
    },
    shell_screening: {
      robust_completed_shell: 4,
      deepest_completed_shell: 4
    }
  }
];

export const POLYCUBE_GCTS_CANDIDATES = Object.freeze(records.map(candidate => Object.freeze({
  ...candidate,
  registry_id: `polycube_${candidate.id.replaceAll("-", "_")}`,
  name: candidate.screening.certificate
    ? `Polycube periodic control ${candidate.id}`
    : `Polycube candidate ${candidate.id}`,
  kind: "polycube_census",
  volume: candidate.voxels.length,
  free_equivalence_class_size: 2,
  survivor_count: candidate.screening.status === "inconclusive" ? 1 : 0,
  screening: Object.freeze(candidate.screening),
  shell_screening: Object.freeze(candidate.shell_screening)
})));
