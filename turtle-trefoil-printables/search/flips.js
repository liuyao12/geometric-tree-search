import {A2_SYMMETRIES,a2Transform,a2Add,a2Sub} from './a2-tiling-engine.js';
import {loops,support,parity,project} from './model.js';
const key=p=>p.join(',');
export function marks(p){const s=p.orientation.symmetry;return support.filter(m=>m.tile===p.tile).map(m=>[key(a2Add(a2Transform(m.point,s),p.translation))+'|'+s.permutation.indexOf(m.component),m.value*parity(s.permutation)]);}
export function compatible(placements){const values=new Map(),totals=new Map();for(const p of placements){for(const [k,e] of p.occupancy){const n=(totals.get(k)||0)+e.weight;if(n>12)return false;totals.set(k,n);}for(const [k,v] of marks(p)){if(values.has(k)&&values.get(k)!==v)return false;values.set(k,v);}}return true;}
export function totals(placements){const result=new Map();for(const p of placements)for(const [k,e] of p.occupancy)result.set(k,(result.get(k)||0)+e.weight);return result;}
const equal=(a,b)=>a.size===b.size&&[...a].every(([k,v])=>b.get(k)===v);
export function transform(p,op){const s=p.orientation.symmetry,symmetry={sign:s.sign*op.sym.sign,permutation:op.sym.permutation.map(i=>s.permutation[i])};const translation=a2Add(a2Transform(p.translation,op.sym),op.translation);return {...p,translation,orientation:{...p.orientation,symmetry},occupancy:new Map([...p.occupancy.values()].map(e=>{const point=a2Add(a2Transform(e.point,op.sym),op.translation);return [key(point),{...e,point}];}))};}
function edges(p){const s=p.orientation.symmetry,vertices=loops[p.tile].map(v=>a2Add(a2Transform(a2Sub(v,loops[p.tile][0]),s),p.translation)),result=new Map();const gcd=(a,b)=>b?gcd(b,a%b):a;for(let i=0;i<vertices.length;i++){const a=vertices[i],d=a2Sub(vertices[(i+1)%vertices.length],a),n=d.map(Math.abs).reduce(gcd);for(let j=0;j<n;j++){const ends=[j,j+1].map(t=>a.map((v,k)=>v+d[k]*t/n));result.set(ends.map(key).sort().join('|'),ends);}}return result;}
export function stateKey(ps){return ps.map(p=>p.tile+':'+[...p.occupancy].map(([k,e])=>k+'='+e.weight).sort().join(';')+':'+marks(p).map(([k,v])=>k+'='+v).sort().join(';')).sort().join('/');}
// A local rearrangement, separate from frontier growth. Certify both the exact
// point totals and the complete polygon boundary, then replay all point marks.
export function findFlips(placements){const moves=[];for(let a=0;a<placements.length;a++){if(placements[a].tile!=='trefoil')continue;for(let b=0;b<placements.length;b++){if(placements[b].tile!=='turtle')continue;const pair=[placements[a],placements[b]],ea=edges(pair[0]),eb=edges(pair[1]);if(![...ea.keys()].some(k=>eb.has(k)))continue;const outline=new Map([...ea,...eb].filter(([k])=>!(ea.has(k)&&eb.has(k)))),sum=totals(pair),mass=[...sum.values()].reduce((a,b)=>a+b,0),centroid=[0,0,0];for(const [k,w] of sum)k.split(',').map(Number).forEach((v,i)=>centroid[i]+=v*w);
 for(const sym of A2_SYMMETRIES){const reflection=parity(sym.permutation)===-1,halfTurn=sym.sign===-1&&sym.permutation.every((v,i)=>v===i);if(!reflection&&!halfTurn)continue;const delta=a2Sub(centroid,a2Transform(centroid,sym));if(delta.some(v=>v%mass))continue;const op={sym,translation:delta.map(v=>v/mass)},affine=p=>a2Add(a2Transform(p,sym),op.translation);if(![...outline.values()].every(ends=>outline.has(ends.map(affine).map(key).sort().join('|'))))continue;
 const changed=pair.map(p=>transform(p,op));if(!equal(sum,totals(changed)))continue;const next=placements.slice();next[a]=changed[0];next[b]=changed[1];if(!compatible(next))continue;
 const p0=project(a2Add([0,0,0],op.translation)),u=project(a2Transform([1,0,-1],sym)),v=project(a2Transform([0,1,-1],sym)),r00=u[0]/(-5*Math.sqrt(3)),r10=u[1]/(-5*Math.sqrt(3)),r01=(v[0]+2.5*Math.sqrt(3)*r00)/(-7.5),r11=(v[1]+2.5*Math.sqrt(3)*r10)/(-7.5);
 // Coordinates after the shared board phase and face-up turnover.
 const phase=[5*Math.sqrt(3),15],shift=[p0[0]+phase[0]-r00*phase[0]-r01*phase[1],p0[1]+phase[1]-r10*phase[0]-r11*phase[1]];
 const axisPoint=[shift[0]/2,-shift[1]/2,2];let axis=[1+r00,-r10,0];if(Math.hypot(...axis)<1e-6)axis=[-r01,1+r11,0];const length=Math.hypot(...axis);axis=reflection?axis.map(v=>v/length):[0,0,1];
 moves.push({kind:reflection?'flip':'turn',indices:[a,b],ids:pair.map(p=>p.id),next,op,axis,axisPoint});
 }
 }}return moves;}
// Explore local rearrangements of a finite, freshly grown patch. This graph is
// not the frontier-growth engine and does not prune or certify infinite tilings.
export function findSequence(placements,limit=300){const queue=[{placements,path:[]}],seen=new Set([stateKey(placements)]);let best=[];for(let i=0;i<queue.length&&i<limit;i++){const state=queue[i];for(const move of findFlips(state.placements)){const k=stateKey(move.next);if(seen.has(k))continue;seen.add(k);const path=[...state.path,move];if(path.length>best.length)best=path;queue.push({placements:move.next,path});}}return {moves:best,states:seen.size,exhausted:queue.length<=limit};}
