import {writeFileSync} from 'node:fs';
import {neighborCatalog} from './penrose-neighbor-catalog.mjs';
import {MIXED_TEMPLATES} from '../assets/penrose-mixed-templates.js';
import {candidateBarContacts} from '../assets/penrose-candidate-contacts.js';
import {extendedBars} from '../assets/penrose-mixed-markings.js';
import {canonical,latticeKey} from '../assets/cyclotomic-five.js';
import {num,add,sub,mul,div,conj,onSegment,pointInPolygon} from '../assets/penrose-polygon.js';
const axes=Array.from({length:5},(_,i)=>canonical({coeff:Array.from({length:5},(_,j)=>+(i===j)),denominator:1}));
const rotation=f=>axes.findIndex(a=>latticeKey(mul(a,a))===latticeKey(mul(f,f)));
const apply=(p,t)=>add(mul(t.factor,t.reflect?conj(p):p),t.delta);
const family=(j,t)=>(rotation(t.factor)+(t.reflect?-j:j)+10)%5;
const undo=(p,t)=>{const q=div(sub(p,t.delta),t.factor);return t.reflect?conj(q):q;};
const undoFamily=(j,t)=>((t.reflect?-1:1)*(j-rotation(t.factor))+10)%5;
const shape=t=>t.exactPoints.map(latticeKey).sort().join('|')+'@'+t.bars.map(b=>[latticeKey(b.from),latticeKey(b.to)].sort().join('>')).sort().join('|');
const symmetries={};
for(const t of MIXED_TEMPLATES){
  const syms=[];
  for(const reflect of[false,true])for(const axis of axes)for(const sign of[1,-1]){
    const factor=mul(axis,num(sign)),raw={factor,reflect,delta:num(0)};
    for(const p of t.exactPoints){const s={...raw,delta:sub(p,apply(t.exactPoints[0],raw))};
      if(shape({exactPoints:t.exactPoints.map(p=>apply(p,s)),bars:t.bars.map(b=>({from:apply(b.from,s),to:apply(b.to,s)}))})===shape(t))syms.push(s);
    }
  }
  symmetries[t.kind]=syms;
}
const catalog=neighborCatalog((kind,n)=>console.log('Catalog',kind,n));
const bad=catalog.filter(c=>!c.good),good=catalog.filter(c=>c.good),groups=[],groupKeys=new Map(),proposals=[];
function group(tile,point,j,value,level){
  const p=undo(point,tile.markingTransform),f=undoFamily(j,tile.markingTransform);
  const rows=new Map(symmetries[tile.kind].map(s=>{const q=apply(p,s),k=family(f,s);return[latticeKey(q)+':'+k,{point:q,family:k}];}));
  const key=tile.kind+':'+value+':'+[...rows.keys()].sort().join('|');
  if(!groupKeys.has(key)){groupKeys.set(key,groups.length);groups.push({kind:tile.kind,value,level,rows:[...rows.values()]});}
  const id=groupKeys.get(key);groups[id].level=Math.min(groups[id].level,level);return id;
}
function firstLevel(tile,p,j){for(let k=0;k<=16;k++)if(extendedBars(tile,k/4).some(b=>b.family===j&&onSegment(p,b.from,b.to)))return k;throw Error('Witness outside permitted extent');}
for(let i=0;i<bad.length;i++){
  const {a,b}=bad[i];
  for(const[source,target]of[[a,b],[b,a]])for(const extent of[0,4])for(const c of candidateBarContacts(source,target,extent))if(c.value===0){
    const positive=group(source,c.point,c.family,1,firstLevel(source,c.point,c.family));
    const zero=group(target,c.point,c.family,0,0);proposals.push({positive,zero,case:i});
  }
}
console.log('Witness pool',groups.length,'orbits;',proposals.length,'paired proposals');
const byKind=new Map(MIXED_TEMPLATES.map(t=>[t.kind,[]]));groups.forEach((g,id)=>byKind.get(g.kind).push(id));
const supportCache=new WeakMap();
function support(tile){
  if(supportCache.has(tile))return supportCache.get(tile);
  const map=new Map();for(const id of byKind.get(tile.kind)){const g=groups[id];for(const r of g.rows){
    const key=latticeKey(apply(r.point,tile.markingTransform))+':'+family(r.family,tile.markingTransform);
    if(!map.has(key))map.set(key,[]);map.get(key).push(id);
  }}supportCache.set(tile,map);return map;
}
function conflicts(a,b,callback){let p=support(a),q=support(b);if(p.size>q.size)[p,q]=[q,p];for(const[key,x]of p){const y=q.get(key);if(y)for(const i of x)for(const j of y)if(groups[i].value!==groups[j].value)callback(i,j);}}
// Record incompatible support orbits from every allowed placement. Selection
// must preserve these constraints; an optional external positive must never
// invalidate a zero needed by the base rule.
const incompatibility=groups.map(()=>new Set());
for(const {a,b}of good)conflicts(a,b,(i,j)=>{incompatibility[i].add(j);incompatibility[j].add(i);});
const packages=new Map(),casePackages=bad.map(()=>new Set());
bad.forEach(({a,b},c)=>conflicts(a,b,(i,j)=>{if(incompatibility[i].has(j)||incompatibility[i].has(i)||incompatibility[j].has(j))return;const key=[i,j].sort((a,b)=>a-b).join(',');if(!packages.has(key))packages.set(key,{ids:[i,j],cases:new Set(),level:Math.max(groups[i].level,groups[j].level)});packages.get(key).cases.add(c);casePackages[c].add(key);}));
const missing=casePackages.map((p,i)=>p.size?null:i).filter(i=>i!==null);
if(missing.length)throw Error(`${missing.length} edge violations cannot be separated safely`);
const selectedAt=new Map(),levels=[];
for(let level=0;level<=16;level++){
  const selected=new Set(),remaining=new Set(bad.map((_,i)=>i)),available=[...packages.values()].filter(p=>p.level<=level);
  while(remaining.size){let best=null,bestScore=-1,bestGain=0;
    for(const p of available){if(p.ids.some(i=>[...selected,...selectedAt.keys()].some(j=>incompatibility[i].has(j))))continue;const gain=[...p.cases].filter(i=>remaining.has(i)).length,cost=p.ids.filter(i=>!selected.has(i)).reduce((s,i)=>s+groups[i].rows.length,0),score=gain/Math.max(cost,0.25);
      if(gain&&(score>bestScore||score===bestScore&&p.level>(best?.level??-1))){best=p;bestScore=score;bestGain=gain;}}
    if(!best)throw Error(`Extent ${level/4} misses ${remaining.size} forbidden placements`);
    best.ids.forEach(id=>selected.add(id));
    for(const p of available)if(p.ids.every(id=>selected.has(id)))for(const c of p.cases)remaining.delete(c);
  }
  // Remove redundant complete symmetry orbits while retaining all witnesses.
  for(const id of [...selected].reverse()){
    selected.delete(id);
    if(casePackages.some(keys=>![...keys].some(key=>{const p=packages.get(key);return p.level<=level&&p.ids.every(i=>selected.has(i));})))selected.add(id);
  }
  for(const id of selected)if(!selectedAt.has(id))selectedAt.set(id,level);
  levels.push({extent:level/4,orbits:selected.size,entries:[...selected].reduce((s,i)=>s+groups[i].rows.length,0)});
}
const tables=Object.fromEntries(MIXED_TEMPLATES.map(t=>[t.kind,[]]));
for(const[id,first]of selectedAt){const g=groups[id];for(const r of g.rows)tables[g.kind].push([r.point.coeff,r.point.denominator,r.family,g.value,first,!pointInPolygon(r.point,MIXED_TEMPLATES.find(t=>t.kind===g.kind).exactPoints)]);}
for(const rows of Object.values(tables))rows.sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b)));
const report={scope:'All nonoverlapping, whole-edge, vertex-aligned pairs in the fixed P1/P2/P3 catalog, modulo a rigid motion of the first tile. Mixed pairs included. No claim of exhaustive distant placements or infinite extendibility.',oracle:'P3 Ammann edge ports (independently checked against arrows); P1/P2 transferred bar edge ports; mixed ports experimental.',neighbors:catalog.length,allowed:good.length,forbidden:bad.length,sharedEdge:catalog.filter(c=>c.shared).length,proposedOrbits:groups.length,incompatibleOrbitPairs:incompatibility.reduce((s,x)=>s+x.size,0)/2,selectedOrbits:selectedAt.size,entries:Object.fromEntries(Object.entries(tables).map(([k,v])=>[k,v.length])),levels};
writeFileSync(new URL('../assets/penrose-finite-marking-data.js',import.meta.url),'// Generated by scripts/generate-penrose-finite-markings.mjs; do not edit.\n// Rows: [coefficients, denominator, family, value, first extent quarter-step, outside tile].\nexport const FINITE_MARKINGS = '+JSON.stringify(tables)+';\n');
writeFileSync(new URL('../docs/penrose-finite-marking-certificate.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
