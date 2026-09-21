// Display data only: the solver's point assignments remain authoritative.
export const markingPointKey = p => `${p.pos}|${p.component ?? 0}`;
export function applyMarkingUpdates(points, updates = []) {
  for (const p of updates) {
    const key = markingPointKey(p);
    if (p.count > 0) points.set(key, p);
    else points.delete(key);
  }
  return points;
}
export function placedMarkingPoints(model, placements) {
  const points = new Map();
  for (const p of placements) for (const m of (model.orientations[p.oi].marks ?? []).flatMap(m => Array.isArray(m.value) ? m.value.map((value, component) => ({...m, value, component})) : [m])) {
    if (m.value == null || m.value === '*') continue;
    const pos = m.pos.map((x, i) => x + p.translation[i]), component = m.component ?? 0;
    const key = markingPointKey({pos, component}), old = points.get(key);
    if (old && old.value !== m.value) throw Error('Displayed marking has conflicting values');
    points.set(key, {pos, component, value: m.value, count: (old?.count ?? 0) + 1});
  }
  return [...points.values()];
}

// Missing components are displayed independently; assigned zero is retained.
export function markingVectors(field=[],componentCount=1){
 const points=new Map();
 for(const m of field){
  const key=m.pos.join(),values=points.get(key)??Array(componentCount).fill('*');
  values[m.component??0]=m.value;points.set(key,values);
 }
 return points;
}
