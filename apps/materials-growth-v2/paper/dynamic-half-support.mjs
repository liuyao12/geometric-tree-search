// Recompute necessary complement support after every authoritative state change.
// This is a derived cache, rebuilt on rollback; it never changes decision order.
import assert from 'node:assert/strict';
export function dynamicHalfSupportClass(Base, model) {
 const groups = new Map(model.supportGroups.map(g => [g.point, g.atoms]));
 const supports = new Map(model.complementSupport.map(c => [c.id, c.groups]));
 assert.equal(supports.size, model.candidates.length);
 return class DynamicHalfSupport extends Base {
  reason(c) { return super.reason(c) || (this.supportRejected?.has(c.id) ? 'no-compatible-half-complement' : null); }
  refresh(changed) {
   this.supportRejected = new Set();
   super.refresh(changed);
   const needs = new Set();
   for (const [point, atoms] of groups) {
    const total = this.points.get(atoms[0]).total;
    assert([0,1,2].includes(total));
    assert(atoms.every(a => this.points.get(a).total === total));
    if (total === 0) needs.add(point);
   }
   const live = new Set([...this.reverse].filter(([, p]) => p.size).map(([id]) => id));
   const counts = new Map(), queue = [];
   for (const id of live) {
    const own = new Map(); counts.set(id, own);
    for (const g of supports.get(id)) if (needs.has(g.point)) {
     const count = g.partners.reduce((n, j) => n + Number(live.has(j)), 0); own.set(g.point, count);
     if (!count) queue.push(id);
    }
   }
   for (let cursor = 0; cursor < queue.length; cursor++) {
    const id = queue[cursor]; if (!live.delete(id)) continue;
    this.supportRejected.add(id);
    for (const g of supports.get(id)) if (needs.has(g.point)) for (const j of g.partners) if (live.has(j)) {
     const own = counts.get(j), count = own.get(g.point) - 1; assert(count >= 0); own.set(g.point, count);
     if (!count) queue.push(j);
    }
   }
   for (const id of this.supportRejected) this.updateCandidate(id);
  }
 };
}
