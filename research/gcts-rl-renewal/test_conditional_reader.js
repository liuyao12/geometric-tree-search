// Validate all positive projections and reject independently corrupted copies.
const fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto'),path=require('node:path');
const root=path.resolve(__dirname,'../..'),doc=path.join(root,'docs/research/gcts-rl-renewal');
const source=fs.readFileSync(path.join(doc,'conditional-attachments.js'),'utf8');
const raw=fs.readFileSync(path.join(doc,'conditional-reader-001.json'));
const data=JSON.parse(raw),context=vm.createContext({TextEncoder,document:{}});
vm.runInContext(source.slice(0,source.lastIndexOf('main();'))+'\nglobalThis.checkProjection=validate;',context);
context.checkProjection(data);
const clone=()=>JSON.parse(raw),rows=[];
function rejects(name,change){const d=clone();change(d);let error;try{context.checkProjection(d);}catch(e){error=e.message;}if(!error)throw Error('corruption accepted: '+name);rows.push({name,status:'rejected',reason:error});}
rejects('Unknown teacher relabeled negative',d=>{const c=d.cases.find(c=>c.probes.some(p=>p.label==='unknown'));const p=c.probes.find(p=>p.label==='unknown');p.label='negative';});
rejects('Omitted Cartesian pair',d=>d.cases[0].probes.pop());
rejects('Changed earlier formula boundary',d=>d.cases[0].probes[0].formulas[0]=['bot']);
rejects('Missing canonical word terminator',d=>d.cases[0].writers[0].word.pop());
rejects('Wrong conditional value',d=>d.cases[0].failures[0].assignments[0].value^=1);
rejects('Missing distant writer',d=>{const f=d.cases[0].failures.find(f=>f.left_keys.length);f.left_keys.pop();});
rejects('Missing single joint writer point',d=>{const f=d.cases[0].failures.find(f=>f.joint_keys.length);f.single_point[1]+=1000;});
rejects('False individually possible claim',d=>{const p=d.cases[0].probes.find(p=>p.genuine);p.individual_labels[0]='unknown';});
rejects('Wrong global native query',d=>d.cases[0].proofs[0].native_query=d.native.length);
rejects('Dropped selected input role',d=>{const p=d.cases[0].proofs[0];const i=p.tiles.findIndex(t=>t.kind==='lemma_input'||t.kind==='unused_input');p.tiles.splice(i,1);});
rejects('Changed lemma attachment',d=>{const p=d.cases[0].proofs.find(p=>p.proof.some(r=>r.rule==='block'));const row=p.proof.find(r=>r.rule==='block');row.inputs[0]=p.proof.length;});
rejects('Wrong selected marking value',d=>d.cases[0].proofs[0].tiles[0].marks[0][1]^=1);
const out={status:'passed',positive_cases:data.cases.length,positive_pairs:data.cases.reduce((a,c)=>a+c.probes.length,0),positive_proofs:data.cases.reduce((a,c)=>a+c.proofs.length,0),corruptions:rows,reader_sha256:crypto.createHash('sha256').update(raw).digest('hex'),script_sha256:crypto.createHash('sha256').update(source).digest('hex')};
console.log(JSON.stringify(out,null,2));
