/* Execute the unchanged browser data validator against positive and corrupt data. */
'use strict';
const fs=require('fs'),vm=require('vm'),path=require('path');
const {TextEncoder}=require('util');
const root=path.resolve(__dirname,'../..'),doc=path.join(root,'docs/research/gcts-rl-renewal');
const source=fs.readFileSync(path.join(doc,'certified-prefix-markings.js'),'utf8');
const cut=source.lastIndexOf('  main().catch(');
if(cut<0)throw Error('Reader entry point changed');
const context={TextEncoder,document:{},console};vm.createContext(context);
vm.runInContext(source.slice(0,cut)+'  globalThis.checkCase=validate;\n})();',context);
const data=JSON.parse(fs.readFileSync(path.join(doc,'certified-prefix-reader-001.json'),'utf8'));
data.cases.forEach(context.checkCase);
const original=data.cases.find(c=>c.id==='renamed-five');
const clone=()=>JSON.parse(JSON.stringify(original)),results=[];
function reject(name,mutate){
  const c=clone();mutate(c);let failure;
  try{context.checkCase(c);}catch(e){failure=e.message;}
  if(!failure)throw Error('Corruption survived: '+name);
  results.push({name,rejected:true,reason:failure});
}
reject('flipped-representative-value',c=>{
  const f=c.failures[0],r=f.representatives[0];r.marks.find(([p,v])=>JSON.stringify(p)===JSON.stringify(f.point))[1]=0;
});
reject('missing-word-terminator',c=>{
  const f=c.failures[0],r=f.representatives[0],n=new TextEncoder().encode(JSON.stringify(f.formula)).length;
  r.marks=r.marks.filter(([p,v])=>JSON.stringify(p)!==JSON.stringify([4*f.slot,100+n]));
});
reject('changed-failure-port',c=>c.failures[0].point[1]++);
reject('dropped-distant-identity',c=>c.failures.find(f=>f.support.some(p=>p.kind==='lemma_input')).support.pop());
reject('unknown-used-as-exclusion',c=>{const p=c.probes.find(p=>p.label==='negative');p.label='unknown';p.status='unknown_search_budget';});
reject('missing-selected-input',c=>c.selected=c.selected.filter(p=>p.kind!=='lemma_input'));
reject('wrong-global-native-query',c=>c.proof_query=0);
reject('changed-final-formula',c=>c.spec.target=['bot']);
const output={status:'passed',positive_cases:data.cases.length,mutations_rejected:results};
const target=path.join(root,'.gcts-active/certified-prefix-markings-20261011/reader-corruptions.json');
fs.writeFileSync(target,JSON.stringify(output,null,2)+'\n');console.log(JSON.stringify(output));
