import { VARIANTS, FACE_DIRECTIONS, IDENTITY, rotationId, worldMarks, SOURCE } from './chair44.js';

// A scalar, pure-pullback realization of the arrow decoration on Z^3.
// Physical unit lengths become 12 lattice steps. Distinct panel centers differ
// by at least 6 in some coordinate, so their radius-2 stencils are disjoint.
export const LATTICE_SCALE = 12;
const dot = (a, b) => a.reduce((sum, value, i) => sum + value * b[i], 0);

export function scalarPanelMark(mark) {
  const center = mark.cell.map((value, i) => 12 * value + 6 + 6 * mark.direction[i]);
  const sign = mark.color === 'red' ? 1 : mark.color === 'green' ? -1 : 0;
  const polar = mark.direction.map(value => sign * value);
  return FACE_DIRECTIONS.flatMap(direction => [
    { point: center.map((value, i) => value + direction[i]), value: dot(mark.arrow, direction) },
    { point: center.map((value, i) => value + 2 * direction[i]), value: dot(polar, direction) },
  ]);
}

export function latticeTile(placement) {
  return {
    t: VARIANTS[placement.variantId].cells.map(cell => ({
      point: cell.map((value, i) => 12 * (value + placement.origin[i]) + 6), value: 1,
    })),
    m: worldMarks(placement).flatMap(scalarPanelMark),
  };
}

export function verifyLatticePatch(placements) {
  const totals = new Map(), values = new Map();
  for (const placement of placements) {
    const { t, m } = latticeTile(placement);
    for (const { point, value } of t) {
      const key = point.join(',');
      const total = (totals.get(key) ?? 0) + value;
      if (total > 1) return { valid: false, reason: 'capacity conflict' };
      totals.set(key, total);
    }
    for (const { point, value } of m) {
      const key = point.join(',');
      if (values.has(key) && values.get(key) !== value) return { valid: false, reason: 'marking conflict' };
      values.set(key, value); // Zero is assigned; only absent keys are free.
    }
  }
  return { valid: true, occupiedPoints: totals.size, markedPoints: values.size };
}

export const LATTICE_MODEL = {
  name: 'Chair44 scalar lattice marking',
  version: 1,
  source: SOURCE,
  role: 'Exact encoding of the given arrow rule; not a learned marking',
  pointDomain: 'Z^3',
  physicalUnitInLatticeSteps: LATTICE_SCALE,
  requiredOccupancyPoints: { offset: [6, 6, 6], step: [12, 12, 12] },
  translations: { step: [12, 12, 12] },
  rotations: { center: [12, 12, 12], matrices: VARIANTS.map(variant => variant.rotation) },
  valueAction: 'Scalar values are unchanged under rotation and translation; only points move',
  unlistedT: 0,
  unlistedM: 'unassigned',
  markingAlphabet: [-1, 0, 1],
  ...latticeTile({ variantId: rotationId(IDENTITY), origin: [0, 0, 0] }),
};
