import {SparseA2Marking} from './a2-tiling-engine.js?v=point-base-adjacency';
import {failureSupport} from './failure-rank3-data.js';

export function failureExtent(setId) {
  if (!Object.hasOwn(failureSupport, setId)) throw new RangeError('Unsupported tile set');
  return Math.max(...failureSupport[setId].map(row => row[5]));
}

export function createFailureMarking(setId, extent = failureExtent(setId)) {
  if (!Object.hasOwn(failureSupport, setId) || !Number.isInteger(extent) || extent < 0 || extent > 9) {
    throw new RangeError('Unsupported tile set or marking extent');
  }
  const support = failureSupport[setId].filter(row => row[5] <= extent)
    .map(([tile,x,y,component,value]) => ({tile, point:[x,y,-x-y], component, value}));
  // Missing components are wildcards. The standard signed permutation action
  // and equality on overlap are both implemented by SparseA2Marking.
  return new SparseA2Marking(support, {label:'Rank 3 from failures'});
}
