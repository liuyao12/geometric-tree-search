import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {verifiedGeometryCoreClass} from './verified-geometry-cores.mjs';
const {PointSearch}=await import(pathToFileURL(process.argv[2]));
const c=(id,base,points)=>({id,base,t:points.map(point=>({point,value:1})),m:[]});
const model={capacity:1,required:['p','q','r'],complete:true,candidates:[c('A','a',['p']),c('A2','a',['p']),c('C','c',['r']),c('Q','q',['p','q']),c('R','r',['q','r'])]};
class Inventory extends PointSearch{reason(c){return super.reason(c)||([...this.placed.keys()].some(id=>this.candidates.get(id).base===c.base)?'inventory':null);}}
const core={owners:['a','c'],point:'q'},E=verifiedGeometryCoreClass(Inventory,model,[core]);
assert.throws(()=>verifiedGeometryCoreClass(Inventory,model,[{owners:['a'],point:'q'}]),/Unverified/);
assert.throws(()=>verifiedGeometryCoreClass(Inventory,model,[{owners:['missing'],point:'q'}]));
const e=new E(model),root=JSON.stringify(e.semanticState());e.apply('A');assert.equal(e.reason(e.candidates.get('C')),'proved-geometric-conflict-core');assert(!e.graph.get('r').has('C'));e.auditGraph();e.undo(0);assert.equal(JSON.stringify(e.semanticState()),root);assert.equal(e.reason(e.candidates.get('C')),null);
let complete=0,pruned=0;
for(let mask=0;mask<32;mask++){
 const rows=model.candidates.filter((_,i)=>mask&(1<<i)),owners=new Set(rows.map(c=>c.base)),totals=model.required.map(p=>rows.reduce((s,c)=>s+c.t.filter(t=>t.point===p).length,0));
 if(owners.size!==rows.length||totals.some(v=>v>1))continue;
 const state=new E(model);let rejected=false;
 for(const c of rows){if(state.reason(state.candidates.get(c.id))){rejected=true;break;}state.apply(c.id);}
 if(totals.every(v=>v===1)){assert(!rejected);complete++;}
 if(rejected){pruned++;assert(owners.has('a')&&owners.has('c'));}
 state.undo(0);state.auditGraph();assert.equal(JSON.stringify(state.semanticState()),root);
}
assert.equal(complete,3);assert.equal(pruned,2);
console.log(JSON.stringify({completeFillingsPreserved:complete,conflictingDecoratedSubsetsRejected:pruned,invalidCertificatesRejected:2,status:'passed'}));
