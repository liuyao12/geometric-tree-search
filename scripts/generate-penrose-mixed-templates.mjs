import {writeFile} from 'node:fs/promises';
import {makeP1Model} from '../assets/penrose-model-set.js';
import {canonical,asFive,embedding,latticeKey} from '../assets/cyclotomic-five.js';
import {growthRhomb} from '../assets/penrose-growth.js';
import {arrowStates} from '../assets/penrose-arrows.js';
import {ammannStates} from '../assets/penrose-ammann.js';
import {num,add,sub,mul,div,norm,lerp,pointInPolygon,overlap,areaSign,clipSegment,conj,cross,cmp} from '../assets/penrose-polygon.js';
const p1=makeP1Model().tiles;
const centers=new Map(p1.filter(t=>t.kind.startsWith('p')).map(t=>[t.id,t.exactPoints.reduce((s,p)=>add(s,mul(p,num(1,5))),num(0))]));
const atVertex=new Map();for(const t of p1.filter(t=>centers.has(t.id)))for(const v of t.vertices){if(!atVertex.has(v))atVertex.set(v,new Set());atVertex.get(v).add(t.id);}
let hbs=[];
for(const t of p1.filter(t=>!centers.has(t.id))){const ids=[...new Set(t.vertices.flatMap(v=>[...(atVertex.get(v)||[])]))];if(ids.length!==({star:10,boat:8,diamond:6}[t.kind]))continue;
 const center=t.exactPoints.reduce((s,p)=>add(s,mul(p,num(1,t.exactPoints.length))),num(0)),c=embedding(center);
 ids.sort((a,b)=>{const p=embedding(centers.get(a)),q=embedding(centers.get(b));return Math.atan2(p.y-c.y,p.x-c.x)-Math.atan2(q.y-c.y,q.x-c.x);});
 hbs.push({kind:t.kind,poly:ids.map(i=>centers.get(i))});}
const origin=hbs[0].poly[0],unit=sub(hbs[0].poly[1],origin);const normalize=p=>canonical(div(sub(p,origin),unit));
hbs=hbs.map(t=>({...t,poly:t.poly.map(normalize)}));
const p1normalized=p1.map(t=>({...t,exactPoints:t.exactPoints.map(normalize)}));
console.log('HBS',hbs.length,'unit',unit,'denominators',new Set(hbs.flatMap(t=>t.poly.map(p=>p.denominator))));
const e=Array.from({length:5},(_,i)=>asFive({coeff:Array.from({length:5},(_,k)=>+(k===i)),denominator:1}));
for(const cell of hbs){const candidates=new Map();for(const anchor of cell.poly)for(let i=0;i<5;i++)for(let j=i+1;j<5;j++)for(const shift of[num(0),e[i],e[j],add(e[i],e[j])]){
 const base=asFive(sub(anchor,shift));if(base.denominator!==1)throw Error('noninteger HBS lattice');const t=growthRhomb(base.coeff,i,j);if(candidates.has(t.id))continue;
 const points=t.exactPoints;
 if(!points.every(p=>pointInPolygon(p,cell.poly))||!points.every((p,k)=>pointInPolygon(lerp(p,points[(k+1)%4],num(1,2)),cell.poly))||!pointInPolygon(lerp(points[0],points[2],num(1,2)),cell.poly))continue;
 candidates.set(t.id,t);
 }
 const groups=new Map();for(const t of candidates.values())for(const state of arrowStates(t)){
 const sink=state.arrows.filter(a=>a.type===2).map(a=>latticeKey(a.to));if(sink[0]!==sink[1])throw Error('bad arrow sink');
 if(!groups.has(sink[0]))groups.set(sink[0],[]);groups.get(sink[0]).push({tile:t,start:state.start});
 }
 if(cell===hbs.find(t=>t.kind===cell.kind))console.log(cell.kind,"candidates",candidates.size,"fan sizes",[...groups.values()].map(g=>g.length));
 cell.choices=[];
 const boundary=new Set(cell.poly.map((p,k)=>[latticeKey(p),latticeKey(cell.poly[(k+1)%cell.poly.length])].sort().join('|')));
 function* subsets(group,n,picked=[],at=0){if(!n){yield picked;return;}for(let i=at;i<=group.length-n;i++)yield*subsets(group,n-1,[...picked,group[i]],i+1);}
 for(const group of groups.values())for(const parts of subsets(group,({star:5,boat:4,diamond:3}[cell.kind]))){
 if(parts.filter(p=>p.tile.kind==='thick').length!==({star:5,boat:3,diamond:1}[cell.kind]))continue;
 if(parts.some((a,i)=>parts.slice(i+1).some(b=>overlap(a.tile.exactPoints,b.tile.exactPoints))))continue;
 const edges=new Map();let valid=true;for(const {tile,start} of parts)for(const [edge,sig]of ammannStates(tile).find(s=>s.start===start).signatures){if(edges.has(edge)){if(edges.get(edge)!==sig)valid=false;edges.delete(edge);}else edges.set(edge,sig);}
 if(valid&&edges.size===boundary.size&&[...edges.keys()].every(e=>boundary.has(e)))cell.choices.push({parts,edges});
 }
}
console.log('choices',Object.fromEntries([0,1,2,3,4].map(n=>[n,hbs.filter(t=>t.choices.length===n).length])));
await writeFile('/tmp/penrose-hbs.json',JSON.stringify({p1:p1normalized,hbs:hbs.map(t=>({...t,choices:t.choices.map(s=>({...s,edges:[...s.edges]}))}))}));

const neighbors=hbs.map(()=>[]),owners=new Map();hbs.forEach((cell,i)=>{for(const edge of cell.choices[0].edges.keys()){if(owners.has(edge)){const j=owners.get(edge);neighbors[i].push([j,edge]);neighbors[j].push([i,edge]);}else owners.set(edge,i);}});
function solve(domains){let changed=true;while(changed){changed=false;for(let i=0;i<hbs.length;i++)for(const[j,e]of neighbors[i]){const ds=domains[i].filter(s=>domains[j].some(t=>hbs[i].choices[s].edges.get(e)===hbs[j].choices[t].edges.get(e)));if(!ds.length)return null;if(ds.length!==domains[i].length){domains[i]=ds;changed=true;}}}const i=domains.findIndex(d=>d.length>1);if(i<0)return domains.map(d=>d[0]);for(const s of domains[i]){const copy=domains.map(d=>d.slice());copy[i]=[s];const r=solve(copy);if(r)return r;}return null;}
const solution=solve(hbs.map(t=>t.choices.map((_,i)=>i)));if(!solution)throw Error('HBS decorations inconsistent');
const parts=hbs.flatMap((t,i)=>t.choices[solution[i]].parts);console.log('Consistent rhombs',parts.length);
await writeFile('/tmp/penrose-common-patch.json',JSON.stringify({p1:p1normalized,hbs,parts}));

await import("./derive-penrose-p2-patch.mjs");
await import("./extract-penrose-mixed-templates.mjs");
