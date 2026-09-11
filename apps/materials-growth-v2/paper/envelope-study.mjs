import fs from 'node:fs';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {hingeExamples,connectionDescriptor,twistConnection} from '../connection-descriptor.mjs';
const raw=fs.readFileSync(process.argv[2]),lines=raw.toString().trim().split(/\r?\n/),frames=new Map();
let offset=0;
for(let id=0;id<168;id++){
  const n=Number(lines[offset]),header=lines[offset+1];
  if(!Number.isInteger(n)||n<1)throw Error('Invalid XYZ');
  if(id>=96){
    const m=header.match(/Lattice="([^"]+)"/);if(!m)throw Error('Missing cell');
    const lattice=m[1].trim().split(/\s+/).map(Number),cell=lattice[0];
    if(lattice.length!==9||lattice.some((v,k)=>Math.abs(v-([0,4,8].includes(k)?cell:0))>1e-7))throw Error('Requires cubic cell');
    const atoms=lines.slice(offset+2,offset+n+2).map(line=>{const f=line.trim().split(/\s+/);return {species:f[0],position:f.slice(1,4).map(Number)};});
    if(atoms.some(a=>a.position.some(v=>!Number.isFinite(v))))throw Error('Invalid coordinates');
    frames.set(id,hingeExamples(atoms,{cell,margin:6}).map(e=>({positive:connectionDescriptor(e.sites),twists:[60,120,180].map(a=>connectionDescriptor(twistConnection(e.sites,a*Math.PI/180)))})));
  }offset+=n+2;
}
let state=2718;const ids=[...frames.keys()];
for(let i=ids.length-1;i>0;i--){state=(Math.imul(1664525,state)+1013904223)>>>0;const j=Math.floor(state/4294967296*(i+1));[ids[i],ids[j]]=[ids[j],ids[i]];}
const split={train:ids.slice(0,48),calibration:ids.slice(48,60),test:ids.slice(60)},library=new Map();
for(const id of split.train)for(const {positive:d} of frames.get(id)){
  if(!library.has(d.key))library.set(d.key,{lo:[...d.values],hi:[...d.values],minimum:Math.min(...d.values)});
  const r=library.get(d.key);d.values.forEach((v,k)=>{r.lo[k]=Math.min(r.lo[k],v);r.hi[k]=Math.max(r.hi[k],v);});r.minimum=Math.min(r.minimum,...d.values);
}
function score(d){const r=library.get(d.key);if(!r)return null;return {baseline:r.minimum-Math.min(...d.values),envelope:Math.max(0,...d.values.flatMap((v,k)=>[r.lo[k]-v,v-r.hi[k]]))};}
const evaluate=ids=>ids.map(id=>({id,connections:frames.get(id).map(e=>({positive:score(e.positive),twists:e.twists.map(score)}))}));
const calibration=evaluate(split.calibration),test=evaluate(split.test),cutoffs={};
for(const name of ['baseline','envelope'])cutoffs[name]=Math.max(...calibration.flatMap(f=>f.connections.filter(c=>c.positive).map(c=>c.positive[name])));
const reject=(s,name)=>s&&(name==='conjunction'?s.baseline>cutoffs.baseline||s.envelope>cutoffs.envelope:s[name]>cutoffs[name]);
const results=['baseline','envelope','conjunction'].map(name=>{
  const perFrame=test.map(f=>{let rejected=0,unknown=0,twistRejected=0,twistKnown=0;for(const c of f.connections){if(!c.positive){unknown++;continue;}if(reject(c.positive,name)){rejected++;continue;}for(const t of c.twists)if(t){twistKnown++;if(reject(t,name))twistRejected++;}}return {id:f.id,total:f.connections.length,rejected,unknown,twistRejected,twistKnown};});
  const sum=key=>perFrame.reduce((s,f)=>s+f[key],0),r={name,preserved:perFrame.filter(f=>!f.rejected).length,configurations:12,total:sum('total'),rejected:sum('rejected'),unknown:sum('unknown'),twistRejected:sum('twistRejected'),twistKnown:sum('twistKnown'),perFrame};
  r.promotion=r.preserved>=11&&r.twistKnown>0&&r.twistRejected/r.twistKnown>=.1&&r.unknown===0;return r;
});
const incremental={eligible:0,baselineOnly:0,envelopeOnly:0,both:0,neither:0};
for(const f of test)for(const c of f.connections)if(c.positive&&!reject(c.positive,'conjunction'))for(const t of c.twists)if(t){incremental.eligible++;const b=reject(t,'baseline'),e=reject(t,'envelope');incremental[b&&e?'both':b?'baselineOnly':e?'envelopeOnly':'neither']++;}
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
fs.writeFileSync(process.argv[3],JSON.stringify({schema:'connection-envelope/1',protocol:'ENVELOPE-PROTOCOL.md',datasetSha256:hash(raw),runnerSha256:hash(fs.readFileSync(fileURLToPath(import.meta.url))),split,seed:2718,cutoffs,library:[...library],results,incremental,calibration,test})+'\n');
console.table(results.map(r=>({method:r.name,preserved:r.preserved,retention:100*(1-r.rejected/r.total),twistRejection:100*r.twistRejected/r.twistKnown,promote:r.promotion})));console.log(incremental);
