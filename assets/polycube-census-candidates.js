// Volume-9 one-sided polycubes retained after the 2026-08-20 certificate funnel.
// Each entry exhausts every HNF periodic quotient with at most six tile copies
// under proper cubic rotations, survives an exact radius-3 corona, and leaves
// the radius-4 exact-cover search incomplete at the recorded bound. These are
// GCTS stress candidates, not aperiodicity certificates.
export const POLYCUBE_GCTS_CANDIDATES = Object.freeze([
  {
    id: "p9-42947", survivor_priority: 1,
    voxels: [[0,0,1],[0,1,0],[0,1,1],[0,1,2],[1,0,0],[1,0,1],[1,1,0],[1,2,0],[2,0,1]],
    periodic_nodes: 73056, periodic_milliseconds: 5101,
    corona4_nodes: 22218
  },
  {
    id: "p9-42969", survivor_priority: 2,
    voxels: [[0,0,1],[0,1,0],[0,1,1],[0,1,2],[1,0,1],[1,0,2],[1,1,2],[1,2,2],[2,0,1]],
    periodic_nodes: 73243, periodic_milliseconds: 5042,
    corona4_nodes: 19494
  },
  {
    id: "p9-43172", survivor_priority: 3,
    voxels: [[0,0,1],[0,1,0],[0,1,1],[0,1,2],[1,1,0],[1,1,2],[1,2,0],[2,1,0],[2,1,1]],
    periodic_nodes: 72247, periodic_milliseconds: 7072,
    corona4_nodes: 11766
  },
  {
    id: "p9-43188", survivor_priority: 4,
    voxels: [[0,0,1],[0,1,0],[0,1,1],[0,1,2],[1,1,0],[1,1,2],[1,2,2],[2,1,1],[2,1,2]],
    periodic_nodes: 72211, periodic_milliseconds: 7096,
    corona4_nodes: 18291
  }
].map(candidate => Object.freeze({
  ...candidate,
  registry_id: `polycube_${candidate.id.replaceAll("-", "_")}`,
  name: `Polycube candidate ${candidate.id}`,
  kind: "polycube_census",
  volume: candidate.voxels.length,
  survivor_count: 4,
  description: "Nonplanar volume-9 polycube retained for deeper GCTS screening.",
  screening: Object.freeze({
    status: "inconclusive",
    certificate: null,
    requires_mirrors: false,
    periodic_hnf_max_motif_tiles: 6,
    periodic_hnf_candidates_exhausted: 19170,
    periodic_nodes: candidate.periodic_nodes,
    periodic_milliseconds: candidate.periodic_milliseconds,
    corona_completed_radius: 3,
    corona_next_radius: 4,
    corona_next_status: "time_limit",
    corona_next_time_limit_ms: 2000,
    corona_next_nodes: candidate.corona4_nodes
  }),
  shell_screening: Object.freeze({
    robust_completed_shell: 3,
    deepest_completed_shell: 3
  })
})));
