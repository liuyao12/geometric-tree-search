import {A2_TILE_LOOPS, FixedA2Marking, a2Add, a2Transform, tileOrientations} from './a2-tiling-engine.js?v=point-base-adjacency';
import {parity} from './tile-connection-learning.js?v=20260921-online-marking';

// Sparse subset of the predictions common to all complete tilings around a seed.
// Rows are grouped by distance from positive tile support. Each entry gives
// [x, y, axis, sign]. A positive sign means one tile contains the whole chord
// centered here, one primitive step either side. Missing entries impose no rule.
const bands = {
  hat: {
    hat: [
      [[-1,5,0,-1], [0,4,1,1], [1,2,2,1], [1,3,0,1], [1,3,1,1]],
      [],
      [[-1,-1,0,1], [4,-2,1,1], [5,-2,0,-1], [6,1,1,-1]],
      [[-4,8,1,1], [-3,9,0,1], [1,-3,2,-1], [7,-1,1,-1]],
      [[-5,6,0,-1], [-5,6,2,-1], [-5,8,0,-1], [-1,10,2,-1], [1,-4,2,-1], [6,-4,1,-1]],
      [[-5,0,2,-1], [-5,1,0,1], [-3,-2,2,-1], [-2,-3,1,-1], [0,-5,0,-1], [2,9,1,-1], [3,-5,2,-1], [3,8,2,-1], [5,6,2,-1], [9,-1,2,-1], [9,1,1,-1]],
      [[-7,3,2,-1], [-7,11,0,1], [-6,1,1,-1], [-6,12,1,1], [-2,-4,0,-1], [1,11,1,-1], [8,4,0,-1], [10,-4,0,-1]],
      [[-8,2,2,-1], [-8,3,1,-1], [4,9,1,-1], [6,7,1,-1], [7,-7,2,-1], [9,-7,2,-1], [10,-7,0,-1], [10,-6,0,-1]],
      [[-9,7,1,-1], [-9,14,0,-1], [-9,14,1,-1], [5,9,1,-1], [6,-8,2,-1], [6,8,0,-1], [8,-8,0,-1]],
    ],
  },
  mixed: {
    turtle: [
      [[-5,1,2,-1], [-4,5,1,-1], [-3,1,1,1], [-3,2,1,1], [-3,3,2,-1], [-2,-2,2,-1], [-2,0,0,1], [-2,0,1,1], [-1,-1,2,1], [-1,0,1,1], [0,-3,1,-1], [0,0,2,-1]],
      [[-6,3,0,1], [-2,4,2,1]],
      [[-6,0,1,1], [-6,0,2,1], [-5,7,1,1], [-3,-3,2,1], [2,-1,0,1]],
      [[-7,7,1,-1], [-1,-5,1,-1], [4,-5,2,1]],
      [[-9,3,2,-1], [-9,5,1,-1], [-7,9,1,-1], [-5,9,1,-1], [3,-7,1,-1]],
      [[-10,5,2,1], [-10,8,1,1], [-1,7,1,-1], [0,-8,0,-1], [4,1,2,1], [4,2,2,-1], [5,-1,2,-1], [6,-6,1,1], [6,-3,2,1]],
      [[-5,-5,0,1], [-3,10,1,-1], [1,6,0,-1], [6,-8,0,-1]],
      [[-12,1,0,-1], [-12,4,2,-1], [-5,12,1,-1], [-4,12,2,-1], [2,6,0,-1], [5,3,2,-1], [8,-6,2,-1], [8,-2,2,-1]],
      [[-13,3,1,-1], [-7,-5,1,-1], [-7,13,2,-1], [-2,11,0,-1]],
      [[-14,5,0,-1], [-7,-6,2,-1], [-3,13,1,-1], [0,10,1,-1], [0,10,2,-1]],
    ],
    hat: [
      [[-1,5,0,-1], [-1,5,2,-1], [0,0,2,-1], [0,3,0,-1], [0,6,2,-1], [1,1,1,-1], [1,2,2,1], [1,3,1,1], [2,2,0,1], [2,2,2,1], [3,3,2,-1], [4,1,0,-1]],
      [],
      [[-3,3,2,1], [-2,1,2,1], [-1,-1,2,1], [1,7,2,1], [4,-2,0,1], [5,-1,0,1]],
      [[-4,3,0,-1], [-4,8,0,1], [5,-3,1,-1], [6,3,0,1]],
      [[-2,-2,2,-1], [2,8,2,-1]],
      [[-5,0,2,-1], [0,-5,1,-1], [9,-3,0,1], [9,-1,2,-1]],
      [[-7,3,1,-1], [-7,5,0,1], [-6,12,1,1], [-2,-4,0,-1], [3,9,2,1], [6,-6,1,1]],
      [[-8,2,2,-1], [-8,9,1,-1], [-8,12,0,-1], [-7,0,0,-1], [-7,13,2,-1], [-6,-1,0,-1], [-6,-1,1,-1], [6,7,1,-1], [10,-7,0,-1], [11,-5,1,-1], [11,-3,1,-1]],
      [[-9,4,0,-1], [-9,14,0,-1], [8,6,2,-1], [9,-8,1,-1], [12,-2,0,-1]],
      [[-10,10,0,-1]],
    ],
  },
};

export const CHORD_MAX_EXTENT = 9;

// Local axis-zero samples of the two tiles that disagree in the recorded
// mixed eight-tile patch, or in the three-Hat obstruction for the Hat set.
const obstructionPoints = {
  mixed: {hat: [[-2,-4]], turtle: [[-2,0]]},
  hat: {hat: [[-3,9],[-1,5]]}
};

export class DeepChordMarking extends FixedA2Marking {
  constructor(setId, extent = CHORD_MAX_EXTENT, {twoMarks = false} = {}) {
    if (!Object.hasOwn(bands, setId)) throw new RangeError('Chords require the Hat or mixed tile set');
    if (!Number.isInteger(extent) || extent < 0 || extent > CHORD_MAX_EXTENT) throw new RangeError('Invalid chord extent');
    super(0, {tiles: Object.keys(bands[setId]), rank: 1});
    this.twoMarks = twoMarks;
    this.chords = {};
    const scalarSites = new Set();
    for (const [tile, rows] of Object.entries(bands[setId])) {
      const chords = rows.slice(0, extent + 1).flat();
      this.chords[tile] = twoMarks ? chords.filter(([x,y,axis]) =>
        axis === 0 && obstructionPoints[setId][tile].some(([u,v]) => u === x && v === y)) : chords;
      if (twoMarks) continue;
      // The twelve listed boundary vertices other than the two 270-degree
      // notches suffice for every former scalar rejection on a legal pair.
      const [canonical] = tileOrientations(tile, A2_TILE_LOOPS[tile]);
      for (const point of canonical.loop) {
        if (canonical.occupancy.get(String(point)).weight !== 9) scalarSites.add(tile + ':' + point);
      }
    }
    this.support = this.support.filter(m => scalarSites.has(m.tile + ':' + m.point));
    this.rotated = new Map();
  }

  segments() { return []; } // The remaining scalar samples are individual sites.

  entries(placement) {
    const {tile, orientation, translation} = placement;
    const key = placement.id ?? `${tile}:${orientation.index}:${translation}`;
    if (this.entryCache.has(key)) return this.entryCache.get(key);
    const values = super.entries(placement);
    const pose = `${tile}:${orientation.index}`;
    if (!this.rotated.has(pose)) {
      const {symmetry} = orientation;
      // Convex 120 degree corner signs change under reflection. Chord
      // containment is an unoriented geometric predicate, so only its axis moves.
      const sign = (tile === 'hat' ? 1 : -1) * parity(symmetry.permutation);
      const marks = this.twoMarks ? [] : [...orientation.occupancy.values()].filter(e => e.weight === 4)
        .map(({point}) => [point, 'corner', sign]);
      for (const [x, y, axis, value] of this.chords[tile]) {
        marks.push([a2Transform([x, y, -x-y], symmetry), 'chord' + symmetry.permutation.indexOf(axis), value]);
      }
      this.rotated.set(pose, marks);
    }
    for (const [point, component, value] of this.rotated.get(pose)) {
      values.set(`${a2Add(point, translation)}|${component}`, value);
    }
    return values;
  }

  stats() {
    if (!this.report) {
      const support = [];
      for (const tile of Object.keys(this.chords)) {
        const orientation = tileOrientations(tile, A2_TILE_LOOPS[tile])[0];
        for (const [key,value] of this.entries({tile, orientation, translation:[0,0,0]})) {
          const [point,channel] = key.split('|');
          support.push({tile, point:point.split(',').map(Number), component:channel === '0' ? 0 : channel,
            value, color:value === 0 ? 0 : value > 0 ? 1 : 2});
        }
      }
      this.report = {...super.stats(), support, supportSites:support.length};
    }
    return {...this.report, prunes:this.prunes};
  }
}
