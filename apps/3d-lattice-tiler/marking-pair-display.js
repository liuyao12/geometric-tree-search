// Inspection only. Reconstruct the assigned overlaps from the selected field;
// a displayed conflict never supplies a label to the unmarked corona oracle.
export function inspectPairMarking(fields, pair) {
  const sites = new Map();
  for (const [tile, p] of pair.entries()) {
    for (const entry of fields[p.oi] ?? []) {
      const components = Array.isArray(entry.value)
        ? entry.value.map((value, component) => ({value, component}))
        : [{value: entry.value, component: entry.component ?? 0}];
      for (const {value, component} of components) {
        if (value == null || value === '*') continue;
        const pos = entry.pos.map((x, i) => x + p.translation[i]);
        const key = `${pos}|${component}`;
        if (!sites.has(key)) sites.set(key, {pos, component, assignments: []});
        sites.get(key).assignments.push({tile, value});
      }
    }
  }
  const points = [...sites.values()].map(p => ({
    ...p,
    overlap: new Set(p.assignments.map(a => a.tile)).size > 1,
    conflict: new Set(p.assignments.map(a => a.value)).size > 1,
  }));
  const overlaps = points.filter(p => p.overlap);
  const conflicts = overlaps.filter(p => p.conflict);
  return {points, overlaps, conflicts, compatible: conflicts.length === 0};
}

export function pairInspectionText(row, inspection) {
  const oracle = row.status === 'valid'
    ? 'Valid: complete 1-corona with viable frontier.'
    : row.status === 'invalid'
      ? 'Invalid: unmarked 1-corona search exhausted.'
      : `Unresolved: ${row.reason ?? 'search budget reached'}.`;
  const marking = inspection.compatible ? 'accepts' : 'rejects';
  const score = row.status === 'unresolved' ? 'not a validity label'
    : (row.status === 'valid') === inspection.compatible ? 'correct' : 'mismatch';
  const cost = Number.isFinite(row.nodes) ? ` ${row.nodes} attempts · ${row.backtracks ?? 0} backtracks.` : '';
  return `${oracle} Marking ${marking} this pair (${score}) · ${inspection.overlaps.length} assigned overlaps · ${inspection.conflicts.length} conflicts.${cost}`;
}
