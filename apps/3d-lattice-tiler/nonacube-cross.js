// One central cube and four coplanar arms of two cubes each.
export const NONACUBE_CROSS = {
  id: 'nonacube_cross',
  name: 'Nonacube cross · two-unit arms',
  voxels: [[0,0,0],[-2,0,0],[-1,0,0],[1,0,0],[2,0,0],[0,-2,0],[0,-1,0],[0,1,0],[0,2,0]],
  note: 'Nine cubes in a planar cross. Exactly one complete lattice corona is possible: a first corona is verified and a checked SAT proof rules out two. Integer translations, cubic rotations, full face/edge/vertex surrounds; no topological-ball requirement. Watch the complete recorded search in the evidence viewer.',
  evidence: 'docs/projects/nonacube-search-tree.html'
};
