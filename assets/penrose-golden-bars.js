import { GOLDEN_PORTS, canonical, cycloAdd, cycloMultiply, edgePort, latticeKey, starMap } from "./cyclotomic-five.js";

const subtract = (a, b) => cycloAdd(a, { ...canonical(b), coeff: canonical(b).coeff.map(n => -n) });
const conjugate = a => starMap(starMap(a));
const zero = a => canonical(a).coeff.every(n => n === 0);
export const exactlyParallel = (a, b) => zero(subtract(cycloMultiply(a, conjugate(b)), cycloMultiply(conjugate(a), b)));
const colors = ["#d4594c", "#d18e2f", "#22877d", "#5578b5", "#8b69a5"];

// Search geometric port supports on a finite patch. No lines are painted across
// the canvas and retroactively labelled as learned tile decorations.
export function auditGoldenBars(tiles) {
  const segments = [], endpoints = new Map(), edgeCounts = new Map();
  const keyOfEdge = (tile, k) => [latticeKey(tile.exactPoints[k]), latticeKey(tile.exactPoints[(k + 1) % 4])].sort().join("|");
  for (const tile of tiles) for (let k = 0; k < 4; k++) {
    const key = keyOfEdge(tile, k); edgeCounts.set(key, (edgeCounts.get(key) || 0) + 1);
  }
  for (const tile of tiles) {
    const ports = tile.exactPoints.flatMap((a, edge) => GOLDEN_PORTS.map(t => ({
      point: edgePort(a, tile.exactPoints[(edge + 1) % 4], t.value), edge: keyOfEdge(tile, edge)
    })));
    for (let i = 0; i < ports.length; i++) for (let j = i + 1; j < ports.length; j++) {
      if (ports[i].edge === ports[j].edge) continue;
      const delta = subtract(ports[j].point, ports[i].point);
      for (let family = 0; family < 5; family++) {
        const axis = { coeff: Array.from({ length: 5 }, (_, k) => Number(k === family)), denominator: 1 };
        if (!exactlyParallel(delta, axis)) continue;
        const segment = { tileId: tile.id, from: ports[i].point, to: ports[j].point, family, color: colors[family],
          ends: [ports[i], ports[j]], alive: true };
        const id = segments.push(segment) - 1;
        for (const port of segment.ends) {
          const key = `${latticeKey(port.point)}:${family}`;
          if (!endpoints.has(key)) endpoints.set(key, []);
          endpoints.get(key).push(id);
        }
      }
    }
  }
  let changed = true;
  while (changed) {
    changed = false;
    for (const segment of segments) if (segment.alive) {
      const unsupported = segment.ends.some(port => edgeCounts.get(port.edge) === 2 &&
        !endpoints.get(`${latticeKey(port.point)}:${segment.family}`).some(id => segments[id].alive && segments[id].tileId !== segment.tileId));
      if (unsupported) { segment.alive = false; changed = true; }
    }
  }
  const surviving = segments.filter(s => s.alive), byTile = new Map();
  let interiorEndpoints = 0, boundaryEndpoints = 0;
  for (const segment of surviving) {
    if (!byTile.has(segment.tileId)) byTile.set(segment.tileId, []);
    byTile.get(segment.tileId).push(segment);
    for (const port of segment.ends) edgeCounts.get(port.edge) === 2 ? interiorEndpoints++ : boundaryEndpoints++;
  }
  return { byTile, candidates: segments.length, survivors: surviving.length, interiorEndpoints, boundaryEndpoints,
    families: new Set(surviving.map(s => s.family)).size, rediscovered: false,
    explanation: "Finite-patch golden-port propagation only; tile-local matching-language equivalence and held-out transfer are unproved." };
}
