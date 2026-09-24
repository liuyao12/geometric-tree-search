// One central cube and four coplanar arms of two cubes each.
export const NONACUBE_CROSS = {
  id: 'nonacube_cross',
  name: 'Nonacube cross · two-unit arms',
  voxels: [[0,0,0],[-2,0,0],[-1,0,0],[1,0,0],[2,0,0],[0,-2,0],[0,-1,0],[0,1,0],[0,2,0]],
  note: 'Nine cubes in a planar cross. Checked region exclusions rule out infinite tiling on the integer cubic lattice. Arbitrary Euclidean placements and the exact Heesch number remain unsettled here. A complete first corona is verified.',
  evidence: 'docs/projects/nonacube-region-markings.html'
};
