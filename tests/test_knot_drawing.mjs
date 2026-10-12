import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { canonical, moves, parse } from '../apps/knot-movie/engine.mjs';
import { planarDrawing, verifyDrawing, movieDrawings } from '../apps/knot-movie/drawing.mjs';
import { annularMovie, segmentKey } from '../apps/knot-movie/annular-movie.mjs';

let pool=new Map([['',[]]]);
for(let round=0;round<3;round++){
  const next=new Map(pool);for(const w of pool.values())for(const m of moves(w,4))next.set(m.key,m.after);pool=next;
}
for(const w of pool.values())assert(verifyDrawing(planarDrawing(w)));
const rows=JSON.parse(readFileSync(new URL('../research/knot-classifier/trefoil-identification.json',import.meta.url))).rows;
for(const {certificate}of rows){
  const generic=movieDrawings(certificate),stable=annularMovie(certificate);assert(stable);assert.equal(stable.length,3);
  for(const frames of [generic,stable])frames.forEach((f,i)=>{
    assert.equal(canonical(f.before.word),i?certificate.steps[i-1].after:certificate.source);
    assert.equal(canonical(f.after.word),certificate.steps[i].after);
    assert(verifyDrawing(f.before));assert(verifyDrawing(f.after));
    assert.equal(f.affected.size,{'I−':1,'II−':2,III:3}[f.kind]);
  });
  for(const f of stable){
    const before=new Set(f.before.edges.map(([a,b])=>segmentKey(f.before,a,b))),after=new Set(f.after.edges.map(([a,b])=>segmentKey(f.after,a,b)));
    assert(f.beforeSegments.size<before.size/2,'Most of the before drawing must stay fixed.');
    assert(f.afterSegments.size<after.size/2,'Most of the after drawing must stay fixed.');
    for(const key of before)assert.equal(f.beforeSegments.has(key),!after.has(key));
    for(const key of after)assert.equal(f.afterSegments.has(key),!before.has(key));
  }
}
const trefoil=planarDrawing(parse('O1+ U2+ O3+ U1+ O2+ U3+'));
const mirror=structuredClone(trefoil);mirror.points.forEach(p=>p[0]*=-1);assert.throws(()=>verifyDrawing(mirror),/sign mismatch/);
const collapsed=structuredClone(trefoil);collapsed.points[collapsed.edges[0][0]]=[...collapsed.points[collapsed.edges[0][1]]];assert.throws(()=>verifyDrawing(collapsed),/Collapsed/);
assert.equal(annularMovie({source:'',target:'',steps:[],crossingCap:3}),null);
console.log(JSON.stringify({passed:true,planarDiagrams:pool.size,trefoilMovies:rows.length,allMoveTypes:true,fixedSurroundings:true,mirrorAndCollapseRejected:true}));
