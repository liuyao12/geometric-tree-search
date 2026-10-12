import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {unitLoop,embeddingKey} from '../research/knot-classifier/lattice-state.mjs';
import {faceSweeps,latticeMoves,VERSION} from '../research/knot-classifier/lattice-moves.mjs';
import {latticeCatalog,solveLattice,verifyLatticeCertificate,classifyLattice} from '../research/knot-classifier/lattice-search.mjs';
import {onlinePointSearch} from '../apps/knot-movie/point-search.mjs';
const fixture=JSON.parse(readFileSync(new URL('../research/knot-classifier/fixtures/trefoil-identification.json',import.meta.url)));
const provenance=JSON.parse(readFileSync(new URL('../research/knot-classifier/fixtures/trefoil-source-provenance.json',import.meta.url)));
const corpus=JSON.parse(readFileSync(new URL('../research/knot-classifier/lattice-corpus-12.json',import.meta.url)));
assert.equal(embeddingKey(provenance.source),embeddingKey(corpus.records.find(r=>r.id==='3_1').vertices));
verifyLatticeCertificate(provenance);
const baseline=solveLattice(fixture.source,fixture.target,{...fixture.bounds,learn:false});
const marked=solveLattice(fixture.source,fixture.target,fixture.bounds);
assert.equal(baseline.status,'equivalent');assert.equal(marked.status,'equivalent');
assert.equal(marked.certificate.version,VERSION);assert.equal(marked.learning.cold,true);assert.equal(marked.learning.initialAssignedValues,0);
assert.equal(marked.learning.failures,2);assert(marked.stats.learnedMarkingEliminations>0);
assert.deepEqual(marked.certificate.steps.map(m=>m.kind),['II−','II+','III','II+','I−']);
assert.equal(marked.stats.nodes,baseline.stats.nodes);
// Separate independent Python geometry + Fraction projection + ribbon replay.
const replay=spawnSync('python3',['-c',`import sys,json;sys.path.insert(0,'research/knot-classifier');from verify_lattice_movie import verify;print(json.dumps([verify(c) for c in json.load(sys.stdin)]))`],{input:JSON.stringify([provenance,baseline.certificate,marked.certificate]),encoding:'utf8'});
assert.equal(replay.status,0,replay.stderr);
// Inverse existence for every demonstrated type; expansions are retained.
for(const cert of [provenance,marked.certificate]){
 let p=cert.source;
 for(const step of cert.steps){assert(latticeMoves(step.vertices,{maxEdges:68}).some(m=>m.key===embeddingKey(p)));p=step.vertices;}
}
// Independent exhaustive edge-set oracle for the complete square-face domain.
const pk=p=>p.join(','),ek=(a,b)=>[pk(a),pk(b)].sort().join('|');
function oracle(input,region,maxEdges){
 const p=unitLoop(input),base=new Set(p.map((a,i)=>ek(a,p[(i+1)%p.length]))),result=new Set();
 for(let normal=0;normal<3;normal++){
  const axes=[0,1,2].filter(k=>k!==normal);
  for(let x=region.min[0];x<=region.max[0];x++)for(let y=region.min[1];y<=region.max[1];y++)for(let z=region.min[2];z<=region.max[2];z++){
   const a=[x,y,z],b=[...a],c=[...a],d=[...a];b[axes[0]]++;c[axes[0]]++;c[axes[1]]++;d[axes[1]]++;
   const f=[a,b,c,d];if(f.some(p=>p.some((v,k)=>v>region.max[k])))continue;
   const e=new Set(base);for(let i=0;i<4;i++){const k=ek(f[i],f[(i+1)%4]);if(e.has(k))e.delete(k);else e.add(k);}
   if(e.size<4||e.size>maxEdges)continue;
   const adj=new Map();for(const edge of e){const [a,b]=edge.split('|');for(const [u,v]of[[a,b],[b,a]]){if(!adj.has(u))adj.set(u,[]);adj.get(u).push(v);}}
   if([...adj.values()].some(a=>a.length!==2))continue;
   const seen=new Set(),stack=[adj.keys().next().value];while(stack.length){const a=stack.pop();if(seen.has(a))continue;seen.add(a);stack.push(...adj.get(a));}
   if(seen.size===adj.size)result.add([...e].sort().join(';'));
  }
 }
 return result;
}
const actual=new Set(faceSweeps(fixture.source,fixture.bounds).map(m=>{const p=unitLoop(m.vertices);return p.map((a,i)=>ek(a,p[(i+1)%p.length])).sort().join(';');}));
assert.deepEqual(actual,oracle(fixture.source,fixture.bounds.region,fixture.bounds.maxEdges));
// Independently prove all activated guards by layered graph reachability;
// this oracle never supplies labels to the learner.
const cat=latticeCatalog(fixture.source,fixture.target,fixture.bounds);
const reachable=Array.from({length:cat.depth+1},()=>new Set()),suffix=Array.from({length:cat.depth+1},()=>new Set());
reachable[0].add(cat.sourceKey);suffix[cat.depth].add(cat.targetKey);
for(let t=0;t<cat.depth;t++)for(const tile of cat.tiles)if(tile.time===t&&reachable[t].has(tile.before))reachable[t+1].add(tile.after);
for(let t=cat.depth-1;t>=0;t--)for(const tile of cat.tiles)if(tile.time===t&&suffix[t+1].has(tile.after))suffix[t].add(tile.before);
for(const event of marked.learning.events){const tile=cat.tiles[event.candidate];assert.equal(reachable[tile.time].has(tile.before)&&suffix[tile.time+1].has(tile.after),false);assert(event.marking);}
const opaque={depth:cat.depth,sourceKey:cat.sourceKey,targetKey:cat.targetKey,tiles:cat.tiles.map(({id,t,m})=>({id,t,m}))};
const capped=onlinePointSearch(opaque,{proofNodeCap:0});assert.equal(capped.status,'equivalent');assert.equal(capped.learning.failures,0);assert.equal(capped.stats.unresolvedLabels,2);
assert.equal(solveLattice(fixture.source,fixture.target,{...fixture.bounds,stateCap:1}).status,'unknown');
assert.equal(solveLattice(fixture.source,fixture.target,{...fixture.bounds,maxEdges:4}).status,'unknown');
assert.equal(solveLattice(fixture.source,fixture.target,{...fixture.bounds,direction:[1,1,1]}).status,'unknown');
assert.equal(solveLattice(fixture.source,fixture.target,{...fixture.bounds,nodeCap:0}).status,'unknown');
const shallow=solveLattice(fixture.source,fixture.target,{...fixture.bounds,depth:2});assert.equal(shallow.status,'exhausted-finite-search');assert.equal(shallow.knotEquivalence,'unknown');
const poisoned=structuredClone(marked.certificate);poisoned.steps[0].kind='III';assert.throws(()=>verifyLatticeCertificate(poisoned));
const changed=structuredClone(marked.certificate);changed.steps[0].vertices[0][0]+=1;assert.throws(()=>verifyLatticeCertificate(changed));
const fake=structuredClone(marked.certificate);fake.steps[0].beforeDiagram='';assert.throws(()=>verifyLatticeCertificate(fake));
// Classification attaches reference identity only after spatial verification.
const identified=classifyLattice({vertices:fixture.source,id:'misleading',crossings:0},[{vertices:fixture.target,id:'3_1',invariant:'unused'}],fixture.bounds);
assert.equal(identified.status,'identified');assert.equal(identified.label,'3_1');
assert.equal(embeddingKey([...fixture.source].reverse()),embeddingKey(fixture.source));
assert.notEqual(embeddingKey(fixture.source.map(([x,y,z])=>[x+1,y,z])),embeddingKey(fixture.source));
console.log(JSON.stringify({passed:true,identification:'3_1',sequence:marked.certificate.steps.map(m=>m.kind),latticeStates:cat.stateCount,tiles:cat.tiles.length,learnedGuards:marked.learning.failures,independentReplay:JSON.parse(replay.stdout),independentFaceEnumeration:true,independentGuardProofs:true,budgetSemantics:true}));
