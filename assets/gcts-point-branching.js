// Geometry-free GCTS scheduling over frontier points and legal placement IDs.
// Callers supply complete domains and restore point introduction ages on rollback.
export function selectPointBranch(frontier, random = Math.random, { restrictToPoint = true, isAdjacent } = {}) {
  const dead = frontier.find(point => point.legal.length === 0);
  if (dead) return { dead, forced: false, moves: [] };
  const forced = frontier.find(point => point.legal.length === 1);
  if (forced) return { dead: null, forced: true, moves: [{ placement: forced.legal[0], frontier: forced }] };
  let oldest = Infinity;
  for (const point of frontier) oldest = Math.min(oldest, point.introducedAt);
  const pool = new Map();
  for (const point of frontier) {
    if (point.introducedAt !== oldest) continue;
    for (const placement of point.legal) {
      if (!pool.has(placement.id)) pool.set(placement.id, { placement, frontier: point });
    }
  }
  let moves = [...pool.values()];
  for (let i = moves.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [moves[i], moves[j]] = [moves[j], moves[i]];
  }
  if (isAdjacent) {
    const nearby = [], others = [];
    for (const move of moves) {
      (isAdjacent(move.placement) ? nearby : others).push(move);
    }
    moves = [...nearby, ...others];
  }
  if (restrictToPoint && moves.length) {
    const point = moves[0].frontier;
    const alternatives = new Set(point.legal.map(placement => placement.id));
    moves = moves.filter(move => alternatives.has(move.placement.id))
      .map(move => ({ ...move, frontier: point }));
  }
  return { dead: null, forced: false, moves };
}
