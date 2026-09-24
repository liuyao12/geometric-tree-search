// One central cube and four coplanar arms of two cubes each.
export const NONACUBE_CROSS = {
  id: 'nonacube_cross',
  name: 'Nonacube cross · two-unit arms',
  voxels: [[0,0,0],[-2,0,0],[-1,0,0],[1,0,0],[2,0,0],[0,-2,0],[0,-1,0],[0,1,0],[0,2,0]],
  note: 'Nine cubes in a planar cross. Space tiling and the exact Heesch number are unresolved here. A complete surrounding layer has been independently verified. Uses exact voxel centers and corners; all three spatial orientations are allowed.',
  evidence: 'docs/projects/nonacube-forbidden-pair.html'
};
